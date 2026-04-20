import hashlib
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Tiktoken with fallback
try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False
    tiktoken = None
    logger = logging.getLogger("janus_backend")
    logger.warning("[TTS-SERVICE] tiktoken not available - using len(text) // 4 fallback")
else:
    logger = logging.getLogger("janus_backend")

from backend.data import database
from backend.services import cost_calculator
from backend.services.tts_normalizer import normalize_text_de
from backend.tts_providers.openai import OpenAITTS
from backend.tts_providers.piper import PiperTTS
from backend.tts_providers.silero import SileroTTS
from backend.utils.paths import get_app_data_dir

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
        self.openai = (
            OpenAITTS(api_key=openai_api_key)
            if openai_api_key
            else OpenAITTS(api_key=os.environ.get("OPENAI_API_KEY"))
        )
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
                all_voices.append(
                    {
                        "id": f"piper_{v.get('id')}",
                        "name": f"Piper {v.get('name')}",
                        "lang": v.get("lang"),
                        "provider": "piper",
                        "speaker": v.get("id"),
                        "path": v.get("path"),
                    }
                )

        # Add Silero voices
        silero_voices = [
            {
                "id": "silero_de_random",
                "name": "Silero Deutsch (Zufällig)",
                "lang": "de",
                "provider": "silero",
                "speaker": "random",
            },
            {
                "id": "silero_de_eva_k",
                "name": "Silero Deutsch Eva K",
                "lang": "de",
                "provider": "silero",
                "speaker": "eva_k",
            },
        ]
        all_voices.extend(silero_voices)

        # Add OpenAI voices
        if self.openai.is_available():
            openai_voices = self.openai.list_voices()
            for v in openai_voices:
                all_voices.append(
                    {
                        "id": f"openai_{v.get('id')}",
                        "name": f"OpenAI {v.get('name')}",
                        "lang": v.get("lang"),
                        "provider": "openai",
                        "speaker": v.get("id"),
                    }
                )
        if lang:
            all_voices = [v for v in all_voices if v["lang"].startswith(lang)]

        return sorted(all_voices, key=lambda v: v["name"])

    def _cache_key(
        self,
        text: str,
        voice: str,
        lang: str,
        speed: float,
        fmt: str,
        provider: str,
        preset_name: Optional[str],
    ) -> str:
        """Generate cache key for TTS request."""
        raw = f"{text}|{voice}|{lang}|{speed}|{fmt}|{provider}|{preset_name}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _cache_path(self, key: str, fmt: str) -> Path:
        """Get cache file path."""
        return TTS_CACHE_DIR / f"{key}.{fmt}"

    def _select_provider_chain(
        self, lang: str, voice_provider: Optional[str] = None, llm_provider: Optional[str] = None
    ) -> List[str]:
        """Wählt den TTS-Provider basierend auf strikten, autonomen Regeln ohne Fallback."""
        logger.debug(
            f"_select_provider_chain called with: lang={lang}, voice_provider={voice_provider}, llm_provider={llm_provider}"
        )

        # Regel 1: Gemini LLM erzwingt Piper TTS.
        if llm_provider and llm_provider.lower().startswith("gemini"):
            logger.info("Gemini provider detected. Forcing Piper TTS (no fallback).")
            return ["piper"]

        # Regel 2: OpenAI LLM hat eine bedingte Logik.
        if llm_provider and llm_provider.lower().startswith("openai"):
            # Wenn "Immer Piper nutzen" aktiv ist, wird Piper erzwungen.
            if self.use_piper_tts:
                logger.info("OpenAI provider with 'use_piper_tts' enabled. Forcing Piper TTS.")
                return ["piper"]
            # Ansonsten wird OpenAI TTS verwendet, wenn verfügbar.
            if self.openai.is_available():
                logger.info("OpenAI provider detected. Using OpenAI TTS.")
                return ["openai"]
            else:
                # Wenn OpenAI nicht verfügbar ist, fällt es auf Piper zurück (einziger erlaubter Fallback hier).
                logger.warning("OpenAI TTS requested but not available. Falling back to Piper.")
                return ["piper"]

        # Regel 3: Wenn eine explizite Stimme ausgewählt wurde, hat deren Provider Priorität.
        # Diese Regel wird von der LLM-Provider-Logik überschrieben, ist aber für andere Fälle nützlich.
        if voice_provider:
            if voice_provider == "openai" and self.openai.is_available() and not self.use_piper_tts:
                return ["openai"]
            if voice_provider == "piper":
                return ["piper"]
            if voice_provider == "silero":  # Silero bleibt als Option, falls direkt gewählt
                return ["silero"]

        # Regel 4: Generischer, sicherer Fallback ist IMMER Piper, wenn es verfügbar ist.
        if self.piper.is_available():
            logger.info("Defaulting to Piper TTS based on availability.")
            return ["piper"]

        # Allerletzter Fallback, wenn selbst Piper nicht geht.
        logger.warning("Piper TTS not available. Falling back to Silero as last resort.")
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
        llm_provider: Optional[str] = None,
    ) -> bytes:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        cleaned_text = clean_text_for_tts(text)

        # --- START DER KORREKTUR: Intelligente Stimmenauswahl ---

        # 1. Bestimme die ursprünglich angeforderte Stimme (aus der Persönlichkeit oder als Fallback)
        requested_voice_id = voice or self.tts_settings.get("voice", "piper_de_DE-thorsten-medium")

        # 2. Bestimme den finalen TTS-Provider basierend auf unseren strikten Regeln
        requested_voice_config = self._get_voice_config(requested_voice_id)
        requested_voice_provider = (
            requested_voice_config.get("provider") if requested_voice_config else None
        )

        provider_chain = (
            [provider]
            if provider
            else self._select_provider_chain(lang, requested_voice_provider, llm_provider)
        )
        final_provider_name = provider_chain[0]

        # 3. Prüfe auf einen Provider-Konflikt und korrigiere die Stimme bei Bedarf
        final_voice_id = requested_voice_id
        if requested_voice_provider != final_provider_name:
            logger.warning(
                f"Provider-Konflikt erkannt! Angefordert: '{requested_voice_provider}', erzwinge aber: '{final_provider_name}'. "
                f"Wechsle zu einer kompatiblen Standardstimme."
            )
            # Hier definieren wir die Standardstimmen für erzwungene Wechsel
            if final_provider_name == "piper" and lang.startswith("de"):
                final_voice_id = "piper_de_DE-thorsten-medium"
                logger.info(f"Standardstimme für Piper gewählt: {final_voice_id}")
            # Hier könnten weitere Regeln für andere Provider folgen

        # 4. Lade die finale Konfiguration für die zu verwendende Stimme
        final_voice_config = self._get_voice_config(final_voice_id)
        if not final_voice_config:
            raise ValueError(f"Unbekannte finale Stimme: {final_voice_id}")

        speaker = final_voice_config.get("speaker", "random")
        # --- ENDE DER KORREKTUR ---

        # Der Rest der Methode nutzt nun die korrigierten Werte
        normalized_text = normalize_text_de(cleaned_text)
        cache_key = self._cache_key(
            normalized_text, final_voice_id, lang, speed, fmt, final_provider_name, preset_name
        )
        cache_file = self._cache_path(cache_key, fmt)

        if cache_file.exists():
            logger.info(f"TTS cache hit: {cache_key}")
            return cache_file.read_bytes()

        last_error = None
        start_time = time.time()

        for (
            prov_name
        ) in provider_chain:  # provider_chain enthält jetzt nur noch den korrekten Provider
            prov = self.providers.get(prov_name)
            if not prov:
                continue

            try:
                logger.info(f"Synthesizing with {prov_name}: {text[:50]}...")
                # Wichtig: Wir übergeben den final korrigierten "speaker"
                audio_bytes = prov.synthesize(
                    text=normalized_text, voice=speaker, lang=lang, speed=speed, fmt=fmt
                )

                if not audio_bytes:
                    logger.warning(f"TTS provider {prov_name} returned no audio data.")
                    continue

                cache_file.write_bytes(audio_bytes)
                elapsed = time.time() - start_time
                logger.info(f"TTS synthesis completed in {elapsed:.2f}s ({len(audio_bytes)} bytes)")

                # Kosten-Tracking für OpenAI
                if prov_name == "openai":
                    try:
                        tts_model_id = "gpt-4o-mini"
                        if _TIKTOKEN_AVAILABLE and tiktoken:
                            encoding = tiktoken.get_encoding("o200k_base")
                            prompt_tokens = 0
                            completion_tokens = len(encoding.encode(normalized_text))
                        else:
                            # Fallback: len(text) // 4 (approximate token count)
                            prompt_tokens = 0
                            completion_tokens = max(1, len(normalized_text) // 4)

                        usage_data = {
                            "input_tokens": len(text),
                            "output_tokens": 0,
                        }
                        usage, cost = cost_calculator.calculate_cost(tts_model_id, usage_data)

                        # KOSTEN-TRACKING FIX:
                        # OpenAI TTS berechnet nach Zeichen (Input).
                        # Wir übergeben die Textlänge als input_tokens.
                        # image_size und image_quality müssen explizit None sein.
                        if cost.get("total_cost", 0) > 0:
                            try:
                                database.save_cost_entry(
                                    date=datetime.now(),
                                    model=tts_model_id,
                                    provider="openai",
                                    input_tokens=len(text),  # Zeichenanzahl als Input
                                    output_tokens=0,
                                    image_quality=None,      # WICHTIG: Fix für TypeError
                                    image_size=None,         # WICHTIG: Fix für TypeError
                                    image_cost=0,
                                    total_cost=cost.get("total_cost", 0),
                                )
                                logger.info(f"TTS cost tracked for {len(text)} chars.")
                            except Exception as e:
                                logger.error(f"Failed to track TTS cost: {e}")
                        
                        logger.info(
                                f"Successfully tracked TTS cost: {cost.get('total_cost')} EUR for {len(text)} chars"
                            )
                    except Exception as e:
                        logger.error(f"Failed to track TTS cost: {e}", exc_info=True)

                return audio_bytes
            except Exception as e:
                logger.error(f"TTS provider {prov_name} failed: {e}")
                last_error = e
                continue

        raise RuntimeError(f"TTS synthesis failed: {last_error}")


def clean_text_for_tts(text: str) -> str:
    """Removes Markdown and other special characters for cleaner speech synthesis."""
    if not text:
        return ""
    # Remove markdown links, keeping the link text
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    # Remove markdown bold, italic, code, blockquotes, and common decorative emojis
    text = re.sub(r"(\*\*|__|\*|_|`|>|🔥|✨|👉)", "", text)
    # Replace horizontal rules with a simple space, NOT a period
    text = re.sub(r"---", " ", text)
    # Replace multiple newlines with a single space
    text = re.sub(r"\n+", " ", text)
    # Collapse multiple spaces into a single space for clean output
    text = " ".join(text.split())
    return text


# Singleton instance
_tts_service = None


def get_tts_service(config: Dict, openai_api_key: Optional[str] = None) -> TTSService:
    """Get or create TTS service singleton."""
    global _tts_service
    if _tts_service is None:
        tts_settings = config.get("tts_settings", {})
        _tts_service = TTSService(
            config=config, tts_settings=tts_settings, openai_api_key=openai_api_key
        )
    return _tts_service
