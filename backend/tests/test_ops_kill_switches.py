import pytest
from fastapi import HTTPException

from backend.services.ops_kill_switches import (
    classify_tool,
    dry_run_inventory,
    provider_access_decision,
    require_local_user_unlocked,
    require_memory_rag_enabled,
    require_write_operations_enabled,
    telemetry_mode,
    telemetry_event_ingest_allowed,
    telemetry_remote_upload_allowed,
    tool_access_decision,
)


def test_provider_kill_switch_blocks_cloud_and_allows_local(monkeypatch):
    monkeypatch.setenv("JANUS_DISABLE_CLOUD_PROVIDERS", "1")

    assert provider_access_decision("openai").disabled is True
    assert provider_access_decision("gemini").code == "OPS_PROVIDER_DISABLED"
    assert provider_access_decision("ollama").disabled is False


def test_provider_kill_switch_restores_after_env_unset(monkeypatch):
    monkeypatch.setenv("JANUS_DISABLE_PROVIDER_ACCESS", "1")
    assert provider_access_decision("openai").disabled is True

    monkeypatch.delenv("JANUS_DISABLE_PROVIDER_ACCESS", raising=False)
    assert provider_access_decision("openai").disabled is False


def test_external_tool_kill_switch_blocks_current_data_tools(monkeypatch):
    monkeypatch.setenv("JANUS_DISABLE_EXTERNAL_TOOLS", "1")

    assert tool_access_decision("system.websearch").code == "OPS_EXTERNAL_TOOLS_DISABLED"
    assert tool_access_decision("system.weather").disabled is True
    assert tool_access_decision("system.price_comparison").disabled is True
    assert tool_access_decision("filesystem.read_file").disabled is False


def test_write_kill_switch_blocks_destructive_and_write_tools(monkeypatch):
    monkeypatch.setenv("JANUS_DISABLE_WRITE_TOOLS", "1")

    assert tool_access_decision("filesystem.create_file").code == "OPS_WRITE_TOOLS_DISABLED"
    assert tool_access_decision("calendar.update_event").disabled is True
    assert tool_access_decision("memory.write").disabled is True
    assert tool_access_decision("filesystem.find_files").disabled is False
    with pytest.raises(HTTPException) as excinfo:
        require_write_operations_enabled()
    assert excinfo.value.status_code == 423


def test_memory_rag_kill_switch_blocks_reads_and_writes(monkeypatch):
    monkeypatch.setenv("JANUS_DISABLE_MEMORY_RAG", "1")

    assert tool_access_decision("memory.read").code == "OPS_MEMORY_RAG_DISABLED"
    assert tool_access_decision("knowledge.query").disabled is True
    with pytest.raises(HTTPException) as excinfo:
        require_memory_rag_enabled()
    assert excinfo.value.status_code == 423


def test_local_user_lock_blocks_non_ops_paths_and_keeps_ops_path_open(monkeypatch):
    monkeypatch.setenv("JANUS_LOCK_LOCAL_BETA_USER", "1")

    require_local_user_unlocked("/api/system/ops/kill-switches")
    with pytest.raises(HTTPException) as excinfo:
        require_local_user_unlocked("/api/chat")
    assert excinfo.value.status_code == 423


def test_telemetry_mode_is_safe_and_bounded(monkeypatch):
    monkeypatch.setenv("JANUS_TELEMETRY_MODE", "minimal")
    assert telemetry_mode() == "minimal"
    assert telemetry_remote_upload_allowed() is False
    assert telemetry_event_ingest_allowed("security_alert") is True
    assert telemetry_event_ingest_allowed("chat_message") is False

    monkeypatch.setenv("JANUS_TELEMETRY_MODE", "secret-super-verbose")
    assert telemetry_mode() == "normal"
    assert telemetry_remote_upload_allowed() is True

    monkeypatch.setenv("JANUS_TELEMETRY_MODE", "off")
    assert telemetry_remote_upload_allowed() is False
    assert telemetry_event_ingest_allowed("security_alert") is False


def test_dry_run_inventory_is_non_secret_and_classifies_required_domains(monkeypatch):
    monkeypatch.setenv("JANUS_DISABLE_CLOUD_PROVIDERS", "1")
    monkeypatch.setenv("JANUS_DISABLE_EXTERNAL_TOOLS", "1")
    monkeypatch.setenv("JANUS_DISABLE_WRITE_TOOLS", "1")
    monkeypatch.setenv("JANUS_DISABLE_MEMORY_RAG", "1")
    monkeypatch.setenv("JANUS_LOCK_LOCAL_BETA_USER", "1")
    monkeypatch.setenv("JANUS_TELEMETRY_MODE", "minimal")

    inventory = dry_run_inventory()
    serialized = str(inventory).lower()

    assert inventory["safeDryRun"] is True
    assert inventory["switches"]["providerAccess"] is True
    assert inventory["switches"]["telemetryMode"] == "minimal"
    assert inventory["switches"]["telemetryRemoteUploadAllowed"] is False
    assert "api_key" not in serialized
    assert "secret" not in serialized
    assert any(probe["id"] == "tool:memory.write" and probe["disabled"] for probe in inventory["probes"])
    assert classify_tool("system.websearch")["external"] is True
