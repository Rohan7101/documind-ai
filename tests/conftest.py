import os
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app


@pytest.fixture
def test_storage(tmp_path: pytest.TempPathFactory) -> str:
    """Create a temporary storage directory for each test."""
    temp_dir = tmp_path / "storage"
    temp_dir.mkdir(parents=True, exist_ok=True)
    orig_storage = settings.STORAGE_DIR
    settings.STORAGE_DIR = str(temp_dir)
    yield str(temp_dir)
    settings.STORAGE_DIR = orig_storage



@pytest.fixture
def db_session(tmp_path: pytest.TempPathFactory) -> Generator[Session, None, None]:
    """Create an isolated SQLite database session for each test function."""
    test_db_file = tmp_path / "test_documind.db"
    test_db_url = f"sqlite:///{test_db_file}"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(db_session: Session, test_storage: str) -> Generator[TestClient, None, None]:
    """TestClient configured with overridden test database session."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
