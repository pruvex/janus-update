import logging
import os

from faster_whisper import WhisperModel
from backend.utils.paths import get_model_cache_dir

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpeechToTextService:
    _instance = None
    _model = None

    def __new__(cls, model_name="base"):
        if cls._instance is None:
            cls._instance = super(SpeechToTextService, cls).__new__(cls)
            try:
                model_cache_path = get_model_cache_dir()
                logger.info(f"Loading faster-whisper model '{model_name}'...")
                # The model will be downloaded to the cache directory
                cls._model = WhisperModel(model_name, device="cpu", compute_type="int8", download_root=model_cache_path)
                logger.info("faster-whisper model loaded successfully.")
            except Exception as e:
                logger.error(f"Error loading Whisper model: {e}")
                cls._instance = None
                raise
        return cls._instance

    def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribes an audio file using the loaded Whisper model.

        Args:
            audio_file_path (str): The path to the audio file.

        Returns:
            str: The transcribed text.
        """
        if self._model is None:
            logger.error("Whisper model is not loaded.")
            return ""

        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found at: {audio_file_path}")
            return ""

        try:
            logger.info(f"Transcribing audio file: {audio_file_path}")
            segments, _ = self._model.transcribe(audio_file_path, word_timestamps=True)
            transcribed_text = "".join(segment.text for segment in segments)
            logger.info(f"Transcription successful. Text: {transcribed_text[:100]}...")
            return transcribed_text
        except Exception as e:
            logger.error(f"Error during audio transcription: {e}")
            return ""


# Singleton instance for easy access
def get_stt_service():
    try:
        return SpeechToTextService()
    except Exception as e:
        logger.error(f"Failed to initialize SpeechToTextService: {e}")
        return None
