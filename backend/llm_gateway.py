import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from backend.context_manager import ContextManager
from backend.llm_providers.base_provider import BaseLLMProvider
from backend.llm_providers.gemini_service import GeminiServiceProvider
from backend.llm_providers.openai_service import OpenAIServiceProvider

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

async def call_llm(provider: str, model_id: str, api_key: str, messages: List[Dict], **kwargs):
    """Ruft den entsprechenden LLM-Provider auf, um eine Antwort zu generieren."""
    llm_provider = get_provider(provider)
    return await llm_provider.generate_response(api_key=api_key, model=model_id, messages=messages, **kwargs)

async def generate_image(provider: str, model_id: str, api_key: str, prompt: str, **kwargs):
    """Ruft den entsprechenden Provider auf, um ein Bild zu generieren."""
    llm_provider = get_provider(provider)
    return await llm_provider.generate_image(api_key=api_key, model=model_id, prompt=prompt, **kwargs)

WEBSEARCH_COST_PER_QUERY = 0.01 # 1 Cent pro Websuche

async def reason_and_respond(user_prompt: str, chat_history: List[Dict], memory_context: str, db: Session, api_key: str, model: str, provider: str, context_manager: ContextManager) -> Dict:
    logger.info(f"reason_and_respond: Original user_prompt={user_prompt}")

    system_rules = f"""Du bist Janus, ein ultra-präziser und logischer Assistent. Deine Aufgabe ist es, die Fragen des Benutzers auf Basis der unten genannten FAKTEN zu beantworten.

**DEINE REGELN SIND ABSOLUT:**
1.  **FAKTENBASIERT ANTWORTEN:** Deine Antwort muss sich direkt aus den Informationen im 'LANGZEITGEDÄCHTNIS' oder dem 'AKTUELLEN GESPRÄCHSVERLAUF' ableiten lassen.
2.  **LOGISCHE SCHLUSSFOLGERUNGEN ZIEHEN:** Du darfst und sollst gegebene Fakten kombinieren, um logische Schlussfolgerungen zu ziehen. Wenn du eine Schlussfolgerung ziehst, die nicht explizit als Fakt genannt wird, musst du deine Argumentation offenlegen.
    - **BEISPIEL:**
        - FAKT A: 'Kalle ist Gudruns Mann.'
        - FAKT B: 'Kalle wohnt in Köln.'
        - FRAGE: 'Wo wohnt Gudrun?'
        - KORREKTE ANTWORT: 'Da Kalle der Mann von Gudrun ist und in Köln wohnt, ist es sehr wahrscheinlich, dass Gudrun ebenfalls in Köln wohnt.'
3.  **KEINE HALLUZINATIONEN:** Erfinde niemals Fakten, Namen oder Beziehungen. Wenn du eine Schlussfolgerung ziehst, muss sie auf den gegebenen Fakten beruhen.
4.  **WISSENSLÜCKEN ZUGEBEN:** Wenn die Fakten keine direkte Antwort oder eine logische Schlussfolgerung zulassen, antworte ausschließlich: 'Ich habe dazu keine Informationen in meinen Fakten.'
5.  **AUF AUSSAGEN REAGIEREN:** Wenn die letzte Nutzereingabe offensichtlich nur neue Informationen liefert und keine Frage stellt, antworte mit einer kurzen, freundlichen Bestätigung (z.B. 'Danke, ich habe mir das gemerkt.' oder 'Verstanden.').

--- FAKTENGRUNDLAGE ---
LANGZEITGEDÄCHTNIS:
{memory_context}

AKTUELLER GESPRÄCHSVERLAUF:
"""

    # Create a new list for the final prompt history
    final_chat_history = []
    
    # Add system rules and memory as the first message
    final_chat_history.append({"role": "system", "content": system_rules})

    # Add the actual chat history (which already includes the latest user prompt from main.py)
    final_chat_history.extend(chat_history)

    from backend.tool_registry import get_all_tool_definitions
    from backend.websearch import perform_websearch # Import perform_websearch
    tools = get_all_tool_definitions()

    

    # Pass the constructed history to the LLM
    response = await call_llm(provider, model, api_key, messages=final_chat_history, tools=tools)

    # Check if the LLM explicitly states it has no information
    if response.get("type") == "text" and response.get("text") == "Ich habe dazu keine Informationen in meinen Fakten.":
        logger.info("LLM indicated no information in facts. Performing web search...")
        web_result = await perform_websearch(user_prompt)
        return {
            "type": "text",
            "text": web_result,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "model": "websearch"},
            "cost": {"total_cost": WEBSEARCH_COST_PER_QUERY}
        }

    if response.get("type") == "tool_code":
        return response

    return {
        "type": "text",
        "text": response.get("text"),
        "image_url": response.get("image_url"),
        "usage": response.get("usage"),
        "cost": response.get("cost")
    }
