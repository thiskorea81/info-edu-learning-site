from fastapi import APIRouter

from .. import data_loader

router = APIRouter(prefix="/api/textbooks", tags=["textbooks"])


@router.get("")
def list_textbooks():
    return data_loader.load_textbooks()
