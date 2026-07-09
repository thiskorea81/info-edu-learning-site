from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent

DATA_DIR = REPO_ROOT / "data"
QUESTIONS_DIR = DATA_DIR / "questions"
STANDARDS_FILE = DATA_DIR / "standards.json"
PROBLEMS_DIR = DATA_DIR / "problems"
USER_QUESTIONS_FILE = QUESTIONS_DIR / "user_added.json"
MATERIALS_DIR = DATA_DIR / "materials"

DATABASE_URL = f"sqlite:///{DATA_DIR / 'study.db'}"
