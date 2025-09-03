import pytest
from unittest.mock import AsyncMock, patch
from backend import memory_extractor


@pytest.mark.asyncio
@patch('backend.crud.save_memory_snippet')
@patch('backend.llm_gateway.call_llm')
async def test_extracts_and_saves_relevant_fact(mock_call_llm, mock_save_snippet, db_session):
    """
    Testet, ob ein relevanter Fakt korrekt extrahiert und gespeichert wird.
    """
    # 1. Mock-Setup: Simuliere, dass das LLM einen relevanten Fakt zurückgibt.
    mock_call_llm.return_value = {"text": "Der Benutzer bevorzugt die Farbe Blau."}
        
    # 2. Aktion: Rufe die zu testende Funktion auf.
    text_block = "User: Ich mag Blau. Assistant: Verstanden."
    result = await memory_extractor.extract_and_save_fact(db_session, chat_id=1, text_block=text_block, api_key="dummy_key")

    # 3. Überprüfung:
    # Wurde die LLM-Gateway-Funktion aufgerufen?
    mock_call_llm.assert_called_once()
    # Wurde die Speicher-Funktion mit dem extrahierten Fakt aufgerufen?
    mock_save_snippet.assert_called_once_with(db_session, chat_id=1, snippet_text="Der Benutzer bevorzugt die Farbe Blau.")
    # Gibt die Funktion den extrahierten Fakt zurück?
    assert result == "Der Benutzer bevorzugt die Farbe Blau."


@pytest.mark.asyncio
@patch('backend.crud.save_memory_snippet')
@patch('backend.llm_gateway.call_llm')
async def test_ignores_irrelevant_text(mock_call_llm, mock_save_snippet, db_session):
    """
    Testet, ob bei irrelevantem Text nichts gespeichert wird.
    """
    # 1. Mock-Setup: Simuliere, dass das LLM "None" zurückgibt.
    mock_call_llm.return_value = {"text": "None"}
        
    # 2. Aktion: Rufe die zu testende Funktion auf.
    text_block = "User: Hallo. Assistant: Wie geht es Ihnen?"
    result = await memory_extractor.extract_and_save_fact(db_session, chat_id=1, text_block=text_block, api_key="dummy_key")

    # 3. Überprüfung:
    # Wurde die LLM-Gateway-Funktion aufgerufen?
    mock_call_llm.assert_called_once()
    # Wurde die Speicher-Funktion NICHT aufgerufen?
    mock_save_snippet.assert_not_called()
    # Gibt die Funktion None zurück?
    assert result is None