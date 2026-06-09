"""Application entrypoint and FastAPI app factory.

Wires together configuration, database initialization, routers, and a small
amount of cross-cutting concern handling (CORS, a health check, and a uniform
validation-error shape).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Importing the models package registers every ORM model on Base.metadata.
from app import models  # noqa: F401
from app.api.routes import auth, tasks
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create database tables on startup.

    For a portfolio/demo app this is convenient and self-contained. A
    production system would manage schema with Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=(
        "A small, production-structured REST API for managing personal tasks, "
        "secured with JWT authentication."
    ),
    lifespan=lifespan,
)

# CORS is restricted to an explicit allow-list of origins (configurable via
# BACKEND_CORS_ORIGINS) rather than a wildcard, which would be unsafe alongside
# credentialed requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a consistent JSON envelope for input-validation failures."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.get("/health", tags=["system"], summary="Liveness/readiness probe")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.ENVIRONMENT}


app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(tasks.router, prefix=settings.API_V1_PREFIX)
