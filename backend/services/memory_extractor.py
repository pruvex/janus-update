# backend/services/memory_extractor.py

import logging
import asyncio
from sqlalchemy.orm import Session
from backend.data import database
from backend.services import llm_gateway, memory_manager, vector_service
from sentence_transformers import util
import json
import numpy as np
import datetime

logger = logging.getLogger("janus_backend")

# --- START: VERBESSERTER EXTRACTION_PROMPT ---
EXTRACTION_PROMPT = (
    "Du bist eine hochpräzise Extraktions-Engine. Deine einzige Aufgabe ist es, aus dem folgenden Dialog jeden einzelnen, neuen und konkreten Fakt zu extrahieren. Konzentriere dich auf Fakten, die der Assistant durch Werkzeuge (z.B. Websuche) gefunden hat.\n"
    "**REGELN:**\n"
    "1.  **LISTEN-REGEL:** WENN eine Liste von Dingen (z.B. Spiele, Personen, Orte) genannt wird, extrahiere JEDEN EINZELNEN Punkt der Liste als separaten Fakt.\n"
    "2.  Formuliere jeden Fakt als knappen, neutralen Satz.\n"
    "3.  Extrahiere persönliche Fakten über den Benutzer (z.B. 'Der Benutzer heißt Klaus') NUR, wenn der Benutzer dies explizit sagt.\n"
    "4.  IGNORIERE Meinungen, Smalltalk, Begrüßungen und Fragen.\n"
    "5.  Wenn keine neuen, konkreten Fakten genannt werden, antworte NUR mit dem Wort 'Keine'.\n\n"
    "--- BEISPIEL ---\n"
    "user: welche switch 2 spiele erscheinen im oktober?\n"
    "assistant: Im Oktober 2025 erscheinen:\n1. Super Mario Galaxy Remake\n2. Borderlands 4\n3. Little Nightmares 3\n"
    "--- EXTRAHIERTE FAKTEN ---\n"
    "Super Mario Galaxy Remake erscheint im Oktober 2025 für die Switch 2.\n"
    "Borderlands 4 erscheint im Oktober 2025 für die Switch 2.\n"
    "Little Nightmares 3 erscheint im Oktober 2025 für die Switch 2.\n\n"
    "--- DIALOG ---\n"
    "{text_block}\n\n"
    "--- EXTRAHIERTE FAKTEN ---"
)
# --- ENDE: VERBESSERTER EXTRACTION_PROMPT ---

IS_CORE_FACT_PROMPT = (
    "Du bist ein Klassifizierungs-Bot. Deine einzige Aufgabe ist es, den folgenden Fakt zu bewerten. "
    "Ein 'Core Fact' ist eine fundamentale, persönliche Information über den Benutzer, seine Familie, Freunde, Haustiere, seine wichtigsten Hobbys, Vorlieben, Abneigungen oder seinen Beruf. "
    "Fakten über einmalige Ereignisse, generierte Bilder oder triviale Details sind KEINE 'Core Facts'.\n\n"
    "FAKT: '{fact}'\n\n"
    "Handelt es sich hierbei um einen 'Core Fact'? Antworte NUR mit 'JA' oder 'NEIN'."
)

IS_TIME_SENSITIVE_PROMPT = (
    "Du bist ein Daten-Analyst. Deine Aufgabe ist es zu bewerten, ob eine Information zeitkritisch oder zeitlos ist.\n"
    "Zeitkritische Informationen sind Dinge wie aktuelle Preise, Nachrichten, Termine, Wetter oder temporäre Zustände, die wahrscheinlich in weniger als 48 Stunden ihre Relevanz verlieren.\n"
    "Zeitlose Informationen sind Anleitungen, Fakten, technische Daten, biografische Details oder historisches Wissen.\n\n"
    "FAKT: '{fact}'\n\n"
    "Ist dieser Fakt wahrscheinlich zeitkritisch? Antworte NUR mit 'JA' oder 'NEIN'."
)


async def extract_and_save_fact(
    db: Session,
    chat_id: int,
    text_block: str,
    main_api_key: str,
    provider: str,
    model: str,
):
    """
    Extrahiert Fakten aus einem Textblock, klassifiziert sie (Core vs. Non-Core, Zeitkritisch vs. Zeitlos) 
    und speichert sie intelligent in der Datenbank.
    """
    logger.info(f"[FACT EXTRACTION] Starte Extraktion für Chat {chat_id}")
    try:
        extraction_history = [
            {"role": "system", "content": EXTRACTION_PROMPT.format(text_block="")},
            {"role": "user", "content": text_block},
        ]
        gateway_response = await llm_gateway.call_llm(
            provider=provider,
            model_id=model,
            api_key=main_api_key,
            messages=extraction_history,
        )
        extracted_text = gateway_response.get("text", "").strip()
        logger.info(f"Extrahierter Text vom LLM: '{extracted_text}'")

        if not extracted_text or extracted_text.lower().strip().rstrip(".") in ["none", "keine"]:
            logger.info("Kein relevanter Fakt im Textblock gefunden.")
            return None

        lines = extracted_text.split("\n")
        extracted_facts = [line.strip() for line in lines if line.strip() and not line.strip().startswith("---")]

        for fact in extracted_facts:
            similar_fact_obj = memory_manager.find_similar_memory_snippet(db, text=fact)
            if similar_fact_obj:
                similarity_score = util.cos_sim(
                    vector_service.model.encode(fact),
                    np.array(json.loads(similar_fact_obj.embedding_json), dtype=np.float32),
                )[0]
                # --- KORREKTUR START ---
                # Konvertiere den Tensor in eine normale Python-Zahl
                score_float = similarity_score.item()
                # --- KORREKTUR ENDE ---
                if score_float > 0.98:
                    logger.info(f"[DUPLICATE] Ignoriere bekannten Fakt (Ähnlichkeit: {score_float:.2f}): '{fact}'")
                    continue

            is_core = False
            expires_at = None

            try:
                classification_history = [{"role": "user", "content": IS_CORE_FACT_PROMPT.format(fact=fact)}]
                classification_response = await llm_gateway.call_llm(
                    provider=provider, model_id=model, api_key=main_api_key, messages=classification_history
                )
                if "ja" in classification_response.get("text", "").lower():
                    is_core = True
            except Exception as e:
                logger.error(f"Konnte Fakt nicht als Core/Non-Core klassifizieren: {e}. Standard: Non-Core.")

            if not is_core:
                try:
                    time_history = [{"role": "user", "content": IS_TIME_SENSITIVE_PROMPT.format(fact=fact)}]
                    time_response = await llm_gateway.call_llm(
                        provider=provider, model_id=model, api_key=main_api_key, messages=time_history
                    )
                    if "ja" in time_response.get("text", "").lower():
                        expires_at = datetime.datetime.now() + datetime.timedelta(days=2)
                        logger.info(f"Fakt als ZEITKRITISCH klassifiziert. Läuft ab am: {expires_at}")
                except Exception as e:
                    logger.error(f"Konnte Fakt nicht als zeitkritisch klassifizieren: {e}. Standard: Zeitlos.")
            
            logger.info(f"[NEW FACT] Speichere neuen Fakt: '{fact}' (Core: {is_core}, Expires: {expires_at})")
            memory_manager.save_memory_snippet(
                db, chat_id=chat_id, snippet_text=fact, is_core=is_core, expires_at=expires_at
            )

        return extracted_facts

    except Exception as e:
        logger.error(f"Fehler bei der Fakten-Extraktion: {e}", exc_info=True)
        return None