import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session as DBSession

from ..auth import get_current_user
from ..database import get_db
from ..models import Session, User
from ..passwords import hash_password, verify_password
from ..schemas import ChangePasswordRequest, LoginRequest, LoginResponse, UserPublic

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        login_id=user.login_id,
        name=user.name,
        role=user.role,
        is_admin=user.is_admin,
        is_archived=user.is_archived,
        must_change_password=user.must_change_password,
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.login_id == payload.login_id.strip()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 일치하지 않습니다")
    if user.is_archived:
        raise HTTPException(status_code=403, detail="보관 처리된 계정입니다. 선생님께 문의하세요")

    token = secrets.token_urlsafe(32)
    db.add(Session(token=token, user_id=user.id))
    db.commit()

    return LoginResponse(token=token, user=_public(user))


@router.post("/logout")
def logout(
    authorization: str | None = Header(default=None),
    db: DBSession = Depends(get_db),
):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        db.query(Session).filter(Session.token == token).delete()
        db.commit()
    return {"status": "logged_out"}


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)):
    return _public(user)


@router.post("/change-password", response_model=UserPublic)
def change_password(
    payload: ChangePasswordRequest,
    db: DBSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    db.commit()
    db.refresh(user)
    return _public(user)
