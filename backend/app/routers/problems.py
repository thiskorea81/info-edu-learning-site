from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import data_loader
from ..database import get_db
from ..models import Submission
from ..runner import execute_python, normalize_output
from ..schemas import SubmitCodeRequest, SubmitResult, TestCaseResult

router = APIRouter(prefix="/api/problems", tags=["problems"])


_DIFFICULTY_LETTER = {"쉬움": "A", "보통": "B", "어려움": "C"}

TYPE_ORDER = ["A", "B", "C", "D", "E", "F", "G"]


def _letter(difficulty: str | None) -> str:
    return _DIFFICULTY_LETTER.get(difficulty or "", "?")


def _category_of(problem: dict[str, Any]) -> str:
    source = problem.get("source") or ""
    if source == "basic_problems":
        return "basic"
    if source.startswith("daily_"):
        return "daily"
    유형 = problem.get("유형")
    if 유형 in TYPE_ORDER:
        return f"type_{유형}"
    return problem.get("standard_id") or "기타"


def _public(problem: dict[str, Any]) -> dict[str, Any]:
    result = {k: v for k, v in problem.items() if k != "tests"}
    result["letter"] = _letter(problem.get("difficulty"))
    result["category"] = _category_of(problem)
    return result


@router.get("")
def list_problems(
    standard_id: str | None = Query(default=None),
    category: str | None = Query(default=None),
):
    problems = data_loader.list_problems()
    if standard_id:
        problems = [p for p in problems if p.get("standard_id") == standard_id]
    if category:
        problems = [p for p in problems if _category_of(p) == category]
    return [_public(p) for p in problems]


def _counts_by_category() -> dict[str, int]:
    counts: dict[str, int] = {}
    for p in data_loader.list_problems():
        key = _category_of(p)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _standard_keys(counts: dict[str, int]) -> list[str]:
    return sorted(k for k in counts if k not in ("basic", "daily") and not k.startswith("type_"))


def _standard_category(key: str, counts: dict[str, int], standards_index: dict[str, Any]) -> dict[str, Any]:
    std = standards_index.get(key, {})
    return {
        "key": key,
        "label": f"[{key}] {std.get('단원', '')}",
        "성취기준명": std.get("성취기준명", ""),
        "count": counts[key],
    }


@router.get("/categories")
def list_categories():
    counts = _counts_by_category()
    standard_keys = _standard_keys(counts)
    type_keys = [f"type_{letter}" for letter in TYPE_ORDER if f"type_{letter}" in counts]

    result: list[dict[str, Any]] = []
    if "basic" in counts:
        result.append({"key": "basic", "label": "기본 예제", "count": counts["basic"]})
    if "daily" in counts:
        result.append(
            {"key": "daily", "label": "일일 문제 (매일 자동 생성)", "count": counts["daily"]}
        )
    if standard_keys:
        result.append(
            {
                "key": "textbook",
                "label": "교과서문제",
                "count": sum(counts[k] for k in standard_keys),
                "folder": True,
            }
        )
    for key in type_keys:
        letter = key.removeprefix("type_")
        result.append({"key": key, "label": f"{letter}형 문제", "count": counts[key]})
    return result


@router.get("/categories/textbook")
def list_textbook_categories():
    counts = _counts_by_category()
    standards_index = data_loader.standards_by_id()
    return [_standard_category(k, counts, standards_index) for k in _standard_keys(counts)]


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
