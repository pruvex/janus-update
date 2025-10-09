import unittest
import os
import sqlite3
from datetime import datetime
from fastapi.testclient import TestClient
from backend.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.data.database import Chat, Message, get_db, SessionLocal, engine, Base
from unittest.mock import patch, AsyncMock


class TestChatAPI(unittest.TestCase):
    def setUp(self):
        self.test_db_path = f"test_chat_{os.getpid()}.db"
        self.test_db_url = f"sqlite:///{self.test_db_path}"

        # Temporäre Engine und SessionLocal für den Test
        self.test_engine = create_engine(
            self.test_db_url, connect_args={"check_same_thread": False}
        )
        self.TestSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.test_engine
        )

        Base.metadata.create_all(bind=self.test_engine)

        # Override the dependency for get_db
        def override_get_db():
            try:
                db = self.TestSessionLocal()
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        # Drop all tables and close the engine
        Base.metadata.drop_all(bind=self.test_engine)
        self.test_engine.dispose()

        # Remove the temporary database file
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_create_chat(self):
        response = self.client.post("/api/chats", json={"title": "Test Chat"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "Test Chat")

    def test_get_all_chats(self):
        self.client.post("/api/chats", json={"title": "Chat 1"})
        self.client.post("/api/chats", json={"title": "Chat 2"})

        response = self.client.get("/api/chats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["title"], "Chat 1")
        self.assertEqual(data[1]["title"], "Chat 2")

    def test_add_message_to_chat(self):
        chat_response = self.client.post(
            "/api/chats", json={"title": "Message Test Chat"}
        )
        chat_id = chat_response.json()["id"]

        message_response = self.client.post(
            f"/api/chats/{chat_id}/messages",
            json={"sender": "user", "content": "Hello, world!"},
        )
        self.assertEqual(message_response.status_code, 200)
        data = message_response.json()
        self.assertIn("id", data)
        self.assertEqual(data["chat_id"], chat_id)
        self.assertEqual(data["sender"], "user")
        self.assertEqual(data["content"], "Hello, world!")

    def test_get_chat_messages(self):
        chat_response = self.client.post(
            "/api/chats", json={"title": "Messages Retrieval Test"}
        )
        chat_id = chat_response.json()["id"]

        self.client.post(
            f"/api/chats/{chat_id}/messages",
            json={"sender": "user", "content": "First message"},
        )
        self.client.post(
            f"/api/chats/{chat_id}/messages",
            json={"sender": "model", "content": "Second message"},
        )

        response = self.client.get(f"/api/chats/{chat_id}/messages")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["content"], "First message")
        self.assertEqual(data[1]["content"], "Second message")

    @patch("keyring.get_password")
    @patch("backend.llm_gateway.call_llm", new_callable=AsyncMock)
    def test_chat_with_history(self, mock_call_llm, mock_get_password):
        mock_get_password.return_value = "mocked-api-key"
        mock_call_llm.return_value = {
            "text": "mocked LLM answer",
            "usage": {"input_tokens": 10, "output_tokens": 20},
            "cost": {"total_cost": 0.001},
        }

        chat_response = self.client.post(
            "/api/chats", json={"title": "History Test Chat"}
        )
        chat_id = chat_response.json()["id"]

        # First message in chat
        response = self.client.post(
            "/api/chat",
            json={
                "prompt": "User message 1",
                "provider": "test-provider",
                "model": "test-model",
                "chat_id": chat_id,
            },
        )
        self.assertEqual(response.status_code, 200)

        # Second message in chat
        response = self.client.post(
            "/api/chat",
            json={
                "prompt": "User message 2",
                "provider": "test-provider",
                "model": "test-model",
                "chat_id": chat_id,
            },
        )
        self.assertEqual(response.status_code, 200)

        # Verify messages are saved in DB via API
        messages_response = self.client.get(f"/api/chats/{chat_id}/messages")
        self.assertEqual(messages_response.status_code, 200)
        messages = messages_response.json()

        self.assertEqual(len(messages), 4)  # 2 user messages + 2 model responses
        self.assertEqual(messages[0]["content"], "User message 1")
        self.assertEqual(messages[1]["content"], "mocked LLM answer")
        self.assertEqual(messages[2]["content"], "User message 2")
        self.assertEqual(messages[3]["content"], "mocked LLM answer")


if __name__ == "__main__":
    unittest.main()
