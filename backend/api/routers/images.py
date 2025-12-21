import logging
import keyring
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.data import schemas, crud
from backend.data.database import get_db
from backend.services import cost_calculator
from backend.llm_providers.openai_service import OpenAIServiceProvider
from backend.llm_providers.gemini_service import GeminiServiceProvider
from backend.data.database import save_cost_entry # NEU: Direkter Import
from datetime import datetime # NEU: Für den Zeitstempel der Kosten

logger = logging.getLogger("janus_backend")
router = APIRouter()

# Instanzen der Provider erstellen
openai_provider = OpenAIServiceProvider()
gemini_provider = GeminiServiceProvider()

PROVIDER_MAP = {
    "openai": openai_provider,
    "google": gemini_provider,
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
    Nimmt eine Anfrage zur Bilderstellung entgegen, ruft den entsprechenden Dienst auf,
    speichert das Ergebnis und gibt die Bild-URL zurück.
    """
    logger.info(f"Anfrage zur Bilderstellung erhalten für Provider {image_request.provider} und Modell {image_request.model}")
    
    provider_service = PROVIDER_MAP.get(image_request.provider)
    if not provider_service:
        raise HTTPException(status_code=400, detail=f"Provider '{image_request.provider}' wird nicht unterstützt.")
        
    api_key = get_api_key(image_request.provider)

    try:
        # Parameter extrahieren
        # Der model_id, der an den Provider übergeben wird, muss dem Eintrag in model_catalog.json entsprechen.
        # Da der Katalog jetzt mit spezifischen IDs wie 'dall-e-3-hd-1024x1024' arbeitet,
        # müssen wir den richtigen 'model' aus den 'image_request.model', 'quality' und 'size' zusammenbauen.
        
        # Annahme: image_request.model ist der Basisname (z.B. "dall-e-3")
        # und quality/size kommen aus image_request.parameters
        
        selected_quality = image_request.parameters.model_dump().get("quality", "medium") # Default to 'medium' for GPT Image
        selected_size = image_request.parameters.model_dump().get("resolution", "1024x1024")
        
        # full_model_id is simply the requested model for GPT Image models
        full_model_id = image_request.model


        result = await provider_service.generate_image(
            api_key=api_key,
            model=image_request.model, 
            prompt=image_request.prompt,
            size=selected_size,
            quality=selected_quality
        )

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
            image_cost=image_cost_details.get("image_cost"),
            total_cost=image_cost_details.get("total_cost"),
        )


        # Datenbankeintrag für das generierte Bild erstellen
        new_image_entry = crud.create_generated_image(
            db=db, 
            image_data=image_request, 
            image_url=image_url
        )
        
        return new_image_entry

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Fehler bei der Bilderstellung: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Interne Server-Fehler bei der Bilderstellung: {str(e)}")


@router.post("/images/upload")
async def upload_image():
    """Nimmt ein vom Benutzer hochgeladenes Bild entgegen und speichert es."""
    raise HTTPException(status_code=501, detail="Endpunkt noch nicht implementiert.")


@router.get("/images/pricing")
async def get_pricing_info():
    """Gibt die Preisstruktur für die Bilderstellung zurück."""
    try:
        pricing_data = cost_calculator.get_image_pricing_structure()
        return pricing_data
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Preisinformationen: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Preisinformationen konnten nicht geladen werden.")

