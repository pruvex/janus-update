import logging
import datetime
import asyncio
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from backend.context_manager import ContextManager
from backend.llm_providers.base_provider import BaseLLMProvider
from backend.llm_providers.gemini_service import GeminiServiceProvider
from backend.llm_providers.openai_service import OpenAIServiceProvider
from backend.tool_registry import get_all_tool_definitions
from backend.websearch import perform_websearch
from backend import memory_manager


logger = logging.getLogger('janus_backend')

PROVIDER_MAP = {
    "gemini": GeminiServiceProvider,
    "openai": OpenAIServiceProvider,
}

def get_provider(provider_name: str) -> BaseLLMProvider:
    """Factory-Funktion, die eine Instanz des angeforderten Providers zurückgibt."""
    provider_class = PROVIDER_MAP.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unbekannter Provider: {provider_name}")
    return provider_class()

async def call_llm(provider: str, model_id: str, api_key: str, messages: List[Dict], image_data: Optional[str] = None, **kwargs):
    """Ruft den entsprechenden LLM-Provider auf, um eine Antwort zu generieren."""
    llm_provider = get_provider(provider)
    return await llm_provider.generate_response(api_key=api_key, model=model_id, messages=messages, image_data=image_data, **kwargs)

async def generate_image(provider: str, model_id: str, api_key: str, prompt: str, previous_response_id: Optional[str] = None, **kwargs):
    """Ruft den entsprechenden Provider auf, um ein Bild zu generieren."""
    llm_provider = get_provider(provider)
    return await llm_provider.generate_image(api_key=api_key, model=model_id, prompt=prompt, previous_response_id=previous_response_id, **kwargs)

WEBSEARCH_COST_PER_QUERY = 0.01 # 1 Cent pro Websuche

async def reason_and_respond(
    provider: str,
    model: str,
    api_key: str,
    chat_history: list,
    context_manager: ContextManager,
    db: Session,
    user_prompt: str,
    chat_id: int,
    memory_context: Optional[str] = None,
    user_name: Optional[str] = None,
    image_data: Optional[str] = None):
    """
    Nimmt eine fertige Nachrichtenliste entgegen, ruft das LLM auf und führt bei Bedarf eine Websuche als Fallback durch.
    """
    tools = get_all_tool_definitions()
    llm_response = await call_llm(provider, model, api_key, messages=chat_history, tools=tools, image_data=image_data)
    return llm_response


# --- STELLEN SIE SICHER, DASS DIESE FUNKTION AUCH IN DER DATEI IST ---

async def classify_and_save_web_result(db: Session, user_question: str, llm_answer: str, api_key: str, provider: str, model: str, chat_id: int):
    """
    Klassifiziert eine aus einer Websuche gewonnene Information und speichert sie 
    ggf. als ephemere Erinnerung.
    """
    
    
    classification_prompt = f"""
    Du bist ein Daten-Analyst. Deine Aufgabe ist es zu bewerten, ob eine Information zeitlos oder zeitkritisch ist.
    Zeitkritische Informationen sind Dinge wie aktuelle Preise, Nachrichten, Termine, Wetter oder temporäre Zustände, die sich wahrscheinlich in weniger als 48 Stunden ändern.
    Zeitlose Informationen sind Anleitungen, Fakten, technische Daten, biografische Details oder historisches Wissen.

    Benutzerfrage: "{user_question}"
    Antwort: "{llm_answer}"

    Ist die Information in der ANTWORT basierend auf der FRAGE wahrscheinlich zeitkritisch?
    Antworte NUR mit 'JA' oder 'NEIN'.
    """
    
    try:
        messages = [{"role": "user", "content": classification_prompt}]
        classification_model = "gpt-4o-mini" if provider == "openai" else "gemini-1.5-flash-latest"
        
        response = await call_llm(provider, classification_model, api_key, messages)
        decision = response.get("text", "NEIN").strip().upper()

        if "JA" in decision:
            expiration_date = datetime.datetime.now() + datetime.timedelta(days=2) # 48 Stunden Gültigkeit
            logger.info(f"Web result classified as EPHEMERAL. Saving with expiration date. Fact: '{llm_answer[:100]}...'" )
            memory_manager.save_memory_snippet(db, chat_id, llm_answer, is_core=False, expires_at=expiration_date)
        else:
            logger.info(f"Web result classified as TIMELESS. Saving as a regular memory. Fact: '{llm_answer[:100]}...'" )
            memory_manager.save_memory_snippet(db, chat_id, llm_answer, is_core=False, expires_at=None)

    except Exception as e:
        logger.error(f"Error during web result classification and saving: {e}", exc_info=True)

async def simple_llm_generate_content(provider: str, model: str, api_key: str, prompt: str):
    """
    Eine vereinfachte Funktion zum Generieren von Inhalten, die nur den Prompt akzeptiert.
    """
    messages = [{"role": "user", "content": prompt}]
    return await call_llm(provider, model, api_key, messages=messages)
