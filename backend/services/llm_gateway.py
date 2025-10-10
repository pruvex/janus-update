import logging
import datetime
import asyncio
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from backend.services.context_manager import ContextManager
from backend.llm_providers.base_provider import BaseLLMProvider
from backend.llm_providers.gemini_service import GeminiServiceProvider
from backend.llm_providers.openai_service import OpenAIServiceProvider
from backend.tool_registry import get_all_tool_definitions
from backend.services.websearch import perform_websearch
from backend.llm_providers.capabilities.gemini_web_search import GeminiWebSearch
from backend.services import memory_manager


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
        "speicher", "save", "erstelle", "create", "schreib", "write",
        "mache", "make", "exportiere", "export", "datei", "file",
        "pdf", "dokument", "document", "lösche", "delete", "benenne um",
        "rename", "verschiebe", "move", "ordner", "directory", "mp3",
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


async def reason_and_respond(
    provider: str,
    model: str,
    api_key: str,
    chat_history: list,
    context_manager: ContextManager,
    db: Session,
    user_prompt: str,
    chat_id: int,
    system_instruction: Optional[str] = None,
    memory_context: Optional[str] = None,
    user_name: Optional[str] = None,
    image_data: Optional[str] = None,
    is_image_analysis_request: bool = False,
    disable_tools: bool = False,  # NEU
):  # NEU
    """
    Nimmt eine fertige Nachrichtenliste entgegen, ruft das LLM auf und führt bei Bedarf eine Websuche als Fallback durch.

    Args:
        provider: Der LLM-Provider (z.B. 'gemini', 'openai')
        model: Die zu verwendende Modell-ID
        api_key: Der API-Schlüssel für den LLM-Provider
        chat_history: Die Chat-Historie im ChatML-Format
        context_manager: Der Kontext-Manager für die Verwaltung des Kontexts
        db: Die Datenbank-Session
        user_prompt: Die Benutzereingabe
        chat_id: Die ID des Chats
        system_instruction: Optionaler expliziter System-Prompt, der den Standard-Prompt überschreibt
        memory_context: Optionaler Speicherkontext
        user_name: Optionaler Benutzername
        image_data: Optionale Bilddaten für visuelle Eingaben
        is_image_analysis_request: NEU: Flag, ob es sich um eine reine Bildanalyse-Anfrage handelt.
        disable_tools: NEU: Flag, um die Werkzeugnutzung für diesen Aufruf zu deaktivieren.
    """
    tools = get_all_tool_definitions() if not disable_tools else None
    if disable_tools:
        logger.info("Tool usage has been explicitly disabled for this LLM call.")

    llm_response = await call_llm(
        provider,
        model,
        api_key,
        messages=chat_history,
        tools=tools,
        image_data=image_data,
        is_image_analysis_request=is_image_analysis_request,
    )

    if llm_response.get("type") == "tool_code":
        tool_name = llm_response["tool_name"]
        tool_args = llm_response["tool_args"]

        # --- START: HIER IST DIE NEUE, ROBUSTE LOGIK ---
        if not _is_user_intent_aligned_with_tool(user_prompt, tool_name):
            # Die Absicht des Benutzers und das Werkzeug stimmen nicht überein.
            # Wir verwerfen den Werkzeugaufruf und bitten die KI, die Frage direkt zu beantworten.
            
            # 1. Erstelle eine neue Anweisung für die KI.
            clarification_prompt = (
                "Deine vorherige Idee, ein Werkzeug zu benutzen, war nicht korrekt. "
                "Der Benutzer hat nur eine Frage gestellt. Bitte beantworte die folgende Frage direkt und umfassend im Chat. "
                "Du kannst am Ende deiner Antwort vorschlagen, die Informationen zu speichern, wenn es passend erscheint.\n\n"
                f"Ursprüngliche Frage des Benutzers: '{user_prompt}'"
            )

            # 2. Wir entfernen die letzte (fehlerhafte) Assistant-Antwort aus der Historie, falls sie dort schon ist.
            # In deinem Code wird die Historie erst später modifiziert, also können wir sie hier direkt verwenden.
            # Wir fügen die neue Anweisung als User-Nachricht hinzu, um die KI zu korrigieren.
            
            # WICHTIG: Wir verwenden die ursprüngliche `chat_history` ohne die fehlerhafte Werkzeug-Antwort.
            # Wir ersetzen die letzte User-Nachricht durch unsere Korrekturanweisung.
            corrected_history = chat_history[:-1] # Entfernt die letzte User-Nachricht mit dem ganzen Kontext
            corrected_history.append({"role": "user", "content": clarification_prompt})

            logger.info("Re-prompting LLM to answer directly after misaligned tool call.")
            
            # 3. Rufe das LLM erneut auf, diesmal OHNE Werkzeuge, um eine Textantwort zu erzwingen.
            second_llm_response = await call_llm(
                provider,
                model,
                api_key,
                messages=corrected_history,
                tools=None, # Wichtig: Keine Werkzeuge erlauben!
            )
            return second_llm_response
        # --- ENDE: NEUE LOGIK ---


        # Der Rest der Funktion bleibt gleich...
        # --- START: KORRIGIERTER, VEREINHEITLICHTER BLOCK ---
        
        # Es gibt keine Sonderbehandlung mehr. Jedes Werkzeug wird gleich behandelt.
        # Die Logik prüft, ob es sich um die spezielle Websuche handelt, die eine 
        # zweite LLM-Runde zur Zusammenfassung benötigt.

        if tool_name == "perform_websearch":
            logger.info(f"Unified Web Search requested with query: {tool_args.get('query')}")

            # 1. Hole die rohe Assistenten-Antwort vom ersten Aufruf.
            # Diese ist in der ursprünglichen llm_response enthalten.
            raw_assistant_response = llm_response.get("raw_assistant_response")
            if not raw_assistant_response:
                logger.error("Could not find raw_assistant_response in LLM response.")
                return {"type": "text", "text": "Error processing tool call."}

            # 2. Hänge die Antwort des Assistenten an die Historie an.
            chat_history.append(raw_assistant_response)

            # 3. Extrahiere die tool_call_id.
            tool_call_id = raw_assistant_response.get("tool_calls", [{}])[0].get("id")
            if not tool_call_id:
                logger.error("Could not extract tool_call_id from assistant response.")
                return {"type": "text", "text": "Error processing tool call ID."}

            # 4. Führe das zentrale Websuch-Werkzeug aus.
            web_search_result = await perform_websearch(
                query=tool_args.get("query", "")
            )

            # 5. Erstelle den Prompt für die Zusammenfassung mit den URLs.
            web_search_text = web_search_result.get("text", "Keine Ergebnisse gefunden.")
            web_search_urls = web_search_result.get("urls", [])
            summarization_prompt = (
                "Hier sind die Ergebnisse einer Websuche. Formuliere basierend auf diesen Informationen eine klare und hilfreiche Antwort auf die ursprüngliche Frage des Benutzers. "
                "Gib am Ende deiner Antwort einen Abschnitt 'Quellen:' an und liste dort die gefundenen URLs auf.\n\n"
                f"Ursprüngliche Frage: '{user_prompt}'\n\n" 
                f"--- Suchergebnisse ---\n{web_search_text}\n\n"
                f"--- Gefundene URLs ---\n"
                + "\n".join([f"- {url}" for url in web_search_urls])
            )

            # 6. Hänge das Werkzeug-Ergebnis an die Historie an.
            chat_history.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": summarization_prompt, 
                }
            )

            # 7. Rufe das LLM erneut auf, um die Ergebnisse zusammenzufassen.
            second_llm_response = await call_llm(
                provider, model, api_key, messages=chat_history, tools=tools
            )
            return second_llm_response
        else:
            # Dies ist der Standardfall für alle ANDEREN Werkzeuge (Dateisystem etc.).
            # Wir geben den validierten Werkzeugaufruf einfach an main.py weiter.
            logger.info(f"Tool call '{tool_name}' validated and passed for execution.")
            return llm_response
        # --- ENDE: KORRIGIERTER, VEREINHEITLICHTER BLOCK ---

    return llm_response


# --- STELLEN SIE SICHER, DASS DIESE FUNKTION AUCH IN DER DATEI IST ---

async def simple_llm_generate_content(
    provider: str, model: str, api_key: str, prompt: str
):
    """
    Eine vereinfachte Funktion zum Generieren von Inhalten, die nur den Prompt akzeptiert.
    """
    messages = [{"role": "user", "content": prompt}]
    return await call_llm(provider, model, api_key, messages=messages)