from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import data_loader
from ..auth import get_current_user
from ..database import get_db
from ..models import Submission, User
from ..runner import execute_python, normalize_output
from ..schemas import SubmitCodeRequest, SubmitResult, TestCaseResult

router = APIRouter(prefix="/api/problems", tags=["problems"])


_DIFFICULTY_LETTER = {"쉬움": "A", "보통": "B", "어려움": "C"}

TYPE_ORDER = ["A", "B", "C", "D", "E", "F", "G"]


def _letter(difficulty: str | None) -> str:
    return _DIFFICULTY_LETTER.get(difficulty or "", "?")


def _category_of(problem: dict[str, Any]) -> str | None:
    """1차 분류: 기본 예제 / 일일 문제 / 교과서(성취기준)만 판단한다.
    유형(A~G)은 이 분류와 무관하게 _type_of()로 별도 판단하며, 한 문제가
    1차 카테고리와 유형 카테고리에 동시에 속할 수 있다(예: 일일 문제이면서 C형)."""
    source = problem.get("source") or ""
    if source == "basic_problems":
        return "basic"
    if source.startswith("daily_"):
        return "daily"
    return problem.get("standard_id") or None


def _type_of(problem: dict[str, Any]) -> str | None:
    유형 = problem.get("유형")
    return 유형 if 유형 in TYPE_ORDER else None


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
        if category.startswith("type_"):
            letter = category.removeprefix("type_")
            problems = [p for p in problems if _type_of(p) == letter]
        else:
            problems = [p for p in problems if _category_of(p) == category]
    return [_public(p) for p in problems]


def _counts_by_category() -> dict[str, int]:
    counts: dict[str, int] = {}
    for p in data_loader.list_problems():
        key = _category_of(p)
        if key is None:
            continue
        counts[key] = counts.get(key, 0) + 1
    return counts


def _counts_by_type() -> dict[str, int]:
    counts: dict[str, int] = {}
    for p in data_loader.list_problems():
        letter = _type_of(p)
        if letter is None:
            continue
        counts[letter] = counts.get(letter, 0) + 1
    return counts


def _standard_keys(counts: dict[str, int]) -> list[str]:
    return sorted(k for k in counts if k not in ("basic", "daily"))


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
    type_counts = _counts_by_type()
    standard_keys = _standard_keys(counts)

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
    for letter in TYPE_ORDER:
        if letter in type_counts:
            result.append(
                {"key": f"type_{letter}", "label": f"{letter}형 문제", "count": type_counts[letter]}
            )
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
def submit(
    problem_id: str,
    payload: SubmitCodeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
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
        user_id=user.id,
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
def list_submissions(
    problem_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Submission)
        .filter(Submission.problem_id == problem_id, Submission.user_id == user.id)
        .order_by(Submission.id.desc())
        .all()
    )
