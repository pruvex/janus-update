import logging
from typing import List, Dict, Optional
import openai
import google.generativeai as genai
import json
from io import BytesIO
from PIL import Image
import os
import uuid
from backend.cost_calculator import calculate_cost, MODEL_PRICES
from sqlalchemy.orm import Session
from backend import crud, vector_service
from backend.context_manager import ContextManager
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger('janus_backend')
IMAGE_DIR = os.path.join(get_app_data_dir(), "images")

def _calculate_and_log_cost(model_id, usage_data=None, custom_prompt=None):
    """Calculates cost, logs it, and returns usage and cost."""
    usage, cost = calculate_cost(model_id, usage_data, custom_prompt)
    
    logger.info(f"\n--- USAGE TRACKING ---\n" \
                f"Model: {model_id}\n" \
                f"Input Tokens: {usage.get('input_tokens', 'N/A')}\n" \
                f"Output Tokens: {usage.get('output_tokens', 'N/A')}\n" \
                f"Image Quality: {usage.get('image_quality', 'N/A')}\n" \
                f"Image Size: {usage.get('image_size', 'N/A')}\n" \
                f"Total Cost: {cost.get('total_cost', 0):.8f} €\n" \
                f"----------------------")
    return usage, cost

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
        return await _call_gemini_api(api_key, model_id, prompt, chat_history, model_info)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

async def _call_openai_api(api_key: str, model_id: str, chat_history: List[Dict], model_info: Dict):
    client = openai.AsyncOpenAI(api_key=api_key)
    is_image_model = model_info.get("type") == "image"

    if is_image_model:
        final_prompt = chat_history[-1]['content']
        
        quality = model_info.get("quality", "standard")
        size = model_info.get("size", "1024x1024")

        response = await client.images.generate(
            model=model_id,
            prompt=final_prompt,
            n=1,
            size=size,
            quality=quality
        )
        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt
        usage, cost = _calculate_and_log_cost(model_id, custom_prompt=revised_prompt)
        return {"text": text_response, "image_url": image_url, "usage": usage, "cost": cost}
    else:
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

        response = await client.chat.completions.create(
            model=model_id,
            messages=chat_history,
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            # Return tool call information to main.py for execution
            for tool_call in tool_calls:
                if tool_call.function.name == "generate_image_tool": # Only handle this specific tool for now
                    function_args = json.loads(tool_call.function.arguments)
                    return {"type": "tool_code", "tool_name": tool_call.function.name, "tool_args": function_args}
            # If other tool calls are detected but not handled, fall through to text response
            text_response = response.choices[0].message.content
            usage, cost = _calculate_and_log_cost(model_id, usage_data=response.usage)
            return {"type": "text", "text": text_response, "image_url": None, "usage": usage, "cost": cost}
        else:
            text_response = response.choices[0].message.content
            usage, cost = _calculate_and_log_cost(model_id, usage_data=response.usage)
            return {"type": "text", "text": text_response, "image_url": None, "usage": usage, "cost": cost}

async def _call_gemini_api(api_key: str, model_id: str, user_prompt: str, chat_history: List[Dict], model_info: Dict):
    genai.configure(api_key=api_key)
    
    # Existing text generation logic
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

    if system_message_content and gemini_history and gemini_history[0]['role'] == 'user':
        gemini_history[0]['parts'][0] = system_message_content + gemini_history[0]['parts'][0]
    elif system_message_content and not gemini_history:
        gemini_history.append({'role': 'user', 'parts': [system_message_content]})

    response = await model.generate_content_async(gemini_history)
    
    text_response = response.text

    input_tokens_count = model.count_tokens(gemini_history).total_tokens
    output_tokens_count = model.count_tokens([{"role": "model", "parts": [text_response]}]).total_tokens

    usage_data = {"prompt_tokens": input_tokens_count, "completion_tokens": output_tokens_count}
    usage, cost = _calculate_and_log_cost(model_id, usage_data=usage_data)

    return {"type": "text", "text": text_response, "image_url": None, "usage": usage, "cost": cost}


async def _call_gemini_image_generation_api(api_key: str, model_id: str, prompt: str):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_id)
    
    try:
        logger.info(f"_call_gemini_image_generation_api: Calling model '{model_id}' with prompt: '{prompt}'")
        response = await model.generate_content_async(prompt)
        
        image_data = None
        text_response = ""
        
        for part in response.candidates[0].content.parts:
            if part.text:
                text_response += part.text
                logger.info(f"_call_gemini_image_generation_api: Detected text part: '{part.text}'")
            elif part.inline_data:
                image_data = part.inline_data.data
                logger.info(f"_call_gemini_image_generation_api: Detected image data.")
                break

        image_url = None
        if image_data:
            file_name = str(uuid.uuid4()) + ".png"
            file_path = os.path.join(IMAGE_DIR, file_name)
            with open(file_path, 'wb') as f:
                f.write(image_data)
            image_url = f"/user_images/{file_name}"
            text_response = "" # Clear text response if image is generated
            logger.info(f"_call_gemini_image_generation_api: Image saved to {file_path}")

        usage, cost = _calculate_and_log_cost(model_id)
        logger.debug(f"_call_gemini_image_generation_api: Returning image_url: {image_url}")
        return {"text": text_response, "image_url": image_url, "usage": usage, "cost": cost}
    except Exception as e:
        logger.error(f"Error generating image with Gemini: {e}")
        return {"text": f"Error generating image: {e}", "image_url": None, "usage": {}, "cost": {}}



async def generate_image_tool(api_key: str, prompt: str, size: str = "1024x1024", quality: str = "standard", response_format: str = "url"):
    client = openai.AsyncOpenAI(api_key=api_key)
    try:
        response = await client.images.generate(
            model="dall-e-3", # <--- SO SOLLTE ES AUSSEHEN
            prompt=prompt,
            n=1,
            size=size,
            quality=quality,
            response_format=response_format
        )
        
        cost_model_id = "dall-e-3-hd" if quality == "hd" else "dall-e-3-standard"
        image_usage, image_cost_data = _calculate_and_log_cost(
            model_id=cost_model_id,
            usage_data={"image_quality": quality, "image_size": size}
        )

        result = {"created": response.created}
        if response_format == "url":
            result["url"] = response.data[0].url
        elif response_format == "b64_json":
            result["b64_json"] = response.data[0].b64_json
        
        result["usage"] = image_usage
        result["cost"] = image_cost_data
        return result
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

async def reason_and_respond(user_prompt: str, chat_history: List[Dict], memory_context: str, db: Session, api_key: str, model: str, provider: str, context_manager: ContextManager) -> Dict:
    logger.info(f"reason_and_respond: user_prompt={user_prompt}")
    logger.info(f"reason_and_respond: chat_history={chat_history}")
    logger.info(f"reason_and_respond: memory_context={memory_context}")
    """
    Der zentrale "Denk"-Schritt, der alle Informationen zusammenführt und eine kohärente Antwort generiert.
    Kann auch Tool-Aufrufe zurückgeben.
    """
    # Define budget configuration for ContextManager
    budget_config = {
        "system_prompt_ratio": 0.1,
        "memory_ratio": 0.3,
        "chat_history_ratio": 0.5,
    }
    
    # Integrate Cross-Chat-Memory into memory_context
    cross_chat_memory_snippets = []
    cross_chat_keywords = ["andere chats", "frühere gespräche", "worüber haben wir gesprochen", "andere unterhaltungen"]
    if any(keyword in user_prompt.lower() for keyword in cross_chat_keywords):
        all_chats = crud.get_chats(db, include_archived=True) # Alle Chats laden
        similar_chats = vector_service.find_similar_chat_summaries(user_prompt, all_chats)
        if similar_chats:
            cross_chat_memory_snippets.append("--- ZUSAMMENFASSUNGEN ANDERER CHATS ---")
            for chat in similar_chats:
                cross_chat_memory_snippets.append(f"Chat ID: {chat.id}, Titel: {chat.title}")
                cross_chat_memory_snippets.append(f"Zusammenfassung: {chat.summary}")
            cross_chat_memory_snippets.append("") # Add a newline for separation
    
    if cross_chat_memory_snippets:
        if memory_context:
            memory_context = memory_context + "\n" + "\n".join(cross_chat_memory_snippets)
        else:
            memory_context = "\n".join(cross_chat_memory_snippets)

    # Use the ContextManager to build the final context
    final_history = await context_manager.build_final_context(
        user_prompt=user_prompt,
        chat_history=chat_history,
        memory_context=memory_context,
        model_id=model,
        api_key=api_key,
        budget_config=budget_config,
        provider=provider
    )

    response = await call_llm(provider, model, user_prompt, api_key, chat_history=final_history)

    # If the response from call_llm is a tool code, return it directly
    if response.get("type") == "tool_code":
        return response
    
    # Otherwise, process as a text response
    return {"type": "text", "text": response.get("text"), "image_url": response.get("image_url"), "usage": response.get("usage"), "cost": response.get("cost")}

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