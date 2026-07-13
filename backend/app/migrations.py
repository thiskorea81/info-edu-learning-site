"""가벼운 수동 마이그레이션 + 초기 시드.

Base.metadata.create_all()은 없는 테이블만 만들 뿐 기존 테이블의 컬럼을
바꿔주지 않는다. 이 프로젝트는 Alembic 없이 SQLite를 직접 쓰므로,
로그인 기능 추가로 필요해진 스키마 변경을 여기서 직접 맞춘다.
"""

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session as DBSession

from . import data_loader
from .passwords import DEFAULT_PASSWORD, hash_password


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(row[1] == column for row in rows)


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table},
    ).fetchone()
    return row is not None


def _index_exists(conn, name: str) -> bool:
    row = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='index' AND name=:name"),
        {"name": name},
    ).fetchone()
    return row is not None


def _reset_legacy_users_table(conn) -> None:
    """(name, number) 기반 구버전 users 테이블이면 통째로 새로 만든다.

    학번/비밀번호 스키마로 구조 자체가 바뀌었고, 이 시점에 users 테이블에는
    테스트용 교사 계정 1개만 있었으므로 데이터 보존보다 단순 재생성이 안전하다.
    attempts/submissions/wrong_notes의 user_id는 nullable FK라 재생성해도
    깨지지 않는다(기존 행은 그대로 고아 상태로 남아 아무에게도 보이지 않는다).
    """
    if _table_exists(conn, "users") and not _column_exists(conn, "users", "login_id"):
        conn.execute(text("DROP TABLE IF EXISTS sessions"))
        conn.execute(text("DROP TABLE IF EXISTS users"))


def _migrate_attempt_tables(conn) -> None:
    for table in ("attempts", "submissions", "wrong_notes"):
        if not _column_exists(conn, table, "user_id"):
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER REFERENCES users(id)"))

    if _index_exists(conn, "ix_wrong_notes_question_id"):
        conn.execute(text("DROP INDEX ix_wrong_notes_question_id"))

    if not _index_exists(conn, "ix_wrong_notes_user_question"):
        conn.execute(
            text(
                "CREATE UNIQUE INDEX ix_wrong_notes_user_question "
                "ON wrong_notes (user_id, question_id)"
            )
        )


def run_pre_create_migrations(engine: Engine) -> None:
    """Base.metadata.create_all() 이전에 실행: 구버전 테이블 정리."""
    with engine.begin() as conn:
        _reset_legacy_users_table(conn)


def run_post_create_migrations(engine: Engine) -> None:
    """Base.metadata.create_all() 이후에 실행: 컬럼 보정."""
    with engine.begin() as conn:
        _migrate_attempt_tables(conn)


def seed_defaults(engine: Engine) -> None:
    """관리자 교사 계정과 커리큘럼 과목이 없으면 만들어 둔다."""
    from .models import Subject, User

    with DBSession(engine) as db:
        admin = db.query(User).filter(User.is_admin == True).first()  # noqa: E712
        if admin is None:
            admin = db.query(User).filter(User.login_id == "teacher").first()
            if admin is None:
                admin = User(
                    login_id="teacher",
                    name="선생님",
                    password_hash=hash_password(DEFAULT_PASSWORD),
                    role="teacher",
                    is_admin=True,
                    must_change_password=True,
                )
                db.add(admin)
                db.commit()
                db.refresh(admin)
            else:
                admin.is_admin = True
                db.commit()

        existing_subjects = {s.name for s in db.query(Subject).all()}
        curriculum_subjects = sorted({s["교과"] for s in data_loader.load_standards()})
        for name in curriculum_subjects:
            if name not in existing_subjects:
                db.add(Subject(name=name, teacher_id=admin.id))
        db.commit()


def run_migrations(engine: Engine) -> None:
    run_post_create_migrations(engine)
    seed_defaults(engine)
