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

async def reason_and_respond(user_prompt: str, chat_history: List[Dict], memory_context: str, db: Session, api_key: str, model: str, provider: str, context_manager: ContextManager) -> Dict:
    logger.info(f"reason_and_respond: Original user_prompt={user_prompt}")

    system_rules = (
        "Du bist Janus, ein hilfreicher KI-Assistent, der logisch schlussfolgert. Deine Aufgabe ist es, die Frage des Benutzers zu beantwortauen.\n"
        "**DEINE GOLDENE REGEL: Deine Antwort MUSS sich auf die unten stehenden BEWEISE stützen. Erfinde keine Fakten.**\n\n"
        "1.  **FAKTEN AUS DEM LANGZEITGEDÄCHTNIS:** Dies ist die absolute Wahrheit über den Benutzer.\n"
        "2.  **AKTUELLER GESPRÄCHSVERLAUF:** Dieser liefert den unmittelbaren Kontext.\n\n"
        "**DEIN VORGEHEN:**\n"
        "- **KOMBINIERE FAKTEN:** Deine wichtigste Fähigkeit ist es, Fakten zu kombinieren, um eine logische Schlussfolgerung zu ziehen. (Beispiel: Wenn FAKT A 'Kalle mag Blau' ist und FAKT B 'Das Auto des Benutzers ist blau' ist, lautet die Schlussfolgerung 'Kalle würde eine Fahrt in dem Auto gefallen').\n"
        "- **ANTWORTE HILFREICH:** Formuliere eine direkte und nützliche Antwort auf die Frage des Benutzers, basierend auf den Fakten und deinen Schlussfolgerungen.\n"
        "- **GIB WISSENSLÜCKEN ZU:** Wenn die Beweise nicht ausreichen, um eine Frage vollständig zu beantworten, sage das klar und deutlich."
    )

    # Create a new list for the final prompt history to avoid modifying the original
    final_chat_history = []
    
    # Add system rules as the first message for the LLM
    final_chat_history.append({"role": "system", "content": system_rules})

    if memory_context:
        final_chat_history.append({"role": "system", "content": f"--- FAKTEN AUS DEM LANGZEITGEDÄCHTNIS ---\n{memory_context}"})

    # Add the actual chat history
    final_chat_history.extend(chat_history)

    # Add the user's latest prompt as the last message
    final_chat_history.append({"role": "user", "content": user_prompt})

    from backend.tool_registry import get_all_tool_definitions
    tools = get_all_tool_definitions()

    # Pass the constructed history to the LLM
    response = await call_llm(provider, model, api_key, messages=final_chat_history, tools=tools)

    if response.get("type") == "tool_code":
        return response

    return {
        "type": "text",
        "text": response.get("text"),
        "image_url": response.get("image_url"),
        "usage": response.get("usage"),
        "cost": response.get("cost")
    }
