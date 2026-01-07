import json
import asyncio
import base64
import logging
import re
from typing import Dict, List, Optional, Any
from functools import lru_cache

from fastapi import BackgroundTasks
from backend import llm_providers
from backend.llm_providers.base_provider import BaseLLMProvider
from backend.llm_providers.gemini_service import GeminiServiceProvider
from backend.llm_providers.openai_service import OpenAIServiceProvider
from backend.services.tool_executor import ToolExecutor
from backend.services.tool_manager import tool_manager # Hinzugefügt
from pydantic import BaseModel
from backend.utils.config_loader import load_model_catalog
from backend.utils import intent_classifier
from sqlalchemy.orm import Session
from backend.services.cost_service import create_cost_entry

logger = logging.getLogger("janus_backend")

# --- HIGH-IMPACT FIX 1: CACHING FÜR MODELLKATALOG ---
@lru_cache(maxsize=1)
def get_cached_model_catalog():
    """Lädt den Modellkatalog und cacht das Ergebnis in-memory."""
    logger.info("Lade und cache den Modellkatalog...")
    return load_model_catalog()


def _is_user_intent_aligned_with_tool(user_prompt: str, tool_name: str) -> bool:
    """
    Prüft, ob die Absicht des Benutzers mit dem vom LLM vorgeschlagenen Werkzeug übereinstimmt.
    Verhindert, dass das LLM unerwünschte Aktionen ausführt (z.B. eine Datei erstellt, obwohl nur eine Frage gestellt wurde).
    """
    prompt_lower = user_prompt.lower()

    # Werkzeuge, die eine explizite Bestätigung erfordern, da sie das Dateisystem verändern.
    critical_file_tools = [
        "create_file_tool",
        "create_pdf_from_markdown",
        "delete_file_tool",
        "rename_file_tool",
        "move_file_tool",
        "create_directory_tool",
        "delete_directory_tool",
        "save_mp3_tool",
    ]

    # Schlüsselwörter, die der Benutzer explizit verwenden muss, um diese Aktionen auszulösen.
    explicit_keywords = [
        "speicher",
        "save",
        "erstelle",
        "create",
        "schreib",
        "write",
        "mache",
        "make",
        "exportiere",
        "export",
        "datei",
        "file",
        "pdf",
        "dokument",
        "document",
        "lösche",
        "delete",
        "benenne um",
        "rename",
        "verschiebe",
        "move",
        "ordner",
        "directory",
        "mp3",
    ]

    if tool_name in critical_file_tools:
        # Wenn ein kritisches Werkzeug aufgerufen wird, MUSS der Prompt ein Schlüsselwort enthalten.
        if any(keyword in prompt_lower for keyword in explicit_keywords):
            logger.info(f"User intent for tool '{tool_name}' is aligned (keyword found).")
            return True
        else:
            # Der Benutzer hat nur eine Frage gestellt, aber die KI will eine Datei erstellen. -> Nicht erlaubt!
            logger.warning(
                f"User intent for tool '{tool_name}' MISMATCH. "
                f"User prompt did not contain explicit keywords. Aborting tool call."
            )
            return False

    # Für alle anderen, nicht-kritischen Werkzeuge (wie Websuche, Bildgenerierung etc.) vertrauen wir der KI.
    return True


PROVIDER_MAP = {
    "gemini": GeminiServiceProvider,
    "openai": OpenAIServiceProvider,
}


def get_provider(provider_name: str) -> BaseLLMProvider:
    """Gibt eine Instanz des angeforderten Providers zurück."""
    provider_class = PROVIDER_MAP.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unbekannter Provider: {provider_name}")
    return provider_class()


async def call_llm(
    provider: str, 
    model_id: str, 
    api_key: str, 
    messages: List[Dict], 
    image_data: Optional[str] = None,
    is_image_analysis_request: bool = False,
    **kwargs
):
    """Ruft den entsprechenden LLM-Provider auf, um eine Antwort zu generieren."""
    try:
        model_catalog = await asyncio.to_thread(get_cached_model_catalog)
        if model_id not in model_catalog:
            raise ValueError(f"Modell '{model_id}' nicht im Modellkatalog gefunden.")
        
        llm_provider = get_provider(provider)
        return await llm_provider.generate_response(
            api_key=api_key,
            model=model_id,
            messages=messages,
            image_data=image_data,
            is_image_analysis_request=is_image_analysis_request,
            **kwargs
        )
    except Exception as e:
        logger.error(f"Fehler beim Aufruf des LLM-Providers: {str(e)}", exc_info=True)
        raise


def _log_cost_in_background(db: Session, cost_data: Dict):
    """Hilfsfunktion zum asynchronen Speichern der Kosten."""
    try:
        create_cost_entry(db=db, **cost_data)
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Kosten im Hintergrund: {e}")


# --- HIGH-IMPACT FIX 2: TOOL-ERGEBNISSE KOMPRIMIEREN ---
def _trim_tool_results(tool_results: List[Dict]) -> List[Dict]:
    """Kürzt den Inhalt von Tool-Ergebnissen, um die Chat-History klein zu halten."""
    trimmed_results = []
    for result in tool_results:
        trimmed_result = result.copy()
        content_str = trimmed_result.get("content", "")
        if len(content_str) > 500: # Kürze alles über 500 Zeichen
            try:
                content_json = json.loads(content_str)
                # Spezifische Logik für Web-Suche
                if "snippets" in content_json:
                    content_json["snippets"] = content_json["snippets"][:2] # Nur die Top 2 Snippets
                
                trimmed_result["content"] = json.dumps({
                    "summary": "Ergebnis wurde gekürzt.",
                    **content_json
                })
            except json.JSONDecodeError:
                trimmed_result["content"] = content_str[:500] + "... (gekürzt)"
        trimmed_results.append(trimmed_result)
    return trimmed_results


def _aggregate_cost(existing_cost: Dict, new_cost: Dict) -> Dict:
    """Aggregiert Kostendaten (z.B. Gesamtkosten)."""
    aggregated = existing_cost.copy()
    for key, value in new_cost.items():
        if key == "total_cost" and isinstance(value, (int, float)):
            aggregated[key] = aggregated.get(key, 0.0) + value
        elif isinstance(value, (int, float)):
            aggregated[key] = aggregated.get(key, 0.0) + value
        else:
            aggregated[key] = value  # Oder andere Aggregationslogik für nicht-numerische Werte
    return aggregated


async def reason_and_respond(
    provider: str, model: str, api_key: str, chat_history: List[Dict],
    context_manager: Any, db: Any, user_prompt: str, chat_id: int,
    tool_executor: ToolExecutor, tools_override: Optional[List[Dict]] = None,
    disable_tools: bool = False, image_data: Optional[str] = None
) -> Dict[str, Any]:
    
    provider_service = get_provider(provider)
    MAX_TOOL_ROUNDS = 1 # --- HIGH-IMPACT FIX 3: NUR EINE TOOL-RUNDE ERLAUBEN ---
    current_round = 0
    current_chat_history = list(chat_history)
    
    background_tasks = BackgroundTasks()

    while current_round < MAX_TOOL_ROUNDS:
        current_round += 1
        
        # Alle verfügbaren Tools an den Provider übergeben, es sei denn, Tools sind komplett deaktiviert
        # Wir holen die Tools vom tool_manager, da ToolExecutor keine get_available_tools Methode hat.
        all_available_tools = list(tool_manager.get_all_tools().values())
        
        # Initialisiere force_tool_name als None
        force_tool_name_for_api = None

        if current_round == 1 and intent_classifier.is_web_search_intent(user_prompt) and not disable_tools:
            logger.info("Web search intent detected. Forcing 'perform_websearch' tool.")
            force_tool_name_for_api = "perform_websearch" # Setze den Namen des zu erzwingenden Tools

        api_call_params = {
            "api_key": api_key, "model": model, "messages": current_chat_history,
            "tools": all_available_tools if not disable_tools else None, # Immer alle Tools übergeben
            "image_data": image_data if current_round == 1 else None,
            "force_tool_name": force_tool_name_for_api # Den neuen Parameter übergeben
        }

        response = await provider_service.generate_response(**api_call_params)
        
        # --- HIGH-IMPACT FIX 4: ASYNCHRONES KOSTEN-TRACKING ---
        if "cost" in response and response["cost"].get("total_cost"):
            cost_data = {
                "amount": response["cost"]["total_cost"], "model": model, "provider": provider,
                "source_type": "conversation",
                "input_tokens": response.get("usage", {}).get("input_tokens", 0),
                "output_tokens": response.get("usage", {}).get("output_tokens", 0)
            }
            background_tasks.add_task(_log_cost_in_background, db, cost_data)

        if response.get("type") != "tool_code":
            if background_tasks:
                asyncio.create_task(background_tasks())
            return response

        tool_calls = response.get("tool_calls", [])
        if not tool_calls:
            return {"text": "Ein Fehler ist aufgetreten: Leere Tool-Aufrufe."}

        tool_results = await tool_executor.execute_tool_calls(tool_calls)
        trimmed_tool_results = _trim_tool_results(tool_results)  # Gekürzte Ergebnisse verwenden

        current_chat_history = provider_service.prepare_history_for_second_call(
            chat_history=current_chat_history,
            raw_assistant_response=response.get("raw_assistant_response"),
            tool_results=trimmed_tool_results
        )

    # Fallback nach max. Runden
    final_response = await provider_service.generate_response(
        api_key=api_key, 
        model=model, 
        messages=current_chat_history, 
        tools=None
    )

    if background_tasks:
        asyncio.create_task(background_tasks())
    
    return final_response


async def get_active_image_generation_model(provider: str) -> Optional[str]:
    """
    Ermittelt das aktuell aktive Bildgenerierungsmodell für den angegebenen Provider
    basierend auf der Konfiguration und dem Modellkatalog.
    """
    logger.debug(f"get_active_image_generation_model called for provider: {provider}")
    config = await asyncio.to_thread(load_config_data)
    
    last_used_text_model_id = config.get("last_used_model") 
    model_catalog = await asyncio.to_thread(load_model_catalog)
    
    logger.debug(f"Config last_used_model: {last_used_text_model_id}")
    logger.debug(f"Model catalog loaded. Number of models: {len(model_catalog)}")

    # NEU: Debugging des relevanten Teils des Modellkatalogs
    logger.debug(f"Model catalog for provider '{provider}':")
    for model_id, model_info in model_catalog.items():
        if model_info.get("provider") == provider:
            logger.debug(f"  - ID: {model_id}, Type: {model_info.get('type')}, ImageGenModel: {model_info.get('image_generation_model')}")

    # 1. Prüfe, ob das aktive Textmodell ein dediziertes Bildgenerierungsmodell hat
    if last_used_text_model_id and last_used_text_model_id in model_catalog:
        text_model_info = model_catalog[last_used_text_model_id]
        logger.debug(f"Text model info: {text_model_info}")
        if text_model_info.get("provider") == provider:
            image_gen_model_id = text_model_info.get("image_generation_model")
            logger.debug(f"Image generation model from text model info: {image_gen_model_id}")
            if image_gen_model_id and image_gen_model_id in model_catalog and model_catalog[image_gen_model_id].get("type") == "image":
                logger.info(f"Using image_generation_model '{image_gen_model_id}' from active text model '{last_used_text_model_id}'.")
                return image_gen_model_id
            else:
                logger.warning(f"Active text model '{last_used_text_model_id}' for provider '{provider}' does not specify a valid image_generation_model in catalog (or it's not type 'image'). Returning None from step 1.")
        else:
            logger.debug(f"Provider mismatch for text model. Text model provider: {text_model_info.get('provider')}, requested provider: {provider}")
    else:
        logger.warning(f"No last used text model '{last_used_text_model_id}' found in catalog for provider '{provider}' (or last_used_text_model_id is None). Continuing to fallback logic.")

    # 2. Fallback: Finde das "beste" Bildmodell für den Provider
    logger.debug(f"Entering fallback logic for provider: {provider}")
    if provider == "gemini":
        # Priorisiere gemini-2.5-flash-image-preview für normale Bildgenerierung
        if "gemini-2.5-flash-image-preview" in model_catalog:
            logger.info("Fallback: Using 'gemini-2.5-flash-image-preview' for Gemini (as requested).")
            return "gemini-2.5-flash-image-preview"
        elif "gemini-3-pro-image-preview" in model_catalog:
            logger.info("Fallback: Using 'gemini-3-pro-image-preview' for Gemini.")
            return "gemini-3-pro-image-preview"
        logger.debug(f"No specific Gemini image model found in fallback for provider: {provider}. Returning None.") # NEU
    elif provider == "openai":
        if "dall-e-3" in model_catalog:
            logger.info("Fallback: Using 'dall-e-3' for OpenAI.")
            return "dall-e-3"
        logger.debug(f"No specific OpenAI image model found in fallback for provider: {provider}. Returning None.") # NEU

    final_return_value = None # NEU
    logger.warning(f"No suitable image generation model found for provider '{provider}' after all attempts. Returning {final_return_value}") # NEU
    return final_return_value # NEU


async def simple_llm_generate_content(provider: str, model: str, api_key: str, prompt: str):
    """
    Eine vereinfachte Funktion zum Generieren von Inhalten, die nur den Prompt akzeptiert.
    """
    messages = [{"role": "user", "content": prompt}]
    return await call_llm(provider, model, api_key, messages=messages)
