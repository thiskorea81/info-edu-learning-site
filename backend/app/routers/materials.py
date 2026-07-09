from fastapi import APIRouter, HTTPException

from .. import data_loader

router = APIRouter(prefix="/api/materials", tags=["materials"])


@router.get("")
def list_materials():
    return [
        {
            "standard_id": m["standard_id"],
            "title": m["title"],
            "성취기준명": m.get("성취기준명", ""),
        }
        for m in data_loader.list_materials()
    ]


@router.get("/{standard_id}")
def get_material(standard_id: str):
    material = data_loader.get_material(standard_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")
    return material
