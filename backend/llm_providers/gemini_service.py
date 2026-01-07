import datetime
import json
import logging
import re # <<< Hinzugefügt
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

import google.generativeai as genai
import sentry_sdk
from google.api_core.exceptions import InvalidArgument, ResourceExhausted
from google.generativeai import protos
from google.generativeai.types import (
    HarmBlockThreshold,
    HarmCategory,
    StopCandidateException,
)
from google.generativeai.types.content_types import to_tool_config
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.llm_providers.base_provider import BaseLLMProvider
from backend.llm_providers.capabilities.gemini_image_generation import GeminiImageGeneration
from backend.llm_providers.capabilities.gemini_multimodal import GeminiMultiModal
from backend.llm_providers.capabilities.gemini_text_generation import GeminiTextGeneration
from backend.llm_providers.capabilities.gemini_web_search import GeminiWebSearch
from backend.services.cost_calculator import calculate_cost

logger = logging.getLogger("janus_backend")


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


def _proto_to_dict(obj: Any) -> Any:
    """Rekursive Konvertierung von Google Protobuf Typen."""
    if hasattr(obj, "items"):
        return {k: _proto_to_dict(v) for k, v in obj.items()}
    elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
        return [_proto_to_dict(v) for v in obj]
    else:
        return obj


class GeminiServiceProvider(BaseLLMProvider):
    def __init__(self):
        self.image_generator = GeminiImageGeneration()
        self.web_search = GeminiWebSearch()
        self.multimodal_generator = GeminiMultiModal()
        self.text_generator = GeminiTextGeneration()

    def _convert_tools_to_gemini_format(
        self, tools: List[Dict]
    ) -> Optional[List[genai.types.Tool]]:
        """
        Konvertiert das interne Tool-Format in das von der Gemini API erwartete Format.
        Diese Funktion ist extrem robust und säubert Pydantic-Schemas aggressiv.
        """
        if not tools:
            return None

        from backend.tool_registry import get_all_tools

        tool_registry = get_all_tools()

        def clean_schema_for_gemini(obj):
            """
            Bereinigt ein Pydantic-Schema-Dictionary rekursiv für Gemini.
            Entfernt aggressiv ALLE Metadaten (default, pattern, etc.), die zu Validierungsfehlern führen.
            Setzt 'nullable': True korrekt um.
            """
            if isinstance(obj, dict):
                # 1. Aggressive Entfernung aller Metadaten, die Gemini verwirren können.
                keys_to_remove = [
                    "title", "default", "format", "pattern", "example", "examples",
                    "uniqueItems", "minItems", "maxItems", "minLength", "maxLength",
                    "exclusiveMinimum", "exclusiveMaximum", "multipleOf", "additionalProperties",
                ]
                for key in keys_to_remove:
                    obj.pop(key, None)

                # 2. 'anyOf' auflösen (für Optional[...])
                if "anyOf" in obj:
                    any_of_list = obj.pop("anyOf")
                    is_nullable = any(item.get("type") == "null" for item in any_of_list)
                    non_null_type = next((item for item in any_of_list if item.get("type") != "null"), None)

                    if non_null_type:
                        obj.update(non_null_type)
                    if is_nullable:
                        obj["nullable"] = True
                    
                    # Rekursiv reinigen, falls der gemergte Typ noch schmutzig ist
                    clean_schema_for_gemini(obj)

                # 3. Rekursion für Properties und Items
                for key, value in list(obj.items()):
                    if isinstance(value, (dict, list)):
                        clean_schema_for_gemini(value)

            elif isinstance(obj, list):
                for item in obj:
                    clean_schema_for_gemini(item)

            # Nach allen Änderungen: Bereinige das 'required'-Array
            if isinstance(obj, dict) and "required" in obj and "properties" in obj:
                obj["required"] = [
                    prop for prop in obj["required"] if prop in obj["properties"]
                ]
                if not obj["required"]:
                    obj.pop("required") # Entferne leeres required-Array

            return obj

        gemini_tools = []
        for tool_def in tools:
            # Greife direkt auf Attribute des Tool-Objekts zu
            func_name = tool_def.name
            description = tool_def.description
            args_schema = tool_def.args_schema

            # Prüfe, ob func_name im Tool-Registry vorhanden ist (was bei Tool-Objekten immer der Fall sein sollte)
            if func_name not in tool_registry:
                logger.warning(f"Tool '{func_name}' from tool_def object not found in tool_registry during conversion. Skipping.")
                continue

            try:
                parameters = {"type": "object", "properties": {}, "required": []}
                if args_schema:
                    schema = args_schema.model_json_schema()
                    cleaned_schema = clean_schema_for_gemini(schema)
                    parameters.update({
                        "properties": cleaned_schema.get("properties", {}),
                        "required": cleaned_schema.get("required", []),
                    })

                function_declaration = genai.types.FunctionDeclaration(
                    name=func_name, description=description or "", parameters=parameters
                )
                gemini_tools.append(function_declaration)

            except Exception as e:
                logger.error(f"Failed to convert tool '{func_name}' for Gemini: {e}", exc_info=True)
                continue

        if gemini_tools:
            return [genai.types.Tool(function_declarations=gemini_tools)]
        else:
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        image_data: Optional[str] = None,
        force_no_tools: bool = False,
        _internal_retry_count: int = 0,
        force_tool_name: Optional[str] = None,  # Hinzugefügt
        **kwargs,
    ) -> Dict:
        genai.configure(api_key=api_key)

        # Standard Safety Settings (nicht zu restriktiv)
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        model_kwargs = {
            "safety_settings": safety_settings,
        }

        # --- TOOL KONFIGURATION ---
        if tools and not force_no_tools:
            gemini_tools = self._convert_tools_to_gemini_format(tools)
            if gemini_tools:
                model_kwargs["tools"] = gemini_tools
                if force_tool_name:
                    model_kwargs["tool_config"] = to_tool_config({
                        "function_calling_config": {
                            "mode": "ANY", # oder "REQUIRED" wenn nur dieses Tool erlaubt ist
                            "allowed_function_names": [force_tool_name]
                        }
                    })
                else:
                    # "auto" ist normalerweise gut, aber bei Problemen kann man "any" erzwingen (Vorsicht)
                    model_kwargs["tool_config"] = to_tool_config({"function_calling_config": {"mode": "auto"}})
        else:
            # Explizit KEINE Tools senden
            model_kwargs.pop("tools", None)
            model_kwargs.pop("tool_config", None)

        # --- SYSTEM PROMPT & HISTORIE ---
        system_instruction = None
        for message in messages:
            if message.get("role") == "system":
                system_instruction = message.get("content")
                break

        history_without_system = [msg for msg in messages if msg.get("role") != "system"]
        gemini_history_for_api = []

        import base64

        # Historie aufbauen
        for message in history_without_system:
            role = "user" if message["role"] == "user" else "model"

            # 1. Text / Bild Nachrichten
            if message["role"] in ["user", "assistant", "model"] and "tool_calls" not in message:
                parts = []
                content = message.get("content")

                if isinstance(content, str):
                    parts.append(content)
                elif isinstance(content, list):
                    for part_data in content:
                        if part_data.get("type") == "text":
                            parts.append(part_data.get("text", ""))

                # Bild anhängen (nur beim letzten User-Prompt relevant für diesen Call)
                if image_data and message == history_without_system[-1]:
                    try:
                        header, encoded = image_data.split(",", 1)
                        mime_type = header.split(":")[1].split(";")[0]
                        image_bytes = base64.b64decode(encoded)
                        parts.append(protos.Part(inline_data=protos.Blob(mime_type=mime_type, data=image_bytes)))
                    except Exception as e:
                        logger.error(f"Image decode error: {e}")

                if parts:
                    gemini_history_for_api.append({"role": role, "parts": parts})

            # 2. Assistant Tool Calls (Historie)
            elif message["role"] in ["assistant", "model"] and "tool_calls" in message:
                tool_calls_proto = []
                for tc in message["tool_calls"]:
                    try:
                        args = json.loads(tc["function"]["arguments"])
                    except:
                        args = {}
                    tool_calls_proto.append(
                        protos.Part(function_call=protos.FunctionCall(name=tc["function"]["name"], args=args))
                    )
                gemini_history_for_api.append({"role": "model", "parts": tool_calls_proto})

            # 3. Tool Results (Antworten auf Calls)
            elif message["role"] == "tool":
                tool_call_id = message.get("tool_call_id")
                function_name = message.get("name")
                
                # Name finden, falls fehlt (Gemini braucht den Namen zwingend)
                if not function_name and tool_call_id:
                    for past_msg in reversed(messages):
                        if "tool_calls" in past_msg:
                            for tc in past_msg["tool_calls"]:
                                if tc.get("id") == tool_call_id:
                                    function_name = tc["function"]["name"]
                                    break
                        if function_name: break
                
                final_name = function_name or "unknown_function"
                
                # Tool Response als 'user' (Gemini Konvention für function_response)
                gemini_history_for_api.append({
                    "role": "user",
                    "parts": [
                        protos.Part(function_response=protos.FunctionResponse(
                            name=final_name, 
                            response={"content": message.get("content")}
                        ))
                    ]
                })

        try:
            gemini_model = genai.GenerativeModel(
                model_name=model, 
                system_instruction=system_instruction
            )
            
            # Timeout etwas erhöhen für Websearch
            request_options = {"timeout": 150} 

            response = await gemini_model.generate_content_async(
                contents=gemini_history_for_api, 
                request_options=request_options, 
                **model_kwargs
            )

            # --- FEHLERBEHANDLUNG & RETRY LOGIK ---
            
            # Sicherheitsfilter checken
            if response.prompt_feedback.block_reason:
                return {"type": "error", "message": f"Blockiert: {response.prompt_feedback.block_reason.name}"}

            if not response.candidates:
                return {"type": "text", "text": "Keine Antwort vom Modell erhalten."}

            first_candidate = response.candidates[0]
            finish_reason = getattr(first_candidate, "finish_reason", 0)

            # SPEZIAL-BEHANDLUNG FÜR TOOL-ABSTÜRZE (Reason 10)
            if finish_reason == 10:
                logger.warning(f"Gemini Tool Error (Reason 10). Retry: {_internal_retry_count}")
                
                # Sentry Info (ohne Crash)
                sentry_sdk.capture_message(f"Gemini Reason 10 (Retry {_internal_retry_count})", level="warning")

                # Strategie: Wir versuchen es NOCHMAL MIT TOOLS.
                # Oft ist Reason 10 ein temporäres Problem oder Kontext-Problem.
                # Wir geben dem Modell bis zu 2 Chancen, das Tool richtig zu nutzen.
                if _internal_retry_count < 2:
                    logger.info("Retrying WITH tools...")
                    return await self.generate_response(
                        api_key=api_key, model=model, messages=messages, tools=tools,
                        image_data=image_data, force_no_tools=False, # Weiterhin Tools erlauben!
                        _internal_retry_count=_internal_retry_count + 1,
                        **kwargs
                    )
                else:
                    # Letzter Ausweg: Ohne Tools, damit User wenigstens Text kriegt.
                    logger.warning("Giving up on tools. Fallback to text.")
                    return await self.generate_response(
                        api_key=api_key, model=model, messages=messages, 
                        tools=None, force_no_tools=True, # Hier schalten wir ab
                        _internal_retry_count=_internal_retry_count + 1,
                        **kwargs
                    )

            # --- ERGEBNIS VERARBEITUNG ---
            
            all_gateway_tool_calls = []
            text_accumulated = ""

            if not first_candidate.content.parts:
                 return {"type": "text", "text": "Leere Antwort erhalten (Fehler bei Verarbeitung)."}

            for part in first_candidate.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    # Wenn es ein Funktionsaufruf ist, behandle ihn
                    fc = part.function_call
                    tool_args = _proto_to_dict(fc.args) or {}
                    
                    all_gateway_tool_calls.append({
                        "id": f"call_{fc.name}_{datetime.datetime.now().timestamp()}",
                        "type": "function",
                        "function": {"name": fc.name, "arguments": json.dumps(tool_args)}
                    })
                elif hasattr(part, "text") and part.text:
                    # Wenn es reiner Text ist und kein Funktionsaufruf, akkumuliere ihn
                    text_accumulated += part.text

            usage_metadata = response.usage_metadata
            usage, cost = _calculate_and_log_cost(
                model,
                {
                    "prompt_tokens": getattr(usage_metadata, "prompt_token_count", 0),
                    "completion_tokens": getattr(usage_metadata, "candidates_token_count", 0),
                },
            )

            if all_gateway_tool_calls:
                parts_for_raw_assistant = []
                # Füge immer einen Text-Part hinzu, auch wenn er leer ist, um thought_signature zu erfüllen
                parts_for_raw_assistant.append(protos.Part(text=text_accumulated if text_accumulated else ""))
                
                # Füge die Tool Calls hinzu
                for tc in all_gateway_tool_calls:
                    parts_for_raw_assistant.append(
                        protos.Part(function_call=protos.FunctionCall(
                            name=tc["function"]["name"], 
                            args=json.loads(tc["function"]["arguments"]) # args muss als Dict übergeben werden
                        ))
                    )

                return {
                    "type": "tool_code",
                    "tool_calls": all_gateway_tool_calls,
                    "usage": usage,
                    "cost": cost,
                    "raw_assistant_response": {
                        "role": "model", # Wichtig: "model" statt "assistant" hier
                        "parts": parts_for_raw_assistant # Verwende die neue Struktur
                    }
                }
            else:
                return {"type": "text", "text": text_accumulated, "usage": usage, "cost": cost}

        except Exception as e:
            logger.error(f"Gemini Exception: {e}", exc_info=True)
            return {"type": "error", "message": f"Fehler: {str(e)}"}

    async def generate_structured_response(self, api_key, model, messages, response_format, **kwargs):
        # Implementierung für JSON Mode (z.B. für Memory Extraction)
        # Nutzen wir hier die einfache Prompting-Methode, da Gemini JSON Mode zickig sein kann
        json_schema = response_format.model_json_schema()
        prompt_suffix = f"\n\nANTWORTE AUSSCHLIESSLICH IM JSON-FORMAT. SCHEMA:\n{json.dumps(json_schema)}"
        
        # System-Prompt anpassen oder anhängen
        mod_messages = list(messages)
        mod_messages.append({"role": "user", "content": "Generiere die strukturierte Antwort jetzt." + prompt_suffix})
        
        resp = await self.generate_response(api_key, model, mod_messages, force_no_tools=True, **kwargs)
        
        if resp["type"] == "text":
            try:
                # Regex, um den JSON-Block zu finden (auch wenn unerwünschter Text davor/danach steht)
                json_match = re.search(r"```json\s*(\{.*?\})\s*```", resp["text"], re.DOTALL)
                if json_match:
                    clean_json = json_match.group(1)
                else:
                    # Fallback: Versuchen, den gesamten Text als JSON zu parsen, wenn kein Code-Block gefunden wird
                    clean_json = resp["text"].strip()
                    # Zusätzliche Bereinigungen, falls Gemini doch etwas anderes als ```json``` liefert
                    clean_json = clean_json.replace("```json", "").replace("```", "").strip()

                return response_format.model_validate_json(clean_json), resp.get("cost", {})
            except Exception as e:
                logger.error(f"JSON Parse Error in generate_structured_response: {e}", exc_info=True)
                raise
        # Wenn der response-Typ nicht "text" ist, ist es ein Fehler
        raise ValueError("Keine Textantwort für Structured Output erhalten")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_image(self, api_key, model, prompt, image_bytes_list=None, **kwargs):
        return await self.image_generator.generate_image(
            api_key=api_key, model=model, prompt=prompt, image_bytes_list=image_bytes_list, **kwargs
        )
        
    def prepare_history_for_second_call(self, chat_history, raw_assistant_response, tool_results):
        # Gemini braucht die Ergebnisse in der Historie
        return chat_history + [raw_assistant_response] + tool_results