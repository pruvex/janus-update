# backend/api/routers/images.py
import logging
import keyring
import os
import json
import re
import hashlib
import io
import tempfile
import uuid
from PIL import Image
from fastapi.responses import FileResponse
from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from typing import List
from pydantic import BaseModel
from tenacity import RetryError  # For handling retryable operations
from backend.utils.paths import get_images_dir
from sqlalchemy.orm import Session
from backend.data import schemas, crud

class PreviewRequest(BaseModel):
    image_base64: str
    format: str # z.B. "jpg_95", "webp", "avif"

# --- FIX 1: Imports bereinigen ---
# Nur get_db bleibt in database
from backend.data.database import get_db
# Modelle kommen aus models
import backend.data.models as models
# Services importieren
from backend.services import image_manager, cost_service, cost_calculator
from backend.services.quality_gate import quality_gate_service
import openai
from backend.llm_providers.openai.service import OpenAIServiceProvider
from backend.llm_providers.gemini.service import GeminiServiceProvider
from backend.data.presets import get_preset, PRESET_DATABASE, generate_preview_prompt
from backend.services.director_service import director_service
# ---------------------------------
from datetime import datetime

DEFAULT_MAX_IMAGE_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_UPLOAD_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


async def _enforce_image_upload_limit(file: UploadFile) -> None:
    max_bytes = int(os.getenv("JANUS_MAX_IMAGE_UPLOAD_BYTES", str(DEFAULT_MAX_IMAGE_UPLOAD_BYTES)))
    sample = await file.read(max_bytes + 1)
    await file.seek(0)
    if len(sample) > max_bytes:
        logger.warning(
            "[ABUSE-LIMIT] scope=upload-image filename_len=%s bytes_over_limit=true",
            len(file.filename or ""),
        )
        raise HTTPException(
            status_code=413,
            detail="Die Bilddatei ist zu groß. Bitte lade eine kleinere Datei hoch.",
        )


async def _generate_and_rename_image_in_background(
    db: Session,
    image_id: int,
    provider: str  # <-- NEU: Provider-Parameter hinzugefügt
):
    """
    Hintergrundaufgabe zur intelligenten Umbenennung eines Bildes basierend auf seinem Inhalt.
    Integriert Vorschläge von GPT-5 (strukturierte Ausgabe, Metadaten, Hash).
    """
    try:
        logger.info(f"[BG-Task] Starte intelligente Umbenennung für Bild-ID {image_id}.")
        image_entry = db.query(models.GeneratedImage).filter(models.GeneratedImage.id == image_id).first()
        if not image_entry:
            logger.error(f"[BG-Task] Bild-ID {image_id} nicht in DB gefunden. Breche ab.")
            return

        old_filename = os.path.basename(image_entry.image_url)
        image_path = os.path.join(get_images_dir(), old_filename)

        if not os.path.exists(image_path):
            logger.error(f"[BG-Task] Bilddatei nicht gefunden: {image_path}. Breche ab.")
            return

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # 1. Prompt-Härtung: Wir fordern JSON an UND geben ein deutsches Beispiel
        naming_prompt = (
            "Analysiere das Bild und antworte mit einem JSON-Objekt mit zwei Schlüsseln: 'keywords' und 'style'.\n"
            "- 'keywords': Eine Liste von 3-4 beschreibenden, generischen, DEUTSCHEN Schlagwörtern für das Hauptmotiv. KEINE Namen von Personen, Marken oder spezifischen Orten.\n"
            "- 'style': Ein einziger, kurzer DEUTSCHER Begriff für den künstlerischen Stil (z.B. 'foto', 'aquarell', '3d-render', 'zeichnung').\n"
            "Beispiel für eine perfekte Antwort bei einem Bild von einem roten Apfel:\n"
            "{\n"
            "  \"keywords\": [\"roter_apfel\", \"obst\", \"stillleben\"],\n"
            "  \"style\": \"foto\"\n"
            "}\n"
            "Antworte NUR mit dem JSON-Objekt."
        )

        # 2. Vision-Analyse durchführen
        api_key = get_api_key(provider)  # Verwende den übergebenen Provider
        evaluation = await quality_gate_service.evaluate_image(
            provider=provider,
            api_key=api_key,
            image_bytes=image_bytes,
            prompt=naming_prompt,
            force_json_schema=False  # Wir parsen das JSON selbst
        )
        
        # --- COST TRACKING: Log vision service usage ---
        usage_data = evaluation.get("usage")
        model_used = evaluation.get("model")
        
        if usage_data and model_used:
            try:
                # Calculate costs using the cost calculator
                _, cost_info = cost_calculator.calculate_cost(
                    model_id=model_used, 
                    usage_data=usage_data
                )
                
                total_cost = cost_info.get("total_cost", 0.0)
                
                if total_cost > 0:
                    # KORREKTUR: Nutze den importierten cost_service
                    cost_service.create_cost_entry(
                        db=db,  # Wichtig: Wir müssen die DB-Session übergeben
                        amount=total_cost,
                        model=model_used,
                        provider=provider,
                        source_type="vision_labeling",
                        input_tokens=usage_data.get("input_tokens", 0),
                        output_tokens=usage_data.get("output_tokens", 0),
                        image_quality=None,
                        image_size=None,
                        image_cost=0.0
                    )
                    logger.info(f"[BG-Task] Vision costs tracked: {total_cost:.6f}€ ({model_used})")
            except Exception as cost_e:
                logger.warning(f"[BG-Task] Error in cost tracking: {cost_e}")
        # --- END COST TRACKING ---
        
        raw_response = evaluation.get("suggestion", "")
        if not raw_response:
            logger.warning("[BG-Task] Vision model did not return a response.")
            return

        # 3. JSON parsen und Tags extrahieren
        try:
            # Bereinige die Antwort, um sicherzustellen, dass es valides JSON ist
            json_str = raw_response.strip().replace("```json\n", "").replace("\n```", "")
            data = json.loads(json_str)
            keywords = data.get("keywords", [])
            style = data.get("style", "art")
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"[BG-Task] Konnte kein valides JSON aus der Vision-Antwort parsen: {raw_response}")
            logger.exception(e)
            return # Sicherer Abbruch

        if not keywords:
            logger.warning("[BG-Task] JSON enthielt keine Keywords.")
            return

        # 4. Dateinamen konstruieren (Keywords + Style + Hash)
        tags_for_db = ", ".join(keywords)  # In der DB speichern wir die echten Umlaute!
        
        def clean_german(text):
            # Umlaute ersetzen für Dateisystem-Sicherheit
            text = text.lower()
            text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
            text = text.replace(" ", "_")
            # Alles was nicht a-z, 0-9 oder _ ist, entfernen
            return re.sub(r'[^a-z0-9_]', '', text)

        filename_parts = [clean_german(k) for k in keywords]
        filename_parts.append(clean_german(style))
        
        # Kurzer, einzigartiger Hash aus ID und Zeitstempel
        hash_input = f"{image_id}-{datetime.utcnow().timestamp()}".encode('utf-8')
        short_hash = hashlib.sha1(hash_input).hexdigest()[:8]
        
        base_filename = "_".join(filename_parts)[:50] # Auf 50 Zeichen kürzen
        final_base_filename = f"{base_filename}__{short_hash}"

        # 5. Sicheres Umbenennen
        directory = os.path.dirname(image_path)
        extension = os.path.splitext(old_filename)[1]
        new_filename = f"{final_base_filename}{extension}"
        
        # Kollisionsprüfung (sollte durch Hash selten sein, aber sicher ist sicher)
        counter = 1
        while os.path.exists(os.path.join(directory, new_filename)):
            new_filename = f"{final_base_filename}_{counter}{extension}"
            counter += 1
        
        new_image_path = os.path.join(directory, new_filename)
        os.rename(image_path, new_image_path)

        # 6. Datenbank aktualisieren
        image_entry.image_url = f"/user_images/{new_filename}"
        image_entry.tags = tags_for_db # Die neuen Tags speichern
        db.commit()
        db.refresh(image_entry)
        
        logger.info(f"[BG-Task] Bild erfolgreich umbenannt: '{old_filename}' -> '{new_filename}'")

    except Exception as e:
        logger.error(f"[BG-Task] Unerwarteter Fehler bei der intelligenten Umbenennung: {e}", exc_info=True)

logger = logging.getLogger("janus_backend")
router = APIRouter()

# Instanzen der Provider erstellen
openai_provider = OpenAIServiceProvider()
gemini_provider = GeminiServiceProvider()

PROVIDER_MAP = {
    "openai": openai_provider,
    "gemini": gemini_provider,
}

# Konfiguration für Quality Gate Retries und Thresholds
QUALITY_GATE_CONFIG = {
    "none":   {"retries": 0, "threshold": 0},
    "low":    {"retries": 1, "threshold": 70},
    "medium": {"retries": 2, "threshold": 80},
    "high":   {"retries": 3, "threshold": 90}
}

def get_api_key(provider: str) -> str:
    """Holt den API-Schlüssel für den gegebenen Provider aus dem Keyring."""
    key = keyring.get_password("Janus-Projekt", provider)
    if not key:
        raise HTTPException(status_code=400, detail=f"API-Schlüssel für {provider} nicht gefunden.")
    return key

@router.post("/images/generate", response_model=schemas.GeneratedImage)
async def generate_image(
    image_request: schemas.GeneratedImageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Nimmt eine Anfrage zur Bilderstellung entgegen.
    Unterstützt Text-zu-Bild, Bild-zu-Bild und Quality Gates.
    """
    logger.info(f"Anfrage zur Bilderstellung erhalten für Provider {image_request.provider} und Modell {image_request.model}")

    # --- STYLE TRANSFER WEICHE (WIEDERHERGESTELLT) ---
    is_style_transfer = (
        (image_request.apply_preset_to_refine or image_request.apply_preset_to_edit) and 
        image_request.style_preset and 
        image_request.variation_preset and 
        image_request.reference_image_url
    )

    if is_style_transfer:
        logger.info("Style Transfer Modus erkannt. Umgehe Director für den Haupt-Prompt.")
        
        # Lade Preset nur für den Namen
        preset_config, _ = get_preset(
            provider=image_request.provider,
            style=image_request.style_preset,
            variation=image_request.variation_preset,
            user_prompt=""
        )
        
        if preset_config:
            user_modification = image_request.prompt or "Keine."
            
            # WICHTIG: Wir überschreiben den User-Prompt mit einer sehr direkten Anweisung
            image_request.prompt = (
                f"Dies ist ein Stil-Transfer. Ignoriere den ursprünglichen Prompt. "
                f"Deine Aufgabe ist es, das Motiv des Basisbildes exakt beizubehalten, "
                f"aber es im Stil von '{preset_config.name}' neu zu rendern. "
                f"Zusätzliche User-Anweisung: '{user_modification}'."
            )
            logger.info(f"Neuer Style-Transfer-Prompt: {image_request.prompt}")
    
    # --- ENDE DER WIEDERHERSTELLUNG ---

    # --- MAGIC PREVIEW PROMPT (NEU) ---
    # Wenn der User "PREVIEW" eingibt, generieren wir automatisch das perfekte Vorschaubild
    if image_request.prompt and image_request.prompt.strip().upper() == "PREVIEW" and image_request.style_preset and image_request.variation_preset:
        logger.info("Magic Preview Prompt detected! Generating master prompt...")
        
        # Config laden (ohne Prompt, nur um an die Daten zu kommen)
        config, _ = get_preset(
            provider=image_request.provider,
            style=image_request.style_preset,
            variation=image_request.variation_preset,
            user_prompt=""
        )
        
        if config:
            # Den Master-Prompt generieren
            magic_prompt = generate_preview_prompt(config)
            # Den User-Prompt damit überschreiben
            image_request.prompt = magic_prompt
            logger.info(f"Preview Prompt generated: {magic_prompt[:100]}...")
            
            # WICHTIG: Wir deaktivieren hier temporär komplexe Logik, 
            # damit das Bild "rein" bleibt und nicht durch Referenzen verfälscht wird.
            image_request.previous_response_id = None
            image_request.reference_image_url = None
            # Auch Presets im Request deaktivieren, damit sie nicht doppelt angewendet werden
            # (Der Prompt enthält ja schon alle Anweisungen)
            # image_request.style_preset = None 
            # image_request.variation_preset = None
    # ----------------------------------
    
    # 1. Preset-Text laden und in den Prompt integrieren
    if image_request.style_preset and image_request.variation_preset:
        try:
            presets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config', 'image_presets.json')
            if os.path.exists(presets_path):
                with open(presets_path, "r", encoding="utf-8") as f:
                    presets_data = json.load(f)
            
                if (image_request.style_preset in presets_data and 
                    image_request.variation_preset in presets_data[image_request.style_preset]):
                    
                    preset_config = presets_data[image_request.style_preset][image_request.variation_preset]
                    system_prompt_add = preset_config.get("system_prompt_add", "")
                    
                    user_input = image_request.prompt if image_request.prompt else ""
                    
                    # Standard prompt generation without style transfer
                    image_request.prompt = f"{system_prompt_add}\n\nUSER REQUEST:\n{user_input}"
                        
            else:
                logger.warning(f"Preset file not found at {presets_path}")
                
        except Exception as e:
            logger.error(f"Error applying preset text: {e}")

    provider_service = PROVIDER_MAP.get(image_request.provider)
    if not provider_service:
        raise HTTPException(status_code=400, detail=f"Provider '{image_request.provider}' wird nicht unterstützt.")
        
    api_key = get_api_key(image_request.provider)
    
    # --- BILDER LADEN (Universal-Loader) ---
    image_bytes_list = []
    target_urls = []
    target_filenames = []  # Initialize the list here to prevent NameError
    
    if image_request.reference_image_urls and len(image_request.reference_image_urls) > 0:
        target_urls = image_request.reference_image_urls
        logger.info(f"Kombinieren-Modus aktiv: {len(target_urls)} Bilder angefordert.")
    elif image_request.reference_image_url:
        target_urls = [image_request.reference_image_url]
        logger.info("Single-Image Modus aktiv.")

    if target_urls:
        for url in target_urls:
            try:
                # Wir extrahieren nur den Dateinamen aus der URL
                from urllib.parse import urlparse
                filename = os.path.basename(urlparse(url).path)
                
                # Wir benutzen unseren eigenen, robusten Endpunkt, um die Datei zu finden
                # (indem wir die Logik quasi simulieren)
                images_dir = get_images_dir()
                file_path = os.path.join(images_dir, filename)
                
                # Prüfen, ob auch im Uploads-Unterordner geschaut werden muss
                if not os.path.exists(file_path):
                    uploads_path = os.path.join(images_dir, "uploads", filename)
                    if os.path.exists(uploads_path):
                        file_path = uploads_path
                    else:
                        # Wenn wir es immer noch nicht finden, ist es ein echter Fehler
                        raise HTTPException(status_code=404, detail=f"Reference image file not found: {filename}")

                # Datei einlesen und zur Liste hinzufügen
                with open(file_path, "rb") as f:
                    image_bytes_list.append(f.read())
                logger.info(f"Referenzbild geladen: {file_path}")

            except HTTPException as he:
                raise he # Fehler direkt weitergeben
            except Exception as e:
                logger.error(f"Fehler beim Laden des Referenzbildes {url}: {e}")
                raise HTTPException(status_code=500, detail=f"Could not load reference image: {str(e)}")
    
    try:
        # STUFE 1: CONFIGURATOR (logic.py)
        # Sammelt alle Regeln und den Kontext
        preset_config, context_dict = get_preset(
            provider=image_request.provider,
            style=image_request.style_preset,
            variation=image_request.variation_preset,
            user_prompt=image_request.prompt or ""  # KORREKTUR: Direkter Zugriff auf den Request-Prompt
        )
        
        # STUFE 2: DIRECTOR (director_service.py) - mit Edit-Modus-Signal
        
        # PRÜFUNG: Handelt es sich um eine einfache Bearbeitung eines eigenen Bildes?
        # Kriterium: Ein Referenzbild ist da, aber KEIN Preset ist aktiv.
        is_simple_edit_mode = bool(image_request.reference_image_url) and not (image_request.style_preset and image_request.variation_preset)

        # WICHTIG: Füge ein klares Signal für den Director zum Kontext hinzu
        context_dict["is_edit_mode"] = is_simple_edit_mode
        context_dict["mode"] = "refine" if image_request.previous_response_id else "new"
        context_dict["previous_response_id"] = image_request.previous_response_id
        context_dict["reference_image_url"] = image_request.reference_image_url
        # WICHTIG: Die Liste muss hier rein!
        context_dict["reference_image_urls"] = image_request.reference_image_urls
        
        if is_simple_edit_mode:
            logger.info("Director: Operating in 'Simple Edit Mode'. Will enhance, not replace.")
        
        # Der Director wird jetzt IMMER aufgerufen, aber sein Verhalten ändert sich basierend auf dem Kontext.
        director_client = openai.AsyncOpenAI(api_key=get_api_key("openai"))
        narrative_prompt = await director_service.create_narrative_prompt(
            context=context_dict,
            director_model="gpt-5.2",
            client=director_client
        )
        
        # Parameter als Dictionary extrahieren
        params_dict = {}
        if image_request.parameters:
            if hasattr(image_request.parameters, "model_dump"):
                params_dict = image_request.parameters.model_dump()
            elif isinstance(image_request.parameters, dict):
                params_dict = image_request.parameters
        
        full_model_id = image_request.model
        
        # Die Entscheidung, ob ein Preset angewendet wird, wird jetzt direkt aus dem Frontend-Request abgeleitet.
        # Die Variable 'shouldSendPresets' in image-studio.js steuert dies.
        # Wir prüfen einfach, ob die entsprechenden Felder im Request vorhanden sind.
        should_apply_preset = bool(image_request.style_preset and image_request.variation_preset)
        
        logger.info(f"Ergebnis der Prüfung 'should_apply_preset': {should_apply_preset}")


        
        final_prompt = narrative_prompt  # Der finale Prompt kommt jetzt vom Director

        # --- QUALITY GATE SETUP ---
        current_prompt = final_prompt
        gate_level = image_request.quality_gate_level or "none"
        gate_config = QUALITY_GATE_CONFIG.get(gate_level, QUALITY_GATE_CONFIG["none"])
        max_retries = gate_config["retries"]
        min_score = gate_config["threshold"]  # Standard-Threshold aus der Konfiguration
        
        # Überschreibe den Threshold, falls im Preset definiert
        vision_criteria = []
        if preset_config:
            if hasattr(preset_config, 'vision_criteria') and preset_config.vision_criteria:
                vision_criteria = preset_config.vision_criteria
            if hasattr(preset_config, 'vision_pass_score') and preset_config.vision_pass_score is not None:
                min_score = preset_config.vision_pass_score  # Überschreibe mit Preset-spezifischem Wert
        
        attempt = 0
        final_result = None
        last_provider_error = None
        
        # Stats-Objekt initialisieren
        qg_stats = {
            "was_active": gate_level != "none",
            "attempts": 0,
            "total_cost": 0.0,
            "final_score": 0,
            "min_required_score": min_score
        }

        logger.info(f"Starte Generierung mit Quality Gate: {gate_level} (Max Retries: {max_retries})")

        # --- DER LOOP ---
        # Wir interpretieren max_retries jetzt als "Maximal erlaubte Versuche insgesamt"
        # Wenn max_retries im Config z.B. 3 ist, machen wir 3 Versuche.
        # Falls der Wert 0 ist (QG aus), machen wir trotzdem 1 Versuch.
        total_allowed_attempts = max(1, max_retries)
        
        for attempt in range(total_allowed_attempts):
            qg_stats["attempts"] = attempt + 1
            logger.info(f"--- Generierungs-Versuch {qg_stats['attempts']} von {total_allowed_attempts} ---")

            try:
                result = await provider_service.generate_image(
                    api_key=api_key,
                    model=image_request.model,
                    prompt=image_request.prompt,  # Original user prompt for context
                    narrative_prompt=narrative_prompt,  # Creative text from director
                    preset_context=context_dict,  # Technical rules from configurator
                    image_bytes_list=image_bytes_list,
                    previous_response_id=image_request.previous_response_id,
                    previous_image_id=image_request.previous_image_id,
                    mask_image_data=image_request.mask_image_data,
                    **params_dict  # Pass through all other parameters from frontend
                )
            except Exception as e:
                # FIX: Extract the actual error if it's wrapped in a RetryError
                if isinstance(e, RetryError):
                    try:
                        e = e.last_attempt.exception()
                    except:
                        pass  # Fallback if extraction fails

                last_provider_error = str(e)
                
                # SPEZIAL-CHECK: OpenAI Guthaben leer
                if "insufficient_quota" in last_provider_error or "exceeded your current quota" in last_provider_error:
                    logger.warning("OpenAI Quota Exceeded.")
                    raise HTTPException(
                        status_code=402,  # 402 Payment Required is semantically appropriate
                        detail="Ihr OpenAI-Guthaben ist aufgebraucht. Bitte prüfen Sie Ihre Abrechnungsdaten bei OpenAI."
                    )

                logger.error(
                    f"Provider-Fehler bei der Bilderstellung ({image_request.provider}/{image_request.model}): {e}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Provider-Fehler ({image_request.provider}): {last_provider_error}",
                )
            
            final_result = result
            image_url = result.get("image_url")
            
            # --- LEAK FIX: Prompt für Anzeige/DB aktualisieren ---
            # Wenn der Provider einen "echten" Prompt zurückgibt (vom Orchestrator),
            # nutzen wir diesen als 'Wahrheit' für die DB und das Frontend.
            # Wenn nicht, nutzen wir den ORIGINALEN User-Prompt (image_request.prompt),
            # NIEMALS die technische Instruktion (current_prompt/final_prompt).
            
            actual_image_prompt = result.get("revised_prompt")
            if not actual_image_prompt:
                actual_image_prompt = image_request.prompt  # Fallback auf User-Input (z.B. "ein apfel")
            
            # Aktualisiere current_prompt für den nächsten Loop-Durchlauf
            # ACHTUNG: Hier müssen wir vorsichtig sein, um das Preset nicht zu verlieren
            if actual_image_prompt and actual_image_prompt != current_prompt:
                logger.info(f"Aktualisiere Prompt für Quality Gate: {actual_image_prompt[:100]}...")
                current_prompt = actual_image_prompt
            
            # Kosten für diesen Versuch addieren
            image_cost_details = result.get("cost", {})
            qg_stats["total_cost"] += image_cost_details.get("total_cost", 0.0)

            # --- FIX: Kosten speichern ---
            # Werte extrahieren für sauberen Aufruf
            usage_data = result.get("usage", {})
            cost_data = result.get("cost", {})
            
            cost_service.create_cost_entry(
                db=db,
                amount=cost_data.get("total_cost", 0.0),
                model=full_model_id,
                provider=image_request.provider,
                source_type="image_generation",
                input_tokens=usage_data.get("input_tokens", 0),
                output_tokens=usage_data.get("output_tokens", 0),
                # Jetzt können wir diese Parameter übergeben!
                image_quality=usage_data.get("image_quality"),
                image_size=usage_data.get("image_size"),
                image_cost=cost_data.get("image_cost", 0.0)
            )

            if gate_level == "none" or not image_url:
                break

            # --- QUALITY GATE RACE CONDITION FIX v2 ---
            filename_for_check = image_url.split("/")[-1]
            # WICHTIG: Definiere die Variable außerhalb des try-Blocks, damit sie im Fehlerfall existiert
            path_for_check = os.path.join(get_images_dir(), filename_for_check) 
            
            # Prüfe auch im uploads-Ordner
            if not os.path.exists(path_for_check):
                path_for_check = os.path.join(get_images_dir(), "uploads", filename_for_check)

            try:
                file_found = False
                for _ in range(5): 
                    if os.path.exists(path_for_check):
                        file_found = True
                        break
                    await asyncio.sleep(0.2)

                if not file_found:
                    # Jetzt können wir die Variable sicher verwenden
                    logger.error(f"Konnte Bild für Quality Check nicht finden: {path_for_check}")
                    break 
                
                # Quality Gate Check
                with open(path_for_check, "rb") as f:
                    img_bytes = f.read()
                
                # Führe die Qualitätsprüfung durch
                evaluation = await quality_gate_service.evaluate_image(
                    provider=image_request.provider,
                    api_key=api_key,
                    image_bytes=img_bytes,
                    prompt=current_prompt,
                    criteria=vision_criteria
                )
                
                score = evaluation.get("score", 0)
                qg_stats["final_score"] = score
                
                # Log the score regardless of pass/fail
                logger.info(f"Quality Gate Bewertung: Score {score} (Benötigt: {min_score})")
                
                if score >= min_score:
                    logger.info(f"Quality Gate BESTANDEN mit Score {score}/{min_score}.")
                    break
                
                if attempt < total_allowed_attempts - 1:
                    suggestion = evaluation.get("suggestion", "make it look more realistic")
                    logger.warning(f"Quality Gate NICHT bestanden. Optimiere Prompt... Suggestion: {suggestion}")
                    current_prompt = f"{current_prompt} - {suggestion}"
                    image_request.previous_response_id = None
                    image_request.previous_image_id = None
                else:
                    logger.warning(f"Quality Gate nach maximalen Versuchen NICHT bestanden.")
                    
            except Exception as e:
                # Hier verwenden wir die Variable 'path_for_check', die immer definiert ist
                logger.error(f"Fehler im Quality Gate Loop für Datei {path_for_check}: {e}", exc_info=True)
                break
            
            attempt += 1
        # --- ENDE LOOP ---

        if not final_result or not final_result.get("image_url"):
             extra = f" Letzter Provider-Fehler: {last_provider_error}" if last_provider_error else ""
             raise HTTPException(
                 status_code=500,
                 detail=f"Generierung fehlgeschlagen nach allen Versuchen.{extra}",
             )

        # --- LEAK FIX: Datenbank & Frontend bereinigen ---
        # Wir entscheiden hier, welcher Text gespeichert wird.
        # Priorität 1: Was das Modell tatsächlich "gesehen" hat (revised_prompt)
        # Priorität 2: Was der User eingegeben hat (image_request.prompt)
        # NIEMALS: current_prompt (das enthält die System-Instruktionen!)
        
        clean_prompt_for_db = image_request.prompt # Standard: User Input
        
        if final_result.get("revised_prompt"):
            clean_prompt_for_db = final_result.get("revised_prompt")
            # Optional: Assert gegen Leaks
            if "ROLE:" in clean_prompt_for_db or "PRESET IDENTITY:" in clean_prompt_for_db:
                logger.error("CRITICAL: Meta-Prompt Leak detected in revised_prompt! Reverting to user prompt.")
                clean_prompt_for_db = image_request.prompt

        # Wir patchen das Objekt für den CRUD-Aufruf
        original_prompt = image_request.prompt
        image_request.prompt = clean_prompt_for_db
        
        # --- PRESET PERSISTENCE FIX ---
        # Wir stellen sicher, dass die Presets im Objekt sind, bevor wir speichern.
        
        # 1. JSON Cleaning (falls es Dictionary ist)
        if isinstance(image_request.style_preset, dict):
            image_request.style_preset = json.dumps(image_request.style_preset)
        
        # 2. Wiederherstellung aus Parametern (Falls Frontend es in params versteckt hat)
        if not image_request.variation_preset and "variation_preset" in params_dict:
             image_request.variation_preset = params_dict["variation_preset"]

        # 3. WICHTIG: Im Refine-Modus müssen wir die Presets explizit setzen, 
        # falls sie im ursprünglichen Request 'None' waren (weil Checkbox aus),
        # aber wir sie trotzdem angewendet haben (z.B. durch interne Logik).
        # HIER: Wir nehmen einfach das, was im Request ankam. Wenn der User
        # "Preset anwenden" geklickt hat, sind die Daten da.
        
        # Manuelles Cleaning von Quotes (Sicherheit)
        if image_request.style_preset:
             if isinstance(image_request.style_preset, str):
                image_request.style_preset = image_request.style_preset.strip('"')
        
        if image_request.variation_preset:
             if isinstance(image_request.variation_preset, str):
                image_request.variation_preset = image_request.variation_preset.strip('"')

        # DB Eintrag erstellen
        new_image_entry = crud.create_generated_image(
            db=db, 
            image_data=image_request, 
            image_url=final_result.get("image_url")
        )

        # --- FIX: Provider ID & PRESETS HART NACHSPEICHERN ---
        
        # 1. Provider/Response ID
        provider_id = (
            final_result.get("previous_response_id") or 
            final_result.get("response_id") or 
            final_result.get("id")
        )
        if provider_id:
            new_image_entry.provider_response_id = provider_id
            
        # 2. PRESETS ERZWINGEN (Das behebt den Fehler beim Reinziehen!)
        # Wir nehmen direkt die Werte aus dem Request-Objekt
        if image_request.style_preset:
            val = image_request.style_preset
            if isinstance(val, dict): val = json.dumps(val)
            new_image_entry.style_preset = str(val).strip('"')
            
        if image_request.variation_preset:
            val = image_request.variation_preset
            new_image_entry.variation_preset = str(val).strip('"')

        # 3. Speichern
        db.add(new_image_entry)
        db.commit()
        db.refresh(new_image_entry)
        
        # Starte die Hintergrundaufgabe für die intelligente Umbenennung
        background_tasks.add_task(
            _generate_and_rename_image_in_background,
            db=db,
            image_id=new_image_entry.id,
            provider=image_request.provider  # <-- NEU: Provider übergeben
        )
        logger.info(f"Intelligente Umbenennung für Bild {new_image_entry.id} in den Hintergrund verschoben.")
        
        # Stelle den ursprünglichen Prompt wieder her
        image_request.prompt = original_prompt
        
        response_data = {
            "id": new_image_entry.id,
            "image_url": new_image_entry.image_url,
            "previous_response_id": new_image_entry.provider_response_id, # WICHTIG: Hier die neue ID zurückgeben
            "previous_image_id": final_result.get('previous_image_id'),
            "created_at": new_image_entry.created_at,
            "quality_gate_stats": qg_stats
        }
        
        return response_data

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Fehler bei der Bilderstellung: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Interne Server-Fehler bei der Bilderstellung: {str(e)}")

@router.post("/images/upload", response_model=schemas.GeneratedImage)
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Handles user-uploaded images."""
    try:
        if file.content_type not in ALLOWED_IMAGE_UPLOAD_TYPES:
            raise HTTPException(status_code=400, detail="Dieser Bildtyp wird nicht unterstützt.")
        await _enforce_image_upload_limit(file)

        new_image_entry = await image_manager.save_uploaded_file(db=db, file=file)
        return new_image_entry

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Bild konnte nicht verarbeitet werden.")

@router.get("/images/pricing")
async def get_pricing_info():
    """Gibt die Preisstruktur für die Bilderstellung zurück."""
    try:
        return cost_calculator.get_image_pricing_structure()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Preisinformationen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Preisinformationen konnten nicht geladen werden.")

@router.get("/images/context")
async def get_image_context(url: str, db: Session = Depends(get_db)):
    """Gibt den Kontext (IDs und PRESETS) für ein Bild zurück."""
    filename = url.split("/")[-1]
    
    # Wir laden alle Bilder und suchen den Treffer in Python, 
    # um Probleme mit Datenbank-Properties zu umgehen.
    all_entries = db.query(models.GeneratedImage).all()
    img_entry = next((img for img in all_entries if img.image_url and filename in img.image_url), None)
    
    if not img_entry:
        return {
            "response_id": None, 
            "image_id": None,
            "style_preset": None,
            "variation_preset": None
        }
    
    return _format_image_context_response(img_entry)

@router.get("/context_by_id/{image_id}")
async def get_image_context_by_id(image_id: int, db: Session = Depends(get_db)):
    """Gibt den Kontext (IDs und PRESETS) für ein Bild anhand seiner ID zurück."""
    img_entry = db.query(models.GeneratedImage).filter(models.GeneratedImage.id == image_id).first()
    if not img_entry:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return _format_image_context_response(img_entry)

def _format_image_context_response(img_entry):
    """Hilfsfunktion zum Formatieren der Bildkontext-Antwort."""
    # --- PRESET CLEANUP ---
    style = img_entry.style_preset
    variation = img_entry.variation_preset
    
    # Clean up JSON quotes if present (Legacy safety)
    if style and style.startswith('"') and style.endswith('"'):
        style = style[1:-1]
    if variation and variation.startswith('"') and variation.endswith('"'):
        variation = variation[1:-1]

    # --- FIX FÜR GEMINI REFINE MODE ---
    # Wenn ein Bild von einem Provider kommt (also generiert ist), aber keine ID hat (wie bei Gemini),
    # generieren wir eine künstliche ID, damit das Frontend in den "Refine Mode" schaltet 
    # statt in den "Edit Mode" (Upload).
    response_id = img_entry.provider_response_id
    
    # Prüfen ob generiert (Provider existiert) aber ID fehlt
    if not response_id and img_entry.provider and img_entry.provider != "internal":
        # Wir nutzen die interne DB-ID als Fake-Response-ID
        response_id = f"gen_{img_entry.id}_synthetic"

    return {
        "response_id": response_id, 
        "image_id": img_entry.id, 
        "style_preset": style,
        "variation_preset": variation,
        "image_url": img_entry.image_url
    }

@router.post("/images/rename", response_model=schemas.GeneratedImage)
async def rename_image(rename_request: schemas.ImageRenameRequest, db: Session = Depends(get_db)):
    """
    Benennt eine Bilddatei um.
    Version: 'Bypass-Fix' - umgeht den fehlerhaften SQLAlchemy-Filter.
    """
    import os
    import traceback
    from backend.utils.paths import get_images_dir

    logger.info("--- START RENAME (Bypass Mode) ---")
    try:
        # 1. Input validieren
        old_filename_only = os.path.basename(rename_request.old_path.replace("\\", "/"))
        if not old_filename_only:
            raise HTTPException(status_code=400, detail="Alter Dateiname fehlt.")

        logger.info(f"1. Target Filename: '{old_filename_only}'")

        # 2. DER BYPASS-FIX: Alle Bilder laden und manuell filtern
        all_images = db.query(models.GeneratedImage).all()
        image_entry = None
        for img in all_images:
            # Wir prüfen manuell, ob der Dateiname am Ende des Pfads übereinstimmt
            if img.image_url and img.image_url.endswith(old_filename_only):
                image_entry = img
                break # Wir haben es gefunden

        if not image_entry:
            logger.error(f"2. DB Search FAILED. File '{old_filename_only}' not in DB.")
            raise HTTPException(status_code=404, detail="Bild in der Datenbank nicht gefunden.")
        
        logger.info(f"2. DB Found by Bypass: ID={image_entry.id}, URL='{image_entry.image_url}'")
        
        # Ab hier ist der Code wieder der gleiche, er sollte jetzt funktionieren
        # 3. Physische Pfade berechnen
        base_dir = get_images_dir()
        relative_path = image_entry.image_url.lstrip("/").replace("user_images/", "", 1)
        old_abs_path = os.path.normpath(os.path.join(base_dir, relative_path))

        if not os.path.exists(old_abs_path):
             raise HTTPException(status_code=404, detail=f"Datei nicht auf Festplatte gefunden: {old_abs_path}")
        
        directory = os.path.dirname(old_abs_path)
        new_abs_path = os.path.join(directory, rename_request.new_filename)
        
        if os.path.exists(new_abs_path):
            raise HTTPException(status_code=409, detail="Ein Bild mit diesem Namen existiert bereits.")

        # 4. Umbenennen mit Retry
        os.rename(old_abs_path, new_abs_path)
        
        # 5. Datenbank aktualisieren
        new_rel_path = os.path.relpath(new_abs_path, base_dir).replace("\\", "/")
        new_db_url = f"/user_images/{new_rel_path}"
        
        # Das Zuweisen funktioniert, nur das Filtern war kaputt
        image_entry.image_url = new_db_url
        db.commit()
        db.refresh(image_entry)
        
        logger.info(f"5. RENAME SUCCESS. DB updated to: '{new_db_url}'")
        return image_entry

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"--- CRITICAL RENAME CRASH ---\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Server Crash: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server-Fehler: {str(e)}")

@router.get("/images/presets/list")
async def list_presets():
    """Gibt die Preset-Datenbank inkl. Metadaten für die UI zurück."""
    try:
        # Konvertiere Dataclasses in JSON-kompatible Dicts
        serializable_db = {}
        for category, presets in PRESET_DATABASE.items():
            serializable_db[category] = {}
            for name, config in presets.items():
                serializable_db[category][name] = asdict(config)
        return serializable_db
    except Exception as e:
        logger.error(f"Fehler beim Laden der Presets: {e}")
        raise HTTPException(status_code=500, detail="Could not load presets")

@router.get("/images/list_all", response_model=List[schemas.GeneratedImage])
async def list_all_images(db: Session = Depends(get_db)):
    """
    Gibt eine Liste aller in der Datenbank erfassten Bilder zurück
    (sowohl generierte als auch hochgeladene).
    Die neuesten Bilder werden zuerst angezeigt.
    """
    try:
        # WICHTIG: models.GeneratedImage statt nur GeneratedImage
        all_images = db.query(models.GeneratedImage).order_by(models.GeneratedImage.created_at.desc()).all()
        logger.info(f"Lade {len(all_images)} Bilder aus der Datenbank für die Gesamt-Galerie.")
        return all_images
    except Exception as e:
        logger.error(f"Fehler beim Auflisten aller Bilder: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Bilderliste konnte nicht geladen werden.")

@router.get("/presets")
async def get_presets():
    # Gibt die Preset-Datenbank inkl. Metadaten für die UI zurück.
    return {
        "presets": PRESET_DATABASE,
        "last_updated": datetime.now().isoformat(),
        "count": len(PRESET_DATABASE),
        "description": "Liste aller verfügbaren Presets für die Bildgenerierung."
    }

# ==============================================================================
# NEUE FUNKTION: BILD-DOWNLOAD UND KONVERTIERUNG
# ==============================================================================
@router.get("/images/{image_id}/download")
async def download_converted_image(
    image_id: int, 
    format: str, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    logger.info(f"Anfrage zum Download von Bild-ID {image_id} als Format '{format}'.")

    # Bild in der Datenbank suchen
    image_entry = db.query(models.GeneratedImage).filter(models.GeneratedImage.id == image_id).first()
    if not image_entry:
        raise HTTPException(status_code=404, detail="Image not found in database.")
    
    # Pfad zur Originaldatei ermitteln
    images_base_dir = get_images_dir()
    filename = os.path.basename(image_entry.image_url)
    original_path = os.path.join(images_base_dir, filename)
    if not os.path.exists(original_path):
        original_path = os.path.join(images_base_dir, "uploads", filename)
        if not os.path.exists(original_path):
            raise HTTPException(status_code=404, detail="Image file not found on disk.")

    base_filename = os.path.splitext(filename)[0]
    requested_format = format.lower()

    # Original PNG direkt zurückgeben
    if requested_format == 'png':
        download_filename = f"{base_filename}.png"
        return FileResponse(path=original_path, filename=download_filename, media_type='image/png')

    try:
        with Image.open(original_path) as img:
            
            # --- START DER FINALEN KORREKTUR ---

            # 1. Konvertiere nach RGB, wenn nötig.
            if img.mode != 'RGB':
                img_to_save = img.convert('RGB')
            else:
                img_to_save = img

            # 2. Definiere Dateiname und temporären Pfad VOR der if/elif Kette
            if 'tiff' in requested_format:
                file_extension = 'tiff'
            else:
                file_extension = requested_format.split('_')[0] # 'jpg_95' -> 'jpg'
            
            download_filename = f"{base_filename}.{file_extension}"
            temp_dir = tempfile.gettempdir()
            temp_filepath = os.path.join(temp_dir, f"{uuid.uuid4()}_{download_filename}")
            media_type = ""

            # 3. Jetzt die saubere if/elif Kette zum Speichern
            if requested_format.startswith('jpg'):
                try:
                    quality = int(requested_format.split('_')[1])
                except (IndexError, ValueError):
                    quality = 95
                logger.info(f"Konvertiere zu JPG (Qualität {quality})...")
                img_to_save.save(temp_filepath, format='JPEG', quality=quality)
                media_type = 'image/jpeg'

            elif requested_format == 'webp':
                logger.info("Konvertiere zu WebP (verlustfrei)...")
                img_to_save.save(temp_filepath, format='WEBP', lossless=True, quality=100)
                media_type = 'image/webp'

            elif requested_format == 'avif':
                logger.info("Konvertiere zu AVIF (verlustfrei)...")
                # KORREKTUR: lossless=True statt quality=-1
                img_to_save.save(temp_filepath, format='AVIF', lossless=True)
                media_type = 'image/avif'
                
            elif requested_format == 'pdf':
                logger.info("Konvertiere zu PDF...")
                img_to_save.save(temp_filepath, format='PDF', resolution=100.0)
                media_type = 'application/pdf'
            
            elif requested_format == 'tiff':
                logger.info("Konvertiere zu unkomprimiertem TIFF...")
                img_to_save.save(temp_filepath, format='TIFF', compression='tiff_disable')
                media_type = 'image/tiff'

            elif requested_format == 'tiff_zip':
                logger.info("Konvertiere zu verlustfrei komprimiertem TIFF (ZIP/Deflate)...")
                img_to_save.save(temp_filepath, format='TIFF', compression='tiff_deflate')
                media_type = 'image/tiff'
            else:
                # Wichtig: Temporäre Datei hier nicht erstellen lassen
                raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

            def cleanup():
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
                    logger.info(f"Temporäre Datei gelöscht: {temp_filepath}")

            background_tasks.add_task(cleanup)
            return FileResponse(path=temp_filepath, filename=download_filename, media_type=media_type)
            # --- ENDE DER FINALEN KORREKTUR ---

    except Exception as e:
        logger.error(f"Fehler bei der Bildkonvertierung für ID {image_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Image conversion failed.")

# ==============================================================================
# UNIVERSAL PREVIEW ENDPOINT
# ==============================================================================
@router.post("/images/preview/size")
async def get_preview_size(request: PreviewRequest):
    """
    Nimmt Base64-Bilddaten und ein Format entgegen,
    komprimiert das Bild im Speicher und gibt die exakte resultierende Dateigröße zurück.
    """
    try:
        import base64
        # Header entfernen falls vorhanden (data:image/png;base64,...)
        if "," in request.image_base64:
            header, encoded = request.image_base64.split(",", 1)
        else:
            encoded = request.image_base64
            
        image_data = base64.b64decode(encoded)
        
        with Image.open(io.BytesIO(image_data)) as img:
            # RGB Konvertierung für Sicherheit
            if img.mode != 'RGB':
                img_to_save = img.convert('RGB')
            else:
                img_to_save = img

            img_byte_arr = io.BytesIO()
            req_format = request.format.lower()

            # Logik analog zur Download-Funktion
            if req_format.startswith('jpg'):
                try:
                    quality = int(req_format.split('_')[1])
                except:
                    quality = 95
                img_to_save.save(img_byte_arr, format='JPEG', quality=quality)
            
            elif req_format == 'webp':
                img_to_save.save(img_byte_arr, format='WEBP', lossless=True, quality=100)
                
            elif req_format == 'avif':
                img_to_save.save(img_byte_arr, format='AVIF', lossless=True)

            # --- NEU: Fehlende Formate hinzugefügt ---
            elif req_format == 'png':
                img_to_save.save(img_byte_arr, format='PNG', optimize=True)

            elif req_format == 'pdf':
                img_to_save.save(img_byte_arr, format='PDF', resolution=100.0)

            elif req_format == 'tiff':
                img_to_save.save(img_byte_arr, format='TIFF', compression='tiff_disable')
            
            elif req_format == 'tiff_zip':
                img_to_save.save(img_byte_arr, format='TIFF', compression='tiff_deflate')
            
            else:
                return {"file_size_bytes": -1}
            # -----------------------------------------
            
            # Größe ermitteln
            file_size_bytes = img_byte_arr.tell()
            
            return {"file_size_bytes": file_size_bytes}

    except Exception as e:
        logger.error(f"Fehler bei der Größenvorschau: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Preview generation failed.")

# ==============================================================================
# NEUE FUNKTION: BILD LÖSCHEN
# ==============================================================================
@router.delete("/images/{image_id}")
async def delete_image(image_id: int, db: Session = Depends(get_db)):
    """
    Löscht ein Bild endgültig.
    Der Pfad /api/images/... ist hier hartcodiert, um exakt mit der Frontend-Anfrage übereinzustimmen.
    """
    logger.info(f"Löschanfrage für Bild-ID {image_id} erhalten.")

    image_entry = db.query(models.GeneratedImage).filter(models.GeneratedImage.id == image_id).first()
    if not image_entry:
        raise HTTPException(status_code=404, detail="Image not found in database.")

    try:
        filename = os.path.basename(image_entry.image_url)
        images_base_dir = get_images_dir()
        target_path = os.path.join(images_base_dir, filename)
        if not os.path.exists(target_path):
            target_path = os.path.join(images_base_dir, "uploads", filename)
        
        if os.path.exists(target_path):
            os.remove(target_path)
            logger.info(f"Datei '{target_path}' erfolgreich gelöscht.")
        else:
            logger.warning(f"Physische Datei für Bild-ID {image_id} nicht gefunden, DB-Eintrag wird trotzdem gelöscht.")
    except Exception as e:
        logger.error(f"Fehler beim Löschen der Datei für Bild-ID {image_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not delete image file.")

    try:
        db.delete(image_entry)
        db.commit()
        logger.info(f"DB-Eintrag für Bild-ID {image_id} erfolgreich gelöscht.")
    except Exception as e:
        db.rollback()
        logger.error(f"Fehler beim Löschen des DB-Eintrags für Bild-ID {image_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not delete database entry.")

    return {"status": "success", "message": f"Image {image_id} deleted successfully."}
