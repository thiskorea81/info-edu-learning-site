import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, index=True)
    number: Mapped[str] = mapped_column(String, unique=True, index=True)
    role: Mapped[str] = mapped_column(String, default="student")  # "student" | "teacher"
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
