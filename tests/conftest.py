"""Pytest fixtures.

Each test runs against a fresh in-memory SQLite database. The app's `get_db`
dependency is overridden so route handlers use the test session.
"""

import os

# Provide required configuration *before* the app (and its cached Settings) is
# imported, so the suite is fully self-contained and never depends on a local
# .env file. SECRET_KEY is intentionally required in production.
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    # StaticPool + a shared in-memory connection keeps the same database alive
    # for the duration of one test across threads.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    """Register + log in a user and return ready-to-use auth headers."""
    email, password = "tester@example.com", "supersecret123"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
