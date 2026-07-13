"""가벼운 수동 마이그레이션.

Base.metadata.create_all()은 없는 테이블만 만들 뿐 기존 테이블의 컬럼을
바꿔주지 않는다. 이 프로젝트는 Alembic 없이 SQLite를 직접 쓰므로,
로그인 기능 추가로 필요해진 user_id 컬럼과 인덱스를 여기서 직접 맞춘다.
새로 만들어지는 DB에서는 모델 정의만으로 이미 맞는 스키마가 생성되므로
아래 구문들은 모두 존재 여부를 먼저 확인하고 없을 때만 실행된다(멱등).
"""

from sqlalchemy import text
from sqlalchemy.engine import Engine


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(row[1] == column for row in rows)


def _index_exists(conn, name: str) -> bool:
    row = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='index' AND name=:name"),
        {"name": name},
    ).fetchone()
    return row is not None


def run_migrations(engine: Engine) -> None:
    with engine.begin() as conn:
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
