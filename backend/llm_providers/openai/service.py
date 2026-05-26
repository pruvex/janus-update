import logging
import json
from typing import Any, AsyncIterator, Dict, List, Optional, Type

import openai
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel

from backend.llm_providers.shared.base_provider import BaseLLMProvider
from backend.llm_providers.capabilities.openai_image_generation import (
    OpenAIImageGeneration,
)
from backend.services.cost_calculator import calculate_cost
from backend.services.orchestrator.stream_protocol import StreamEvent

logger = logging.getLogger("janus_backend")

_FINANCE_ASSISTANT_DIRECTIVE = (
    "Du bist ein Finanzassistent. Wenn du nach Goldpreisen oder Finanzdaten suchst, "
    "antworte in Euro (€), nenne den Preis und die Quelle als Link."
)


def _contains_finance_instruction(messages: List[Dict]) -> bool:
    for msg in messages or []:
        if not isinstance(msg, dict):
            continue
        if msg.get("role") != "system":
            continue
        content = str(msg.get("content") or "")
        if _FINANCE_ASSISTANT_DIRECTIVE in content:
            return True
    return False


def _is_websearch_tool_payload(tool_result: Dict) -> bool:
    if not isinstance(tool_result, dict):
        return False
    skill_name = str(
        tool_result.get("_skill_id")
        or tool_result.get("skill_id")
        or tool_result.get("name")
        or ""
    ).strip().lower()
    if skill_name in {"system.websearch", "websearch_wrapper"}:
        return True
    payload = tool_result.get("content")
    try:
        payload = json.loads(payload) if isinstance(payload, str) else payload
    except Exception:
        payload = None
    if not isinstance(payload, dict):
        return False
    inner_skill = str(payload.get("_skill_id") or payload.get("name") or "").strip().lower()
    return inner_skill in {"system.websearch", "websearch_wrapper"}


def _calculate_and_log_cost(model_id, usage_data=None, custom_prompt=None):
    """
    Berechnet die Kosten und gibt sie formatiert im Log aus (analog zu Gemini).
    """
    usage, cost = calculate_cost(model_id, usage_data, custom_prompt)
    
    # FIX: Korrekte Dictionary-Keys für das Logging verwenden
    input_tokens = usage.get('input_tokens', 0)
    output_tokens = usage.get('output_tokens', 0)
    total_cost = cost.get('total_cost', 0) if isinstance(cost, dict) else 0
    
    logger.info(
        f"\n--- USAGE TRACKING (OpenAI) ---\n"
        f"Model: {model_id}\n"
        f"Input Tokens: {input_tokens}\n"
        f"Output Tokens: {output_tokens}\n"
        f"Total Cost: {total_cost:.8f} €\n"
        f"-----------------------------"
    )
    return usage, cost


async def iter_openai_chat_completion_stream_events(
    client: openai.AsyncOpenAI,
    *,
    model: str,
    api_call_params: Dict[str, Any],
) -> AsyncIterator[StreamEvent]:
    """
    OpenAI-kompatibler Chat-Stream → StreamEvent-Folge (auch für Ollama AsyncOpenAI).
    """
    params = dict(api_call_params)
    params["stream"] = True
    params["stream_options"] = {"include_usage": True}
    
    # 💎 OPENAI_SHIM: Normalize tool names to match ^[a-zA-Z0-9_-]+$ pattern
    # OpenAI doesn't accept dots in tool names, so we replace them with underscores
    if "tools" in params:
        for tool in params["tools"]:
            if isinstance(tool, dict) and "function" in tool and "name" in tool["function"]:
                original_name = tool["function"]["name"]
                normalized_name = original_name.replace(".", "_")
                if original_name != normalized_name:
                    logger.debug(f"[OPENAI_SHIM] Normalizing tool name from '{original_name}' to '{normalized_name}'")
                    tool["function"]["name"] = normalized_name
    
    # Also normalize tool_choice if it's a function
    if "tool_choice" in params and isinstance(params["tool_choice"], dict) and "function" in params["tool_choice"]:
        if "name" in params["tool_choice"]["function"]:
            original_name = params["tool_choice"]["function"]["name"]
            normalized_name = original_name.replace(".", "_")
            if original_name != normalized_name:
                logger.debug(f"[OPENAI_SHIM] Normalizing tool_choice from '{original_name}' to '{normalized_name}'")
                params["tool_choice"]["function"]["name"] = normalized_name
    
    # 💎 OPENAI_SHIM: Re-injection Guard - Ensure forced tool is in tools list
    if "tool_choice" in params and isinstance(params["tool_choice"], dict) and "function" in params["tool_choice"]:
        if "name" in params["tool_choice"]["function"]:
            forced_tool_name = params["tool_choice"]["function"]["name"]
            # Check if forced tool exists in tools list
            tool_names = [tool.get("function", {}).get("name") for tool in params.get("tools", []) if isinstance(tool, dict)]
            if forced_tool_name not in tool_names:
                # Re-inject missing forced tool
                from backend.services.skill_router import skill_router
                try:
                    tool_def = skill_router.get_tool_definition(forced_tool_name)
                    # Format tool definition for OpenAI API
                    tool_obj = {
                        "type": "function",
                        "function": {
                            "name": forced_tool_name,
                            "description": tool_def.description or "",
                            "parameters": tool_def.parameters.model_dump() if hasattr(tool_def, "parameters") else {}
                        }
                    }
                    if "tools" not in params:
                        params["tools"] = []
                    params["tools"].append(tool_obj)
                    logger.warning("[OPENAI_SHIM] Re-injecting missing forced tool definition: %s", forced_tool_name)
                except Exception as e:
                    logger.error("[OPENAI_SHIM] Failed to re-inject forced tool %s: %s", forced_tool_name, e)
    try:
        stream = await client.chat.completions.create(**params)
    except TypeError:
        params.pop("stream_options", None)
        stream = await client.chat.completions.create(**params)

    async for chunk in stream:
        if getattr(chunk, "usage", None):
            usage, cost = _calculate_and_log_cost(model, usage_data=chunk.usage)
            yield StreamEvent(
                type="usage",
                content={"usage": usage, "cost": cost},
                metadata={"provider": "openai"},
            )
        choices = getattr(chunk, "choices", None) or []
        if not choices:
            continue
        choice = choices[0]
        delta = getattr(choice, "delta", None)
        if delta is not None:
            content_piece = getattr(delta, "content", None)
            if content_piece:
                yield StreamEvent(type="text_delta", content=str(content_piece), metadata={})
            tool_calls = getattr(delta, "tool_calls", None)
            if tool_calls:
                for tc in tool_calls:
                    frag: Dict[str, Any] = {}
                    idx = getattr(tc, "index", None)
                    if idx is not None:
                        frag["index"] = idx
                    if getattr(tc, "id", None):
                        frag["id"] = tc.id
                    fn = getattr(tc, "function", None)
                    if fn is not None:
                        if getattr(fn, "name", None):
                            frag["name"] = fn.name
                        if getattr(fn, "arguments", None):
                            frag["arguments"] = fn.arguments
                    yield StreamEvent(type="tool_delta", content=frag, metadata={})
        finish = getattr(choice, "finish_reason", None)
        if finish:
            yield StreamEvent(type="finish", content=None, metadata={"finish_reason": str(finish)})

    yield StreamEvent(type="done", content=None, metadata={"provider": "openai"})


class OpenAIServiceProvider(BaseLLMProvider):
    def __init__(self):
        self.image_generator = OpenAIImageGeneration()

    @staticmethod
    def _to_openai_tool_name(name: str) -> str:
        return str(name or "").replace(".", "_")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        image_data: Optional[str] = None,
        force_tool_name: Optional[str] = None,
        max_completion_tokens: Optional[int] = None,
        **kwargs, # Hier **kwargs hinzugefügt
    ) -> Dict:
        client = openai.AsyncOpenAI(api_key=api_key, timeout=180.0)
        try:
            # 1. Input-Bereinigung
            clean_messages = []
            for msg in messages:
                if msg.get("role") == "system" and not msg.get("content"):
                    continue
                # Entferne leere Tool Calls, die OpenAI verwirren könnten
                if "tool_calls" in msg and msg["tool_calls"] is None:
                    del msg["tool_calls"]
                clean_messages.append(msg)

            if image_data and clean_messages:
                last_user_idx = next(
                    (idx for idx in range(len(clean_messages) - 1, -1, -1) if clean_messages[idx].get("role") == "user"),
                    None,
                )
                if last_user_idx is not None:
                    last_user_msg = dict(clean_messages[last_user_idx])
                    content = last_user_msg.get("content")

                    if isinstance(content, str):
                        multimodal_content = [{"type": "text", "text": content}]
                    elif isinstance(content, list):
                        multimodal_content = list(content)
                    else:
                        multimodal_content = []

                    has_image_part = any(
                        isinstance(part, dict)
                        and part.get("type") in {"image_url", "input_image"}
                        for part in multimodal_content
                    )
                    if not has_image_part:
                        multimodal_content.append({
                            "type": "image_url",
                            "image_url": {"url": image_data},
                        })
                    last_user_msg["content"] = multimodal_content
                    clean_messages[last_user_idx] = last_user_msg

            api_call_params = {
                "model": model,
                "messages": clean_messages,
            }
            
            # Falls max_tokens in kwargs vorhanden ist, füge es zu api_call_params["max_tokens"] hinzu
            if "max_tokens" in kwargs:
                api_call_params["max_tokens"] = kwargs["max_tokens"]
                kwargs.pop("max_tokens") # Aus kwargs entfernen, um Redundanz zu vermeiden
            
            # Falls max_completion_tokens explizit als Parameter an generate_response übergeben wurde, hat es Vorrang und wird zu api_call_params["max_tokens"]
            if max_completion_tokens is not None:
                api_call_params["max_tokens"] = max_completion_tokens

            # Gateway-Only Flags niemals an OpenAI API durchreichen
            kwargs.pop("is_image_analysis_request", None)
            kwargs.pop("requested_skills", None)
            kwargs.pop("force_no_tools", None)

            # Füge die restlichen kwargs hinzu, die nicht explizit behandelt wurden.
            api_call_params.update(kwargs)

            if tools:
                converted_tools = self._convert_tools_to_openai_format(tools)
                if converted_tools:
                    api_call_params["tools"] = converted_tools
                    if force_tool_name:
                        api_call_params["tool_choice"] = {
                            "type": "function",
                            "function": {"name": self._to_openai_tool_name(force_tool_name)},
                        }
                    elif "tool_choice" not in api_call_params:
                        api_call_params["tool_choice"] = "auto"

            # MUSS-FIX: Parameter-Umbenennung für neue Modelle (o1, o3, gpt-5-nano)
            if "max_tokens" in api_call_params:
                logger.info("Interception: Renaming max_tokens to max_completion_tokens for OpenAI compatibility.")
                api_call_params["max_completion_tokens"] = api_call_params.pop("max_tokens")

            # 2. API Aufruf
            response = await client.chat.completions.create(**api_call_params)

            # --- START DER FINALEN KORREKTUR ---

            # Extrahiere das usage-Objekt aus der Antwort. Es ist nicht None.
            usage_data = response.usage

            # Rufe den Kostenrechner jetzt mit den echten Nutzungsdaten auf.
            usage, cost = _calculate_and_log_cost(model, usage_data=usage_data)

            # --- ENDE DER FINALEN KORREKTUR ---
            
            response_message = response.choices[0].message

            # 3. Tool Call Handling (Goldstandard)
            if response_message.tool_calls:
                tool_calls_list = [tc.model_dump() for tc in response_message.tool_calls]

                logger.info(f"OpenAI triggered {len(tool_calls_list)} tool calls.")

                return {
                    "type": "tool_code",
                    "tool_calls": tool_calls_list,
                    "usage": usage,
                    "cost": cost,
                    "raw_assistant_response": response_message.model_dump(),
                }

            # 4. Standard Text Antwort
            text_response = response_message.content
            finish_reason = response.choices[0].finish_reason # Extrahiere finish_reason

            # Prüfung auf Refusal (Safety)
            if hasattr(response_message, "refusal") and response_message.refusal:
                logger.warning(f"OpenAI Refusal: {response_message.refusal}")
                return {
                    "type": "text",
                    "text": f"Anfrage abgelehnt: {response_message.refusal}",
                    "usage": usage,
                    "cost": cost,
                    "finish_reason": finish_reason,
                }

            return {
                "type": "text",
                "text": text_response,
                "image_url": None,
                "usage": usage,
                "cost": cost,
                "finish_reason": finish_reason,
            }

        except Exception as e:
            logger.error(f"An error occurred with OpenAI API: {e}", exc_info=True)
            raise

    def _build_stream_api_params(
        self,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]],
        image_data: Optional[str],
        force_tool_name: Optional[str],
        max_completion_tokens: Optional[int],
        kwargs: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Wie generate_response: Request-Dict ohne stream (für Streaming-Pipeline)."""
        kwargs = dict(kwargs or {})
        clean_messages = []
        for msg in messages:
            if msg.get("role") == "system" and not msg.get("content"):
                continue
            if "tool_calls" in msg and msg["tool_calls"] is None:
                del msg["tool_calls"]
            clean_messages.append(msg)

        if image_data and clean_messages:
            last_user_idx = next(
                (idx for idx in range(len(clean_messages) - 1, -1, -1) if clean_messages[idx].get("role") == "user"),
                None,
            )
            if last_user_idx is not None:
                last_user_msg = dict(clean_messages[last_user_idx])
                content = last_user_msg.get("content")

                if isinstance(content, str):
                    multimodal_content = [{"type": "text", "text": content}]
                elif isinstance(content, list):
                    multimodal_content = list(content)
                else:
                    multimodal_content = []

                has_image_part = any(
                    isinstance(part, dict)
                    and part.get("type") in {"image_url", "input_image"}
                    for part in multimodal_content
                )
                if not has_image_part:
                    multimodal_content.append({
                        "type": "image_url",
                        "image_url": {"url": image_data},
                    })
                last_user_msg["content"] = multimodal_content
                clean_messages[last_user_idx] = last_user_msg

        api_call_params: Dict[str, Any] = {
            "model": model,
            "messages": clean_messages,
        }

        if "max_tokens" in kwargs:
            api_call_params["max_tokens"] = kwargs["max_tokens"]
            kwargs.pop("max_tokens")

        if max_completion_tokens is not None:
            api_call_params["max_tokens"] = max_completion_tokens

        kwargs.pop("is_image_analysis_request", None)
        kwargs.pop("requested_skills", None)
        kwargs.pop("force_no_tools", None)

        api_call_params.update(kwargs)

        if tools:
            converted_tools = self._convert_tools_to_openai_format(tools)
            if converted_tools:
                api_call_params["tools"] = converted_tools
                if force_tool_name:
                    api_call_params["tool_choice"] = {
                        "type": "function",
                        "function": {"name": self._to_openai_tool_name(force_tool_name)},
                    }
                    logger.info("💎 VIDEO-FORCE (stream): tool_choice forced to function: %s", force_tool_name)
                else:
                    api_call_params["tool_choice"] = "auto"
                    logger.info("💎 VIDEO-FORCE (stream): tool_choice set to auto (no force_tool_name)")
            elif force_tool_name:
                # Fallback: If tools conversion failed but force_tool_name is set, still try to force it
                api_call_params["tool_choice"] = {
                    "type": "function",
                    "function": {"name": self._to_openai_tool_name(force_tool_name)},
                }
                logger.warning("💎 VIDEO-FORCE (stream): tool_choice forced despite empty converted_tools: %s", force_tool_name)

        if "max_tokens" in api_call_params:
            logger.info("Interception: Renaming max_tokens to max_completion_tokens for OpenAI compatibility.")
            api_call_params["max_completion_tokens"] = api_call_params.pop("max_tokens")

        return api_call_params

    async def generate_response_stream(
        self,
        api_key: str,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        image_data: Optional[str] = None,
        force_tool_name: Optional[str] = None,
        max_completion_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[StreamEvent]:
        """Streaming-Variante: echte Token-/Chunk-Events, unabhängig von generate_response."""
        logger.info("💎 VIDEO-FORCE (OpenAI.generate_response_stream): Received force_tool_name=%s", force_tool_name)
        client = openai.AsyncOpenAI(api_key=api_key, timeout=180.0)
        api_call_params = self._build_stream_api_params(
            model,
            messages,
            tools,
            image_data,
            force_tool_name,
            max_completion_tokens,
            kwargs,
        )
        async for ev in iter_openai_chat_completion_stream_events(
            client, model=model, api_call_params=api_call_params
        ):
            yield ev

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_structured_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict],
        response_format: Type[BaseModel],
        **kwargs,
    ) -> tuple[BaseModel, Dict[str, Any]]:
        client = openai.AsyncOpenAI(api_key=api_key, timeout=180.0)
        try:
            clean_messages = []
            for msg in messages:
                if msg.get("role") == "system" and not msg.get("content"):
                    continue
                clean_messages.append(msg)

            # Beta Parse Call
            completion = await client.beta.chat.completions.parse(
                model=model,
                messages=clean_messages,
                response_format=response_format,
            )

            # Kostenberechnung
            cost_data = {} # Default
            usage = {}
            if completion.usage:
                usage_dict = {
                    "prompt_tokens": completion.usage.prompt_tokens,
                    "completion_tokens": completion.usage.completion_tokens
                }
                usage, cost_data = _calculate_and_log_cost(model, usage_data=usage_dict)

            message = completion.choices[0].message

            if message.refusal:
                logger.warning(f"OpenAI Refusal during structured output: {message.refusal}")
                raise ValueError(f"Model refused request: {message.refusal}")

            # RÜCKGABE: Tuple (Parsed Object, Cost Data)
            return message.parsed, cost_data

        except Exception as e:
            logger.error(f"Error in generate_structured_response (OpenAI): {e}", exc_info=True)
            raise

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
        """Generiert ein Bild mit dem OpenAI Image Generator.
        
        Args:
            api_key: API-Schlüssel für OpenAI
            model: Modellname (z.B. 'dall-e-3')
            prompt: Der primäre Prompt für die Bildgenerierung
            narrative_prompt: Eine narrative Beschreibung des gewünschten Ergebnisses
            preset_context: Kontextinformationen für Preset-Einstellungen
            image_bytes_list: Liste von Bilddaten für Bearbeitung/Kombination
            **kwargs: Zusätzliche parameter-spezifische Argumente
            
        Returns:
            Ein Dictionary mit der generierten Bild-URL und Metadaten
        """
        return await self.image_generator.generate_image(
            api_key=api_key,
            model=model,
            prompt=prompt,
            narrative_prompt=narrative_prompt,
            preset_context=preset_context,
            image_bytes_list=image_bytes_list,
            **kwargs
        )
        
    def _sanitize_openai_tool_schema(self, schema: Any) -> Dict[str, Any]:
        """Clamp Pydantic JSON schema to OpenAI function-calling safe subset."""
        if not isinstance(schema, dict):
            return {"type": "object", "properties": {}}

        def _sanitize_node(node: Any) -> Any:
            if isinstance(node, dict):
                # Strip metadata fields that are irrelevant or problematic for provider parsing.
                cleaned = {
                    key: _sanitize_node(value)
                    for key, value in node.items()
                    if key not in {
                        "title",
                        "examples",
                        "example",
                        "default",
                        "$defs",
                        "definitions",
                        "strict",
                    }
                }

                # Normalize anyOf/oneOf into a simple, predictable shape.
                if "anyOf" in cleaned or "oneOf" in cleaned:
                    variants = cleaned.get("anyOf") or cleaned.get("oneOf") or []
                    if isinstance(variants, list):
                        non_null_variants = [
                            v for v in variants
                            if not (isinstance(v, dict) and v.get("type") == "null")
                        ]
                        if len(non_null_variants) == 1 and isinstance(non_null_variants[0], dict):
                            merged = dict(non_null_variants[0])
                            if "description" in cleaned and "description" not in merged:
                                merged["description"] = cleaned["description"]
                            cleaned = _sanitize_node(merged)
                        else:
                            # Fall back to permissive string for incompatible unions.
                            cleaned = {"type": "string", "description": cleaned.get("description", "")}

                # Ensure object schemas always have properties/required.
                if cleaned.get("type") == "object":
                    props = cleaned.get("properties")
                    if not isinstance(props, dict):
                        cleaned["properties"] = {}
                    req = cleaned.get("required")
                    if not isinstance(req, list):
                        cleaned["required"] = []

                return cleaned
            if isinstance(node, list):
                return [_sanitize_node(item) for item in node]
            return node

        sanitized = _sanitize_node(schema)
        if not isinstance(sanitized, dict):
            return {"type": "object", "properties": {}}
        if sanitized.get("type") != "object":
            sanitized = {"type": "object", "properties": dict(sanitized.get("properties") or {})}
        sanitized.setdefault("properties", {})
        if not isinstance(sanitized.get("properties"), dict):
            sanitized["properties"] = {}
        if "required" in sanitized and not isinstance(sanitized.get("required"), list):
            sanitized["required"] = []
        return sanitized

    def _convert_tools_to_openai_format(self, tools: List[Any]) -> List[Dict]:
        openai_tools = []
        seen_names = set()
        for tool in tools:
            try:
                name = getattr(tool, "name", tool.get("name") if isinstance(tool, dict) else "unknown")
                desc = getattr(tool, "description", tool.get("description") if isinstance(tool, dict) else "")
                args_schema_model = getattr(tool, "args_schema", None)
                schema = {"type": "object", "properties": {}}
                if isinstance(tool, dict) and isinstance(tool.get("parameters"), dict):
                    schema = tool.get("parameters")

                if args_schema_model:
                    if hasattr(args_schema_model, "model_json_schema"):
                        schema = args_schema_model.model_json_schema()
                    elif hasattr(args_schema_model, "schema"):
                        schema = args_schema_model.schema()

                raw_name = str(name)
                openai_safe_name = self._to_openai_tool_name(raw_name)
                if openai_safe_name in seen_names:
                    logger.debug("OpenAI: Skipping duplicate tool name '%s'", openai_safe_name)
                    continue
                seen_names.add(openai_safe_name)
                safe_schema = self._sanitize_openai_tool_schema(schema)
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": openai_safe_name,
                        "description": desc,
                        "parameters": safe_schema,
                    }
                })
            except Exception as e:
                logger.error(f"Überspringe Tool {getattr(tool, 'name', 'unknown')} wegen Konvertierungsfehler: {e}")
                continue

        # 💎 OPENAI_LIMIT: Max 128 tools (API hard limit)
        if len(openai_tools) > 128:
            logger.warning(f"[OPENAI_LIMIT] Truncating {len(openai_tools)} tools to 128 (OpenAI API limit)")
            openai_tools = openai_tools[:128]

        return openai_tools

        
    def prepare_history_for_second_call(
        self,
        chat_history: List[Dict],
        raw_assistant_response: Dict,
        tool_results: List[Dict]
    ) -> List[Dict]:
        """
        Bereitet die Chat-Historie für den Folgeaufruf nach einer Tool-Ausführung vor.
        
        Für OpenAI werden die Assistenten-Antwort und die Tool-Ergebnisse
        einfach an die Historie angehängt. Es ist keine spezielle Behandlung nötig.
        
        Args:
            chat_history: Die bisherige Chat-Historie
            raw_assistant_response: Die rohe Antwort des Assistenten mit dem Tool-Aufruf
            tool_results: Die Ergebnisse der Tool-Ausführung(en)
            
        Returns:
            Die vorbereitete Chat-Historie für den nächsten Aufruf
        """
        # Für OpenAI: Einfach die Antwort des Assistenten und die Tool-Ergebnisse anhängen
        return chat_history + [raw_assistant_response] + tool_results