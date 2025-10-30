import os
import logging
import hashlib
import time
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime

# --- NEU: Imports für Kostenberechnung ---
from backend.services import cost_calculator
from backend.data import database

from backend.tts_providers.silero import SileroTTS
from backend.tts_providers.piper import PiperTTS
from backend.tts_providers.openai import OpenAITTS
from backend.services.tts_normalizer import normalize_text_de
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger("janus_backend")

# TTS cache directory
TTS_CACHE_DIR = Path(get_app_data_dir()) / "tts_cache"
TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class TTSService:
    """Text-to-Speech service with caching and provider fallback."""
    
    def __init__(self, config: Dict, tts_settings: Dict, openai_api_key: Optional[str] = None):
        self.config = config
        self.tts_settings = tts_settings
        self.use_piper_tts = self.config.get("tts_settings", {}).get("use_piper_tts", False)
        self.silero = SileroTTS()
        self.piper = PiperTTS()
        self.openai = OpenAITTS(api_key=openai_api_key) if openai_api_key else OpenAITTS(api_key=os.environ.get("OPENAI_API_KEY"))
        self.providers = {
            "silero": self.silero,
            "piper": self.piper,
            "openai": self.openai,
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
        
        # Add Silero voices
        silero_voices = [
            {"id": "silero_de_random", "name": "Silero Deutsch (Zufällig)", "lang": "de", "provider": "silero", "speaker": "random"},
            {"id": "silero_de_eva_k", "name": "Silero Deutsch Eva K", "lang": "de", "provider": "silero", "speaker": "eva_k"},
        ]
        all_voices.extend(silero_voices)

        # Add OpenAI voices
        if self.openai.is_available():
            openai_voices = self.openai.list_voices()
            for v in openai_voices:
                all_voices.append({
                    "id": f"openai_{v.get('id')}",
                    "name": f"OpenAI {v.get('name')}",
                    "lang": v.get('lang'),
                    "provider": "openai",
                    "speaker": v.get('id'),
                })
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
    
    def _select_provider_chain(self, lang: str, voice_provider: Optional[str] = None, llm_provider: Optional[str] = None) -> List[str]:
        # (Diese Funktion bleibt unverändert)
        logger.debug(f"_select_provider_chain called with: lang={lang}, voice_provider={voice_provider}, llm_provider={llm_provider}")
        if self.use_piper_tts:
            return ["piper", "silero"]
        if voice_provider:
            if voice_provider == "openai": return ["openai", "piper", "silero"]
            elif voice_provider == "piper": return ["piper", "silero"]
            elif voice_provider == "silero": return ["silero"]
            else: return ["piper", "silero"]
        if llm_provider == "openai" and self.openai.is_available():
            return ["openai", "piper", "silero"]
        if lang.startswith("de") and self.piper.is_available():
            return ["piper", "silero"]
        else:
            return ["silero"]
    
    def _get_voice_config(self, voice_id: str) -> Optional[dict]:
        """Get voice configuration by ID."""
        for voice in self.get_voices():
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
        preset_name: Optional[str] = None,
        llm_provider: Optional[str] = None
    ) -> bytes:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if not voice:
            if self.tts_settings.get("voice"):
                voice = self.tts_settings.get("voice")
            elif self.piper.is_available() and lang.startswith("de"):
                voice = "piper_de_DE-thorsten-medium"
            else:
                voice = "de_random"
        
        voice_config = self._get_voice_config(voice)
        if not voice_config:
            raise ValueError(f"Unknown voice: {voice}")
        
        speaker = voice_config.get("speaker", "random")
        voice_provider = voice_config.get("provider")
        
        provider_chain = [provider] if provider else self._select_provider_chain(lang, voice_provider, llm_provider)
        
        normalized_text = normalize_text_de(text)
        cache_key = self._cache_key(normalized_text, voice, lang, speed, fmt, provider_chain[0], preset_name)
        cache_file = self._cache_path(cache_key, fmt)
        
        if cache_file.exists():
            logger.info(f"TTS cache hit: {cache_key}")
            return cache_file.read_bytes()
        
        last_error = None
        start_time = time.time()
        
        for prov_name in provider_chain:
            prov = self.providers.get(prov_name)
            if not prov:
                continue
            
            try:
                logger.info(f"Synthesizing with {prov_name}: {text[:50]}...")
                audio_bytes = prov.synthesize(
                    text=normalized_text, voice=speaker, lang=lang, speed=speed, fmt=fmt
                )
                
                if not audio_bytes:
                    logger.warning(f"TTS provider {prov_name} returned no audio data.")
                    continue

                cache_file.write_bytes(audio_bytes)
                elapsed = time.time() - start_time
                logger.info(f"TTS synthesis completed in {elapsed:.2f}s ({len(audio_bytes)} bytes)")

                if prov_name == "openai":
                    try:
                        tts_model_id = "gpt-4o-mini-tts"
                        usage_data = {"input_characters": len(normalized_text)}
                        usage, cost = cost_calculator.calculate_cost(tts_model_id, usage_data)
                        
                        if cost.get("total_cost", 0) > 0:
                            database.save_cost_entry(
                                date=datetime.now(),
                                model=tts_model_id,
                                input_tokens=usage.get("input_tokens", 0),
                                output_tokens=0,
                                image_quality=None,  # Standardwert für Nicht-Bild-Modelle
                                image_cost=0,        # Standardwert für Nicht-Bild-Modelle
                                total_cost=cost.get("total_cost", 0),
                            )
                            logger.info(f"Successfully tracked TTS cost: {cost.get('total_cost')} EUR")
                    except Exception as e:
                        logger.error(f"Failed to track TTS cost: {e}", exc_info=True)

                return audio_bytes
            except Exception as e:
                logger.error(f"TTS provider {prov_name} failed: {e}")
                last_error = e
                continue
        
        raise RuntimeError(f"TTS synthesis failed: {last_error}")


# Singleton instance
_tts_service = None

def get_tts_service(config: Dict, openai_api_key: Optional[str] = None) -> TTSService:
    """Get or create TTS service singleton."""
    global _tts_service
    if _tts_service is None:
        tts_settings = config.get("tts_settings", {})
        _tts_service = TTSService(config=config, tts_settings=tts_settings, openai_api_key=openai_api_key)
    return _tts_service