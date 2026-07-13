from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from .. import data_loader
from ..auth import require_admin, require_teacher
from ..database import get_db
from ..models import Enrollment, Subject, User
from ..schemas import EnrollRequest, EnrollResult, SubjectPublic, UserPublic
from .stats import _compute_stats, _practice_item_stats, _theory_item_stats

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


@router.get("/{subject_id}/stats")
def subject_class_stats(
    subject_id: int,
    db: DBSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    """이 과목 수강생들의 성취도를, 다른 과목 성적과 섞이지 않도록 이 과목 성취기준만으로 집계한다."""
    subject = _get_subject(db, subject_id, teacher)
    students = (
        db.query(User)
        .join(Enrollment, Enrollment.user_id == User.id)
        .filter(Enrollment.subject_id == subject_id, User.is_archived == False)  # noqa: E712
        .order_by(User.login_id)
        .all()
    )
    result = []
    for student in students:
        stats = _compute_stats(db, student.id, subjects={subject.name})
        subj_stats = next((s for s in stats["by_subject"] if s["교과"] == subject.name), None)
        result.append(
            {
                "id": student.id,
                "login_id": student.login_id,
                "name": student.name,
                "solved": subj_stats["solved"] if subj_stats else 0,
                "accuracy": subj_stats["accuracy"] if subj_stats else 0.0,
                "standards_attempted": subj_stats["standards_attempted"] if subj_stats else 0,
                "achievement": subj_stats["achievement"] if subj_stats else None,
                "grade": subj_stats["grade"] if subj_stats else None,
            }
        )
    return result


@router.get("/{subject_id}/stats-summary")
def subject_class_summary(
    subject_id: int,
    db: DBSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    """학급 전체가 잘 따라오고 있는지 확인하기 위한 요약: 학생별이 아니라 성취기준별로
    몇 명이 풀었는지·평균 정답률이 얼마인지를 보여준다. 아직 아무도 안 푼 성취기준은
    수업 진도가 거기까지 못 갔거나 학생들이 놓치고 있다는 신호가 된다."""
    subject = _get_subject(db, subject_id, teacher)
    students = (
        db.query(User)
        .join(Enrollment, Enrollment.user_id == User.id)
        .filter(Enrollment.subject_id == subject_id, User.is_archived == False)  # noqa: E712
        .order_by(User.login_id)
        .all()
    )

    standards = [s for s in data_loader.load_standards() if s["교과"] == subject.name]
    by_standard = {
        s["standard_id"]: {
            "standard_id": s["standard_id"],
            "단원": s["단원"],
            "성취기준명": s["성취기준명"],
            "solved_students": 0,
            "_accuracy_sum": 0.0,
            "practice_students": 0,
            "_practice_accuracy_sum": 0.0,
        }
        for s in standards
    }

    grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "미응시": 0}
    started_count = 0
    achievement_sum = 0.0
    achievement_count = 0

    for student in students:
        stats = _compute_stats(db, student.id, subjects={subject.name})
        if any(row["solved"] or row["practice_attempted"] for row in stats["by_standard"]):
            started_count += 1

        subj_stats = next((s for s in stats["by_subject"] if s["교과"] == subject.name), None)
        if subj_stats and subj_stats["grade"]:
            grade_distribution[subj_stats["grade"]] += 1
            achievement_sum += subj_stats["achievement"]
            achievement_count += 1
        else:
            grade_distribution["미응시"] += 1

        for row in stats["by_standard"]:
            agg = by_standard.get(row["standard_id"])
            if agg is None:
                continue
            if row["solved"]:
                agg["solved_students"] += 1
                agg["_accuracy_sum"] += row["accuracy"]
            if row["practice_attempted"]:
                agg["practice_students"] += 1
                agg["_practice_accuracy_sum"] += row["practice_accuracy"]

    for agg in by_standard.values():
        accuracy_sum = agg.pop("_accuracy_sum")
        practice_accuracy_sum = agg.pop("_practice_accuracy_sum")
        agg["avg_accuracy"] = (
            round(accuracy_sum / agg["solved_students"], 1) if agg["solved_students"] else None
        )
        agg["avg_practice_accuracy"] = (
            round(practice_accuracy_sum / agg["practice_students"], 1)
            if agg["practice_students"]
            else None
        )

    return {
        "subject": subject.name,
        "student_count": len(students),
        "started_count": started_count,
        "not_started_count": len(students) - started_count,
        "average_achievement": (
            round(achievement_sum / achievement_count, 1) if achievement_count else None
        ),
        "grade_distribution": grade_distribution,
        "by_standard": sorted(by_standard.values(), key=lambda e: e["standard_id"]),
    }


@router.get("/{subject_id}/stats-items/{standard_id}")
def subject_standard_items(
    subject_id: int,
    standard_id: str,
    db: DBSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    """이 성취기준에 속한 문항(이론)·문제(실습) 하나하나의 시도/정답 수를 보여준다.
    성취기준 평균만으로는 어떤 문항이 특히 어려웠는지 알 수 없어서 필요하다."""
    subject = _get_subject(db, subject_id, teacher)
    standard = data_loader.standards_by_id().get(standard_id)
    if standard is None or standard.get("교과") != subject.name:
        raise HTTPException(status_code=404, detail="이 과목의 성취기준이 아닙니다")

    student_ids = [
        uid
        for (uid,) in db.query(User.id)
        .join(Enrollment, Enrollment.user_id == User.id)
        .filter(Enrollment.subject_id == subject_id, User.is_archived == False)  # noqa: E712
        .all()
    ]
    if not student_ids:
        return {"성취기준명": standard.get("성취기준명", ""), "이론": [], "실습": []}

    questions = [
        q for q in data_loader.all_questions() if q.get("standard_id") == standard_id
    ]
    question_ids = [q["id"] for q in questions]
    theory_stats = _theory_item_stats(db, student_ids, question_ids)
    theory_items = [
        {"id": q["id"], "문항": q.get("문제") or "", **theory_stats[q["id"]]} for q in questions
    ]

    problems_by_id = data_loader.load_problems()
    problems = [
        p for p in problems_by_id.values() if p.get("standard_id") == standard_id
    ]
    problem_ids = [p["id"] for p in problems]
    practice_stats = _practice_item_stats(db, student_ids, problem_ids)
    practice_items = [
        {"id": p["id"], "제목": p.get("title") or p["id"], **practice_stats[p["id"]]}
        for p in problems
    ]

    return {
        "성취기준명": standard.get("성취기준명", ""),
        "이론": theory_items,
        "실습": practice_items,
    }


@router.get("/{subject_id}/stats/{user_id}")
def subject_student_stats(
    subject_id: int,
    user_id: int,
    db: DBSession = Depends(get_db),
    teacher: User = Depends(require_teacher),
):
    """이 과목에 한정한 학생 한 명의 성취기준별 상세 성취도."""
    subject = _get_subject(db, subject_id, teacher)
    enrolled = (
        db.query(Enrollment)
        .filter(Enrollment.subject_id == subject_id, Enrollment.user_id == user_id)
        .first()
    )
    if enrolled is None:
        raise HTTPException(status_code=404, detail="이 과목의 수강생이 아닙니다")
    student = db.get(User, user_id)
    stats = _compute_stats(db, user_id, subjects={subject.name})
    return {
        "student": {"id": student.id, "name": student.name, "login_id": student.login_id},
        "subject": subject.name,
        **stats,
    }
