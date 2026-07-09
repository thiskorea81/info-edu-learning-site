from fastapi import APIRouter

from ..runner import execute_python
from ..schemas import RunCodeRequest, RunCodeResult

router = APIRouter(prefix="/api", tags=["code-runner"])


@router.post("/run-code", response_model=RunCodeResult)
def run_code(payload: RunCodeRequest):
    result = execute_python(payload.code, payload.stdin)
    return RunCodeResult(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        timed_out=result.timed_out,
    )
