import logging
import keyring
import os
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional, List
from backend.utils.paths import get_app_data_dir
from sqlalchemy.orm import Session
from backend.data import schemas, crud
from backend.data.database import get_db, save_cost_entry, GeneratedImage
from backend.services import cost_calculator
from backend.llm_providers.openai_service import OpenAIServiceProvider
from backend.llm_providers.gemini_service import GeminiServiceProvider
from datetime import datetime
from backend.services import image_manager
from dataclasses import asdict
from backend.data.presets import get_preset, PRESET_DATABASE
from backend.services.quality_gate import quality_gate_service

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
    db: Session = Depends(get_db)
):
    """
    Nimmt eine Anfrage zur Bilderstellung entgegen.
    Unterstützt Text-zu-Bild, Bild-zu-Bild und Quality Gates.
    """
    logger.info(f"Anfrage zur Bilderstellung erhalten für Provider {image_request.provider} und Modell {image_request.model}")
    
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
                    
                    # Wir aktivieren den aggressiven Stil-Modus, sobald wir ein Referenzbild haben 
                    # UND ein Preset gewählt wurde. Egal ob Upload oder KI-Bild.
                    # Denn auch bei Uploads willst du ja, dass der Stil sich ändert!
                    is_style_transfer = (image_request.previous_response_id is not None or image_request.reference_image_url is not None) and image_request.style_preset is not None
                    
                    if is_style_transfer:
                        # FALL 1: Refinement mit Preset -> "Time Travel" Modus
                        logger.info(f"🎨 Applying TIME TRAVEL / STYLE ADAPTATION: {image_request.variation_preset}")
                        
                        task_instruction = (
                            "⚡ TASK: ERA ADAPTATION & STYLE TRANSFER ⚡\n"
                            "1. ANALYZE the subject (face/pose) from the reference image.\n"
                            "2. KEEP the person's identity and facial features strictly consistent.\n"
                            "3. CHANGE the clothing, hairstyle, and background to match the target ERA defined below.\n"
                            "   (e.g., If preset is 1890s, replace modern clothes with victorian attire).\n"
                            "4. APPLY the visual aesthetic (film stock, lighting) of the preset."
                        )
                        
                        image_request.prompt = (
                            f"{task_instruction}\n\n"
                            f"▼▼▼ TARGET PRESET / ERA ▼▼▼\n"
                            f"{system_prompt_add}\n\n"
                            f"▼▼▼ USER MODIFICATION ▼▼▼\n"
                            f"{user_input}"
                        )
                        
                    else:
                        # FALL 2: Neues Bild ohne Referenz (kein Stil-Transfer)
                        logger.info(f"🎨 Standard mode: No style transfer - {image_request.variation_preset}")
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
    
    if image_request.reference_image_urls and len(image_request.reference_image_urls) > 0:
        target_urls = image_request.reference_image_urls
        logger.info(f"Kombinieren-Modus aktiv: {len(target_urls)} Bilder angefordert.")
    elif image_request.reference_image_url:
        target_urls = [image_request.reference_image_url]
        logger.info("Single-Image Modus aktiv.")

    if target_urls:
        for url in target_urls:
            try:
                # URL parsen, um den Pfad zu bekommen
                from urllib.parse import urlparse
                parsed_url = urlparse(url)
                url_path = parsed_url.path  # z.B. "/user_images/uploads/meinbild.jpg"
                
                filename = os.path.basename(url_path)
                app_data = get_app_data_dir()
                
                # LOGIK-FIX: Prüfen, ob das Bild im Uploads-Ordner liegt
                if "/uploads/" in url_path or "uploads" in url_path.split("/"):
                    # Es ist ein Upload -> Pfad: AppData/images/uploads/filename
                    file_path = os.path.join(app_data, "images", "uploads", filename)
                    logger.info(f"Using uploaded reference image from: {file_path}")
                else:
                    # Es ist ein generiertes Bild -> Pfad: AppData/images/filename
                    file_path = os.path.join(app_data, "images", filename)
                    logger.info(f"Using generated reference image from: {file_path}")
                
                # Sicherheitscheck
                if not os.path.exists(file_path):
                    logger.error(f"Reference image not found at: {file_path}")
                    # Versuche Fallback (vielleicht liegt es doch im anderen Ordner?)
                    fallback_path = os.path.join(app_data, "images", "generated" if "/uploads/" in url_path else "uploads", filename)
                    if os.path.exists(fallback_path):
                        file_path = fallback_path
                        logger.info(f"Found image at fallback path: {file_path}")
                    else:
                        raise HTTPException(status_code=404, detail=f"Bild '{filename}' nicht gefunden.")
                
                if file_path:
                    with open(file_path, "rb") as f:
                        image_bytes_list.append(f.read())
                    logger.info(f"Bild geladen: {file_path} ({os.path.getsize(file_path)} Bytes)")
                else:
                    logger.error(f"Bild nicht gefunden: {filename}")
                    raise HTTPException(status_code=404, detail=f"Bild '{filename}' nicht gefunden.")
                    
            except HTTPException as he:
                raise he
            except Exception as e:
                logger.error(f"Fehler beim Laden von {url}: {e}")
                raise HTTPException(status_code=500, detail=f"Ladefehler: {str(e)}")

    try:
        # Parameter als Dictionary extrahieren
        params_dict = {}
        if image_request.parameters:
            if hasattr(image_request.parameters, "model_dump"):
                params_dict = image_request.parameters.model_dump()
            elif isinstance(image_request.parameters, dict):
                params_dict = image_request.parameters
        
        full_model_id = image_request.model

        # --- PRESET LOGIK (Version 3.0 - mit Edit-Mode-Integration) ---
        preset_config = None
        user_prompt_for_preset = image_request.prompt or ""

        # --- PRESET EDIT LOGIK (Version 4.0 - True Time Travel) ---
        
        # Spezial-Logik für "Preset auf eigenes Bild anwenden"
        if getattr(image_request, 'apply_preset_to_edit', False):
            # Basis-Prompt setzen, falls leer
            if not user_prompt_for_preset.strip():
                user_prompt_for_preset = "Ein Porträt der Person aus dem Referenzbild."

            # --- DIE NEUE DIAMOND-STANDARD INSTRUKTION ---
            # Wir nutzen eine hierarchische Struktur, um Identität und Zeit zu trennen.
            identity_locked_protocol = (
                "\n\n--- EDITING MODE: IDENTITY-LOCKED TEMPORAL RECOMPOSITION ---\n\n"
                "1. IDENTITY (LOCKED – MUST NOT CHANGE):\n"
                "- Preserve the exact facial structure, proportions, and identity of the person from the reference image.\n"
                "- Do not beautify, stylize, or idealize the face beyond the limits of the film stock.\n"
                "- The person must remain clearly recognizable as the specific individual from the source.\n\n"
                
                "2. TEMPORAL OVERRIDE (MANDATORY):\n"
                "- COMPLETELY REPLACE clothing, hairstyle, background, objects, and environment.\n"
                "- IGNORE the modern context of the reference image (e.g., modern streets, t-shirts, cars).\n"
                "- All replaced elements must strictly conform to the selected PRESET ERA.\n"
                "- Example: Replace a hoodie with a period-correct coat/suit; replace neon lights with gas lamps.\n\n"
                
                "3. PHYSICAL RE-SIMULATION (MANDATORY):\n"
                "- Re-render the entire image as if it were originally captured using the camera, lens, film stock, and lighting defined in the preset.\n"
                "- The result must look like a GENUINE photograph from that era, not a modern photo with a vintage filter.\n\n"
                
                "FAILURE CONDITION:\n"
                "- If the image shows modern clothing or objects with a vintage filter, the result is invalid.\n"
            )
            
            user_prompt_for_preset += identity_locked_protocol
            logger.info("Edit-Mode: 'Identity-Locked' Protokoll aktiviert.")

        # --- DEBUG: PRESET-ANWENDUNG PRÜFEN ---
        logger.info("--- DEBUG: PRESET-ANWENDUNG PRÜFEN ---")
        logger.info(f"Style Preset vom Frontend: {image_request.style_preset}")
        logger.info(f"Variation Preset vom Frontend: {image_request.variation_preset}")
        logger.info(f"Reference Image URL vorhanden: {bool(image_request.reference_image_url)}")
        logger.info(f"Apply Preset to Edit-Checkbox: {getattr(image_request, 'apply_preset_to_edit', False)}")
        
        # Bedingung, um Presets anzuwenden:
        # 1. Preset wurde explizit im UI ausgewählt.
        # UND (
        # 2. Es ist KEIN Edit-Mode ODER es ist Edit-Mode UND die "Preset anwenden"-Box ist gecheckt.
        # )
        should_apply_preset = (
            image_request.style_preset and 
            image_request.variation_preset and
            (not image_request.reference_image_url or getattr(image_request, 'apply_preset_to_edit', False))
        )
        
        logger.info(f"Ergebnis der Prüfung 'should_apply_preset': {should_apply_preset}")

        if should_apply_preset:
            # Presets sind aktiv
            logger.info(f"Stil-Preset '{image_request.style_preset} / {image_request.variation_preset}' wird angewendet.")
            config, prompt = get_preset(
                provider=image_request.provider,
                style=image_request.style_preset,
                variation=image_request.variation_preset,
                user_prompt=user_prompt_for_preset
            )
            preset_config = config
            final_prompt = prompt
        else:
            # Presets sind NICHT aktiv -> Nutze Default-Verhalten
            logger.info("Kein Preset angewendet. Standard-Generierung wird verwendet.")
            config, prompt = get_preset(
                provider=image_request.provider,
                style="", # Leere Werte, damit Fallback greift
                variation="",
                user_prompt=user_prompt_for_preset
            )
            preset_config = config 
            final_prompt = prompt

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
        while attempt <= max_retries:
            qg_stats["attempts"] = attempt + 1
            logger.info(f"--- Generierungs-Versuch {qg_stats['attempts']} von {max_retries + 1} ---")
            
            result = await provider_service.generate_image(
                api_key=api_key,
                model=image_request.model,
                prompt=current_prompt,
                image_bytes_list=image_bytes_list,
                previous_response_id=image_request.previous_response_id,
                previous_image_id=image_request.previous_image_id,
                mask_image_data=image_request.mask_image_data,
                **params_dict  # Alle Parameter aus dem Frontend durchreichen
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

            # --- FIX: Variablen für Kostenspeicherung definieren ---
            selected_quality = image_request.params.get('quality', 'standard') if hasattr(image_request, 'params') else 'standard'
            selected_size = image_request.params.get('size', '1024x1024') if hasattr(image_request, 'params') else '1024x1024'

            save_cost_entry(
                date=datetime.now(),
                model=full_model_id,
                provider=image_request.provider,
                source_type="image_generation",
                input_tokens=result.get("usage", {}).get("input_tokens"),
                output_tokens=result.get("usage", {}).get("output_tokens"),
                image_quality=result.get("usage", {}).get("image_quality") or selected_quality,
                image_size=result.get("usage", {}).get("image_size") or selected_size,
                image_cost=image_cost_details.get("image_cost"),
                total_cost=image_cost_details.get("total_cost"),
            )

            if gate_level == "none" or not image_url:
                break

            # Quality Gate Check
            try:
                # Bildpfad ermitteln
                filename = image_url.split("/")[-1]
                app_data_dir = get_app_data_dir()
                final_path = os.path.join(app_data_dir, "images", filename)
                
                if os.path.exists(final_path):
                    with open(final_path, "rb") as img_file:
                        img_bytes = img_file.read()
                    
                    check_api_key = get_api_key(image_request.provider)
                    
                    evaluation = await quality_gate_service.evaluate_image(
                        provider=image_request.provider,
                        api_key=check_api_key,
                        image_bytes=img_bytes,
                        prompt=current_prompt,
                        criteria=vision_criteria
                    )
                    
                    score = evaluation.get("score", 0)
                    qg_stats["final_score"] = score
                    
                    if score >= min_score:
                        logger.info(f"Quality Gate BESTANDEN mit Score {score}/{min_score}.")
                        break
                    
                    if attempt < max_retries:
                        suggestion = evaluation.get("suggestion", "make it look more realistic")
                        logger.warning(f"Quality Gate NICHT bestanden. Optimiere Prompt... Suggestion: {suggestion}")
                        current_prompt = f"{current_prompt} - {suggestion}"
                        image_request.previous_response_id = None
                        image_request.previous_image_id = None
                else:
                    logger.error(f"Konnte Bild für Quality Check nicht finden: {final_path}")
                    break
            except Exception as e:
                logger.error(f"Fehler im Quality Gate Loop: {e}", exc_info=True)
                break
            
            attempt += 1
        # --- ENDE LOOP ---

        if not final_result or not final_result.get("image_url"):
             raise HTTPException(status_code=500, detail="Generierung fehlgeschlagen nach allen Versuchen.")

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
        db.add(new_image_entry) # Wichtig: Als "modified" markieren
        db.commit()
        db.refresh(new_image_entry)
        
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
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File is not an image.")

        new_image_entry = await image_manager.save_uploaded_file(db=db, file=file)
        return new_image_entry

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

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
    # Suche auch nach Dateien, die evtl. Suffixe haben, indem wir matchen
    img_entry = db.query(GeneratedImage).filter(GeneratedImage.image_url.contains(filename)).first()
    
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
    img_entry = db.query(GeneratedImage).filter(GeneratedImage.id == image_id).first()
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

    return {
        "response_id": img_entry.provider_response_id, 
        "image_id": img_entry.previous_image_id,  # Für Gemini History
        "style_preset": style,
        "variation_preset": variation
    }

@router.post("/images/rename", response_model=schemas.GeneratedImage)
async def rename_image(rename_request: schemas.ImageRenameRequest, db: Session = Depends(get_db)):
    """Benennt eine Bilddatei um."""
    try:
        image_manager.rename_image_file(rename_request.old_path, rename_request.new_filename)

        old_image_url = f"/user_images/{rename_request.old_path}"
        image_entry = db.query(GeneratedImage).filter(GeneratedImage.image_url == old_image_url).first()

        if not image_entry:
            raise LookupError(f"DB-Eintrag für {old_image_url} nicht gefunden.")

        image_directory = os.path.dirname(rename_request.old_path)
        new_image_url = f"/user_images/{os.path.join(image_directory, rename_request.new_filename)}".replace('\\', '/')
        image_entry.image_url = new_image_url
        
        db.commit()
        db.refresh(image_entry)
        
        logger.info(f"Datenbankeintrag für Bild ID {image_entry.id} auf '{new_image_url}' aktualisiert.")
        return image_entry

    except (FileNotFoundError, FileExistsError, LookupError) as e:
        logger.warning(f"Fehler beim Umbenennen des Bildes: {e}")
        if isinstance(e, FileNotFoundError) or isinstance(e, LookupError):
             raise HTTPException(status_code=404, detail=str(e))
        else:
             raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Umbenennen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")

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