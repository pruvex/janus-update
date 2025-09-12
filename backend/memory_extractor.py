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
    "**REGELN:**\n"
    "1.  Extrahiere jeden einzelnen Fakt auf einer **NEUEN ZEILE**. \n"
    "2.  Formuliere die Fakten als knappe, neutrale Aussagen. Wenn der Name des Benutzers bereits bekannt ist (z.B. Klaus), beziehe die Fakten direkt auf diese Person (z.B. 'Klaus' Eltern sind...', 'Klaus' Tante mag...'). Ansonsten verwende 'Der Benutzer...'.\n"
    "2.1. **STRIKTE IDENTITÄTSREGEL:** Extrahiere den Namen des Benutzers (z.B. 'Der Benutzer heißt Klaus') NUR, wenn der Benutzer dies explizit sagt (z.B. 'Ich heiße Klaus', 'Mein Name ist Klaus'). Wenn eine andere Person erwähnt wird (z.B. 'Kalle wohnt in Köln'), extrahiere NUR diesen Fakt ('Kalle wohnt in Köln') und **NIEMALS** 'Der Benutzer heißt Kalle'.\n"
    "3.  **WICHTIG: Leite KEINERLEI neue Beziehungen ab.** Wenn der User sagt 'Gudrun ist die Schwester meiner Mutter Susi', extrahiere NUR 'Gudrun ist die Schwester von Susi' und/oder 'Susi ist die Mutter des Benutzers'. Extrahiere NICHT 'Gudrun ist die Tante des Benutzers'. Das ist die Aufgabe des Assistenten, nicht deine.\n"
    "4.  Wenn der **'user'** in seiner letzten Nachricht keine neuen, konkreten Fakten nennt, antworte NUR mit dem Wort 'Keine'.\n\n"
    "--- BEISPIEL ---\n"
    "user: Ich heiße Anna, mein Hund Bello mag Knochen und meine Katze Minka ist schwarz.\n"
    "--- EXTRAHIERTE FAKTEN ---\n"
    "Der Benutzer heißt Anna.\n"
    "Annas Hund heißt Bello.\n"
    "Bello mag Knochen.\n"
    "Annas Katze heißt Minka.\n"
    "Minka ist schwarz.\n\n"
    "--- DIALOG ---\n"
    "{text_block}\n\n"
    "--- EXTRAHIERTE FAKTEN ---"
)

IS_CORE_FACT_PROMPT = (
    "Du bist ein Klassifizierungs-Bot. Deine einzige Aufgabe ist es, den folgenden Fakt zu bewerten. "
    "Ein 'Core Fact' ist eine fundamentale, persönliche Information über den Benutzer, seine Familie, Freunde, Haustiere, seine wichtigsten Hobbys, Vorlieben, Abneigungen oder seinen Beruf. "
    "Fakten über einmalige Ereignisse, generierte Bilder oder triviale Details sind KEINE 'Core Facts'.\n\n"
    "FAKT: '{fact}'\n\n"
    "Handelt es sich hierbei um einen 'Core Fact'? Antworte NUR mit 'JA' oder 'NEIN'."
)

async def consolidate_state_with_new_fact(db: Session, old_fact: str, new_info: str, main_api_key: str, provider: str, model: str) -> str:
    """
    Nimmt einen alten Fakt (den aktuellen Zustand) und eine neue Information.
    Gibt den neuen, konsolidierten Fakt zurck. Wenn keine Konsolidierung mglich ist, gibt es 'None' zurck.
    """
    prompt = (
        f"Du bist eine ultra-przise Engine zur Zustands-Aktualisierung einer Wissensdatenbank. Deine Aufgabe ist es, einen neuen Fakt zu generieren, der den aktuellen Zustand widerspiegelt.\n\n"
        f"**AKTUELLER ZUSTAND (ALTER FAKT):** '{old_fact}'\n"
        f"**NEUE INFORMATION:** '{new_info}'\n\n"
        f"**AUFGABE:** Analysiere die 'NEUE INFORMATION' im Kontext des 'AKTUELLEN ZUSTANDS'.\n"
        f"- Wenn die neue Information den alten Zustand aktualisiert (z.B. eine Mengennderung, eine Statusnderung), formuliere den **neuen, finalen Zustand** als einen einzigen, przisen Fakt in der **Gegenwart** (z.B. 'Klaus hat 8 pfel.').\n"
        f"- Wenn die neue Information eine vage Aussage durch eine spezifischere ersetzt (z.B. 'Der Benutzer' -> 'Klaus'), gib den neuen, spezifischeren Fakt zurck.\n"
        f"- **WICHTIG:** Wenn die beiden Fakten unterschiedliche Themen behandeln (z.B. pfel und Verwandte), auch wenn sie sich auf dieselbe Person beziehen, haben sie nichts miteinander zu tun. Antworte in diesem Fall NUR mit dem Wort 'Keine'.\n\n"
        f"**BEISPIEL 1 (Menge):**\n"
        f"- ALTER FAKT: 'Klaus hat 10 pfel.'\n"
        f"- NEUE INFORMATION: 'Klaus hat 2 pfel gegessen.'\n"
        f"- ANTWORT: 'Klaus hat 8 pfel.'\n\n"
        f"**BEISPIEL 2 (Spezifitt):**\n"
        f"- ALTER FAKT: 'Der Benutzer hat einen Onkel.'\n"
        f"- NEUE INFORMATION: 'Klaus' Onkel heit Kalle.'\n"
        f"- ANTWORT: 'Klaus' Onkel heit Kalle.'\n\n"
        f"**BEISPIEL 3 (Kein Bezug):**\n"
        f"- ALTER FAKT: 'Klaus' Eltern sind Hans und Susi.'\n"
        f"- NEUE INFORMATION: 'Klaus' Onkel heit Kalle.'\n"
        f"- ANTWORT: 'Keine'\n\n"
        f"--- NEUER, KONSOLIDIERTER FAKT ---"
    )
    history = [{"role": "user", "content": prompt}]
    try:
        response = await llm_gateway.call_llm(
            provider=provider, model_id=model, api_key=main_api_key, messages=history
        )
        new_fact = response.get("text", "").strip()
        if new_fact.lower() in ['keine', 'none', '']:
            return None
        return new_fact
    except Exception as e:
        logger.error(f"Error during state consolidation: {e}")
        return None




# In backend/memory_extractor.py

# ... (bestehende imports)

# ... (bestehender EXTRACTION_PROMPT)


# Ändere die Signatur von save_memory_snippet in memory_manager.py, damit es is_core_fact akzeptiert
# (Das machen wir im nächsten Schritt, hier nehmen wir es vorweg)

async def extract_and_save_fact(db: Session, chat_id: int, text_block: str, original_prompt: str, main_api_key: str, provider: str, model: str):
    """
    Extrahiert Fakten, klassifiziert sie und konsolidiert sie mit dem bestehenden Wissen.
    """
    logger.info(f"Attempting to extract, classify, and save facts for chat {chat_id} from text: '{text_block}'")
    try:
        gateway_response = {}
        if not text_block and original_prompt:
            extracted_text = f"Ein Bild von '{original_prompt}' wurde generiert."
            logger.info(f"Default fact created for image generation: '{extracted_text}'")
        else:
            extraction_history = [
                {"role": "system", "content": EXTRACTION_PROMPT.format(text_block='')},
                {"role": "user", "content": text_block}
            ]
            gateway_response = await llm_gateway.call_llm(
                provider=provider, model_id=model, api_key=main_api_key, messages=extraction_history
            )
            extracted_text = gateway_response.get("text", "").strip()

        logger.info(f"Extracted text: '{extracted_text}'")

        usage = gateway_response.get("usage")
        cost = gateway_response.get("cost", {})
        if usage and cost.get("total_cost", 0) > 0:
            database.save_cost_entry(
                date=datetime.datetime.now(), model=model,
                input_tokens=usage.get("input_tokens"), output_tokens=usage.get("output_tokens"),
                image_quality=usage.get("image_quality"), image_cost=cost.get("image_cost"),
                total_cost=cost.get("total_cost", 0)
            )

        if extracted_text and extracted_text.lower().strip().rstrip('.') not in ['none', 'keine']:
            lines = extracted_text.split('\n')
            extracted_facts = [line.strip() for line in lines if line.strip() and not line.strip().startswith('---')]
            
            for fact in extracted_facts:
                is_core = False
                try:
                    classification_history = [{"role": "user", "content": IS_CORE_FACT_PROMPT.format(fact=fact)}]
                    classification_response = await llm_gateway.call_llm(
                        provider=provider, model_id=model, api_key=main_api_key, messages=classification_history
                    )
                    if "ja" in classification_response.get("text", "").lower():
                        is_core = True
                        logger.info(f"Fact classified as CORE: '{fact}'")
                    else:
                        logger.info(f"Fact classified as NON-CORE: '{fact}'")
                except Exception as e:
                    logger.error(f"Could not classify fact '{fact}': {e}. Defaulting to NON-CORE.")

                similar_fact_obj = memory_manager.find_similar_memory_snippet(db, text=fact)
                
                if similar_fact_obj:
                    if util.cos_sim(vector_service.model.encode(fact), np.array(json.loads(similar_fact_obj.embedding_json), dtype=np.float32))[0] > 0.98:
                         logger.info(f"Bekannter Fakt ignoriert (Duplikat): '{fact}'.")
                         continue
                    
                    consolidated_fact = await consolidate_state_with_new_fact(
                        db, similar_fact_obj.snippet, fact, main_api_key, provider, model
                    )

                    if consolidated_fact:
                        logger.info(f"Fakt wird konsolidiert/aktualisiert: '{similar_fact_obj.snippet}' -> '{consolidated_fact}'.")
                        memory_manager.update_memory_snippet(db, memory_id=similar_fact_obj.id, new_snippet=consolidated_fact, is_core=is_core)
                        continue 

                logger.info(f"NEUER relevanter Fakt extrahiert: '{fact}'. Speichere in Memory.")
                memory_manager.save_memory_snippet(db, chat_id=chat_id, snippet_text=fact, is_core=is_core)
            
            return extracted_facts
        else:
            logger.info("Kein relevanter Fakt im Textblock gefunden.")
            return None
    except Exception as e:
        logger.error(f"Fehler bei der Fakten-Extraktion: {e}", exc_info=True)
        return None

