import logging
import asyncio
from sqlalchemy.orm import Session
from . import llm_gateway, memory_manager, database, vector_service
from sentence_transformers import util # Added for util.cos_sim
import json # Added for json.loads
import numpy as np # Added for np.array
import keyring # Import keyring
import datetime # Import datetime

logger = logging.getLogger('janus_backend')

EXTRACTION_PROMPT = (
    "Du bist ein ultra-präziser Daten-Logger. Deine einzige Aufgabe ist es, Fakten aus der **letzten Äußerung des 'user'** in einem Dialog zu extrahieren. **IGNORIERE ALLES, WAS DER 'assistant' SAGT.**\n"
    "Formuliere die Fakten als knappe, neutrale Aussagen in der dritten Person (z.B. 'Der Benutzer heißt Klaus', 'Der Benutzer mag die Farbe Blau').\n"
    "Wenn der **'user'** in seiner letzten Nachricht keine neuen, konkreten Fakten nennt (z.B. nur eine Frage stellt oder Smalltalk macht), antworte NUR mit dem Wort 'Keine'.\n\n"
    "--- DIALOG ---\n"
    "{text_block}\n\n"
    "--- FAKTEN AUS DER LETZTEN USER-AUSSAGE ---"
)

async def resolve_fact_conflict(db: Session, old_fact: str, new_fact: str, main_api_key: str, provider: str, model: str):
    """Fragt eine LLM, ob ein neuer Fakt einen alten korrigiert."""
    prompt = (
        f"ALTER FAKT: '{old_fact}'\n"
        f"NEUER FAKT: '{new_fact}'\n\n"
        "Handelt es sich beim neuen Fakt um eine direkte Korrektur oder Aktualisierung des alten Fakts? "
        "Antworte nur mit 'JA' oder 'NEIN'."
    )
    history = [{"role": "user", "content": prompt}]
    response = await llm_gateway.call_llm(provider, model, prompt, main_api_key, chat_history=history)
    return "ja" in response.get("text", "").lower()

async def extract_and_save_fact(db: Session, chat_id: int, text_block: str, original_prompt: str, main_api_key: str, provider: str, model: str):
    """
    Extrahiert einen oder mehrere Fakten aus einem Textblock und speichert sie, wenn sie relevant sind.
    """
    logger.info(f"Attempting to extract and save facts for chat {chat_id} from text: '{text_block}'")
    try:
        # If text_block is empty but an image was generated, create a default fact
        if not text_block and original_prompt: # Assuming text_block is empty when image is generated
            extracted_text = f"Ein Bild von '{original_prompt}' wurde generiert."
            logger.info(f"Default fact created for image generation: '{extracted_text}'")
        else:
            extraction_history = [
                {"role": "system", "content": EXTRACTION_PROMPT.format(text_block='')}, # System prompt
                {"role": "user", "content": text_block} # User's text block
            ]

            gateway_response = await llm_gateway.call_llm(
                provider,
                model,
                text_block, # Pass the actual text block as the prompt
                main_api_key,
                chat_history=extraction_history
            )

            extracted_text = gateway_response.get("text", "").strip()
            logger.info(f"Extracted text: '{extracted_text}'")

        # Kosten für die Fakten-Extraktion speichern
        usage = gateway_response.get("usage")
        cost = gateway_response.get("cost", {})
        if usage and cost.get("total_cost", 0) > 0:
            database.save_cost_entry(
                date=datetime.datetime.now(), model=model,
                input_tokens=usage.get("input_tokens"), output_tokens=usage.get("output_tokens"),
                image_quality=usage.get("image_quality"), image_cost=cost.get("image_cost"),
                total_cost=cost.get("total_cost", 0)
            )

        if extracted_text and extracted_text.lower() != 'none':
            # Teile die Antwort in einzelne Fakten auf (eine pro Zeile)
            extracted_facts = [fact.strip() for fact in extracted_text.split('\n') if fact.strip()]
            
            for fact in extracted_facts:
                similar_fact_obj = memory_manager.find_similar_memory_snippet(db, text=fact)
                
                if similar_fact_obj:
                    # Wenn es sehr ähnlich ist, ist es ein Duplikat
                    # Need to import vector_service.model for this, or pass it around
                    # For now, assuming model is accessible (e.g., from vector_service)
                    # This part needs to be careful about the model import
                    # Assuming vector_service.model is the correct way to access it
                    if util.cos_sim(vector_service.model.encode(fact), np.array(json.loads(similar_fact_obj.embedding_json), dtype=np.float32))[0] > 0.95:
                         logger.info(f"Bekannter Fakt ignoriert (Duplikat): '{fact}'.")
                         continue
                    
                    # Wenn es nur mäßig ähnlich ist, könnte es eine Korrektur sein
                    is_correction = await resolve_fact_conflict(db, similar_fact_obj.snippet, fact, main_api_key, provider, model)
                    if is_correction:
                        logger.info(f"Fakt wird aktualisiert: '{similar_fact_obj.snippet}' -> '{fact}'.")
                        memory_manager.update_memory_snippet(db, memory_id=similar_fact_obj.id, new_snippet=fact)
                        continue # Gehe zum nächsten extrahierten Fakt

                # Wenn nichts Ähnliches gefunden wurde oder es keine Korrektur war
                logger.info(f"NEUER relevanter Fakt extrahiert: '{fact}'. Speichere in Memory.")
                memory_manager.save_memory_snippet(db, chat_id=chat_id, snippet_text=fact)
            
            return extracted_facts
        else:
            logger.info("Kein relevanter Fakt im Textblock gefunden.")
            return None

    except Exception as e:
        logger.error(f"Fehler bei der Fakten-Extraktion: {e}")
        return None
