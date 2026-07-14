from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import UPLOADS_DIR
from .database import Base, engine
from .migrations import run_migrations, run_pre_create_migrations
from .routers import (
    assignments,
    attempts,
    auth,
    code_runner,
    exams,
    materials,
    problems,
    roster,
    stats,
    subject_admin,
    subjects,
    unit_reports,
)

run_pre_create_migrations(engine)
Base.metadata.create_all(bind=engine)
run_migrations(engine)

app = FastAPI(title="정보ON")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(roster.router)
app.include_router(subject_admin.router)
app.include_router(exams.router)
app.include_router(attempts.router)
app.include_router(stats.router)
app.include_router(code_runner.router)
app.include_router(subjects.router)
app.include_router(problems.router)
app.include_router(materials.router)
app.include_router(unit_reports.router)
app.include_router(assignments.router)

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok"}
