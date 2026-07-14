from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from .. import data_loader
from ..auth import get_current_user, require_teacher
from ..config import TEXTBOOK_TEACHER_DIR
from ..models import User

router = APIRouter(prefix="/api/textbooks", tags=["textbooks"])


@router.get("")
def list_textbooks(user: User = Depends(get_current_user)):
    textbooks = data_loader.load_textbooks()
    if user.role != "teacher":
        textbooks = [t for t in textbooks if not t.get("teacher_only")]
    return textbooks


@router.get("/teacher-file/{file_path:path}")
def get_teacher_file(file_path: str, _teacher: User = Depends(require_teacher)):
    """정답·해설이 포함된 교사용 PDF는 정적 서빙 경로 밖(textbook_teacher/)에 두고
    이 인증된 엔드포인트로만 내려준다. 매니페스트에 등록된 teacher_only 파일만 허용한다."""
    manifest = data_loader.load_textbooks()
    entry = next(
        (t for t in manifest if t.get("teacher_only") and t["파일명"] == file_path), None
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")

    full_path = (TEXTBOOK_TEACHER_DIR / file_path).resolve()
    if TEXTBOOK_TEACHER_DIR.resolve() not in full_path.parents:
        raise HTTPException(status_code=400, detail="잘못된 경로입니다")

    return FileResponse(full_path, media_type="application/pdf", filename=full_path.name)
