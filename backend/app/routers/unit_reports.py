from fastapi import APIRouter, Query

from .. import data_loader

router = APIRouter(prefix="/api/unit-reports", tags=["unit-reports"])


@router.get("")
def list_unit_reports(
    교과: str | None = Query(default=None),
    단원: str | None = Query(default=None),
):
    reports = data_loader.load_unit_reports()
    if 교과:
        reports = [r for r in reports if r["교과"] == 교과]
    if 단원:
        reports = [r for r in reports if r["단원"] == 단원]
    return reports
