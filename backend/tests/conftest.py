# backend/tests/conftest.py

import sys
import os
import json

os.environ.setdefault("JANUS_DISABLE_SENTRY", "1")

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
import backend.data.models  # noqa: F401 — register all ORM tables on Base.metadata for create_all
from backend import tool_registry
from backend.services.skill_router import skill_router
from backend.services import filesystem_manager
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


@pytest.fixture(scope="function", autouse=True)
def registered_tools():
    """Stellt sicher, dass alle Tools/Skills für Contract-Tests registriert sind."""
    tool_registry.register_all_tools()
    yield


@pytest.fixture(scope="function")
def isolated_workspace(tmp_path, monkeypatch):
    """Virtueller Workspace für sichere filesystem.* Tests ohne Side-Effects."""
    workspace = (tmp_path / "workspace").resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(filesystem_manager, "_get_allowed_workspaces", lambda: [workspace])
    return workspace


@pytest.fixture(scope="function")
def skill_router_instance():
    """Gibt die aktive SkillRouter-Instanz für Mapping/Dead-Link-Tests zurück."""
    return skill_router


@pytest.fixture(scope="function")
def assert_skill_response_contract():
    """Helper: validiert das SkillResponse-Contract-Grundschema."""

    def _assert(payload):
        if isinstance(payload, str):
            payload = json.loads(payload)
        assert isinstance(payload, dict)
        assert payload.get("status") in {"ok", "error", "permission_required", "dry_run_success"}
        if payload.get("status") in {"ok", "dry_run_success"}:
            assert "data" in payload
        else:
            assert "error" in payload

    return _assert

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
