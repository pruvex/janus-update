import pytest
import sys
import os
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# PFAD-FIX: Add the root directory to PYTHONPATH
# This ensures 'backend.data...' is found, even when running pytest from 'tests/'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.data.database import Base
# We mock the Notification Manager to prevent real queues from being created
from backend.services.memory_extractor import notification_manager

# In-Memory SQLite for ultra-fast, isolated tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Creates a fresh database session for EACH test.
    Creates tables before the test and drops them afterward.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def mock_notification_manager(monkeypatch):
    """
    Automatically prevents the real NotificationManager
    from trying to establish SSE connections in ALL tests.
    """
    async def mock_broadcast():
        pass  # Do nothing
    monkeypatch.setattr(notification_manager, "broadcast_refresh", mock_broadcast)
