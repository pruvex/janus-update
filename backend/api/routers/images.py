import logging
import keyring
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional
from backend.utils.paths import get_app_data_dir
from sqlalchemy.orm import Session
from backend.data import schemas, crud
from backend.data.database import get_db
from backend.services import cost_calculator
from backend.llm_providers.openai_service import OpenAIServiceProvider
from backend.llm_providers.gemini_service import GeminiServiceProvider
from backend.data.database import save_cost_entry, get_db # NEU: Direkter Import
from datetime import datetime # NEU: Für den Zeitstempel der Kosten
from backend.services import image_manager # NEU: Für Bildmanagement
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from backend.data.database import GeneratedImage
from backend.data.presets import get_preset

logger = logging.getLogger("janus_backend")
router = APIRouter()

# Instanzen der Provider erstellen
openai_provider = OpenAIServiceProvider()
gemini_provider = GeminiServiceProvider()

PROVIDER_MAP = {
    "openai": openai_provider,
    "gemini": gemini_provider,
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
    Unterstützt Text-zu-Bild und Bild-zu-Bild (Editierung) via 'reference_image_url'.
    """
    logger.info(f"Anfrage zur Bilderstellung erhalten für Provider {image_request.provider} und Modell {image_request.model}")
    
    provider_service = PROVIDER_MAP.get(image_request.provider)
    if not provider_service:
        raise HTTPException(status_code=400, detail=f"Provider '{image_request.provider}' wird nicht unterstützt.")
        
    api_key = get_api_key(image_request.provider)
    
    # --- BILDER LADEN (Universal-Loader) ---
    image_bytes_list = []
    
    # 1. Wir bestimmen, welche Bilder geladen werden sollen
    target_urls = []
    
    # Hat der User die "Kombinieren"-Liste geschickt?
    if image_request.reference_image_urls and len(image_request.reference_image_urls) > 0:
        target_urls = image_request.reference_image_urls
        logger.info(f"Kombinieren-Modus aktiv: {len(target_urls)} Bilder angefordert.")
        
    # Oder ist es ein Einzelbild (Refinement/Edit)?
    elif image_request.reference_image_url:
        target_urls = [image_request.reference_image_url]
        logger.info("Single-Image Modus aktiv.")

    # 2. Lade-Schleife
    if target_urls:
        base_dir = os.getcwd()
        for url in target_urls:
            try:
                filename = url.split("/")[-1]
                
                # Pfad-Such-Strategie (für Uploads UND Generierte)
                possible_paths = [
                    os.path.join(base_dir, "images", "uploads", filename),
                    os.path.join(base_dir, "backend", "user_images", "uploads", filename),
                    os.path.join(base_dir, "images", "generated", filename),
                    # LOCALAPPDATA (Server-Speicherort)
                    os.path.join(os.getenv('LOCALAPPDATA', ''), "JanusDev", "Janus Projekt", "images", "uploads", filename),
                    os.path.join(os.getenv('LOCALAPPDATA', ''), "JanusDev", "Janus Projekt", "images", filename),
                    # APPDATA Fallback
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
    # ---------------------------------------

    # --- STIL-PRESETS ANWENDEN (NEUE LOGIK) ---
    if isinstance(image_request.style_preset, dict) and 'style' in image_request.style_preset and 'variation' in image_request.style_preset:
        style = image_request.style_preset['style']
        variation = image_request.style_preset['variation']
        logger.info(f"Stil-Preset '{style} / {variation}' wird angewendet.")
        
        preset_prompt = get_preset(
            provider=image_request.provider,
            style=style,
            variation=variation,
            prompt=image_request.prompt
        )
        
        if preset_prompt:
            # Der Preset-Prompt ersetzt den User-Prompt, da er ihn bereits enthält
            image_request.prompt = preset_prompt
        else:
            logger.warning(f"Stil-Preset '{style} / {variation}' für Provider '{image_request.provider}' nicht gefunden.")

    try:
        # Parameter extrahieren
        selected_quality = image_request.parameters.model_dump().get("quality", "medium") # Default to 'medium' for GPT Image
        selected_size = image_request.parameters.model_dump().get("resolution", "1024x1024")
        
        # full_model_id is simply the requested model for GPT Image models
        full_model_id = image_request.model

        # WICHTIG: Wir übergeben jetzt IMMER eine Liste (image_bytes_list)
        # und entfernen das alte "image_bytes" Argument
        result = await provider_service.generate_image(
            api_key=api_key,
            model=image_request.model,
            prompt=image_request.prompt,
            image_bytes_list=image_bytes_list,
            size=selected_size,
            quality=selected_quality,
            previous_response_id=image_request.previous_response_id,
            previous_image_id=image_request.previous_image_id,
            mask_image_data=image_request.mask_image_data,
        )
        
        # Update the request with the new IDs for database storage
        if result.get('previous_response_id') is not None:
            image_request.previous_response_id = result.get('previous_response_id')
        if result.get('previous_image_id') is not None:
            image_request.previous_image_id = result.get('previous_image_id')

        image_url = result.get("image_url")
        if not image_url:
            raise HTTPException(status_code=500, detail="Bildgenerierung fehlgeschlagen, keine URL erhalten.")

        # Kosteninformationen extrahieren
        image_usage = result.get("usage", {})
        image_cost_details = result.get("cost", {})
        
        # Kosten in der Datenbank speichern
        save_cost_entry(
            date=datetime.now(),
            model=full_model_id, # Speichere die vollständige Model-ID
            provider=image_request.provider,
            source_type="image_generation",
            input_tokens=image_usage.get("input_tokens"), # Falls relevant für Multimodal
            output_tokens=image_usage.get("output_tokens"), # Falls relevant für Multimodal
            image_quality=image_usage.get("image_quality") or selected_quality,
            image_size=image_usage.get("image_size") or selected_size, # NEU: image_size hinzufügen
            image_cost=image_cost_details.get("image_cost"),
            total_cost=image_cost_details.get("total_cost"),
        )


        # Create database entry for the generated image
        new_image_entry = crud.create_generated_image(
            db=db, 
            image_data=image_request, 
            image_url=image_url
        )
        
        # Return all required fields in the response
        response_data = {
            "id": new_image_entry.id,
            "image_url": new_image_entry.image_url,
            "previous_response_id": result.get('previous_response_id'),
            "previous_image_id": result.get('previous_image_id'),
            "created_at": new_image_entry.created_at  # Required by the response model
        }
        
        return response_data

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Fehler bei der Bilderstellung: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Interne Server-Fehler bei der Bilderstellung: {str(e)}")


@router.post("/images/upload", response_model=schemas.GeneratedImage)
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Handles user-uploaded images.
    Saves the image locally, creates a database entry, and returns the image object.
    """
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File is not an image.")

        # Use the new generic function in image_manager
        new_image_entry = await image_manager.save_uploaded_file(db=db, file=file)
        
        return new_image_entry

    except HTTPException as e:
        # Re-raise HTTPException to let FastAPI handle it
        raise e
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")


@router.get("/images/pricing")
async def get_pricing_info():
    """Gibt die Preisstruktur für die Bilderstellung zurück."""
    try:
        pricing_data = cost_calculator.get_image_pricing_structure()
        return pricing_data
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Preisinformationen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Preisinformationen konnten nicht geladen werden.")


@router.get("/images/context")
async def get_image_context(url: str, db: Session = Depends(get_db)):
    """
    Gibt den Kontext (previous_response_id und previous_image_id) für ein bestimmtes Bild zurück.
    """
    # Extrahiere den Dateinamen aus der URL
    filename = url.split("/")[-1]
    # Suche in der Datenbank nach dem Eintrag für dieses Bild
    img_entry = db.query(GeneratedImage).filter(GeneratedImage.image_url.contains(filename)).first()
    
    if not img_entry:
        return {"response_id": None, "image_id": None}
        
    return {
        "response_id": img_entry.previous_response_id,
        "image_id": img_entry.previous_image_id
    }

@router.post("/images/rename", response_model=schemas.GeneratedImage)
async def rename_image(rename_request: schemas.ImageRenameRequest, db: Session = Depends(get_db)):
    """
    Benennt eine generierte Bilddatei auf der Festplatte und in der Datenbank um.
    """
    try:
        # 1. Datei im Dateisystem umbenennen (ruft die korrigierte Funktion auf)
        image_manager.rename_image_file(rename_request.old_path, rename_request.new_filename)

        # 2. Datenbankeintrag aktualisieren (Logik hier, um circular import zu vermeiden)
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
        # Für den Client ist es oft hilfreicher, einen spezifischen Fehlercode zu erhalten
        if isinstance(e, FileNotFoundError) or isinstance(e, LookupError):
             raise HTTPException(status_code=404, detail=str(e))
        else: # FileExistsError
             raise HTTPException(status_code=409, detail=str(e)) # 409 Conflict
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Umbenennen des Bildes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ein interner Fehler ist aufgetreten: {str(e)}")
