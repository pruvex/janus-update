from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from fastapi import HTTPException, status


TRUTHY_VALUES = {"1", "true", "yes", "on", "enabled", "disable", "disabled"}
FALSEY_VALUES = {"0", "false", "no", "off", "disabled", ""}

CLOUD_PROVIDERS = {"openai", "gemini", "google", "anthropic", "cohere"}

EXTERNAL_TOOL_IDS = {
    "system.websearch",
    "websearch_wrapper",
    "system.weather",
    "get_weather_from_api_tool",
    "system.rss_news",
    "get_latest_news_rss",
    "system.wikipedia",
    "get_wikipedia_summary",
    "system.routing",
    "get_distance_and_route_tool",
    "system.price_comparison",
    "price_comparison_tool",
    "video.search",
    "video.understand",
    "get_country_info_tool",
}

WRITE_TOOL_MARKERS = (
    "create",
    "delete",
    "update",
    "write",
    "move",
    "rename",
    "save",
    "upload",
    "index",
    "generate_image",
    "save_mp3",
    "edit_pdf",
)

WRITE_TOOL_IDS = {
    "filesystem.create_file",
    "filesystem.delete_file",
    "filesystem.create_directory",
    "filesystem.delete_directory",
    "filesystem.rename_file",
    "filesystem.move_file",
    "filesystem.move_files",
    "create_file_tool",
    "delete_file_tool",
    "create_directory",
    "delete_directory",
    "rename_file",
    "move_file",
    "move_files",
    "memory.write",
    "memory.update",
    "memory.delete",
    "memory_write",
    "memory_update",
    "memory_delete",
    "calendar.create_event",
    "calendar.delete_event",
    "calendar.update_event",
    "calendar.find_and_update_event",
    "calendar.find_address_and_update_event",
    "create_calendar_event",
    "delete_calendar_event",
    "update_calendar_event",
    "find_and_update_calendar_event",
    "find_address_and_update_calendar_event",
    "system.create_pdf",
    "save_mp3_tool",
    "generate_image_tool",
}

MEMORY_RAG_TOOL_IDS = {
    "memory.write",
    "memory.read",
    "memory.update",
    "memory.delete",
    "memory.history",
    "memory_write",
    "memory_read",
    "memory_update",
    "memory_delete",
    "memory_history",
    "knowledge.query",
    "knowledge.open_document",
    "knowledge.read_full_text",
    "query_knowledge_base",
    "open_knowledge_document",
    "get_full_document_text",
}

SAFE_DISABLED_MESSAGE = (
    "Diese Funktion ist gerade durch einen Ops-Recovery-Schalter deaktiviert. "
    "Bitte versuche es spaeter erneut oder kontaktiere den Betreiber."
)


@dataclass(frozen=True)
class KillSwitchDecision:
    disabled: bool
    code: str
    message: str
    switch: str
    category: str


def _env_flag(*names: str) -> bool:
    for name in names:
        raw = os.getenv(name)
        if raw is None:
            continue
        value = raw.strip().lower()
        if value in TRUTHY_VALUES:
            return True
        if value in FALSEY_VALUES:
            return False
        return True
    return False


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _matches_any(value: str, candidates: Iterable[str]) -> bool:
    return value in candidates or any(value.endswith(f".{candidate}") for candidate in candidates)


def cloud_provider_access_disabled() -> bool:
    return _env_flag("JANUS_DISABLE_CLOUD_PROVIDERS", "JANUS_DISABLE_PROVIDER_ACCESS")


def external_tools_disabled() -> bool:
    return _env_flag("JANUS_DISABLE_EXTERNAL_TOOLS", "JANUS_DISABLE_CURRENT_DATA_TOOLS")


def write_tools_disabled() -> bool:
    return _env_flag("JANUS_DISABLE_WRITE_TOOLS", "JANUS_DISABLE_DESTRUCTIVE_TOOLS")


def memory_rag_disabled() -> bool:
    return _env_flag("JANUS_DISABLE_MEMORY_RAG", "JANUS_DISABLE_RAG", "JANUS_DISABLE_MEMORY")


def local_user_locked() -> bool:
    return _env_flag("JANUS_LOCK_LOCAL_BETA_USER", "JANUS_DISABLE_USER_ACCOUNTS")


def telemetry_mode() -> str:
    mode = _norm(os.getenv("JANUS_TELEMETRY_MODE") or "normal")
    allowed = {"off", "minimal", "normal", "debug"}
    return mode if mode in allowed else "normal"


def telemetry_remote_upload_allowed() -> bool:
    return telemetry_mode() in {"normal", "debug"}


def telemetry_event_ingest_allowed(event_type: Optional[str] = None) -> bool:
    mode = telemetry_mode()
    if mode == "off":
        return False
    if mode != "minimal":
        return True
    normalized_event_type = _norm(event_type)
    return normalized_event_type.startswith(("security", "ops", "abuse"))


def provider_access_decision(provider: str) -> KillSwitchDecision:
    provider_key = _norm(provider)
    disabled = cloud_provider_access_disabled() and provider_key in CLOUD_PROVIDERS
    return KillSwitchDecision(
        disabled=disabled,
        code="OPS_PROVIDER_DISABLED" if disabled else "OPS_PROVIDER_ALLOWED",
        message=SAFE_DISABLED_MESSAGE if disabled else "Provider access allowed.",
        switch="JANUS_DISABLE_CLOUD_PROVIDERS",
        category="provider",
    )


def classify_tool(tool_name: str) -> Dict[str, bool]:
    name = _norm(tool_name).replace("_tool", "")
    external = _matches_any(name, EXTERNAL_TOOL_IDS) or any(
        marker in name for marker in ("websearch", "weather", "rss", "wikipedia", "routing", "route", "price_comparison")
    )
    memory_rag = _matches_any(name, MEMORY_RAG_TOOL_IDS) or name.startswith("memory.") or "knowledge" in name or "rag" in name
    write = _matches_any(name, WRITE_TOOL_IDS) or any(marker in name for marker in WRITE_TOOL_MARKERS)
    if name in {"filesystem.read_file", "filesystem.list_directory", "filesystem.find_files", "memory.read", "memory.history"}:
        write = False
    return {"external": external, "write": write, "memory_rag": memory_rag}


def tool_access_decision(tool_name: str) -> KillSwitchDecision:
    classes = classify_tool(tool_name)
    if memory_rag_disabled() and classes["memory_rag"]:
        return KillSwitchDecision(True, "OPS_MEMORY_RAG_DISABLED", SAFE_DISABLED_MESSAGE, "JANUS_DISABLE_MEMORY_RAG", "memory_rag")
    if write_tools_disabled() and classes["write"]:
        return KillSwitchDecision(True, "OPS_WRITE_TOOLS_DISABLED", SAFE_DISABLED_MESSAGE, "JANUS_DISABLE_WRITE_TOOLS", "write")
    if external_tools_disabled() and classes["external"]:
        return KillSwitchDecision(True, "OPS_EXTERNAL_TOOLS_DISABLED", SAFE_DISABLED_MESSAGE, "JANUS_DISABLE_EXTERNAL_TOOLS", "external")
    return KillSwitchDecision(False, "OPS_TOOL_ALLOWED", "Tool access allowed.", "", "tool")


def require_write_operations_enabled() -> None:
    if write_tools_disabled():
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=SAFE_DISABLED_MESSAGE)


def require_memory_rag_enabled() -> None:
    if memory_rag_disabled():
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=SAFE_DISABLED_MESSAGE)


def require_local_user_unlocked(path: Optional[str] = None) -> None:
    if not local_user_locked():
        return
    route = str(path or "")
    if route.startswith("/api/system/ops"):
        return
    raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=SAFE_DISABLED_MESSAGE)


def dry_run_inventory() -> Dict[str, Any]:
    probes: List[Dict[str, Any]] = []
    for provider in ("openai", "gemini", "ollama"):
        decision = provider_access_decision(provider)
        probes.append({"id": f"provider:{provider}", "disabled": decision.disabled, "code": decision.code})
    for tool in ("system.websearch", "system.weather", "memory.write", "knowledge.query", "filesystem.create_file", "calendar.update_event"):
        decision = tool_access_decision(tool)
        probes.append(
            {
                "id": f"tool:{tool}",
                "disabled": decision.disabled,
                "code": decision.code,
                "classification": classify_tool(tool),
            }
        )
    return {
        "schemaVersion": "janus.ops-kill-switches.v1",
        "status": "ok",
        "safeDryRun": True,
        "switches": {
            "providerAccess": cloud_provider_access_disabled(),
            "externalTools": external_tools_disabled(),
            "writeTools": write_tools_disabled(),
            "memoryRag": memory_rag_disabled(),
            "localUserLocked": local_user_locked(),
            "telemetryMode": telemetry_mode(),
            "telemetryRemoteUploadAllowed": telemetry_remote_upload_allowed(),
        },
        "probes": probes,
        "restoreProcedure": [
            "Unset JANUS_DISABLE_CLOUD_PROVIDERS/JANUS_DISABLE_PROVIDER_ACCESS.",
            "Unset JANUS_DISABLE_EXTERNAL_TOOLS/JANUS_DISABLE_CURRENT_DATA_TOOLS.",
            "Unset JANUS_DISABLE_WRITE_TOOLS/JANUS_DISABLE_DESTRUCTIVE_TOOLS.",
            "Unset JANUS_DISABLE_MEMORY_RAG/JANUS_DISABLE_RAG/JANUS_DISABLE_MEMORY.",
            "Unset JANUS_LOCK_LOCAL_BETA_USER/JANUS_DISABLE_USER_ACCOUNTS.",
            "Set JANUS_TELEMETRY_MODE back to normal.",
            "Restart the packaged-local Janus backend and verify /api/health plus this endpoint.",
        ],
    }
