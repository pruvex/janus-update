import logging
from typing import List, Dict, Optional
import openai
import google.generativeai as genai
from backend.cost_calculator import calculate_cost
from sqlalchemy.orm import Session # Import Session
from backend import crud, vector_service # Import crud

logger = logging.getLogger('janus_backend')

async def call_llm(provider: str, model: str, prompt: str, api_key: str, chat_history: Optional[List[Dict]] = None):
    """
    Haupt-Gateway-Funktion, die Anfragen an den entsprechenden API-Provider weiterleitet.
    Der 'prompt' Parameter wird ignoriert, da der eigentliche Inhalt in 'chat_history' liegt.
    """
    if not chat_history:
        chat_history = [{"role": "user", "content": prompt}]

    if provider == "openai":
        return await _call_openai_api(api_key, model, chat_history)
    elif provider == "gemini":
        return await _call_gemini_api(api_key, model, chat_history)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

async def _call_openai_api(api_key: str, model_id: str, chat_history: List[Dict]):
    client = openai.AsyncOpenAI(api_key=api_key)
    is_image_model = "dall-e" in model_id.lower()

    if is_image_model:
        final_prompt = chat_history[-1]['content']
        response = await client.images.generate(
            model=model_id,
            prompt=final_prompt,
            n=1,
            size="1024x1024",
            quality="standard"
        )
        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt
        usage, cost = calculate_cost(model_id, custom_prompt=revised_prompt)
        return {"text": revised_prompt, "image_url": image_url, "usage": usage, "cost": cost}
    else:
        response = await client.chat.completions.create(
            model=model_id,
            messages=chat_history
        )
        text_response = response.choices[0].message.content
        usage, cost = calculate_cost(model_id, usage_data=response.usage)
        return {"text": text_response, "image_url": None, "usage": usage, "cost": cost}

async def _call_gemini_api(api_key: str, model_id: str, chat_history: List[Dict]):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_id)
    
    gemini_history = []
    system_message_content = ""

    for msg in chat_history:
        if msg['role'] == 'system':
            system_message_content += msg['content'] + "\n"
        elif msg['role'] == 'user':
            gemini_history.append({'role': 'user', 'parts': [msg['content']]})
        elif msg['role'] == 'assistant':
            gemini_history.append({'role': 'model', 'parts': [msg['content']]})

    # Prepend system message content to the first user message
    if system_message_content and gemini_history and gemini_history[0]['role'] == 'user':
        gemini_history[0]['parts'][0] = system_message_content + gemini_history[0]['parts'][0]
    elif system_message_content and not gemini_history:
        # If only a system message exists, create a dummy user message to carry it
        gemini_history.append({'role': 'user', 'parts': [system_message_content]})

    response = await model.generate_content_async(gemini_history)
    
    text_response = response.text
    usage, cost = {}, {} # Platzhalter
    return {"text": text_response, "image_url": None, "usage": usage, "cost": cost}

async def expand_query(query: str, api_key: str) -> str:
    """
    Erweitert eine Benutzeranfrage um Synonyme und verwandte Konzepte,
    um die semantische Suche im Gedächtnis zu verbessern.
    """
    try:
        prompt = (
            "Du bist ein Assistent für Query Expansion. Deine Aufgabe ist es, eine Benutzerfrage "
            "in eine Liste von Schlüsselkonzepten und Synonymen umzuwandeln, die für eine Datenbanksuche nützlich sind. "
            "Gib nur die Schlüsselwörter und Konzepte zurück, getrennt durch Leerzeichen.\n\n"
            f"Beispiel 1:\nFrage: was isst meine mutter gerne?\nAntwort: essen mutterfrau vorlieben lieblingsessen\n\n"
            f"Beispiel 2:\nFrage: wer ist mit franz verheiratet?\nAntwort: franz frau ehefrau ehepartner\n\n"
            f"Frage: {query}\n"
            "Antwort:"
        )
        history = [{"role": "user", "content": prompt}]
        response = await _call_openai_api(api_key, "gpt-4o-mini", history)
        expanded_terms = response.get("text", "").strip()
        return f"{query} {expanded_terms}"
    except Exception as e:
        logger.error(f"Fehler bei der Query Expansion: {e}")
        return query

async def deconstruct_query_for_memory(query: str, api_key: str) -> List[str]:
    """
    Zerlegt eine komplexe Frage in einfache, suchbare Unterfragen.
    """
    prompt = f"Zerlege die folgende Benutzerfrage in eine Liste von einfachen Schlüsselbegriff-Suchen für eine Datenbank. Jede Suche sollte in einer neuen Zeile stehen.\nFrage: {query}\n\nSuchen:"
    history = [{"role": "user", "content": prompt}]
    response = await _call_openai_api(api_key, "gpt-4o-mini", history)
    return response['text'].split('\n')

async def resolve_contradictions(facts: str, api_key: str) -> str:
    """
    Überprüft eine Liste von Fakten auf Widersprüche und fasst sie zusammen.
    """
    prompt = f"""Hier sind einige Fakten aus einer Datenbank. Fasse sie zu einer kohärenten, widerspruchsfreien Aussage zusammen. Ignoriere veraltete Informationen, wenn eine neuere Korrektur vorhanden ist.

Fakten:
{facts}

Zusammenfassung:"""
    history = [{"role": "user", "content": prompt}]
    response = await _call_openai_api(api_key, "gpt-4o-mini", history)
    return response['text']

async def reason_about_context(user_prompt: str, context_snippets: List[str], api_key: str) -> str:
    """
    Ein dedizierter LLM-Aufruf, der aus verstreuten Fakten eine logische,
    widerspruchsfreie Zusammenfassung erstellt, um eine komplexe Frage zu beantworten.
    """
    if not context_snippets:
        return "Ich habe keine Informationen zu diesem Thema in meinem Gedächtnis."
    facts = "\n".join(f"- {s}" for s in context_snippets)
    prompt = f"""Du bist ein Logik-Assistent. Deine Aufgabe ist es, aus den folgenden Fakten eine präzise und widerspruchsfreie Antwort auf die Frage des Benutzers zu formulieren. Leite, wenn nötig, logische Schlussfolgerungen ab (z.B. wenn A die Schwester von B ist und B die Frau von C, dann ist A die Schwägerin von C).

--- FAKTEN AUS DEM GEDÄCHTNIS ---
{facts}

--- FRAGE DES BENUTZERS ---
{user_prompt}

--- FINALE ANTWORT ---"""
    history = [{"role": "user", "content": prompt}]
    # Wir verwenden ein leistungsstarkes Modell für diese Aufgabe
    response = await _call_openai_api(api_key, "gpt-4o-mini", history)
    return response.get("text", "Ich konnte keine Antwort finden.")

async def reason_and_respond(user_prompt: str, chat_history: List[Dict], memory_context: str, db: Session, api_key: str, model: str, provider: str) -> str:
    logger.info(f"reason_and_respond: user_prompt={user_prompt}")
    logger.info(f"reason_and_respond: chat_history={chat_history}")
    logger.info(f"reason_and_respond: memory_context={memory_context}")
    """
    Der zentrale "Denk"-Schritt, der alle Informationen zusammenführt und eine kohärente Antwort generiert.
    """
    full_context = ""
    if memory_context:
        full_context += f"""--- RELEVANTE ERINNERUNGEN ---
{memory_context}\n"""
    
    # Füge den bisherigen Chat-Verlauf hinzu
    if chat_history:
        full_context += f"""--- CHAT VERLAUF ---
"""
        for msg in chat_history:
            full_context += f"{msg['role']}: {msg['content']}\n"
        full_context += "\n"

    # NEU: Cross-Chat-Memory mit Vektor-Suche
    cross_chat_keywords = ["andere chats", "frühere gespräche", "worüber haben wir gesprochen", "andere unterhaltungen"]
    if any(keyword in user_prompt.lower() for keyword in cross_chat_keywords):
        all_chats = crud.get_chats(db, include_archived=True) # Alle Chats laden
        similar_chats = vector_service.find_similar_chat_summaries(user_prompt, all_chats)
        if similar_chats:
            full_context += f"""--- ZUSAMMENFASSUNGEN ANDERER CHATS ---
"""
            for chat in similar_chats:
                full_context += f"Chat ID: {chat.id}, Titel: {chat.title}\n"
                full_context += f"Zusammenfassung: {chat.summary}\n\n"
            full_context += "\n"

    prompt = f"""Du bist ein intelligenter Assistent. Deine Aufgabe ist es, die Frage des Benutzers zu beantworten. Nutze dabei alle relevanten Informationen aus den bereitgestellten Erinnerungen und dem Chat-Verlauf. Formuliere eine präzise, hilfreiche und kohärente Antwort.

{full_context}
--- AKTUELLE BENUTZERANFRAGE ---
{user_prompt}

--- ANTWORT ---"""

    history = [{"role": "user", "content": prompt}]
    response = await call_llm(provider, model, prompt, api_key, chat_history=history) # Corrected call
    return response.get("text", "Es tut mir leid, ich konnte keine Antwort finden.")

async def summarize_chat_topic(chat_history: List[Dict], api_key: str, provider: str, model: str) -> str:
    """
    Erstellt eine prägnante Zusammenfassung eines Chats.
    """
    prompt = (
        "Du bist ein Assistent zur Chat-Zusammenfassung. Deine Aufgabe ist es, aus dem folgenden Chatverlauf "
        "ein kurzes, prägnantes Thema oder eine Zusammenfassung in einem Satz zu generieren. "
        "Diese Zusammenfassung wird als Titel für den Chat verwendet. Antworte nur mit dem Titel."
        "\n\n--- Chatverlauf ---"
    )
    history = [{"role": "user", "content": prompt}]
    history.extend(chat_history)

    response = await call_llm(provider, model, prompt, api_key, chat_history=history)
    return response.get("text", "Unbenannter Chat").strip()
