from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import data_loader
from ..auth import get_current_user
from ..database import get_db
from ..models import Attempt, Submission, User
from .subjects import _enrolled_subject_names

router = APIRouter(prefix="/api/stats", tags=["stats"])

_GRADE_CUTS = [(90, "A"), (80, "B"), (70, "C"), (60, "D")]


def _grade(percent: float) -> str:
    for cut, letter in _GRADE_CUTS:
        if percent >= cut:
            return letter
    return "E"


def _compute_stats(db: Session, user_id: int, subjects: set[str] | None = None) -> dict:
    """subjects가 주어지면 해당 교과(들)의 성취기준으로만 범위를 좁혀 집계한다.
    한 학생이 여러 과목을 수강할 수 있으므로, 과목을 섞어 하나의 등급으로
    뭉뚱그리지 않도록 by_subject에 과목별 종합 등급을 별도로 담는다."""
    standards_index = data_loader.standards_by_id()

    def subject_of(standard_id: str) -> str:
        return standards_index.get(standard_id, {}).get("교과", "")

    def in_scope(standard_id: str) -> bool:
        return subjects is None or subject_of(standard_id) in subjects

    # 이론(객관식) 문항별 최신 시도 (해당 사용자 것만)
    theory_subq = (
        select(Attempt.question_id, func.max(Attempt.id).label("max_id"))
        .where(Attempt.user_id == user_id)
        .group_by(Attempt.question_id)
        .subquery()
    )
    latest_theory = [
        a
        for a in db.query(Attempt).join(theory_subq, Attempt.id == theory_subq.c.max_id).all()
        if in_scope(a.standard_id)
    ]

    # 실습(코딩테스트) 문제별 최신 제출 (해당 사용자 것만)
    practice_subq = (
        select(Submission.problem_id, func.max(Submission.id).label("max_id"))
        .where(Submission.user_id == user_id)
        .group_by(Submission.problem_id)
        .subquery()
    )
    latest_practice = (
        db.query(Submission).join(practice_subq, Submission.id == practice_subq.c.max_id).all()
    )

    problems_by_id = data_loader.load_problems()

    total_questions = sum(
        1 for q in data_loader.all_questions() if in_scope(q.get("standard_id", ""))
    )
    solved = len(latest_theory)
    correct = sum(1 for a in latest_theory if a.is_correct)

    by_standard: dict[str, dict] = {}

    def entry_for(standard_id: str) -> dict:
        return by_standard.setdefault(
            standard_id,
            {
                "standard_id": standard_id,
                "교과": subject_of(standard_id),
                "성취기준명": standards_index.get(standard_id, {}).get("성취기준명", ""),
                "단원": standards_index.get(standard_id, {}).get("단원", ""),
                "solved": 0,
                "correct": 0,
                "practice_attempted": 0,
                "practice_correct": 0,
            },
        )

    for a in latest_theory:
        entry = entry_for(a.standard_id)
        entry["solved"] += 1
        entry["correct"] += 1 if a.is_correct else 0

    for s in latest_practice:
        problem = problems_by_id.get(s.problem_id)
        standard_id = problem.get("standard_id") if problem else None
        if not standard_id or not in_scope(standard_id):
            continue  # 기본예제/일일문제 등 성취기준이 없거나 범위 밖인 문제는 제외
        entry = entry_for(standard_id)
        entry["practice_attempted"] += 1
        entry["practice_correct"] += 1 if s.verdict == "AC" else 0

    for entry in by_standard.values():
        theory_acc = (entry["correct"] / entry["solved"] * 100) if entry["solved"] else None
        practice_acc = (
            entry["practice_correct"] / entry["practice_attempted"] * 100
            if entry["practice_attempted"]
            else None
        )
        entry["accuracy"] = round(theory_acc, 1) if theory_acc is not None else 0.0
        entry["practice_accuracy"] = round(practice_acc, 1) if practice_acc is not None else 0.0

        # 이론:실습 = 50:50. 한쪽만 시도했다면 시도한 쪽만으로 판정한다.
        parts = [v for v in (theory_acc, practice_acc) if v is not None]
        combined = sum(parts) / len(parts) if parts else None
        entry["achievement"] = round(combined, 1) if combined is not None else None
        entry["grade"] = _grade(combined) if combined is not None else None

    # 과목별 종합 등급: 여러 과목을 수강하는 학생도 과목마다 따로 판정한다.
    by_subject: dict[str, dict] = {}
    if subjects is not None:
        for name in subjects:
            by_subject[name] = {
                "교과": name,
                "solved": 0,
                "correct": 0,
                "practice_attempted": 0,
                "practice_correct": 0,
                "standards_attempted": 0,
                "achievement": None,
                "grade": None,
            }
    achievement_parts: dict[str, list[float]] = {}
    for entry in by_standard.values():
        subj = entry["교과"]
        agg = by_subject.setdefault(
            subj,
            {
                "교과": subj,
                "solved": 0,
                "correct": 0,
                "practice_attempted": 0,
                "practice_correct": 0,
                "standards_attempted": 0,
                "achievement": None,
                "grade": None,
            },
        )
        agg["solved"] += entry["solved"]
        agg["correct"] += entry["correct"]
        agg["practice_attempted"] += entry["practice_attempted"]
        agg["practice_correct"] += entry["practice_correct"]
        if entry["solved"] or entry["practice_attempted"]:
            agg["standards_attempted"] += 1
        if entry["achievement"] is not None:
            achievement_parts.setdefault(subj, []).append(entry["achievement"])

    for subj, agg in by_subject.items():
        agg["accuracy"] = round(agg["correct"] / agg["solved"] * 100, 1) if agg["solved"] else 0.0
        agg["practice_accuracy"] = (
            round(agg["practice_correct"] / agg["practice_attempted"] * 100, 1)
            if agg["practice_attempted"]
            else 0.0
        )
        parts = achievement_parts.get(subj, [])
        overall = round(sum(parts) / len(parts), 1) if parts else None
        agg["achievement"] = overall
        agg["grade"] = _grade(overall) if overall is not None else None

    return {
        "total_questions": total_questions,
        "solved": solved,
        "correct": correct,
        "accuracy": round(correct / solved * 100, 1) if solved else 0.0,
        "by_standard": sorted(by_standard.values(), key=lambda e: e["standard_id"]),
        "by_subject": sorted(by_subject.values(), key=lambda e: e["교과"]),
    }


@router.get("")
def get_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    subjects = _enrolled_subject_names(db, user) if user.role == "student" else None
    return _compute_stats(db, user.id, subjects=subjects)
