import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .. import data_loader
from ..auth import require_teacher
from ..database import get_db
from ..models import Enrollment, Subject, User
from ..schemas import BulkQuestionItemResult, BulkQuestionResult, QuestionCreate
from .stats import _grade, _theory_item_stats

router = APIRouter(prefix="/api", tags=["questions"])

_HIDDEN_FIELDS = {"정답", "해설"}

TEMPLATE_QUESTIONS = [
    {
        "standard_id": "12정03-07",
        "내용영역": "Ⅲ-2. 프로그래밍",
        "문제": "다음 코드를 실행했을 때 출력 결과로 옳은 것은?",
        "코드": "print(1 + 2)",
        "언어": "python",
        "표": None,
        "이미지": None,
        "선택지": ["1", "2", "3", "12", "오류가 발생한다"],
        "정답": 3,
        "해설": "1 + 2는 3이다.",
    },
    {
        "standard_id": "12정01-01",
        "내용영역": "Ⅰ-1. 네트워크",
        "문제": "네트워크에 대한 설명 중 옳은 것은?",
        "코드": None,
        "언어": None,
        "표": None,
        "이미지": None,
        "선택지": [
            "IPv4는 32비트로 구성된다.",
            "IPv6는 64비트로 구성된다.",
            "DNS는 MAC 주소를 IP 주소로 변환한다.",
            "라우터는 같은 네트워크 내부에서만 사용된다.",
            "허브는 지능적으로 필요한 포트로만 데이터를 전달한다.",
        ],
        "정답": 1,
        "해설": "IPv4 주소는 32비트로 구성된다.",
    },
]


def _public(question: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in question.items() if k not in _HIDDEN_FIELDS}


def _build_question(payload: QuestionCreate) -> dict[str, Any]:
    std = data_loader.standards_by_id().get(payload.standard_id)
    if std is None:
        raise ValueError(f"알 수 없는 성취기준입니다: {payload.standard_id}")

    return {
        "id": f"q_user_{uuid.uuid4().hex[:10]}",
        "standard_id": payload.standard_id,
        "교과": std["교과"],
        "단원": std["단원"],
        "내용영역": payload.내용영역,
        "성취기준명": std["성취기준명"],
        "유형": "5지선다형",
        "문제": payload.문제,
        "코드": payload.코드,
        "언어": payload.언어 or ("python" if payload.코드 else None),
        "실행결과": None,
        "표": payload.표,
        "이미지": payload.이미지,
        "선택지": {str(i + 1): c for i, c in enumerate(payload.선택지)},
        "정답": payload.정답,
        "해설": payload.해설,
    }


@router.get("/exams")
def get_exams():
    return data_loader.list_exams()


@router.get("/standards")
def get_standards():
    return data_loader.load_standards()


@router.get("/questions")
def get_questions(
    exam_id: str | None = Query(default=None),
    standard_id: str | None = Query(default=None),
    교과: str | None = Query(default=None),
    단원: str | None = Query(default=None),
    include_similar: bool = Query(default=False),
):
    questions = data_loader.all_questions()
    if not include_similar:
        questions = [q for q in questions if not q.get("유사문제")]
    if exam_id:
        questions = [q for q in questions if q["exam_id"] == exam_id]
    if standard_id:
        questions = [q for q in questions if q["standard_id"] == standard_id]
    if 교과 or 단원:
        standards_index = data_loader.standards_by_id()

        def matches(q: dict) -> bool:
            std = standards_index.get(q["standard_id"])
            if std is None:
                return False
            if 교과 and std["교과"] != 교과:
                return False
            if 단원 and std["단원"] != 단원:
                return False
            return True

        questions = [q for q in questions if matches(q)]
    return [_public(q) for q in questions]


@router.post("/questions", status_code=201)
def create_question(payload: QuestionCreate):
    try:
        question = _build_question(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    data_loader.add_questions([question])
    return question


@router.get("/questions/template")
def download_template():
    return JSONResponse(
        content=TEMPLATE_QUESTIONS,
        headers={"Content-Disposition": "attachment; filename=question_template.json"},
    )


@router.post("/questions/bulk", response_model=BulkQuestionResult)
async def bulk_create_questions(file: UploadFile = File(...)):
    content = await file.read()
    try:
        items = json.loads(content)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON 파싱 오류: {e}") from e
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="JSON 파일은 문제 배열([...]) 형식이어야 합니다")

    results: list[BulkQuestionItemResult] = []
    valid_questions: list[dict[str, Any]] = []

    for i, raw in enumerate(items):
        try:
            payload = QuestionCreate(**raw)
            question = _build_question(payload)
        except (ValidationError, ValueError, TypeError) as e:
            results.append(BulkQuestionItemResult(index=i, status="error", reason=str(e)))
            continue
        valid_questions.append(question)
        results.append(
            BulkQuestionItemResult(
                index=i, status="ok", id=question["id"], 문제=question["문제"][:60]
            )
        )

    if valid_questions:
        data_loader.add_questions(valid_questions)

    return BulkQuestionResult(
        total=len(items),
        succeeded=len(valid_questions),
        failed=len(items) - len(valid_questions),
        results=results,
    )


def _enrolled_student_ids(db: Session, subject_name: str) -> list[int]:
    subject = db.query(Subject).filter(Subject.name == subject_name).first()
    if subject is None:
        return []
    return [
        uid
        for (uid,) in db.query(User.id)
        .join(Enrollment, Enrollment.user_id == User.id)
        .filter(Enrollment.subject_id == subject.id, User.is_archived == False)  # noqa: E712
        .all()
    ]


@router.get("/questions/stats")
def get_questions_stats(
    교과: str = Query(...),
    단원: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _teacher: User = Depends(require_teacher),
):
    """교사가 '평가'에서 문항 목록을 볼 때 문항별 시도/정답 인원을 한 번에 보여주기 위한 집계.
    정답률이 낮거나 아무도 안 푼 문항을 표시해 중점 지도가 필요한 곳을 짚어준다."""
    standards_index = data_loader.standards_by_id()

    def matches(q: dict) -> bool:
        std = standards_index.get(q["standard_id"])
        if std is None or std["교과"] != 교과:
            return False
        if 단원 and std["단원"] != 단원:
            return False
        return True

    questions = [q for q in data_loader.all_questions() if not q.get("유사문제") and matches(q)]
    question_ids = [q["id"] for q in questions]
    student_ids = _enrolled_student_ids(db, 교과)
    item_stats = _theory_item_stats(db, student_ids, question_ids)

    items = {}
    for qid, s in item_stats.items():
        items[qid] = {
            **s,
            "grade": _grade(s["accuracy"]) if s["accuracy"] is not None else None,
            "needs_attention": s["accuracy"] is not None and s["accuracy"] < 60,
        }

    return {"student_count": len(student_ids), "items": items}


@router.get("/questions/{question_id}/teacher-view")
def get_question_teacher_view(
    question_id: str,
    db: Session = Depends(get_db),
    _teacher: User = Depends(require_teacher),
):
    """정답·해설을 감추지 않고, 이 문항의 학급 정답/오답 인원까지 함께 돌려주는 교사 전용 조회."""
    question = data_loader.get_question(question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    student_ids = _enrolled_student_ids(db, question.get("교과", ""))
    stats = _theory_item_stats(db, student_ids, [question_id])[question_id]
    return {
        **question,
        "student_count": len(student_ids),
        "attempted": stats["attempted"],
        "correct": stats["correct"],
        "accuracy": stats["accuracy"],
        "grade": _grade(stats["accuracy"]) if stats["accuracy"] is not None else None,
        "needs_attention": stats["accuracy"] is not None and stats["accuracy"] < 60,
    }


@router.get("/questions/{question_id}")
def get_question(question_id: str):
    question = data_loader.get_question(question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return _public(question)
