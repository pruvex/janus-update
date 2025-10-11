from abc import ABC, abstractmethod
from typing import Optional, Generator, List, Dict


class TTSProviderBase(ABC):
    """Abstract base class for all TTS providers."""
    name = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available (e.g., binary exists, API key is set)."""
        raise NotImplementedError

    @abstractmethod
    def list_voices(self) -> List[Dict]:
        """Return a list of available voices for this provider."""
        raise NotImplementedError

    def supports_streaming(self, fmt: str) -> bool:
        """Check if the provider supports streaming for the given format."""
        return False

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: str,
        lang: str,
        speed: float,
        fmt: str,
        preset_name: Optional[str] = None,
    ) -> bytes:
        """Synthesize speech from text and return audio bytes."""
        raise NotImplementedError

    @abstractmethod
    def synthesize_stream(
        self,
        text: str,
        voice: str,
        lang: str,
        speed: float,
        fmt: str,
        preset_name: Optional[str] = None,
    ) -> Generator[bytes, None, None]:
        """Synthesize speech from text and return an audio stream generator."""
        raise NotImplementedError