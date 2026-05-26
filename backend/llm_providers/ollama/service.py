import asyncio
import json
import logging
import re
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Type

import openai
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from .adapter import (
    build_text_outcome,
    build_tool_outcome,
    get_or_create_capabilities,
    set_cached_native_tool_support,
)
from backend.llm_providers.shared.base_provider import BaseLLMProvider
from backend.llm_providers.openai.service import iter_openai_chat_completion_stream_events
from backend.services.orchestrator.stream_protocol import StreamEvent
from backend.utils.config_loader import DEFAULT_OLLAMA_BASE_URL, load_config_data

logger = logging.getLogger("janus_backend")

_MAX_TOOL_SELF_HEAL_ATTEMPTS = 1


def _is_retryable_ollama_exception(exc: Exception) -> bool:
    if isinstance(exc, openai.NotFoundError):
        return False
    if isinstance(exc, openai.BadRequestError):
        return int(getattr(exc, "status_code", 0) or 0) >= 500
    return True


class OllamaServiceProvider(BaseLLMProvider):
    BASE_URL = "http://localhost:11434/v1"
    _TOOL_SUPPORT_CACHE: Dict[str, bool] = {}

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=2),
        retry=retry_if_exception(_is_retryable_ollama_exception),
    )
    async def generate_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        image_data: Optional[str] = None,
        force_tool_name: Optional[str] = None,
        max_completion_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        target_model, target_node_id = self._split_model_node_identifier(model)
        target_base_url = self._get_ollama_openai_base_url(node_id=target_node_id)
        logger.info(
            "Ollama Routing: requested_model=%s target_model=%s node_id=%s base_url=%s",
            model,
            target_model,
            target_node_id,
            target_base_url,
        )
        client = openai.AsyncOpenAI(
            api_key=api_key or "ollama",
            base_url=target_base_url,
            timeout=180.0,
        )
        call_type = str(kwargs.pop("call_type", "") or "").strip().lower()
        is_synthesis_call = call_type == "synthesis"
        request_deadline_seconds = float(
            kwargs.pop(
                "request_deadline_seconds",
                180.0 if is_synthesis_call else 120.0,
            )
        )
        strict_tool_calls = bool(kwargs.pop("strict_tool_calls", False))
        capabilities = get_or_create_capabilities(target_model, target_base_url)
        supports_tools = capabilities.supports_native_tools

        # 💎 EINZIGER Tool-Override: Bekannte tool-fähige Modelle erzwingen supports_tools=True
        model_name_lower = str(target_model).lower()
        is_known_tool_model = any(
            kw in model_name_lower for kw in ("qwen", "llama", "nemo", "mistral", "functionary")
        )
        if tools and is_known_tool_model and not supports_tools:
            supports_tools = True
            logger.info("OLLAMA-TOOL-OVERRIDE: model=%s -> supports_tools auf True erzwungen", target_model)

        clean_messages: List[Dict[str, Any]] = []
        for msg in messages:
            if msg.get("role") == "system" and not msg.get("content"):
                continue
            clean_messages.append(msg)

        request_payload: Dict[str, Any] = {
            "model": target_model,
            "messages": clean_messages,
        }

        if max_completion_tokens is not None:
            request_payload["max_tokens"] = max_completion_tokens
        elif isinstance(kwargs.get("max_tokens"), int):
            request_payload["max_tokens"] = kwargs["max_tokens"]

        kwargs.pop("max_tokens", None)
        kwargs.pop("is_image_analysis_request", None)
        kwargs.pop("force_no_tools", None)

        explicit_tool_choice = kwargs.pop("tool_choice", None)

        # 💎 KONSOLIDIERTE Tool-Entscheidung (eine Stelle, keine Redundanz)
        converted_tools = self._convert_tools_to_openai_format(tools) if tools else []
        if tools and supports_tools and converted_tools:
            request_payload["tools"] = converted_tools
            if force_tool_name:
                request_payload["tool_choice"] = {"type": "function", "function": {"name": force_tool_name}}
            elif explicit_tool_choice is not None:
                request_payload["tool_choice"] = explicit_tool_choice
            else:
                request_payload["tool_choice"] = "auto"
        elif tools and not supports_tools:
            # Modell kann keine Tools -> JSON-Fallback-Anweisung injizieren
            clean_messages = self._inject_tool_json_fallback_instruction(clean_messages, tools)
            request_payload["messages"] = clean_messages
            logger.info(
                "OLLAMA-TOOL-FALLBACK: model=%s supports_tools=False -> JSON-Fallback-Anweisung.",
                target_model,
            )

        if is_synthesis_call:
            request_payload.pop("tools", None)
            request_payload.pop("tool_choice", None)
            request_payload["stream"] = True

        forced_format = kwargs.pop("format", None)
        # 💎 Nur format=json setzen wenn keine Tools erzwungen werden (tool_choice != "required")
        # Ollama kann nicht gleichzeitig JSON-Format erzwingen und Tools erzwingen
        tool_choice_val = request_payload.get("tool_choice")
        is_tool_forced = (
            tool_choice_val == "required" or
            (isinstance(tool_choice_val, dict) and tool_choice_val.get("type") == "function")
        )
        if forced_format == "json" and not is_tool_forced:
            extra_body = request_payload.get("extra_body") or {}
            extra_body["format"] = "json"
            request_payload["extra_body"] = extra_body
            # 💎 System-Prompt injizieren, damit das Modell weiß wie Text in JSON verpackt wird
            clean_messages = self._inject_json_response_wrapper(clean_messages)
            request_payload["messages"] = clean_messages
        elif forced_format == "json" and is_tool_forced:
            logger.debug("OLLAMA-FORMAT-SKIP: format=json ignoriert weil tool_choice=%s erzwungen", tool_choice_val)

        request_payload.update(kwargs)
        request_payload.pop("provider", None)
        request_payload.pop("_force_tools_override", None)

        # 💎 HARTER TOOL-OVERRIDE: Nach ALLEN Filtern — Tools erzwingen wenn sie verschwunden sind
        if tools and is_known_tool_model and not is_synthesis_call and "tools" not in request_payload:
            if not converted_tools:
                converted_tools = self._convert_tools_to_openai_format(tools)
            if converted_tools:
                request_payload["tools"] = converted_tools
                request_payload["tool_choice"] = "auto"
                logger.warning(
                    "OLLAMA-HARD-OVERRIDE: Tools waren nach Filtern verschwunden! "
                    "Erzwungen für model=%s (%d tools)", target_model, len(converted_tools),
                )

        system_messages = [
            str(msg.get("content") or "")
            for msg in clean_messages
            if str(msg.get("role") or "") == "system"
        ]
        system_preview = system_messages[0][:160] if system_messages else ""
        logger.info(
            "Ollama Payload-Check: keys=%s has_tools=%s has_tool_choice=%s messages=%s system_preview=%s",
            sorted(request_payload.keys()),
            "tools" in request_payload,
            "tool_choice" in request_payload,
            len(clean_messages),
            system_preview,
        )

        prompt_size_chars = self._estimate_prompt_size_chars(request_payload)
        if is_synthesis_call:
            logger.info(
                "Ollama [%s] - Synthese-Phase startet. Prompt-Groesse: %s Zeichen.",
                model,
                prompt_size_chars,
            )
        else:
            logger.info("Ollama Start: Prompt-Groesse = %s Zeichen.", prompt_size_chars)
        started_at = time.perf_counter()

        if is_synthesis_call:
            synthesis_result = await self._await_with_deadline(
                self._create_streaming_text_completion(client, request_payload),
                timeout_seconds=request_deadline_seconds,
                context="synthesis",
                model=model,
                estimated_prompt_tokens=gateway_kwargs.get("_estimated_prompt_tokens"),
            )
            elapsed_seconds = time.perf_counter() - started_at
            logger.info("Ollama - Antwort erhalten nach %.1f Sekunden.", elapsed_seconds)
            return build_text_outcome(
                text=synthesis_result.get("text"),
                usage=synthesis_result.get("usage", {}),
                finish_reason=synthesis_result.get("finish_reason"),
            )

        response, detected_supports_tools = await self._await_with_deadline(
            self._create_chat_completion_with_tool_fallback(
                client,
                target_model,
                target_base_url,
                request_payload,
            ),
            timeout_seconds=request_deadline_seconds,
            context="chat",
            model=model,
            estimated_prompt_tokens=gateway_kwargs.get("_estimated_prompt_tokens"),
        )
        if detected_supports_tools is False:
            supports_tools = False
            set_cached_native_tool_support(target_model, target_base_url, False)
        elapsed_seconds = time.perf_counter() - started_at
        logger.info("Ollama Ende: Antwort erhalten nach %.1f Sekunden.", elapsed_seconds)
        response_message = response.choices[0].message
        usage = self._normalize_usage(response.usage)

        if response_message.tool_calls:
            tool_calls_list = [tc.model_dump() for tc in response_message.tool_calls]
            return build_tool_outcome(
                tool_calls=tool_calls_list,
                usage=usage,
                raw_assistant_response=response_message.model_dump(),
            )

        pseudo_tool_calls = []
        if tools:
            pseudo_tool_calls = await self._resolve_tool_calls_from_non_native_response(
                client,
                target_model,
                request_payload,
                tools,
                response_message.content,
            )
        if pseudo_tool_calls:
            logger.warning(
                "OLLAMA-TOOL-FALLBACK: %s pseudo tool calls aus Text extrahiert.",
                len(pseudo_tool_calls),
            )
            return build_tool_outcome(
                tool_calls=pseudo_tool_calls,
                usage=usage,
                raw_assistant_response={
                    "role": "assistant",
                    "content": response_message.content,
                },
            )
        if strict_tool_calls:
            logger.info("OLLAMA-TOOL-FALLBACK: strict_tool_calls aktiv, aber kein Tool gefunden.")

        return build_text_outcome(
            text=response_message.content,
            usage=usage,
            finish_reason=response.choices[0].finish_reason,
        )

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
        """
        OpenAI-kompatibler Streaming-Pfad über denselben AsyncOpenAI-Client wie generate_response.
        Keine Änderung an generate_response.
        """
        kwargs = dict(kwargs)
        target_model, target_node_id = self._split_model_node_identifier(model)
        target_base_url = self._get_ollama_openai_base_url(node_id=target_node_id)
        logger.info(
            "Ollama STREAM Routing: requested_model=%s target_model=%s node_id=%s base_url=%s",
            model,
            target_model,
            target_node_id,
            target_base_url,
        )
        client = openai.AsyncOpenAI(
            api_key=api_key or "ollama",
            base_url=target_base_url,
            timeout=180.0,
        )
        call_type = str(kwargs.pop("call_type", "") or "").strip().lower()
        is_synthesis_call = call_type == "synthesis"
        kwargs.pop(
            "request_deadline_seconds",
            180.0 if is_synthesis_call else 120.0,
        )
        strict_tool_calls = bool(kwargs.pop("strict_tool_calls", False))
        capabilities = get_or_create_capabilities(target_model, target_base_url)
        supports_tools = capabilities.supports_native_tools

        model_name_lower = str(target_model).lower()
        is_known_tool_model = any(
            kw in model_name_lower for kw in ("qwen", "llama", "nemo", "mistral", "functionary")
        )
        if tools and is_known_tool_model and not supports_tools:
            supports_tools = True
            logger.info("OLLAMA-TOOL-OVERRIDE: model=%s -> supports_tools auf True erzwungen", target_model)

        clean_messages: List[Dict[str, Any]] = []
        for msg in messages:
            if msg.get("role") == "system" and not msg.get("content"):
                continue
            clean_messages.append(msg)

        request_payload: Dict[str, Any] = {
            "model": target_model,
            "messages": clean_messages,
        }

        if max_completion_tokens is not None:
            request_payload["max_tokens"] = max_completion_tokens
        elif isinstance(kwargs.get("max_tokens"), int):
            request_payload["max_tokens"] = kwargs["max_tokens"]

        kwargs.pop("max_tokens", None)
        kwargs.pop("is_image_analysis_request", None)
        kwargs.pop("force_no_tools", None)

        explicit_tool_choice = kwargs.pop("tool_choice", None)

        converted_tools = self._convert_tools_to_openai_format(tools) if tools else []
        if tools and supports_tools and converted_tools:
            request_payload["tools"] = converted_tools
            if force_tool_name:
                request_payload["tool_choice"] = {"type": "function", "function": {"name": force_tool_name}}
            elif explicit_tool_choice is not None:
                request_payload["tool_choice"] = explicit_tool_choice
            else:
                request_payload["tool_choice"] = "auto"
        elif tools and not supports_tools:
            clean_messages = self._inject_tool_json_fallback_instruction(clean_messages, tools)
            request_payload["messages"] = clean_messages
            logger.info(
                "OLLAMA-TOOL-FALLBACK: model=%s supports_tools=False -> JSON-Fallback-Anweisung.",
                target_model,
            )

        if is_synthesis_call:
            request_payload.pop("tools", None)
            request_payload.pop("tool_choice", None)
            request_payload["stream"] = True

        forced_format = kwargs.pop("format", None)
        # 💎 Nur format=json setzen wenn keine Tools erzwungen werden (tool_choice != "required")
        # Ollama kann nicht gleichzeitig JSON-Format erzwingen und Tools erzwingen
        tool_choice_val = request_payload.get("tool_choice")
        is_tool_forced = (
            tool_choice_val == "required" or
            (isinstance(tool_choice_val, dict) and tool_choice_val.get("type") == "function")
        )
        if forced_format == "json" and not is_tool_forced:
            extra_body = request_payload.get("extra_body") or {}
            extra_body["format"] = "json"
            request_payload["extra_body"] = extra_body
            # 💎 System-Prompt injizieren, damit das Modell weiß wie Text in JSON verpackt wird
            clean_messages = self._inject_json_response_wrapper(clean_messages)
            request_payload["messages"] = clean_messages
        elif forced_format == "json" and is_tool_forced:
            logger.debug("OLLAMA-FORMAT-SKIP: format=json ignoriert weil tool_choice=%s erzwungen", tool_choice_val)

        request_payload.update(kwargs)
        request_payload.pop("provider", None)
        request_payload.pop("_force_tools_override", None)

        if tools and is_known_tool_model and not is_synthesis_call and "tools" not in request_payload:
            if not converted_tools:
                converted_tools = self._convert_tools_to_openai_format(tools)
            if converted_tools:
                request_payload["tools"] = converted_tools
                request_payload["tool_choice"] = "auto"
                logger.warning(
                    "OLLAMA-HARD-OVERRIDE: Tools waren nach Filtern verschwunden! "
                    "Erzwungen für model=%s (%d tools)", target_model, len(converted_tools),
                )

        _ = strict_tool_calls  # Parität zu generate_response; Streaming wertet es nicht separat aus

        # Entferne stream-Flag falls gesetzt — iter_openai_chat_completion_stream_events setzt es inkl. stream_options
        request_payload.pop("stream", None)

        async for ev in iter_openai_chat_completion_stream_events(
            client,
            model=model,
            api_call_params=request_payload,
        ):
            yield ev

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception(_is_retryable_ollama_exception),
    )
    async def generate_structured_response(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, Any]],
        response_format: Type[BaseModel],
        **kwargs,
    ) -> tuple[BaseModel, Dict[str, Any]]:
        prompt_messages = list(messages)
        prompt_messages.append(
            {
                "role": "system",
                "content": "Antworte als valides JSON gemaess dem geforderten Schema, ohne Markdown.",
            }
        )
        tools = kwargs.pop("tools", None)
        result = await self.generate_response(
            api_key=api_key,
            model=model,
            messages=prompt_messages,
            tools=tools,
            format="json",
            **kwargs,
        )

        text = self._normalize_structured_json_text(result.get("text"))
        try:
            parsed = response_format.model_validate(json.loads(text))
        except (ValidationError, json.JSONDecodeError) as exc:
            extracted_candidate = self._extract_first_json_object(text)
            if extracted_candidate and extracted_candidate != text:
                try:
                    parsed = response_format.model_validate(json.loads(extracted_candidate))
                    return parsed, {"total_cost": 0.0}
                except (ValidationError, json.JSONDecodeError):
                    pass
            logger.warning(
                "Ollama structured response invalid (%s); returning empty facts. text=%s",
                type(exc).__name__,
                text[:1024],
            )
            parsed = response_format.model_validate({"facts": []})
        return parsed, {"total_cost": 0.0}

    async def generate_image(
        self,
        api_key: str,
        model: str,
        prompt: str,
        narrative_prompt: str,
        preset_context: Dict,
        **kwargs,
    ) -> Dict[str, Any]:
        raise ValueError("Ollama provider does not support image generation in Janus.")

    def prepare_history_for_second_call(
        self,
        chat_history: List[Dict],
        raw_assistant_response: Dict,
        tool_results: List[Dict],
    ) -> List[Dict]:
        return chat_history + [raw_assistant_response] + tool_results

    def _convert_tools_to_openai_format(self, tools: List[Any]) -> List[Dict[str, Any]]:
        converted: List[Dict[str, Any]] = []
        for tool in tools:
            try:
                if isinstance(tool, dict):
                    name = tool.get("name") or tool.get("function", {}).get("name")
                    description = tool.get("description") or tool.get("function", {}).get("description", "")
                    parameters = tool.get("parameters") or tool.get("function", {}).get("parameters")
                else:
                    name = getattr(tool, "name", None)
                    description = getattr(tool, "description", "")
                    args_schema = getattr(tool, "args_schema", None)
                    parameters = (
                        args_schema.model_json_schema()
                        if args_schema and hasattr(args_schema, "model_json_schema")
                        else {"type": "object", "properties": {}}
                    )

                if not name:
                    continue

                if not isinstance(parameters, dict):
                    parameters = {"type": "object", "properties": {}}

                converted.append(
                    {
                        "type": "function",
                        "function": {
                            "name": str(name),
                            "description": str(description or ""),
                            "parameters": parameters,
                        },
                    }
                )
            except Exception as exc:
                logger.warning("Skipping tool conversion for Ollama due to error: %s", exc)

        return converted

    @staticmethod
    def _normalize_usage(raw_usage: Any) -> Dict[str, int]:
        if raw_usage is None:
            return {}

        if isinstance(raw_usage, dict):
            prompt_tokens = int(raw_usage.get("prompt_tokens") or raw_usage.get("input_tokens") or 0)
            completion_tokens = int(raw_usage.get("completion_tokens") or raw_usage.get("output_tokens") or 0)
            return {"input_tokens": prompt_tokens, "output_tokens": completion_tokens}

        prompt_tokens = int(getattr(raw_usage, "prompt_tokens", 0) or getattr(raw_usage, "input_tokens", 0) or 0)
        completion_tokens = int(getattr(raw_usage, "completion_tokens", 0) or getattr(raw_usage, "output_tokens", 0) or 0)
        return {"input_tokens": prompt_tokens, "output_tokens": completion_tokens}

    @staticmethod
    def _estimate_prompt_size_chars(request_payload: Dict[str, Any]) -> int:
        payload_for_size = {
            "messages": request_payload.get("messages") or [],
            "tools": request_payload.get("tools") or [],
            "tool_choice": request_payload.get("tool_choice"),
        }
        try:
            return len(json.dumps(payload_for_size, ensure_ascii=False, default=str))
        except Exception:
            return len(str(payload_for_size))

    async def _create_chat_completion_with_tool_fallback(
        self,
        client: openai.AsyncOpenAI,
        model: str,
        base_url: str,
        request_payload: Dict[str, Any],
    ) -> tuple[Any, Optional[bool]]:
        try:
            return await client.chat.completions.create(**request_payload), True
        except openai.BadRequestError as exc:
            error_text = str(exc).lower()
            if exc.status_code == 400 and "does not support tools" in error_text:
                logger.warning(
                    "Modell %s unterstuetzt keine Tools. Starte Fallback auf Text-Only.",
                    model,
                )
                set_cached_native_tool_support(model, base_url, False)
                fallback_payload = dict(request_payload)
                fallback_payload.pop("tools", None)
                fallback_payload.pop("tool_choice", None)
                return await client.chat.completions.create(**fallback_payload), False
            raise

    async def _await_with_deadline(
        self,
        awaitable,
        *,
        timeout_seconds: float,
        context: str,
        model: str,
        estimated_prompt_tokens: Optional[int] = None,
    ):
        # 💎 CU-4: Dynamisches Timeout basierend auf Token-Zahl
        if estimated_prompt_tokens is not None and estimated_prompt_tokens > 4000:
            # Bei großen Anfragen (>4000 Token) erhöhen wir das Timeout auf 5 Minuten
            dynamic_timeout = 300  # 5 Minuten
            logger.info(
                "[CU-4] Large request detected (%d tokens), increasing timeout from %.1fs to %.1fs",
                estimated_prompt_tokens,
                timeout_seconds,
                dynamic_timeout,
            )
            timeout_seconds = dynamic_timeout

        try:
            return await asyncio.wait_for(awaitable, timeout=timeout_seconds)
        except asyncio.TimeoutError as exc:
            logger.error(
                "OLLAMA TIMEOUT: context=%s model=%s deadline=%.1fs",
                context,
                model,
                timeout_seconds,
            )
            raise TimeoutError(
                f"Ollama timeout after {timeout_seconds:.1f}s (context={context}, model={model})."
            ) from exc

    async def _create_streaming_text_completion(
        self,
        client: openai.AsyncOpenAI,
        request_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        stream = await client.chat.completions.create(**request_payload)
        text_parts: List[str] = []
        finish_reason: Optional[str] = None
        usage: Dict[str, int] = {}

        async for chunk in stream:
            if getattr(chunk, "usage", None):
                usage = self._normalize_usage(chunk.usage)
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            choice = choices[0]
            delta = getattr(choice, "delta", None)
            if delta is not None:
                content_piece = getattr(delta, "content", None)
                if content_piece:
                    text_parts.append(str(content_piece))
            reason = getattr(choice, "finish_reason", None)
            if reason:
                finish_reason = str(reason)

        return {
            "text": "".join(text_parts).strip(),
            "usage": usage,
            "finish_reason": finish_reason,
        }

    async def _resolve_tool_calls_from_non_native_response(
        self,
        client: openai.AsyncOpenAI,
        model: str,
        request_payload: Dict[str, Any],
        tools: List[Dict[str, Any]],
        content: Any,
    ) -> List[Dict[str, Any]]:
        normalized = self._normalize_non_native_tool_payload(content, tools)
        if normalized:
            return normalized
        repaired_content = await self._attempt_tool_call_self_heal(
            client,
            model,
            request_payload,
            tools,
            content,
        )
        if repaired_content is None:
            return []
        return self._normalize_non_native_tool_payload(repaired_content, tools)

    async def _attempt_tool_call_self_heal(
        self,
        client: openai.AsyncOpenAI,
        model: str,
        request_payload: Dict[str, Any],
        tools: List[Dict[str, Any]],
        content: Any,
    ) -> Optional[str]:
        tool_spec_by_name = self._tool_spec_by_name(tools)
        validation_error = self._describe_tool_payload_error(content, tool_spec_by_name)
        if not validation_error:
            return None
        logger.info(
            "OLLAMA-TOOL-SELF-HEAL: model=%s reason=%s",
            model,
            validation_error,
        )
        retry_payload = dict(request_payload)
        retry_messages = list(request_payload.get("messages") or [])
        retry_messages.append(
            {
                "role": "system",
                "content": (
                    "Dein letzter Tool-Call war ungueltig. "
                    f"Fehler: {validation_error}. "
                    "Antworte jetzt ausschliesslich mit genau einem validen JSON-Objekt im Format "
                    '{"name":"tool_name","parameters":{...}} ohne Markdown und ohne zusaetzlichen Text.'
                ),
            }
        )
        retry_payload["messages"] = retry_messages
        extra_body = dict(retry_payload.get("extra_body") or {})
        extra_body["format"] = "json"
        retry_payload["extra_body"] = extra_body
        try:
            for _attempt in range(_MAX_TOOL_SELF_HEAL_ATTEMPTS):
                response = await client.chat.completions.create(**retry_payload)
                response_message = response.choices[0].message
                repaired_content = str(getattr(response_message, "content", "") or "").strip()
                if self._normalize_non_native_tool_payload(repaired_content, tools):
                    return repaired_content
        except Exception as exc:
            logger.warning("OLLAMA-TOOL-SELF-HEAL failed for model=%s error=%s", model, exc)
        return None

    def _normalize_non_native_tool_payload(self, content: Any, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        raw_text = str(content or "").strip()
        if not raw_text:
            return []
        tool_spec_by_name = self._tool_spec_by_name(tools)
        tool_calls = self._extract_pseudo_tool_calls_from_text(raw_text)
        if tool_calls:
            normalized_tool_calls: List[Dict[str, Any]] = []
            for tool_call in tool_calls:
                function = tool_call.get("function") if isinstance(tool_call, dict) else None
                tool_name = str((function or {}).get("name") or "").strip()
                if not tool_name or tool_name not in tool_spec_by_name:
                    continue
                try:
                    arguments = json.loads(str((function or {}).get("arguments") or "{}"))
                except json.JSONDecodeError:
                    continue
                normalized_call = self._build_normalized_tool_call(tool_name, arguments, tool_spec_by_name)
                if normalized_call:
                    normalized_tool_calls.append(normalized_call)
            if normalized_tool_calls:
                return normalized_tool_calls

        parsed_payload = self._extract_tool_payload_candidate(raw_text)
        if parsed_payload is None:
            return []
        payload_candidates = parsed_payload if isinstance(parsed_payload, list) else [parsed_payload]
        normalized_tool_calls = []
        for candidate in payload_candidates:
            normalized_call = self._normalize_single_tool_candidate(candidate, tool_spec_by_name)
            if normalized_call:
                normalized_tool_calls.append(normalized_call)
        return normalized_tool_calls

    def _normalize_single_tool_candidate(
        self,
        candidate: Any,
        tool_spec_by_name: Dict[str, Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(candidate, dict):
            return None
        if isinstance(candidate.get("tool_calls"), list):
            for nested in candidate.get("tool_calls") or []:
                normalized = self._normalize_single_tool_candidate(nested, tool_spec_by_name)
                if normalized:
                    return normalized
            return None
        function_payload = candidate.get("function") if isinstance(candidate.get("function"), dict) else None
        tool_name = str(candidate.get("name") or (function_payload or {}).get("name") or "").strip()
        arguments = candidate.get("parameters")
        if arguments is None:
            arguments = candidate.get("arguments")
        if arguments is None and function_payload is not None:
            arguments = function_payload.get("arguments")
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                return None
        if not tool_name or not isinstance(arguments, dict):
            return None
        return self._build_normalized_tool_call(tool_name, arguments, tool_spec_by_name)

    def _build_normalized_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        tool_spec_by_name: Dict[str, Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        spec = tool_spec_by_name.get(tool_name)
        if spec is None:
            return None
        missing_required = [field for field in spec.get("required", []) if field not in arguments or arguments.get(field) in (None, "")]
        if missing_required:
            return None
        normalized_arguments = json.dumps(arguments, ensure_ascii=False)
        return {
            "id": f"ollama-pseudo-call-{tool_name}-{abs(hash(normalized_arguments))}",
            "type": "function",
            "function": {
                "name": tool_name,
                "arguments": normalized_arguments,
            },
        }

    def _describe_tool_payload_error(self, content: Any, tool_spec_by_name: Dict[str, Dict[str, Any]]) -> Optional[str]:
        parsed_payload = self._extract_tool_payload_candidate(content)
        if parsed_payload is None:
            return "Kein parsebares Tool-JSON gefunden"
        payload_candidates = parsed_payload if isinstance(parsed_payload, list) else [parsed_payload]
        for candidate in payload_candidates:
            if not isinstance(candidate, dict):
                continue
            function_payload = candidate.get("function") if isinstance(candidate.get("function"), dict) else None
            tool_name = str(candidate.get("name") or (function_payload or {}).get("name") or "").strip()
            if not tool_name:
                return "Das Feld 'name' fehlt"
            spec = tool_spec_by_name.get(tool_name)
            if spec is None:
                return f"Tool '{tool_name}' ist nicht erlaubt"
            arguments = candidate.get("parameters")
            if arguments is None:
                arguments = candidate.get("arguments")
            if arguments is None and function_payload is not None:
                arguments = function_payload.get("arguments")
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    return "Das Feld 'parameters' enthaelt kein valides JSON"
            if not isinstance(arguments, dict):
                return "Das Feld 'parameters' fehlt oder ist kein JSON-Objekt"
            missing_required = [field for field in spec.get("required", []) if field not in arguments or arguments.get(field) in (None, "")]
            if missing_required:
                return f"Pflichtfelder fehlen: {', '.join(missing_required)}"
        return "Kein gueltiger Tool-Call gefunden"

    def _extract_tool_payload_candidate(self, content: Any) -> Optional[Any]:
        text = self._normalize_structured_json_text(content)
        if not text:
            return None
        candidates = [text]
        extracted = self._extract_first_json_object(text)
        if extracted and extracted != text:
            candidates.append(extracted)
        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        return None

    def _tool_spec_by_name(self, tools: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        specs: Dict[str, Dict[str, Any]] = {}
        for tool in self._convert_tools_to_openai_format(tools):
            function_payload = tool.get("function") if isinstance(tool, dict) else None
            if not isinstance(function_payload, dict):
                continue
            tool_name = str(function_payload.get("name") or "").strip()
            parameters = function_payload.get("parameters") if isinstance(function_payload.get("parameters"), dict) else {}
            if not tool_name:
                continue
            specs[tool_name] = {
                "required": [str(field).strip() for field in (parameters.get("required") or []) if str(field).strip()],
            }
        return specs

    @staticmethod
    def _extract_pseudo_tool_calls_from_text(content: Any) -> List[Dict[str, Any]]:
        text = str(content or "").strip()
        if not text:
            return []

        def _to_tool_call(parsed_payload: Any, idx: int) -> Optional[Dict[str, Any]]:
            candidate = parsed_payload
            if isinstance(candidate, list) and candidate:
                candidate = candidate[0]
            if not isinstance(candidate, dict):
                return None
            tool_name = str(candidate.get("name") or "").strip()
            parameters = candidate.get("parameters")
            if not tool_name or not isinstance(parameters, dict):
                return None
            return {
                "id": f"ollama-pseudo-call-{idx}",
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": json.dumps(parameters, ensure_ascii=False),
                },
            }

        def _iter_json_candidates(raw_text: str):
            decoder = json.JSONDecoder()
            for match in re.finditer(r"[\[{]", raw_text):
                start_idx = match.start()
                try:
                    candidate, _end = decoder.raw_decode(raw_text[start_idx:])
                    yield candidate
                except Exception:
                    continue

        tool_calls: List[Dict[str, Any]] = []
        seen_signatures: set[str] = set()
        fenced_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
        candidate_sources: List[str] = [text]
        candidate_sources.extend(str(block or "") for block in fenced_blocks)

        for source in candidate_sources:
            for parsed_candidate in _iter_json_candidates(source):
                tool_call = _to_tool_call(parsed_candidate, len(tool_calls) + 1)
                if not tool_call:
                    continue
                signature = json.dumps(tool_call.get("function") or {}, ensure_ascii=False, sort_keys=True)
                if signature in seen_signatures:
                    continue
                seen_signatures.add(signature)
                tool_calls.append(tool_call)

        return tool_calls

    def _supports_native_tools(self, model: str, base_url: str) -> bool:
        return get_or_create_capabilities(model, base_url).supports_native_tools

    def _set_native_tool_support(self, model: str, base_url: str, supports_tools: bool) -> None:
        set_cached_native_tool_support(model, base_url, supports_tools)

    @staticmethod
    def _tool_support_cache_key(model: str, base_url: str) -> str:
        return f"{str(base_url or '').strip().lower()}::{str(model or '').strip().lower()}"

    @staticmethod
    def _is_tool_blind_model(model: str) -> bool:
        return not get_or_create_capabilities(model, "").supports_native_tools

    def _inject_tool_json_fallback_instruction(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        fallback_instruction = self._build_tool_json_fallback_instruction(tools)
        if not fallback_instruction:
            return messages
        patched_messages = list(messages)
        for idx, msg in enumerate(patched_messages):
            if str(msg.get("role") or "") == "system":
                base_content = str(msg.get("content") or "").strip()
                if fallback_instruction in base_content:
                    return patched_messages
                merged_content = f"{base_content}\n\n{fallback_instruction}" if base_content else fallback_instruction
                patched_messages[idx] = {**msg, "content": merged_content}
                return patched_messages
        patched_messages.insert(0, {"role": "system", "content": fallback_instruction})
        return patched_messages

    def _build_tool_json_fallback_instruction(self, tools: List[Dict[str, Any]]) -> str:
        converted_tools = self._convert_tools_to_openai_format(tools)
        tool_names = [
            str(tool.get("function", {}).get("name") or "").strip()
            for tool in converted_tools
            if isinstance(tool, dict)
        ]
        tool_names = [name for name in tool_names if name]
        if not tool_names:
            return ""
        example_tool = tool_names[0]
        has_routing_tool = "system.routing" in tool_names
        has_local_business_tool = "system.local_business" in tool_names
        routing_few_shot = (
            "WICHTIG: Du musst Tools ueber JSON aufrufen. Antworte in diesem exakten Format, ohne weiteren Text:\n"
            "{\n"
            '  "name": "system.routing",\n'
            '  "parameters": {\n'
            '    "origin": "Startort",\n'
            '    "destination": "Zielort"\n'
            "  }\n"
            "}"
        )
        local_business_few_shot = (
            "WICHTIG fuer lokale Suche: system.local_business braucht mindestens query und location.\n"
            "Beispiel fuer Restaurantsuche:\n"
            "{\n"
            '  "name": "system.local_business",\n'
            '  "parameters": {\n'
            '    "query": "italienisches Restaurant",\n'
            '    "location": "Berlin Prenzlauer Berg",\n'
            '    "limit": 4\n'
            "  }\n"
            "}"
        )
        instruction = (
            "TOOL-CALL FALLBACK FORMAT (JSON ONLY): Wenn ein Tool noetig ist, antworte NICHT frei, "
            "sondern mit exakt einem JSON-Objekt in einer Zeile.\n"
            "Erlaubte Struktur: {\"name\": \"<tool_name>\", \"parameters\": {...}}\n"
            "Regeln:\n"
            "1) Keine Markdown-Blocks, kein ```json, kein zusaetzlicher Text.\n"
            f"2) name muss einer der erlaubten Tools sein: {', '.join(tool_names)}\n"
            "3) parameters muss ein JSON-Objekt sein und alle Pflichtfelder enthalten.\n"
        )
        if has_routing_tool:
            instruction += f"4) {routing_few_shot}\n"
        if has_local_business_tool:
            instruction += f"5) {local_business_few_shot}\n"
        instruction += (
            "Few-shot Beispiel A (Tool-Aufruf):\n"
            f'{{"name": "{example_tool}", "parameters": {{"query": "Aktuelle Nachrichten zu KI"}}}}\n'
            "Few-shot Beispiel B (kein Tool noetig):\n"
            "Wenn kein Tool noetig ist, antworte normal als Text."
        )
        return instruction

    def _inject_json_response_wrapper(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Injiziert einen System-Prompt, der das Modell anweist, normalen Text als JSON zu verpacken.

        Wird verwendet wenn format=json gesetzt ist, aber keine Tools erzwungen werden.
        Das Modell soll den Text im Format {"response": "Hier ist meine Antwort..."} zurückgeben.
        """
        wrapper_instruction = (
            "WICHTIG: Deine Antwort muss als valides JSON-Objekt zurückgegeben werden. "
            "Verwende dieses Format:\n"
            '{"response": "Hier ist meine Antwort als normaler Text..."}\n'
            "Regeln:\n"
            "1) Antworte ausschliesslich mit dem JSON-Objekt, ohne Markdown-Blocks oder ```json.\n"
            "2) Der Wert von 'response' sollte deine normale, natuerliche Antwort enthalten.\n"
            "3) Wenn du keinen Text hast, nutze: {\"response\": \"\"}"
        )
        patched_messages = list(messages)
        # Prüfe ob bereits ein System-Prompt mit Wrapper-Anweisung existiert
        has_wrapper = any(
            str(msg.get("role") or "") == "system" and
            "WICHTIG: Deine Antwort muss als valides JSON-Objekt" in str(msg.get("content") or "")
            for msg in patched_messages
        )
        if not has_wrapper:
            patched_messages.insert(0, {"role": "system", "content": wrapper_instruction})
        return patched_messages

    @staticmethod
    def _normalize_structured_json_text(content: Any) -> str:
        text = str(content or "").strip()
        if not text:
            return "{}"
        text = text.replace("\ufeff", "")
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text, flags=re.IGNORECASE)
        text = text.strip()
        if text.startswith("`") and text.endswith("`"):
            text = text.strip("`").strip()
        return text or "{}"

    @classmethod
    def _extract_first_json_object(cls, content: Any) -> str:
        text = cls._normalize_structured_json_text(content)
        if text.startswith("{") and text.endswith("}"):
            return text
        depth = 0
        start_idx: Optional[int] = None
        for idx, char in enumerate(text):
            if char == "{":
                if depth == 0:
                    start_idx = idx
                depth += 1
            elif char == "}":
                if depth <= 0:
                    continue
                depth -= 1
                if depth == 0 and start_idx is not None:
                    return text[start_idx: idx + 1].strip()
        return text

    @classmethod
    def _get_ollama_openai_base_url(cls, node_id: Optional[str] = None) -> str:
        config = load_config_data()
        normalized = None
        if isinstance(config, dict):
            nodes = config.get("ollama_nodes")
            if isinstance(nodes, list):
                active_node = None
                normalized_node_id = str(node_id or "").strip()
                if normalized_node_id:
                    active_node = next(
                        (
                            node
                            for node in nodes
                            if isinstance(node, dict)
                            and str(node.get("id") or "").strip() == normalized_node_id
                            and cls._normalize_ollama_base_url(node.get("url"))
                        ),
                        None,
                    )
                if active_node is None:
                    active_node = next(
                        (
                            node
                            for node in nodes
                            if isinstance(node, dict)
                            and bool(node.get("active"))
                            and cls._normalize_ollama_base_url(node.get("url"))
                        ),
                        None,
                    )
                if active_node is None:
                    active_node = next(
                        (
                            node
                            for node in nodes
                            if isinstance(node, dict)
                            and cls._normalize_ollama_base_url(node.get("url"))
                        ),
                        None,
                    )
                if isinstance(active_node, dict):
                    normalized = cls._normalize_ollama_base_url(active_node.get("url"))
            if not normalized:
                configured = config.get("ollama_base_url")
                normalized = cls._normalize_ollama_base_url(configured)
        base_url = normalized or DEFAULT_OLLAMA_BASE_URL
        if base_url.endswith("/v1"):
            return base_url
        return f"{base_url}/v1"

    @staticmethod
    def _normalize_ollama_base_url(value: Any) -> Optional[str]:
        raw = str(value or "").strip()
        if not raw:
            return None
        if not raw.startswith("http://") and not raw.startswith("https://"):
            raw = f"http://{raw}"
        return raw.rstrip("/")

    @staticmethod
    def _split_model_node_identifier(model_id: str) -> tuple[str, Optional[str]]:
        raw = str(model_id or "").strip()
        if not raw:
            return "", None
        if "@" not in raw:
            return raw, None
        base_model, node_id = raw.rsplit("@", 1)
        cleaned_model = str(base_model or "").strip() or raw
        cleaned_node = str(node_id or "").strip() or None
        return cleaned_model, cleaned_node
