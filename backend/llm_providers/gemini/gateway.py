"""
Gemini Gateway – Diamond Standard Refactored

Zuständigkeiten:
- Tool-Loop Orchestrierung
- MoA-Routing (Mixture of Agents)
- Prompt-AST Aufbau
- DELEGATION an LinkRenderer für Link-Injection (keine I/O im Hot-Path)
"""

import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from .compiler import GeminiCompiler
from .link_renderer import get_link_renderer
from .constants import LIST_QUERY_TOKENS
from ..shared.base_gateway import BaseProviderGateway
from ..shared.moa import MOA_MODEL_HIERARCHY
from ..shared.utils import (
    _extract_tool_payload,
    _extract_websearch_sources_for_compaction,
)
from .service import GeminiServiceProvider
from backend.services.prompting.core.model import Prompt, PromptBlock

logger = logging.getLogger("janus_backend")


class GeminiGateway(BaseProviderGateway):
    """
    Diamond-Standard Gemini Provider Gateway.
    
    Kernaufgaben:
    1. Provider-spezifische Orchestrierung (Tool-Loop, MoA)
    2. Prompt-AST Komposition
    3. Link-Rendering DELEGATION an LinkRenderer (I/O-frei)
    """

    def __init__(self) -> None:
        self.service = GeminiServiceProvider()
        self.compiler = GeminiCompiler()
        self._link_renderer = get_link_renderer()

    @staticmethod
    def _sanitize_generate_response_kwargs(
        kwargs: Optional[Dict[str, Any]], *explicit_keys: str
    ) -> Dict[str, Any]:
        sanitized = dict(kwargs or {})
        for key in explicit_keys:
            sanitized.pop(key, None)
        return sanitized

    @staticmethod
    def _extract_grounding_query_count(grounding_metadata: Optional[Dict[str, Any]]) -> int:
        if not isinstance(grounding_metadata, dict):
            return 0
        raw_queries = grounding_metadata.get("web_search_queries")
        if not isinstance(raw_queries, list):
            raw_queries = grounding_metadata.get("webSearchQueries")
        if not isinstance(raw_queries, list):
            return 0
        return sum(1 for query in raw_queries if str(query or "").strip())

    @staticmethod
    def _build_gemini_request_attribution_ids(chat_id: Optional[int]) -> Dict[str, Optional[str]]:
        request_id = uuid.uuid4().hex
        session_id = str(chat_id) if chat_id is not None else None
        group_id = f"gemini-request:{session_id or 'sessionless'}:{request_id}"
        return {
            "attribution_group_id": group_id,
            "attribution_request_id": request_id,
            "attribution_session_id": session_id,
            "attribution_test_run_id": None,
        }

    @staticmethod
    def _build_gemini_attribution_metadata(
        *,
        component: str,
        request_kind: str,
        grounding_metadata: Optional[Dict[str, Any]],
        websearch_query_count: int,
        persistence_gap: Optional[str] = None,
        failed_components: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        grounding = grounding_metadata if isinstance(grounding_metadata, dict) else {}
        metadata: Dict[str, Any] = {
            "request_kind": request_kind,
            "component_scope": component,
            "grounding_metadata_present": bool(grounding),
            "grounding_query_count": GeminiGateway._extract_grounding_query_count(grounding),
            "websearch_query_count": int(websearch_query_count or 0),
        }
        grounding_chunks = grounding.get("groundingChunks")
        if isinstance(grounding_chunks, list):
            metadata["grounding_chunk_count"] = len(grounding_chunks)
        failed = [str(item).strip() for item in (failed_components or []) if str(item).strip()]
        if failed:
            metadata["failed_components"] = failed
        if persistence_gap:
            metadata["attribution_gap"] = str(persistence_gap)
        return metadata

    @staticmethod
    def _extract_visible_model_override(chat_history: Optional[List[Dict[str, Any]]]) -> Optional[str]:
        if not chat_history:
            return None
        for msg in chat_history:
            if msg.get("role") != "system":
                continue
            content = str(msg.get("content", ""))
            if "MODEL_OVERRIDE:" not in content:
                continue
            match = re.search(r"MODEL_OVERRIDE:\s*(\S+)", content)
            if match:
                return match.group(1).strip()
        return None

    @staticmethod
    def _persist_cost_entry_with_result(**kwargs: Any) -> bool:
        from backend.services.cost_service import create_cost_entry

        created_entry = create_cost_entry(**kwargs)
        return created_entry is not None

    def _persist_gemini_request_costs(
        self,
        *,
        db: Any,
        provider: Optional[str],
        model: Optional[str],
        chat_id: Optional[int],
        conversation_cost_eur: float,
        input_tokens: int,
        output_tokens: int,
        websearch_query_count: int,
        grounding_metadata: Optional[Dict[str, Any]],
        request_kind: str,
    ) -> Dict[str, Any]:
        attribution_ids = self._build_gemini_request_attribution_ids(chat_id)
        provider_name = str(provider or "gemini")
        model_name = str(model or "gemini")
        failed_components: List[str] = []

        if db is not None and websearch_query_count > 0:
            websearch_ok = self._persist_cost_entry_with_result(
                db=db,
                amount=round(websearch_query_count * 0.01, 6),
                model=model_name,
                provider=provider_name,
                source_type="websearch",
                context_details=f"query_count={websearch_query_count}",
                attribution_component="grounding_websearch",
                attribution_status="intern attribuiert",
                attribution_manual_override=False,
                attribution_metadata=self._build_gemini_attribution_metadata(
                    component="grounding_websearch",
                    request_kind=request_kind,
                    grounding_metadata=grounding_metadata,
                    websearch_query_count=websearch_query_count,
                ),
                **attribution_ids,
            )
            if websearch_ok:
                logger.info(
                    "GEMINI-WEBSEARCH-PERSIST: Saved %d queries (%.4f€)",
                    websearch_query_count,
                    websearch_query_count * 0.01,
                )
            else:
                failed_components.append("grounding_websearch")
                logger.warning(
                    "GEMINI-WEBSEARCH-PERSIST: Attribution record missing for %d queries.",
                    websearch_query_count,
                )

        conversation_status = (
            "intern attribuiert" if not failed_components else "nicht eindeutig attribuiert"
        )
        conversation_gap = None
        if failed_components:
            conversation_gap = f"component_persist_failed:{','.join(failed_components)}"

        conversation_component_cost = max(
            0.0,
            float(conversation_cost_eur or 0.0) - round(float(websearch_query_count or 0) * 0.01, 6),
        )

        conversation_persisted = False
        if db is not None and conversation_component_cost > 0:
            conversation_persisted = self._persist_cost_entry_with_result(
                db=db,
                amount=conversation_component_cost,
                model=model_name,
                provider=provider_name,
                source_type="conversation",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                attribution_component="conversation",
                attribution_status=conversation_status,
                attribution_manual_override=False,
                attribution_metadata=self._build_gemini_attribution_metadata(
                    component="conversation",
                    request_kind=request_kind,
                    grounding_metadata=grounding_metadata,
                    websearch_query_count=websearch_query_count,
                    persistence_gap=conversation_gap,
                    failed_components=failed_components,
                ),
                **attribution_ids,
            )
            if conversation_persisted:
                logger.info(
                    "GEMINI-COST-PERSIST: Saved %.6f€ for %s",
                    conversation_component_cost,
                    model_name,
                )
            else:
                failed_components.append("conversation")
                logger.warning(
                    "GEMINI-COST-PERSIST: Attribution record missing for %s.",
                    model_name,
                )

        elif db is not None and conversation_cost_eur > 0:
            conversation_persisted = True

        final_status = "intern attribuiert"
        if failed_components or not conversation_persisted:
            final_status = "nicht eindeutig attribuiert"

        try:
            from backend.services.cost_service import emit_cost_tracking_debug_event

            emit_cost_tracking_debug_event(
                event_type="gemini_request_cost_attribution",
                provider=provider_name,
                model=model_name,
                source_type="conversation",
                amount=float(conversation_cost_eur or 0.0),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                attribution_group_id=attribution_ids["attribution_group_id"],
                attribution_request_id=attribution_ids["attribution_request_id"],
                attribution_session_id=attribution_ids["attribution_session_id"],
                attribution_test_run_id=attribution_ids["attribution_test_run_id"],
                attribution_status=final_status,
                attribution_component="gemini_request",
                metadata={
                    "request_kind": request_kind,
                    "websearch_query_count": int(websearch_query_count or 0),
                    "failed_components": failed_components,
                    "conversation_persisted": conversation_persisted,
                    "websearch_persisted": websearch_query_count <= 0 or "grounding_websearch" not in failed_components,
                },
            )
        except Exception:
            logger.warning("GEMINI-COST-DEBUG: request summary log failed", exc_info=True)

        return {
            **attribution_ids,
            "attribution_status": final_status,
            "failed_components": failed_components,
            "conversation_persisted": conversation_persisted,
            "websearch_persisted": websearch_query_count <= 0 or "grounding_websearch" not in failed_components,
        }

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
        background_tasks: Any = None,
        bypass_policy: bool = False,
        tool_results: Optional[List[Dict[str, Any]]] = None,
        trimmed_tool_results: Optional[List[Dict[str, Any]]] = None,
        websearch_synthesis_instruction: Optional[str] = None,
        provider_service: Optional[GeminiServiceProvider] = None,
        _gemini_engine_owned_tool_loop: bool = False,
        force_tool_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        JANUS ZWANGSJACKE: Einziger Exit-Punkt garantiert Renderer-Aufruf.
        
        Alle Pfade führen zu final_result, dann wird render_final_response erzwungen.
        """
        # 💎 ZWANGSJACKE: Einziger Exit-Punkt
        final_result, metadata = await self._reason_and_respond_inner(
            provider=provider,
            model=model,
            api_key=api_key,
            chat_history=chat_history,
            context_manager=context_manager,
            db=db,
            user_prompt=user_prompt,
            chat_id=chat_id,
            tool_executor=tool_executor,
            allowed_skill_ids=allowed_skill_ids,
            max_tool_rounds=max_tool_rounds,
            tools_override=tools_override,
            disable_tools=disable_tools,
            image_data=image_data,
            background_tasks=background_tasks,
            bypass_policy=bypass_policy,
            tool_results=tool_results,
            trimmed_tool_results=trimmed_tool_results,
            websearch_synthesis_instruction=websearch_synthesis_instruction,
            provider_service=provider_service,
            _gemini_engine_owned_tool_loop=_gemini_engine_owned_tool_loop,
            force_tool_name=force_tool_name,
        )
        
        # --- 🔒 ZWANGSJACKE: ABSOLUT LETZTER HOOK ---
        # 💎 AGGREGATOR FIX: Gateway ist jetzt "dummer" Überbringer.
        # Das Rendering findet im Orchestrator statt (einmalig nach dem Loop).
        # Wir geben nur die Rohdaten zurück – der Orchestrator ruft den Renderer.
        
        # Nur noch Metadaten anreichern für den Orchestrator
        final_result["_preserved_metadata"] = metadata
        final_result.setdefault("tool_results", tool_results or [])
        final_result.setdefault("wiki_results", [])  # Wird vom Orchestrator gefüllt
        
        return final_result
    
    async def _reason_and_respond_inner(
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
        background_tasks: Any = None,
        bypass_policy: bool = False,
        tool_results: Optional[List[Dict[str, Any]]] = None,
        trimmed_tool_results: Optional[List[Dict[str, Any]]] = None,
        websearch_synthesis_instruction: Optional[str] = None,
        provider_service: Optional[GeminiServiceProvider] = None,
        _gemini_engine_owned_tool_loop: bool = False,
        force_tool_name: Optional[str] = None,
    ) -> tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Interne Implementierung - gibt (final_result, metadata) zurück.
        Keine direkten returns, immer Tuple für Zwangsdurchlauf.
        """
        lowered_prompt = str(user_prompt or "").strip().lower()
        is_list_query = self._is_list_query(lowered_prompt)

        active_service = provider_service or self.service

        # 💎 HARTES GEMINI MOA-ROUTING: Erzwinge Modell-Wechsel für system.websearch
        original_model = model
        if allowed_skill_ids and "system.websearch" in allowed_skill_ids:
            from backend.services.tool_manager import tool_manager

            tier = tool_manager.get_optimal_model_tier("system.websearch", "gemini")
            forced_model = MOA_MODEL_HIERARCHY["gemini"].get(tier, model)

            if forced_model != model:
                logger.info(f"💎 GEMINI MOA: Forciere Modell-Switch von {model} auf {forced_model}")
                model = forced_model

        if tool_results is None:
            # ═══════════════════════════════════════════════════════════════════
            # FIX-035: PRECEDENCE GUARD — Drill-Down Kill-Switch
            # ═══════════════════════════════════════════════════════════════════
            # _run_drill_down_list_research hardcodes a system.websearch call,
            # bypassing allowed_skill_ids entirely.  When the orchestrator has
            # removed websearch (personal recall), the drill-down MUST be
            # blocked — otherwise we get the WEBSEARCH_FAILED cascade.
            # ═══════════════════════════════════════════════════════════════════
            _websearch_allowed = (
                allowed_skill_ids is None  # None = no filtering = all allowed
                or "system.websearch" in (allowed_skill_ids or [])
            )
            _use_drill_down = is_list_query and _websearch_allowed

            if not _use_drill_down:
                if _gemini_engine_owned_tool_loop:
                    logger.info(
                        "[GEMINI-FIX] Gemini: Orchestrator-owned tool loop — eine API-Runde pro "
                        "Aufruf (interner Multi-Runden-Loop deaktiviert)."
                    )
                    loop_result = await self._run_engine_owned_gemini_turn(
                        provider=provider,
                        model=model,
                        api_key=api_key,
                        chat_history=chat_history,
                        user_prompt=user_prompt,
                        provider_service=active_service,
                        tool_executor=tool_executor,
                        allowed_skill_ids=allowed_skill_ids,
                        max_tool_rounds=max_tool_rounds,
                        background_tasks=background_tasks,
                        image_data=image_data,
                        bypass_policy=bypass_policy,
                        is_list_query=is_list_query,
                        db=db,
                        chat_id=chat_id,
                        force_tool_name=force_tool_name,
                    )
                else:
                    if is_list_query and not _websearch_allowed:
                        logger.info(
                            "[PRECEDENCE-GUARD-035] Drill-Down BLOCKED — websearch not in "
                            "allowed_skill_ids (personal recall). Falling back to simple tool-loop."
                        )
                    else:
                        logger.info("Gemini Silo: Führe einfachen Tool-Loop aus.")
                    loop_result = await self._run_simple_tool_loop(
                        provider=provider,
                        model=model,
                        api_key=api_key,
                        chat_history=chat_history,
                        user_prompt=user_prompt,
                        provider_service=active_service,
                        tool_executor=tool_executor,
                        allowed_skill_ids=allowed_skill_ids,
                        max_tool_rounds=max_tool_rounds,
                        background_tasks=background_tasks,
                        image_data=image_data,
                        bypass_policy=bypass_policy,
                        is_list_query=is_list_query,
                        db=db,
                        chat_id=chat_id,
                        force_tool_name=force_tool_name,
                    )
                # Extrahiere Metadata aus dem Loop-Ergebnis
                loop_metadata = (
                    loop_result.pop("_preserved_metadata", None) 
                    if isinstance(loop_result, dict) else None
                )
                return loop_result, loop_metadata

            # List Query Path (only when websearch is explicitly allowed)
            drill_result = await self._run_drill_down_list_research(
                provider=provider,
                model=model,
                api_key=api_key,
                chat_history=chat_history,
                user_prompt=user_prompt,
                provider_service=active_service,
                tool_executor=tool_executor,
                bypass_policy=bypass_policy,
            )
            drill_metadata = (
                drill_result.pop("_preserved_metadata", None) 
                if isinstance(drill_result, dict) else None
            )
            return drill_result, drill_metadata

        logger.info("Gemini Silo Gateway aktiv: finalisiere grounded Websearch-Antwort.")

        # 💎 DIAMOND RUNTIME BRIDGE: Lade Skill-Directives als Synthese-Basis
        if not websearch_synthesis_instruction and allowed_skill_ids:
            from backend.services.tool_manager import tool_manager as _tm
            for _sid in (allowed_skill_ids or []):
                _sd = _tm.get_synthesis_directives(str(_sid))
                if _sd:
                    websearch_synthesis_instruction = _sd
                    logger.info("SKILL-DIRECTIVE SYNTHESIS: Verwende '%s' Direktive als Synthese-Basis.", _sid)
                    break

        research_context = self.build_websearch_context_block(trimmed_tool_results or [])
        if research_context and websearch_synthesis_instruction and "<context>" not in websearch_synthesis_instruction:
            websearch_synthesis_instruction = f"{websearch_synthesis_instruction}\n\n{research_context}"

        websearch_synthesis_instruction = self._ensure_grounding_rules(
            base_instruction=websearch_synthesis_instruction or "Antworte basierend auf den Fakten.",
            is_list_query=is_list_query,
        )

        final_messages = self._build_final_messages(chat_history, websearch_synthesis_instruction)

        # 💎 GEMINI MOA RÜCKSPRUNG: Finale Synthese immer mit ursprünglichem Modell
        synthesis_model = original_model if allowed_skill_ids and "system.websearch" in allowed_skill_ids else model

        response = await active_service.generate_response(
            api_key=api_key,
            model=synthesis_model,
            messages=final_messages,
            tools=None,
            image_data=None,
        )

        response.setdefault("tool_results", tool_results)
        response.setdefault("provider", provider)
        response.setdefault("model", model)
        
        # Extrahiere Metadata für Zwangsdurchlauf
        response_metadata = (
            response.pop("_preserved_metadata", None) 
            if isinstance(response, dict) else None
        ) or response.get("grounding_metadata") or response.get("groundingMetadata")
        
        return response, response_metadata

    async def _run_engine_owned_gemini_turn(self, **kwargs) -> Dict[str, Any]:
        """
        Eine Gemini-API-Runde mit Tools; Tool-Ausfuehrung bleibt beim Orchestrator
        (execution_engine), damit [GEMINI-FIX] und Hard-Loop-Breaker pro Runde greifen.
        """
        from backend.llm_providers.shared.utils import (
            _filter_tools_by_skill_ids,
            _build_tool_definitions_for_llm,
            _prevalidate_tool_calls,
            _apply_routing_quality_guards,
        )
        passthrough_kwargs = dict(kwargs or {})
        provider = passthrough_kwargs.pop("provider", None)
        model = passthrough_kwargs.pop("model", None)
        api_key = passthrough_kwargs.pop("api_key", None)
        chat_history = passthrough_kwargs.pop("chat_history", [])
        user_prompt = passthrough_kwargs.pop("user_prompt", "")
        allowed_skill_ids = passthrough_kwargs.pop("allowed_skill_ids", None)
        passthrough_kwargs.pop("tool_executor", None)
        passthrough_kwargs.pop("max_tool_rounds", None)
        passthrough_kwargs.pop("background_tasks", None)
        image_data = passthrough_kwargs.pop("image_data", None)
        force_tool_name = str(passthrough_kwargs.pop("force_tool_name", "") or "").strip() or None
        provider_service = passthrough_kwargs.pop("provider_service", None) or self.service
        db = passthrough_kwargs.pop("db", None)
        chat_id = passthrough_kwargs.pop("chat_id", None)
        passthrough_kwargs.pop("is_list_query", None)

        from backend.llm_providers.shared.moa import resolve_moa_model

        user_base_model = model
        visible_override = self._extract_visible_model_override(chat_history)
        if allowed_skill_ids and "system.websearch" in allowed_skill_ids:
            tool_execution_model = visible_override or "gemini-3-flash-preview"
            moa_active = bool(visible_override)
            if visible_override:
                logger.info("GEMINI-OVERRIDE: Visible override '%s' applied for system.websearch.", visible_override)
            elif tool_execution_model != user_base_model:
                logger.info("GEMINI-WEBSEARCH-POLICY: Defaulting system.websearch to '%s'.", tool_execution_model)
        else:
            tool_execution_model, moa_active = resolve_moa_model(
                provider=provider,
                user_base_model=user_base_model,
                allowed_skill_ids=allowed_skill_ids,
            )
            if visible_override:
                tool_execution_model = visible_override
                moa_active = True
                logger.info("GEMINI-OVERRIDE: Forced model '%s' successfully applied.", visible_override)

        if moa_active and tool_execution_model != user_base_model:
            logger.info(
                "GEMINI MOA: Force model switch %s -> %s",
                user_base_model,
                tool_execution_model,
            )

        current_chat_history = list(chat_history)
        loop_cost_eur = 0.0
        loop_input_tokens = 0
        loop_output_tokens = 0
        loop_websearch_queries = 0

        all_available_tools = _filter_tools_by_skill_ids(allowed_skill_ids)
        tools_for_call = _build_tool_definitions_for_llm(all_available_tools)

        loop_kwargs = passthrough_kwargs.get("passthrough_kwargs")
        if loop_kwargs is None:
            loop_kwargs = {}
        loop_kwargs = self._sanitize_generate_response_kwargs(
            loop_kwargs,
            "api_key",
            "model",
            "messages",
            "tools",
            "image_data",
        )

        response = await provider_service.generate_response(
            api_key=api_key,
            model=tool_execution_model,
            messages=current_chat_history,
            tools=tools_for_call,
            image_data=image_data,
            force_tool_name=force_tool_name,
            **loop_kwargs,
        )

        round_cost = response.get("cost") or {}
        round_usage = response.get("usage") or {}
        loop_cost_eur += float(round_cost.get("total_cost", 0.0))
        loop_input_tokens += int(round_usage.get("input_tokens", 0))
        loop_output_tokens += int(round_usage.get("output_tokens", 0))
        grounding_metadata = response.get("grounding_metadata") or {}
        raw_queries = grounding_metadata.get("web_search_queries") or grounding_metadata.get("webSearchQueries") or []
        valid_queries = [str(query or "").strip() for query in raw_queries if str(query or "").strip()]
        search_cost = len(valid_queries) * 0.01
        loop_websearch_queries += len(valid_queries)
        loop_cost_eur += search_cost
        if valid_queries:
            logger.info(
                "GEMINI-SEARCH-BILLING: %d queries billed at %.4f EUR.",
                len(valid_queries),
                search_cost,
            )

        if response.get("type") != "tool_code":
            final_grounding_metadata = grounding_metadata
            if moa_active:
                logger.info(
                    "SKILL-MOA RETURN: Tool loop finished with '%s'.",
                    tool_execution_model,
                )
                synthesis_response = await provider_service.generate_response(
                    api_key=api_key,
                    model=tool_execution_model,
                    messages=current_chat_history,
                    tools=None,
                    image_data=None,
                )
                synthesis_response = _apply_routing_quality_guards(
                    synthesis_response, current_chat_history
                )
                synthesis_cost = synthesis_response.get("cost") or {}
                synthesis_usage = synthesis_response.get("usage") or {}
                loop_cost_eur += float(synthesis_cost.get("total_cost", 0.0))
                loop_input_tokens += int(synthesis_usage.get("input_tokens", 0))
                loop_output_tokens += int(synthesis_usage.get("output_tokens", 0))
                synthesis_grounding_metadata = synthesis_response.get("grounding_metadata") or {}
                synthesis_raw_queries = (
                    synthesis_grounding_metadata.get("web_search_queries")
                    or synthesis_grounding_metadata.get("webSearchQueries")
                    or []
                )
                synthesis_valid_queries = [
                    str(query or "").strip()
                    for query in synthesis_raw_queries
                    if str(query or "").strip()
                ]
                synthesis_search_cost = len(synthesis_valid_queries) * 0.01
                loop_websearch_queries += len(synthesis_valid_queries)
                loop_cost_eur += synthesis_search_cost
                if synthesis_valid_queries:
                    logger.info(
                        "GEMINI-SEARCH-BILLING: %d queries billed at %.4f EUR.",
                        len(synthesis_valid_queries),
                        synthesis_search_cost,
                    )
                synthesis_response["cost"] = {"total_cost": loop_cost_eur}
                synthesis_response["usage"] = {
                    "input_tokens": loop_input_tokens,
                    "output_tokens": loop_output_tokens,
                }
                attribution_result = self._persist_gemini_request_costs(
                    db=db,
                    provider=provider,
                    model=tool_execution_model,
                    chat_id=chat_id,
                    conversation_cost_eur=loop_cost_eur,
                    input_tokens=loop_input_tokens,
                    output_tokens=loop_output_tokens,
                    websearch_query_count=loop_websearch_queries,
                    grounding_metadata=synthesis_grounding_metadata or grounding_metadata,
                    request_kind="engine_owned_tool_loop",
                )
                synthesis_response["_preserved_metadata"] = (
                    synthesis_response.get("grounding_metadata")
                    or synthesis_response.get("groundingMetadata")
                )
                synthesis_response["_cost_attribution"] = attribution_result
                synthesis_response["moa_tool_model"] = tool_execution_model
                synthesis_response["moa_synthesis_model"] = tool_execution_model
                synthesis_response.setdefault("provider", provider)
                synthesis_response.setdefault("model", model)
                return synthesis_response

            response = _apply_routing_quality_guards(response, current_chat_history)
            response["cost"] = {"total_cost": loop_cost_eur}
            response["usage"] = {
                "input_tokens": loop_input_tokens,
                "output_tokens": loop_output_tokens,
            }
            attribution_result = self._persist_gemini_request_costs(
                db=db,
                provider=provider,
                model=tool_execution_model,
                chat_id=chat_id,
                conversation_cost_eur=loop_cost_eur,
                input_tokens=loop_input_tokens,
                output_tokens=loop_output_tokens,
                websearch_query_count=loop_websearch_queries,
                grounding_metadata=final_grounding_metadata,
                request_kind="engine_owned_tool_loop",
            )
            response["_preserved_metadata"] = response.get("grounding_metadata") or response.get(
                "groundingMetadata"
            )
            response["_cost_attribution"] = attribution_result
            response.setdefault("provider", provider)
            response.setdefault("model", model)
            return response

        tool_calls = response.get("tool_calls", [])
        preflight = _prevalidate_tool_calls(tool_calls, user_prompt=user_prompt)
        validated_tool_calls = preflight["valid_calls"]

        if not validated_tool_calls:
            return response

        response["tool_calls"] = validated_tool_calls
        response["cost"] = {"total_cost": loop_cost_eur}
        response["usage"] = {
            "input_tokens": loop_input_tokens,
            "output_tokens": loop_output_tokens,
        }
        attribution_result = self._persist_gemini_request_costs(
            db=db,
            provider=provider,
            model=tool_execution_model,
            chat_id=chat_id,
            conversation_cost_eur=loop_cost_eur,
            input_tokens=loop_input_tokens,
            output_tokens=loop_output_tokens,
            websearch_query_count=loop_websearch_queries,
            grounding_metadata=grounding_metadata,
            request_kind="engine_owned_tool_loop",
        )
        response["_preserved_metadata"] = response.get("grounding_metadata") or response.get(
            "groundingMetadata"
        )
        response["_cost_attribution"] = attribution_result
        response.setdefault("provider", provider)
        response.setdefault("model", model)
        return response

    async def _run_simple_tool_loop(self, **kwargs) -> Dict[str, Any]:
        from backend.llm_providers.shared.tool_loop_runner import TRANSPORT_TOOL_LOOP_RUNNER_ENABLED

        if TRANSPORT_TOOL_LOOP_RUNNER_ENABLED:
            return await self._run_simple_tool_loop_with_runner(**kwargs)
        return await self._run_legacy_simple_tool_loop(**kwargs)

    async def _run_legacy_simple_tool_loop(self, **kwargs) -> Dict[str, Any]:
        """
        Interne Implementierung des Tool-Loops.
        MoA-Integration: Tool-Loop mit optimiertem Modell, Synthese mit User-Modell.
        """
        from backend.llm_providers.shared.utils import (
            _filter_tools_by_skill_ids,
            _build_tool_definitions_for_llm,
            _prevalidate_tool_calls,
            _apply_routing_quality_guards,
        )
        passthrough_kwargs = dict(kwargs or {})
        provider = passthrough_kwargs.pop("provider", None)
        model = passthrough_kwargs.pop("model", None)
        api_key = passthrough_kwargs.pop("api_key", None)
        chat_history = passthrough_kwargs.pop("chat_history", [])
        user_prompt = passthrough_kwargs.pop("user_prompt", "")
        allowed_skill_ids = passthrough_kwargs.pop("allowed_skill_ids", None)
        tool_executor = passthrough_kwargs.pop("tool_executor", None)
        max_tool_rounds = passthrough_kwargs.pop("max_tool_rounds", 5)
        background_tasks = passthrough_kwargs.pop("background_tasks", None)
        image_data = passthrough_kwargs.pop("image_data", None)
        force_tool_name = str(passthrough_kwargs.pop("force_tool_name", "") or "").strip() or None
        provider_service = passthrough_kwargs.pop("provider_service", None) or self.service
        db = passthrough_kwargs.pop("db", None)
        chat_id = passthrough_kwargs.pop("chat_id", None)
        is_list_query = passthrough_kwargs.pop("is_list_query", None)
        if is_list_query is None:
            is_list_query = self._is_list_query(str(user_prompt or "").strip().lower())

        if is_list_query:
            previous_round_cap = max_tool_rounds
            max_tool_rounds = max(max_tool_rounds, 12)
            if max_tool_rounds != previous_round_cap:
                logger.info("DIAMOND-RESEARCH: Listen-Anfrage. Max Tool-Rounds auf %s erhoeht.", max_tool_rounds)

        from backend.llm_providers.shared.moa import resolve_moa_model

        user_base_model = model
        visible_override = self._extract_visible_model_override(chat_history)
        if allowed_skill_ids and "system.websearch" in allowed_skill_ids:
            tool_execution_model = visible_override or "gemini-3-flash-preview"
            moa_active = bool(visible_override)
            if visible_override:
                logger.info("GEMINI-OVERRIDE: Visible override '%s' applied for system.websearch.", visible_override)
            elif tool_execution_model != user_base_model:
                logger.info("GEMINI-WEBSEARCH-POLICY: Defaulting system.websearch to '%s'.", tool_execution_model)
        else:
            tool_execution_model, moa_active = resolve_moa_model(
                provider=provider,
                user_base_model=user_base_model,
                allowed_skill_ids=allowed_skill_ids,
            )
            if visible_override:
                tool_execution_model = visible_override
                moa_active = True
                logger.info("GEMINI-OVERRIDE: Forced model '%s' successfully applied.", visible_override)

        if moa_active and tool_execution_model != user_base_model:
            logger.info(
                "GEMINI MOA: Force model switch %s -> %s",
                user_base_model,
                tool_execution_model,
            )

        current_round = 0
        current_chat_history = list(chat_history)
        loop_cost_eur = 0.0
        loop_input_tokens = 0
        loop_output_tokens = 0
        loop_websearch_queries = 0

        all_available_tools = _filter_tools_by_skill_ids(allowed_skill_ids)
        tools_for_call = _build_tool_definitions_for_llm(all_available_tools)

        while current_round < max_tool_rounds:
            current_round += 1

            loop_kwargs = passthrough_kwargs.get("passthrough_kwargs")
            if loop_kwargs is None:
                loop_kwargs = {}
            loop_kwargs = self._sanitize_generate_response_kwargs(
                loop_kwargs,
                "api_key",
                "model",
                "messages",
                "tools",
                "image_data",
            )

            round_force_tool_name = force_tool_name if current_round == 1 else None
            response = await provider_service.generate_response(
                api_key=api_key,
                model=tool_execution_model,
                messages=current_chat_history,
                tools=tools_for_call,
                image_data=image_data if current_round == 1 else None,
                force_tool_name=round_force_tool_name,
                **loop_kwargs,
            )

            round_cost = response.get("cost") or {}
            round_usage = response.get("usage") or {}
            loop_cost_eur += float(round_cost.get("total_cost", 0.0))
            loop_input_tokens += int(round_usage.get("input_tokens", 0))
            loop_output_tokens += int(round_usage.get("output_tokens", 0))
            grounding_metadata = response.get("grounding_metadata") or {}
            raw_queries = grounding_metadata.get("web_search_queries") or grounding_metadata.get("webSearchQueries") or []
            valid_queries = [str(query or "").strip() for query in raw_queries if str(query or "").strip()]
            search_cost = len(valid_queries) * 0.01
            loop_websearch_queries += len(valid_queries)
            loop_cost_eur += search_cost
            if valid_queries:
                logger.info(
                    "GEMINI-SEARCH-BILLING: %d queries billed at %.4f EUR.",
                    len(valid_queries),
                    search_cost,
                )

            if response.get("type") != "tool_code":
                if moa_active:
                    logger.info(
                        "SKILL-MOA RETURN: Tool-Loop abgeschlossen mit '%s'.",
                        tool_execution_model,
                    )
                    synthesis_response = await provider_service.generate_response(
                        api_key=api_key,
                        model=tool_execution_model,
                        messages=current_chat_history,
                        tools=None,
                        image_data=None,
                    )
                    synthesis_response = _apply_routing_quality_guards(synthesis_response, current_chat_history)
                    synthesis_cost = synthesis_response.get("cost") or {}
                    synthesis_usage = synthesis_response.get("usage") or {}
                    loop_cost_eur += float(synthesis_cost.get("total_cost", 0.0))
                    loop_input_tokens += int(synthesis_usage.get("input_tokens", 0))
                    loop_output_tokens += int(synthesis_usage.get("output_tokens", 0))
                    synthesis_grounding_metadata = synthesis_response.get("grounding_metadata") or {}
                    synthesis_raw_queries = (
                        synthesis_grounding_metadata.get("web_search_queries")
                        or synthesis_grounding_metadata.get("webSearchQueries")
                        or []
                    )
                    synthesis_valid_queries = [
                        str(query or "").strip()
                        for query in synthesis_raw_queries
                        if str(query or "").strip()
                    ]
                    synthesis_search_cost = len(synthesis_valid_queries) * 0.01
                    loop_websearch_queries += len(synthesis_valid_queries)
                    loop_cost_eur += synthesis_search_cost
                    if synthesis_valid_queries:
                        logger.info(
                            "GEMINI-SEARCH-BILLING: %d queries billed at %.4f EUR.",
                            len(synthesis_valid_queries),
                            synthesis_search_cost,
                        )
                    synthesis_response["cost"] = {"total_cost": loop_cost_eur}
                    synthesis_response["usage"] = {
                        "input_tokens": loop_input_tokens,
                        "output_tokens": loop_output_tokens,
                    }
                    attribution_result = self._persist_gemini_request_costs(
                        db=db,
                        provider=provider,
                        model=tool_execution_model,
                        chat_id=chat_id,
                        conversation_cost_eur=loop_cost_eur,
                        input_tokens=loop_input_tokens,
                        output_tokens=loop_output_tokens,
                        websearch_query_count=loop_websearch_queries,
                        grounding_metadata=synthesis_grounding_metadata or grounding_metadata,
                        request_kind="simple_tool_loop",
                    )
                    synthesis_response["_preserved_metadata"] = synthesis_response.get("grounding_metadata") or synthesis_response.get("groundingMetadata")
                    synthesis_response["_cost_attribution"] = attribution_result
                    synthesis_response["moa_tool_model"] = tool_execution_model
                    synthesis_response["moa_synthesis_model"] = tool_execution_model
                    return synthesis_response

                response = _apply_routing_quality_guards(response, current_chat_history)
                response["cost"] = {"total_cost": loop_cost_eur}
                response["usage"] = {
                    "input_tokens": loop_input_tokens,
                    "output_tokens": loop_output_tokens,
                }
                attribution_result = self._persist_gemini_request_costs(
                    db=db,
                    provider=provider,
                    model=tool_execution_model,
                    chat_id=chat_id,
                    conversation_cost_eur=loop_cost_eur,
                    input_tokens=loop_input_tokens,
                    output_tokens=loop_output_tokens,
                    websearch_query_count=loop_websearch_queries,
                    grounding_metadata=grounding_metadata,
                    request_kind="simple_tool_loop",
                )
                response["_preserved_metadata"] = response.get("grounding_metadata") or response.get("groundingMetadata")
                response["_cost_attribution"] = attribution_result
                return response

            tool_calls = response.get("tool_calls", [])
            preflight = _prevalidate_tool_calls(tool_calls, user_prompt=user_prompt)
            validated_tool_calls = preflight["valid_calls"]

            if not validated_tool_calls:
                return response

            executor_results = await tool_executor.execute_tool_calls(validated_tool_calls)

            current_chat_history = self.service.prepare_history_for_second_call(
                chat_history=current_chat_history,
                raw_assistant_response=response.get("raw_assistant_response"),
                tool_results=executor_results,
            )

        return {"text": "Maximale Tool-Runden erreicht.", "tool_limit_reached": True}

    async def _run_simple_tool_loop_with_runner(self, **kwargs) -> Dict[str, Any]:
        from backend.llm_providers.shared.moa import resolve_moa_model
        from backend.llm_providers.shared.tool_loop_runner import (
            NonToolResponseAction,
            ToolLoopContext,
            ToolLoopRunner,
        )
        from backend.llm_providers.shared.utils import (
            _apply_routing_quality_guards,
            _build_tool_definitions_for_llm,
            _filter_tools_by_skill_ids,
            _prevalidate_tool_calls,
        )

        passthrough_kwargs = dict(kwargs or {})
        provider = passthrough_kwargs.pop("provider", None)
        model = passthrough_kwargs.pop("model", None)
        api_key = passthrough_kwargs.pop("api_key", None)
        chat_history = passthrough_kwargs.pop("chat_history", [])
        user_prompt = passthrough_kwargs.pop("user_prompt", "")
        allowed_skill_ids = passthrough_kwargs.pop("allowed_skill_ids", None)
        tool_executor = passthrough_kwargs.pop("tool_executor", None)
        max_tool_rounds = passthrough_kwargs.pop("max_tool_rounds", 5)
        passthrough_kwargs.pop("background_tasks", None)
        image_data = passthrough_kwargs.pop("image_data", None)
        force_tool_name = str(passthrough_kwargs.pop("force_tool_name", "") or "").strip() or None
        provider_service = passthrough_kwargs.pop("provider_service", None) or self.service
        db = passthrough_kwargs.pop("db", None)
        chat_id = passthrough_kwargs.pop("chat_id", None)
        is_list_query = passthrough_kwargs.pop("is_list_query", None)
        if is_list_query is None:
            is_list_query = self._is_list_query(str(user_prompt or "").strip().lower())

        round_state: Dict[str, Any] = {"grounding_metadata": {}}

        context = ToolLoopContext(
            provider=str(provider or "gemini"),
            model=model,
            api_key=api_key,
            chat_history=list(chat_history),
            user_prompt=user_prompt,
            allowed_skill_ids=allowed_skill_ids,
            tool_executor=tool_executor,
            max_tool_rounds=max_tool_rounds,
            image_data=image_data,
            force_tool_name=force_tool_name,
            passthrough_kwargs=passthrough_kwargs,
        )

        def resolve_gemini_execution_model(loop_context: ToolLoopContext) -> Tuple[str, bool]:
            user_base_model = loop_context.model
            visible_override = self._extract_visible_model_override(loop_context.chat_history)
            if loop_context.allowed_skill_ids and "system.websearch" in loop_context.allowed_skill_ids:
                tool_execution_model = visible_override or "gemini-3-flash-preview"
                moa_active = bool(visible_override)
                if visible_override:
                    logger.info(
                        "GEMINI-OVERRIDE: Visible override '%s' applied for system.websearch.",
                        visible_override,
                    )
                elif tool_execution_model != user_base_model:
                    logger.info(
                        "GEMINI-WEBSEARCH-POLICY: Defaulting system.websearch to '%s'.",
                        tool_execution_model,
                    )
            else:
                tool_execution_model, moa_active = resolve_moa_model(
                    provider=loop_context.provider,
                    user_base_model=user_base_model,
                    allowed_skill_ids=loop_context.allowed_skill_ids,
                )
                if visible_override:
                    tool_execution_model = visible_override
                    moa_active = True
                    logger.info(
                        "GEMINI-OVERRIDE: Forced model '%s' successfully applied.",
                        visible_override,
                    )

            if moa_active and tool_execution_model != user_base_model:
                logger.info(
                    "GEMINI MOA: Force model switch %s -> %s",
                    user_base_model,
                    tool_execution_model,
                )
            return tool_execution_model, moa_active

        def resolve_gemini_max_tool_rounds(loop_context: ToolLoopContext) -> int:
            effective_rounds = loop_context.max_tool_rounds
            if is_list_query:
                previous_round_cap = effective_rounds
                effective_rounds = max(effective_rounds, 12)
                if effective_rounds != previous_round_cap:
                    logger.info(
                        "DIAMOND-RESEARCH: Listen-Anfrage. Max Tool-Rounds auf %s erhoeht.",
                        effective_rounds,
                    )
            return effective_rounds

        def on_gemini_round_response(response: Dict[str, Any], loop_context: ToolLoopContext) -> None:
            grounding_metadata = response.get("grounding_metadata") or {}
            round_state["grounding_metadata"] = grounding_metadata
            raw_queries = (
                grounding_metadata.get("web_search_queries")
                or grounding_metadata.get("webSearchQueries")
                or []
            )
            valid_queries = [str(query or "").strip() for query in raw_queries if str(query or "").strip()]
            search_cost = len(valid_queries) * 0.01
            loop_context.loop_websearch_queries += len(valid_queries)
            loop_context.loop_cost_eur += search_cost
            if valid_queries:
                logger.info(
                    "GEMINI-SEARCH-BILLING: %d queries billed at %.4f EUR.",
                    len(valid_queries),
                    search_cost,
                )

        def _apply_gemini_grounding_cost(
            response: Dict[str, Any],
            loop_context: ToolLoopContext,
        ) -> Dict[str, Any]:
            grounding_metadata = response.get("grounding_metadata") or {}
            raw_queries = (
                grounding_metadata.get("web_search_queries")
                or grounding_metadata.get("webSearchQueries")
                or []
            )
            valid_queries = [str(query or "").strip() for query in raw_queries if str(query or "").strip()]
            search_cost = len(valid_queries) * 0.01
            loop_context.loop_websearch_queries += len(valid_queries)
            loop_context.loop_cost_eur += search_cost
            if valid_queries:
                logger.info(
                    "GEMINI-SEARCH-BILLING: %d queries billed at %.4f EUR.",
                    len(valid_queries),
                    search_cost,
                )
            return grounding_metadata

        async def handle_non_tool_response(
            response: Dict[str, Any],
            loop_context: ToolLoopContext,
            round_force: Optional[str],
        ) -> NonToolResponseAction:
            grounding_metadata = round_state.get("grounding_metadata") or {}

            if loop_context.moa_active:
                logger.info(
                    "SKILL-MOA RETURN: Tool-Loop abgeschlossen mit '%s'.",
                    loop_context.tool_execution_model,
                )
                synthesis_response = await provider_service.generate_response(
                    api_key=api_key,
                    model=loop_context.tool_execution_model,
                    messages=loop_context.chat_history,
                    tools=None,
                    image_data=None,
                )
                synthesis_response = _apply_routing_quality_guards(
                    synthesis_response,
                    loop_context.chat_history,
                )
                synthesis_cost = synthesis_response.get("cost") or {}
                synthesis_usage = synthesis_response.get("usage") or {}
                loop_context.loop_cost_eur += float(synthesis_cost.get("total_cost", 0.0))
                loop_context.loop_input_tokens += int(synthesis_usage.get("input_tokens", 0))
                loop_context.loop_output_tokens += int(synthesis_usage.get("output_tokens", 0))
                synthesis_grounding_metadata = _apply_gemini_grounding_cost(
                    synthesis_response,
                    loop_context,
                )
                synthesis_response["cost"] = {"total_cost": loop_context.loop_cost_eur}
                synthesis_response["usage"] = {
                    "input_tokens": loop_context.loop_input_tokens,
                    "output_tokens": loop_context.loop_output_tokens,
                }
                attribution_result = self._persist_gemini_request_costs(
                    db=db,
                    provider=provider,
                    model=loop_context.tool_execution_model,
                    chat_id=chat_id,
                    conversation_cost_eur=loop_context.loop_cost_eur,
                    input_tokens=loop_context.loop_input_tokens,
                    output_tokens=loop_context.loop_output_tokens,
                    websearch_query_count=loop_context.loop_websearch_queries,
                    grounding_metadata=synthesis_grounding_metadata or grounding_metadata,
                    request_kind="simple_tool_loop",
                )
                synthesis_response["_preserved_metadata"] = (
                    synthesis_response.get("grounding_metadata")
                    or synthesis_response.get("groundingMetadata")
                )
                synthesis_response["_cost_attribution"] = attribution_result
                synthesis_response["moa_tool_model"] = loop_context.tool_execution_model
                synthesis_response["moa_synthesis_model"] = loop_context.tool_execution_model
                return NonToolResponseAction(kind="return", response=synthesis_response)

            response = _apply_routing_quality_guards(response, loop_context.chat_history)
            response["cost"] = {"total_cost": loop_context.loop_cost_eur}
            response["usage"] = {
                "input_tokens": loop_context.loop_input_tokens,
                "output_tokens": loop_context.loop_output_tokens,
            }
            attribution_result = self._persist_gemini_request_costs(
                db=db,
                provider=provider,
                model=loop_context.tool_execution_model,
                chat_id=chat_id,
                conversation_cost_eur=loop_context.loop_cost_eur,
                input_tokens=loop_context.loop_input_tokens,
                output_tokens=loop_context.loop_output_tokens,
                websearch_query_count=loop_context.loop_websearch_queries,
                grounding_metadata=grounding_metadata,
                request_kind="simple_tool_loop",
            )
            response["_preserved_metadata"] = response.get("grounding_metadata") or response.get(
                "groundingMetadata"
            )
            response["_cost_attribution"] = attribution_result
            return NonToolResponseAction(kind="return", response=response)

        return await ToolLoopRunner().run(
            service=provider_service,
            context=context,
            sanitize_generate_response_kwargs=self._sanitize_generate_response_kwargs,
            prepare_history_for_second_call=self.service.prepare_history_for_second_call,
            handle_non_tool_response=handle_non_tool_response,
            filter_tools_by_skill_ids=_filter_tools_by_skill_ids,
            build_tool_definitions_for_llm=_build_tool_definitions_for_llm,
            prevalidate_tool_calls=_prevalidate_tool_calls,
            resolve_execution_model=resolve_gemini_execution_model,
            resolve_max_tool_rounds=resolve_gemini_max_tool_rounds,
            on_round_response=on_gemini_round_response,
        )

    async def _run_drill_down_list_research(
        self,
        *,
        provider: str,
        model: str,
        api_key: str,
        chat_history: List[Dict[str, Any]],
        user_prompt: str,
        passthrough_kwargs: Optional[Dict[str, Any]] = None,
        provider_service: Optional[GeminiServiceProvider] = None,
        tool_executor: Any = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        passthrough_kwargs = dict(kwargs or {})
        passthrough_kwargs.pop("provider", None)
        passthrough_kwargs.pop("model", None)
        passthrough_kwargs.pop("api_key", None)
        passthrough_kwargs.pop("chat_history", None)
        passthrough_kwargs.pop("user_prompt", None)
        passthrough_kwargs.pop("tool_executor", None)
        passthrough_kwargs.pop("provider_service", None)
        passthrough_kwargs.pop("passthrough_kwargs", None)

        if tool_executor is None:
            logger.warning("DIAMOND DRILL-DOWN: Kein ToolExecutor vorhanden. Fallback auf einfachen Tool-Loop.")
            return await self._run_simple_tool_loop(
                provider=provider,
                model=model,
                api_key=api_key,
                chat_history=chat_history,
                user_prompt=user_prompt,
                passthrough_kwargs=passthrough_kwargs,
                provider_service=provider_service,
                **passthrough_kwargs,
            )

        logger.info("DIAMOND DRILL-DOWN: Starte Zwei-Phasen-Recherche für Listen-Anfrage.")
        active_service = provider_service or self.service
        safe_passthrough = passthrough_kwargs if passthrough_kwargs is not None else {}
        call_kwargs = dict(safe_passthrough)
        call_kwargs = self._sanitize_generate_response_kwargs(
            call_kwargs,
            "api_key",
            "model",
            "messages",
            "tools",
            "image_data",
        )

        logger.info("Drill-Down (Phase 1): Führe allgemeine Websuche aus.")
        bypass_policy = bool(passthrough_kwargs.get("bypass_policy", False))
        tool_call = {
            "id": "initial_web_search",
            "function": {
                "name": "system.websearch",
                "arguments": json.dumps({"query": user_prompt}, ensure_ascii=False),
            },
        }
        initial_results = await tool_executor.execute_tool_calls([tool_call], bypass_policy=bypass_policy)

        logger.info("Drill-Down (Phase 2): Synthetisiere Rohtext aus Websuche.")
        synthesis_history = list(chat_history) + [
            {"role": "assistant", "content": None, "tool_calls": [tool_call]},
            *initial_results,
        ]
        prompt_ast = self._build_synthesis_ast(
            user_prompt=user_prompt,
            synthesis_history=synthesis_history,
            is_list_query=True,
            allow_links=False,
        )
        synthesis_prompt = self.compiler.compile(
            prompt_ast=prompt_ast,
            model_id=model,
            max_tokens=2048,
            allow_links=False,
        )
        final_response = await active_service.generate_response(
            api_key=api_key,
            model=model,
            messages=[{"role": "user", "content": synthesis_prompt}],
            tools=None,
            image_data=None,
            **call_kwargs,
        )

        generated_text = str(final_response.get("text") or "").strip()
        if not generated_text:
            logger.error("Drill-Down: Synthese-Phase hat keinen Text generiert. Breche ab.")
            return {"text": "Ich konnte keine Informationen zu deiner Anfrage finden."}

        logger.info("Drill-Down (Phase 3): Bereite finale Antwort vor.")
        # 💎 METADATA PRESERVATION: Capture metadata for parent method to use in rendering
        final_response["_preserved_metadata"] = final_response.get("grounding_metadata") or final_response.get("groundingMetadata")

        final_response.setdefault("tool_results", initial_results)
        final_response.setdefault("provider", provider)
        final_response.setdefault("model", model)
        return final_response

    @staticmethod
    def _build_synthesis_ast(
        *,
        user_prompt: str,
        synthesis_history: List[Dict[str, Any]],
        is_list_query: bool,
        allow_links: bool,
    ) -> Prompt:
        context_blocks: List[str] = []
        for message in synthesis_history or []:
            role = str(message.get("role") or "").strip()
            if role == "tool":
                content = str(message.get("content") or "").strip()
                if content:
                    context_blocks.append(content)

        blocks = [
            PromptBlock(
                type="system_role",
                content="Du bist ein präziser Recherche-Synthesizer. Antworte ausschließlich auf Basis des bereitgestellten Kontexts.",
                priority=1,
                required=True,
            ),
            PromptBlock(
                type="memory",
                content="\n\n".join(context_blocks),
                priority=2,
                required=True,
            ),
            PromptBlock(
                type="grounding_rules",
                content="Nutze ausschließlich Informationen aus dem <context> und erfinde keine Fakten.",
                priority=1,
                required=True,
            ),
            PromptBlock(
                type="user_prompt",
                content=user_prompt,
                priority=1,
                required=True,
            ),
        ]

        if is_list_query and not allow_links:
            blocks.append(
                PromptBlock(
                    type="output_contract",
                    content="Erzeuge eine saubere Markdown-Liste. Hebe pro Eintrag die Kern-Entität fett hervor.",
                    priority=2,
                    required=True,
                )
            )

        return Prompt(blocks=blocks)

    @staticmethod
    def build_websearch_context_block(tool_results: List[Dict[str, Any]]) -> str:
        """
        Aggregiert Websearch-Ergebnisse zu einem Kontext-Block.
        """
        blocks: List[str] = []
        all_facts: List[str] = []
        all_sources: List[Dict[str, Any]] = []

        for index, result in enumerate(tool_results or [], start=1):
            payload = _extract_tool_payload(result)
            if not payload or payload.get("status") != "ok":
                continue

            data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
            text_value = str(data.get("text") or "").strip()
            facts = data.get("facts") if isinstance(data.get("facts"), list) else []
            sources = data.get("sources") if isinstance(data.get("sources"), list) else []

            if text_value:
                blocks.append(f"--- Rechercheblock {index} ---\n{text_value}")

            for fact in facts:
                f_str = str(fact or "").strip()
                if f_str and f_str not in all_facts:
                    all_facts.append(f_str)

            all_sources.extend(sources)

        final_parts: List[str] = []
        if blocks:
            final_parts.append("### Recherche-Details\n" + "\n\n".join(blocks))

        if all_facts:
            final_parts.append("### Gesammelte Fakten\n" + "\n".join(f"- {f}" for f in all_facts[:30]))

        if all_sources:
            compact_sources = _extract_websearch_sources_for_compaction(all_sources, max_items=20)
            source_lines = ["### Quellenverzeichnis"]
            for s in compact_sources:
                title = str(s.get("title") or "Quelle").strip()
                url = str(s.get("url") or s.get("uri") or "").strip()
                if url:
                    source_lines.append(f"- {title}: {url}")
            final_parts.append("\n".join(source_lines))

        return "\n\n".join(final_parts).strip()

    @staticmethod
    def _build_final_messages(
        chat_history: List[Dict[str, Any]],
        websearch_instruction: str,
    ) -> List[Dict[str, Any]]:
        system_parts: List[str] = []
        seen_parts: set[str] = set()
        for message in chat_history or []:
            if str(message.get("role") or "") != "system":
                continue
            content = str(message.get("content") or "").strip()
            if not content or content in seen_parts:
                continue
            seen_parts.add(content)
            system_parts.append(content)

        final_messages: List[Dict[str, Any]] = []
        if system_parts:
            final_messages.append({"role": "system", "content": "\n\n".join(system_parts).strip()})
        final_messages.append({"role": "user", "content": websearch_instruction})
        return final_messages

    @staticmethod
    def _is_list_query(lowered_prompt: str) -> bool:
        normalized = str(lowered_prompt or "")
        if not normalized:
            return False
        return any(token in normalized for token in LIST_QUERY_TOKENS)

    @classmethod
    def _ensure_grounding_rules(cls, base_instruction: str, *, is_list_query: bool) -> str:
        from .constants import HYBRID_LINK_DIRECTIVE, UNIVERSAL_LINK_DIRECTIVE
        instruction = str(base_instruction or "").strip()
        if not instruction:
            instruction = "Antworte basierend auf den Fakten."

        # STRICT GROUNDING RULE: Verhindert Nutzung veralteten Trainingswissens
        STRICT_GROUNDING_RULE = """\n\n🔒 STRICT GROUNDING RULE / STRIKTE WÄHRUNGS-DIREKTIVE:
Du bist ein europäischer Finanzassistent. Deine Aufgabe ist es, den Preis in EURO zu finden. Halte dich an folgende Regeln:

1. PRIORISIERE EURO: Durchsuche die Websuche-Ergebnisse explizit nach Preisen in Euro (€). Nenne diesen Preis und das Datum (heute ist der 26.03.2026).

2. FALLBACK MIT WARNUNG: Wenn du absolut keinen Preis in Euro findest, aber einen in einer anderen Währung (z.B. US-Dollar), dann nenne diesen Preis und gib die Währung explizit an (Beispiel: '1.936 US-Dollar').

3. IGNORIERE DEIN WISSEN: Verlasse dich nur auf die Preise und Daten in den aktuellen Suchergebnissen. Konvertiere keine Währungen selbstständig.

Nutze für die Antwort AUSSCHLIESSLICH die Preise und Fakten aus den vorliegenden Recherche-Ergebnissen.
Übernimm die Werte exakt so, wie sie in den Snippets stehen.
Wenn ein Preis gefunden wurde, ist dieser für das heutige Datum (26.03.2026) absolut bindend.
"""
        if "STRICT GROUNDING RULE" not in instruction:
            instruction = instruction + STRICT_GROUNDING_RULE

        if is_list_query and "CRITICAL HYBRID-LINKING DIRECTIVE" not in instruction:
            instruction = cls._append_constraint_block(instruction, HYBRID_LINK_DIRECTIVE)
        if not is_list_query and "CRITICAL UNIVERSAL LINKING DIRECTIVE" not in instruction:
            instruction = cls._append_constraint_block(instruction, UNIVERSAL_LINK_DIRECTIVE)
        return instruction

    @staticmethod
    def _append_constraint_block(instruction: str, block: str) -> str:
        if "<constraints>" in instruction and "</constraints>" in instruction:
            return instruction.replace("</constraints>", f"{block}\n</constraints>", 1)
        if instruction.endswith("</task>"):
            return instruction.replace("</task>", f"\n\n{block}\n</task>", 1)
        return f"{instruction}\n\n{block}"
