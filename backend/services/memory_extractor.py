# backend/services/memory_extractor.py

import datetime
import logging
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.services import llm_gateway, memory_manager
from backend.llm_providers.base_provider import BaseLLMProvider

logger = logging.getLogger("janus_backend")

# Pydantic models for fact extraction
class ExtractedFact(BaseModel):
    fact: str
    category: str
    is_core: bool
    expires_in_hours: Optional[int] = None

class FactExtractionResponse(BaseModel):
    facts: List[ExtractedFact]

# Simple prompt since schema handles the structure
EXTRACTION_PROMPT = """
Extrahiere relevante persönliche Fakten aus dem folgenden Gespräch.
Achte darauf, nur Fakten zu extrahieren, die direkt den Benutzer betreffen.
Ignoriere allgemeines Wissen und Kontaktinformationen.
"""




# (Die Funktion `extract_and_save_fact` muss ebenfalls leicht angepasst werden, um `is_core` zu verarbeiten)


async def extract_and_save_fact(
    db: Session,
    chat_id: int,
    text_block: str,
    main_api_key: str,
    provider: str,
    model: str,
):
    """
    Extrahiert Fakten, klassifiziert sie, bewertet Zeitlichkeit & Wichtigkeit und speichert sie intelligent.
    """
    logger.info(
        f"[FACT EXTRACTION V5] Starte Extraktion, Klassifizierung, Zeitlichkeit & Wichtigkeit für Chat {chat_id}"
    )
    try:
        # Get the provider instance
        provider_instance = llm_gateway.get_provider(provider)
        
        from backend.services.cost_service import create_cost_entry

        # Call the structured response endpoint
        extracted_data, cost_data = await provider_instance.generate_structured_response(
            api_key=main_api_key,
            model=model,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": text_block}
            ],
            response_format=FactExtractionResponse
        )

        # Save the cost data if available
        if cost_data and "total_cost" in cost_data:
            try:
                # We use a generic string for the source, or the chat ID if available
                create_cost_entry(
                    db=db,
                    amount=cost_data["total_cost"],
                    model=model,
                    provider=provider,
                    source_type="fact_extraction", 
                    input_tokens=cost_data.get("input_tokens", 0),
                    output_tokens=cost_data.get("output_tokens", 0)
                )
                # db is closed by dependency injection, manual closure here if needed
            except Exception as e:
                logger.error(f"Failed to save costs for memory extraction: {e}")

        # Extract the facts from the response
        extracted_items = [fact.dict() for fact in extracted_data.facts]
        
        if not extracted_items:
            logger.info("Keine neuen Fakten im Textblock gefunden.")
            return None

        for item in extracted_items:
            fact = item.get("fact")
            category = item.get("category", "General Fact")
            expires_in_hours = item.get("expires_in_hours")
            is_core = item.get("is_core", False)  # NEU

            if not fact:
                continue

            # ... (Duplikatsprüfung bleibt gleich) ...
            similar_fact_obj = memory_manager.find_similar_memory_snippet(db, text=fact)
            if similar_fact_obj:
                logger.info(f"[DUPLICATE] Ignoriere bekannten Fakt: '{fact}'")
                continue

            expires_at = None
            if isinstance(expires_in_hours, (int, float)) and expires_in_hours > 0:
                expires_at = datetime.datetime.now() + datetime.timedelta(hours=expires_in_hours)
                log_prefix = "[NEW EPHEMERAL FACT]"
            else:
                log_prefix = "[NEW PERMANENT FACT]"

            logger.info(
                f"{log_prefix} (Core: {is_core}) Speichere: '{fact}' (Kategorie: {category})"
            )

            memory_manager.save_memory_snippet(
                db,
                chat_id=chat_id,
                snippet_text=fact,
                category=category,
                expires_at=expires_at,
                is_core=is_core,  # NEU
            )

        return extracted_items

    except Exception as e:
        logger.error(f"Fehler bei der V5 Fakten-Extraktion: {e}", exc_info=True)
        return None
