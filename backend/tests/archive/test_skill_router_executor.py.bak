import json
from uuid import UUID
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend import tool_registry
from backend.data.models import SkillTelemetry
from backend.services.skill_router import SkillNotFoundError, skill_router
from backend.services.tool_executor import ToolExecutor


@pytest.fixture(autouse=True)
def _register_tools_once():
    tool_registry.register_all_tools()


@pytest.mark.parametrize(
    "name",
    ["delete_file", "filesystem.delete_file"],
)
def test_skill_router_resolves_legacy_and_skill_names(name: str):
    resolved = skill_router.resolve_tool_name(name)
    assert resolved == "delete_file"


def test_skill_router_raises_for_unknown_skill():
    with pytest.raises(SkillNotFoundError):
        skill_router.resolve_tool_name("imaginary.skill")


def test_skill_router_resolves_openai_safe_alias_for_skill_id():
    resolved = skill_router.resolve_tool_name("system_price_comparison")
    assert resolved == "price_comparison_tool"


@pytest.mark.parametrize(
    "skill_name,expected_legacy",
    [
        ("knowledge.query", "query_knowledge_base"),
        ("knowledge.edit_pdf", "edit_pdf_text_in_place"),
        ("knowledge.hardened_edit", "hardened_edit_pdf"),
        ("system.routing", "get_distance_and_route_tool"),
    ],
)
def test_skill_router_resolves_valid_knowledge_skills(skill_name: str, expected_legacy: str):
    assert skill_router.resolve_tool_name(skill_name) == expected_legacy


@pytest.mark.asyncio
async def test_executor_returns_skill_not_found_contract_for_unknown_call():
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    results = await executor.execute_tool_calls(
        [
            {
                "id": "tc-unknown",
                "function": {"name": "imaginary.skill", "arguments": "{}"},
            }
        ]
    )

    assert len(results) == 1
    payload = json.loads(results[0]["content"])
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "SKILL_NOT_FOUND"


@pytest.mark.asyncio
async def test_executor_blocks_policy_before_dispatch(monkeypatch):
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "REQUIRE_CONSENT",
    )
    executor.execute_tool_call = AsyncMock()

    results = await executor.execute_tool_calls(
        [
            {
                "id": "tc-policy",
                "function": {"name": "filesystem.delete_file", "arguments": "{}"},
            }
        ],
        bypass_policy=False,
    )

    assert executor.execute_tool_call.await_count == 0
    assert len(results) == 1
    payload = json.loads(results[0]["content"])
    assert payload["status"] == "permission_required"
    assert payload["error"]["code"] == "USER_CONSENT_NEEDED"


@pytest.mark.asyncio
async def test_executor_bypass_allows_dispatch_for_skill_name(monkeypatch):
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "REQUIRE_CONSENT",
    )
    executor.execute_tool_call = AsyncMock(
        return_value={
            "role": "tool",
            "name": "filesystem.delete_file",
            "content": json.dumps({"status": "ok", "data": {"deleted": True}}),
        }
    )

    results = await executor.execute_tool_calls(
        [
            {
                "id": "tc-bypass",
                "function": {"name": "filesystem.delete_file", "arguments": "{}"},
            }
        ],
        bypass_policy=True,
    )

    assert executor.execute_tool_call.await_count == 1
    assert len(results) == 1
    payload = json.loads(results[0]["content"])
    assert payload["status"] == "ok"


@pytest.mark.asyncio
@pytest.mark.parametrize("skill_name", ["knowledge.query", "knowledge.edit_pdf", "knowledge.hardened_edit"])
async def test_executor_valid_skill_call_returns_skill_response_contract(monkeypatch, skill_name: str):
    async def _dummy_handler(**_kwargs):
        return {"result": "ok"}
    dummy_tool_def = SimpleNamespace(name="dummy_handler", func=_dummy_handler)

    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.get_tool_definition",
        lambda _name: dummy_tool_def,
    )

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    result = await executor.execute_tool_call(skill_name, {})
    payload = json.loads(result["content"])
    assert payload["status"] == "ok"
    assert payload["data"]["result"] == "ok"


@pytest.mark.asyncio
async def test_executor_dispatches_valid_knowledge_skill_names(monkeypatch):
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )

    executor.execute_tool_call = AsyncMock(
        side_effect=[
            {
                "role": "tool",
                "name": "knowledge.query",
                "content": json.dumps({"status": "ok", "data": {"source": "rag"}}),
            },
            {
                "role": "tool",
                "name": "knowledge.edit_pdf",
                "content": json.dumps({"status": "ok", "data": {"source": "pdf"}}),
            },
        ]
    )

    results = await executor.execute_tool_calls(
        [
            {
                "id": "tc-rag",
                "function": {"name": "knowledge.query", "arguments": "{}"},
            },
            {
                "id": "tc-pdf",
                "function": {"name": "knowledge.edit_pdf", "arguments": "{}"},
            },
        ],
        bypass_policy=False,
    )

    assert executor.execute_tool_call.await_count == 2
    assert len(results) == 2
    first = json.loads(results[0]["content"])
    second = json.loads(results[1]["content"])
    assert first["status"] == "ok"
    assert second["status"] == "ok"


@pytest.mark.asyncio
async def test_executor_returns_missing_content_for_empty_system_create_pdf_content(monkeypatch):
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="ollama",
        model="gemma2:27b",
    )

    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )

    result = await executor.execute_tool_call(
        "system.create_pdf",
        {
            "content": "   ",
            "filename": "schweden.pdf",
            "location": "workspace",
        },
    )

    payload = json.loads(result["content"])
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "MISSING_CONTENT"


@pytest.mark.asyncio
async def test_executor_normalizes_legacy_create_pdf_arguments(monkeypatch):
    captured_args = {}

    async def _fake_create_pdf_from_markdown(**kwargs):
        captured_args.update(kwargs)
        return {"status": "ok", "data": {"accepted": True}}

    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.get_tool_definition",
        lambda _name: SimpleNamespace(
            name="create_pdf_from_markdown",
            func=_fake_create_pdf_from_markdown,
            args_schema=None,
            description="",
        ),
    )
    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    result = await executor.execute_tool_call(
        "system.create_pdf",
        {
            "pdf_filename": "Affen_Bericht.pdf",
            "markdown_content": "![Affe](/user_images/affe.png)\n\nKurzbeschreibung.",
            "include_image": True,
            "location": "Documents",
        },
    )

    payload = json.loads(result["content"])
    assert payload["status"] == "ok"
    assert captured_args["filename"] == "Affen_Bericht.pdf"
    assert captured_args["content"].startswith("![Affe](/user_images/affe.png)")
    assert captured_args["image_path"] == "/user_images/affe.png"


@pytest.mark.asyncio
async def test_executor_blocks_tool_not_allowed_in_phase(monkeypatch):
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="ollama",
        model="llama3.1:8b",
        additional_context={"allowed_skill_ids": ["system.country_info"]},
    )

    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.resolve_tool_name",
        lambda name: "get_distance_and_route_tool" if str(name) == "system.routing" else str(name),
    )
    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )
    executor.execute_tool_call = AsyncMock()

    results = await executor.execute_tool_calls(
        [
            {
                "id": "tc-routing-not-allowed",
                "function": {
                    "name": "system.routing",
                    "arguments": '{"origin":"Tokio","destination":"Kyoto"}',
                },
            }
        ],
        bypass_policy=False,
    )

    assert executor.execute_tool_call.await_count == 0
    assert len(results) == 1
    payload = json.loads(results[0]["content"])
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "TOOL_NOT_ALLOWED_IN_PHASE"
    assert payload["error"]["details"]["allowed_skill_ids"] == ["system.country_info"]
    assert payload["error"]["details"]["requested_skill"] == "system.routing"


@pytest.mark.asyncio
async def test_executor_keeps_registered_legacy_tool_name_lookup(monkeypatch):
    lookup_calls = []

    async def _dummy_handler(**_kwargs):
        return {"result": "ok"}

    def _fake_get_tool_definition(name: str):
        lookup_calls.append(name)
        return SimpleNamespace(name="get_distance_and_route_tool", func=_dummy_handler, args_schema=None)

    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.get_tool_definition",
        _fake_get_tool_definition,
    )

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    result = await executor.execute_tool_call(
        "get_distance_and_route_tool",
        {"origin": "Berlin", "destination": "Hamburg", "mode": "driving"},
    )

    payload = json.loads(result["content"])
    assert payload["status"] == "ok"
    assert lookup_calls == ["get_distance_and_route_tool"]


@pytest.mark.asyncio
async def test_executor_normalizes_unknown_snake_case_name_to_skill_id(monkeypatch):
    lookup_calls = []

    async def _dummy_handler(**_kwargs):
        return {"result": "ok"}

    def _fake_get_tool_definition(name: str):
        lookup_calls.append(name)
        return SimpleNamespace(name="system.routing", func=_dummy_handler, args_schema=None)

    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.get_tool_definition",
        _fake_get_tool_definition,
    )

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    result = await executor.execute_tool_call(
        "system_routing",
        {"origin": "Berlin", "destination": "Hamburg", "mode": "driving"},
    )

    payload = json.loads(result["content"])
    assert payload["status"] == "ok"
    assert lookup_calls == ["system_routing"]


@pytest.mark.asyncio
async def test_executor_maps_openai_style_snake_name_to_registered_tool(monkeypatch):
    lookup_calls = []

    async def _dummy_handler(**_kwargs):
        return {"result": "ok"}

    def _fake_get_tool_definition(name: str):
        lookup_calls.append(name)
        return SimpleNamespace(name="price_comparison_tool", func=_dummy_handler, args_schema=None)

    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.get_tool_definition",
        _fake_get_tool_definition,
    )

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    result = await executor.execute_tool_call(
        "system_price_comparison",
        {"product_name": "Nintendo Switch 2"},
    )

    payload = json.loads(result["content"])
    assert payload["status"] == "ok"
    assert lookup_calls == ["system_price_comparison"]


@pytest.mark.asyncio
async def test_executor_returns_invalid_arguments_contract_for_schema_violation():
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    result = await executor.execute_tool_call(
        "knowledge.edit_pdf",
        {
            "original_filename": "demo.pdf",
            "modifications": "not-a-list",
        },
    )

    payload = json.loads(result["content"])
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "INVALID_ARGUMENTS"


@pytest.mark.asyncio
async def test_executor_executes_legacy_routing_tool_name_without_skill_not_found(monkeypatch):
    async def _fake_geocode(_geolocator, query: str):
        if "Berlin" in str(query):
            return SimpleNamespace(latitude=52.52, longitude=13.40)
        return SimpleNamespace(latitude=53.55, longitude=10.00)

    class _FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {
                "code": "Ok",
                "routes": [{"distance": 250000, "duration": 7200, "legs": []}],
            }

    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )
    monkeypatch.setattr("backend.tools.geo_service._geocode_city_center", _fake_geocode)
    monkeypatch.setattr("backend.tools.geo_service.requests.get", lambda *_args, **_kwargs: _FakeResponse())

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    results = await executor.execute_tool_calls(
        [
            {
                "id": "tc-routing",
                "function": {
                    "name": "get_distance_and_route_tool",
                    "arguments": '{"origin":"Berlin","destination":"Hamburg","mode":"driving"}',
                },
            }
        ],
        bypass_policy=False,
    )

    assert len(results) == 1
    payload = json.loads(results[0]["content"])
    assert payload["status"] == "ok"
    assert payload.get("error") is None
    assert payload["data"]["distance_km"] == 250.0


@pytest.mark.asyncio
async def test_executor_uses_canonical_routing_skill_id_for_telemetry(db_session, monkeypatch, caplog):
    async def _fake_geocode(_geolocator, query: str):
        if "Berlin" in str(query):
            return SimpleNamespace(latitude=52.52, longitude=13.40)
        return SimpleNamespace(latitude=53.55, longitude=10.00)

    class _FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {
                "code": "Ok",
                "routes": [{"distance": 250000, "duration": 7200, "legs": []}],
            }

    caplog.set_level("WARNING", logger="janus_backend")
    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )
    monkeypatch.setattr("backend.tools.geo_service._geocode_city_center", _fake_geocode)
    monkeypatch.setattr("backend.tools.geo_service.requests.get", lambda *_args, **_kwargs: _FakeResponse())

    executor = ToolExecutor(
        db=db_session,
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    results = await executor.execute_tool_calls(
        [
            {
                "id": "tc-routing-canonical",
                "function": {
                    "name": "get_distance_and_route_tool",
                    "arguments": '{"origin":"Berlin","destination":"Hamburg","mode":"driving"}',
                },
            }
        ],
        bypass_policy=False,
    )

    assert len(results) == 1
    payload = json.loads(results[0]["content"])
    assert payload["status"] == "ok"

    latest = db_session.query(SkillTelemetry).order_by(SkillTelemetry.id.desc()).first()
    assert latest is not None
    assert latest.skill_id == "system.routing"
    assert "SKILL-DEPRECATION" not in caplog.text


@pytest.mark.asyncio
async def test_executor_blocks_fourth_call_with_rate_limit(monkeypatch):
    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )
    executor.execute_tool_call = AsyncMock(
        return_value={
            "role": "tool",
            "name": "filesystem.delete_file",
            "content": json.dumps({"status": "ok", "data": {"deleted": True}}),
        }
    )

    calls = [
        {"id": f"tc-del-{idx}", "function": {"name": "filesystem.delete_file", "arguments": "{}"}}
        for idx in range(1, 5)
    ]

    results = await executor.execute_tool_calls(calls, bypass_policy=False)

    assert executor.execute_tool_call.await_count == 3
    assert len(results) == 4
    fourth_payload = json.loads(results[3]["content"])
    assert fourth_payload["status"] == "error"
    assert fourth_payload["error"]["code"] == "RATE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_executor_logs_same_trace_id_for_calls_in_same_turn(db_session, monkeypatch):
    async def _dummy_handler(**_kwargs):
        return {"result": "ok"}

    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.resolve_tool_name",
        lambda name: str(name),
    )
    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.get_tool_definition",
        lambda name: SimpleNamespace(name=str(name), func=_dummy_handler, args_schema=None),
    )
    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )

    executor = ToolExecutor(
        db=db_session,
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
    )

    results = await executor.execute_tool_calls(
        [
            {"id": "tc-list", "function": {"name": "filesystem.list_directory", "arguments": '{"path":"."}'}},
            {"id": "tc-read", "function": {"name": "filesystem.read_file", "arguments": '{"path":"./foo.txt"}'}},
        ],
        bypass_policy=False,
    )

    assert len(results) == 2
    telemetry_rows = (
        db_session.query(SkillTelemetry)
        .order_by(SkillTelemetry.id.desc())
        .limit(2)
        .all()
    )
    assert len(telemetry_rows) == 2

    trace_ids = {row.trace_id for row in telemetry_rows}
    assert len(trace_ids) == 1
    trace_id = next(iter(trace_ids))
    assert trace_id
    UUID(trace_id)


@pytest.mark.asyncio
async def test_internal_call_is_blocked_by_nested_policy(monkeypatch):
    async def _dummy_handler(**_kwargs):
        return {"result": "ok"}

    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.resolve_tool_name",
        lambda name: "delete_file" if str(name) == "filesystem.delete_file" else str(name),
    )
    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.get_tool_definition",
        lambda name: SimpleNamespace(name="delete_file", func=_dummy_handler, args_schema=None),
    )
    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "REQUIRE_CONSENT",
    )

    executor = ToolExecutor(
        db=MagicMock(),
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
        additional_context={"trace_id": "trace-internal-block"},
    )

    result = await executor.call_internal_skill(
        "filesystem.delete_file",
        {"path": "workspace/demo.txt"},
    )

    assert result["status"] == "permission_required"
    assert result["error"]["code"] == "USER_CONSENT_NEEDED"


@pytest.mark.asyncio
async def test_internal_call_keeps_trace_and_marks_telemetry(db_session, monkeypatch):
    async def _dummy_handler(**_kwargs):
        return {"result": "ok"}

    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.resolve_tool_name",
        lambda name: str(name),
    )
    monkeypatch.setattr(
        "backend.services.tool_executor.skill_router.get_tool_definition",
        lambda name: SimpleNamespace(name=str(name), func=_dummy_handler, args_schema=None),
    )
    monkeypatch.setattr(
        "backend.services.tool_executor.PolicyEngine.evaluate",
        lambda _tool_name, _db: "ALLOW",
    )

    fixed_trace = "trace-internal-123"
    executor = ToolExecutor(
        db=db_session,
        api_key="dummy",
        provider="openai",
        model="gpt-5.4-nano",
        additional_context={"trace_id": fixed_trace, "chat_id": 77},
    )

    result = await executor.call_internal_skill(
        "filesystem.list_directory",
        {"path": "."},
    )

    assert result["status"] == "ok"
    latest = db_session.query(SkillTelemetry).order_by(SkillTelemetry.id.desc()).first()
    assert latest is not None
    assert latest.trace_id == fixed_trace
    assert isinstance(latest.arguments_json, dict)
    assert latest.arguments_json.get("__call_type") == "internal"
