import json
import asyncio  # Add asyncio for await asyncio.to_thread
import base64
import binascii
import logging
import re
import json
from typing import Dict, List, Optional, Any

from backend import llm_providers

from backend.llm_providers.base_provider import BaseLLMProvider
from backend.llm_providers.gemini_service import GeminiServiceProvider
from backend.llm_providers.openai_service import OpenAIServiceProvider
from backend.services import (
    filesystem_manager,
)
from backend.services.context_manager import ContextManager
from backend.services.tool_executor import ToolExecutor
from backend.tool_registry import get_all_tool_definitions
from backend.utils.config_loader import load_config_data, load_model_catalog
from backend.utils import intent_classifier
from sqlalchemy.orm import Session
from backend.services.cost_service import create_cost_entry

logger = logging.getLogger("janus_backend")


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
    """Factory-Funktion, die eine Instanz des angeforderten Providers zurückgibt."""
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
    **kwargs,
):
    """Ruft den entsprechenden LLM-Provider auf, um eine Antwort zu generieren."""
    # --- START KORREKTUR: Provider und Modell Validierung ---
    model_catalog = await asyncio.to_thread(load_model_catalog)
    model_info = model_catalog.get(model_id)

    if not model_info:
        raise ValueError(f"Modell '{model_id}' nicht im Katalog gefunden.")

    expected_provider = model_info.get("provider")

    if not provider and expected_provider:
        logger.warning(
            f"Provider nicht explizit angegeben für Modell '{model_id}'. Verwende erwarteten Provider: '{expected_provider}'."
        )
        provider = expected_provider
    elif provider and expected_provider and provider.lower() != expected_provider.lower():
        raise ValueError(
            f"Angegebener Provider '{provider}' stimmt nicht mit dem erwarteten Provider '{expected_provider}' für Modell '{model_id}' überein."
        )
    elif not provider and not expected_provider:
        raise ValueError(
            f"Kein Provider für Modell '{model_id}' im Katalog gefunden und nicht explizit angegeben."
        )
    # --- ENDE KORREKTUR ---

    llm_provider = get_provider(provider)
    return await llm_provider.generate_response(
        api_key=api_key,
        model=model_id,
        messages=messages,
        image_data=image_data,
        is_image_analysis_request=is_image_analysis_request,
        **kwargs,
    )


async def generate_image(
    provider: str,
    model_id: str,
    api_key: str,
    prompt: str,
    previous_response_id: Optional[str] = None,
    reference_image_path: Optional[str] = None,
    **kwargs,
):
    """Ruft den entsprechenden Provider auf, um ein Bild zu generieren."""
    llm_provider = get_provider(provider)
    return await llm_provider.generate_image(
        api_key=api_key,
        model=model_id,
        prompt=prompt,
        previous_response_id=previous_response_id,
        reference_image_path=reference_image_path,
        **kwargs,
    )


WEBSEARCH_COST_PER_QUERY = 0.01  # 1 Cent pro Websuche



def _attempt_to_fix_json_hallucination(response: Dict) -> Dict:
    """
    Untersucht Text-Antworten auf versehentlich ausgegebenen JSON-Code,
    der eigentlich ein Tool-Call sein sollte.
    """
    if response.get("type") != "text":
        return response

    text = response.get("text", "")
    if not text:
        return response

    # Suche nach JSON-Blöcken, die einen "query"-Parameter enthalten
    try:
        match = re.search(r'(\{.*"query"\s*:\s*".*?\}.*?\}?)', text, re.DOTALL)
        if match:
            potential_json = match.group(1)
            data = json.loads(potential_json)
            
            # Validierung: Ist es ein bekannter Tool-Call?
            if isinstance(data, dict) and "query" in data:
                logger.info(f"🛡️ Gateway: Halluzinierten Tool-Call erkannt und repariert.")
                
                # Tool-Namen bestimmen (Default: perform_websearch)
                tool_name = "find_local_business_tool" if "location" in data else "perform_websearch"

                return {
                    "type": "tool_code",
                    "tool_calls": [{
                        "id": "hallucination_fix_" + str(hash(text)),
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(data)
                        }
                    }],
                    "usage": response.get("usage"),
                    "cost": response.get("cost"),
                    "raw_assistant_response": {"content": text}
                }
    except Exception:
        pass # Parsing fehlgeschlagen, ignoriere

    return response


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
    provider: str,
    model: str,
    api_key: str,
    chat_history: List[Dict],
    context_manager: Any,
    db: Any,
    user_prompt: str,
    chat_id: int,
    tool_executor: ToolExecutor,
    tools_override: Optional[List[Dict]] = None,
    disable_tools: bool = False,
    image_data: Optional[str] = None
) -> Dict[str, Any]:
    
    provider_service = llm_providers.get_provider(provider)
    if not provider_service:
        return {"text": f"Error: Provider '{provider}' not supported."}

    # === ERSTER LLM-AUFRUF (REASONING & TOOL CALLS) ===
    
    # Standard-Parameter für den API-Aufruf
    api_call_params = {
        "api_key": api_key,
        "model": model,
        "messages": chat_history,
        "tools": tools_override if not disable_tools else None,
        "image_data": image_data
    }

    # Wenn der Intent klar eine Websuche ist, zwingen wir das Modell dazu.
    # Dies verhindert das "Plaudern" über die Suche.
    if intent_classifier.is_web_search_intent(user_prompt) and not disable_tools:
        logger.info("Web search intent detected. Forcing 'perform_websearch' tool.")
        api_call_params["tool_choice"] = {"type": "function", "function": {"name": "perform_websearch"}}

    # Wir rufen jetzt mit den vorbereiteten Parametern auf
    first_response = await provider_service.generate_response(**api_call_params)
    
    # Versuche, Halluzinationen zu reparieren (falsche Tool-Calls als Text)
    first_response = _attempt_to_fix_json_hallucination(first_response)

    if "cost" in first_response and first_response["cost"].get("total_cost"):
        create_cost_entry(
            db=db,
            amount=first_response["cost"]["total_cost"],
            model=model,
            provider=provider,
            source_type="conversation",
            input_tokens=first_response.get("usage", {}).get("input_tokens", 0),
            output_tokens=first_response.get("usage", {}).get("output_tokens", 0)
        )

    if first_response.get("type") != "tool_code":
        return first_response

    # === TOOL-AUSFÜHRUNG & ZWEITER LLM-AUFRUF ===

    tool_calls = first_response.get("tool_calls", [])
    if not tool_calls:
        return {"text": "Ein Fehler ist aufgetreten: Leere Tool-Aufrufe."}

    tool_results = await tool_executor.execute_tool_calls(tool_calls)
    
    generated_image_url = None # NEU: Variable für generierte Bild-URL

    # --- START: FINALE, KORRIGIERTE LOGIK ZUM SAMMELN ALLER QUELL-URLS ---
    all_source_urls = set()
    for result in tool_results:
        try:
            content_data = json.loads(result.get("content", "{}"))
            
            # 1. Kosten-Tracking (bleibt unverändert)
            if "cost" in content_data and content_data["cost"].get("total_cost", 0) > 0:
                create_cost_entry(
                    db=db,
                    amount=content_data["cost"]["total_cost"],
                    model=result.get("name"),
                    provider=provider,
                    source_type="tool"
                )

            # 2. URLs sammeln & Bild-URL extrahieren
            if result.get("name") == "generate_image_tool" and content_data.get("url"):
                generated_image_url = content_data["url"] # NEU: Bild-URL speichern
            
            if "text" in content_data and content_data["text"]:
                markdown_links = re.findall(r'\[.*?\]\((https?://[^\s)]+)\)', content_data["text"])
                for url in markdown_links:
                    all_source_urls.add(url)
                    
            # Fallback: URLs aus dem urls-Feld (falls vorhanden)
            if "urls" in content_data and content_data["urls"]:
                for url in content_data["urls"]:
                    if isinstance(url, str):
                        all_source_urls.add(url)
                    
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Konnte Tool-Content nicht vollständig verarbeiten: {e}")
    # --- ENDE: FINALE LOGIK ZUM SAMMELN ---
    
    second_call_history = provider_service.prepare_history_for_second_call(
        chat_history=chat_history,
        raw_assistant_response=first_response.get("raw_assistant_response"),
        tool_results=tool_results
    )

    # === ZWEITER LLM-AUFRUF (FINALE ANTWORT) ===
    
    final_response = await provider_service.generate_response(
        api_key=api_key,
        model=model,
        messages=second_call_history,
        tools=None 
    )

    if "cost" in final_response and final_response["cost"].get("total_cost"):
         create_cost_entry(
            db=db,
            amount=final_response["cost"]["total_cost"],
            model=model,
            provider=provider,
            source_type="conversation",
            input_tokens=final_response.get("usage", {}).get("input_tokens", 0),
            output_tokens=final_response.get("usage", {}).get("output_tokens", 0)
        )
    
    # NEU: Füge die generierte Bild-URL zur final_response hinzu
    if generated_image_url:
        final_response["image_url"] = generated_image_url

    # --- NUR NOCH DAS URLS-FELD FÜR DIE UI AKTUALISIEREN ---
    if all_source_urls:
        # Wir fügen die URLs nur noch als separates Feld für die UI hinzu
        # und lassen den von der KI formatierten Text unberührt.
        final_response["urls"] = sorted(list(all_source_urls))
        
    logger.debug(f"llm_gateway.py: reason_and_respond - Final response before returning: {final_response}") # NEU

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
