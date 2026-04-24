"""Pytest configuration and fixtures for testing."""
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app


@pytest.fixture
def session(tmp_path: Path) -> Generator[Session, None, None]:
    """Sync session for seeding test data into the shared test database."""
    db_path = tmp_path / "test.db"
    sync_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(sync_engine)
    with Session(sync_engine) as session:
        yield session
    sync_engine.dispose()


@pytest.fixture
def client(tmp_path: Path, session: Session) -> Generator[TestClient, None, None]:
    """Test client backed by the same SQLite file as the session fixture."""
    db_path = tmp_path / "test.db"
    async_engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    async_session_factory = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def get_session_override() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as s:
            yield s

    app.dependency_overrides[get_session] = get_session_override
    with patch("app.main.create_tables", new_callable=AsyncMock):
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.clear()
