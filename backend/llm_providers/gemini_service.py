# VOLLSTÄNDIGER, FINALER UND GETESTETER INHALT FÜR: backend/llm_providers/gemini_service.py

import logging
import re
import datetime
import json
from typing import List, Dict, Optional
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InvalidArgument
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.services.cost_calculator import calculate_cost
from backend.llm_providers.base_provider import BaseLLMProvider
from backend.llm_providers.capabilities.gemini_image_generation import (
    GeminiImageGeneration,
)
from backend.llm_providers.capabilities.gemini_web_search import GeminiWebSearch
from backend.llm_providers.capabilities.gemini_multimodal import GeminiMultiModal
from backend.llm_providers.capabilities.gemini_text_generation import (
    GeminiTextGeneration,
)

logger = logging.getLogger("janus_backend")


def _extract_image_description(prompt: str) -> str:
    """Extracts a concise, filename-safe description from the user's prompt."""
    prompt = re.sub(
        r"\b(zeichne|male|erstelle|generiere|create|draw|generate|ein bild von)\b",
        "",
        prompt,
        flags=re.IGNORECASE,
    )
    safe_prompt = re.sub(r"[^a-zA-Z0-9\s-]", "", prompt).strip()
    filename = safe_prompt.replace(" ", "-").lower()[:50]
    return filename or "generated-image"


def _calculate_and_log_cost(model_id, usage_data=None, custom_prompt=None):
    """Berechnet die Kosten und gibt sie im Log aus."""
    usage, cost = calculate_cost(model_id, usage_data, custom_prompt)
    logger.info(
        f"\n--- USAGE TRACKING ---\n"
        f"Model: {model_id}\n"
        f"Input Tokens: {usage.get('input_tokens', 'N/A')}\n"
        f"Output Tokens: {usage.get('output_tokens', 'N/A')}\n"
        f"Image Quality: {usage.get('image_quality', 'N/A')}\n"
        f"Image Size: {usage.get('image_size', 'N/A')}\n"
        f"Total Cost: {cost.get('total_cost', 0):.8f} €\n"
        f"----------------------"
    )
    return usage, cost


class GeminiServiceProvider(BaseLLMProvider):
    def __init__(self):
        self.image_generator = GeminiImageGeneration()
        self.web_search = GeminiWebSearch()
        self.multimodal_generator = GeminiMultiModal()
        self.text_generator = GeminiTextGeneration()

    def _convert_tools_to_gemini_format(
        self,
        tools: List[Dict]
    ) -> Optional[List[genai.types.Tool]]:
        """
        Konvertiert das interne Tool-Format in das von der Gemini API erwartete Format.
        Behebt insbesondere das Kompatibilitätsproblem mit Pydantic's 'Optional' Feldern (anyOf).
        """
        if not tools:
            return None

        from backend.tool_registry import get_all_tools

        tool_registry = get_all_tools()

        gemini_tools = []
        for tool_def in tools:
            func_name = tool_def.get("function", {}).get("name")
            if func_name in tool_registry:
                schema = tool_registry[func_name].args_schema.model_json_schema()

                properties = schema.get("properties", {})

                # --- NEU: Schema-Bereinigung ---
                # Diese Schleife behebt das 'anyOf'-Problem für optionale Felder.
                for prop_name, prop_details in properties.items():
                    if "anyOf" in prop_details:
                        # Finde den Nicht-Null-Typ in der 'anyOf'-Liste
                        non_null_type = next(
                            (
                                t
                                for t in prop_details["anyOf"]
                                if t.get("type") != "null"
                            ),
                            None,
                        )
                        if non_null_type:
                            # Ersetze die 'anyOf'-Struktur durch eine einfache Typdefinition
                            new_prop = non_null_type
                            # Behalte wichtige Metadaten wie die Beschreibung bei
                            if "description" in prop_details:
                                new_prop["description"] = prop_details["description"]
                            properties[prop_name] = new_prop
                # --- ENDE: Schema-Bereinigung ---

                # --- START: HINZUGEFÜGTE LÖSUNG ---
                # Diese Schleife entfernt das inkompatible 'default'-Feld aus allen Parametern.
                for prop in properties.values():
                    prop.pop("default", None) 
                # --- ENDE: HINZUGEFÜGTE LÖSUNG ---

                for prop in properties.values():
                    prop.pop("title", None)

                function_declaration = genai.types.FunctionDeclaration(
                    name=func_name,
                    description=tool_def.get("function", {}).get("description", ""),
                    parameters={
                        "type": "object",
                        "properties": properties,
                        "required": schema.get("required", []),
                    },
                )
                gemini_tools.append(function_declaration)

        return (
            [genai.types.Tool(function_declarations=gemini_tools)]
            if gemini_tools
            else None
        )

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        image_data: Optional[str] = None,
        is_image_analysis_request: bool = False,
        **kwargs,
    ) -> Dict:
        genai.configure(api_key=api_key)

        system_instruction = None
        gemini_history_for_api = []

        # --- START: NEUER, KORRIGIERTER CODE ---
        gemini_history_for_api = []
        last_message = None 
        
        import base64

        for i, message in enumerate(messages):
            role = "user" if message["role"] == "user" else "model"
            
            if message.get("role") == "system":
                system_instruction = message.get("content")
                continue

            # Fall 1: Standard User/Assistant Nachricht ohne Tool-Bezug
            if message["role"] in ["user", "assistant", "model"] and "tool_calls" not in message:
                content = message.get("content")
                parts = []
                
                text_content = ""
                if isinstance(content, str):
                    text_content = content
                elif isinstance(content, list):
                    for part_data in content:
                        if part_data.get("type") == "text":
                            text_content = part_data.get("text", "")
                
                if text_content:
                    parts.append(text_content)

                if role == "user" and i == len(messages) - 1 and image_data:
                    try:
                        header, encoded = image_data.split(",", 1)
                        mime_type = header.split(":")[1].split(";")[0]
                        image_bytes = base64.b64decode(encoded)
                        parts.append(genai.protos.Part(inline_data=genai.protos.Blob(mime_type=mime_type, data=image_bytes)))
                        logger.info("Successfully added image data to the Gemini request parts.")
                    except Exception as e:
                        logger.error(f"Error processing image data URI for Gemini: {e}", exc_info=True)
                        return {"type": "text", "text": f"Fehler bei der Verarbeitung der Bilddaten: {e}"}

                if parts:
                    gemini_history_for_api.append({"role": role, "parts": parts})

            # Fall 2: Die Antwort des Assistenten, die den Tool-Aufruf enthält
            elif message["role"] in ["assistant", "model"] and "tool_calls" in message:
                 tool_call = message["tool_calls"][0]
                 gemini_history_for_api.append({'role': 'model', 'parts': [genai.protos.Part(function_call=
                     genai.protos.FunctionCall(name=tool_call["function"]["name"], args=json.loads(tool_call["function"]["arguments"])))]})

            # Fall 3: Die "tool" Nachricht, die das Ergebnis enthält (NEU!)
            elif message["role"] == "tool":
                tool_name = message.get("name")
                tool_content = message.get("content")
                gemini_history_for_api.append({'role': 'user', 'parts': [genai.protos.Part(function_response=
                    genai.protos.FunctionResponse(name=tool_name, response={"content": tool_content}))]})

            last_message = message

        gemini_tools = self._convert_tools_to_gemini_format(tools)
        
        # KORREKTUR: Initialisiere model_kwargs IMMER als leeres Dictionary
        model_kwargs = {}
        
        # Fülle es nur, wenn Werkzeuge vorhanden sind
        if gemini_tools:
            model_kwargs["tools"] = gemini_tools

        try:
            if (
                is_image_analysis_request
            ):  # NEU: Vereinfachte Initialisierung für Bildanalyse
                logger.info(
                    "Initializing Gemini model for pure image analysis (no system instruction, no tools)."
                )
                genai_model = genai.GenerativeModel(model_name=model)
            else:
                genai_model = genai.GenerativeModel(
                    model_name=model,
                    system_instruction=system_instruction,
                    **model_kwargs
                )
        except Exception as e:
            logger.error(f"Error initializing Gemini model: {e}", exc_info=True)
            return {
                "type": "text",
                "text": f"Fehler bei der Initialisierung des Modells: {e}",
            }

        try:
            usage_metadata = None
            history = gemini_history_for_api
            content_to_send = []  # Initialize as list

            # If the last message in the original prompt was a tool response,
            # it should remain in the history. We send a neutral continuation prompt
            # because the API does not allow empty content.
            if messages and messages[-1].get("role") == "tool":
                content_to_send = " "
            # Otherwise, the last message is a standard user query.
            # We pop it from the history and use its content for the `send_message_async` call.
            elif history:
                last_message = history.pop()
                content_to_send = last_message["parts"]

            # A fallback to ensure content is never empty, preventing an API error.
            if not content_to_send:
                logger.warning(
                    "Content to send to Gemini was empty. This can happen with an empty initial prompt. Sending a space as a fallback."
                )
                content_to_send = " "

            chat = genai_model.start_chat(history=history)
            response = await chat.send_message_async(content_to_send, **model_kwargs)

            if not response.candidates:
                logger.warning(
                    f"Gemini returned no candidates, possibly due to safety filters or an empty prompt. History: {gemini_history_for_api}"
                )
                return {
                    "type": "text",
                    "text": "Ich konnte keine passende Antwort generieren. Möglicherweise wurde sie durch einen Sicherheitsfilter blockiert.",
                }

            first_candidate = response.candidates[0]

            if not first_candidate.content.parts:
                finish_reason = first_candidate.finish_reason.name
                safety_ratings = [
                    str(rating) for rating in first_candidate.safety_ratings
                ]
                error_message = f"Gemini response was blocked. Reason: {finish_reason}. Safety Ratings: {safety_ratings}"
                logger.warning(error_message)
                return {
                    "type": "text",
                    "text": "Meine Antwort wurde aufgrund von Sicherheitsrichtlinien blockiert. Bitte formuliere die Anfrage anders.",
                }

            first_part = first_candidate.content.parts[0]

            if hasattr(first_part, "function_call") and first_part.function_call:
                tool_call = first_part.function_call
                tool_name = tool_call.name
                tool_args = {key: value for key, value in tool_call.args.items()}
                logger.info(f"Gemini requested tool call: {tool_name} with args: {tool_args}")
                logger.debug(f"Gemini tool_call.args: {tool_call.args}")

                # 1. Erstelle die rohe Assistenten-Nachricht, die der OpenAI-Struktur entspricht.
                # WICHTIG: Die tool_call.id wird hier künstlich erzeugt, da Gemini keine stabile ID liefert.
                # Für den zweistufigen Prozess ist das aber ausreichend.
                raw_assistant_response_for_gateway = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": f"call_{tool_name}_{datetime.datetime.now().timestamp()}",
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(tool_args),
                            },
                        }
                    ],
                }

                usage_metadata = response.usage_metadata
                if usage_metadata:
                    usage, cost = _calculate_and_log_cost(
                        model,
                        {
                            "prompt_tokens": usage_metadata.prompt_token_count,
                            "completion_tokens": usage_metadata.candidates_token_count,
                        },
                    )
                else:
                    usage, cost = {},
                # 2. Füge das neue Feld zur Rückgabe hinzu.
                return {
                    "type": "tool_code",
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "usage": usage,
                    "cost": cost,
                    "raw_assistant_response": raw_assistant_response_for_gateway, # <-- DAS IST DIE WICHTIGE ERGÄNZUNG
                }
            else:
                text_response = "".join(
                    part.text
                    for part in first_candidate.content.parts
                    if hasattr(part, "text")
                )
                usage_metadata = response.usage_metadata
                if usage_metadata:
                    usage, cost = _calculate_and_log_cost(
                        model,
                        {
                            "prompt_tokens": usage_metadata.prompt_token_count,
                            "completion_tokens": usage_metadata.candidates_token_count,
                        },
                    )
                else:
                    usage, cost = {},
                return {
                    "type": "text",
                    "text": text_response,
                    "usage": usage,
                    "cost": cost,
                }

        except (ResourceExhausted, InvalidArgument) as e:
            logger.error(f"API Error with Gemini: {e}", exc_info=True)
            return {"type": "text", "text": f"API-Fehler bei Gemini: {e}"}
        except Exception as e:
            if "response.candidates is empty" in str(e):
                logger.warning(
                    f"Gemini returned no candidates, possibly due to safety filters or an empty prompt. History: {gemini_history_for_api}"
                )
                return {
                    "type": "text",
                    "text": "Ich konnte keine passende Antwort generieren. Möglicherweise wurde sie durch einen Sicherheitsfilter blockiert.",
                }
            logger.error(
                f"An unexpected error occurred with Gemini SDK: {e}", exc_info=True
            )
            return {
                "type": "text",
                "text": f"Ein unerwarteter Fehler ist aufgetreten: {e}",
            }

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_image(
        self,
        api_key: str,
        model: str,
        prompt: str,
        reference_image_path: Optional[str] = None,
        **kwargs,
    ) -> Dict:
        return await self.image_generator.generate_image(
            api_key, model, prompt, reference_image_path=reference_image_path, **kwargs
        )
