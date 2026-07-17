from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import openai
import pytest

from backend.llm_providers.openrouter.gateway import OpenRouterGateway
from backend.llm_providers.openrouter.service import (
    OpenRouterAuthenticationRejected,
    OpenRouterMalformedResponseError,
    OpenRouterModelIdentityError,
    OpenRouterServiceProvider,
)
from backend.services.openrouter_credential_authority import (
    OpenRouterCredentialBinding,
    OpenRouterRuntimeCredential,
)


MODEL = "vendor/model-2026-07-17"
SENTINEL = "TEST_OPENROUTER_PROVIDER_SECRET"


class Reader:
    def __init__(self, credential=None):
        self.credential = credential
        self.calls = 0

    def get_eligible_credential(self):
        self.calls += 1
        return self.credential


class Invalidator:
    def __init__(self):
        self.bindings = []

    def invalidate_authenticated_rejection(self, binding):
        self.bindings.append(binding)
        return True


class FakeService:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    async def generate_response(self, *args, **kwargs):
        if args:
            kwargs = {
                **dict(zip(("api_key", "model", "messages"), args)),
                **kwargs,
            }
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return dict(outcome)

    def prepare_history_for_second_call(self, chat_history, raw_assistant_response, tool_results):
        return list(chat_history) + [raw_assistant_response] + list(tool_results)


class FakeAsyncStream:
    def __init__(self, outcomes):
        self.outcomes = iter(outcomes)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            outcome = next(self.outcomes)
        except StopIteration:
            raise StopAsyncIteration
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class FakeStreamingService:
    def __init__(self, outcome):
        self.outcome = outcome
        self.calls = []

    async def generate_response_stream(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        for event in self.outcome:
            yield event


def credential():
    return OpenRouterRuntimeCredential(
        api_key=SENTINEL,
        binding=OpenRouterCredentialBinding("a" * 64),
    )


def catalog(_provider):
    return [{"id": MODEL, "provider": "openrouter"}]


@pytest.mark.asyncio
async def test_eligibility_fails_before_catalog_and_transport():
    catalog_calls = []
    service = FakeService([{"type": "text", "text": "must not run"}])
    gateway = OpenRouterGateway(
        service=service,
        eligibility_reader=Reader(None),
        invalidator=Invalidator(),
        catalog_loader=lambda provider: catalog_calls.append(provider) or [],
    )

    result = await gateway.generate_once(model=MODEL, messages=[])

    assert result["error_code"] == "OPENROUTER_CREDENTIAL_INELIGIBLE"
    assert catalog_calls == []
    assert service.calls == []


@pytest.mark.asyncio
async def test_exact_certified_model_is_sent_once_and_caller_key_is_ignored():
    service = FakeService(
        [{"type": "text", "text": "ok", "model": MODEL, "response_model": MODEL}]
    )
    gateway = OpenRouterGateway(
        service=service,
        eligibility_reader=Reader(credential()),
        invalidator=Invalidator(),
        catalog_loader=catalog,
    )

    result = await gateway.reason_and_respond(
        provider="openrouter",
        model=MODEL,
        api_key="CALLER_KEY_MUST_NOT_BE_USED",
        chat_history=[{"role": "user", "content": "hello"}],
        context_manager=None,
        db=None,
        user_prompt="hello",
        chat_id=1,
        tool_executor=AsyncMock(),
        disable_tools=True,
    )

    assert result["text"] == "ok"
    assert len(service.calls) == 1
    assert service.calls[0]["api_key"] == SENTINEL
    assert service.calls[0]["model"] == MODEL


@pytest.mark.asyncio
async def test_typed_auth_rejection_invalidates_once_without_retry():
    invalidator = Invalidator()
    service = FakeService([OpenRouterAuthenticationRejected("rejected")])
    gateway = OpenRouterGateway(
        service=service,
        eligibility_reader=Reader(credential()),
        invalidator=invalidator,
        catalog_loader=catalog,
    )

    result = await gateway.generate_once(model=MODEL, messages=[])

    assert result["error_code"] == "OPENROUTER_AUTHENTICATION_REJECTED"
    assert len(service.calls) == 1
    assert len(invalidator.bindings) == 1
    assert SENTINEL not in str(result)


@pytest.mark.parametrize(
    "failure",
    [
        TimeoutError("timeout"),
        ConnectionError("network"),
        RuntimeError("provider"),
        ValueError("malformed"),
        OpenRouterModelIdentityError("mismatch"),
    ],
)
@pytest.mark.asyncio
async def test_technical_and_model_failures_never_invalidate_or_retry(failure):
    invalidator = Invalidator()
    service = FakeService([failure])
    gateway = OpenRouterGateway(
        service=service,
        eligibility_reader=Reader(credential()),
        invalidator=invalidator,
        catalog_loader=catalog,
    )

    result = await gateway.generate_once(model=MODEL, messages=[])

    assert len(service.calls) == 1
    assert invalidator.bindings == []
    assert result["error_code"] in {
        "OPENROUTER_PROVIDER_ERROR",
        "OPENROUTER_MODEL_IDENTITY_MISMATCH",
    }


@pytest.mark.asyncio
async def test_response_identity_failure_happens_before_any_tool_execution():
    service = FakeService([OpenRouterModelIdentityError("mismatch")])
    executor = SimpleNamespace(execute_tool_calls=AsyncMock())
    gateway = OpenRouterGateway(
        service=service,
        eligibility_reader=Reader(credential()),
        invalidator=Invalidator(),
        catalog_loader=catalog,
    )

    result = await gateway.reason_and_respond(
        provider="openrouter",
        model=MODEL,
        api_key="",
        chat_history=[{"role": "user", "content": "do something"}],
        context_manager=None,
        db=None,
        user_prompt="do something",
        chat_id=1,
        tool_executor=executor,
        disable_tools=True,
    )

    assert result["error_code"] == "OPENROUTER_MODEL_IDENTITY_MISMATCH"
    executor.execute_tool_calls.assert_not_awaited()


@pytest.mark.asyncio
async def test_exact_model_stays_pinned_across_tool_and_synthesis_rounds():
    raw_tool_message = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "system_weather",
                    "arguments": '{"city":"Berlin"}',
                },
            }
        ],
    }
    service = FakeService(
        [
            {
                "type": "tool_code",
                "tool_calls": raw_tool_message["tool_calls"],
                "raw_assistant_response": raw_tool_message,
                "openrouter_telemetry": {
                    "response_model": MODEL,
                    "prompt_tokens": 11,
                },
            },
            {
                "type": "text",
                "text": "done",
                "response_model": MODEL,
                "openrouter_telemetry": {
                    "response_model": MODEL,
                    "prompt_tokens": 7,
                },
            },
        ]
    )
    executor = SimpleNamespace(
        execute_tool_calls=AsyncMock(
            return_value=[
                {
                    "role": "tool",
                    "tool_call_id": "call_1",
                    "name": "system.weather",
                    "content": "{}",
                }
            ]
        )
    )
    gateway = OpenRouterGateway(
        service=service,
        eligibility_reader=Reader(credential()),
        invalidator=Invalidator(),
        catalog_loader=catalog,
    )

    result = await gateway.reason_and_respond(
        provider="openrouter",
        model=MODEL,
        api_key="",
        chat_history=[{"role": "user", "content": "weather"}],
        context_manager=None,
        db=None,
        user_prompt="weather",
        chat_id=1,
        tool_executor=executor,
        allowed_skill_ids=["system.weather"],
        max_tool_rounds=2,
        openrouter_turn_id="turn-telemetry-1",
        current_round=1,
    )

    assert result["text"] == "done"
    assert [call["model"] for call in service.calls] == [MODEL, MODEL]
    assert [call["api_key"] for call in service.calls] == [SENTINEL, SENTINEL]
    assert result["_openrouter_turn_id"] == "turn-telemetry-1"
    assert result["_openrouter_telemetry_records"] == [
        {"response_model": MODEL, "prompt_tokens": 11, "round": 2},
        {"response_model": MODEL, "prompt_tokens": 7, "round": 3},
    ]
    executor.execute_tool_calls.assert_awaited_once()


class FakeCompletionClient:
    def __init__(self, outcome, recorder):
        self._outcome = outcome
        self._recorder = recorder
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    async def create(self, **kwargs):
        self._recorder.append(kwargs)
        if isinstance(self._outcome, BaseException):
            raise self._outcome
        return self._outcome


def usage(payload):
    return SimpleNamespace(model_dump=lambda: dict(payload))


def response(model=MODEL, text="ok", usage_payload=None):
    message = SimpleNamespace(content=text, tool_calls=None)
    return SimpleNamespace(
        model=model,
        choices=[SimpleNamespace(message=message, finish_reason="stop")],
        usage=usage(usage_payload) if usage_payload is not None else None,
    )


def stream_chunk(*, model=MODEL, text=None, finish_reason=None, usage_payload=None):
    return SimpleNamespace(
        model=model,
        usage=usage(usage_payload) if usage_payload is not None else None,
        choices=[
            SimpleNamespace(
                delta=SimpleNamespace(content=text, tool_calls=None),
                finish_reason=finish_reason,
            )
        ],
    )


async def collect_stream(stream):
    return [event async for event in stream]


@pytest.mark.asyncio
async def test_service_sets_openrouter_base_url_zero_retries_and_checks_response_model():
    client_kwargs = []
    requests = []

    def factory(**kwargs):
        client_kwargs.append(kwargs)
        return FakeCompletionClient(response(), requests)

    result = await OpenRouterServiceProvider(client_factory=factory).generate_response(
        api_key=SENTINEL,
        model=MODEL,
        messages=[{"role": "user", "content": "hello"}],
    )

    assert result["response_model"] == MODEL
    assert client_kwargs == [
        {
            "api_key": SENTINEL,
            "base_url": "https://openrouter.ai/api/v1",
            "timeout": 180.0,
            "max_retries": 0,
        }
    ]
    assert len(requests) == 1
    assert requests[0]["model"] == MODEL


@pytest.mark.asyncio
async def test_service_propagates_authoritative_nonstream_telemetry():
    service = OpenRouterServiceProvider(
        client_factory=lambda **_kwargs: FakeCompletionClient(
            response(
                usage_payload={
                    "prompt_tokens": 3,
                    "completion_tokens": 0,
                    "total_tokens": 3,
                    "prompt_tokens_details": {"cached_tokens": 0},
                    "cost": 0.0,
                }
            ),
            [],
        )
    )

    result = await service.generate_response(
        api_key=SENTINEL,
        model=MODEL,
        messages=[],
    )

    assert result["openrouter_telemetry"]["response_model"] == MODEL
    assert result["openrouter_telemetry"]["completion_tokens"] == 0
    assert result["openrouter_telemetry"]["cached_tokens"] == 0
    assert result["openrouter_telemetry"]["credits_cost"] == 0.0
    assert result["openrouter_telemetry"]["reasoning_tokens"] is None


@pytest.mark.asyncio
async def test_service_rejects_missing_or_mismatched_response_model():
    for actual in (None, "other/model"):
        service = OpenRouterServiceProvider(
            client_factory=lambda **_kwargs: FakeCompletionClient(response(actual), [])
        )
        with pytest.raises(OpenRouterModelIdentityError):
            await service.generate_response(
                api_key=SENTINEL,
                model=MODEL,
                messages=[],
            )


@pytest.mark.asyncio
async def test_service_maps_only_sdk_authentication_error_to_typed_rejection():
    request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    auth_error = openai.AuthenticationError(
        "unauthorized",
        response=httpx.Response(401, request=request),
        body={"error": {"message": "rejected"}},
    )
    service = OpenRouterServiceProvider(
        client_factory=lambda **_kwargs: FakeCompletionClient(auth_error, [])
    )

    with pytest.raises(OpenRouterAuthenticationRejected):
        await service.generate_response(api_key=SENTINEL, model=MODEL, messages=[])

    technical = OpenRouterServiceProvider(
        client_factory=lambda **_kwargs: FakeCompletionClient(
            openai.RateLimitError(
                "limited",
                response=httpx.Response(429, request=request),
                body={"error": {}},
            ),
            [],
        )
    )
    with pytest.raises(openai.RateLimitError):
        await technical.generate_response(api_key=SENTINEL, model=MODEL, messages=[])


@pytest.mark.asyncio
async def test_service_stream_requires_exact_identity_and_completed_upstream_stream():
    empty = OpenRouterServiceProvider(
        client_factory=lambda **_kwargs: FakeCompletionClient(FakeAsyncStream([]), [])
    )
    with pytest.raises(OpenRouterModelIdentityError):
        await collect_stream(
            empty.generate_response_stream(api_key=SENTINEL, model=MODEL, messages=[])
        )

    incomplete = OpenRouterServiceProvider(
        client_factory=lambda **_kwargs: FakeCompletionClient(
            FakeAsyncStream([stream_chunk(text="partial")]),
            [],
        )
    )
    with pytest.raises(OpenRouterMalformedResponseError):
        await collect_stream(
            incomplete.generate_response_stream(
                api_key=SENTINEL,
                model=MODEL,
                messages=[],
            )
        )

    mismatch = OpenRouterServiceProvider(
        client_factory=lambda **_kwargs: FakeCompletionClient(
            FakeAsyncStream([stream_chunk(model="other/model", finish_reason="stop")]),
            [],
        )
    )
    with pytest.raises(OpenRouterModelIdentityError):
        await collect_stream(
            mismatch.generate_response_stream(api_key=SENTINEL, model=MODEL, messages=[])
        )

    complete = OpenRouterServiceProvider(
        client_factory=lambda **_kwargs: FakeCompletionClient(
            FakeAsyncStream(
                [
                    stream_chunk(text="ok"),
                    stream_chunk(finish_reason="stop"),
                ]
            ),
            [],
        )
    )
    events = await collect_stream(
        complete.generate_response_stream(api_key=SENTINEL, model=MODEL, messages=[])
    )
    assert [event.type for event in events] == ["text_delta", "finish", "done"]


@pytest.mark.asyncio
async def test_service_stream_emits_authoritative_telemetry_before_completion_proof():
    complete = OpenRouterServiceProvider(
        client_factory=lambda **_kwargs: FakeCompletionClient(
            FakeAsyncStream(
                [
                    stream_chunk(
                        usage_payload={
                            "prompt_tokens": 5,
                            "completion_tokens": 0,
                            "total_tokens": 5,
                            "cost": 0.0,
                        }
                    ),
                    stream_chunk(finish_reason="stop"),
                ]
            ),
            [],
        )
    )

    events = await collect_stream(
        complete.generate_response_stream(api_key=SENTINEL, model=MODEL, messages=[])
    )

    assert [event.type for event in events] == ["usage", "finish", "done"]
    telemetry = events[0].content["openrouter_telemetry"]
    assert telemetry["response_model"] == MODEL
    assert telemetry["completion_tokens"] == 0
    assert telemetry["credits_cost"] == 0.0
    assert telemetry["cached_tokens"] is None


@pytest.mark.asyncio
async def test_service_stream_maps_sdk_auth_rejection_without_replay():
    request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    auth_error = openai.AuthenticationError(
        "unauthorized",
        response=httpx.Response(401, request=request),
        body={"error": {"message": "rejected"}},
    )
    requests = []
    service = OpenRouterServiceProvider(
        client_factory=lambda **_kwargs: FakeCompletionClient(
            FakeAsyncStream([auth_error]),
            requests,
        )
    )

    with pytest.raises(OpenRouterAuthenticationRejected):
        await collect_stream(
            service.generate_response_stream(api_key=SENTINEL, model=MODEL, messages=[])
        )
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_gateway_stream_auth_rejection_invalidates_once_without_retry():
    invalidator = Invalidator()
    service = FakeStreamingService(OpenRouterAuthenticationRejected("rejected"))
    gateway = OpenRouterGateway(
        service=service,
        eligibility_reader=Reader(credential()),
        invalidator=invalidator,
        catalog_loader=catalog,
    )

    events = await collect_stream(gateway.stream(model=MODEL, messages=[]))

    assert len(service.calls) == 1
    assert len(invalidator.bindings) == 1
    assert [event.type for event in events] == ["error"]
    assert events[0].metadata["error_code"] == "OPENROUTER_AUTHENTICATION_REJECTED"
    assert SENTINEL not in str(events)


@pytest.mark.parametrize(
    ("failure", "expected_code"),
    [
        (
            OpenRouterModelIdentityError("mismatch"),
            "OPENROUTER_MODEL_IDENTITY_MISMATCH",
        ),
        (
            OpenRouterMalformedResponseError("incomplete"),
            "OPENROUTER_MALFORMED_RESPONSE",
        ),
        (TimeoutError("interrupted"), "OPENROUTER_PROVIDER_ERROR"),
    ],
)
@pytest.mark.asyncio
async def test_gateway_stream_non_auth_failures_are_terminal_and_state_neutral(
    failure,
    expected_code,
):
    invalidator = Invalidator()
    service = FakeStreamingService(failure)
    gateway = OpenRouterGateway(
        service=service,
        eligibility_reader=Reader(credential()),
        invalidator=invalidator,
        catalog_loader=catalog,
    )

    events = await collect_stream(gateway.stream(model=MODEL, messages=[]))

    assert len(service.calls) == 1
    assert invalidator.bindings == []
    assert [event.type for event in events] == ["error"]
    assert events[0].metadata["error_code"] == expected_code
