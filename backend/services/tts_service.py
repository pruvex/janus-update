import logging
import hashlib
import time
from typing import Optional, List, Dict
from pathlib import Path

from backend.tts_providers.silero import SileroTTS
from backend.tts_providers.piper import PiperTTS, apply_basic_normalization
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger("janus_backend")

# TTS cache directory
TTS_CACHE_DIR = Path(get_app_data_dir()) / "tts_cache"
TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class TTSService:
    """Text-to-Speech service with caching and provider fallback."""
    
    def __init__(self):
        self.silero = SileroTTS()
        self.piper = PiperTTS()
        self.providers = {
            "silero": self.silero,
            "piper": self.piper,
        }
    
    def get_voices(self, lang: Optional[str] = None) -> List[Dict]:
        """Get available voices, optionally filtered by language."""
        all_voices = []

        # Add Piper voices
        if self.piper.is_available():
            piper_voices = self.piper.list_voices()
            for v in piper_voices:
                all_voices.append({
                    "id": f"piper_{v.get('id')}",
                    "name": f"Piper {v.get('name')}",
                    "lang": v.get('lang'),
                    "provider": "piper",
                    "speaker": v.get('id'),
                    "path": v.get('path')
                })
        
        # Add Silero voices (hardcoded for now, can be made dynamic later)
        # Silero DE speakers: bernd_ungerer, eva_k, friedrich, hokuspokus, karlsson, random
        # Silero EN speakers: en_0, en_1, en_2, ..., random
        silero_voices = [
            {"id": "silero_de_random", "name": "Silero Deutsch (Zufällig)", "lang": "de", "provider": "silero", "speaker": "random"},
            {"id": "silero_de_eva_k", "name": "Silero Deutsch Eva K", "lang": "de", "provider": "silero", "speaker": "eva_k"},
            {"id": "silero_de_hokuspokus", "name": "Silero Deutsch Hokuspokus", "lang": "de", "provider": "silero", "speaker": "hokuspokus"},
            {"id": "silero_de_karlsson", "name": "Silero Deutsch Karlsson", "lang": "de", "provider": "silero", "speaker": "karlsson"},
            {"id": "silero_en_random", "name": "Silero English (Random)", "lang": "en", "provider": "silero", "speaker": "random"},
            {"id": "silero_en_0", "name": "Silero English Voice 0", "lang": "en", "provider": "silero", "speaker": "en_0"},
            {"id": "silero_en_1", "name": "Silero English Voice 1", "lang": "en", "provider": "silero", "speaker": "en_1"},
        ]
        all_voices.extend(silero_voices)

        if lang:
            all_voices = [v for v in all_voices if v["lang"].startswith(lang)]
        
        return sorted(all_voices, key=lambda v: v["name"])
    
    def _cache_key(self, text: str, voice: str, lang: str, speed: float, fmt: str, provider: str, preset_name: Optional[str]) -> str:
        """Generate cache key for TTS request."""
        raw = f"{text}|{voice}|{lang}|{speed}|{fmt}|{provider}|{preset_name}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
    
    def _cache_path(self, key: str, fmt: str) -> Path:
        """Get cache file path."""
        return TTS_CACHE_DIR / f"{key}.{fmt}"
    
    def _select_provider_chain(self, lang: str, voice_provider: Optional[str] = None) -> List[str]:
        """Select provider fallback chain based on language and voice preference."""
        if voice_provider:
            # Use specific provider requested by voice
            if voice_provider == "piper":
                return ["piper", "silero"]  # Fallback to Silero if Piper fails
            elif voice_provider == "silero":
                return ["silero"]
        
        # Default: Piper first (if available), then Silero
        if lang.startswith("de") and self.piper.is_available():
            return ["piper", "silero"]
        else:
            return ["silero"]
    
    def _get_voice_config(self, voice_id: str) -> Optional[dict]:
        """Get voice configuration by ID."""
        all_available_voices = self.get_voices() # Get all dynamically loaded voices
        for voice in all_available_voices:
            if voice["id"] == voice_id:
                return voice
        return None
    
    def synthesize(
        self,
        text: str,
        lang: str = "de",
        voice: Optional[str] = None,
        speed: float = 1.0,
        fmt: str = "mp3",
        provider: Optional[str] = None,
        stream: bool = False,
        preset_name: Optional[str] = None
    ) -> bytes:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            lang: Language code (de, en)
            voice: Voice ID (optional, auto-selected)
            speed: Speech speed (0.5 - 2.0)
            fmt: Audio format (mp3, wav, ogg)
            provider: Provider name (optional, auto-selected)
            stream: Enable streaming (if supported)
        
        Returns:
            Audio bytes
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Select default voice if not specified
        if not voice:
            # Use Piper by default if available, otherwise Silero
            if self.piper.is_available() and lang.startswith("de"):
                voice = "de_thorsten_medium"  # Medium is more natural than high
            elif lang.startswith("de"):
                voice = "de_random"
            else:
                voice = "en_random"
        
        # Get voice configuration
        voice_config = self._get_voice_config(voice)
        if not voice_config:
            raise ValueError(f"Unknown voice: {voice}")
        
        # Extract speaker name and provider from voice config
        speaker = voice_config.get("speaker", "random")
        voice_provider = voice_config.get("provider")
        
        # Select provider chain
        if provider:
            provider_chain = [provider]
        else:
            provider_chain = self._select_provider_chain(lang, voice_provider)
        
        # Generate cache key
        cache_key = self._cache_key(text, voice, lang, speed, fmt, provider_chain[0], preset_name)
        cache_file = self._cache_path(cache_key, fmt)
        
        # Check cache
        if cache_file.exists():
            logger.info(f"TTS cache hit: {cache_key}")
            return cache_file.read_bytes()
        
        # Synthesize with fallback
        last_error = None
        start_time = time.time()
        
        for prov_name in provider_chain:
            prov = self.providers.get(prov_name)
            if not prov:
                logger.warning(f"Provider {prov_name} not available")
                continue
            
            try:
                logger.info(f"Synthesizing with {prov_name}: {text[:50]}...")
                # Apply normalization only for Piper for now, as it's designed for it
                normalized_text = apply_basic_normalization(text) if prov_name == "piper" else text

                audio_bytes = prov.synthesize(
                    text=normalized_text,
                    voice=speaker,  # Use speaker for all providers
                    lang=lang,
                    speed=speed,
                    fmt=fmt,
                    preset_name=preset_name # Pass the preset name
                )
                
                # Cache result
                cache_file.write_bytes(audio_bytes)
                
                elapsed = time.time() - start_time
                logger.info(f"TTS synthesis completed in {elapsed:.2f}s ({len(audio_bytes)} bytes)")
                
                return audio_bytes
            except Exception as e:
                logger.error(f"TTS provider {prov_name} failed: {e}")
                last_error = e
                continue
        
        # All providers failed
        raise RuntimeError(f"TTS synthesis failed: {last_error}")


# Singleton instance
_tts_service = None


def get_tts_service() -> TTSService:
    """Get or create TTS service singleton."""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
