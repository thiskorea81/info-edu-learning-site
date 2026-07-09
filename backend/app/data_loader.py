import json
from functools import lru_cache
from typing import Any

from .config import PROBLEMS_DIR, QUESTIONS_DIR, STANDARDS_FILE, USER_QUESTIONS_FILE


@lru_cache
def load_standards() -> list[dict[str, Any]]:
    with open(STANDARDS_FILE, encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def standards_by_id() -> dict[str, dict[str, Any]]:
    return {s["standard_id"]: s for s in load_standards()}


@lru_cache
def load_exams() -> dict[str, list[dict[str, Any]]]:
    """exam_id (filename stem) -> list of questions, each tagged with exam_id."""
    exams: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(QUESTIONS_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            questions = json.load(f)
        for q in questions:
            q["exam_id"] = path.stem
        exams[path.stem] = questions
    return exams


def list_exams() -> list[dict[str, Any]]:
    return [
        {"exam_id": exam_id, "count": len(questions)}
        for exam_id, questions in load_exams().items()
    ]


def all_questions() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for questions in load_exams().values():
        result.extend(questions)
    return result


def get_question(question_id: str) -> dict[str, Any] | None:
    for q in all_questions():
        if q["id"] == question_id:
            return q
    return None


@lru_cache
def load_problems() -> dict[str, dict[str, Any]]:
    """problem_id -> problem dict, tagged with its source file stem."""
    problems: dict[str, dict[str, Any]] = {}
    for path in sorted(PROBLEMS_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
        for p in items:
            p["source"] = path.stem
            problems[p["id"]] = p
    return problems


def list_problems() -> list[dict[str, Any]]:
    return list(load_problems().values())


def get_problem(problem_id: str) -> dict[str, Any] | None:
    return load_problems().get(problem_id)


def add_questions(new_questions: list[dict[str, Any]]) -> None:
    existing: list[dict[str, Any]] = []
    if USER_QUESTIONS_FILE.exists():
        with open(USER_QUESTIONS_FILE, encoding="utf-8") as f:
            existing = json.load(f)
    existing.extend(new_questions)
    with open(USER_QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    reload_data()


def reload_data() -> None:
    load_standards.cache_clear()
    standards_by_id.cache_clear()
    load_exams.cache_clear()
    load_problems.cache_clear()
