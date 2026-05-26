"""Policy-Consent (1/2/3) und zugehörige Early-Exit-Antworten — ausgelagert aus ChatOrchestrator."""

from __future__ import annotations

import json
import logging
import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional

from backend.services.orchestrator.intent_engine import intent_engine
from backend.services.orchestrator.prompt_registry import prompt_registry
from backend.services.orchestrator.schemas import ExecutionResponse
from backend.services.tool_executor import ToolExecutor

if TYPE_CHECKING:
    from backend.services.chat_orchestrator import ChatOrchestrator
    from backend.services.chat_orchestrator import RequestContext

logger = logging.getLogger("janus_backend")


def _intent_is_policy_consent(wf: Any) -> bool:
    inc = getattr(wf, "intent_detection_result", None)
    if inc is not None:
        return bool(inc.is_policy_consent)
    return intent_engine.is_policy_consent_choice(wf.user_text_clean)


def _intent_is_one_time_policy(wf: Any) -> bool:
    inc = getattr(wf, "intent_detection_result", None)
    if inc is not None:
        return bool(inc.is_one_time_policy)
    return intent_engine.is_one_time_policy_choice(wf.user_text_clean)


async def handle_policy_consent_phase(
    orchestrator: "ChatOrchestrator",
    ctx: "RequestContext",
) -> Optional[Dict[str, Any]]:
    """
    Verarbeitet DB-Pending-Consent und Fallback über letzte Assistant-Nachricht.
    Gibt eine fertige API-Response zurück oder None, wenn der normale Flow weiterläuft.
    Mutiert ctx.workflow (wf) wie zuvor im Orchestrator.
    """
    wf = ctx.workflow
    request = ctx.request

    if wf.is_waiting_for_consent:
        wf.is_policy_response = True
        logger.info("[POLICY] STATE (DB): Pending-Status für Chat %s verbraucht.", request.chat_id)
        wf.blocked_skill_id = str((wf.policy_pending_data or {}).get("blocked_skill_id") or "").strip()
        wf.blocked_arguments = (wf.policy_pending_data or {}).get("blocked_arguments") or {}
        if wf.blocked_skill_id and _intent_is_policy_consent(wf):
            wf.request_trace_id = str(uuid.uuid4())
            wf.executor = ToolExecutor(
                orchestrator.db,
                wf.api_key,
                request.provider,
                request.model,
                additional_context={"chat_id": request.chat_id, "trace_id": wf.request_trace_id, "provider": request.provider, "model": request.model},
            )
            if _intent_is_one_time_policy(wf):
                wf.resume_results = await wf.executor.execute_tool_calls(
                    [
                        {
                            "id": "policy-resume-once",
                            "function": {
                                "name": wf.blocked_skill_id,
                                "arguments": json.dumps(wf.blocked_arguments, ensure_ascii=False),
                            },
                        }
                    ],
                    bypass_policy=True,
                )
                orchestrator._set_policy_pending_data(request.chat_id, None)
                wf.payload = orchestrator._extract_tool_result_payload(wf.resume_results[0] if wf.resume_results else None)
                wf.execution_for_api = ExecutionResponse(
                    text=orchestrator._build_policy_resume_text(wf.payload, wf.blocked_skill_id, "resume"),
                    tool_calls=wf.resume_results,
                    is_agent_flow=False,
                    raw_response={"text": orchestrator._build_policy_resume_text(wf.payload, wf.blocked_skill_id, "resume")},
                )
                orchestrator.status_sync.persist_assistant_message(request.chat_id, wf.execution_for_api)
                return orchestrator.status_sync.build_api_response(execution_response=wf.execution_for_api)
            if wf.user_text_clean in ["2", "2.", "immer"]:
                wf.grant_results = await wf.executor.execute_tool_calls(
                    [
                        {
                            "id": "policy-grant-always",
                            "function": {
                                "name": "system.grant_permission",
                                "arguments": json.dumps({"skill_id": wf.blocked_skill_id}, ensure_ascii=False),
                            },
                        }
                    ],
                    bypass_policy=False,
                )
                wf.grant_payload = orchestrator._extract_tool_result_payload(wf.grant_results[0] if wf.grant_results else None)
                if wf.grant_payload.get("status") == "ok":
                    wf.resume_results = await wf.executor.execute_tool_calls(
                        [
                            {
                                "id": "policy-resume-always",
                                "function": {
                                    "name": wf.blocked_skill_id,
                                    "arguments": json.dumps(wf.blocked_arguments, ensure_ascii=False),
                                },
                            }
                        ],
                        bypass_policy=False,
                    )
                    orchestrator._set_policy_pending_data(request.chat_id, None)
                    wf.resume_payload = orchestrator._extract_tool_result_payload(wf.resume_results[0] if wf.resume_results else None)
                    wf.final_text = orchestrator._build_policy_resume_text(wf.resume_payload, wf.blocked_skill_id, "grant")
                    wf.execution_for_api = ExecutionResponse(
                        text=wf.final_text,
                        tool_calls=wf.grant_results + wf.resume_results,
                        is_agent_flow=False,
                        raw_response={"text": wf.final_text},
                    )
                    orchestrator.status_sync.persist_assistant_message(request.chat_id, wf.execution_for_api)
                    return orchestrator.status_sync.build_api_response(execution_response=wf.execution_for_api)
                orchestrator._set_policy_pending_data(request.chat_id, None)
                wf.final_text = orchestrator._build_policy_resume_text(wf.grant_payload, wf.blocked_skill_id, "grant")
                wf.execution_for_api = ExecutionResponse(
                    text=wf.final_text,
                    tool_calls=wf.grant_results,
                    is_agent_flow=False,
                    raw_response={"text": wf.final_text},
                    error=wf.grant_payload.get("error") if isinstance(wf.grant_payload, dict) else None,
                )
                orchestrator.status_sync.persist_assistant_message(request.chat_id, wf.execution_for_api)
                return orchestrator.status_sync.build_api_response(execution_response=wf.execution_for_api)
            if wf.user_text_clean in ["3", "3.", "abbrechen", "nein"]:
                orchestrator._set_policy_pending_data(request.chat_id, None)
                _cancel = prompt_registry.get_directive("policy_action_cancelled")
                wf.execution_for_api = ExecutionResponse(
                    text=_cancel,
                    tool_calls=[],
                    is_agent_flow=False,
                    raw_response={"text": _cancel},
                )
                orchestrator.status_sync.persist_assistant_message(request.chat_id, wf.execution_for_api)
                return orchestrator.status_sync.build_api_response(execution_response=wf.execution_for_api)
        orchestrator._set_policy_pending(request.chat_id, False)
        if _intent_is_one_time_policy(wf):
            wf.bypass_policy_this_turn = True
            logger.info("[POLICY] BYPASS: Einmalige Freigabe für diesen Turn AKTIV.")
            wf.policy_injection_message = prompt_registry.get_directive("policy_injection_one_time")
            wf.user_text = f"{wf.user_text}{prompt_registry.get_directive('policy_user_text_suffix')}"
        elif _intent_is_policy_consent(wf):
            logger.info("[POLICY] STATE (DB): Pending-Status für Chat %s zurückgesetzt.", request.chat_id)

    if request.chat_id is not None:
        from backend.data.models import Message

        wf.last_model_message = (
            orchestrator.db.query(Message)
            .filter(Message.chat_id == request.chat_id, Message.role.in_(["assistant", "model"]))
            .order_by(Message.id.desc())
            .first()
        )
        wf.last_model_text = (wf.last_model_message.content or "" if wf.last_model_message else "").lower()
        if not wf.is_policy_response and _intent_is_policy_consent(wf) and intent_engine.is_policy_prompt_text(wf.last_model_text):
            wf.is_policy_response = True
            logger.warning("[POLICY] STATE FALLBACK: Consent-Antwort erkannt ohne DB-Pending-Flag (Chat %s).", request.chat_id)
            if _intent_is_one_time_policy(wf):
                wf.bypass_policy_this_turn = True
                logger.info("[POLICY] BYPASS: Einmalige Freigabe (Fallback) für diesen Turn AKTIV.")
                wf.policy_injection_message = prompt_registry.get_directive("policy_injection_one_time")
                wf.user_text = f"{wf.user_text}{prompt_registry.get_directive('policy_user_text_suffix')}"
            orchestrator._set_policy_pending(request.chat_id, False)
        if not wf.factcheck_prompt_pending:
            wf.factcheck_prompt_pending = "möchtest du jetzt einen faktencheck durchführen" in wf.last_model_text
        wf.is_policy_question = wf.is_policy_response or intent_engine.is_policy_prompt_text(wf.last_model_text)

    return None
