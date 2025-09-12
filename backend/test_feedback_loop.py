
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app, get_db
from backend import crud

# --- Testdatenbank-Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Fixtures ---
@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# --- Tests ---
@patch("keyring.get_password", return_value="test_api_key")
@patch("backend.llm_gateway.reason_and_respond", new_callable=AsyncMock)
@patch("backend.memory_extractor.extract_and_save_fact", new_callable=AsyncMock)
def test_feedback_loop_is_triggered_on_confirmation(
    mock_extract_fact: AsyncMock,
    mock_reason_and_respond: AsyncMock,
    mock_get_password,
    client: TestClient,
    db_session,
):
    # 1. Test-Setup: Chat und Nachrichten erstellen
    chat = crud.create_chat(db_session, title="Test Chat")
    crud.create_message(db_session, chat_id=chat.id, sender="model", content="Das ist eine Aussage des Assistenten.")
    
    # Mock-Antwort für reason_and_respond, falls es aufgerufen wird
    mock_reason_and_respond.return_value = {"type": "text", "text": "Okay, verstanden."}

    # 2. Aktion: Eine Bestätigungsnachricht senden
    response = client.post(
        "/api/chat",
        json={
            "prompt": "ja, das stimmt",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "chat_id": chat.id,
        },
    )

    # 3. Überprüfung
    assert response.status_code == 200
    
    # Stelle sicher, dass die Faktenextraktion aufgerufen wurde
    mock_extract_fact.assert_called_once()
    
    # Überprüfe die Argumente, mit denen die Faktenextraktion aufgerufen wurde
    args, kwargs = mock_extract_fact.call_args
    assert kwargs["chat_id"] == chat.id
    assert "Der Benutzer hat die folgende Aussage des Assistenten als korrekt bestätigt: Das ist eine Aussage des Assistenten." in kwargs["text_block"]
    assert kwargs["original_prompt"] == "ja, das stimmt"
