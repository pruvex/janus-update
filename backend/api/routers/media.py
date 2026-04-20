import json
import logging
import os
import shutil
import tempfile
from typing import Optional

import keyring
from backend.services.speech_to_text_service import get_stt_service
from backend.services.tts_service import get_tts_service
from backend.utils.config_loader import initialize_file_from_template
from backend.utils.paths import get_app_data_dir, resource_path
from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger("janus_backend")

# --- Config & Paths ---
DATA_DIR = get_app_data_dir()
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
PERSONALITIES_FILE = os.path.join(DATA_DIR, "personalities.json")
TEMPLATE_CONFIG_FILE = resource_path("backend/config/config.json")
TEMPLATE_PERSONALITIES_FILE = resource_path("backend/config/personalities.json")


def load_config():
    initialize_file_from_template(TEMPLATE_CONFIG_FILE, CONFIG_FILE)
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def load_personalities():
    initialize_file_from_template(TEMPLATE_PERSONALITIES_FILE, PERSONALITIES_FILE)
    try:
        with open(PERSONALITIES_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading personalities: {e}")
        return []


class PersonalityUpdate(BaseModel):
    personality_id: str


# --- Endpoints: Images ---


@router.get("/images")
async def get_all_images():
    image_dir = os.path.join(get_app_data_dir(), "images")
    try:
        if not os.path.exists(image_dir):
            return {"images": []}

        all_files = os.listdir(image_dir)
        supported = (".png", ".jpg", ".jpeg", ".gif", ".webp")
        image_files = [f for f in all_files if f.lower().endswith(supported)]
        image_files.sort(key=lambda x: os.path.getmtime(os.path.join(image_dir, x)), reverse=True)

        return {"images": [f"/user_images/{f}" for f in image_files]}
    except Exception as e:
        logger.error(f"Error listing images: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve images.")


# --- Endpoints: Transcribe (STT) ---


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    stt_service = get_stt_service()
    if not stt_service:
        raise HTTPException(status_code=500, detail="STT service unavailable.")

    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(file.filename)[1]
        ) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed: {e}")
    finally:
        file.file.close()

    try:
        text = stt_service.transcribe_audio(tmp_path)
        if text is None:
            raise HTTPException(status_code=500, detail="Transcription failed.")
        return {"transcription": text}
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# --- Endpoints: TTS ---

@router.get("/tts/settings")
async def get_tts_settings():
    # Dummy-Endpunkt, um 404-Fehler im Frontend zu vermeiden.
    # TODO: Mit echter Konfiguration füllen, falls benötigt.
    return {}

@router.get("/tts/voices")
async def get_tts_voices(lang: Optional[str] = None):
    try:
        config = load_config()
        tts_service = get_tts_service(config=config)
        return {"voices": tts_service.get_voices(lang=lang)}
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts/synthesize")
async def synthesize_speech(
    text: str,
    lang: str = Query("de"),
    voice_id: Optional[str] = None,
    speed: Optional[float] = None,
    fmt: str = Query("mp3"),
    provider: Optional[str] = None,
    stream: bool = False,
    preset: Optional[str] = None,
    llm_provider: Optional[str] = None,
):
    try:
        config = load_config()
        personalities = load_personalities()
        api_key = keyring.get_password("Janus-Projekt", "openai")

        tts_service = get_tts_service(config, api_key)

        # Personality Settings resolving
        active_pid = config.get("active_personality", "ai_assistant")
        active_p = next((p for p in personalities if p.get("id") == active_pid), None) or {}
        p_settings = active_p.get("tts_settings", {"voice": "openai_alloy", "speed": 1.0})

        final_voice = voice_id or p_settings.get("voice")
        final_speed = speed or p_settings.get("speed")

        logger.info(f"Synthesizing ({active_pid}): voice='{final_voice}', speed={final_speed}")

        audio = tts_service.synthesize(
            text=text,
            lang=lang,
            voice=final_voice,
            speed=final_speed,
            fmt=fmt,
            provider=provider,
            stream=stream,
            preset_name=preset,
            llm_provider=llm_provider,
        )

        mime = {"mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg"}.get(fmt.lower())
        return Response(content=audio, media_type=mime)

    except ValueError as e:
        # FIX: ValueError explizit als 400 behandeln
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"TTS failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# --- Endpoints: Personalities ---


@router.get("/personalities")
async def get_personalities():
    return load_personalities()


@router.get("/personalities/active")
async def get_active_personality():
    config = load_config()
    return {"active_personality_id": config.get("active_personality", "ai_assistant")}


@router.post("/personalities/active")
async def set_active_personality(update: PersonalityUpdate):
    config = load_config()
    personalities = load_personalities()
    ids = [p.get("id") for p in personalities]

    if update.personality_id not in ids:
        raise HTTPException(status_code=404, detail="Personality not found.")

    config["active_personality"] = update.personality_id
    save_config(config)
    return {"message": f"Active personality set to {update.personality_id}"}
