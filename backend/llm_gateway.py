import logging
import datetime
import asyncio  # <--- DIESE ZEILE HINZUFÜGEN
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from backend.context_manager import ContextManager
from backend.llm_providers.base_provider import BaseLLMProvider
from backend.llm_providers.gemini_service import GeminiServiceProvider
from backend.llm_providers.openai_service import OpenAIServiceProvider
from backend.tool_registry import get_all_tool_definitions


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

async def reason_and_respond(user_prompt: str, chat_history: List[Dict], memory_context: str, db: Session, api_key: str, model: str, provider: str, context_manager: ContextManager, chat_id: int, user_name: Optional[str] = None) -> Dict:
    logger.info(f"reason_and_respond: Original user_prompt={user_prompt}")

    current_month_year = datetime.date.today().strftime("%B %Y")

    identity_prompt = ""
    if user_name:
        identity_prompt = f"**BENUTZERIDENTITÄT:** Du sprichst mit {user_name}. Alle Fakten, die sich auf '{user_name}' oder 'der Benutzer' beziehen, beziehen sich auf die Person, die 'ich' oder 'mein' sagt.\n\n"

    system_rules = f"""Du bist Janus, ein ultra-präziser und logischer Assistent. Deine Aufgabe ist es, die Fragen des Benutzers auf Basis der unten genannten FAKTEN zu beantworten.
Aktuelles Datum: {current_month_year}. Beziehe dich bei zeitbezogenen Fragen auf dieses Datum.

{identity_prompt}**DEINE REGELN SIND ABSOLUT:**
0.  **PRINZIP DER GEGENWARTS-WAHRHEIT:** Alle Fakten im 'LANGZEITGEDÄCHTNIS' repräsentieren den **aktuellen, wahren Zustand**, es sei denn, der unmittelbare Gesprächsverlauf widerspricht dem explizit. Ein Fakt wie "Du hast 10 Äpfel" bedeutet, du hast sie **jetzt**.

1.  **FAKTENBASIERT ANTWORTEN:** Deine Antwort muss sich **ausschließlich** aus den Informationen im 'LANGZEITGEDÄCHTNIS' oder dem 'AKTUELLEN GESPRÄCHSVERLAUF' ableiten lassen. **Ignoriere dein internes Wissen, wenn es den bereitgestellten Fakten widerspricht oder diese ergänzt.**

2.  **FAKTEN SYNTHETISIEREN & SCHLUSSFOLGERN (ZENTRALE REGEL):** Deine Hauptaufgabe ist es, bereitgestellte Fakten nicht nur aufzulisten, sondern sie aktiv zu kombinieren und daraus logische Schlussfolgerungen abzuleiten. **Beantworte dabei immer alle Teile der Benutzerfrage.** Es gibt zwei Arten von Schlussfolgerungen:
    - **Logische Deduktion (Sichere Schlüsse):** Dies sind 100% wahre Ableitungen.
        - BEISPIEL: Wenn FAKT A 'Susi ist die Mutter von Klaus' und FAKT B 'Gudrun ist die Schwester von Susi' lauten, lautet die korrekte Antwort auf 'Wer ist Gudrun für mich?' -> 'Gudrun ist die Schwester deiner Mutter Susi und somit deine Tante.'
    - **Plausible Inferenz (Wahrscheinliche Schlüsse):** Dies sind logische Annahmen basierend auf gesundem Menschenverstand. Formuliere diese immer vorsichtig mit "sehr wahrscheinlich", "vermutlich" oder "naheliegend".
        - BEISPIEL: Wenn FAKT A 'Kalle ist Gudruns Mann' und FAKT B 'Kalle wohnt in Köln' lauten, lautet die korrekte Antwort auf 'Wo wohnt Gudrun?' -> 'Da Kalle der Mann von Gudrun ist und in Köln wohnt, ist es sehr wahrscheinlich, dass Gudrun ebenfalls in Köln wohnt.'

3.  **KEINE HALLUZINATIONEN:** Erfinde niemals Fakten, Namen oder Beziehungen. Jede Schlussfolgerung, auch eine wahrscheinliche, muss direkt auf den gegebenen Fakten beruhen.

4.  **WISSENSLÜCKEN ZUGEBEN:** Wenn die Fakten weder eine sichere noch eine wahrscheinliche Schlussfolgerung zulassen, antworte ausschließlich: 'Ich habe dazu keine Informationen in meinen Fakten.'

5.  **AUF AUSSAGEN REAGIEREN:** Wenn die letzte Nutzereingabe offensichtlich nur neue Informationen liefert und keine Frage stellt, antworte mit einer kurzen, freundlichen Bestätigung (z.B. 'Danke, ich habe mir das gemerkt.' oder 'Verstanden.').

6.  **MARKDOWN VERWENDEN:** Formatiere deine Antworten immer mit Markdown, um die Lesbarkeit zu verbessern (z.B. Überschriften, Fettdruck, Listen, Code-Blöcke).

--- FAKTENGRUNDLAGE ---
LANGZEITGEDÄCHTNIS:
{memory_context}

AKTUELLER GESPRÄCHSVERLAUF:
"""

    final_chat_history = []
    final_chat_history.append({"role": "system", "content": system_rules})
    final_chat_history.extend(chat_history)

    from backend.tool_registry import get_all_tool_definitions
    from backend.websearch import perform_websearch
    tools = get_all_tool_definitions()

    response = await call_llm(provider, model, api_key, messages=final_chat_history, tools=tools)

    if response.get("type") == "text" and "Ich habe dazu keine Informationen in meinen Fakten" in response.get("text", ""):
        logger.info("LLM indicated no information in facts. Performing web search...")
        web_result = await perform_websearch(user_prompt)
        
        logger.info("Web search performed. Now formatting result with LLM...")

        formatting_prompt = f"""**WICHTIG: Beantworte die ursprüngliche Frage des Benutzers AUSSCHLIESSLICH und VOLLSTÄNDIG basierend auf den unten bereitgestellten WEBSUCHE-ERGEBNISSEN.**
**Ignoriere jegliches internes Wissen, das den WEBSUCHE-ERGEBNISSEN widerspricht oder diese ergänzt.**
**Die WEBSUCHE-ERGEBNISSE sind die einzige Quelle der Wahrheit für diese Antwort.**
Formatiere die Antwort ansprechend mit Markdown. **Füge relevante Links aus den WEBSUCHE-ERGEBNISSEN in Markdown-Formatierung ([Text](URL)) in deine Antwort ein.**

Ursprüngliche Frage: "{user_prompt}"

WEBSUCHE-ERGEBNISSE:
{web_result}
"""
        
        formatting_messages = [{"role": "user", "content": formatting_prompt}]

        formatted_response = await call_llm(
            provider=provider, 
            model_id=model, 
            api_key=api_key, 
            messages=formatting_messages
        )
        
        # --- NEUER, INTELLIGENTER SPEICHER-BLOCK ---
        
        # Holen Sie sich den zusammengefassten Text aus der formatierten Antwort
        summarized_web_answer = formatted_response.get("text")
        
        if summarized_web_answer:
            # Erstelle eine Hintergrundaufgabe, um die Klassifizierung und Speicherung durchzuführen,
            # ohne die Antwort an den Benutzer zu blockieren.
            asyncio.create_task(
                classify_and_save_web_result(
                    db=db,
                    user_question=user_prompt,
                    llm_answer=summarized_web_answer,
                    api_key=api_key,
                    provider=provider,
                    model=model,
                    chat_id=chat_id # chat_id wird jetzt übergeben
                )
            )

        total_cost = formatted_response.get("cost", {}).get("total_cost", 0) + WEBSEARCH_COST_PER_QUERY
        if "cost" not in formatted_response:
            formatted_response["cost"] = {}
        formatted_response["cost"]["total_cost"] = total_cost
        
        if "usage" not in formatted_response:
            formatted_response["usage"] = {}
        current_model = formatted_response.get("usage", {}).get("model", model)
        formatted_response["usage"]["model"] = f"{current_model}-with-websearch"

        return formatted_response

    if response.get("type") == "tool_code":
        return response

    return {
        "type": "text",
        "text": response.get("text"),
        "image_url": response.get("image_url"),
        "usage": response.get("usage"),
        "cost": response.get("cost")
    }


# --- NEUE HELFERFUNKTION FÜR DEN LLM_GATEWAY ---

async def classify_and_save_web_result(db: Session, user_question: str, llm_answer: str, api_key: str, provider: str, model: str, chat_id: int):
    """
    Klassifiziert eine aus einer Websuche gewonnene Information und speichert sie 
    ggf. als ephemere Erinnerung.
    """
    from backend import memory_manager # Import hier, um Zirkelimporte zu vermeiden
    
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
        # Wir verwenden ein schnelles, günstiges Modell für die Klassifizierung
        classification_model = "gpt-4o-mini" if provider == "openai" else "gemini-1.5-flash-latest"
        
        response = await call_llm(provider, classification_model, api_key, messages)
        decision = response.get("text", "NEIN").strip().upper()

        if "JA" in decision:
            expiration_date = datetime.datetime.now() + datetime.timedelta(days=2) # 48 Stunden Gültigkeit
            logger.info(f"Web result classified as EPHEMERAL. Saving with expiration date. Fact: '{llm_answer[:100]}...'")
            memory_manager.save_memory_snippet(db, chat_id, llm_answer, is_core=False, expires_at=expiration_date)
        else:
            logger.info(f"Web result classified as TIMELESS. Saving as a regular memory. Fact: '{llm_answer[:100]}...'")
            # Wir speichern es als normalen, nicht-essentiellen Fakt, der den normalen Archivierungsprozess durchläuft
            memory_manager.save_memory_snippet(db, chat_id, llm_answer, is_core=False, expires_at=None)

    except Exception as e:
        logger.error(f"Error during web result classification and saving: {e}", exc_info=True)