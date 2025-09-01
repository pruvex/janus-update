Arbeitsauftrag 4: Implementierung der Pytest-Testinfrastruktur
AGENTIC HANDLUNGSPLAN:
Dein Ziel: Eine robuste Testumgebung für die neue API-Logik schaffen, indem pytest mit einer In-Memory-Datenbank konfiguriert und ein erster Satz von API-Tests implementiert wird.
Relevante PHASE_X.md: REFAKTORING_PLANalt.md (Block 8)
Der Plan:
Stufe 1: Validierung des Ausgangszustands
Führe python health_check.py aus.
Überprüfe das waechter-Verzeichnis mit list_directory.
Stufe 2: Planung & Recherche
Plane die Erstellung der Konfigurationsdatei waechter/conftest.py.
Plane das Überschreiben der alten Testdatei waechter/test_main_api.py mit pytest-kompatiblen Tests.
Stufe 3: Implementierung & Arbeits-Logbuch
Erstelle waechter/conftest.py. Nutze write_file. Inhalt:
code
Python
# waechter/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
from backend.main import app
from backend.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

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
def test_client(db_session):
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with patch('keyring.get_password', return_value='mock_api_key'):
        client = TestClient(app)
        yield client
    del app.dependency_overrides[get_db]
Dokumentiere im AGENT_WORK_LOG.md: "Aktion: waechter/conftest.py erstellt. Grund: Einrichtung der Pytest-Fixtures für eine In-Memory-Datenbank und einen Test-Client, um API-Tests zu isolieren."
Überschreibe waechter/test_main_api.py. Nutze write_file. Inhalt:
code
Python
# waechter/test_main_api.py
from unittest.mock import patch, MagicMock, AsyncMock

def test_chat_text_response(test_client, db_session):
    with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason:
        mock_reason.return_value = {
            "type": "text", "text": "Mocked response.",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            "cost": {"total_cost": 0.0001}
        }
        response = test_client.post("/api/chat", json={
            "prompt": "Hello", "provider": "openai", "model": "gpt-4o-mini"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Mocked response."

def test_chat_image_tool_call(test_client, db_session):
    with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason, \
         patch('backend.tool_registry.TOOL_REGISTRY.get') as mock_get_tool, \
         patch('backend.image_manager.save_image_from_url', new_callable=AsyncMock) as mock_save:

        mock_reason.return_value = {
            "type": "tool_code", "tool_name": "generate_image_tool",
            "tool_args": {"prompt": "a cat"}
        }
        
        mock_tool_func = AsyncMock(return_value={
            "url": "http://example.com/cat.png", "usage": {}, "cost": {"total_cost": 0.04}
        })
        mock_tool = MagicMock()
        mock_tool.func = mock_tool_func
        mock_get_tool.return_value = mock_tool
        
        mock_save.return_value = "/user_images/mocked_cat.png"

        response = test_client.post("/api/chat", json={
            "prompt": "draw a cat", "provider": "openai", "model": "gpt-4o-mini"
        })

        assert response.status_code == 200
        data = response.json()
        assert "Bild wurde erfolgreich generiert" in data["text"]
        assert data["image_url"] == "/user_images/mocked_cat.png"
        mock_tool.func.assert_called_once_with(api_key="mock_api_key", prompt="a cat")
Dokumentiere im AGENT_WORK_LOG.md: "Aktion: waechter/test_main_api.py mit Pytest-Tests überschrieben. Grund: Erstellung von Integrationstests für den neuen API-Flow (Text-Antwort und Tool-Aufruf)."
Stufe 4: Dynamische Verifizierung (Funktionstest)
Führe die neuen Tests aus. Nutze run_shell_command: pytest waechter/test_main_api.py.
Erwartetes Ergebnis: Die Tests sollten erfolgreich durchlaufen ("2 passed"). Dies validiert die gesamte neue Architektur von main.py bis zum Tool-Aufruf.
Stufe 5: Aufräumen & Finale Validierung
Führe python health_check.py erneut aus.
Stufe 6: Archivierung & Lockfile-Garantie (KRITISCHE STUFE)
Führe git add . aus.
Führe git commit -m "test(agent): Implement pytest infrastructure and API tests for Gold Switch" mit run_shell_command aus.
Stufe 7: Dokumentation aktualisieren
Aktualisiere REFAKTORING_PLANalt.md. Setze (Erledigt - mit In-Memory-DB und Pytest) hinter die Aktion "Umfassendes Testen".
Stufe 8: Vorbereitung für die Zukunft
Block 8 ist abgeschlossen. Erstelle einen Branch für den nächsten Block, Block 9. Nutze run_shell_command: git checkout -b "feature/frontend-image-modal".
Erfolgs-Kriterien:
Die Dateien waechter/conftest.py und waechter/test_main_api.py existieren mit dem neuen Inhalt.
Der Befehl pytest wird erfolgreich ausgeführt und alle Tests sind grün.
Finale Erfolgsmeldung:
Arbeitsauftrag 4 und somit Block 8 erfolgreich abgeschlossen. Die neue Architektur ist implementiert, robust und durch automatisierte Tests validiert. Das Backend ist bereit für die Anpassungen am Frontend.