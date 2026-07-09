from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import data_loader
from ..database import get_db
from ..models import Attempt

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
def get_stats(db: Session = Depends(get_db)):
    subq = (
        select(Attempt.question_id, func.max(Attempt.id).label("max_id"))
        .group_by(Attempt.question_id)
        .subquery()
    )
    latest = db.query(Attempt).join(subq, Attempt.id == subq.c.max_id).all()

    total_questions = len(data_loader.all_questions())
    solved = len(latest)
    correct = sum(1 for a in latest if a.is_correct)

    standards_index = data_loader.standards_by_id()
    by_standard: dict[str, dict] = {}
    for a in latest:
        entry = by_standard.setdefault(
            a.standard_id,
            {
                "standard_id": a.standard_id,
                "성취기준명": standards_index.get(a.standard_id, {}).get("성취기준명", ""),
                "단원": standards_index.get(a.standard_id, {}).get("단원", ""),
                "solved": 0,
                "correct": 0,
            },
        )
        entry["solved"] += 1
        entry["correct"] += 1 if a.is_correct else 0

    for entry in by_standard.values():
        entry["accuracy"] = round(entry["correct"] / entry["solved"] * 100, 1) if entry["solved"] else 0.0

    return {
        "total_questions": total_questions,
        "solved": solved,
        "correct": correct,
        "accuracy": round(correct / solved * 100, 1) if solved else 0.0,
        "by_standard": sorted(by_standard.values(), key=lambda e: e["standard_id"]),
    }
