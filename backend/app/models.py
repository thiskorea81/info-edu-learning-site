import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    standard_id: Mapped[str] = mapped_column(String, index=True)
    last_selected: Mapped[int] = mapped_column(Integer)
    added_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    problem_id: Mapped[str] = mapped_column(String, index=True)
    code: Mapped[str] = mapped_column(Text)
    verdict: Mapped[str] = mapped_column(String)
    passed_count: Mapped[int] = mapped_column(Integer)
    total_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
