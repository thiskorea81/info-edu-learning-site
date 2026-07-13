from typing import Any

from pydantic import BaseModel, field_validator


class LoginRequest(BaseModel):
    name: str
    number: str


class UserPublic(BaseModel):
    id: int
    name: str
    number: str
    role: str


class LoginResponse(BaseModel):
    token: str
    user: UserPublic


class RosterCreate(BaseModel):
    name: str
    number: str
    role: str = "student"

    @field_validator("role")
    @classmethod
    def _check_role(cls, v: str) -> str:
        if v not in ("student", "teacher"):
            raise ValueError("role은 student 또는 teacher여야 합니다")
        return v


class AttemptCreate(BaseModel):
    question_id: str
    selected: int


class AttemptResult(BaseModel):
    question_id: str
    selected: int
    correct_answer: int
    is_correct: bool
    해설: str
    선택지: dict[str, Any]


class RunCodeRequest(BaseModel):
    code: str
    stdin: str = ""


class RunCodeResult(BaseModel):
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool


class SubmitCodeRequest(BaseModel):
    code: str


class TestCaseResult(BaseModel):
    index: int
    verdict: str
    input: str
    expected: str
    actual: str
    stderr: str


class SubmitResult(BaseModel):
    verdict: str
    passed_count: int
    total_count: int
    cases: list[TestCaseResult]


class QuestionCreate(BaseModel):
    standard_id: str
    문제: str
    선택지: list[str]
    정답: int
    코드: str | None = None
    언어: str | None = None
    표: str | None = None
    이미지: str | None = None
    내용영역: str = ""
    해설: str = ""

    @field_validator("선택지")
    @classmethod
    def _check_choices(cls, v: list[str]) -> list[str]:
        if len(v) != 5:
            raise ValueError("선택지는 정확히 5개여야 합니다")
        return v

    @field_validator("정답")
    @classmethod
    def _check_answer(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("정답은 1~5 사이의 값이어야 합니다")
        return v


class BulkQuestionItemResult(BaseModel):
    index: int
    status: str
    id: str | None = None
    문제: str | None = None
    reason: str | None = None


class BulkQuestionResult(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[BulkQuestionItemResult]
