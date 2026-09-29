"""Database engine and session management.

The database URL is configurable; SQLite is the default for the MVP. Schema
creation is centralised here so tests can point at a throwaway database.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

# Importing the models package registers all tables on SQLModel.metadata.
import app.models  # noqa: F401  (side-effect import)

connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args,
)


def create_all() -> None:
    """Create any missing tables. Safe to call repeatedly."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    with Session(engine) as session:
        yield session


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context-managed session for scripts and services outside a request."""
    with Session(engine) as session:
        yield session
