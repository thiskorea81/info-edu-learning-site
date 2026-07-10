from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import data_loader
from ..database import get_db
from ..models import Attempt, Submission

router = APIRouter(prefix="/api/stats", tags=["stats"])

_GRADE_CUTS = [(90, "A"), (80, "B"), (70, "C"), (60, "D")]


def _grade(percent: float) -> str:
    for cut, letter in _GRADE_CUTS:
        if percent >= cut:
            return letter
    return "E"


@router.get("")
def get_stats(db: Session = Depends(get_db)):
    # 이론(객관식) 문항별 최신 시도
    theory_subq = (
        select(Attempt.question_id, func.max(Attempt.id).label("max_id"))
        .group_by(Attempt.question_id)
        .subquery()
    )
    latest_theory = db.query(Attempt).join(theory_subq, Attempt.id == theory_subq.c.max_id).all()

    # 실습(코딩테스트) 문제별 최신 제출
    practice_subq = (
        select(Submission.problem_id, func.max(Submission.id).label("max_id"))
        .group_by(Submission.problem_id)
        .subquery()
    )
    latest_practice = (
        db.query(Submission).join(practice_subq, Submission.id == practice_subq.c.max_id).all()
    )

    problems_by_id = data_loader.load_problems()
    standards_index = data_loader.standards_by_id()

    total_questions = len(data_loader.all_questions())
    solved = len(latest_theory)
    correct = sum(1 for a in latest_theory if a.is_correct)

    by_standard: dict[str, dict] = {}

    def entry_for(standard_id: str) -> dict:
        return by_standard.setdefault(
            standard_id,
            {
                "standard_id": standard_id,
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
        if not standard_id:
            continue  # 기본예제/일일문제 등 성취기준이 없는 문제는 성취도 집계에서 제외
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

    return {
        "total_questions": total_questions,
        "solved": solved,
        "correct": correct,
        "accuracy": round(correct / solved * 100, 1) if solved else 0.0,
        "by_standard": sorted(by_standard.values(), key=lambda e: e["standard_id"]),
    }
