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
from typing import Any, Dict, List, Optional

from .compiler import GeminiCompiler
from .link_renderer import get_link_renderer
from .constants import LIST_QUERY_TOKENS
from ..shared.base_gateway import BaseProviderGateway
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
            from backend.services.chat_orchestrator import ChatOrchestrator

            tier = tool_manager.get_optimal_model_tier("system.websearch", "gemini")
            forced_model = ChatOrchestrator.MODEL_HIERARCHY["gemini"].get(tier, model)

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
        Eine Gemini-API-Runde mit Tools; Tool-Ausführung bleibt beim Orchestrator
        (execution_engine), damit [GEMINI-FIX] und Hard-Loop-Breaker pro Runde greifen.
        """
        from backend.llm_providers.shared.utils import (
            _filter_tools_by_skill_ids,
            _build_tool_definitions_for_llm,
            _prevalidate_tool_calls,
            _apply_routing_quality_guards,
        )
        from backend.llm_providers.shared.moa import resolve_moa_model

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
        provider_service = passthrough_kwargs.pop("provider_service", None) or self.service
        db = passthrough_kwargs.pop("db", None)
        passthrough_kwargs.pop("is_list_query", None)

        user_base_model = model
        tool_execution_model, moa_active = resolve_moa_model(
            provider=provider,
            user_base_model=user_base_model,
            allowed_skill_ids=allowed_skill_ids,
        )

        forced_model = None
        if chat_history and len(chat_history) > 0:
            for msg in chat_history:
                if msg.get("role") == "system" and "MODEL_OVERRIDE:" in str(msg.get("content", "")):
                    _match = re.search(r"MODEL_OVERRIDE:\s*(\S+)", str(msg.get("content", "")))
                    if _match:
                        forced_model = _match.group(1).strip()
                        break

        if forced_model:
            tool_execution_model = forced_model
            moa_active = True
            logger.info("✅ GEMINI-OVERRIDE: Forced model '%s' successfully applied.", forced_model)

        if moa_active and tool_execution_model != user_base_model:
            logger.info(
                "💎 GEMINI MOA: Forciere Modell-Switch %s -> %s",
                user_base_model,
                tool_execution_model,
            )

        current_chat_history = list(chat_history)
        _loop_cost_eur = 0.0
        _loop_input_tokens = 0
        _loop_output_tokens = 0
        _loop_websearch_queries = 0

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
            **loop_kwargs,
        )

        _r_cost = response.get("cost") or {}
        _r_usage = response.get("usage") or {}
        _loop_cost_eur += float(_r_cost.get("total_cost", 0.0))
        _loop_input_tokens += int(_r_usage.get("input_tokens", 0))
        _loop_output_tokens += int(_r_usage.get("output_tokens", 0))
        _gm = response.get("grounding_metadata") or {}
        _raw_queries = _gm.get("web_search_queries") or []
        valid_queries = [str(q or "").strip() for q in _raw_queries if str(q or "").strip()]
        search_cost = len(valid_queries) * 0.01
        _loop_websearch_queries += len(valid_queries)
        _loop_cost_eur += search_cost
        if valid_queries:
            logger.info(
                "✅ GEMINI-SEARCH-BILLING: %d queries billed at %.4f€.",
                len(valid_queries),
                search_cost,
            )

        if response.get("type") != "tool_code":
            if moa_active:
                logger.info(
                    "💎 SKILL-MOA RÜCKSPRUNG: Tool-Loop abgeschlossen mit '%s'. "
                    "Synthetisiere finale Antwort mit smartem Tool-Modell '%s'.",
                    tool_execution_model,
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
                _syn_cost = synthesis_response.get("cost") or {}
                _syn_usage = synthesis_response.get("usage") or {}
                _loop_cost_eur += float(_syn_cost.get("total_cost", 0.0))
                _loop_input_tokens += int(_syn_usage.get("input_tokens", 0))
                _loop_output_tokens += int(_syn_usage.get("output_tokens", 0))
                _syn_gm = synthesis_response.get("grounding_metadata") or {}
                _syn_raw_queries = _syn_gm.get("web_search_queries") or []
                syn_valid_queries = [
                    str(q or "").strip() for q in _syn_raw_queries if str(q or "").strip()
                ]
                syn_search_cost = len(syn_valid_queries) * 0.01
                _loop_websearch_queries += len(syn_valid_queries)
                _loop_cost_eur += syn_search_cost
                if syn_valid_queries:
                    logger.info(
                        "✅ GEMINI-SEARCH-BILLING: %d queries billed at %.4f€.",
                        len(syn_valid_queries),
                        syn_search_cost,
                    )
                synthesis_response["cost"] = {"total_cost": _loop_cost_eur}
                synthesis_response["usage"] = {
                    "input_tokens": _loop_input_tokens,
                    "output_tokens": _loop_output_tokens,
                }
                if db is not None and _loop_cost_eur > 0:
                    try:
                        from backend.services.cost_service import create_cost_entry

                        create_cost_entry(
                            db=db,
                            amount=_loop_cost_eur,
                            model=tool_execution_model,
                            provider=str(provider or "gemini"),
                            source_type="conversation",
                            input_tokens=_loop_input_tokens,
                            output_tokens=_loop_output_tokens,
                        )
                        logger.info(
                            "GEMINI-COST-PERSIST: Saved %.6f€ for %s",
                            _loop_cost_eur,
                            tool_execution_model,
                        )
                    except Exception:
                        logger.warning("GEMINI-COST-PERSIST: Failed to save cost", exc_info=True)
                if db is not None and _loop_websearch_queries > 0:
                    try:
                        from backend.services.cost_service import create_cost_entry

                        create_cost_entry(
                            db=db,
                            amount=round(_loop_websearch_queries * 0.01, 6),
                            model=tool_execution_model,
                            provider=str(provider or "gemini"),
                            source_type="websearch",
                            context_details=f"query_count={_loop_websearch_queries}",
                        )
                        logger.info(
                            "GEMINI-WEBSEARCH-PERSIST: Saved %d queries (%.4f€)",
                            _loop_websearch_queries,
                            _loop_websearch_queries * 0.01,
                        )
                    except Exception:
                        logger.warning(
                            "GEMINI-WEBSEARCH-PERSIST: Failed to save websearch cost",
                            exc_info=True,
                        )
                synthesis_response["_preserved_metadata"] = (
                    synthesis_response.get("grounding_metadata")
                    or synthesis_response.get("groundingMetadata")
                )
                synthesis_response["moa_tool_model"] = tool_execution_model
                synthesis_response["moa_synthesis_model"] = tool_execution_model
                synthesis_response.setdefault("provider", provider)
                synthesis_response.setdefault("model", model)
                return synthesis_response

            response = _apply_routing_quality_guards(response, current_chat_history)
            response["cost"] = {"total_cost": _loop_cost_eur}
            response["usage"] = {
                "input_tokens": _loop_input_tokens,
                "output_tokens": _loop_output_tokens,
            }
            if db is not None and _loop_cost_eur > 0:
                try:
                    from backend.services.cost_service import create_cost_entry

                    create_cost_entry(
                        db=db,
                        amount=_loop_cost_eur,
                        model=tool_execution_model,
                        provider=str(provider or "gemini"),
                        source_type="conversation",
                        input_tokens=_loop_input_tokens,
                        output_tokens=_loop_output_tokens,
                    )
                    logger.info(
                        "GEMINI-COST-PERSIST: Saved %.6f€ for %s",
                        _loop_cost_eur,
                        tool_execution_model,
                    )
                except Exception:
                    logger.warning("GEMINI-COST-PERSIST: Failed to save cost", exc_info=True)
            if db is not None and _loop_websearch_queries > 0:
                try:
                    from backend.services.cost_service import create_cost_entry

                    create_cost_entry(
                        db=db,
                        amount=round(_loop_websearch_queries * 0.01, 6),
                        model=tool_execution_model,
                        provider=str(provider or "gemini"),
                        source_type="websearch",
                        context_details=f"query_count={_loop_websearch_queries}",
                    )
                    logger.info(
                        "GEMINI-WEBSEARCH-PERSIST: Saved %d queries (%.4f€)",
                        _loop_websearch_queries,
                        _loop_websearch_queries * 0.01,
                    )
                except Exception:
                    logger.warning(
                        "GEMINI-WEBSEARCH-PERSIST: Failed to save websearch cost",
                        exc_info=True,
                    )
            response["_preserved_metadata"] = response.get("grounding_metadata") or response.get(
                "groundingMetadata"
            )
            response.setdefault("provider", provider)
            response.setdefault("model", model)
            return response

        tool_calls = response.get("tool_calls", [])
        preflight = _prevalidate_tool_calls(tool_calls, user_prompt=user_prompt)
        validated_tool_calls = preflight["valid_calls"]

        if not validated_tool_calls:
            return response

        response["tool_calls"] = validated_tool_calls

        response["cost"] = {"total_cost": _loop_cost_eur}
        response["usage"] = {
            "input_tokens": _loop_input_tokens,
            "output_tokens": _loop_output_tokens,
        }
        if db is not None and _loop_cost_eur > 0:
            try:
                from backend.services.cost_service import create_cost_entry

                create_cost_entry(
                    db=db,
                    amount=_loop_cost_eur,
                    model=tool_execution_model,
                    provider=str(provider or "gemini"),
                    source_type="conversation",
                    input_tokens=_loop_input_tokens,
                    output_tokens=_loop_output_tokens,
                )
                logger.info(
                    "GEMINI-COST-PERSIST: Saved %.6f€ for %s",
                    _loop_cost_eur,
                    tool_execution_model,
                )
            except Exception:
                logger.warning("GEMINI-COST-PERSIST: Failed to save cost", exc_info=True)
        if db is not None and _loop_websearch_queries > 0:
            try:
                from backend.services.cost_service import create_cost_entry

                create_cost_entry(
                    db=db,
                    amount=round(_loop_websearch_queries * 0.01, 6),
                    model=tool_execution_model,
                    provider=str(provider or "gemini"),
                    source_type="websearch",
                    context_details=f"query_count={_loop_websearch_queries}",
                )
                logger.info(
                    "GEMINI-WEBSEARCH-PERSIST: Saved %d queries (%.4f€)",
                    _loop_websearch_queries,
                    _loop_websearch_queries * 0.01,
                )
            except Exception:
                logger.warning(
                    "GEMINI-WEBSEARCH-PERSIST: Failed to save websearch cost",
                    exc_info=True,
                )
        response["_preserved_metadata"] = response.get("grounding_metadata") or response.get(
            "groundingMetadata"
        )
        response.setdefault("provider", provider)
        response.setdefault("model", model)
        return response

    async def _run_simple_tool_loop(self, **kwargs) -> Dict[str, Any]:
        """
        Interne Implementierung des Tool-Loops.
        💎 MoA-Integration: Tool-Loop mit optimiertem Modell, Synthese mit User-Modell.
        """
        from backend.llm_providers.shared.utils import (
            _filter_tools_by_skill_ids,
            _build_tool_definitions_for_llm,
            _prevalidate_tool_calls,
            _apply_routing_quality_guards
        )
        from backend.llm_providers.shared.moa import resolve_moa_model

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
        provider_service = passthrough_kwargs.pop("provider_service", None) or self.service
        db = passthrough_kwargs.pop("db", None)
        is_list_query = passthrough_kwargs.pop("is_list_query", None)
        if is_list_query is None:
            is_list_query = self._is_list_query(str(user_prompt or "").strip().lower())

        if is_list_query:
            previous_round_cap = max_tool_rounds
            max_tool_rounds = max(max_tool_rounds, 12)
            if max_tool_rounds != previous_round_cap:
                logger.info("DIAMOND-RESEARCH: Listen-Anfrage. Max Tool-Rounds auf %s erhöht.", max_tool_rounds)

        # 💎 MoA-Routing
        user_base_model = model
        tool_execution_model, moa_active = resolve_moa_model(
            provider=provider,
            user_base_model=user_base_model,
            allowed_skill_ids=allowed_skill_ids,
        )

        # 💎 MODEL_OVERRIDE: Prüfe auf forced model in system messages (analog zu OpenAI)
        forced_model = None
        if chat_history and len(chat_history) > 0:
            for msg in chat_history:
                if msg.get("role") == "system" and "MODEL_OVERRIDE:" in str(msg.get("content", "")):
                    _match = re.search(r"MODEL_OVERRIDE:\s*(\S+)", str(msg.get("content", "")))
                    if _match:
                        forced_model = _match.group(1).strip()
                        break

        if forced_model:
            tool_execution_model = forced_model
            moa_active = True
            logger.info(f"✅ GEMINI-OVERRIDE: Forced model '{forced_model}' successfully applied.")

        if moa_active and tool_execution_model != user_base_model:
            logger.info(
                "💎 GEMINI MOA: Forciere Modell-Switch %s -> %s",
                user_base_model,
                tool_execution_model,
            )

        current_round = 0
        current_chat_history = list(chat_history)
        # 💎 COST-ACCUMULATION: Sammle Kosten über alle internen Runden
        _loop_cost_eur = 0.0
        _loop_input_tokens = 0
        _loop_output_tokens = 0
        _loop_websearch_queries = 0

        while current_round < max_tool_rounds:
            current_round += 1

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
                image_data=image_data if current_round == 1 else None,
                **loop_kwargs
            )

            # Accumulate cost from this round
            _r_cost = response.get("cost") or {}
            _r_usage = response.get("usage") or {}
            _loop_cost_eur += float(_r_cost.get("total_cost", 0.0))
            _loop_input_tokens += int(_r_usage.get("input_tokens", 0))
            _loop_output_tokens += int(_r_usage.get("output_tokens", 0))
            # 💎 SEARCH GROUNDING BILLING: Parse and bill non-empty native search queries
            _gm = response.get("grounding_metadata") or {}
            _raw_queries = _gm.get("web_search_queries") or []
            valid_queries = [str(q or "").strip() for q in _raw_queries if str(q or "").strip()]
            search_cost = len(valid_queries) * 0.01
            _loop_websearch_queries += len(valid_queries)
            _loop_cost_eur += search_cost
            if valid_queries:
                logger.info(f"✅ GEMINI-SEARCH-BILLING: {len(valid_queries)} queries billed at {search_cost:.4f}€.")

            if response.get("type") != "tool_code":
                # 💎 MoA-Rücksprung
                if moa_active:
                    logger.info(
                        "💎 SKILL-MOA RÜCKSPRUNG: Tool-Loop abgeschlossen mit '%s'. "
                        "Synthetisiere finale Antwort mit smartem Tool-Modell '%s'.",
                        tool_execution_model,
                        tool_execution_model,
                    )
                    # --- SMART SYNTHESIS FIX ---
                    synthesis_response = await provider_service.generate_response(
                        api_key=api_key,
                        model=tool_execution_model, # <--- NICHT user_base_model nutzen!
                        messages=current_chat_history,
                        tools=None,
                        image_data=None,
                    )
                    synthesis_response = _apply_routing_quality_guards(synthesis_response, current_chat_history)
                    # Add synthesis call cost to accumulated loop cost
                    _syn_cost = synthesis_response.get("cost") or {}
                    _syn_usage = synthesis_response.get("usage") or {}
                    _loop_cost_eur += float(_syn_cost.get("total_cost", 0.0))
                    _loop_input_tokens += int(_syn_usage.get("input_tokens", 0))
                    _loop_output_tokens += int(_syn_usage.get("output_tokens", 0))
                    _syn_gm = synthesis_response.get("grounding_metadata") or {}
                    _syn_raw_queries = _syn_gm.get("web_search_queries") or []
                    syn_valid_queries = [str(q or "").strip() for q in _syn_raw_queries if str(q or "").strip()]
                    syn_search_cost = len(syn_valid_queries) * 0.01
                    _loop_websearch_queries += len(syn_valid_queries)
                    _loop_cost_eur += syn_search_cost
                    if syn_valid_queries:
                        logger.info(f"✅ GEMINI-SEARCH-BILLING: {len(syn_valid_queries)} queries billed at {syn_search_cost:.4f}€.")
                    synthesis_response["cost"] = {"total_cost": _loop_cost_eur}
                    synthesis_response["usage"] = {
                        "input_tokens": _loop_input_tokens,
                        "output_tokens": _loop_output_tokens,
                    }
                    # 💎 PERSISTENCE: Speichere akkumulierte Tool-Loop Kosten
                    if db is not None and _loop_cost_eur > 0:
                        try:
                            from backend.services.cost_service import create_cost_entry
                            create_cost_entry(
                                db=db,
                                amount=_loop_cost_eur,
                                model=tool_execution_model,
                                provider=str(provider or "gemini"),
                                source_type="conversation",
                                input_tokens=_loop_input_tokens,
                                output_tokens=_loop_output_tokens,
                            )
                            logger.info("GEMINI-COST-PERSIST: Saved %.6f€ for %s", _loop_cost_eur, tool_execution_model)
                        except Exception:
                            logger.warning("GEMINI-COST-PERSIST: Failed to save cost", exc_info=True)
                    # 💎 NATIVE WEBSEARCH TRACKING
                    if db is not None and _loop_websearch_queries > 0:
                        try:
                            from backend.services.cost_service import create_cost_entry
                            create_cost_entry(
                                db=db,
                                amount=round(_loop_websearch_queries * 0.01, 6),
                                model=tool_execution_model,
                                provider=str(provider or "gemini"),
                                source_type="websearch",
                                context_details=f"query_count={_loop_websearch_queries}",
                            )
                            logger.info("GEMINI-WEBSEARCH-PERSIST: Saved %d queries (%.4f€)", _loop_websearch_queries, _loop_websearch_queries * 0.01)
                        except Exception:
                            logger.warning("GEMINI-WEBSEARCH-PERSIST: Failed to save websearch cost", exc_info=True)
                    # 💎 METADATA PRESERVATION: Capture metadata from synthesis for parent method
                    # Note: Link rendering happens at final return point in reason_and_respond
                    synthesis_response["_preserved_metadata"] = synthesis_response.get("grounding_metadata") or synthesis_response.get("groundingMetadata")
                    synthesis_response["moa_tool_model"] = tool_execution_model
                    synthesis_response["moa_synthesis_model"] = tool_execution_model
                    return synthesis_response

                response = _apply_routing_quality_guards(response, current_chat_history)
                # Attach accumulated costs
                response["cost"] = {"total_cost": _loop_cost_eur}
                response["usage"] = {
                    "input_tokens": _loop_input_tokens,
                    "output_tokens": _loop_output_tokens,
                }
                # 💎 PERSISTENCE: Speichere akkumulierte Tool-Loop Kosten
                if db is not None and _loop_cost_eur > 0:
                    try:
                        from backend.services.cost_service import create_cost_entry
                        create_cost_entry(
                            db=db,
                            amount=_loop_cost_eur,
                            model=tool_execution_model,
                            provider=str(provider or "gemini"),
                            source_type="conversation",
                            input_tokens=_loop_input_tokens,
                            output_tokens=_loop_output_tokens,
                        )
                        logger.info("GEMINI-COST-PERSIST: Saved %.6f€ for %s", _loop_cost_eur, tool_execution_model)
                    except Exception:
                        logger.warning("GEMINI-COST-PERSIST: Failed to save cost", exc_info=True)
                # 💎 NATIVE WEBSEARCH TRACKING
                if db is not None and _loop_websearch_queries > 0:
                    try:
                        from backend.services.cost_service import create_cost_entry
                        create_cost_entry(
                            db=db,
                            amount=round(_loop_websearch_queries * 0.01, 6),
                            model=tool_execution_model,
                            provider=str(provider or "gemini"),
                            source_type="websearch",
                            context_details=f"query_count={_loop_websearch_queries}",
                        )
                        logger.info("GEMINI-WEBSEARCH-PERSIST: Saved %d queries (%.4f€)", _loop_websearch_queries, _loop_websearch_queries * 0.01)
                    except Exception:
                        logger.warning("GEMINI-WEBSEARCH-PERSIST: Failed to save websearch cost", exc_info=True)
                # 💎 METADATA PRESERVATION: Capture metadata for parent method
                response["_preserved_metadata"] = response.get("grounding_metadata") or response.get("groundingMetadata")
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
                tool_results=executor_results
            )

        return {"text": "Maximale Tool-Runden erreicht.", "tool_limit_reached": True}

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
