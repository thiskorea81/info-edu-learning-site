import datetime
import re
from typing import Any

from pydantic import BaseModel, field_validator

_PASSWORD_RE = re.compile(r"^\d{4}$")


def _check_password_format(v: str) -> str:
    if not _PASSWORD_RE.match(v):
        raise ValueError("비밀번호는 숫자 4자리여야 합니다")
    return v


class LoginRequest(BaseModel):
    login_id: str
    password: str


class UserPublic(BaseModel):
    id: int
    login_id: str
    name: str
    role: str
    is_admin: bool
    is_archived: bool
    must_change_password: bool


class LoginResponse(BaseModel):
    token: str
    user: UserPublic


class ChangePasswordRequest(BaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _check_new_password(cls, v: str) -> str:
        return _check_password_format(v)


class RosterCreate(BaseModel):
    login_id: str
    name: str
    role: str = "student"
    is_admin: bool = False

    @field_validator("role")
    @classmethod
    def _check_role(cls, v: str) -> str:
        if v not in ("student", "teacher"):
            raise ValueError("role은 student 또는 teacher여야 합니다")
        return v


class RosterBulkCreate(BaseModel):
    text: str  # 스프레드시트에서 복사한 여러 줄. 한 줄에 "학번<TAB 또는 ,>이름"


class RosterBulkItemResult(BaseModel):
    line: str
    status: str  # "created" | "skipped" | "error"
    reason: str | None = None


class RosterBulkResult(BaseModel):
    total: int
    created: int
    skipped: int
    results: list[RosterBulkItemResult]


class SubjectPublic(BaseModel):
    id: int
    name: str
    teacher_id: int
    teacher_name: str
    is_archived: bool
    student_count: int


class EnrollRequest(BaseModel):
    login_ids: list[str]


class EnrollResult(BaseModel):
    enrolled: list[str]
    not_found: list[str]
    already_enrolled: list[str]


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


_BLOCK_TYPES = {"text", "table", "code", "image"}


class AssignmentCreate(BaseModel):
    title: str
    description: str
    단원: str | None = None
    due_at: datetime.datetime | None = None


class AssignmentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    단원: str | None = None
    due_at: datetime.datetime | None = None


class AssignmentPublic(BaseModel):
    id: int
    subject_id: int
    subject_name: str
    title: str
    description: str
    단원: str | None = None
    due_at: datetime.datetime | None = None
    created_at: datetime.datetime
    student_count: int | None = None
    submitted_count: int | None = None
    graded_count: int | None = None
    my_status: str | None = None
    my_score: int | None = None


class SubmissionBlock(BaseModel):
    type: str
    value: str
    language: str | None = None

    @field_validator("type")
    @classmethod
    def _check_type(cls, v: str) -> str:
        if v not in _BLOCK_TYPES:
            raise ValueError(f"블록 타입은 {_BLOCK_TYPES} 중 하나여야 합니다")
        return v


class SubmissionSave(BaseModel):
    blocks: list[SubmissionBlock]


class SubmissionPublic(BaseModel):
    id: int
    assignment_id: int
    user_id: int
    login_id: str | None = None
    name: str | None = None
    blocks: list[SubmissionBlock]
    status: str
    submitted_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
    score: int | None = None
    feedback: str | None = None
    graded_at: datetime.datetime | None = None


class GradeRequest(BaseModel):
    score: int | None = None
    feedback: str | None = None


class UploadResult(BaseModel):
    id: int
    url: str
