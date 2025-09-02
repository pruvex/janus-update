# waechter/test_llm_gateway.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from backend import llm_gateway

@pytest.mark.asyncio
async def test_reason_and_respond_builds_detective_prompt():
    """
    Tests that the 'detective prompt' is correctly assembled.
    """
    user_prompt = "Wer ist mein Onkel und was mag er?"
    memory_context = "- Der Onkel des Benutzers heißt Kalle.\n- Kalle mag die Farbe Blau."
    chat_history = [{"role": "user", "content": "Hallo"}]

    # Mocke Abhängigkeiten, die nicht direkt zum Test gehören
    mock_context_manager = MagicMock()

    with patch('backend.llm_gateway.call_llm', new_callable=AsyncMock) as mock_call_llm:
        mock_call_llm.return_value = {"type": "text", "text": "Dummy"} # Dummy-Antwort für diesen Test

        await llm_gateway.reason_and_respond(
            user_prompt=user_prompt,
            chat_history=chat_history,
            memory_context=memory_context,
            db=MagicMock(),
            api_key="test_key",
            model="test_model",
            provider="test_provider",
            context_manager=mock_context_manager
        )

        # Überprüfe, ob der finale Prompt für das LLM korrekt zusammengebaut wurde
        mock_call_llm.assert_called_once()
        args, kwargs = mock_call_llm.call_args
        final_prompt = args[2] # Argument `prompt` in `call_llm`

        # Prüfe auf die Schlüsselelemente des "Detektiv-Prompts"
        assert "Du bist Janus, ein hilfreicher KI-Detektiv" in final_prompt
        assert "**DEINE GOLDENE REGEL:**" in final_prompt
        assert "--- FAKTEN AUS DEM LANGZEITGEDÄCHTNIS ---" in final_prompt
        assert "- Der Onkel des Benutzers heißt Kalle." in final_prompt
        assert "- Kalle mag die Farbe Blau." in final_prompt
        assert "--- AKTUELLER GESPRÄCHSVERLAUF ---" in final_prompt
        assert "user: Hallo" in final_prompt
        assert "--- FRAGE DES BENUTZERS ---" in final_prompt
        assert "Wer ist mein Onkel und was mag er?" in final_prompt
