import resource
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TIMEOUT_SECONDS = 5
CPU_SECONDS = 3
MEMORY_BYTES = 256 * 1024 * 1024  # 256MB
MAX_OUTPUT_CHARS = 20_000


@dataclass
class ExecResult:
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool


def _limit_resources() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))
    resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))


def execute_python(code: str, stdin: str = "", timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> ExecResult:
    with tempfile.TemporaryDirectory(prefix="pyrun_") as tmpdir:
        script_path = Path(tmpdir) / "main.py"
        script_path.write_text(code, encoding="utf-8")

        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-S", "-B", str(script_path)],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=tmpdir,
                env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "PYTHONIOENCODING": "utf-8"},
                preexec_fn=_limit_resources,
            )
        except subprocess.TimeoutExpired as e:
            return ExecResult(
                stdout=(e.stdout or "")[:MAX_OUTPUT_CHARS],
                stderr=((e.stderr or "") + "\n[실행 시간 초과]")[:MAX_OUTPUT_CHARS],
                exit_code=None,
                timed_out=True,
            )

        return ExecResult(
            stdout=proc.stdout[:MAX_OUTPUT_CHARS],
            stderr=proc.stderr[:MAX_OUTPUT_CHARS],
            exit_code=proc.returncode,
            timed_out=False,
        )


def normalize_output(text: str) -> str:
    lines = [line.rstrip() for line in text.rstrip("\n").split("\n")]
    return "\n".join(lines)
