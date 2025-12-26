import io
import logging
import os
from typing import Dict
import keyring # NEU: Import keyring

from openai import AsyncOpenAI
from pydub import AudioSegment
from tenacity import retry, stop_after_attempt

from backend.llm_providers.openai_service import OpenAIServiceProvider
from backend.services.tts_service import TTSService
from backend.utils.paths import get_desktop_path
from backend.services import llm_gateway # NEU: Import llm_gateway

logger = logging.getLogger("janus_backend")


async def save_mp3_tool(
    content: str = None,
    filename: str = "output.mp3",
    voice: str = "fable",
    last_ssml_content: str = None,
) -> Dict[str, str]:
    """
    Synthetisiert Text zu Audio (MP3) und speichert ihn auf dem Desktop.
    Wenn kein Inhalt übergeben wird, versucht das Tool, den letzten gesprochenen Text (SSML) zu nutzen.
    """
    # Logik-Update: Content aus Context holen, falls leer
    if not content and last_ssml_content:
        content = last_ssml_content

    if not content:
        return {"status": "error", "message": "Kein Text zum Speichern gefunden."}

    if not filename.lower().endswith(".mp3"):
        filename += ".mp3"

    desktop_path = get_desktop_path()
    if not desktop_path:
        return {"status": "error", "message": "Desktop-Pfad nicht gefunden."}

    path = os.path.join(desktop_path, os.path.basename(filename))

    try:
        # SSML-Erkennung für OpenAI
        if content.strip().startswith("<speak>"):
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                return {"status": "error", "message": "OpenAI API Key fehlt für SSML."}

            client = AsyncOpenAI(api_key=api_key)
            # Hier vereinfacht ohne Chunking für Lesbarkeit, ggf. Chunking-Logik hierher verschieben
            resp = await client.audio.speech.create(model="tts-1-hd", voice=voice, input=content)

            # Pydub nutzen um sicherzustellen dass es valide ist
            audio_segment = AudioSegment.from_file(io.BytesIO(resp.content), format="mp3")
            audio_segment.export(path, format="mp3")
        else:
            # Lokale TTS
            from backend.main import load_config

            config = load_config()
            tts = TTSService(config=config, tts_settings=config.get("tts_settings", {}))
            audio = tts.synthesize(text=content, voice="piper_de_DE-thorsten-medium")
            if audio:
                with open(path, "wb") as f:
                    f.write(audio)
            else:
                return {"status": "error", "message": "Lokale TTS hat keine Daten geliefert."}

        return {"status": "success", "message": f"Audiodatei erstellt: {path}"}
    except Exception as e:
        logger.error(f"Audio Tool Fehler: {e}")
        return {"status": "error", "message": str(e)}


@retry(stop=stop_after_attempt(2))
async def _generate_image_tool_internal(api_key: str, provider: str, image_model: str, prompt: str, size: str = "1024x1024", quality: str = "standard", **kwargs) -> Dict:
    """Interne Funktion zur Bildgenerierung, die den spezifischen Provider und das Modell nutzt."""
    logger.debug(f"media_tools.py: _generate_image_tool_internal - Instantiating LLM provider for: {provider}") # NEU
    # `get_provider` holt die korrekte Provider-Instanz (OpenAI oder Gemini)
    llm_provider_instance = llm_gateway.get_provider(provider) 
    logger.debug(f"media_tools.py: _generate_image_tool_internal - Calling generate_image for model: {image_model} with provider: {type(llm_provider_instance).__name__}") # NEU
    res = await llm_provider_instance.generate_image(api_key, image_model, prompt, size=size, quality=quality, **kwargs)
    logger.debug(f"media_tools.py: _generate_image_tool_internal - Result from generate_image: {res}") # NEU
    return {"url": res.get("image_url"), "cost": res.get("cost")}


async def generate_image_tool(prompt: str, size: str = "1024x1024", quality: str = "standard", **kwargs) -> Dict:
    """
    Ein Wrapper-Tool, das das aktuell aktive Bildgenerierungsmodell und den Provider
    dynamisch ermittelt und die Bildgenerierung auslöst.
    """
    from backend.utils.config_loader import load_config_data
    
    config = load_config_data()
    current_provider = config.get("last_used_provider", "openai")
    logger.debug(f"media_tools.py: generate_image_tool - current_provider from config: {current_provider}") # NEU
    
    image_model = await llm_gateway.get_active_image_generation_model(current_provider)
    logger.debug(f"media_tools.py: generate_image_tool - image_model from gateway: {image_model}") # NEU
    
    if not image_model:
        return {"status": "error", "message": f"Kein Bildgenerierungsmodell für Provider '{current_provider}' gefunden."}
        
    api_key = keyring.get_password("Janus-Projekt", current_provider)
    if not api_key:
        return {"status": "error", "message": f"API Key für '{current_provider}' fehlt."}
    
    logger.info(f"Using provider '{current_provider}' and image model '{image_model}' for image generation.") # NEU
    return await _generate_image_tool_internal(api_key, current_provider, image_model, prompt, size=size, quality=quality, **kwargs)
