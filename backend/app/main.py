from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .routers import appointments, doctors

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Appointment booking API for a small multi-doctor clinic.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schema is owned by Alembic (the container runs `alembic upgrade head` before uvicorn),
# so the app never calls create_all itself.
Instrumentator(
    excluded_handlers=["/metrics", "/health", "/ready"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.include_router(doctors.router)
app.include_router(appointments.router)


@app.get("/", tags=["meta"])
def root():
    return {"service": settings.app_name, "version": settings.app_version, "docs": "/docs"}


@app.get("/health", tags=["meta"])
def health():
    # liveness: the process is up and answering, nothing else
    return {"status": "UP"}


@app.get("/ready", tags=["meta"])
def ready(db: Session = Depends(get_db)):
    # readiness: only take traffic once the database answers
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "NOT_READY", "database": "unreachable"})
    return {"status": "READY", "database": "ok"}
