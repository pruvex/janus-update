from typing import Optional, Generator


class TTSProviderBase:
    """Base class for all TTS providers."""
    name = "base"

    def voices(self):
        """Return available voices for this provider."""
        return []

    def supports_streaming(self, fmt: str) -> bool:
        """Check if provider supports streaming for the given format."""
        return False

    def synthesize(self, text: str, voice: str, lang: str, speed: float, fmt: str) -> bytes:
        """Synthesize speech from text and return audio bytes."""
        raise NotImplementedError

    def synthesize_stream(self, text: str, voice: str, lang: str, speed: float, fmt: str) -> Generator[bytes, None, None]:
        """Synthesize speech from text and return audio stream."""
        raise NotImplementedError
