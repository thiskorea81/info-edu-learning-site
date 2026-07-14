import json
from functools import lru_cache
from typing import Any

from .config import (
    MATERIALS_DIR,
    PROBLEMS_DIR,
    QUESTIONS_DIR,
    STANDARDS_FILE,
    TEXTBOOK_DIR,
    TEXTBOOK_TEACHER_DIR,
    TEXTBOOKS_FILE,
    UNIT_REPORTS_FILE,
    USER_QUESTIONS_FILE,
)


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


@lru_cache
def load_materials() -> dict[str, dict[str, Any]]:
    """standard_id -> material dict."""
    materials: dict[str, dict[str, Any]] = {}
    for path in sorted(MATERIALS_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            material = json.load(f)
        materials[material["standard_id"]] = material
    return materials


def list_materials() -> list[dict[str, Any]]:
    return list(load_materials().values())


def get_material(standard_id: str) -> dict[str, Any] | None:
    return load_materials().get(standard_id)


@lru_cache
def load_unit_reports() -> list[dict[str, Any]]:
    if not UNIT_REPORTS_FILE.exists():
        return []
    with open(UNIT_REPORTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def get_unit_report(교과: str, 단원: str) -> dict[str, Any] | None:
    for report in load_unit_reports():
        if report["교과"] == 교과 and report["단원"] == 단원:
            return report
    return None


@lru_cache
def load_textbooks() -> list[dict[str, Any]]:
    """교과서 PDF 목록(교과/단원/파일명). 실제 파일은 textbook/(공개) 또는
    textbook_teacher/(teacher_only 항목, 정답·해설 포함) 아래에 있고 둘 다 git에는 안 올라간다."""
    if not TEXTBOOKS_FILE.exists():
        return []
    with open(TEXTBOOKS_FILE, encoding="utf-8") as f:
        entries = json.load(f)
    result = []
    for entry in entries:
        base_dir = TEXTBOOK_TEACHER_DIR if entry.get("teacher_only") else TEXTBOOK_DIR
        path = base_dir / entry["파일명"]
        if not path.is_file():
            continue
        result.append({**entry, "size_mb": round(path.stat().st_size / 1024 / 1024, 1)})
    return result


def add_questions(new_questions: list[dict[str, Any]]) -> None:
    existing: list[dict[str, Any]] = []
    if USER_QUESTIONS_FILE.exists():
        with open(USER_QUESTIONS_FILE, encoding="utf-8") as f:
            existing = json.load(f)
    existing.extend(new_questions)
    with open(USER_QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    reload_data()


def set_question_verified(question_id: str, verified: bool) -> bool:
    """문항이 들어있는 원본 파일을 찾아 검증 여부를 기록한다. 못 찾으면 False."""
    for path in sorted(QUESTIONS_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            questions = json.load(f)
        for q in questions:
            if q.get("id") == question_id:
                q["검증"] = verified
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(questions, f, ensure_ascii=False, indent=2)
                    f.write("\n")
                reload_data()
                return True
    return False


def reload_data() -> None:
    load_standards.cache_clear()
    standards_by_id.cache_clear()
    load_exams.cache_clear()
    load_problems.cache_clear()
    load_materials.cache_clear()
    load_unit_reports.cache_clear()
    load_textbooks.cache_clear()
