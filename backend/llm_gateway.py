import logging
from typing import List, Dict, Optional
import openai
import google.generativeai as genai
import json
from backend.cost_calculator import calculate_cost, MODEL_PRICES
from sqlalchemy.orm import Session # Import Session
from backend import crud, vector_service # Import crud

logger = logging.getLogger('janus_backend')

async def call_llm(provider: str, model_id: str, prompt: str, api_key: str, chat_history: Optional[List[Dict]] = None):
    """
    Haupt-Gateway-Funktion, die Anfragen an den entsprechenden API-Provider weiterleitet.
    Der 'prompt' Parameter wird ignoriert, da der eigentliche Inhalt in 'chat_history' liegt.
    """
    if not chat_history:
        chat_history = [{"role": "user", "content": prompt}]

    model_info = MODEL_PRICES.get(model_id)
    if not model_info:
        raise ValueError(f"Model {model_id} not found in model catalog.")

    if provider == "openai":
        return await _call_openai_api(api_key, model_id, chat_history, model_info)
    elif provider == "gemini":
        return await _call_gemini_api(api_key, model_id, chat_history)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

async def _call_openai_api(api_key: str, model_id: str, chat_history: List[Dict], model_info: Dict):
    client = openai.AsyncOpenAI(api_key=api_key)
    is_image_model = model_info.get("type") == "image"

    if is_image_model:
        final_prompt = chat_history[-1]['content']
        
        # Extract quality and size from model_info
        quality = model_info.get("quality", "standard")
        size = model_info.get("size", "1024x1024")

        response = await client.images.generate(
            model="dall-e-3", # Always use dall-e-3 as the model name
            prompt=final_prompt,
            n=1,
            size=size,
            quality=quality
        )
        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt
        usage, cost = calculate_cost(model_id, custom_prompt=revised_prompt)
        return {"text": revised_prompt, "image_url": image_url, "usage": usage, "cost": cost}
    else:
        # Define the tool for image generation
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "generate_image_tool",
                    "description": "Generates an image based on a text prompt using DALL-E 3.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "A detailed text description of the image to generate."
                            },
                            "size": {
                                "type": "string",
                                "enum": ["1024x1024", "1792x1024", "1024x1792"],
                                "description": "The size of the generated image. Defaults to 1024x1024."
                            },
                            "quality": {
                                "type": "string",
                                "enum": ["standard", "hd"],
                                "description": "The quality of the generated image. Defaults to standard."
                            },
                            "response_format": {
                                "type": "string",
                                "enum": ["url", "b64_json"],
                                "description": "The format of the response, either a URL or base64 encoded JSON. Defaults to url."
                            }
                        },
                        "required": ["prompt"]
                    }
                }
            }
        ]

        # First LLM call with tool definition
        response = await client.chat.completions.create(
            model=model_id,
            messages=chat_history,
            tools=tools,
            tool_choice="auto" # Allow the model to choose to call a tool
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            # Extend chat history with the model's tool call message
            chat_history.append(response_message)

            # Execute each tool call
            for tool_call in tool_calls:
                if tool_call.function.name == "generate_image_tool":
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the tool function
                    tool_output = await generate_image_tool(
                        api_key=api_key,
                        prompt=function_args.get("prompt"),
                        size=function_args.get("size", "1024x1024"),
                        quality=function_args.get("quality", "standard"),
                        response_format=function_args.get("response_format", "url")
                    )
                    
                    # Add tool output to chat history
                    chat_history.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": tool_call.function.name,
                            "content": json.dumps(tool_output),
                        }
                    )
            
            # Second LLM call with tool output
            second_response = await client.chat.completions.create(
                model=model_id,
                messages=chat_history
            )
            text_response = second_response.choices[0].message.content
            
            # Check if the tool output contains an image URL
            image_url = None
            if tool_output and "url" in tool_output:
                image_url = tool_output["url"]
            elif tool_output and "b64_json" in tool_output:
                # Handle base64 image if needed, for now, we'll just pass the text
                pass

            usage, cost = calculate_cost(model_id, usage_data=response.usage) # Use usage from first call
            return {"text": text_response, "image_url": image_url, "usage": usage, "cost": cost}
        else:
            # No tool call, just a regular text response
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

    # Manuelle Token-Zählung für Gemini
    input_tokens_count = model.count_tokens(gemini_history).total_tokens
    output_tokens_count = model.count_tokens([{"role": "model", "parts": [text_response]}]).total_tokens

    usage_data = {"prompt_tokens": input_tokens_count, "completion_tokens": output_tokens_count}
    usage, cost = calculate_cost(model_id, usage_data=usage_data)

    return {"text": text_response, "image_url": None, "usage": usage, "cost": cost}

async def generate_image_tool(api_key: str, prompt: str, size: str = "1024x1024", quality: str = "standard", response_format: str = "url"):
    client = openai.AsyncOpenAI(api_key=api_key)
    try:
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size=size,
            quality=quality,
            response_format=response_format
        )
        if response_format == "url":
            return {"url": response.data[0].url, "created": response.created}
        elif response_format == "b64_json":
            return {"b64_json": response.data[0].b64_json, "created": response.created}
    except Exception as e:
        logger.error(f"Error generating image with tool: {e}")
        return {"error": str(e)}

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

    system_prompt = f"""Du bist ein intelligenter Assistent. Deine Aufgabe ist es, die Frage des Benutzers zu beantworten. Nutze dabei alle relevanten Informationen aus den bereitgestellten Erinnerungen und dem Chat-Verlauf. Formuliere eine präzise, hilfreiche und kohärente Antwort.

{full_context}
--- ANTWORT ---"""

    history = [{"role": "system", "content": system_prompt}]
    history.extend(chat_history)
    history.append({"role": "user", "content": user_prompt})

    response = await call_llm(provider, model, "", api_key, chat_history=history)
    return response

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
    return {"text": response.get("text", "Unbenannter Chat").strip(), "usage": response.get("usage"), "cost": response.get("cost")}
