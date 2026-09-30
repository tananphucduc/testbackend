from fastapi import FastAPI

from app.core.database import engine, Base
from app.models import user, task  # noqa: F401 — ensure models are registered
from app.routers import auth, tasks

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Management API", version="1.0.0")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "Task Management API is running"}
