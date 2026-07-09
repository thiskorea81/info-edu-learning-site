from collections import Counter

from fastapi import APIRouter

from .. import data_loader

router = APIRouter(prefix="/api", tags=["subjects"])


@router.get("/subjects")
def get_subjects():
    standards = data_loader.load_standards()
    counts = Counter(
        q["standard_id"] for q in data_loader.all_questions() if not q.get("유사문제")
    )

    subjects: dict[str, dict] = {}
    for s in standards:
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
