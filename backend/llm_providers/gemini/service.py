import datetime
import json
import logging
import copy
import re # <<< Hinzugefügt
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import google.generativeai as genai
import sentry_sdk
from google.generativeai import protos
from google.generativeai.types import (
    HarmBlockThreshold,
    HarmCategory,
)
from google.generativeai.types.content_types import to_tool_config
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.llm_providers.shared.base_provider import BaseLLMProvider
from .capabilities.image_generation import GeminiImageGeneration
from .capabilities.multimodal import GeminiMultiModal
from .capabilities.text_generation import GeminiTextGeneration
from .web_search import GeminiWebSearch
from backend.services.cost_calculator import calculate_cost
from backend.services.orchestrator.stream_protocol import StreamEvent

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

    def _resolve_local_json_ref(self, schema_root: Dict[str, Any], ref: str) -> Dict[str, Any]:
        if not isinstance(ref, str) or not ref.startswith("#/"):
            raise ValueError(f"Unsupported JSON ref: {ref}")

        current: Any = schema_root
        for token in ref[2:].split("/"):
            key = token.replace("~1", "/").replace("~0", "~")
            if not isinstance(current, dict) or key not in current:
                raise ValueError(f"Unresolvable JSON ref: {ref}")
            current = current[key]

        if not isinstance(current, dict):
            raise ValueError(f"Resolved JSON ref is not an object: {ref}")
        return copy.deepcopy(current)

    def _resolve_schema_refs(self, raw_schema: Dict[str, Any]) -> Dict[str, Any]:
        schema_root = copy.deepcopy(raw_schema or {})

        def _walk(node: Any, depth: int = 0, seen_refs: Optional[List[str]] = None) -> Any:
            if depth > 30:
                raise ValueError("Schema reference depth limit exceeded")
            if seen_refs is None:
                seen_refs = []

            if isinstance(node, list):
                return [_walk(item, depth + 1, seen_refs) for item in node]

            if not isinstance(node, dict):
                return node

            if "$ref" in node:
                ref = node.get("$ref")
                if ref in seen_refs:
                    raise ValueError(f"Circular JSON ref detected: {ref}")

                resolved = self._resolve_local_json_ref(schema_root, ref)
                sibling_overrides = {k: v for k, v in node.items() if k != "$ref"}
                merged = {**resolved, **sibling_overrides}
                return _walk(merged, depth + 1, seen_refs + [ref])

            cleaned = {}
            for key, value in node.items():
                if key in {"$defs", "definitions"}:
                    continue
                cleaned[key] = _walk(value, depth + 1, seen_refs)
            return cleaned

        return _walk(schema_root)

    def _clean_gemini_schema(self, obj: Any) -> Any:
        if not isinstance(obj, dict):
            if isinstance(obj, list):
                return [self._clean_gemini_schema(i) for i in obj]
            return obj

        forbidden = [
            "title",
            "default",
            "anyOf",
            "allOf",
            "oneOf",
            "pattern",
            "format",
            "minLength",
            "maxLength",
            "minimum",
            "maximum",
            "exclusiveMinimum",
            "exclusiveMaximum",
            "multipleOf",
            "minItems",
            "maxItems",
            "uniqueItems",
            "minProperties",
            "maxProperties",
            "examples",
            "description_internal",
            "$defs",
            "definitions",
            "$ref",
        ]
        new_obj = {k: self._clean_gemini_schema(v) for k, v in obj.items() if k not in forbidden}

        if "anyOf" in obj or "oneOf" in obj:
            options = obj.get("anyOf") or obj.get("oneOf")
            valid_types = [t for t in options if isinstance(t, dict) and t.get("type") != "null"]
            if valid_types:
                new_obj.update(self._clean_gemini_schema(valid_types[0]))
        if "const" in obj:
            new_obj["enum"] = [obj["const"]]
            if "const" in new_obj:
                del new_obj["const"]

        if "properties" in new_obj and "required" in new_obj:
            valid_properties = set(new_obj["properties"].keys())
            synced_required = [req for req in new_obj["required"] if req in valid_properties]
            if synced_required:
                new_obj["required"] = synced_required
            else:
                del new_obj["required"]

        return new_obj

    def _sanitize_tool_schema(self, raw_schema: Dict[str, Any]) -> Dict[str, Any]:
        resolved_schema = self._resolve_schema_refs(raw_schema)
        final_schema = self._clean_gemini_schema(resolved_schema)

        if not isinstance(final_schema, dict):
            raise ValueError("Sanitized schema is not an object")

        if final_schema.get("type") != "object":
            final_schema["type"] = "object"
        if not isinstance(final_schema.get("properties"), dict):
            final_schema["properties"] = {}

        return final_schema

    def _recursive_remove_additional_properties(self, schema: Any) -> Any:
        if isinstance(schema, dict):
            return {
                key: self._recursive_remove_additional_properties(value)
                for key, value in schema.items()
                if key != "additionalProperties"
            }
        if isinstance(schema, list):
            return [self._recursive_remove_additional_properties(item) for item in schema]
        return schema

    @staticmethod
    def _sanitize_gemini_name(name: str) -> str:
        """Sanitize a tool/function name for Gemini API compatibility.
        Gemini requires: alphanumeric (a-z, A-Z, 0-9) or underscores (_) only."""
        if not name or not isinstance(name, str) or name == "None":
            return "unknown_tool"
        safe = name.replace(".", "_").replace("-", "_")
        # Strip any remaining non-alphanumeric/underscore chars
        safe = re.sub(r'[^a-zA-Z0-9_]', '_', safe)
        return safe or "unknown_tool"

    def _convert_tools_to_gemini_format(self, tools: List[Any]) -> List[Any]:
        gemini_tools = []
        seen_names = set()  # Track seen function names to prevent duplicates
        for tool in tools:
            try:
                # Unwrap OpenAI-format dicts: {"type": "function", "function": {"name": ..., ...}}
                func_def = None
                if isinstance(tool, dict) and "function" in tool and isinstance(tool["function"], dict):
                    func_def = tool["function"]
                
                if func_def:
                    name = func_def.get("name")
                    desc = func_def.get("description", "")
                    raw_schema = func_def.get("parameters", {"type": "object", "properties": {}})
                else:
                    name = getattr(tool, "name", tool.get("name") if isinstance(tool, dict) else "unknown")
                    desc = getattr(tool, "description", tool.get("description") if isinstance(tool, dict) else "")
                    raw_schema = {"type": "object", "properties": {}}
                    if isinstance(tool, dict) and isinstance(tool.get("parameters"), dict):
                        raw_schema = tool.get("parameters")
                
                args_schema_model = getattr(tool, "args_schema", None) if not func_def else None
                if args_schema_model:
                    if hasattr(args_schema_model, "model_json_schema"):
                        try:
                            raw_schema = args_schema_model.model_json_schema(mode="serialization")
                        except TypeError:
                            raw_schema = args_schema_model.model_json_schema()
                    elif hasattr(args_schema_model, "schema"):
                        raw_schema = args_schema_model.schema()

                # Sanitize name for Gemini (dots/hyphens -> underscores)
                safe_name = self._sanitize_gemini_name(name)
                if name != safe_name:
                    logger.info("[GEMINI-SANITIZE] Tool name '%s' -> '%s'", name, safe_name)
                
                # Sanitize description
                if not desc or not isinstance(desc, str) or desc == "None":
                    desc = f"Tool {safe_name}"
                
                # Skip duplicate tool names to prevent Gemini ValueError
                if safe_name in seen_names:
                    logger.debug("Gemini: Skipping duplicate tool name '%s'", safe_name)
                    continue
                seen_names.add(safe_name)

                raw_schema_clean = self._recursive_remove_additional_properties(raw_schema)
                try:
                    final_schema = self._sanitize_tool_schema(raw_schema_clean)
                except Exception as schema_exc:
                    logger.warning(
                        "Gemini schema sanitization failed for tool '%s': %s. Falling back to empty object schema.",
                        safe_name,
                        schema_exc,
                    )
                    final_schema = {"type": "object", "properties": {}}

                gemini_tools.append({
                    "function_declarations": [{
                        "name": safe_name,
                        "description": desc,
                        "parameters": final_schema
                    }]
                })
            except Exception as e:
                logger.error(f"Gemini Konvertierungs-Fehler: {e}")
                continue
        return gemini_tools

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
        # Sicherstellen, dass kwargs ein valides Dict ist
        kwargs = kwargs or {}
        
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
                    safe_force_name = self._sanitize_gemini_name(force_tool_name)
                    model_kwargs["tool_config"] = to_tool_config({
                        "function_calling_config": {
                            "mode": "ANY",
                            "allowed_function_names": [safe_force_name]
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
        system_instruction_parts = []
        for message in messages:
            if message.get("role") != "system":
                continue
            content = str(message.get("content") or "").strip()
            if content:
                system_instruction_parts.append(content)
        system_instruction = "\n\n".join(system_instruction_parts) if system_instruction_parts else None

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
                raw_parts = message.get("_gemini_raw_model_parts")
                n_tc = len(message.get("tool_calls") or [])
                if (
                    isinstance(raw_parts, list)
                    and len(raw_parts) > 0
                    and n_tc > 0
                    and len(raw_parts) >= n_tc
                ):
                    try:
                        gemini_history_for_api.append({"role": "model", "parts": list(raw_parts)})
                        logger.info(
                            "GEMINI-HISTORY (sync): Stream-Model-Parts übernommen (%d parts, %d tool_calls).",
                            len(raw_parts),
                            n_tc,
                        )
                        continue
                    except Exception as raw_exc:
                        logger.warning("GEMINI-HISTORY (sync): Raw-Parts Fallback: %s", raw_exc)
                tool_calls_proto = []
                for tc in message["tool_calls"]:
                    try:
                        args = json.loads(tc["function"]["arguments"])
                    except:
                        args = {}
                    tc_name = self._sanitize_gemini_name(tc["function"]["name"])
                    tool_calls_proto.append(
                        protos.Part(function_call=protos.FunctionCall(name=tc_name, args=args))
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
                
                final_name = self._sanitize_gemini_name(function_name or "unknown_function")

                # Gemini expects ``function_response.response`` to be a structured
                # dict. Parse the JSON envelope so Gemini sees the real payload and
                # does not loop by re-calling the tool.
                raw_content = message.get("content")
                if isinstance(raw_content, dict):
                    parsed_response = raw_content
                else:
                    try:
                        parsed_response = json.loads(str(raw_content))
                        if not isinstance(parsed_response, dict):
                            parsed_response = {"content": parsed_response}
                    except Exception:
                        parsed_response = {"content": str(raw_content) if raw_content is not None else ""}

                # Tool Response als 'user' (Gemini Konvention für function_response)
                gemini_history_for_api.append({
                    "role": "user",
                    "parts": [
                        protos.Part(function_response=protos.FunctionResponse(
                            name=final_name,
                            response=parsed_response,
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

            if "tools" in model_kwargs:
                model_kwargs["tools"] = self._recursive_remove_additional_properties(model_kwargs["tools"])

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
                fallback_path = "tool_retry_then_text_fallback"
                logger.warning(
                    "Gemini Tool Error (Reason 10). attempt=%s fallback_path=%s strategy=tool_retry_then_text_fallback",
                    _internal_retry_count,
                    fallback_path,
                )
                
                # Sentry Info (ohne Crash)
                sentry_sdk.capture_message(f"Gemini Reason 10 (Retry {_internal_retry_count})", level="warning")

                # Strategie: maximal ein Retry mit Tools, danach genau ein Text-Only-Fallback.
                # Wenn selbst der Text-Only-Aufruf wieder Reason 10 liefert, stoppen wir hart
                # (kein rekursiver Retry-Loop, keine attempt=2/3 Log-Spam).
                if force_no_tools:
                    logger.warning(
                        "Gemini Reason 10 persists in text-only mode. fallback_path=deterministic_text_deny"
                    )
                    return {
                        "type": "text",
                        "text": (
                            "Ich konnte gerade keine stabile Modellantwort erzeugen. "
                            "Die Tool-Aktion wurde bereits ausgeführt; bitte nutze den bestätigten PDF-Pfad "
                            "aus der Antworthistorie."
                        ),
                        "usage": {},
                        "cost": {"total_cost": 0.0},
                    }

                if _internal_retry_count < 1:
                    logger.info(
                        "Gemini Reason 10: Retrying WITH tools (single retry). fallback_path=tool_retry"
                    )
                    return await self.generate_response(
                        api_key=api_key, model=model, messages=messages, tools=tools,
                        image_data=image_data, force_no_tools=False, # Weiterhin Tools erlauben!
                        _internal_retry_count=_internal_retry_count + 1,
                        **kwargs
                    )
                else:
                    logger.warning(
                        "Gemini Reason 10: Giving up on tools. fallback_path=text_only_fallback"
                    )
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
                    
                    # Reverse-map: underscores back to dots for ToolExecutor
                    original_name = fc.name.replace("_", ".", fc.name.count("_")) if fc.name else fc.name
                    # Only restore dots for known namespace patterns (e.g. system_weather -> system.weather)
                    restored_name = fc.name
                    if "_" in fc.name:
                        parts = fc.name.split("_", 1)
                        candidate = f"{parts[0]}.{parts[1]}" if len(parts) == 2 else fc.name
                        # Check if dot-notation version is a known skill
                        from backend.services.tool_manager import tool_manager as _tm
                        if _tm.get_tool(candidate):
                            restored_name = candidate
                    
                    all_gateway_tool_calls.append({
                        "id": f"call_{fc.name}_{datetime.datetime.now().timestamp()}",
                        "type": "function",
                        "function": {"name": restored_name, "arguments": json.dumps(tool_args)}
                    })
                elif hasattr(part, "text") and part.text:
                    # Wenn es reiner Text ist und kein Funktionsaufruf, akkumuliere ihn
                    text_accumulated += part.text
                    
                    # --- CLEANUP: INTERNE GEDANKEN FILTERN ---
                    # Wenn das Modell fälschlicherweise seinen Denkprozess ausgibt (beginnt oft mit "thought")
                    if text_accumulated.strip().lower().startswith("thought"):
                        # Suche nach dem Trenner, wo die echte Antwort beginnt (meist "Text:", "Antwort:" oder "Output:")
                        # Wir suchen nach dem letzten Vorkommen eines solchen Trenners
                        split_match = re.search(r'\n(Text|Antwort|Output|Response):\s*\n', text_accumulated, re.IGNORECASE)
                        if split_match:
                            # Wir nehmen nur den Teil NACH dem Trenner
                            logger.info("Filtered out internal Chain-of-Thought from Gemini response.")
                            text_accumulated = text_accumulated[split_match.end():].strip()
                    # -----------------------------------------

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

                # 💎 METADATA EXTRACTION: Grounding Metadata für LinkRenderer
                grounding_metadata = self._extract_grounding_metadata(response)

                return {
                    "type": "tool_code",
                    "tool_calls": all_gateway_tool_calls,
                    "usage": usage,
                    "cost": cost,
                    "grounding_metadata": grounding_metadata,  # 💎 Für LinkRenderer
                    "raw_assistant_response": {
                        "role": "model", # Wichtig: "model" statt "assistant" hier
                        "parts": parts_for_raw_assistant # Verwende die neue Struktur
                    }
                }
            else:
                # 💎 METADATA EXTRACTION: Grounding Metadata für LinkRenderer
                grounding_metadata = self._extract_grounding_metadata(response)

                return {
                    "type": "text", 
                    "text": text_accumulated, 
                    "usage": usage, 
                    "cost": cost,
                    "grounding_metadata": grounding_metadata  # 💎 Für LinkRenderer
                }

        except Exception as e:
            logger.error(f"Gemini Exception: {e}", exc_info=True)
            return {"type": "error", "message": f"Fehler: {str(e)}"}

    def _gemini_stream_build_request(
        self,
        api_key: str,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]],
        image_data: Optional[str],
        force_no_tools: bool,
        force_tool_name: Optional[str],
    ) -> Tuple[Any, List[Any], Dict[str, Any], Dict[str, Any]]:
        """
        Gleiche Aufbereitung wie generate_response bis zum API-Call (nur für Streaming).
        generate_response bleibt unverändert.
        """
        genai.configure(api_key=api_key)

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        model_kwargs: Dict[str, Any] = {
            "safety_settings": safety_settings,
        }

        if tools and not force_no_tools:
            gemini_tools = self._convert_tools_to_gemini_format(tools)
            if gemini_tools:
                model_kwargs["tools"] = gemini_tools
                if force_tool_name:
                    safe_force_name = self._sanitize_gemini_name(force_tool_name)
                    model_kwargs["tool_config"] = to_tool_config({
                        "function_calling_config": {
                            "mode": "ANY",
                            "allowed_function_names": [safe_force_name],
                        }
                    })
                else:
                    model_kwargs["tool_config"] = to_tool_config({"function_calling_config": {"mode": "auto"}})
        else:
            model_kwargs.pop("tools", None)
            model_kwargs.pop("tool_config", None)

        system_instruction_parts = []
        for message in messages:
            if message.get("role") != "system":
                continue
            content = str(message.get("content") or "").strip()
            if content:
                system_instruction_parts.append(content)
        system_instruction = "\n\n".join(system_instruction_parts) if system_instruction_parts else None

        history_without_system = [msg for msg in messages if msg.get("role") != "system"]
        gemini_history_for_api: List[Any] = []

        import base64

        for message in history_without_system:
            role = "user" if message["role"] == "user" else "model"

            if message["role"] in ["user", "assistant", "model"] and "tool_calls" not in message:
                parts = []
                content = message.get("content")

                if isinstance(content, str):
                    parts.append(content)
                elif isinstance(content, list):
                    for part_data in content:
                        if part_data.get("type") == "text":
                            parts.append(part_data.get("text", ""))

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

            elif message["role"] in ["assistant", "model"] and "tool_calls" in message:
                raw_parts = message.get("_gemini_raw_model_parts")
                n_tc = len(message.get("tool_calls") or [])
                if (
                    isinstance(raw_parts, list)
                    and len(raw_parts) > 0
                    and n_tc > 0
                    and len(raw_parts) >= n_tc
                ):
                    try:
                        gemini_history_for_api.append({"role": "model", "parts": list(raw_parts)})
                        logger.info(
                            "GEMINI-HISTORY: Stream-Model-Parts übernommen (%d parts, %d tool_calls) — thought_signature-Pfad aktiv.",
                            len(raw_parts),
                            n_tc,
                        )
                        continue
                    except Exception as raw_exc:
                        logger.warning("GEMINI-HISTORY: Raw-Parts unbrauchbar, synthetische Parts: %s", raw_exc)
                tool_calls_proto = []
                for tc in message["tool_calls"]:
                    try:
                        args = json.loads(tc["function"]["arguments"])
                    except Exception:
                        args = {}
                    tc_name = self._sanitize_gemini_name(tc["function"]["name"])
                    tool_calls_proto.append(
                        protos.Part(function_call=protos.FunctionCall(name=tc_name, args=args))
                    )
                gemini_history_for_api.append({"role": "model", "parts": tool_calls_proto})

            elif message["role"] == "tool":
                tool_call_id = message.get("tool_call_id")
                function_name = message.get("name")

                if not function_name and tool_call_id:
                    for past_msg in reversed(messages):
                        if "tool_calls" in past_msg:
                            for tc in past_msg["tool_calls"]:
                                if tc.get("id") == tool_call_id:
                                    function_name = tc["function"]["name"]
                                    break
                        if function_name:
                            break

                final_name = self._sanitize_gemini_name(function_name or "unknown_function")

                # Gemini expects ``function_response.response`` to be a structured dict.
                # Passing a raw JSON-string under {"content": "..."} prevents Gemini from
                # seeing the tool actually returned data, causing it to re-call the tool
                # in a loop. Parse the JSON envelope and hand Gemini the structured
                # payload directly; fall back to a string wrapper only on parse errors.
                raw_content = message.get("content")
                parsed_response: Dict[str, Any]
                if isinstance(raw_content, dict):
                    parsed_response = raw_content
                else:
                    try:
                        parsed_response = json.loads(str(raw_content))
                        if not isinstance(parsed_response, dict):
                            parsed_response = {"content": parsed_response}
                    except Exception:
                        parsed_response = {"content": str(raw_content) if raw_content is not None else ""}

                gemini_history_for_api.append({
                    "role": "user",
                    "parts": [
                        protos.Part(function_response=protos.FunctionResponse(
                            name=final_name,
                            response=parsed_response,
                        ))
                    ],
                })

        gemini_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_instruction,
        )

        request_options = {"timeout": 150}

        if "tools" in model_kwargs:
            model_kwargs["tools"] = self._recursive_remove_additional_properties(model_kwargs["tools"])

        return gemini_model, gemini_history_for_api, model_kwargs, request_options

    async def generate_response_stream(
        self,
        api_key: str,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        image_data: Optional[str] = None,
        force_no_tools: bool = False,
        force_tool_name: Optional[str] = None,
        stream_workflow_ref: Any = None,
        **kwargs,
    ) -> AsyncIterator[StreamEvent]:
        """Streaming-Variante: generate_content_async(..., stream=True); generate_response unverändert.

        ``stream_workflow_ref``: optional :class:`ChatRequestWorkflowState` — letzte Kandidaten-``parts``
        (inkl. ``thought_signature`` auf Proto-Ebene, sobald die API sie liefert) werden für die nächste
        Tool-Runde in ``gemini_stream_raw_model_parts`` gehalten.
        """
        kwargs = kwargs or {}
        try:
            gemini_model, gemini_history_for_api, model_kwargs, request_options = self._gemini_stream_build_request(
                api_key,
                model,
                messages,
                tools,
                image_data,
                force_no_tools,
                force_tool_name,
            )
            stream_iter = await gemini_model.generate_content_async(
                contents=gemini_history_for_api,
                request_options=request_options,
                stream=True,
                **model_kwargs,
            )
            last_usage: Any = None
            async for chunk in stream_iter:
                if hasattr(chunk, "prompt_feedback") and chunk.prompt_feedback:
                    br = getattr(chunk.prompt_feedback, "block_reason", None)
                    if br:
                        yield StreamEvent(
                            type="error",
                            content=f"Blockiert: {getattr(br, 'name', br)}",
                            metadata={"provider": "gemini"},
                        )
                        return
                if not getattr(chunk, "candidates", None):
                    continue
                cand = chunk.candidates[0]
                content_obj = getattr(cand, "content", None)
                if content_obj and getattr(content_obj, "parts", None):
                    if stream_workflow_ref is not None:
                        try:
                            stream_workflow_ref.gemini_stream_raw_model_parts = list(content_obj.parts)
                        except Exception as buf_exc:
                            logger.debug("GEMINI-STREAM: Konnte model parts nicht puffern: %s", buf_exc)
                    for part in content_obj.parts:
                        if hasattr(part, "text") and part.text:
                            yield StreamEvent(type="text_delta", content=part.text, metadata={})
                        if hasattr(part, "function_call") and part.function_call:
                            fc = part.function_call
                            tool_args = _proto_to_dict(fc.args) if fc.args else {}
                            # Reverse-map: underscores back to dots for ToolExecutor
                            stream_restored_name = fc.name
                            if fc.name and "_" in fc.name:
                                _parts = fc.name.split("_", 1)
                                _candidate = f"{_parts[0]}.{_parts[1]}" if len(_parts) == 2 else fc.name
                                from backend.services.tool_manager import tool_manager as _tm2
                                if _tm2.get_tool(_candidate):
                                    stream_restored_name = _candidate
                            yield StreamEvent(
                                type="tool_delta",
                                content={"name": stream_restored_name, "arguments": tool_args},
                                metadata={},
                            )
                um = getattr(chunk, "usage_metadata", None)
                if um is not None:
                    last_usage = um

            if last_usage is not None:
                usage, cost = _calculate_and_log_cost(
                    model,
                    {
                        "prompt_tokens": getattr(last_usage, "prompt_token_count", 0),
                        "completion_tokens": getattr(last_usage, "candidates_token_count", 0),
                    },
                )
                yield StreamEvent(
                    type="usage",
                    content={"usage": usage, "cost": cost},
                    metadata={"provider": "gemini"},
                )
            yield StreamEvent(type="done", content=None, metadata={"provider": "gemini"})
        except Exception as e:
            logger.error(f"Gemini stream exception: {e}", exc_info=True)
            yield StreamEvent(type="error", content=str(e), metadata={"provider": "gemini"})

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
    async def generate_image(
        self,
        api_key: str,
        model: str,
        prompt: str,
        narrative_prompt: str,
        preset_context: Dict,
        image_bytes_list: list = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generates an image using Google's Gemini models.
        Applies "Diamond Standard" prompt engineering before calling the capability.
        
        Args:
            api_key: Gemini API key
            model: Model name (e.g., 'gemini-1.5-pro')
            prompt: Primary prompt for image generation
            narrative_prompt: Director's narrative description of the desired output
            preset_context: Context information for preset configurations
            image_bytes_list: List of image data for editing/combination
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing the generated image URL and metadata
        """
        # --- 1. PROMPT ASSEMBLY ---
        # Start with the Director's high-quality narrative.
        # Fallback to user prompt if narrative is missing.
        final_prompt_for_gemini = narrative_prompt if narrative_prompt else prompt
        
        # --- 2. STYLE ENFORCEMENT (The Fix) ---
        # Gemini (Imagen 3) often requires explicit style keywords at the very end 
        # to override its internal safety/aesthetic filters (e.g. for "dirty" historical photos).
        if preset_context and preset_context.get("has_preset"):
            tech_keywords = preset_context.get("gemini_style_keywords", "")
            
            if tech_keywords and len(tech_keywords) > 5:
                # We append keywords explicitly, even if the Director might have used them.
                # Redundancy is key for Gemini adherence.
                final_prompt_for_gemini = f"{final_prompt_for_gemini} \n\n!!! CRITICAL STYLE REFERENCE !!!\n{tech_keywords}"
                logger.info("Gemini Provider: Enforced technical keywords via append.")

        logger.info(f"Gemini Provider: Delegating to capability. Final Prompt Length: {len(final_prompt_for_gemini)}")

        # --- 3. DELEGATION ---
        # We pass 'final_prompt_for_gemini' as the 'prompt' argument to the capability.
        return await self.image_generator.generate_image(
            api_key=api_key,
            model=model,
            prompt=final_prompt_for_gemini,  # <--- KEY FIX: Use the assembled prompt!
            narrative_prompt=narrative_prompt,  # Still pass through for reference
            preset_context=preset_context,
            image_bytes_list=image_bytes_list,
            **kwargs
        )

    def _extract_grounding_metadata(self, response) -> dict:
        """Extrahiert Grounding Metadata (Chunks, Supports, Queries) sicher aus der Response."""
        metadata = {
            "grounding_chunks": [],
            "grounding_supports": [],
            "web_search_queries": []
        }

        try:
            if not response or not response.candidates:
                return metadata

            candidate = response.candidates[0]
            if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
                gm = candidate.grounding_metadata

                if hasattr(gm, "grounding_chunks"):
                    metadata["grounding_chunks"] = gm.grounding_chunks
                if hasattr(gm, "grounding_supports"):
                    metadata["grounding_supports"] = gm.grounding_supports
                if hasattr(gm, "web_search_queries"):
                    metadata["web_search_queries"] = list(gm.web_search_queries)

        except Exception as e:
            logger.warning(f"Fehler bei Grounding-Metadata Extraktion: {e}")

        return metadata

    def prepare_history_for_second_call(self, chat_history, raw_assistant_response, tool_results):
        # Gemini braucht die Ergebnisse in der Historie
        return chat_history + [raw_assistant_response] + tool_results