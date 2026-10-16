import os

# Never let the test run touch a real Postgres, even if DATABASE_URL is exported in the shell
os.environ["DATABASE_URL"] = "sqlite://"

from datetime import UTC, datetime, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    # fresh in-memory database for every test so tests can't leak into each other
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def doctor(client):
    res = client.post(
        "/api/doctors",
        json={"full_name": "Dr. Test Doctor", "specialty": "General Medicine", "room": "101"},
    )
    assert res.status_code == 201
    return res.json()


@pytest.fixture()
def slot():
    """A timestamp tomorrow at 10:00 UTC, far enough ahead to be a valid booking."""
    tomorrow = datetime.now(UTC).date() + timedelta(days=1)
    return datetime(tomorrow.year, tomorrow.month, tomorrow.day, 10, 0, tzinfo=UTC)


@pytest.fixture()
def book(client, doctor, slot):
    def _book(**overrides):
        body = {
            "patient_name": "Riya Sharma",
            "patient_phone": "+91 98765 43210",
            "doctor_id": doctor["id"],
            "scheduled_at": slot.isoformat(),
            "duration_minutes": 20,
            "reason": "Fever since two days",
        }
        body.update(overrides)
        return client.post("/api/appointments", json=body)

    return _book
