# VOLLSTÄNDIGER, FINALER UND KORRIGIERTER INHALT FÜR: backend/llm_providers/gemini_service.py

import datetime
import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

import google.generativeai as genai
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
    """Rekursive Konvertierung von Google Protobuf Typen (RepeatedComposite, MapComposite) in native Python Typen."""
    if hasattr(obj, "items"):  # MapComposite oder Dict
        return {k: _proto_to_dict(v) for k, v in obj.items()}
    elif hasattr(obj, "__iter__") and not isinstance(
        obj, (str, bytes)
    ):  # RepeatedComposite oder List
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

        # --- START GOLDSTANDARD-FIX FÜR GEMINI-TOOL-KONVERTIERUNG V3.0 (AGGRESSIVE CLEANUP) ---
        def clean_schema_for_gemini(obj):
            """
            Bereinigt ein Pydantic-Schema-Dictionary rekursiv für Gemini.
            Entfernt aggressiv ALLE Metadaten (default, pattern, etc.), die zu Validierungsfehlern führen.
            Setzt 'nullable': True korrekt um.
            """
            if isinstance(obj, dict):
                # 1. Aggressive Entfernung aller Metadaten, die Gemini verwirren können.
                # 'default' ist besonders wichtig zu entfernen, da Gemini sonst oft stolpert.
                keys_to_remove = [
                    "title",
                    "default",
                    "format",
                    "pattern",
                    "example",
                    "examples",
                    "uniqueItems",
                    "minItems",
                    "maxItems",
                    "minLength",
                    "maxLength",
                    "exclusiveMinimum",
                    "exclusiveMaximum",
                    "multipleOf",
                    "additionalProperties",
                ]
                for key in keys_to_remove:
                    obj.pop(key, None)

                # 2. 'anyOf' auflösen (für Optional[...])
                if "anyOf" in obj:
                    any_of_list = obj["anyOf"]
                    is_nullable = False
                    non_null_type = None

                    for item in any_of_list:
                        if item.get("type") == "null":
                            is_nullable = True
                        else:
                            # Wir nehmen den ersten echten Typen
                            non_null_type = item

                    # 'anyOf' entfernen
                    obj.pop("anyOf")

                    if non_null_type:
                        # Den eigentlichen Typ in das aktuelle Objekt mergen
                        obj.update(non_null_type)

                    # Nullable explizit setzen
                    if is_nullable:
                        obj["nullable"] = True

                    # Rekursiv reinigen (wichtig, falls der gemergte Typ noch schmutzig ist)
                    clean_schema_for_gemini(obj)

                # 3. 'allOf' auflösen (selten, aber sicher ist sicher)
                if "allOf" in obj:
                    first_type = obj["allOf"][0] if obj["allOf"] else {}
                    obj.pop("allOf")
                    obj.update(first_type)
                    clean_schema_for_gemini(obj)

                # 4. Rekursion für Properties und Items
                for key, value in list(obj.items()):
                    if isinstance(value, (dict, list)):
                        clean_schema_for_gemini(value)

            elif isinstance(obj, list):
                for item in obj:
                    clean_schema_for_gemini(item)

            return obj

        # --- ENDE GOLDSTANDARD-FIX V3.0 ---

        gemini_tools = []
        for tool_def in tools:
            func_name = tool_def.get("function", {}).get("name")
            if func_name not in tool_registry:
                continue

            logger.info(f"Converting tool to Gemini format: {func_name}")

            try:
                tool_obj = tool_registry[func_name]
                parameters = {"type": "object", "properties": {}, "required": []}

                if tool_obj.args_schema:
                    # Generiere das Schema und reinige es sofort und aggressiv
                    schema = tool_obj.args_schema.model_json_schema()
                    cleaned_schema = clean_schema_for_gemini(schema)
                    parameters.update(
                        {
                            "properties": cleaned_schema.get("properties", {}),
                            "required": cleaned_schema.get("required", []),
                        }
                    )

                function_declaration = genai.types.FunctionDeclaration(
                    name=func_name, description=tool_obj.description or "", parameters=parameters
                )
                gemini_tools.append(function_declaration)

            except Exception as e:
                logger.error(f"Failed to convert tool '{func_name}' for Gemini: {e}", exc_info=True)
                continue

        return [genai.types.Tool(function_declarations=gemini_tools)] if gemini_tools else None

    # ... Der Rest der Datei bleibt unverändert ...
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        image_data: Optional[str] = None,
        force_no_tools: bool = False,
        **kwargs,
    ) -> Dict:
        genai.configure(api_key=api_key)

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        model_kwargs = {
            "safety_settings": safety_settings,
        }

        if tools and not force_no_tools:
            gemini_tools = self._convert_tools_to_gemini_format(tools)
            if gemini_tools:
                model_kwargs["tools"] = gemini_tools
                tool_config = to_tool_config({"function_calling_config": {"mode": "auto"}})
                model_kwargs["tool_config"] = tool_config
        else:
            model_kwargs["tool_config"] = to_tool_config(
                {"function_calling_config": {"mode": "none"}}
            )

        system_instruction = None
        gemini_history_for_api = []

        import base64

        # --- START GOLDSTANDARD-FIX V2: "Kontext-Erhaltungs"-Strategie für Gemini ---
        # Diese Strategie formatiert den gesamten von der Orchestrierung übergebenen
        # Verlauf für Gemini, ohne ihn zu kürzen. Dies stellt sicher, dass der
        # volle Konversationskontext erhalten bleibt, was für mehrstufige Aufgaben
        # und kontextbezogene Anfragen entscheidend ist.

        # 1. Extrahiere die Systemanweisung, da sie separat übergeben wird.
        for message in messages:
            if message.get("role") == "system":
                system_instruction = message.get("content")
                break

        # 2. Filtere die Systemanweisung aus dem Verlauf, um Duplikate zu vermeiden.
        history_without_system_prompt = [msg for msg in messages if msg.get("role") != "system"]

        # 3. Baue die vollständige, aber saubere Historie für die API auf.
        for message in history_without_system_prompt:
            role = "user" if message["role"] == "user" else "model"

            # Normale Text- oder Assistenten-Nachrichten (ohne Tool-Calls)
            if message["role"] in ["user", "assistant", "model"] and "tool_calls" not in message:
                parts = []
                content = message.get("content")

                # Verarbeite einfachen Text oder eine Liste von Inhaltsteilen
                if isinstance(content, str):
                    parts.append(content)
                elif isinstance(content, list):
                    for part_data in content:
                        if part_data.get("type") == "text":
                            parts.append(part_data.get("text", ""))

                # Füge Bilddaten hinzu, wenn sie für diese spezifische Nachricht relevant sind
                if image_data and message == history_without_system_prompt[-1]:
                    try:
                        header, encoded = image_data.split(",", 1)
                        mime_type = header.split(":")[1].split(";")[0]
                        image_bytes = base64.b64decode(encoded)
                        parts.append(
                            protos.Part(
                                inline_data=protos.Blob(mime_type=mime_type, data=image_bytes)
                            )
                        )
                    except Exception as e:
                        logger.error(
                            f"Error processing image data URI for Gemini: {e}", exc_info=True
                        )
                        return {
                            "type": "text",
                            "text": f"Fehler bei der Verarbeitung der Bilddaten: {e}",
                        }

                if parts:
                    gemini_history_for_api.append({"role": role, "parts": parts})

            # Assistenten-Nachrichten, die Tool-Calls enthalten
            elif message["role"] in ["assistant", "model"] and "tool_calls" in message:
                tool_calls_proto = [
                    protos.Part(
                        function_call=protos.FunctionCall(
                            name=tc["function"]["name"],
                            args=json.loads(tc["function"]["arguments"]),
                        )
                    )
                    for tc in message["tool_calls"]
                ]
                gemini_history_for_api.append({"role": "model", "parts": tool_calls_proto})

            # Tool-Antworten
            elif message["role"] == "tool":
                # CRITICAL FIX: Gemini benötigt zwingend den Funktionsnamen (z.B. 'get_latest_emails'),
                # nicht die tool_call_id (z.B. 'call_123').

                tool_call_id = message.get("tool_call_id")
                function_name = message.get("name")

                # Wenn der Name im Tool-Message-Objekt fehlt, rekonstruieren wir ihn aus der Historie
                if not function_name and tool_call_id:
                    # Wir suchen rückwärts durch die bisherigen Nachrichten
                    # (reversed, um den jüngsten passenden Aufruf zuerst zu finden)
                    for past_msg in reversed(messages):
                        if past_msg.get("role") == "assistant" and "tool_calls" in past_msg:
                            for tc in past_msg["tool_calls"]:
                                if tc.get("id") == tool_call_id:
                                    function_name = tc["function"]["name"]
                                    break
                        if function_name:
                            break

                # Fallback: Wenn wir trotz Suche nichts finden, nehmen wir die ID (besser als nichts)
                final_name = function_name or tool_call_id

                # Das 'user'-Rollback für Tool-Antworten ist spezifisch für die Gemini API Struktur
                gemini_history_for_api.append(
                    {
                        "role": "user",
                        "parts": [
                            protos.Part(
                                function_response=protos.FunctionResponse(
                                    name=final_name, response={"content": message.get("content")}
                                )
                            )
                        ],
                    }
                )
        # --- ENDE GOLDSTANDARD-FIX V2 ---

        try:
            gemini_model = genai.GenerativeModel(
                model_name=model, system_instruction=system_instruction
            )
            request_options = {"timeout": 130}

            generation_config = {}
            if "thinking_level" in kwargs:
                generation_config["thinkingConfig"] = {"thinkingLevel": kwargs["thinking_level"]}
            if "media_resolution" in kwargs:
                generation_config["mediaResolution"] = {"level": kwargs["media_resolution"]}
            
            if generation_config:
                model_kwargs["generation_config"] = generation_config


            response = await gemini_model.generate_content_async(
                contents=gemini_history_for_api, request_options=request_options, **model_kwargs
            )

            if response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason.name
                logger.error(f"Gemini response blocked due to prompt. Reason: {block_reason}")
                return {
                    "type": "error",
                    "message": f"Die Anfrage wurde vom Sicherheitsfilter blockiert: {block_reason}",
                }

            if not response.candidates:
                logger.warning(f"Gemini returned no candidates. History: {gemini_history_for_api}")
                return {
                    "type": "text",
                    "text": "Ich konnte keine passende Antwort generieren (Keine Kandidaten).",
                }

            first_candidate = response.candidates[0]

            finish_reason_obj = getattr(first_candidate, "finish_reason", None)
            logger.info(f"Gemini Finish Reason: {finish_reason_obj}")

            if finish_reason_obj == 2:  # protos.FinishReason.SAFETY
                safety_ratings = [
                    str(rating) for rating in getattr(first_candidate, "safety_ratings", [])
                ]
                logger.warning(
                    f"Gemini response blocked. Reason: SAFETY. Ratings: {safety_ratings}"
                )
                return {
                    "type": "text",
                    "text": "Meine Antwort wurde aufgrund von Sicherheitsrichtlinien blockiert.",
                }

            if not first_candidate.content.parts:
                logger.warning(f"Gemini response has no parts. Finish Reason: {finish_reason_obj}")
                return {
                    "type": "text",
                    "text": "Ich habe die Daten verarbeitet, aber die KI hat eine leere Antwort zurückgegeben.",
                }

            # --- GOLDSTANDARD FIX: PARALLEL FUNCTION CALLING ---
            # Wir sammeln ALLE Function Calls aus ALLEN Parts, nicht nur dem ersten.
            all_gateway_tool_calls = []
            text_accumulated = ""

            for part in first_candidate.content.parts:
                logger.debug(f"Gemini response part: {part}") # NEU
                # 1. Text-Parts sammeln
                if hasattr(part, "text") and part.text:
                    text_accumulated += part.text

                # 2. Function-Calls sammeln
                # Prüfe explizit auf function_call und image Parts
                function_call = None
                if hasattr(part, "function_call"):
                    function_call = part.function_call
                
                # Image parts for multimodal input/output are not directly handled as tool_calls here
                # but rather by other parts of the generate_response logic or context building.
                # However, for the purpose of ensuring a tool call is identified correctly,
                # we focus on the function_call attribute.

                if function_call:
                    tool_name = function_call.name
                    logger.info(f"Gemini triggered a function call in part: {tool_name}")

                    try:
                        # Versuche, args als Dictionary zu interpretieren, falls es nicht schon eins ist
                        tool_args = _proto_to_dict(function_call.args)
                        if tool_args is None:
                            tool_args = {}
                    except Exception as e:
                        logger.error(f"Error converting tool args for {tool_name}: {e}")
                        tool_args = {}

                    all_gateway_tool_calls.append(
                        {
                            "id": f"call_{tool_name}_{datetime.datetime.now().timestamp()}_{len(all_gateway_tool_calls)}",
                            "type": "function",
                            "function": {"name": tool_name, "arguments": json.dumps(tool_args)},
                        }
                    )

            usage_metadata = response.usage_metadata
            usage, cost = _calculate_and_log_cost(
                model,
                {
                    "prompt_tokens": getattr(usage_metadata, "prompt_token_count", 0),
                    "completion_tokens": getattr(usage_metadata, "candidates_token_count", 0),
                },
            )

            # Entscheidung: Haben wir Tool Calls gefunden?
            if all_gateway_tool_calls:
                logger.info(f"Gemini returned {len(all_gateway_tool_calls)} tool calls.")

                raw_assistant_response_for_gateway = {
                    "role": "assistant",
                    "content": text_accumulated
                    if text_accumulated
                    else None,  # Gemini kann Text UND Tools senden
                    "tool_calls": all_gateway_tool_calls,
                }

                return {
                    "type": "tool_code",
                    "tool_calls": all_gateway_tool_calls,
                    "usage": usage,
                    "cost": cost,
                    "raw_assistant_response": raw_assistant_response_for_gateway,
                }
            else:
                # Nur Textantwort
                return {"type": "text", "text": text_accumulated, "usage": usage, "cost": cost}

        except (InvalidArgument, ResourceExhausted) as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            return {"type": "error", "message": f"Gemini API Fehler: {str(e)}"}
        except StopCandidateException as e:
            logger.warning(f"Gemini StopCandidateException: {e}")
            return {"type": "text", "text": f"Die Antwort wurde vorzeitig beendet: {e}"}
        except Exception as e:
            logger.error(f"Unexpected error during Gemini call: {e}", exc_info=True)
            return {"type": "error", "message": f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}"}

    async def generate_structured_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict],
        response_format: BaseModel,
        **kwargs,
    ) -> tuple[BaseModel, Dict]:
        """
        Generiert eine strukturierte JSON-Antwort basierend auf einem Pydantic-Modell.
        Diese Funktion ist spezifisch für Gemini und nutzt einen Prompt-basierten Ansatz.
        """
        try:
            # 1. Erstelle das JSON-Schema aus dem Pydantic-Modell
            json_schema = response_format.model_json_schema()

            # 2. Erstelle eine spezifische Systemanweisung
            json_instruction = (
                "Deine Aufgabe ist es, die Anfrage des Benutzers zu analysieren und "
                "deine Antwort ausschließlich und exakt im folgenden JSON-Format zurückzugeben. "
                "Gib nichts anderes als das JSON-Objekt aus. Kein einleitender Text, keine Erklärungen, "
                "keine Code-Block-Markierungen (```json). Nur das reine JSON.\n\n"
                f"JSON-Schema:\n{json.dumps(json_schema, indent=2)}"
            )

            # 3. Bereite die Nachrichtenliste vor
            modified_messages = messages.copy()
            # Füge die Anweisung am Anfang ein, damit sie als System-Prompt wirkt
            modified_messages.insert(0, {"role": "system", "content": json_instruction})

            # 4. Normale Response generieren (Tools deaktiviert!)
            response = await self.generate_response(
                api_key=api_key,
                model=model,
                messages=modified_messages,
                force_no_tools=True,
                **kwargs
            )

            # 5. Ergebnis parsen
            if response["type"] == "text":
                text_content = response["text"]
                # Entferne Markdown-Code-Blöcke, falls das Modell sie trotzdem sendet
                cleaned_text = text_content.replace("```json", "").replace("```", "").strip()
                parsed_obj = response_format.model_validate_json(cleaned_text)
                
                # Kosten aus der normalen Response extrahieren
                cost_data = response.get("cost", {})
                
                # RÜCKGABE: Tuple (Parsed Object, Cost Data)
                return parsed_obj, cost_data
            
            elif response["type"] == "error":
                raise ValueError(f"Gemini Error: {response.get('message')}")
            else:
                raise ValueError(f"Unexpected response type from Gemini: {response['type']}")

        except Exception as e:
            logger.error(f"Error in generate_structured_response (Gemini): {e}", exc_info=True)
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_image(
        self,
        api_key: str,
        model: str,
        prompt: str,
        image_bytes_list: list = None,
        **kwargs,
    ) -> Dict:
        """
        Routes the image generation request to the GeminiImageGeneration class.
        """
        return await self.image_generator.generate_image(
            api_key=api_key,
            model=model,
            prompt=prompt,
            image_bytes_list=image_bytes_list,
            **kwargs
        )
        
    def prepare_history_for_second_call(
        self,
        chat_history: List[Dict],
        raw_assistant_response: Dict,
        tool_results: List[Dict]
    ) -> List[Dict]:
        """
        Bereitet die Chat-Historie für den Folgeaufruf nach einer Tool-Ausführung vor.
        
        Für Gemini hängen wir die Ergebnisse an und fügen eine explizite
        Benutzeraufforderung hinzu, damit das Modell die Ergebnisse verarbeitet
        und eine finale Antwort formuliert.
        
        Args:
            chat_history: Die bisherige Chat-Historie
            raw_assistant_response: Die rohe Antwort des Assistenten mit dem Tool-Aufruf
            tool_results: Die Ergebnisse der Tool-Ausführung(en)
            
        Returns:
            Die vorbereitete Chat-Historie für den nächsten Aufruf
        """
        # Füge die Antwort des Assistenten und die Tool-Ergebnisse zur Historie hinzu
        new_history = chat_history + [raw_assistant_response] + tool_results
        
        # Füge eine explizite Aufforderung als User hinzu
        trigger_message = {
            "role": "user",
            "content": (
                "Die Werkzeuge wurden erfolgreich ausgeführt und die Ergebnisse liegen oben vor (siehe 'tool' messages). "
                "Bitte analysiere diese Ergebnisse jetzt und formuliere basierend darauf deine endgültige Antwort an mich."
            ),
        }
        new_history.append(trigger_message)
        
        return new_history
