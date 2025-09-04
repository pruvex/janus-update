import logging
from typing import List, Dict, Optional
from tenacity import RetryError
from sqlalchemy.orm import Session
from backend.context_manager import ContextManager
from backend.llm_providers import openai_service, gemini_service
from backend.cost_calculator import MODEL_PRICES

logger = logging.getLogger('janus_backend')

async def call_llm(provider: str, model_id: str, prompt: str, api_key: str, chat_history: Optional[List[Dict]] = None, tools: Optional[List[Dict]] = None):
    if not chat_history:
        chat_history = [{"role": "user", "content": prompt}]

    model_info = MODEL_PRICES.get(model_id)
    if not model_info:
        raise ValueError(f"Model {model_id} not found in model catalog.")

    try:
        if provider == "openai":
            # The tools are passed to the openai_service
            return await openai_service._call_openai_api(api_key, model_id, chat_history, model_info, tools)
        elif provider == "gemini":
            # Gemini service in this implementation does not use tools, so we don't pass them.
            return await gemini_service._call_gemini_api(api_key, model_id, chat_history, model_info)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    except RetryError as e:
        logger.error(f"API call failed after multiple retries: {e}")
        return {"type": "text", "text": "Die Anfrage an die API ist nach mehreren Versuchen fehlgeschlagen.", "image_url": None, "usage": {}, "cost": {}}

async def reason_and_respond(user_prompt: str, chat_history: List[Dict], memory_context: str, db: Session, api_key: str, model: str, provider: str, context_manager: ContextManager) -> Dict:
    logger.info(f"reason_and_respond: Original user_prompt={user_prompt}")
    
    system_rules = (
        "Du bist Janus, ein hilfreicher KI-Assistent, der logisch schlussfolgert. Deine Aufgabe ist es, die Frage des Benutzers zu beantworten.\n"
        "**DEINE GOLDENE REGEL: Deine Antwort MUSS sich auf die unten stehenden BEWEISE stützen. Erfinde keine Fakten.**\n\n"
        "1.  **FAKTEN AUS DEM LANGZEITGEDÄCHTNIS:** Dies ist die absolute Wahrheit über den Benutzer.\n"
        "2.  **AKTUELLER GESPRÄCHSVERLAUF:** Dieser liefert den unmittelbaren Kontext.\n\n"
        "**DEIN VORGEHEN:**\n"
        "- **KOMBINIERE FAKTEN:** Deine wichtigste Fähigkeit ist es, Fakten zu kombinieren, um eine logische Schlussfolgerung zu ziehen. (Beispiel: Wenn FAKT A 'Kalle mag Blau' ist und FAKT B 'Das Auto des Benutzers ist blau' ist, lautet die Schlussfolgerung 'Kalle würde eine Fahrt in dem Auto gefallen').\n"
        "- **ANTWORTE HILFREICH:** Formuliere eine direkte und nützliche Antwort auf die Frage des Benutzers, basierend auf den Fakten und deinen Schlussfolgerungen.\n"
        "- **GIB WISSENSLÜCKEN ZU:** Wenn die Beweise nicht ausreichen, um eine Frage vollständig zu beantworten, sage das klar und deutlich."
    )

    final_prompt_for_llm = f"{system_rules}\n\n"
    if memory_context:
        final_prompt_for_llm += f"--- FAKTEN AUS DEM LANGZEITGEDÄCHTNIS ---\n{memory_context}\n\n"
        
    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
    final_prompt_for_llm += f"--- AKTUELLER GESPRÄCHSVERLAUF ---\n{history_str}\n\n"
    final_prompt_for_llm += f"--- FRAGE DES BENUTZERS ---\n{user_prompt}\n\n--- ANTWORT ---"

    # We need to get the tools here to pass them to call_llm
    from backend.tool_registry import get_all_tool_definitions
    tools = get_all_tool_definitions()

    response = await call_llm(provider, model, final_prompt_for_llm, api_key, chat_history=[], tools=tools)
    
    if response.get("type") == "tool_code":
        return response
    
    return {
        "type": "text", 
        "text": response.get("text"), 
        "image_url": response.get("image_url"), 
        "usage": response.get("usage"), 
        "cost": response.get("cost")
    }
