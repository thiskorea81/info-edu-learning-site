from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DBSession

from ..auth import require_teacher
from ..database import get_db
from ..models import User
from ..schemas import RosterCreate, UserPublic

router = APIRouter(prefix="/api/roster", tags=["roster"])


@router.get("", response_model=list[UserPublic])
def list_roster(db: DBSession = Depends(get_db), _teacher: object = Depends(require_teacher)):
    users = db.query(User).order_by(User.role.desc(), User.number).all()
    return [UserPublic(id=u.id, name=u.name, number=u.number, role=u.role) for u in users]


@router.post("", response_model=UserPublic)
def add_student(
    payload: RosterCreate,
    db: DBSession = Depends(get_db),
    _teacher: object = Depends(require_teacher),
):
    user = User(name=payload.name.strip(), number=payload.number.strip(), role=payload.role)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="이미 등록된 번호입니다")
    db.refresh(user)
    return UserPublic(id=user.id, name=user.name, number=user.number, role=user.role)


@router.delete("/{user_id}")
def delete_student(
    user_id: int,
    db: DBSession = Depends(get_db),
    _teacher: object = Depends(require_teacher),
):
    deleted = db.query(User).filter(User.id == user_id).delete()
    db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return {"status": "deleted"}
