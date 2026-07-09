from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import data_loader
from ..database import get_db
from ..models import Submission
from ..runner import execute_python, normalize_output
from ..schemas import SubmitCodeRequest, SubmitResult, TestCaseResult

router = APIRouter(prefix="/api/problems", tags=["problems"])


def _public(problem: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in problem.items() if k != "tests"}


@router.get("")
def list_problems(standard_id: str | None = Query(default=None)):
    problems = data_loader.list_problems()
    if standard_id:
        problems = [p for p in problems if p.get("standard_id") == standard_id]
    return [_public(p) for p in problems]


@router.get("/groups/by-standard")
def list_problem_groups():
    standards_index = data_loader.standards_by_id()
    groups: dict[str, dict[str, Any]] = {}
    for p in data_loader.list_problems():
        sid = p.get("standard_id")
        key = sid or "기타"
        group = groups.setdefault(key, {
            "standard_id": sid,
            "성취기준명": p.get("성취기준명") or standards_index.get(sid, {}).get("성취기준명", ""),
            "단원": p.get("단원") or standards_index.get(sid, {}).get("단원", ""),
            "problems": [],
        })
        group["problems"].append({"id": p["id"], "title": p["title"], "difficulty": p["difficulty"]})
    return list(groups.values())


@router.get("/{problem_id}")
def get_problem(problem_id: str):
    problem = data_loader.get_problem(problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return _public(problem)


@router.post("/{problem_id}/submit", response_model=SubmitResult)
def submit(problem_id: str, payload: SubmitCodeRequest, db: Session = Depends(get_db)):
    problem = data_loader.get_problem(problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")

    timeout_seconds = problem.get("time_limit_ms", 2000) / 1000
    tests = problem["tests"]
    cases: list[TestCaseResult] = []
    passed = 0

    for i, test in enumerate(tests, start=1):
        result = execute_python(payload.code, test["input"], timeout_seconds)

        if result.timed_out:
            verdict = "TLE"
        elif result.exit_code != 0:
            verdict = "RE"
        elif normalize_output(result.stdout) == normalize_output(test["output"]):
            verdict = "AC"
        else:
            verdict = "WA"

        if verdict == "AC":
            passed += 1

        cases.append(
            TestCaseResult(
                index=i,
                verdict=verdict,
                input=test["input"],
                expected=test["output"],
                actual=result.stdout,
                stderr=result.stderr,
            )
        )

    overall = "AC" if passed == len(tests) else next(c.verdict for c in cases if c.verdict != "AC")

    submission = Submission(
        problem_id=problem_id,
        code=payload.code,
        verdict=overall,
        passed_count=passed,
        total_count=len(tests),
    )
    db.add(submission)
    db.commit()

    return SubmitResult(verdict=overall, passed_count=passed, total_count=len(tests), cases=cases)


@router.get("/{problem_id}/submissions")
def list_submissions(problem_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Submission)
        .filter(Submission.problem_id == problem_id)
        .order_by(Submission.id.desc())
        .all()
    )
