from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from .. import data_loader
from ..auth import get_current_user
from ..database import get_db
from ..models import Enrollment, Subject, User

router = APIRouter(prefix="/api", tags=["subjects"])


def _enrolled_subject_names(db: DBSession, user: User) -> set[str] | None:
    """학생이면 수강 중인 과목명 집합을, 교사/관리자면 None(전체 허용)을 반환한다."""
    if user.role != "student":
        return None
    rows = (
        db.query(Subject.name)
        .join(Enrollment, Enrollment.subject_id == Subject.id)
        .filter(Enrollment.user_id == user.id)
        .all()
    )
    return {name for (name,) in rows}


@router.get("/subjects")
def get_subjects(db: DBSession = Depends(get_db), user: User = Depends(get_current_user)):
    allowed = _enrolled_subject_names(db, user)

    standards = data_loader.load_standards()
    counts = Counter(
        q["standard_id"] for q in data_loader.all_questions() if not q.get("유사문제")
    )

    subjects: dict[str, dict] = {}
    for s in standards:
        if allowed is not None and s["교과"] not in allowed:
            continue
        subject = subjects.setdefault(
            s["교과"], {"교과": s["교과"], "units": {}, "question_count": 0}
        )
        unit = subject["units"].setdefault(
            s["단원"], {"단원": s["단원"], "standards": [], "question_count": 0}
        )
        qc = counts.get(s["standard_id"], 0)
        unit["standards"].append(
            {
                "standard_id": s["standard_id"],
                "성취기준명": s["성취기준명"],
                "question_count": qc,
            }
        )
        unit["question_count"] += qc
        subject["question_count"] += qc

    result = []
    for subject in subjects.values():
        subject["units"] = list(subject["units"].values())
        result.append(subject)
    return result
