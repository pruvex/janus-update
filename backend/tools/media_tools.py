import aiohttp
import io
import json
import logging
import os
import time
from typing import Dict

import keyring  # NEU: Import keyring

from openai import AsyncOpenAI
from pydub import AudioSegment
from tenacity import retry, stop_after_attempt

from backend.data.schemas_tools import ToolResultV1
from backend.tools.tool_contract_v1 import tool_err_v1, tool_ok_v1
from backend.services.image_manager import save_image_from_bytes
from backend.services.tts_service import TTSService
from backend.services import llm_gateway  # NEU: Import llm_gateway

logger = logging.getLogger("janus_backend")

QUALITY_MAP = {
    "openai": {
        "hd": "high",
        "standard": "low",
        "low": "low",
        "medium": "medium",
        "high": "high",
        "auto": "auto",
    },
}


def _normalize_image_quality(quality: str, provider: str) -> str:
    normalized = (quality or "").lower()
    provider_map = QUALITY_MAP.get(provider, {})
    if normalized in provider_map:
        return provider_map[normalized]
    if not normalized:
        return "low"
    return normalized


def _force_quality_for_model(image_model: str, provider: str, quality: str) -> str:
    normalized_model = str(image_model or "").lower()
    normalized_provider = str(provider or "").lower()
    normalized_quality = (quality or "").lower() or "low"
    if normalized_provider == "openai" and normalized_model.startswith("gpt-image-1.5"):
        if normalized_quality != "low":
            logger.info(
                "QUALITY-GUARD: Übersteuere Qualität '%s' -> 'low' für Modell '%s'.",
                normalized_quality,
                image_model,
            )
        return "low"
    return normalized_quality


async def save_mp3_tool(
    content: str = None,
    filename: str = "output.mp3",
    voice: str = "fable",
    last_ssml_content: str = None,
    **kwargs,
) -> ToolResultV1:
    """
    Synthetisiert Text zu Audio (MP3) und speichert ihn auf dem Desktop.
    Wenn kein Inhalt übergeben wird, versucht das Tool, den letzten gesprochenen Text (SSML) zu nutzen.
    Gibt ToolResultV1 zurück.
    """
    from backend.utils.paths import get_desktop_path

    started_at = time.perf_counter()
    skill_name = "system.save_mp3"

    def _elapsed_ms() -> int:
        return int((time.perf_counter() - started_at) * 1000)

    try:
        if not content and last_ssml_content:
            content = last_ssml_content

        if not content:
            logger.warning("skill=%s status=error code=INVALID_INPUT", skill_name)
            return tool_err_v1(
                "INVALID_INPUT",
                "Kein Text zum Speichern gefunden.",
                started_at=started_at,
                tags=["media"],
            )

        if not filename.lower().endswith(".mp3"):
            filename += ".mp3"

        desktop_path = get_desktop_path()
        if not desktop_path:
            logger.warning("skill=%s status=error code=PATH_NOT_FOUND", skill_name)
            return tool_err_v1(
                "PATH_NOT_FOUND",
                "Desktop-Pfad nicht gefunden.",
                started_at=started_at,
                tags=["media"],
            )

        path = os.path.join(desktop_path, os.path.basename(filename))

        if content.strip().startswith("<speak>"):
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logger.warning("skill=%s status=error code=PROVIDER_KEY_MISSING", skill_name)
                return tool_err_v1(
                    "PROVIDER_KEY_MISSING",
                    "OpenAI API Key fehlt für SSML.",
                    started_at=started_at,
                    tags=["media"],
                )

            client = AsyncOpenAI(api_key=api_key)
            resp = await client.audio.speech.create(model="tts-1-hd", voice=voice, input=content)

            audio_segment = AudioSegment.from_file(io.BytesIO(resp.content), format="mp3")
            audio_segment.export(path, format="mp3")
        else:
            from backend.main import load_config

            config = load_config()
            tts = TTSService(config=config, tts_settings=config.get("tts_settings", {}))
            audio = tts.synthesize(text=content, voice="piper_de_DE-thorsten-medium")
            if audio:
                with open(path, "wb") as f:
                    f.write(audio)
            else:
                logger.warning("skill=%s status=error code=TTS_NO_DATA", skill_name)
                return tool_err_v1(
                    "TTS_NO_DATA",
                    "Lokale TTS hat keine Daten geliefert.",
                    started_at=started_at,
                    tags=["media"],
                )

        logger.info("skill=%s status=ok path=%s ms=%s", skill_name, path, _elapsed_ms())
        return tool_ok_v1(
            {"file_path": path, "filename": os.path.basename(path)},
            message=f"MP3 gespeichert: {os.path.basename(path)}",
            tags=["media"],
            started_at=started_at,
        )
    except Exception as e:
        logger.error(
            "skill=%s status=error code=TTS_FAILED error=%s ms=%s",
            skill_name,
            e,
            _elapsed_ms(),
            exc_info=True,
        )
        return tool_err_v1(
            "TTS_FAILED",
            str(e),
            started_at=started_at,
            tags=["media"],
        )


@retry(stop=stop_after_attempt(2))
async def _generate_image_tool_internal(api_key: str, provider: str, image_model: str, prompt: str, size: str = "1024x1024", quality: str = "low", **kwargs) -> Dict:
    """Interne Funktion zur Bildgenerierung, die den spezifischen Provider und das Modell nutzt."""
    if provider == "ollama":
        timeout = aiohttp.ClientTimeout(total=None)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "http://127.0.0.1:8188/sdapi/v1/txt2img",
                json={"prompt": prompt},
            ) as resp:
                resp.raise_for_status()
                logger.info("media_tools: ollama local engine response status=%s", resp.status)
                result = await resp.json()
                image_url = result.get("images", [{}])[0].get("url")
                if not image_url:
                    logger.error(
                        "media_tools: ollama response missing image url for prompt '%s': %s",
                        prompt,
                        result,
                    )
                return {"url": image_url, "cost": 0.0}
    narrative_prompt = kwargs.pop("narrative_prompt", prompt)
    preset_context = kwargs.pop("preset_context", {})
    logger.debug(f"media_tools.py: _generate_image_tool_internal - Instantiating LLM provider for: {provider}")
    llm_provider_instance = llm_gateway.get_provider(provider)
    logger.debug(f"media_tools.py: _generate_image_tool_internal - Calling generate_image for model: {image_model} with provider: {type(llm_provider_instance).__name__}")
    res = await llm_provider_instance.generate_image(
        api_key,
        image_model,
        prompt,
        narrative_prompt=narrative_prompt,
        preset_context=preset_context,
        size=size,
        quality=quality,
        **kwargs,
    )
    logger.debug(f"media_tools.py: _generate_image_tool_internal - Result from generate_image: {res}")
    return {"url": res.get("image_url"), "cost": res.get("cost")}


async def generate_image_tool(
    prompt: str, size: str = "1024x1024", quality: str = "low", db=None, **kwargs
) -> ToolResultV1:
    """
    BILDGENERATOR. NUTZE IMMER DIESES TOOL, WENN DER USER EIN BILD ERSTELLEN, ZEICHNEN ODER GENERIEREN MÖCHTE.
    Verwende NIEMALS system.create_pdf, wenn der Nutzer nach einem Bild fragt!
    Generiert ein Bild via DALL-E/Gemini, lädt es lokal herunter und speichert es für das Image Studio in der DB.
    """
    start_time = time.perf_counter()
    from backend.data import models
    from backend.services import llm_gateway
    from backend.utils.config_loader import load_config_data, load_model_catalog

    try:
        config = load_config_data()
        current_provider = config.get("last_used_provider", "openai")

        try:
            image_model_id = await llm_gateway.get_active_image_generation_model(current_provider)
        except Exception as e:
            logger.warning(f"Gateway Fehler ignoriert: {e}. Nutze Fallback.")
            image_model_id = "gpt-image-1.5" if current_provider == "openai" else "gemini-3-pro-image-preview"

        if current_provider == "openai":
            active_text_model = config.get("last_used_model")
            text_model_details = llm_gateway.get_model_details(active_text_model)
            image_model_id = text_model_details.get("image_generation_model", "gpt-image-1.5")
            logger.info(
                f"Using image_generation_model '{image_model_id}' from active text model '{active_text_model}'."
            )
        elif current_provider == "gemini":
            image_model_id = "gemini-2.5-flash-image"
            logger.info(f"Gemini-Provider aktiv. Erzwinge kostengünstiges Chat-Modell: '{image_model_id}'.")

        models_catalog = load_model_catalog()
        if isinstance(models_catalog, str):
            try:
                models_catalog = json.loads(models_catalog)
            except Exception:
                models_catalog = []

        target_model = {}
        if isinstance(models_catalog, list):
            target_model = next(
                (m for m in models_catalog if isinstance(m, dict) and m.get("id") == image_model_id),
                {},
            )
        elif isinstance(models_catalog, dict):
            target_model = models_catalog.get(image_model_id, {})

        model_details = target_model or llm_gateway.get_model_details(image_model_id)

        pricing_info = model_details.get("pricing", {}) if isinstance(model_details, dict) else {}
        requested_quality = _normalize_image_quality(quality, current_provider)
        ALLOWED_SIZES = pricing_info.get(requested_quality, {}).keys() or ["1024x1024"]
        ALLOWED_QUALITIES = pricing_info.keys() or ["low", "medium", "high"]

        default_size = model_details.get("default_size", "1024x1024") if isinstance(model_details, dict) else "1024x1024"
        default_quality = model_details.get("default_quality", "medium") if isinstance(model_details, dict) else "medium"

        final_size = size if size in ALLOWED_SIZES else default_size
        final_quality = requested_quality if requested_quality in ALLOWED_QUALITIES else default_quality
        final_quality = _force_quality_for_model(image_model_id, current_provider, final_quality)

        if size not in ALLOWED_SIZES:
            logger.warning(f"Ungültige Größe '{size}' für Modell '{image_model_id}'. Fallback auf '{final_size}'.")
        if requested_quality not in ALLOWED_QUALITIES:
            logger.warning(
                f"Ungültige Qualität '{requested_quality}' für Modell '{image_model_id}'. Fallback auf '{final_quality}'."
            )

        api_key = None
        if current_provider != "ollama":
            api_key = keyring.get_password("Janus-Projekt", current_provider)
            if not api_key:
                return tool_err_v1(
                    "PROVIDER_KEY_MISSING",
                    f"API Key für '{current_provider}' fehlt.",
                    started_at=start_time,
                    tags=["media"],
                )
        else:
            api_key = "local_engine_mode"

        logger.info(
            f"Skill generate_image: Provider '{current_provider}', Modell '{image_model_id}', "
            f"Quality '{final_quality}', Size '{final_size}'."
        )

        res = await _generate_image_tool_internal(
            api_key=api_key,
            provider=current_provider,
            image_model=image_model_id,
            prompt=prompt,
            size=final_size,
            quality=final_quality,
            **kwargs,
        )

        generated_path = res.get("url")
        local_path = generated_path

        if not local_path:
            return tool_err_v1(
                "GENERATION_FAILED",
                "Der Provider lieferte kein Bild zurück.",
                started_at=start_time,
                tags=["media"],
            )

        safe_title = "".join([c if c.isalnum() else "_" for c in prompt[:25]])
        if os.path.isfile(local_path):
            try:
                with open(local_path, "rb") as src:
                    image_bytes = src.read()
                web_path = save_image_from_bytes(image_bytes, description=safe_title)
                if web_path:
                    local_path = web_path
                else:
                    logger.warning("media_tools: Failed to save %s via image_manager", local_path)
            except OSError as io_err:
                logger.error("media_tools: file save failed for %s: %s", local_path, io_err, exc_info=True)
                return tool_err_v1(
                    "IMAGE_SAVE_FAILED",
                    f"Bilddatei konnte nicht gelesen oder kopiert werden: {io_err}",
                    details={"path": local_path},
                    started_at=start_time,
                    tags=["media"],
                )

        if db:
            new_image = models.GeneratedImage(
                prompt=prompt,
                provider=current_provider,
                model=image_model_id,
                image_url=local_path,
                is_uploaded=False,
            )
            db.add(new_image)
            db.commit()
            logger.info(f"Bild erfolgreich in DB gespeichert (ID: {new_image.id}) für Image Studio.")
        else:
            logger.warning("Kein DB-Objekt an generate_image_tool übergeben. Bild fehlt im Image Studio Verlauf!")

        return tool_ok_v1(
            {
                "message": "Bild erfolgreich generiert und im Image Studio gespeichert.",
                "local_image_path": local_path,
                "image_url": local_path,
                "markdown_image": f"![{safe_title}]({local_path})",
                "prompt_used": prompt,
                "cost": res.get("cost"),
            },
            message="Bild erfolgreich generiert.",
            tags=["media"],
            started_at=start_time,
        )
    except Exception as e:
        logger.error(f"Fehler in generate_image_tool: {e}", exc_info=True)
        return tool_err_v1(
            "UNEXPECTED_ERROR",
            str(e),
            started_at=start_time,
            tags=["media"],
        )
