from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from ..auth import require_admin, require_teacher
from ..database import get_db
from ..models import Enrollment, Subject, User
from ..schemas import EnrollRequest, EnrollResult, SubjectPublic, UserPublic

router = APIRouter(prefix="/api/subject-admin", tags=["subject-admin"])


def _subject_public(subject: Subject, db: DBSession) -> SubjectPublic:
    teacher = db.get(User, subject.teacher_id)
    count = db.query(Enrollment).filter(Enrollment.subject_id == subject.id).count()
    return SubjectPublic(
        id=subject.id,
        name=subject.name,
        teacher_id=subject.teacher_id,
        teacher_name=teacher.name if teacher else "",
        is_archived=subject.is_archived,
        student_count=count,
    )


@router.get("", response_model=list[SubjectPublic])
def list_subjects(db: DBSession = Depends(get_db), teacher: User = Depends(require_teacher)):
    query = db.query(Subject)
    if not teacher.is_admin:
        query = query.filter(Subject.teacher_id == teacher.id)
    subjects = query.order_by(Subject.name).all()
    return [_subject_public(s, db) for s in subjects]


def _get_subject(db: DBSession, subject_id: int, teacher: User) -> Subject:
    subject = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="과목을 찾을 수 없습니다")
    if not teacher.is_admin and subject.teacher_id != teacher.id:
        raise HTTPException(status_code=403, detail="담당 과목만 관리할 수 있습니다")
    return subject


@router.patch("/{subject_id}/archive", response_model=SubjectPublic)
def set_subject_archived(
    subject_id: int,
    is_archived: bool,
    db: DBSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    subject = _get_subject(db, subject_id, teacher)
    subject.is_archived = is_archived
    db.commit()
    db.refresh(subject)
    return _subject_public(subject, db)


@router.patch("/{subject_id}/teacher", response_model=SubjectPublic)
def reassign_teacher(
    subject_id: int,
    teacher_id: int,
    db: DBSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    subject = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="과목을 찾을 수 없습니다")
    new_teacher = db.get(User, teacher_id)
    if new_teacher is None or new_teacher.role != "teacher":
        raise HTTPException(status_code=400, detail="교사 계정이 아닙니다")
    subject.teacher_id = teacher_id
    db.commit()
    db.refresh(subject)
    return _subject_public(subject, db)


@router.get("/{subject_id}/students", response_model=list[UserPublic])
def list_students(
    subject_id: int,
    db: DBSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    _get_subject(db, subject_id, teacher)
    rows = (
        db.query(User)
        .join(Enrollment, Enrollment.user_id == User.id)
        .filter(Enrollment.subject_id == subject_id)
        .order_by(User.login_id)
        .all()
    )
    return [
        UserPublic(
            id=u.id,
            login_id=u.login_id,
            name=u.name,
            role=u.role,
            is_admin=u.is_admin,
            is_archived=u.is_archived,
            must_change_password=u.must_change_password,
        )
        for u in rows
    ]


@router.post("/{subject_id}/students", response_model=EnrollResult)
def enroll_students(
    subject_id: int,
    payload: EnrollRequest,
    db: DBSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    _get_subject(db, subject_id, teacher)

    enrolled, not_found, already = [], [], []
    for login_id in payload.login_ids:
        login_id = login_id.strip()
        if not login_id:
            continue
        student = db.query(User).filter(User.login_id == login_id).first()
        if student is None:
            not_found.append(login_id)
            continue
        exists = (
            db.query(Enrollment)
            .filter(Enrollment.subject_id == subject_id, Enrollment.user_id == student.id)
            .first()
        )
        if exists is not None:
            already.append(login_id)
            continue
        db.add(Enrollment(subject_id=subject_id, user_id=student.id))
        enrolled.append(login_id)

    db.commit()
    return EnrollResult(enrolled=enrolled, not_found=not_found, already_enrolled=already)


@router.delete("/{subject_id}/students/{user_id}")
def unenroll_student(
    subject_id: int,
    user_id: int,
    db: DBSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    _get_subject(db, subject_id, teacher)
    deleted = (
        db.query(Enrollment)
        .filter(Enrollment.subject_id == subject_id, Enrollment.user_id == user_id)
        .delete()
    )
    db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="수강 정보를 찾을 수 없습니다")
    return {"status": "removed"}
