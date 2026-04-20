import hashlib
import io
import logging
import os
from typing import Dict, List, Optional

import torch
from pydub import AudioSegment

from backend.tts_providers.base import TTSProviderBase
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger("janus_backend")

# Model configurations
SILERO_MODELS = {
    "en": {"name": "en_v3", "url": "https://models.silero.ai/models/tts/en/v3_en.pt", "sha256": "02b71034d9f13bc4001195017bac9db1c6bb6115e03fea52983e8abcff13b665"},
    "de": {"name": "de_v3", "url": "https://models.silero.ai/models/tts/de/v3_de.pt", "sha256": "2e22f38619e1d1da96d963bda5fab6d53843e8837438cb5a45dc376882b0354b"},
}

CACHE_DIR = os.path.join(get_app_data_dir(), "tts_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def calculate_sha256(file_path: str) -> str:
    """Calculates the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

class SileroTTS(TTSProviderBase):
    """Silero TTS Provider - Local PyTorch-based TTS."""

    name = "silero"

    def __init__(self):
        self.models = {}  # lang -> model
        self.device = torch.device("cpu")

    def is_available(self) -> bool:
        """Check if Silero is available."""
        # Silero is always considered available if the models can be loaded/downloaded
        # We don't check for an external binary like Piper
        return True

    def supports_streaming(self, fmt: str) -> bool:
        return False

    def list_voices(self) -> List[Dict]:
        """List available Silero voices."""
        voices = []
        for lang_key, info in SILERO_MODELS.items():
            # For Silero, we'll just list a generic voice per language for now
            voices.append(
                {
                    "id": f"{lang_key}_random",
                    "name": f"Silero {lang_key.upper()} (Zufällig)",
                    "lang": lang_key,
                    "provider": "silero",
                    "speaker": "random",  # Silero uses generic speakers or random
                }
            )
        return voices

    def _load_model(self, lang: str):
        """Load or retrieve cached Silero model."""
        lang_key = "de" if lang.startswith("de") else "en"
        if lang_key in self.models:
            return self.models[lang_key]

        info = SILERO_MODELS[lang_key]
        local_path = os.path.join(CACHE_DIR, info["name"] + ".pt")

        if not os.path.exists(local_path):
            logger.info(f"Downloading Silero model {info['name']}...")
            import urllib.request

            try:
                urllib.request.urlretrieve(info["url"], local_path)
                logger.info(f"Silero model downloaded to {local_path}")
            except Exception as e:
                logger.error(f"Failed to download Silero model: {e}")
                raise

        # --- NEU: Integritätsprüfung des heruntergeladenen Modells ---
        expected_sha256 = info.get("sha256")
        if expected_sha256:
            actual_sha256 = calculate_sha256(local_path)
            if actual_sha256 != expected_sha256:
                error_msg = f"Integritätsprüfung für Silero-Modell {info['name']} fehlgeschlagen! Erwartet: {expected_sha256}, Gefunden: {actual_sha256}"
                logger.error(error_msg)
                # Lösche die potenziell bösartige Datei
                os.remove(local_path)
                raise ValueError(error_msg)
            else:
                logger.info(f"Integritätsprüfung für Silero-Modell {info['name']} erfolgreich.")
        else:
            logger.warning(f"Kein SHA256-Hash für Silero-Modell {info['name']} in Konfiguration gefunden. Laden ohne Integritätsprüfung.")

        # Load model
        try:
            model = torch.package.PackageImporter(local_path).load_pickle("tts_models", "model")
            model.to(self.device)
            self.models[lang_key] = model
            logger.info(f"Silero model {info['name']} loaded successfully")
            return model
        except Exception as e:
            logger.error(f"Failed to load Silero model: {e}")
            raise

    def synthesize(
        self,
        text: str,
        voice: str,
        lang: str,
        speed: float,
        fmt: str,
        preset_name: Optional[str] = None,
    ) -> bytes:
        """Synthesize speech using Silero TTS."""
        try:
            model = self._load_model(lang)
            sample_rate = 48000  # Silero default

            # Silero kennt die Piper-Stimmen nicht. Wir wählen eine gültige aus der Liste.
            speaker_to_use = "random"  # Sicherster Fallback

            audio = model.apply_tts(text=text, speaker=speaker_to_use, sample_rate=sample_rate)

            # Convert tensor to bytes
            audio_np = audio.numpy()
            audio_int16 = (audio_np * 32767).astype("int16")

            # Create audio segment
            seg = AudioSegment(
                audio_int16.tobytes(), frame_rate=sample_rate, sample_width=2, channels=1
            )

            # Export to requested format
            out = io.BytesIO()
            if fmt.lower() == "wav":
                seg.export(out, format="wav")
            elif fmt.lower() == "ogg":
                seg.export(out, format="ogg")
            else:
                seg.export(out, format="mp3")

            return out.getvalue()
        except Exception as e:
            logger.error(f"Silero TTS synthesis failed: {e}")
            raise

    def synthesize_stream(
        self,
        text: str,
        voice: str,
        lang: str,
        speed: float,
        fmt: str,
        preset_name: Optional[str] = None,
    ):
        raise NotImplementedError("Silero TTS does not support streaming.")
