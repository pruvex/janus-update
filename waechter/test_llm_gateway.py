# waechter/test_llm_gateway.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from backend import llm_gateway

@pytest.mark.asyncio
async def test_reason_and_respond_builds_correct_prompt():
    # Testet, ob der "Detektiv-Prompt" korrekt zusammengebaut wird

    user_prompt = "Wer ist mein Onkel?"
    memory_context = "- Der Onkel des Benutzers heißt Kalle."
    chat_history = [{"role": "user", "content": "Hallo"}]

    # Mocke die Abhängigkeiten, die nicht direkt getestet werden
    mock_context_manager = MagicMock()
    mock_context_manager.build_final_context = AsyncMock(return_value=chat_history) # Simpler Mock
    with patch('backend.llm_gateway.call_llm', new_callable=AsyncMock) as mock_call_llm:
        mock_call_llm.return_value = {"type": "text", "text": "Test"} # Dummy-Antwort

        await llm_gateway.reason_and_respond(
            user_prompt=user_prompt,
            chat_history=chat_history,
            memory_context=memory_context,
            db=MagicMock(),
            api_key="test",
            model="test",
            provider="test",
            context_manager=mock_context_manager
        )

        # Überprüfe, ob call_llm mit dem korrekt zusammengebauten Master-Prompt aufgerufen wurde
        mock_call_llm.assert_called_once()
        args, kwargs = mock_call_llm.call_args
        final_prompt = args[2] # Das ist der final_prompt_for_llm

        assert "Du bist Janus, ein hilfreicher KI-Detektiv" in final_prompt
        assert "--- FAKTEN AUS DEM LANGZEITGEDÄCHTNIS ---" in final_prompt
        assert "- Der Onkel des Benutzers heißt Kalle." in final_prompt
        assert "--- AKTUELLER GESPRÄCHSVERLAUF ---" in final_prompt
        assert "user: Hallo" in final_prompt
        assert "--- FRAGE DES BENUTZERS ---" in final_prompt
        assert "Wer ist mein Onkel?" in final_prompt