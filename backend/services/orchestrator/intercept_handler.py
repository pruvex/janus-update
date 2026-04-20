"""Ollama lokale Bild-Pipeline (Engine-Status, JIT-Start, UI-Commands) — ausgelagert aus dem Orchestrator."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from backend.services.image_engine_checker import (
    get_engine_type_and_status,
    is_local_engine_ready,
    start_engine_process,
)
from backend.services.image_engine_catalog import choose_model_for_engine
from backend.services.orchestrator.intent_engine import intent_engine
from backend.services.orchestrator.prompt_registry import prompt_registry
from backend.services.orchestrator.schemas import ExecutionResponse

if TYPE_CHECKING:
    from backend.services.chat_orchestrator import ChatOrchestrator
    from backend.services.chat_orchestrator import RequestContext

logger = logging.getLogger("janus_backend")

_DEFAULT_IMAGE_ENGINE_BAT = os.getenv(
    "JANUS_LOCAL_IMAGE_ENGINE_BAT",
    r"C:\KI\Janus-Image-Engine-CPU\run_engine.bat",
)


def apply_image_intent_skill_guardrails(wf: Any) -> None:
    """Setzt relevant_skill_ids für Bild- bzw. Bild+PDF-Anfragen (vor Agent/Meta)."""
    kws: List[str] = list(wf.image_intent_keywords) if getattr(wf, "image_intent_keywords", None) else list(intent_engine.image_intent_keywords)
    if not any((kw in wf.user_prompt_lower for kw in kws)):
        return
    wf.pdf_requested = "pdf" in wf.user_prompt_lower
    if wf.pdf_requested:
        logger.info(
            "[INTERCEPT] DIAMOND GUARDRAIL: Bild+PDF erkannt. Erlaube sequenzielle Kette generate_image -> create_pdf."
        )
        wf.relevant_skill_ids = ["system.generate_image", "system.create_pdf"]
    else:
        logger.info(
            "[INTERCEPT] DIAMOND GUARDRAIL: Bild-Intent erkannt. Forciere 'system.generate_image' und blockiere alle anderen Skills."
        )
        wf.relevant_skill_ids = ["system.generate_image"]


async def handle_local_requests(
    orchestrator: "ChatOrchestrator",
    ctx: "RequestContext",
) -> Optional[Dict[str, Any]]:
    """
    Hard-Intercept für Ollama + Bild-Keywords: lokale Engine prüfen/starten, ggf. direktes generate_image.
    Rückgabe: fertige API-Response oder None.
    """
    wf = ctx.workflow
    request = ctx.request

    if str(request.provider or "").lower() != "ollama":
        return None
    if not any((kw in wf.user_text_lower for kw in intent_engine.image_keywords)):
        return None

    logger.info("[INTERCEPT] Ollama Bild-Intent: Hard-Intercept (umgehe LLM-Parsing).")
    if not await is_local_engine_ready():
        logger.info("[INTERCEPT] JIT-START: Starte Bild-Engine...")
        start_engine_process(_DEFAULT_IMAGE_ENGINE_BAT)
        await asyncio.sleep(15)
    wf.engine_status = await get_engine_type_and_status()
    if wf.engine_status.get("engine_type") == "none":
        logger.warning("[INTERCEPT] Lokale Engine fehlt nach Startversuch. Sende Hinweis an User.")
        wf.cmd = {"action": "open_settings", "tab": "settings-section-image-gen"}
        wf.execution_for_api = ExecutionResponse(
            text=prompt_registry.get_directive("local_image_settings_install_hint"),
            tool_calls=[],
            is_agent_flow=False,
            ui_command=wf.cmd,
        )
        orchestrator.status_sync.persist_assistant_message(request.chat_id, wf.execution_for_api)
        return orchestrator.status_sync.build_api_response(execution_response=wf.execution_for_api)
    if not wf.engine_status.get("is_running"):
        logger.warning("[INTERCEPT] Lokale Engine ist installiert, aber nicht gestartet. Sende Hinweis.")
        wf.cmd = {"action": "open_settings", "tab": "settings-section-image-gen"}
        wf.execution_for_api = ExecutionResponse(
            text=prompt_registry.get_directive("local_image_engine_not_running"),
            tool_calls=[],
            is_agent_flow=False,
            ui_command=wf.cmd,
        )
        orchestrator.status_sync.persist_assistant_message(request.chat_id, wf.execution_for_api)
        return orchestrator.status_sync.build_api_response(execution_response=wf.execution_for_api)
    logger.info("[INTERCEPT] Lokale Engine bereit. Führe Bild-Skill direkt aus.")
    from backend.tools.media_tools import generate_image_tool

    wf.model = choose_model_for_engine(wf.engine_status.get("engine_type"))
    if not wf.model:
        _no_models = prompt_registry.get_directive("local_image_no_models")
        wf.execution_for_api = ExecutionResponse(text=_no_models, tool_calls=[], is_agent_flow=False)
        orchestrator.status_sync.persist_assistant_message(request.chat_id, wf.execution_for_api)
        return orchestrator.status_sync.build_api_response(execution_response=wf.execution_for_api)
    wf.result = await generate_image_tool(
        prompt=wf.user_text,
        size="1024x1024",
        quality="low",
        db=orchestrator.db,
        engine_model_id=wf.model.get("id"),
    )
    if hasattr(wf.result, "model_dump"):
        wf.result = wf.result.model_dump()
    if wf.result.get("status") == "ok":
        wf.final_markdown = wf.result.get("data", {}).get("markdown_image", "")
        wf.response_text = (
            f"{prompt_registry.get_directive('local_image_success_intro')}{wf.final_markdown}"
            if wf.final_markdown
            else prompt_registry.get_directive("local_image_success_plain")
        )
    else:
        wf.err_msg = wf.result.get("error", {}).get("message", "Unbekannt")
        wf.response_text = f"{prompt_registry.get_directive('local_image_error_prefix')}{wf.err_msg}"
    wf.execution_for_api = ExecutionResponse(text=wf.response_text, tool_calls=[], is_agent_flow=False)
    orchestrator.status_sync.persist_assistant_message(request.chat_id, wf.execution_for_api)
    return orchestrator.status_sync.build_api_response(execution_response=wf.execution_for_api)
