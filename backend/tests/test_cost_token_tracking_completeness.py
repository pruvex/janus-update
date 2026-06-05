import asyncio
import json
from datetime import datetime

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from backend.api.routers import system
from backend.data import crud
from backend.data import database as database_module
from backend.data.models import Base, Cost
from backend.llm_providers.gemini.gateway import GeminiGateway
from backend.services.orchestrator.execution_engine import (
    _emit_stream_final_usage_debug_decision,
    _should_persist_stream_final_usage_cost,
)
from backend.services.cost_service import create_cost_entry


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def test_cost_entry_persists_cached_and_total_tokens_for_deep_dive():
    db = _session()

    entry = create_cost_entry(
        db=db,
        amount=0.001,
        model="gpt-5.4-nano",
        provider="openai",
        source_type="conversation",
        input_tokens=1000,
        output_tokens=120,
        cached_tokens=350,
        total_tokens=1120,
        context_details="tool_loop_iteration=1;tool_calls=1",
    )

    stored = db.query(Cost).filter(Cost.id == entry.id).one()
    assert stored.cached_tokens == 350
    assert stored.total_tokens == 1120
    assert "tool_calls=1" in stored.context


def test_cost_entry_persists_structured_attribution_metadata_without_full_prompt_or_response():
    db = _session()

    entry = create_cost_entry(
        db=db,
        amount=0.0025,
        model="gemini-3-flash-preview",
        provider="gemini",
        source_type="conversation",
        input_tokens=800,
        output_tokens=140,
        attribution_group_id="grp-001",
        attribution_request_id="req-001",
        attribution_session_id="chat-77",
        attribution_test_run_id="TEST-RUN-2026-06-02-001",
        attribution_status="intern_attribuiert",
        attribution_component="grounding",
        attribution_manual_override=True,
        context_details="component=grounding;query_count=2",
        attribution_metadata={
            "provider_scope": "gemini",
            "component_label": "native_grounding",
            "prompt": "do not persist me",
            "response": "do not persist me either",
        },
    )

    stored = db.query(Cost).filter(Cost.id == entry.id).one()
    assert stored.attribution_group_id == "grp-001"
    assert stored.attribution_request_id == "req-001"
    assert stored.attribution_session_id == "chat-77"
    assert stored.attribution_test_run_id == "TEST-RUN-2026-06-02-001"
    assert stored.attribution_status == "intern_attribuiert"
    assert stored.attribution_component == "grounding"
    assert stored.attribution_manual_override is True
    assert stored.attribution_metadata["provider_scope"] == "gemini"
    assert stored.attribution_metadata["component_label"] == "native_grounding"
    assert stored.attribution_metadata["compact_cause_context"] == "component=grounding;query_count=2"
    assert "prompt" not in stored.attribution_metadata
    assert "response" not in stored.attribution_metadata


def test_cost_entry_recursively_sanitizes_nested_attribution_metadata():
    db = _session()

    entry = create_cost_entry(
        db=db,
        amount=0.0031,
        model="gemini-3-flash-preview",
        provider="gemini",
        source_type="conversation",
        attribution_metadata={
            "provider_scope": "gemini",
            "nested": {
                "prompt": "drop me",
                "allowed": "keep me",
                "response": "drop me too",
            },
            "components": [
                {"label": "conversation", "messages": ["drop this nested list"]},
                {"label": "grounding_websearch", "details": {"chat_history": ["drop"], "query_count": 1}},
            ],
        },
    )

    stored = db.query(Cost).filter(Cost.id == entry.id).one()
    assert stored.attribution_metadata["provider_scope"] == "gemini"
    assert stored.attribution_metadata["nested"] == {"allowed": "keep me"}
    assert stored.attribution_metadata["components"] == [
        {"label": "conversation"},
        {"label": "grounding_websearch", "details": {"query_count": 1}},
    ]


def test_monthly_deep_dive_aggregates_hidden_cached_tokens_and_context_breakdown():
    db = _session()
    create_cost_entry(
        db=db,
        amount=0.001,
        model="gpt-5.4-nano",
        provider="openai",
        source_type="conversation",
        input_tokens=1000,
        output_tokens=120,
        cached_tokens=350,
        total_tokens=1120,
        context_details="tool_loop_iteration=1;tool_calls=1",
    )
    create_cost_entry(
        db=db,
        amount=0.0005,
        model="gpt-5.4-nano",
        provider="openai",
        source_type="conversation",
        input_tokens=200,
        output_tokens=50,
        cached_tokens=0,
        total_tokens=250,
        context_details="stream_final_usage=1",
    )

    now = datetime.utcnow()
    summary = crud.get_monthly_cost_summary_by_model(db, now.year, now.month)
    row = next(item for item in summary if item["model"] == "gpt-5.4-nano")

    assert row["total_input_tokens"] == 1200
    assert row["total_output_tokens"] == 170
    assert row["total_cached_tokens"] == 350
    assert row["total_tokens"] == 1370
    contexts = {item["context"]: item for item in row["context_breakdown"]}
    assert contexts["conversation (tool_loop_iteration=1;tool_calls=1)"]["cached_tokens"] == 350
    assert contexts["conversation (stream_final_usage=1)"]["total_tokens"] == 250


def test_websearch_costs_remain_separate_deep_dive_component():
    db = _session()
    create_cost_entry(
        db=db,
        amount=0.009,
        model="websearch",
        provider="openai",
        source_type="websearch",
        context_details="query_count=1",
    )

    now = datetime.utcnow()
    summary = crud.get_monthly_cost_summary_by_model(db, now.year, now.month)
    row = next(item for item in summary if item["model"] == "__WEB_SEARCHES__")

    assert row["display_name"] == "Web-Recherchen"
    assert row["search_count"] == 1
    assert row["search_cost"] == 0.009


def test_gemini_stream_final_usage_costs_are_excluded_from_generic_stream_persistence():
    assert _should_persist_stream_final_usage_cost("gemini") is False
    assert _should_persist_stream_final_usage_cost("google") is False
    assert _should_persist_stream_final_usage_cost("openai") is True
    assert _should_persist_stream_final_usage_cost("anthropic") is True


def test_cost_entry_writes_privacy_safe_debug_log_in_dev_mode(monkeypatch, tmp_path):
    log_path = tmp_path / "cost-tracking-debug.jsonl"
    monkeypatch.setenv("JANUS_COST_TRACKING_DEBUG_LOG_PATH", str(log_path))
    db = _session()

    create_cost_entry(
        db=db,
        amount=0.0025,
        model="gemini-3-flash-preview",
        provider="gemini",
        source_type="conversation",
        input_tokens=800,
        output_tokens=140,
        context_details="component=grounding;query_count=2",
        attribution_group_id="grp-001",
        attribution_request_id="req-001",
        attribution_status="intern attribuiert",
        attribution_component="grounding",
        attribution_metadata={
            "provider_scope": "gemini",
            "prompt": "do not persist me",
            "nested": {
                "response": "drop me",
                "allowed": "keep me",
            },
        },
    )

    payload = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert payload["event_type"] == "cost_entry_persisted"
    assert payload["provider"] == "gemini"
    assert payload["attribution_request_id"] == "req-001"
    assert payload["context_details"] == "component=grounding;query_count=2"
    assert payload["metadata"]["provider_scope"] == "gemini"
    assert payload["metadata"]["nested"] == {"allowed": "keep me"}
    assert "prompt" not in payload["metadata"]
    assert "response" not in payload["metadata"]


def test_gemini_gateway_emits_request_level_debug_log_summary(monkeypatch, tmp_path):
    log_path = tmp_path / "cost-tracking-debug.jsonl"
    monkeypatch.setenv("JANUS_COST_TRACKING_DEBUG_LOG_PATH", str(log_path))
    gateway = GeminiGateway()
    monkeypatch.setattr(gateway, "_persist_cost_entry_with_result", lambda **kwargs: True)

    result = gateway._persist_gemini_request_costs(
        db=object(),
        provider="gemini",
        model="gemini-3-flash-preview",
        chat_id=321,
        conversation_cost_eur=0.03,
        input_tokens=900,
        output_tokens=180,
        websearch_query_count=1,
        grounding_metadata={"web_search_queries": ["switch 2 release"]},
        request_kind="simple_tool_loop",
    )

    lines = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    summary_event = next(item for item in lines if item["event_type"] == "gemini_request_cost_attribution")
    assert summary_event["provider"] == "gemini"
    assert summary_event["attribution_request_id"] == result["attribution_request_id"]
    assert summary_event["attribution_component"] == "gemini_request"
    assert summary_event["metadata"]["request_kind"] == "simple_tool_loop"
    assert summary_event["metadata"]["websearch_query_count"] == 1
    assert "prompt" not in summary_event["metadata"]
    assert "response" not in summary_event["metadata"]


def test_stream_final_usage_skip_emits_debug_event_for_gemini(monkeypatch, tmp_path):
    log_path = tmp_path / "cost-tracking-debug.jsonl"
    monkeypatch.setenv("JANUS_COST_TRACKING_DEBUG_LOG_PATH", str(log_path))

    _emit_stream_final_usage_debug_decision(
        provider="gemini",
        model="gemini-3-flash-preview",
        total_cost=0.031,
        input_tokens=1000,
        output_tokens=120,
        cached_tokens=0,
        total_tokens=1120,
        reason="provider_has_own_attribution_path",
    )

    payload = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert payload["event_type"] == "stream_final_usage_persist_skipped"
    assert payload["provider"] == "gemini"
    assert payload["attribution_component"] == "stream_final_usage"
    assert payload["metadata"]["reason"] == "provider_has_own_attribution_path"


def test_costs_sqlite_schema_migration_adds_attribution_columns(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE costs (
                    id INTEGER PRIMARY KEY,
                    timestamp DATETIME,
                    provider VARCHAR,
                    model VARCHAR,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    cached_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    total_cost FLOAT DEFAULT 0.0,
                    context VARCHAR,
                    tokens_saved INTEGER DEFAULT 0,
                    cost_saved FLOAT DEFAULT 0.0
                )
                """
            )
        )

    monkeypatch.setattr(database_module, "engine", engine)
    database_module._ensure_sqlite_schema_migrations()

    columns = {column["name"] for column in inspect(engine).get_columns("costs")}
    assert "attribution_group_id" in columns
    assert "attribution_request_id" in columns
    assert "attribution_session_id" in columns
    assert "attribution_test_run_id" in columns
    assert "attribution_status" in columns
    assert "attribution_component" in columns
    assert "attribution_manual_override" in columns
    assert "attribution_metadata" in columns


def test_cross_provider_deep_dive_summary_restores_provider_model_and_savings_visibility():
    db = _session()

    create_cost_entry(
        db=db,
        amount=0.004,
        model="gpt-5.4-nano",
        provider="openai",
        source_type="conversation",
        input_tokens=700,
        output_tokens=90,
        cached_tokens=250,
        total_tokens=790,
        tokens_saved=250,
        context_details="tool_loop_iteration=1;tool_calls=1",
    )
    create_cost_entry(
        db=db,
        amount=0.020,
        model="gemini-3-flash-preview",
        provider="gemini",
        source_type="conversation",
        input_tokens=900,
        output_tokens=180,
        attribution_group_id="grp-100",
        attribution_request_id="req-100",
        attribution_session_id="chat-88",
        attribution_status="intern attribuiert",
        attribution_component="conversation",
        attribution_metadata={"request_kind": "simple_tool_loop"},
    )
    create_cost_entry(
        db=db,
        amount=0.010,
        model="gemini-3-flash-preview",
        provider="gemini",
        source_type="websearch",
        context_details="query_count=1",
        attribution_group_id="grp-100",
        attribution_request_id="req-100",
        attribution_session_id="chat-88",
        attribution_status="intern attribuiert",
        attribution_component="grounding_websearch",
        attribution_metadata={"request_kind": "simple_tool_loop", "websearch_query_count": 1},
    )
    create_cost_entry(
        db=db,
        amount=0.050,
        model="gemini-3-pro-preview",
        provider="gemini",
        source_type="conversation",
        input_tokens=1100,
        output_tokens=220,
        attribution_group_id="grp-200",
        attribution_request_id="req-200",
        attribution_test_run_id="TEST-RUN-2026-06-03-001",
        attribution_status="intern attribuiert",
        attribution_component="conversation",
        attribution_manual_override=False,
        attribution_metadata={"request_kind": "engine_owned_tool_loop"},
    )

    now = datetime.utcnow()
    summary = crud.get_costs_deep_dive_summary(db, now.year, now.month)

    assert summary["provider_scope"] == "cross_provider"
    assert summary["ui_contract"]["primary_surface"] == "user_cost_overview"
    assert summary["ui_contract"]["debug_surface"] == "separate_dev_log"
    assert summary["ui_contract"]["detail_surface"] == "forensic_followup"
    assert summary["user_summary"]["primary_message"] == "Kosten verstehen und Optimierungspotenziale erkennen."
    assert summary["user_summary"]["provider_count"] == 2
    assert summary["user_summary"]["model_count"] == 3
    assert summary["user_summary"]["top_providers"] == ["gemini", "openai"]
    assert summary["user_summary"]["top_models"][0] == "gemini-3-pro-preview"
    assert summary["truthfulness_hints"] == []
    cross_provider_summary = summary["cross_provider_summary"]
    assert cross_provider_summary["provider_count"] == 2
    assert cross_provider_summary["model_count"] == 3
    assert cross_provider_summary["total_cached_tokens"] == 250
    assert cross_provider_summary["total_tokens_saved"] == 250
    assert cross_provider_summary["total_cost_saved"] > 0.0

    providers = {item["provider"]: item for item in cross_provider_summary["provider_breakdown"]}
    assert providers["openai"]["total_cost"] == 0.004
    assert providers["openai"]["total_cached_tokens"] == 250
    assert providers["openai"]["total_tokens_saved"] == 250
    assert providers["openai"]["models"] == ["gpt-5.4-nano"]
    assert providers["gemini"]["total_cost"] == 0.08

    model_breakdown = {
        (item["provider"], item["model"]): item
        for item in cross_provider_summary["model_breakdown"]
    }
    openai_model = model_breakdown[("openai", "gpt-5.4-nano")]
    assert openai_model["total_cost"] == 0.004
    assert openai_model["total_cached_tokens"] == 250
    assert openai_model["total_tokens_saved"] == 250
    assert openai_model["component_breakdown"][0]["component"] == "conversation"

    assert summary["summary"]["group_count"] == 3
    assert summary["summary"]["request_count"] == 3
    assert summary["summary"]["forensic_provider_scope"] == "gemini"
    assert summary["summary"]["internal_attributed_total"] == 0.08
    assert summary["summary"]["unattributed_residual_total"] == 0.0
    assert summary["summary"]["external_billing_total"] == 0.08
    assert summary["summary"]["truthfulness_status"] == "complete"
    assert summary["summary"]["truthfulness_message"] == "Die sichtbare Kostensicht ist fuer diesen Zeitraum belastbar."
    assert summary["anomaly_overview"][0]["type"] == "avoidable_pro"
    assert not any(hint["type"] == "attribution_partial" for hint in summary["truthfulness_hints"])

    groups = {group["group_key"]: group for group in summary["groups"]}
    session_group = groups["session:chat-88"]
    test_run_group = groups["test_run:TEST-RUN-2026-06-03-001"]
    assert session_group["request_count"] == 1
    assert test_run_group["request_count"] == 1

    request = session_group["requests"][0]
    assert request["request_id"] == "req-100"
    assert request["internal_attributed_total"] == 0.03
    assert request["unattributed_residual_total"] == 0.0
    components = {component["component"]: component for component in request["components"]}
    assert components["conversation"]["total_cost"] == 0.02
    assert components["grounding_websearch"]["total_cost"] == 0.01


def test_gemini_deep_dive_summary_keeps_may_2026_residual_visible_for_legacy_costs():
    db = _session()

    attributed = create_cost_entry(
        db=db,
        amount=0.030,
        model="gemini-3-flash-preview",
        provider="gemini",
        source_type="conversation",
        attribution_group_id="grp-may",
        attribution_request_id="req-may",
        attribution_session_id="chat-may",
        attribution_status="intern attribuiert",
        attribution_component="conversation",
    )
    legacy = create_cost_entry(
        db=db,
        amount=0.020,
        model="gemini-3-flash-preview",
        provider="gemini",
        source_type="conversation",
        context_details="legacy_reconstruction=1",
    )

    attributed.timestamp = datetime(2026, 5, 14, 10, 0, 0)
    legacy.timestamp = datetime(2026, 5, 14, 10, 5, 0)
    db.commit()

    summary = crud.get_costs_deep_dive_summary(db, 2026, 5)

    assert summary["historical_reconciliation"]["mode"] == "may_2026_forensic_reconstruction"
    assert summary["historical_reconciliation"]["visible_residual_required"] is True
    assert summary["truthfulness_hints"][0]["type"] == "attribution_partial"
    assert summary["truthfulness_hints"][0]["message"] == "Ein historischer Kostenanteil bleibt noch als sichtbarer Rest bestehen."
    assert summary["summary"]["internal_attributed_total"] == 0.03
    assert summary["summary"]["unattributed_residual_total"] == 0.02
    assert summary["summary"]["external_billing_total"] == 0.05
    assert summary["summary"]["deviation_total"] == 0.02
    assert summary["summary"]["truthfulness_status"] == "partial"
    assert summary["summary"]["truthfulness_message"] == "Ein historischer Kostenanteil bleibt noch als sichtbarer Rest bestehen."
    assert summary["anomaly_overview"][0]["type"] == "attribution_gap"
    assert any(hint["type"] == "billing_alignment_partial" for hint in summary["truthfulness_hints"])

    unscoped_group = next(group for group in summary["groups"] if group["group_kind"] == "unscoped")
    legacy_request = unscoped_group["requests"][0]
    assert legacy_request["request_label"].startswith("Legacy-Kostenblock")
    assert legacy_request["attribution_status"] == "nicht eindeutig attribuiert"
    assert legacy_request["unattributed_residual_total"] == 0.02


def test_costs_deep_dive_endpoint_returns_anomaly_first_payload():
    db = _session()

    create_cost_entry(
        db=db,
        amount=0.011,
        model="gemini-3-flash-preview",
        provider="gemini",
        source_type="conversation",
        attribution_group_id="grp-endpoint",
        attribution_request_id="req-endpoint",
        attribution_session_id="chat-endpoint",
        attribution_status="intern attribuiert",
        attribution_component="conversation",
    )

    now = datetime.utcnow()
    payload = asyncio.run(system.get_costs_deep_dive(year=now.year, month=now.month, db=db))

    assert payload["provider_scope"] == "cross_provider"
    assert "ui_contract" in payload
    assert "user_summary" in payload
    assert "truthfulness_hints" in payload
    assert "anomaly_overview" in payload
    assert "summary" in payload
    assert "cross_provider_summary" in payload
    assert "groups" in payload
