import logging
from . import llm_gateway, crud
from sqlalchemy.orm import Session

logger = logging.getLogger('janus_backend')

EXTRACTION_PROMPT = (
    "Du bist ein Assistent, dessen einzige Aufgabe es ist, aus einem Gesprächs-Ausschnitt "
    "einen einzigen, dauerhaft relevanten Fakt zu extrahieren. "
    "Fakten sind z.B. persönliche Vorlieben, Namen, Ziele, Projekte oder wichtige Termine. "
    "Formuliere den Fakt in einem kurzen, prägnanten Satz. "
    "Wenn der Text keine dauerhaft relevanten Fakten enthält, antworte AUSSCHLIESSLICH mit dem Wort 'None'."
    "\n\n--- Gesprächs-Ausschnitt ---"
    "{text_block}"
    "\n\n--- Extrahierter Fakt ---"
)

async def extract_and_save_fact(db: Session, chat_id: int, text_block: str, api_key: str):
    """
    Extrahiert einen Fakt aus einem Textblock und speichert ihn, wenn er relevant ist.
    """
    try:
        # Wir verwenden ein günstiges, schnelles Modell für diese Aufgabe.
        model_id = "gpt-4o-mini" # Annahme, kann später konfiguriert werden
        provider = "openai" # Annahme

        prompt = EXTRACTION_PROMPT.format(text_block=text_block)
        
        # Wir erstellen eine minimale chat_history nur für diesen einen Aufruf
        extraction_history = [{"role": "user", "content": prompt}]

        gateway_response = await llm_gateway.call_llm(
            provider,
            model_id, 
            "", # Prompt ist in der History
            api_key,
            chat_history=extraction_history
        )

        extracted_fact = gateway_response.get("text", "").strip()

        if extracted_fact and extracted_fact.lower() != 'none':
            logger.info(f"Relevanter Fakt extrahiert: '{extracted_fact}'. Speichere in Memory.")
            crud.save_memory_snippet(db, chat_id=chat_id, snippet_text=extracted_fact)
            return extracted_fact
        else:
            logger.info("Kein relevanter Fakt im Textblock gefunden.")
            return None

    except Exception as e:
        logger.error(f"Fehler bei der Fakten-Extraktion: {e}")
        return None
