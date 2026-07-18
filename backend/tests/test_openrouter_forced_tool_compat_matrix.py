"""Offline regression matrix for OpenRouter forced-tool family compat.

Hard families (live evidence):
- Qwen: named tool_choice + reasoning.effort=none
- Kimi / GLM: tool_choice=required + tools narrowed to forced tool

Covers non-stream and stream request shaping for every certified catalog id
in those families so a catalog expansion cannot silently drop the fix.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.llm_providers.openrouter.service import OpenRouterServiceProvider


SENTINEL = "TEST_OPENROUTER_FORCED_TOOL_MATRIX_SECRET"

WEATHER_TOOL = {
    "name": "system.weather",
    "description": "Get weather",
    "parameters": {
        "type": "object",
        "properties": {"location": {"type": "string"}},
        "required": ["location"],
    },
}
EXTRA_TOOL = {
    "name": "system.websearch",
    "description": "Search",
    "parameters": {"type": "object", "properties": {}},
}

# Expectation: ("qwen_named" | "required_narrow")
HARD_FAMILY_MODELS = (
    ("qwen/qwen3.6-flash", "qwen_named"),
    ("qwen/qwen3.7-plus", "qwen_named"),
    ("qwen/qwen3.7-max", "qwen_named"),
    ("moonshotai/kimi-k2.6", "required_narrow"),
    ("moonshotai/kimi-k3", "required_narrow"),
    ("z-ai/glm-4.7-flash", "required_narrow"),
    ("z-ai/glm-5.2", "required_narrow"),
)


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


class FakeAsyncStream:
    def __init__(self, outcomes):
        self.outcomes = iter(outcomes)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            outcome = next(self.outcomes)
        except StopIteration as exc:
            raise StopAsyncIteration from exc
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def _response(model: str):
    message = SimpleNamespace(content="ok", tool_calls=None)
    return SimpleNamespace(
        model=model,
        choices=[SimpleNamespace(message=message, finish_reason="stop")],
        usage=None,
    )


def _stream_chunk(*, model: str):
    return SimpleNamespace(
        model=model,
        usage=None,
        choices=[
            SimpleNamespace(
                delta=SimpleNamespace(content="ok", tool_calls=None),
                finish_reason="stop",
            )
        ],
    )


def _tool_names(payload: dict) -> list[str]:
    names: list[str] = []
    for item in payload.get("tools") or []:
        if not isinstance(item, dict):
            continue
        fn = item.get("function") if isinstance(item.get("function"), dict) else {}
        name = str(fn.get("name") or item.get("name") or "").strip()
        if name:
            names.append(name)
    return names


def _assert_compat(payload: dict, *, model: str, mode: str) -> None:
    if mode == "qwen_named":
        assert payload["tool_choice"] == {
            "type": "function",
            "function": {"name": "system_weather"},
        }
        assert payload.get("extra_body") == {"reasoning": {"effort": "none"}}
        assert "system_weather" in _tool_names(payload)
        return

    assert mode == "required_narrow"
    assert payload["tool_choice"] == "required"
    assert "extra_body" not in payload
    assert _tool_names(payload) == ["system_weather"], model


@pytest.mark.asyncio
@pytest.mark.parametrize("model,mode", HARD_FAMILY_MODELS)
async def test_forced_tool_compat_nonstream_matrix(model: str, mode: str):
    requests: list[dict] = []
    service = OpenRouterServiceProvider(
        client_factory=lambda **_kwargs: FakeCompletionClient(
            _response(model),
            requests,
        )
    )

    await service.generate_response(
        api_key=SENTINEL,
        model=model,
        messages=[{"role": "user", "content": "weather?"}],
        tools=[WEATHER_TOOL, EXTRA_TOOL],
        force_tool_name="system.weather",
    )

    assert len(requests) == 1
    _assert_compat(requests[0], model=model, mode=mode)


@pytest.mark.asyncio
@pytest.mark.parametrize("model,mode", HARD_FAMILY_MODELS)
async def test_forced_tool_compat_stream_matrix(model: str, mode: str):
    requests: list[dict] = []
    service = OpenRouterServiceProvider(
        client_factory=lambda **_kwargs: FakeCompletionClient(
            FakeAsyncStream([_stream_chunk(model=model)]),
            requests,
        )
    )

    events = [
        event
        async for event in service.generate_response_stream(
            api_key=SENTINEL,
            model=model,
            messages=[{"role": "user", "content": "weather?"}],
            tools=[WEATHER_TOOL, EXTRA_TOOL],
            force_tool_name="system.weather",
        )
    ]
    assert events
    assert len(requests) == 1
    _assert_compat(requests[0], model=model, mode=mode)


def test_hard_family_matrix_covers_certified_catalog_ids():
    """Guard: certified hard-family ids must stay in the offline matrix."""
    from pathlib import Path
    import json

    catalog_path = Path(__file__).resolve().parents[1] / "config" / "model_catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    certified_hard = {
        str(row.get("id") or "").strip()
        for row in catalog
        if isinstance(row, dict)
        and str(row.get("provider") or "").lower() == "openrouter"
        and (
            str(row.get("id") or "").startswith("qwen/")
            or str(row.get("id") or "").startswith("moonshotai/")
            or str(row.get("id") or "").startswith("z-ai/")
        )
    }
    matrix_ids = {model for model, _mode in HARD_FAMILY_MODELS}
    missing = sorted(certified_hard - matrix_ids)
    assert not missing, f"certified hard-family models missing from matrix: {missing}"
