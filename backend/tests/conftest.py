# backend/tests/conftest.py
import os
import sys
from unittest.mock import patch

import pytest

# --- PATH FIX START (Goldstandard für Robustheit) ---
# Wir ermitteln den Pfad zu dieser Datei (conftest.py)
current_test_dir = os.path.dirname(os.path.abspath(__file__))
# Wir ermitteln den 'backend' Ordner (ein Level höher)
backend_dir = os.path.dirname(current_test_dir)
# Wir ermitteln das Projekt-Root (noch ein Level höher)
project_root = os.path.dirname(backend_dir)

# Wir fügen Projekt-Root hinzu, damit 'from backend.main import ...' funktioniert
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Wir fügen backend_dir hinzu, damit Importe innerhalb von backend funktionieren
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
# --- PATH FIX END ---

# Jetzt können wir sicher importieren
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Wir nutzen try-except für Importe, um flexibler zu sein
try:
    from backend.data.database import Base, get_db
    from backend.main import app
except ImportError:
    # Fallback, falls wir direkt im backend ordner sind und 'backend.' Prefix stört
    from data.database import Base, get_db
    from main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Erstellt die Datenbank-Tabellen für die Tests und räumt danach auf."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Erstellt eine frische Datenbank-Session für jeden Test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_client(db_session):
    """Erstellt einen Test-Client mit gemockter DB und Auth."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # Wir mocken keyring, damit keine echten Passwörter abgefragt werden
    with patch("keyring.get_password", return_value="mock_api_key"):
        client = TestClient(app)
        yield client
    del app.dependency_overrides[get_db]
