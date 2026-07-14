import datetime
import json
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import UPLOADS_DIR
from ..database import get_db
from ..models import Assignment, AssignmentSubmission, Subject, Upload, User
from ..schemas import (
    AssignmentPublic,
    SubmissionBlock,
    SubmissionPublic,
    SubmissionSave,
    UploadResult,
)
from .subjects import _enrolled_subject_names

router = APIRouter(prefix="/api", tags=["assignments"])

_ALLOWED_IMAGE_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/gif": "gif",
    "image/webp": "webp",
}
_MAX_UPLOAD_SIZE = 5 * 1024 * 1024


def _my_submission_status(db: Session, assignment_id: int, user_id: int) -> tuple[str, int | None]:
    sub = (
        db.query(AssignmentSubmission)
        .filter(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.user_id == user_id,
        )
        .first()
    )
    if sub is None:
        return "not_submitted", None
    if sub.score is not None:
        return "graded", sub.score
    if sub.submitted_at is not None:
        return "submitted", None
    return "draft", None


def _assignment_public(a: Assignment, db: Session, user: User) -> AssignmentPublic:
    subject = db.get(Subject, a.subject_id)
    my_status, my_score = _my_submission_status(db, a.id, user.id)
    return AssignmentPublic(
        id=a.id,
        subject_id=a.subject_id,
        subject_name=subject.name if subject else "",
        title=a.title,
        description=a.description,
        단원=a.단원,
        due_at=a.due_at,
        created_at=a.created_at,
        my_status=my_status,
        my_score=my_score,
    )


def _submission_public(s: AssignmentSubmission) -> SubmissionPublic:
    blocks = [SubmissionBlock(**b) for b in json.loads(s.content or "[]")]
    status = "graded" if s.score is not None else ("submitted" if s.submitted_at else "draft")
    return SubmissionPublic(
        id=s.id,
        assignment_id=s.assignment_id,
        user_id=s.user_id,
        blocks=blocks,
        status=status,
        submitted_at=s.submitted_at,
        updated_at=s.updated_at,
        score=s.score,
        feedback=s.feedback,
        graded_at=s.graded_at,
    )


@router.get("/assignments", response_model=list[AssignmentPublic])
def list_my_assignments(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == "student":
        allowed = _enrolled_subject_names(db, user)
        if not allowed:
            return []
        subject_ids = [s.id for s in db.query(Subject).filter(Subject.name.in_(allowed)).all()]
    else:
        subject_ids = [s.id for s in db.query(Subject).all()]

    items = (
        db.query(Assignment)
        .filter(Assignment.subject_id.in_(subject_ids))
        .order_by(Assignment.due_at.is_(None), Assignment.due_at)
        .all()
    )
    return [_assignment_public(a, db, user) for a in items]


def _require_access(db: Session, assignment_id: int, user: User) -> Assignment:
    a = db.get(Assignment, assignment_id)
    if a is None:
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다")
    if user.role == "student":
        subject = db.get(Subject, a.subject_id)
        allowed = _enrolled_subject_names(db, user)
        if subject is None or subject.name not in (allowed or set()):
            raise HTTPException(status_code=403, detail="수강 중인 과목의 과제가 아닙니다")
    return a


@router.get("/assignments/{assignment_id}", response_model=AssignmentPublic)
def get_assignment(
    assignment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    a = _require_access(db, assignment_id, user)
    return _assignment_public(a, db, user)


@router.get("/assignments/{assignment_id}/submission", response_model=SubmissionPublic)
def get_my_submission(
    assignment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    _require_access(db, assignment_id, user)
    s = (
        db.query(AssignmentSubmission)
        .filter(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.user_id == user.id,
        )
        .first()
    )
    if s is None:
        return SubmissionPublic(
            id=0,
            assignment_id=assignment_id,
            user_id=user.id,
            blocks=[],
            status="not_submitted",
            updated_at=None,
        )
    return _submission_public(s)


@router.put("/assignments/{assignment_id}/submission", response_model=SubmissionPublic)
def save_submission(
    assignment_id: int,
    payload: SubmissionSave,
    submit: bool = Query(default=False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_access(db, assignment_id, user)
    if user.role != "student":
        raise HTTPException(status_code=403, detail="학생만 제출할 수 있습니다")

    s = (
        db.query(AssignmentSubmission)
        .filter(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.user_id == user.id,
        )
        .first()
    )
    if s is not None and s.score is not None:
        raise HTTPException(status_code=400, detail="이미 채점된 과제는 수정할 수 없습니다")

    content = json.dumps([b.model_dump() for b in payload.blocks], ensure_ascii=False)
    if s is None:
        s = AssignmentSubmission(assignment_id=assignment_id, user_id=user.id, content=content)
        db.add(s)
    else:
        s.content = content
    if submit:
        s.submitted_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(s)
    return _submission_public(s)


@router.post("/uploads", response_model=UploadResult)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ext = _ALLOWED_IMAGE_TYPES.get(file.content_type or "")
    if ext is None:
        raise HTTPException(status_code=400, detail="이미지 파일(png/jpeg/gif/webp)만 업로드할 수 있습니다")

    data = await file.read()
    if len(data) > _MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기는 5MB를 넘을 수 없습니다")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    with open(UPLOADS_DIR / filename, "wb") as f:
        f.write(data)

    upload = Upload(
        filename=filename,
        original_name=file.filename or filename,
        content_type=file.content_type,
        uploaded_by=user.id,
    )
    db.add(upload)
    db.commit()

    return UploadResult(id=upload.id, url=f"/uploads/{filename}")
