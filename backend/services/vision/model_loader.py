import logging
import threading
import torch
import clip
from pathlib import Path
import sys

logger = logging.getLogger("janus_backend")


class ModelLoadingState:
    """Status-Tracking für CLIP-Model-Download."""
    MODEL_LOADING = "model_loading"
    MODEL_LOADED = "model_loaded"
    MODEL_ERROR = "model_error"


class ClipModelLoader:
    """Asynchroner CLIP-Model-Loader mit Lazy-Loading Pattern."""
    
    def __init__(self):
        self.model = None
        self.preprocess = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.state = ModelLoadingState.MODEL_LOADING
        self.error_message = None
        self._load_thread = None
        self._load_started = False
        
    def start_async_load(self):
        """Startet den asynchronen Download im Hintergrund."""
        if self._load_started:
            logger.info("MODEL-LOADER: Download bereits gestartet.")
            return
            
        self._load_started = True
        self._load_thread = threading.Thread(target=self._load_clip_model, daemon=True)
        self._load_thread.start()
        logger.info("MODEL-LOADER: Asynchroner CLIP-Model-Download gestartet im Hintergrund.")
        
    def _load_clip_model(self):
        """Lädt das CLIP-Model asynchron im Hintergrund."""
        try:
            logger.info(f"MODEL-LOADER: Starte CLIP-Model-Download auf {self.device}...")
            self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
            self.state = ModelLoadingState.MODEL_LOADED
            logger.info(f"MODEL-LOADER: CLIP-Modell erfolgreich auf {self.device} geladen.")
        except Exception as exc:
            self.state = ModelLoadingState.MODEL_ERROR
            self.error_message = str(exc)
            self.model = None
            self.preprocess = None
            logger.warning(
                "⚠️ MODEL-LOADER: CLIP-Modell konnte nicht geladen werden (Bildsuche deaktiviert)"
            )
            logger.debug("MODEL-LOADER: CLIP-Load error details: %s", exc, exc_info=True)
            
    def get_state(self):
        """Gibt den aktuellen Loading-Status zurück."""
        return {
            "state": self.state,
            "error": self.error_message,
            "device": self.device
        }
        
    def is_ready(self):
        """Prüft ob das Model geladen und bereit ist."""
        return self.state == ModelLoadingState.MODEL_LOADED and self.model is not None
        
    def wait_for_load(self, timeout=300):
        """Wartet auf das Laden des Models (mit Timeout)."""
        if self._load_thread and self._load_thread.is_alive():
            self._load_thread.join(timeout=timeout)
        return self.is_ready()


# Globaler Model-Loader Singleton
_model_loader = None


def get_model_loader():
    """Gibt den globalen Model-Loader zurück (Singleton Pattern)."""
    global _model_loader
    if _model_loader is None:
        _model_loader = ClipModelLoader()
    return _model_loader


def start_clip_model_download():
    """Startet den asynchronen CLIP-Model-Download."""
    loader = get_model_loader()
    loader.start_async_load()
    return loader
