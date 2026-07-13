from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session as DBSession

from .database import get_db
from .models import Session, User


def get_current_user(
    authorization: str | None = Header(default=None),
    db: DBSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")

    token = authorization.removeprefix("Bearer ").strip()
    session = db.get(Session, token)
    if session is None:
        raise HTTPException(status_code=401, detail="로그인이 만료되었습니다. 다시 로그인해 주세요")

    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="계정을 찾을 수 없습니다")
    if user.is_archived:
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=403, detail="보관 처리된 계정입니다")
    return user


def require_teacher(user: User = Depends(get_current_user)) -> User:
    if user.role != "teacher":
        raise HTTPException(status_code=403, detail="교사만 접근할 수 있습니다")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="관리자만 접근할 수 있습니다")
    return user
