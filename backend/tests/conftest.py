"""Test configuration.

Environment is forced here, before any application module is imported, so the
test run never touches the development database and never picks up real
credentials. The settings singleton is created on first import, which is why
this file must set the environment before importing anything from ``app``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

BACKEND_ROOT = Path(__file__).resolve().parent.parent
TEST_DB = BACKEND_ROOT / "test_incidents.db"

# Force an isolated, offline configuration.
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["APP_ENV"] = "test"
os.environ["DEMO_MODE"] = "true"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["LOG_JSON"] = "false"
os.environ["GROQ_API_KEY"] = ""
os.environ["HINDSIGHT_BASE_URL"] = ""
os.environ["HINDSIGHT_API_KEY"] = ""
os.environ["MEMORY_PROVIDER"] = "auto"
os.environ["LLM_PROVIDER"] = "auto"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.database import create_all, engine  # noqa: E402
from app.main import app  # noqa: E402
from seed.seed_incidents import reset_and_seed  # noqa: E402

get_settings.cache_clear()


def pytest_sessionstart(session) -> None:
    if TEST_DB.exists():
        TEST_DB.unlink()
    create_all()


def pytest_sessionfinish(session, exitstatus) -> None:
    # Dispose the engine first: on Windows an open handle blocks the unlink.
    engine.dispose()
    if TEST_DB.exists():
        try:
            TEST_DB.unlink()
        except OSError:
            pass


@pytest.fixture()
def session() -> Iterator[Session]:
    """A clean database seeded with the reference corpus."""
    with Session(engine) as db:
        reset_and_seed(db)
        yield db


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """A TestClient over a freshly seeded database."""
    with Session(engine) as db:
        reset_and_seed(db)
    with TestClient(app) as test_client:
        yield test_client
