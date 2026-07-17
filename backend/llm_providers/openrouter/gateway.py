"""Fail-closed OpenRouter gateway with exact-key and exact-model enforcement."""

from __future__ import annotations

from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple

from backend.llm_providers.openrouter.service import (
    OpenRouterAuthenticationRejected,
    OpenRouterMalformedResponseError,
    OpenRouterModelIdentityError,
    OpenRouterServiceProvider,
)
from backend.llm_providers.shared.tool_loop_runner import (
    NonToolResponseAction,
    ToolLoopContext,
    ToolLoopRunner,
)
from backend.llm_providers.transports.openai_compat import OpenAICompatTransport
from backend.services.model_catalog import get_models_by_provider
from backend.services.openrouter_credential_authority import (
    OpenRouterCredentialBinding,
    OpenRouterRuntimeCredential,
    OpenRouterRuntimeEligibilityReader,
    OpenRouterRuntimeInvalidator,
    get_openrouter_runtime_invalidator,
    get_openrouter_runtime_reader,
)
from backend.services.ops_kill_switches import provider_access_decision
from backend.services.orchestrator.stream_protocol import StreamEvent


class OpenRouterGateway:
    """Dedicated provider silo; it never consumes a caller-supplied credential."""

    def __init__(
        self,
        *,
        service: Optional[OpenRouterServiceProvider] = None,
        eligibility_reader: Optional[OpenRouterRuntimeEligibilityReader] = None,
        invalidator: Optional[OpenRouterRuntimeInvalidator] = None,
        catalog_loader: Optional[Callable[[str], List[Dict[str, Any]]]] = None,
    ) -> None:
        self.service = service or OpenRouterServiceProvider()
        self.transport = OpenAICompatTransport(self.service)
        self._eligibility_reader = eligibility_reader or get_openrouter_runtime_reader()
        self._invalidator = invalidator or get_openrouter_runtime_invalidator()
        self._catalog_loader = catalog_loader or get_models_by_provider

    @staticmethod
    def _error(code: str, message: str) -> Dict[str, Any]:
        return {
            "type": "error",
            "text": "",
            "content": "",
            "error": message,
            "error_code": code,
            "provider": "openrouter",
        }

    @staticmethod
    def _certified_ids(entries: List[Dict[str, Any]]) -> set[str]:
        return {
            str(entry.get("id") or "").strip()
            for entry in entries
            if isinstance(entry, dict) and str(entry.get("id") or "").strip()
        }

    def _authorize(self, model: str) -> Tuple[Optional[OpenRouterRuntimeCredential], Optional[Dict[str, Any]]]:
        credential = self._eligibility_reader.get_eligible_credential()
        if credential is None:
            return None, self._error(
                "OPENROUTER_CREDENTIAL_INELIGIBLE",
                "OpenRouter credential is not eligible for chat.",
            )

        provider_gate = provider_access_decision("openrouter")
        if provider_gate.disabled:
            return None, self._error(provider_gate.code, provider_gate.message)

        selected_model = str(model or "").strip()
        if not selected_model or "latest" in {
            token
            for token in selected_model.lower().replace("/", " ").replace(":", " ").replace("-", " ").split()
        }:
            return None, self._error(
                "OPENROUTER_MODEL_NOT_CERTIFIED",
                "Selected OpenRouter model is not certified.",
            )
        certified_ids = self._certified_ids(self._catalog_loader("openrouter"))
        if selected_model not in certified_ids:
            return None, self._error(
                "OPENROUTER_MODEL_NOT_CERTIFIED",
                "Selected OpenRouter model is not certified.",
            )
        return credential, None

    def _invalidate(self, binding: OpenRouterCredentialBinding) -> None:
        try:
            self._invalidator.invalidate_authenticated_rejection(binding)
        except Exception:
            # The turn remains terminal and must never retry the provider.
            return

    async def _send_authorized_round(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        credential, error = self._authorize(model)
        if credential is None:
            return error or self._error(
                "OPENROUTER_CREDENTIAL_INELIGIBLE",
                "OpenRouter credential is not eligible for chat.",
            )
        try:
            return await self.transport.send(
                api_key=credential.api_key,
                model=model,
                messages=messages,
                tools=tools,
                **kwargs,
            )
        except OpenRouterAuthenticationRejected:
            self._invalidate(credential.binding)
            return self._error(
                "OPENROUTER_AUTHENTICATION_REJECTED",
                "OpenRouter rejected the request credential.",
            )
        except OpenRouterModelIdentityError:
            return self._error(
                "OPENROUTER_MODEL_IDENTITY_MISMATCH",
                "OpenRouter returned an unexpected model identity.",
            )
        except OpenRouterMalformedResponseError:
            return self._error(
                "OPENROUTER_MALFORMED_RESPONSE",
                "OpenRouter returned an invalid response.",
            )
        except Exception:
            return self._error(
                "OPENROUTER_PROVIDER_ERROR",
                "OpenRouter could not complete the current turn.",
            )

    async def generate_once(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return await self._send_authorized_round(
            model=model,
            messages=messages,
            tools=tools,
            **kwargs,
        )

    async def reason_and_respond(
        self,
        provider: str,
        model: str,
        api_key: str,
        chat_history: List[Dict[str, Any]],
        context_manager: Any,
        db: Any,
        user_prompt: str,
        chat_id: int,
        tool_executor: Any,
        allowed_skill_ids: Optional[List[str]] = None,
        max_tool_rounds: int = 5,
        tools_override: Optional[List[Dict[str, Any]]] = None,
        disable_tools: bool = False,
        image_data: Optional[str] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None,
        force_tool_name: Optional[str] = None,
        openrouter_turn_id: Optional[str] = None,
        current_round: int = 0,
        **_: Any,
    ) -> Dict[str, Any]:
        del api_key, context_manager, db, chat_id
        if str(provider or "").strip().lower() != "openrouter":
            return self._error(
                "OPENROUTER_PROVIDER_MISMATCH",
                "OpenRouter gateway received a mismatched provider.",
            )

        if tool_results is not None:
            response = await self._send_authorized_round(
                model=model,
                messages=list(chat_history),
                tools=None,
            )
            telemetry = response.get("openrouter_telemetry")
            if isinstance(telemetry, dict):
                response["_openrouter_telemetry_records"] = [
                    {
                        **telemetry,
                        "round": max(0, int(current_round)) + 1,
                    }
                ]
                response["_openrouter_turn_id"] = str(openrouter_turn_id or "")
            return response

        gateway = self
        telemetry_records: List[Dict[str, Any]] = []

        class _AuthorizedRoundService:
            async def generate_response(self, **kwargs: Any) -> Dict[str, Any]:
                kwargs.pop("api_key", None)
                return await gateway._send_authorized_round(**kwargs)

            def prepare_history_for_second_call(self, **kwargs: Any) -> List[Dict[str, Any]]:
                return gateway.service.prepare_history_for_second_call(**kwargs)

        async def _handle_non_tool_response(
            response: Dict[str, Any],
            context: ToolLoopContext,
            _round_force: Optional[str],
        ) -> NonToolResponseAction:
            response.setdefault("provider", "openrouter")
            response.setdefault("model", context.model)
            response["_internal_tool_results"] = list(context.all_tool_results)
            response["_openrouter_telemetry_records"] = list(telemetry_records)
            response["_openrouter_turn_id"] = str(openrouter_turn_id or "")
            return NonToolResponseAction(kind="return", response=response)

        def _capture_round_telemetry(
            response: Dict[str, Any],
            round_context: ToolLoopContext,
        ) -> None:
            telemetry = response.get("openrouter_telemetry")
            if not isinstance(telemetry, dict):
                return
            telemetry_records.append(
                {
                    **telemetry,
                    "round": (
                        max(0, int(current_round))
                        + int(round_context.current_round)
                    ),
                }
            )

        context = ToolLoopContext(
            provider="openrouter",
            model=model,
            api_key="",
            chat_history=[dict(message) for message in chat_history],
            user_prompt=user_prompt,
            allowed_skill_ids=allowed_skill_ids,
            tool_executor=tool_executor,
            max_tool_rounds=max(1, int(max_tool_rounds)),
            image_data=image_data,
            force_tool_name=force_tool_name,
        )

        filter_tools = None
        build_tools = None
        if disable_tools:
            filter_tools = lambda _ids: []
            build_tools = lambda tools: list(tools)
        elif tools_override is not None:
            filter_tools = lambda _ids: list(tools_override)
            build_tools = lambda tools: list(tools)

        return await ToolLoopRunner().run(
            service=_AuthorizedRoundService(),
            context=context,
            sanitize_generate_response_kwargs=lambda kwargs, *keys: {
                key: value for key, value in dict(kwargs or {}).items() if key not in keys
            },
            prepare_history_for_second_call=self.service.prepare_history_for_second_call,
            handle_non_tool_response=_handle_non_tool_response,
            filter_tools_by_skill_ids=filter_tools,
            build_tool_definitions_for_llm=build_tools,
            resolve_execution_model=lambda current: (current.model, False),
            on_round_response=_capture_round_telemetry,
        )

    async def stream(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        force_tool_name: Optional[str] = None,
        max_completion_tokens: Optional[int] = None,
    ) -> AsyncIterator[StreamEvent]:
        credential, error = self._authorize(model)
        if credential is None:
            failure = error or self._error(
                "OPENROUTER_CREDENTIAL_INELIGIBLE",
                "OpenRouter credential is not eligible for chat.",
            )
            yield StreamEvent(
                type="error",
                content=failure["error"],
                metadata={"fatal": True, "error_code": failure["error_code"]},
            )
            return

        try:
            async for event in self.service.generate_response_stream(
                api_key=credential.api_key,
                model=model,
                messages=messages,
                tools=tools,
                force_tool_name=force_tool_name,
                max_completion_tokens=max_completion_tokens,
            ):
                yield event
        except OpenRouterAuthenticationRejected:
            self._invalidate(credential.binding)
            yield StreamEvent(
                type="error",
                content="OpenRouter rejected the request credential.",
                metadata={
                    "fatal": True,
                    "error_code": "OPENROUTER_AUTHENTICATION_REJECTED",
                },
            )
        except OpenRouterModelIdentityError:
            yield StreamEvent(
                type="error",
                content="OpenRouter returned an unexpected model identity.",
                metadata={
                    "fatal": True,
                    "error_code": "OPENROUTER_MODEL_IDENTITY_MISMATCH",
                },
            )
        except OpenRouterMalformedResponseError:
            yield StreamEvent(
                type="error",
                content="OpenRouter returned an invalid stream.",
                metadata={
                    "fatal": True,
                    "error_code": "OPENROUTER_MALFORMED_RESPONSE",
                },
            )
        except Exception:
            yield StreamEvent(
                type="error",
                content="OpenRouter could not complete the current turn.",
                metadata={"fatal": True, "error_code": "OPENROUTER_PROVIDER_ERROR"},
            )
