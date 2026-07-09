from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import attempts, code_runner, exams, problems, stats, subjects

Base.metadata.create_all(bind=engine)

app = FastAPI(title="정보교육학습사이트")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(exams.router)
app.include_router(attempts.router)
app.include_router(stats.router)
app.include_router(code_runner.router)
app.include_router(subjects.router)
app.include_router(problems.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
