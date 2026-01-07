# backend/tests/conftest.py

import sys
import os

# --- HIER IST DIE KORREKTUR ---
# Fügt das Projekt-Stammverzeichnis (C:\KI\Janus-Projekt) zum Suchpfad hinzu.
# Dies muss GANZ AM ANFANG stehen, vor allen anderen Imports.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- ENDE DER KORREKTUR ---


# Jetzt können die restlichen Imports folgen, und sie werden funktionieren.
# Wir korrigieren hier auch den relativen Import zu einem absoluten.

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# KORRIGIERTER IMPORT:
from backend.data.database import Base, get_db
# ALT (falsch): from data.database import Base, get_db

from backend.main import app


# --- Der Rest deiner conftest.py Datei ---

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Erstellt die Datenbank-Tabellen für die Tests und räumt danach auf."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def test_client(db_session):
    """Create a test client that uses the_session fixture."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # Wir mocken keyring, damit keine echten Passwörter abgefragt werden
    with patch("keyring.get_password", return_value="mock_api_key"):
        client = TestClient(app)
        yield client
    del app.dependency_overrides[get_db]
