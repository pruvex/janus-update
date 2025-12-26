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
        base_dir = os.getcwd()
        for url in target_urls:
            try:
                filename = url.split("/")[-1]
                possible_paths = [
                    os.path.join(base_dir, "images", "uploads", filename),
                    os.path.join(base_dir, "backend", "user_images", "uploads", filename),
                    os.path.join(base_dir, "images", "generated", filename),
                    os.path.join(os.getenv('LOCALAPPDATA', ''), "JanusDev", "Janus Projekt", "images", "uploads", filename),
                    os.path.join(os.getenv('LOCALAPPDATA', ''), "JanusDev", "Janus Projekt", "images", filename),
                    os.path.join(os.getenv('APPDATA', ''), "JanusDev", "Janus Projekt", "images", "uploads", filename),
                    os.path.join(os.getenv('APPDATA', ''), "JanusDev", "Janus Projekt", "images", filename)
                ]

                file_path = None
                for p in possible_paths:
                    if os.path.exists(p):
                        file_path = p
                        break
                
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
        # Parameter extrahieren
        selected_quality = "medium"
        selected_size = "1024x1024"
        
        if image_request.parameters:
            params_dict = image_request.parameters if isinstance(image_request.parameters, dict) else image_request.parameters.model_dump()
            selected_quality = params_dict.get("quality", "medium")
            selected_size = params_dict.get("resolution", "1024x1024")
        
        full_model_id = image_request.model

        # --- PRESET LOGIK (ROBUSTER) ---
        preset_config = None # Initialisiere als None
        
        if image_request.style_preset and image_request.variation_preset:
            # Holen Sie sich den formatierten Prompt
            formatted_prompt = get_preset(
                provider=image_request.provider,
                style=image_request.style_preset.get('style'), # Jetzt ein Diktat
                variation=image_request.style_preset.get('variation'), # Jetzt ein Diktat
                prompt=image_request.prompt # Hier sollte der User-Prompt übergeben werden
            )
            final_prompt = formatted_prompt if formatted_prompt else image_request.prompt

            # Holen Sie sich die volle Konfiguration des Presets
            # image_request.style_preset ist jetzt ein Diktat, muss entsprechend zugegriffen werden
            preset_conf_data = PRESET_DATABASE.get(image_request.style_preset.get('style'), {}).get(image_request.style_preset.get('variation'))
            if preset_conf_data:
                # Konvertiere das Diktat in ein Objekt, um 'hasattr' zu ermöglichen
                preset_config = type('PresetConfig', (object,), preset_conf_data)()
            
            logger.info(f"Stil-Preset '{image_request.style_preset.get('style')} / {image_request.style_preset.get('variation')}' wird angewendet.")
        else:
            # Wenn keine Presets, nutze den Original-Prompt
            final_prompt = image_request.prompt

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
                size=selected_size,
                quality=selected_quality,
                previous_response_id=image_request.previous_response_id,
                previous_image_id=image_request.previous_image_id,
                mask_image_data=image_request.mask_image_data,
            )
            
            final_result = result
            image_url = result.get("image_url")
            
            # Kosten für diesen Versuch addieren
            image_cost_details = result.get("cost", {})
            qg_stats["total_cost"] += image_cost_details.get("total_cost", 0.0)

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

        # DB Eintrag erstellen
        if isinstance(image_request.style_preset, dict):
             image_request.style_preset = json.dumps(image_request.style_preset)
             
        new_image_entry = crud.create_generated_image(
            db=db, 
            image_data=image_request, 
            image_url=final_result.get("image_url")
        )
        
        response_data = {
            "id": new_image_entry.id,
            "image_url": new_image_entry.image_url,
            "previous_response_id": final_result.get('previous_response_id'),
            "previous_image_id": final_result.get('previous_image_id'),
            "created_at": new_image_entry.created_at,
            "quality_gate_stats": qg_stats # Stats an das Frontend senden
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
    """Gibt den Kontext für ein Bild zurück."""
    filename = url.split("/")[-1]
    img_entry = db.query(GeneratedImage).filter(GeneratedImage.image_url.contains(filename)).first()
    
    if not img_entry:
        return {"response_id": None, "image_id": None}
        
    return {
        "response_id": img_entry.previous_response_id,
        "image_id": img_entry.previous_image_id
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