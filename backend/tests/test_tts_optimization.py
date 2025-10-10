import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
import shutil
from pathlib import Path

# Import the main FastAPI app
from backend.main import app
from backend.services.tts_service import TTS_CACHE_DIR
from backend.tts_providers.piper import apply_basic_normalization # Import the normalization function

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_tts_cache():
    # Ensure cache directory exists before tests
    TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Clean up cache directory after tests
    if TTS_CACHE_DIR.exists():
        shutil.rmtree(TTS_CACHE_DIR)


@pytest.fixture
def mock_piper_tts_available():
    with patch('backend.tts_providers.piper.PiperTTS.is_available', return_value=True) as mock_is_available:
        with patch('backend.tts_providers.piper.PiperTTS.list_voices', return_value=[
            {"id": "de_DE-thorsten-high", "name": "Thorsten High", "lang": "de", "path": "/mock/path/thorsten.onnx"}
        ]) as mock_list_voices:
            with patch('backend.tts_providers.piper.PiperTTS.synthesize', return_value=b"mock_wav_data") as mock_synthesize:
                with patch('backend.services.tts_service.TTSService._select_provider_chain', return_value=["piper"]) as mock_select_provider_chain:
                    yield mock_is_available, mock_list_voices, mock_synthesize, mock_select_provider_chain


@pytest.fixture
def mock_silero_tts_available():
    with patch('backend.tts_providers.silero.SileroTTS.is_available', return_value=True) as mock_is_available:
        with patch('backend.tts_providers.silero.SileroTTS.synthesize', return_value=b"mock_wav_data_silero") as mock_synthesize:
            with patch('backend.services.tts_service.TTSService._select_provider_chain', return_value=["silero"]) as mock_select_provider_chain:
                with patch('backend.tts_providers.silero.SileroTTS.list_voices', return_value=[
                    {"id": "de_random", "name": "Deutsch Silero (Zufällig)", "lang": "de", "provider": "silero", "speaker": "random"}
                ]) as mock_silero_list_voices:
                    with patch('backend.services.tts_service.TTSService.get_voices', return_value=[
                        {"id": "silero_de_random", "name": "Silero Deutsch (Zufällig)", "lang": "de", "provider": "silero", "speaker": "random"}
                    ]) as mock_tts_service_get_voices:
                        yield mock_is_available, mock_synthesize, mock_select_provider_chain, mock_silero_list_voices, mock_tts_service_get_voices

def test_get_tts_voices_contains_thorsten(mock_piper_tts_available):
    mock_is_available, mock_list_voices, mock_synthesize, mock_select_provider_chain = mock_piper_tts_available
    response = client.get("/api/tts/voices")
    assert response.status_code == 200
    voices = response.json()["voices"]
    assert any(v["id"] == "piper_de_DE-thorsten-high" for v in voices)
    assert any(v["name"] == "Piper Thorsten High" for v in voices)

def test_synthesize_speech_with_preset(mock_piper_tts_available):
    mock_is_available, mock_list_voices, mock_synthesize, mock_select_provider_chain = mock_piper_tts_available
    
    # Test with 'assistenz' preset
    response_assistenz = client.post(
        "/api/tts/synthesize",
        params={
            "text": "Hallo Welt",
            "lang": "de",
            "voice_id": "piper_de_DE-thorsten-high",
            "preset": "assistenz"
        }
    )
    assert response_assistenz.status_code == 200
    assert response_assistenz.content == b"mock_wav_data"
    mock_synthesize.assert_called_with(
        text="Hallo Welt",
        voice="de_DE-thorsten-high", # Hier muss es de_DE-thorsten-high sein, da der Piper-Provider das Präfix entfernt
        lang="de",
        speed=1.0,
        fmt="mp3",
        preset_name="assistenz"
    )
    mock_synthesize.reset_mock()

    # Test with 'diktat' preset
    response_diktat = client.post(
        "/api/tts/synthesize",
        params={
            "text": "Hallo Welt",
            "lang": "de",
            "voice_id": "piper_de_DE-thorsten-high",
            "preset": "diktat"
        }
    )
    assert response_diktat.status_code == 200
    assert response_diktat.content == b"mock_wav_data"
    mock_synthesize.assert_called_with(
        text="Hallo Welt",
        voice="de_DE-thorsten-high", # Hier muss es de_DE-thorsten-high sein
        lang="de",
        speed=1.0,
        fmt="mp3",
        preset_name="diktat"
    )

def test_synthesize_speech_caching(mock_piper_tts_available):
    mock_is_available, mock_list_voices, mock_synthesize, mock_select_provider_chain = mock_piper_tts_available

    # First call - should synthesize
    response1 = client.post(
        "/api/tts/synthesize",
        params={
            "text": "Hallo Cache",
            "lang": "de",
            "voice_id": "piper_de_DE-thorsten-high",
            "preset": "assistenz"
        }
    )
    assert response1.status_code == 200
    assert mock_synthesize.call_count == 1
    mock_synthesize.reset_mock()

    # Second call with same parameters - should hit cache, not synthesize again
    response2 = client.post(
        "/api/tts/synthesize",
        params={
            "text": "Hallo Cache",
            "lang": "de",
            "voice_id": "piper_de_DE-thorsten-high",
            "preset": "assistenz"
        }
    )
    assert response2.status_code == 200
    assert mock_synthesize.call_count == 0  # Should not be called again
    assert response1.content == response2.content # Content should be the same

def test_synthesize_speech_empty_text_error():
    response = client.post("/api/tts/synthesize", params={"text": "", "lang": "de"})
    assert response.status_code == 400
    assert "Text cannot be empty" in response.json()["detail"]

def test_synthesize_speech_piper_not_available(mock_piper_tts_available, mock_silero_tts_available):
    mock_is_available, mock_list_voices, mock_synthesize, mock_select_provider_chain = mock_piper_tts_available
    mock_silero_is_available, mock_silero_synthesize, mock_silero_select_provider_chain, mock_silero_list_voices, mock_tts_service_get_voices = mock_silero_tts_available
    # Mock the provider chain to select Silero when Piper is unavailable
    with patch('backend.services.tts_service.TTSService._select_provider_chain', return_value=["silero"]):
        with patch('backend.tts_providers.piper.PiperTTS.is_available', return_value=False):
            response = client.post(
                "/api/tts/synthesize",
                params={
                    "text": "Test",
                    "lang": "de",
                    "voice_id": "silero_de_random",
                    "preset": "assistenz"
                }
            )
            assert response.status_code == 200
            assert response.content == b"mock_wav_data_silero"
            mock_silero_synthesize.assert_called_once()

def test_synthesize_speech_unknown_voice():
    response = client.post(
        "/api/tts/synthesize",
        params={
            "text": "Test",
            "lang": "de",
            "voice_id": "unknown_voice",
            "preset": "assistenz"
        }
    )
    assert response.status_code == 400
    assert "Unknown voice: unknown_voice" in response.json()["detail"]


def test_normalization_applied(mock_piper_tts_available):
    mock_is_available, mock_list_voices, mock_synthesize, mock_select_provider_chain = mock_piper_tts_available

    test_text = "z.B. ca. 10% u.a. in €"

    client.post(
        "/api/tts/synthesize",
        params={
            "text": test_text,
            "lang": "de",
            "voice_id": "piper_de_DE-thorsten-high",
            "preset": "assistenz"
        }
    )
    # Verify that the synthesize method was called with the normalized text
    mock_synthesize.assert_called_once()
    call_args = mock_synthesize.call_args[1]
    assert call_args["text"] == apply_basic_normalization(test_text)

def test_ordinal_normalization(mock_piper_tts_available):
    mock_is_available, mock_list_voices, mock_synthesize, mock_select_provider_chain = mock_piper_tts_available

    test_text = "Am den 10. Oktober"

    client.post(
        "/api/tts/synthesize",
        params={
            "text": test_text,
            "lang": "de",
            "voice_id": "piper_de_DE-thorsten-high",
            "preset": "assistenz"
        }
    )
    # Verify that the synthesize method was called with the normalized text
    mock_synthesize.assert_called_once()
    call_args = mock_synthesize.call_args[1]
    assert call_args["text"] == "Am den zehnten Oktober"