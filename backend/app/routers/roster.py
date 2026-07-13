from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DBSession

from ..auth import require_admin, require_teacher
from ..database import get_db
from ..models import Enrollment, Session, User
from ..passwords import DEFAULT_PASSWORD, hash_password
from ..schemas import (
    RosterBulkCreate,
    RosterBulkItemResult,
    RosterBulkResult,
    RosterCreate,
    UserPublic,
)

router = APIRouter(prefix="/api/roster", tags=["roster"])


def _public(u: User) -> UserPublic:
    return UserPublic(
        id=u.id,
        login_id=u.login_id,
        name=u.name,
        role=u.role,
        is_admin=u.is_admin,
        is_archived=u.is_archived,
        must_change_password=u.must_change_password,
    )


def _get_target(db: DBSession, user_id: int) -> User:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return target


def _require_admin_for_teacher_target(target: User, actor: User) -> None:
    if target.role == "teacher" and not actor.is_admin:
        raise HTTPException(status_code=403, detail="교사 계정 관리는 관리자만 가능합니다")


@router.get("", response_model=list[UserPublic])
def list_roster(
    include_archived: bool = Query(default=False),
    db: DBSession = Depends(get_db),
    _teacher: User = Depends(require_teacher),
):
    query = db.query(User)
    if not include_archived:
        query = query.filter(User.is_archived == False)  # noqa: E712
    users = query.order_by(User.role.desc(), User.login_id).all()
    return [_public(u) for u in users]


@router.post("", response_model=UserPublic)
def add_user(
    payload: RosterCreate,
    db: DBSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    if (payload.role == "teacher" or payload.is_admin) and not teacher.is_admin:
        raise HTTPException(status_code=403, detail="교사 계정 생성·관리자 지정은 관리자만 가능합니다")

    user = User(
        login_id=payload.login_id.strip(),
        name=payload.name.strip(),
        password_hash=hash_password(DEFAULT_PASSWORD),
        role=payload.role,
        is_admin=payload.is_admin,
        must_change_password=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="이미 등록된 학번/교사ID입니다")
    db.refresh(user)
    return _public(user)


@router.post("/bulk", response_model=RosterBulkResult)
def add_students_bulk(
    payload: RosterBulkCreate,
    db: DBSession = Depends(get_db),
    _teacher: User = Depends(require_teacher),
):
    """스프레드시트에서 복사한 여러 줄을 한 번에 등록한다.
    한 줄 형식: '학번<TAB 또는 ,>이름' (양쪽 공백은 무시)."""
    results: list[RosterBulkItemResult] = []
    created = 0
    skipped = 0

    for raw_line in payload.text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        parts = [p.strip() for p in (line.split("\t") if "\t" in line else line.split(",")) if p.strip() != ""]
        if len(parts) < 2:
            results.append(RosterBulkItemResult(line=line, status="error", reason="형식이 '학번,이름'이 아닙니다"))
            skipped += 1
            continue

        login_id, name = parts[0], parts[1]
        if db.query(User).filter(User.login_id == login_id).first() is not None:
            results.append(RosterBulkItemResult(line=line, status="skipped", reason="이미 등록된 학번"))
            skipped += 1
            continue

        db.add(
            User(
                login_id=login_id,
                name=name,
                password_hash=hash_password(DEFAULT_PASSWORD),
                role="student",
                must_change_password=True,
            )
        )
        results.append(RosterBulkItemResult(line=line, status="created"))
        created += 1

    db.commit()
    return RosterBulkResult(total=len(results), created=created, skipped=skipped, results=results)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: DBSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    target = _get_target(db, user_id)
    _require_admin_for_teacher_target(target, teacher)
    db.query(Enrollment).filter(Enrollment.user_id == user_id).delete()
    db.query(Session).filter(Session.user_id == user_id).delete()
    db.delete(target)
    db.commit()
    return {"status": "deleted"}


@router.post("/{user_id}/reset-password", response_model=UserPublic)
def reset_password(
    user_id: int,
    db: DBSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    target = _get_target(db, user_id)
    _require_admin_for_teacher_target(target, teacher)
    target.password_hash = hash_password(DEFAULT_PASSWORD)
    target.must_change_password = True
    db.commit()
    db.refresh(target)
    return _public(target)


@router.patch("/{user_id}/archive", response_model=UserPublic)
def set_archived(
    user_id: int,
    is_archived: bool,
    db: DBSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    target = _get_target(db, user_id)
    _require_admin_for_teacher_target(target, teacher)
    target.is_archived = is_archived
    db.commit()
    db.refresh(target)
    return _public(target)


@router.patch("/{user_id}/admin", response_model=UserPublic)
def set_admin(
    user_id: int,
    is_admin: bool,
    db: DBSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    target = _get_target(db, user_id)
    if target.role != "teacher":
        raise HTTPException(status_code=400, detail="관리자 권한은 교사 계정에만 부여할 수 있습니다")
    target.is_admin = is_admin
    db.commit()
    db.refresh(target)
    return _public(target)
