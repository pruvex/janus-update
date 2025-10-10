import os
import io
import logging
from typing import Optional, List, Dict
from pydub import AudioSegment
from openai import OpenAI

from backend.tts_providers.base import TTSProviderBase

logger = logging.getLogger("janus_backend")

class OpenAITTS(TTSProviderBase):
    """OpenAI TTS Provider - Uses OpenAI's GPT-4o mini TTS model."""
    name = "openai"

    def __init__(self):
        self.client = OpenAI()
        self.available_voices = [
            {"id": "alloy", "name": "Alloy", "lang": "en", "provider": "openai"},
            {"id": "ash", "name": "Ash", "lang": "en", "provider": "openai"},
            {"id": "ballad", "name": "Ballad", "lang": "en", "provider": "openai"},
            {"id": "coral", "name": "Coral", "lang": "en", "provider": "openai"},
            {"id": "echo", "name": "Echo", "lang": "en", "provider": "openai"},
            {"id": "fable", "name": "Fable", "lang": "en", "provider": "openai"},
            {"id": "nova", "name": "Nova", "lang": "en", "provider": "openai"},
            {"id": "onyx", "name": "Onyx", "lang": "en", "provider": "openai"},
            {"id": "sage", "name": "Sage", "lang": "en", "provider": "openai"},
            {"id": "shimmer", "name": "Shimmer", "lang": "en", "provider": "openai"},
        ]
        # Note: OpenAI TTS is primarily optimized for English. Lang is hardcoded for now.

    def is_available(self) -> bool:
        """Check if OpenAI TTS is available (i.e., API key is configured)."""
        # For now, we assume it's available if the client can be initialized.
        # A more robust check would involve a dummy API call.
        return True # Assuming API key is handled at a higher level

    def list_voices(self) -> List[Dict]:
        """List available OpenAI TTS voices."""
        return self.available_voices

    def supports_streaming(self, fmt: str) -> bool:
        # OpenAI TTS supports streaming for certain formats, but for simplicity, we'll treat it as non-streaming for now.
        return False

    def synthesize(self, text: str, voice: str, lang: str, speed: float, fmt: str, preset_name: Optional[str] = None) -> bytes:
        """Synthesize speech using OpenAI TTS."""
        try:
            # OpenAI TTS model is gpt-4o-mini-tts
            response = self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=voice, # Use the provided voice ID
                input=text,
                response_format=fmt, # mp3, opus, aac, flac, wav, pcm
                speed=speed # 0.25 to 4.0
            )
            return response.content
        except Exception as e:
            logger.error(f"OpenAI TTS synthesis failed: {e}")
            raise

    # OpenAI TTS does not directly expose a streaming method in this simple client setup.
    # The `with_streaming_response.create` is for advanced usage and would require a different integration.
    # For now, we'll rely on the non-streaming `synthesize` method.
    def synthesize_stream(self, text: str, voice: str, lang: str, speed: float, fmt: str, preset_name: Optional[str] = None):
        raise NotImplementedError("OpenAI TTS streaming is not yet implemented.")
