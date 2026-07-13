from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import data_loader
from ..auth import get_current_user
from ..database import get_db
from ..models import Attempt, User, WrongNote
from ..schemas import AttemptCreate, AttemptResult

router = APIRouter(prefix="/api/attempts", tags=["attempts"])


@router.post("", response_model=AttemptResult)
def create_attempt(
    payload: AttemptCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    question = data_loader.get_question(payload.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    correct_answer = question["정답"]
    is_correct = payload.selected == correct_answer

    attempt = Attempt(
        user_id=user.id,
        exam_id=question["exam_id"],
        question_id=question["id"],
        standard_id=question["standard_id"],
        selected=payload.selected,
        correct_answer=correct_answer,
        is_correct=is_correct,
    )
    db.add(attempt)

    if not is_correct:
        note = (
            db.query(WrongNote)
            .filter(WrongNote.user_id == user.id, WrongNote.question_id == question["id"])
            .first()
        )
        if note is None:
            db.add(
                WrongNote(
                    user_id=user.id,
                    question_id=question["id"],
                    standard_id=question["standard_id"],
                    last_selected=payload.selected,
                )
            )
        else:
            note.last_selected = payload.selected

    db.commit()

    return AttemptResult(
        question_id=question["id"],
        selected=payload.selected,
        correct_answer=correct_answer,
        is_correct=is_correct,
        해설=question.get("해설") or "",
        선택지=question.get("선택지") or {},
    )


@router.get("/wrong")
def wrong_note(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    notes = (
        db.query(WrongNote)
        .filter(WrongNote.user_id == user.id)
        .order_by(WrongNote.added_at.desc())
        .all()
    )
    result = []
    for note in notes:
        question = data_loader.get_question(note.question_id)
        if question is None:
            continue
        result.append(
            {
                "question": question,
                "selected": note.last_selected,
                "attempted_at": note.added_at,
            }
        )
    return result


@router.delete("/wrong/{question_id}")
def delete_wrong_note(
    question_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deleted = (
        db.query(WrongNote)
        .filter(WrongNote.user_id == user.id, WrongNote.question_id == question_id)
        .delete()
    )
    db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Wrong note not found")
    return {"status": "deleted"}


@router.get("/question/{question_id}")
def attempt_history(
    question_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    attempts = (
        db.query(Attempt)
        .filter(Attempt.question_id == question_id, Attempt.user_id == user.id)
        .order_by(Attempt.id.desc())
        .all()
    )
    return attempts
