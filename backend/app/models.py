import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    login_id: Mapped[str] = mapped_column(String, unique=True, index=True)  # 학생: 학번, 교사: 교사ID
    name: Mapped[str] = mapped_column(String, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="student")  # "student" | "teacher"
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)  # teacher 중 관리자 권한
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)  # 학년 종료 후 보관 모드
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class Session(Base):
    __tablename__ = "sessions"

    token: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class Subject(Base):
    """과목(수강 단위). 커리큘럼 데이터(data/standards.json)의 '교과' 값과 이름이 매칭된다."""

    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class Enrollment(Base):
    """학생-과목 수강 관계(다대다 조인 테이블)."""

    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "subject_id", name="uq_enrollment_user_subject"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    subject_id: Mapped[int] = mapped_column(Integer, ForeignKey("subjects.id"), index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    exam_id: Mapped[str] = mapped_column(String, index=True)
    question_id: Mapped[str] = mapped_column(String, index=True)
    standard_id: Mapped[str] = mapped_column(String, index=True)
    selected: Mapped[int] = mapped_column(Integer)
    correct_answer: Mapped[int] = mapped_column(Integer)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class WrongNote(Base):
    __tablename__ = "wrong_notes"
    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="ix_wrong_notes_user_question"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    question_id: Mapped[str] = mapped_column(String, index=True)
    standard_id: Mapped[str] = mapped_column(String, index=True)
    last_selected: Mapped[int] = mapped_column(Integer)
    added_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    problem_id: Mapped[str] = mapped_column(String, index=True)
    code: Mapped[str] = mapped_column(Text)
    verdict: Mapped[str] = mapped_column(String)
    passed_count: Mapped[int] = mapped_column(Integer)
    total_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class Assignment(Base):
    """교사가 과목 단위로 내는 과제(예: 심화탐구보고서). 구글 클래스룸의 '과제'에 해당."""

    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(Integer, ForeignKey("subjects.id"), index=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    단원: Mapped[str | None] = mapped_column(String, nullable=True)
    due_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class AssignmentSubmission(Base):
    """학생이 과제에 제출한 답안. content는 텍스트/표/코드/이미지 블록의 JSON 배열 문자열."""

    __tablename__ = "assignment_submissions"
    __table_args__ = (
        UniqueConstraint("assignment_id", "user_id", name="uq_assignment_submission_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assignment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assignments.id"), index=True
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text, default="[]")
    submitted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    graded_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    graded_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)


class Upload(Base):
    """과제 제출물에 첨부하는 업로드 이미지 파일 메타데이터."""

    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String)
    original_name: Mapped[str] = mapped_column(String)
    content_type: Mapped[str] = mapped_column(String)
    uploaded_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
