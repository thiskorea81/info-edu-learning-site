import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session as DBSession

from ..auth import get_current_user
from ..database import get_db
from ..models import Session, User
from ..schemas import LoginRequest, LoginResponse, UserPublic

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: DBSession = Depends(get_db)):
    user = (
        db.query(User)
        .filter(User.name == payload.name.strip(), User.number == payload.number.strip())
        .first()
    )
    if user is None:
        raise HTTPException(status_code=401, detail="이름 또는 번호가 일치하지 않습니다")

    token = secrets.token_urlsafe(32)
    db.add(Session(token=token, user_id=user.id))
    db.commit()

    return LoginResponse(
        token=token,
        user=UserPublic(id=user.id, name=user.name, number=user.number, role=user.role),
    )


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
    return UserPublic(id=user.id, name=user.name, number=user.number, role=user.role)
