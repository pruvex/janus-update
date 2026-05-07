import json
import logging
import os
import re
import time
import uuid
from urllib.parse import urlparse
from typing import Any, AsyncIterator, Dict, List, Optional, cast

import keyring

from backend.data.schemas import AgentSpec, PlannerContext, PlannerProviderProfile
from backend.data.schemas_logging import LogEventCreate
from backend.services.logging.logger_core import log_event
from backend.llm_providers.gemini.service import GeminiServiceProvider
from backend.llm_providers.ollama.service import OllamaServiceProvider
from backend.llm_providers.openai.service import OpenAIServiceProvider
from backend.llm_providers.shared.utils import _build_tool_definitions_for_llm, _filter_tools_by_skill_ids
from backend.services import llm_gateway
from backend.services.tool_executor import ToolExecutor
from backend.services.tool_manager import tool_manager
from backend.services.orchestrator.schemas import ExecutionResponse, OrchestratorContext
from backend.services.orchestrator.stream_protocol import StreamEvent
from backend.services.orchestrator.intent_engine import IntentDetectionResult
from backend.services.prompt_cache import clone_decision_for_route, decision_from_gateway_kwargs, merge_decision_into_usage
from backend.utils.config_loader import load_config_data, load_model_catalog
from backend.renderers.attribution import append_tool_attributions_from_tools
from backend.utils.link_sanitizer import force_sanitize_links

logger = logging.getLogger("janus_backend")

# Tool wall-clock limits: ToolExecutor uses asyncio.wait_for with each skill's ``timeout_ms``
# (see backend/skills/). Example: system.local_business is 45s so geo/OSM + enrichment can finish.
#
# TASK-067: Pending calendar mutations (MutationProposal) live in
# ``backend.services.calendar.mutation_guard_store`` — confirmed via ChatOrchestrator, not here.

MAPS_LINK_REGEX = re.compile(r'"maps_link"\s*:\s*"([^"]+)"')


def _reload_api_key_for_provider(provider: str) -> str:
    """
    Lädt den API-Key für den angegebenen Provider frisch aus dem Keyring.
    Wird bei Provider-Switch aufgerufen, um Key-Leaks zu verhindern.
    """
    prov = str(provider or "").strip().lower()
    if not prov:
        return ""
    if prov == "ollama":
        return "ollama"
    # Frischer Key aus Keyring
    key = keyring.get_password("Janus-Projekt", prov)
    if key:
        logger.info(f"AUTH-REFRESH: Geladener API-Key für Provider '{prov}' (Länge: {len(key)})")
        return key
    # Fallback: env
    env_var = f"{prov.upper()}_API_KEY"
    env_key = os.getenv(env_var, "").strip()
    if env_key:
        logger.info(f"AUTH-REFRESH: Verwende Env-Key {env_var} für Provider '{prov}'")
        return env_key
    logger.warning(f"AUTH-REFRESH: Kein API-Key gefunden für Provider '{prov}'")
    return ""


def _stream_tools_list_for_llm(gateway_kwargs: Dict[str, Any]) -> Optional[List[Any]]:
    if gateway_kwargs.get("disable_tools"):
        return None
    to = gateway_kwargs.get("tools_override")
    if to is not None and len(to) == 0:
        return []
    raw = _filter_tools_by_skill_ids(gateway_kwargs.get("allowed_skill_ids"))
    return _build_tool_definitions_for_llm(raw)


def _stream_merge_openai_tool_delta(acc: Dict[int, Dict[str, Any]], frag: Dict[str, Any]) -> None:
    idx = int(frag.get("index", 0))
    slot = acc.setdefault(idx, {"id": "", "name": "", "arguments": ""})
    if frag.get("id"):
        slot["id"] = str(frag["id"])
    if frag.get("name"):
        slot["name"] = str(frag["name"])
    if frag.get("arguments"):
        slot["arguments"] = str(slot.get("arguments") or "") + str(frag["arguments"])


def _stream_finalize_openai_tool_slots(acc: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for idx in sorted(acc.keys()):
        s = acc[idx]
        name = str(s.get("name") or "").strip()
        if not name:
            continue
        call_id = str(s.get("id") or "").strip() or f"call_{idx}"
        args_raw = str(s.get("arguments") or "").strip() or "{}"
        out.append(
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": args_raw},
            }
        )
    return out


def _gemini_tool_delta_to_call(content: Dict[str, Any]) -> Dict[str, Any]:
    name = str(content.get("name") or "").strip()
    provider_name = str(content.get("_gemini_provider_name") or "").strip()
    args = content.get("arguments")
    if isinstance(args, dict):
        args_str = json.dumps(args, ensure_ascii=False)
    else:
        args_str = str(args or "{}")
    function = {"name": name, "arguments": args_str}
    if provider_name:
        function["_gemini_provider_name"] = provider_name
    call = {
        "id": f"gemini_{uuid.uuid4().hex[:16]}",
        "type": "function",
        "function": function,
    }
    if provider_name:
        call["_gemini_provider_name"] = provider_name
    return call


async def _async_iter_llm_stream(
    gateway_kwargs: Dict[str, Any],
    tools_llm: Optional[List[Any]],
    force_tool_name: Optional[str] = None,
) -> AsyncIterator[StreamEvent]:
    """Single LLM round: provider-native StreamEvents (text_delta, tool_delta, usage, done, error)."""
    provider = str(gateway_kwargs.get("provider") or "").lower()
    api_key = gateway_kwargs.get("api_key") or ""
    model = gateway_kwargs.get("model") or ""
    messages = list(gateway_kwargs.get("chat_history") or [])
    max_tok = gateway_kwargs.get("max_tokens")
    prompt_cache_decision = decision_from_gateway_kwargs(gateway_kwargs)
    extra: Dict[str, Any] = {}
    if provider == "ollama" and gateway_kwargs.get("format"):
        extra["format"] = gateway_kwargs["format"]

    logger.info("💎 VIDEO-FORCE (_async_iter_llm_stream): Received force_tool_name=%s for provider=%s", force_tool_name, provider)
    if prompt_cache_decision is not None:
        yield StreamEvent(type="cache_metrics", content=prompt_cache_decision.to_dict(), metadata={})

    # NOTE: Previous implementation injected a synthetic assistant message with
    # `tool_calls` into `messages` when `forced_tool_args` was present.
    # That violated the OpenAI Chat Completions contract (assistant tool_calls
    # without matching tool-role replies) and caused 400 BadRequest.
    # The forced-tool-call start is now handled at the tool-loop level in
    # OrchestratorExecutionEngine.run_tool_loop / run_tool_loop_stream, which
    # synthesizes the initial tool_calls and skips the LLM round entirely,
    # keeping the OpenAI message history clean.

    if provider == "openai":
        svc = OpenAIServiceProvider()
        async for ev in svc.generate_response_stream(
            api_key=api_key,
            model=model,
            messages=messages,
            tools=tools_llm,
            force_tool_name=force_tool_name,
            max_completion_tokens=max_tok,
            **extra,
        ):
            yield ev
    elif provider in ("gemini", "google"):
        svc = GeminiServiceProvider()
        stream_wf = gateway_kwargs.get("_workflow")
        async for ev in svc.generate_response_stream(
            api_key=api_key,
            model=model,
            messages=messages,
            tools=tools_llm,
            force_no_tools=bool(gateway_kwargs.get("disable_tools")),
            force_tool_name=force_tool_name,
            stream_workflow_ref=stream_wf,
            **extra,
        ):
            yield ev
    elif provider == "ollama":
        svc = OllamaServiceProvider()
        async for ev in svc.generate_response_stream(
            api_key=api_key,
            model=model,
            messages=messages,
            tools=tools_llm,
            force_tool_name=force_tool_name,
            max_completion_tokens=max_tok,
            **extra,
        ):
            yield ev
    else:
        logger.error("run_tool_loop_stream: unsupported provider %s", provider)
        yield StreamEvent(type="error", content=f"Unsupported provider: {provider}", metadata={})


# ---------------------------------------------------------------------------
# IRON-GATE: Compiled patterns for price-response auditing
# ---------------------------------------------------------------------------
_IRON_GATE_URL_RE = re.compile(r"https?://[^\s\)\]>,\"']+")
_IRON_GATE_MD_LINK_RE = re.compile(r"\[[^\]]+\]\(https?://[^\)]+\)")
_IRON_GATE_PRICE_RE = re.compile(r"(\d{1,6}(?:[.,]\d{2})?)\s*(?:€|EUR)")
_IRON_GATE_BUDGET_REF_RE = re.compile(
    r"(?:bis|unter|max|budget|höchstens|limit)\s+(\d{1,6}(?:[.,]\d{2})?)\s*(?:€|EUR)",
    re.IGNORECASE,
)
_IRON_GATE_TRUSTED_DOMAINS = ("idealo.de", "geizhals.de")


class OrchestratorExecutionEngine:
    """Executes agent and gateway tool-loop flows for the orchestrator facade."""

    def __init__(self, db, context_manager, model_hierarchy, agent_planner, agent_runtime, skill_selector, capability_registry=None):
        self.db = db
        self.context_manager = context_manager
        self.model_hierarchy = model_hierarchy
        self.agent_planner = agent_planner
        self.agent_runtime = agent_runtime
        self.skill_selector = skill_selector
        self.capability_registry = capability_registry

    # ------------------------------------------------------------------
    # IRON-GATE: Output-Auditor for price_comparison responses
    # ------------------------------------------------------------------
    @staticmethod
    def _audit_price_response(
        text: str,
        budget_limit: Optional[float] = None,
    ) -> List[str]:
        """Validates an LLM synthesis against Diamond compliance rules.

        Returns a list of violation descriptions (empty = compliant).
        """
        if not text or not text.strip():
            return ["LEER: Keine Antwort generiert."]

        violations: List[str] = []

        # --- REGEL A: Source-Validierung ---
        all_urls = _IRON_GATE_URL_RE.findall(text)
        untrusted = [
            u for u in all_urls
            if not any(d in u.lower() for d in _IRON_GATE_TRUSTED_DOMAINS)
        ]
        if untrusted:
            samples = ", ".join(u[:60] for u in untrusted[:3])
            violations.append(f"FREMD-QUELLEN: {samples}")

        # --- REGEL B: Budget-Compliance ---
        if budget_limit is not None:
            budget_ref_positions = {
                m.start(1) for m in _IRON_GATE_BUDGET_REF_RE.finditer(text)
            }
            for m in _IRON_GATE_PRICE_RE.finditer(text):
                if m.start(1) in budget_ref_positions:
                    continue
                raw = m.group(1).replace(".", "").replace(",", ".")
                try:
                    price = float(raw)
                except ValueError:
                    continue
                if price > budget_limit * 1.05:
                    violations.append(
                        f"BUDGET-VERSTOSS: {price:.2f}€ überschreitet "
                        f"Limit {budget_limit:.0f}€"
                    )
                    break

        # --- REGEL C: Link-Pflicht ---
        md_links = _IRON_GATE_MD_LINK_RE.findall(text)
        if not md_links:
            if all_urls:
                violations.append(
                    "LINK-FORMAT: Rohe URLs statt klickbarer Markdown-Links"
                )
            else:
                violations.append(
                    "LINK-PFLICHT: Keine klickbaren Links in der Antwort"
                )

        return violations

    @staticmethod
    def _build_iron_gate_correction(
        violations: List[str],
        budget_limit: Optional[float] = None,
    ) -> str:
        """Builds the system correction prompt for a failed audit."""
        budget_clause = ""
        if budget_limit is not None:
            budget_clause = (
                f"\n- Nenne NUR Preise bis {budget_limit:.0f}€. "
                f"Produkte über {budget_limit:.0f}€ sind STRENG VERBOTEN."
            )

        return (
            "!!! SYSTEM-KORREKTUR (IRON-GATE) !!!\n"
            "Deine vorherige Antwort wurde ABGELEHNT.\n\n"
            "VERSTÖSSE:\n"
            + "\n".join(f"  • {v}" for v in violations)
            + "\n\n"
            "KORRIGIERE SOFORT nach diesen Regeln:\n"
            "- Verwende AUSSCHLIESSLICH Links zu idealo.de oder geizhals.de.\n"
            "- Jeder Preis MUSS ein klickbarer Markdown-Link sein: "
            "[Produktname ab X€](https://idealo.de/...).\n"
            "- Entferne ALLE Amazon-, eBay-, LEGO- und sonstigen Fremd-Links."
            + budget_clause
            + "\n\nFormatiere die Daten aus den vorherigen Tool-Ergebnissen korrekt."
        )

    @staticmethod
    def _build_video_modal_request_from_tool_results(tool_results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Derive a canonical video modal_request from successful video.search tool results."""
        for tr in (tool_results or []):
            if not isinstance(tr, dict):
                continue
            name = str(tr.get("name") or "").strip().lower()
            if name != "video.search":
                continue
            raw_payload = tr.get("_raw_content") or tr.get("content") or "{}"
            try:
                parsed = json.loads(raw_payload) if isinstance(raw_payload, str) else dict(raw_payload or {})
            except Exception:
                continue
            if not isinstance(parsed, dict) or parsed.get("status") != "ok":
                continue
            # LIST-MODE GUARD: Kein Auto-Modal bei Video-Listen
            metadata = parsed.get("metadata") if isinstance(parsed.get("metadata"), dict) else {}
            if str(metadata.get("mode") or "").strip().lower() == "list":
                continue  # Kein Modal für Listen
            data = parsed.get("data") if isinstance(parsed.get("data"), dict) else {}
            if isinstance(data.get("videos"), list) and "selected_video" not in data:
                continue  # List-Response → kein Modal
            selected = data.get("selected_video") if isinstance(data.get("selected_video"), dict) else {}
            embed_url = str(selected.get("embed_url") or "").strip()
            watch_url = str(selected.get("watch_url") or "").strip()
            video_id = str(selected.get("video_id") or "").strip()
            title = str(selected.get("title") or "").strip()
            channel = str(selected.get("channel") or "").strip()
            is_embeddable = bool(selected.get("is_embeddable", True))
            if not watch_url and len(video_id) == 11:
                watch_url = f"https://www.youtube.com/watch?v={video_id}"
            if not embed_url and len(video_id) == 11:
                embed_url = f"https://www.youtube.com/embed/{video_id}?rel=0"
            if not watch_url and not embed_url:
                continue
            modal_title = title if not channel else f"{title} - {channel}"
            return {
                "type": "video",
                "payload": {
                    "source": "youtube",
                    "url": watch_url or embed_url,
                    "title": modal_title or "Video",
                    "embed_url": embed_url if is_embeddable else "",
                    "is_embeddable": is_embeddable,
                    "external_only": (not is_embeddable),
                    "external_hint": "Nur direkt auf YouTube verfügbar.",
                },
                "options": {"auto_open": True, "pinnable": True},
            }
        return None

    def _build_planner_capability_groups(self, *, allowed_skill_ids: List[str]) -> Dict[str, List[str]]:
        if self.capability_registry is not None and hasattr(self.capability_registry, "get_capability_groups"):
            groups = self.capability_registry.get_capability_groups(allowed_skill_ids=allowed_skill_ids)
            if groups:
                return groups
        return self.skill_selector.filter_capability_groups(
            tool_manager.get_capability_groups(),
            allowed_skill_ids,
        )

    def _build_planner_context(
        self,
        *,
        user_text: str,
        relevant_skill_ids: List[str],
        intent_result: IntentDetectionResult,
    ) -> PlannerContext:
        allowed = [
            str(skill_id).strip()
            for skill_id in (relevant_skill_ids or [])
            if str(skill_id).strip()
        ]
        forbidden: List[str] = []
        negative_constraints: List[str] = []
        primary_intent = str(getattr(intent_result, "primary_intent", "") or "")

        if getattr(intent_result, "is_calendar_intent", False) or primary_intent == "calendar":
            forbidden.extend(["system.create_pdf", "knowledge.edit_pdf", "system.generate_image"])
            negative_constraints.append(
                "Kalender-Turn: PDF-, Bild- und Nicht-Kalender-Tools sind verboten. Nutze Kalender-Skills."
            )
        if getattr(intent_result, "is_personal_recall", False) or primary_intent == "personal_recall":
            forbidden.extend(["system.websearch", "system.rss_news"])
            negative_constraints.append(
                "Personal-Recall-Turn: Websuche ist verboten; nutze Memory-/Kontext-Skills."
            )
        if getattr(intent_result, "is_shopping_intent", False) or primary_intent == "shopping":
            negative_constraints.append(
                "Shopping-Turn: system.price_comparison ist Pflicht; system.websearch darf nicht als Ersatz geplant werden."
            )

        forbidden_set = {s for s in forbidden if s}
        return PlannerContext(
            original_user_text=str(user_text or ""),
            allowed_skill_ids=[s for s in allowed if s not in forbidden_set],
            forbidden_skill_ids=sorted(forbidden_set),
            negative_constraints=negative_constraints,
        )

    def _build_planner_provider_profile(
        self,
        *,
        provider: str,
        requested_model: Optional[str],
        planner_model: str,
    ) -> PlannerProviderProfile:
        model_id = str(planner_model or requested_model or "").strip()
        model_l = model_id.lower()
        provider_key = str(provider or "").strip().lower()
        is_local = provider_key == "ollama" or ":" in model_l
        if is_local:
            model_class = "local"
            cap = 4
        elif "nano" in model_l:
            model_class = "nano"
            cap = 4
        elif "mini" in model_l or "flash" in model_l:
            model_class = "mini"
            cap = 6
        elif "pro" in model_l or "logic" in model_l or "gpt-5" in model_l:
            model_class = "logic"
            cap = 8
        else:
            model_class = "standard"
            cap = 6
        return PlannerProviderProfile(
            provider=provider_key,
            requested_model=str(requested_model or ""),
            planner_model=model_id,
            model_class=model_class,
            is_local=is_local,
            max_iterations_cap=cap,
            allow_llm_planning=True,
        )

    async def run_agent_factory(
        self,
        *,
        enabled: bool,
        chat_id: Optional[int],
        user_text: str,
        relevant_skill_ids: List[str],
        provider: str,
        model: Optional[str],
        api_key: str,
        intent_result: IntentDetectionResult,
    ) -> ExecutionResponse:
        if not enabled:
            return ExecutionResponse(text="", agent_payload=None, tool_calls=[], is_agent_flow=False)

        try:
            planner_model = self._resolve_planner_model(provider=provider, requested_model=model)
            provider_profile = self._build_planner_provider_profile(
                provider=provider,
                requested_model=model,
                planner_model=planner_model,
            )
            planner_context = self._build_planner_context(
                user_text=user_text,
                relevant_skill_ids=relevant_skill_ids,
                intent_result=intent_result,
            )
            capability_groups = self._build_planner_capability_groups(
                allowed_skill_ids=planner_context.allowed_skill_ids,
            )
            completed_skills: List[str] = []
            step_outputs: List[str] = []
            failed_steps: List[str] = []
            fatal_failed_skills: set[str] = set()
            round_trace_ids: List[str] = []
            last_spec: Optional[AgentSpec] = None
            initial_plan_skills: Optional[set[str]] = None
            planner_lockdown_after_pdf = False
            max_atomic_rounds = 6

            for round_idx in range(1, max_atomic_rounds + 1):
                planner_prompt = self._build_atomic_planner_prompt(user_text, step_outputs, failed_steps)
                if planner_lockdown_after_pdf:
                    planner_prompt += (
                        "\n\nLOCKDOWN_MODE: CREATE_PDF_DONE\n"
                        "Regel: Keine weiteren Tools planen. required_skills MUSS [] sein."
                    )
                agent_spec = await self.agent_planner.plan(
                    user_prompt=planner_prompt,
                    intent_result=intent_result,
                    planner_context=planner_context.model_copy(
                        update={
                            "completed_skills": list(completed_skills),
                            "failed_steps": list(failed_steps),
                            "round_idx": round_idx,
                            "lockdown_after_pdf": planner_lockdown_after_pdf,
                        }
                    ),
                    provider_profile=provider_profile,
                    capability_registry=self.capability_registry,
                    capability_groups=capability_groups,
                    relevant_skill_ids=relevant_skill_ids,
                    provider=provider,
                    model=planner_model,
                    api_key=api_key or "",
                )
                last_spec = agent_spec
                planned_skills = [
                    str(skill).strip() for skill in (agent_spec.required_skills or []) if str(skill).strip()
                ]
                if not planned_skills:
                    logger.info(
                        "ATOMIC LOOP: [EXIT] Keine weiteren Skills geplant. Starte finale Synthese."
                    )
                    final_text = await self._run_final_synthesis(
                        user_text=user_text,
                        step_outputs=step_outputs,
                        provider=provider,
                        model=planner_model,
                        api_key=api_key,
                        chat_id=chat_id,
                        completed_skills=completed_skills,
                    )
                    return ExecutionResponse(
                        text=final_text,
                        agent_payload={
                            "name": (last_spec.name if last_spec else "Atomic Agent"),
                            "goal": (last_spec.goal if last_spec else "Atomic Loop"),
                            "required_skills": list(completed_skills),
                            "trace_id": round_trace_ids[0] if round_trace_ids else None,
                            "trace_ids": list(round_trace_ids),
                            "mode": "atomic_loop",
                        },
                        tool_calls=[],
                        is_agent_flow=True,
                    )
                pending_skills = [
                    skill
                    for skill in planned_skills
                    if skill not in completed_skills and skill not in fatal_failed_skills
                ]
                if initial_plan_skills is None and pending_skills:
                    initial_plan_skills = {str(skill).strip() for skill in pending_skills if str(skill).strip()}

                if not pending_skills:
                    logger.info(
                        "ATOMIC LOOP RUNDE %s: Planner sieht keine neuen Tasks mehr -> finale Antwort.",
                        round_idx,
                    )
                    logger.info("ATOMIC LOOP: [EXIT] Grund=NO_PENDING_SKILLS")
                    if fatal_failed_skills and not completed_skills:
                        return ExecutionResponse(
                            text=self._build_atomic_final_text(user_text, step_outputs),
                            agent_payload=None,
                            tool_calls=[],
                            is_agent_flow=False,
                            error={
                                "code": "AGENT_FACTORY_FAILED",
                                "message": "Alle geplanten Skills sind final fehlgeschlagen.",
                                "details": {"failed_skills": sorted(fatal_failed_skills)},
                            },
                        )
                    if not completed_skills and not step_outputs:
                        return ExecutionResponse(
                            text=self._build_atomic_final_text(user_text, step_outputs),
                            agent_payload={
                                "name": (last_spec.name if last_spec else "Atomic Agent"),
                                "goal": (last_spec.goal if last_spec else "Atomic Loop"),
                                "required_skills": list(completed_skills),
                                "trace_id": round_trace_ids[0] if round_trace_ids else None,
                                "trace_ids": list(round_trace_ids),
                                "mode": "atomic_loop",
                            },
                            tool_calls=[],
                            is_agent_flow=True,
                        )
                    final_text = await self._run_atomic_clean_synthesis(
                        user_text=user_text,
                        step_outputs=step_outputs,
                        provider=provider,
                        model=planner_model,
                        api_key=api_key,
                        chat_id=chat_id,
                        completed_skills=completed_skills,
                    )
                    return ExecutionResponse(
                        text=final_text,
                        agent_payload={
                            "name": (last_spec.name if last_spec else "Atomic Agent"),
                            "goal": (last_spec.goal if last_spec else "Atomic Loop"),
                            "required_skills": list(completed_skills),
                            "trace_id": round_trace_ids[0] if round_trace_ids else None,
                            "trace_ids": list(round_trace_ids),
                            "mode": "atomic_loop",
                        },
                        tool_calls=[],
                        is_agent_flow=True,
                    )

                current_skill = pending_skills[0]
                skill_label = self._skill_label(current_skill)
                logger.info("ATOMIC LOOP RUNDE %s: Planung %s", round_idx, skill_label)

                spec_name = str(getattr(agent_spec, "name", "Atomic Agent") or "Atomic Agent")
                spec_goal = str(getattr(agent_spec, "goal", user_text) or user_text)
                spec_instructions = str(
                    getattr(agent_spec, "instructions", "Arbeite strikt zielorientiert.")
                    or "Arbeite strikt zielorientiert."
                )

                step_spec = AgentSpec(
                    name=spec_name,
                    goal=spec_goal,
                    required_skills=[current_skill],
                    instructions=spec_instructions,
                    max_iterations=1,
                )
                step_result = await self.agent_runtime.run(
                    spec=step_spec,
                    user_prompt=planner_prompt,
                    original_user_text=user_text,
                    provider=provider,
                    model=planner_model,
                    api_key=api_key or "",
                    chat_id=chat_id,
                    skip_final_synthesis=True,
                )
                step_text = str(step_result.get("text") or "").strip()
                step_trace_id = step_result.get("trace_id")
                if step_trace_id:
                    round_trace_ids.append(str(step_trace_id))

                error_info = self._extract_step_error(step_result)
                if error_info:
                    error_code = str(error_info.get("code") or "UNKNOWN_ERROR")
                    error_message = str(error_info.get("message") or "Unbekannter Fehler")
                    fatal_failed_skills.add(current_skill)
                    failed_steps.append(
                        f"[{current_skill}] FAILED_FINAL code={error_code} message={error_message}"
                    )
                    logger.warning(
                        "ATOMIC LOOP RUNDE %s: Fataler Fehler bei %s (code=%s). Skill wird final gesperrt.",
                        round_idx,
                        skill_label,
                        error_code,
                    )
                    logger.info("ATOMIC LOOP: [NEUER LOOP]")
                    continue

                if not self._step_has_tool_call(step_result):
                    logger.info(
                        "ATOMIC LOOP RUNDE %s: Modell lieferte Text ohne Tool-Call -> finale Antwort.",
                        round_idx,
                    )
                    logger.info("ATOMIC LOOP: [EXIT] Grund=TEXT_ONLY_STEP")
                    final_text = step_text or self._build_atomic_final_text(user_text, step_outputs)
                    return ExecutionResponse(
                        text=final_text,
                        agent_payload={
                            "name": (last_spec.name if last_spec else "Atomic Agent"),
                            "goal": (last_spec.goal if last_spec else "Atomic Loop"),
                            "required_skills": list(completed_skills),
                            "trace_id": round_trace_ids[0] if round_trace_ids else None,
                            "trace_ids": list(round_trace_ids),
                            "mode": "atomic_loop",
                        },
                        tool_calls=[],
                        is_agent_flow=True,
                    )

                logger.info("ATOMIC LOOP RUNDE %s: Executing %s", round_idx, skill_label)
                logger.info("ATOMIC LOOP RUNDE %s: Task Complete %s", round_idx, skill_label)

                completed_skills.append(current_skill)
                if step_text:
                    step_outputs.append(f"[{current_skill}] {step_text}")

                if self._is_pdf_create_skill(current_skill) and self._is_pdf_creation_request(user_text):
                    planner_lockdown_after_pdf = True
                    logger.info(
                        "ATOMIC LOOP RUNDE %s: PDF-Erstellung abgeschlossen -> Planner-Lockdown fuer Folgerunde aktiv.",
                        round_idx,
                    )
                    logger.info("ATOMIC LOOP: [NEUER LOOP]")
                    continue

                tools_planned = [
                    skill
                    for skill in pending_skills[1:]
                    if skill and skill not in completed_skills and skill not in fatal_failed_skills
                ]
                if not tools_planned:
                    logger.info(
                        "ATOMIC LOOP RUNDE %s: Keine weiteren Tools in aktueller Planung -> finale Antwort.",
                        round_idx,
                    )
                    logger.info("ATOMIC LOOP: [EXIT] Grund=NO_TOOLS_PLANNED_AFTER_STEP")
                    if len(step_outputs) == 1:
                        final_text = self._build_atomic_final_text(user_text, step_outputs)
                    else:
                        final_text = await self._run_atomic_clean_synthesis(
                            user_text=user_text,
                            step_outputs=step_outputs,
                            provider=provider,
                            model=planner_model,
                            api_key=api_key,
                            chat_id=chat_id,
                            completed_skills=completed_skills,
                        )
                    return ExecutionResponse(
                        text=final_text,
                        agent_payload={
                            "name": (last_spec.name if last_spec else "Atomic Agent"),
                            "goal": (last_spec.goal if last_spec else "Atomic Loop"),
                            "required_skills": list(completed_skills),
                            "trace_id": round_trace_ids[0] if round_trace_ids else None,
                            "trace_ids": list(round_trace_ids),
                            "mode": "atomic_loop",
                        },
                        tool_calls=[],
                        is_agent_flow=True,
                    )

                if initial_plan_skills:
                    attempted_skills = set(completed_skills) | set(fatal_failed_skills)
                    if attempted_skills.issuperset(initial_plan_skills):
                        logger.info(
                            "ATOMIC LOOP RUNDE %s: Alle initial geplanten Skills ausgefuehrt -> finale Antwort.",
                            round_idx,
                        )
                        logger.info("ATOMIC LOOP: [EXIT] Grund=ALL_INITIAL_SKILLS_COMPLETED")
                        final_text = await self._run_atomic_clean_synthesis(
                            user_text=user_text,
                            step_outputs=step_outputs,
                            provider=provider,
                            model=planner_model,
                            api_key=api_key,
                            chat_id=chat_id,
                            completed_skills=completed_skills,
                        )
                        return ExecutionResponse(
                            text=final_text,
                            agent_payload={
                                "name": (last_spec.name if last_spec else "Atomic Agent"),
                                "goal": (last_spec.goal if last_spec else "Atomic Loop"),
                                "required_skills": list(completed_skills),
                                "trace_id": round_trace_ids[0] if round_trace_ids else None,
                                "trace_ids": list(round_trace_ids),
                                "mode": "atomic_loop",
                            },
                            tool_calls=[],
                            is_agent_flow=True,
                        )

                logger.info("ATOMIC LOOP: [NEUER LOOP]")

            logger.warning(
                "ATOMIC LOOP STOP: Maximal %s Runden erreicht. Liefere Teilantwort.",
                max_atomic_rounds,
            )
            final_text = await self._run_atomic_clean_synthesis(
                user_text=user_text,
                step_outputs=step_outputs,
                provider=provider,
                model=planner_model,
                api_key=api_key,
                chat_id=chat_id,
                completed_skills=completed_skills,
            )
            return ExecutionResponse(
                text=final_text,
                agent_payload={
                    "name": (last_spec.name if last_spec else "Atomic Agent"),
                    "goal": (last_spec.goal if last_spec else "Atomic Loop"),
                    "required_skills": list(completed_skills),
                    "trace_id": round_trace_ids[0] if round_trace_ids else None,
                    "trace_ids": list(round_trace_ids),
                    "mode": "atomic_loop",
                },
                tool_calls=[],
                is_agent_flow=True,
            )
        except Exception as exc:
            logger.error(
                "Error in orchestrator.execution_engine.run_agent_factory",
                exc_info=True,
            )
            return ExecutionResponse(
                text="",
                agent_payload=None,
                tool_calls=[],
                is_agent_flow=False,
                error={
                    "code": "AGENT_FACTORY_FAILED",
                    "message": str(exc),
                },
            )

    def _resolve_model_for_skill(self, skill_id: str, provider: str, requested_model: Optional[str]) -> str:
        """
        Resolves the appropriate model for a skill execution.
        Rule: override only if skill tier rank > user model tier rank.
        Tier ranking: speed=1, balanced=2, logic=3.
        """
        if not skill_id or not provider:
            return requested_model or ""

        provider_key = str(provider or "").strip().lower()
        provider_map = self.model_hierarchy.get(provider_key) or {}
        if not isinstance(provider_map, dict) or not provider_map:
            return requested_model or ""

        tier_rank = {"speed": 1, "balanced": 2, "logic": 3}

        def _normalize_tier(raw_tier: Optional[str]) -> str:
            t = str(raw_tier or "").strip().lower()
            if t in tier_rank:
                return t
            # legacy aliases
            if t in ("quality", "reasoning", "high"):
                return "logic"
            if t in ("default", "normal", "medium"):
                return "balanced"
            return ""

        def _tier_for_model(model_id: str) -> str:
            needle = str(model_id or "").strip()
            if not needle:
                return ""
            for tier_name, configured_model in provider_map.items():
                if str(configured_model or "").strip() == needle:
                    return _normalize_tier(str(tier_name))
            return ""

        optimal_tier = tool_manager.get_optimal_model_tier(skill_id, provider)
        optimal_tier_norm = _normalize_tier(optimal_tier)
        user_model = str(requested_model or "").strip()
        user_tier = _tier_for_model(user_model)
        if not user_tier:
            user_tier = "logic" if user_model else "balanced"

        # Map tier to actual model using model_hierarchy; only upgrade, never downgrade.
        if optimal_tier_norm and optimal_tier_norm in provider_map:
            if tier_rank.get(optimal_tier_norm, 0) > tier_rank.get(user_tier, 0):
                resolved_model = str(provider_map[optimal_tier_norm] or "").strip()
                if not resolved_model:
                    return user_model or str(provider_map.get("logic") or "")
                logger.info(
                    "MODEL-TIER-OVERRIDE: Skill '%s' upgrades tier '%s' -> '%s' (provider: %s)",
                    skill_id, user_tier, optimal_tier_norm, provider_key
                )
                
                # Log fallback_trigger for model upgrade
                import asyncio
                from backend.services.logging.logger_core import log_event
                from backend.data.schemas_logging import LogEventCreate
                try:
                    asyncio.create_task(log_event(LogEventCreate(
                        event_type="fallback_trigger",
                        status="success",
                        payload={
                            "input_hash": str(hash(skill_id)),
                            "output_summary": f"Model tier upgraded from {user_tier} to {optimal_tier_norm}",
                            "error_code": None
                        }
                    )))
                except Exception as log_exc:
                    logger.error(f"Failed to log fallback_trigger: {log_exc}")
                
                return resolved_model
            logger.info(
                "MODEL-TIER-OVERRIDE: Skill '%s' requests tier '%s' but user tier '%s' is equal/higher; keep model '%s' (provider: %s)",
                skill_id, optimal_tier_norm, user_tier, user_model, provider_key
            )
            return user_model or str(provider_map.get("logic") or "")

        # Fallback to requested model
        return user_model or str(provider_map.get("logic") or "")

    def _find_provider_for_model(self, model_id: Optional[str]) -> str:
        needle = str(model_id or "").strip()
        if not needle:
            return ""
        # 1. Check model hierarchy first
        for prov, tiers in (self.model_hierarchy or {}).items():
            if not isinstance(tiers, dict):
                continue
            for _tier, configured_model in tiers.items():
                if str(configured_model or "").strip() == needle:
                    return str(prov or "").strip().lower()
        # 2. Fallback: Check model catalog for Koppel-Prinzip (provider consistency)
        try:
            catalog = load_model_catalog()
            for entry in (catalog or []):
                if not isinstance(entry, dict):
                    continue
                if str(entry.get("id") or "").strip() == needle:
                    return str(entry.get("provider") or "").strip().lower()
        except Exception:
            pass  # Catalog loading failed, proceed with empty result
        return ""

    def _normalize_provider_model_pair(
        self,
        *,
        provider: Optional[str],
        model: Optional[str],
        fallback_model: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Keep provider/model consistent across MoA upgrades.
        If model belongs to another known provider, switch provider too.
        If model is empty, use provider fallback.
        """
        prov = str(provider or "").strip().lower()
        mdl = str(model or "").strip()
        fallback = str(fallback_model or "").strip()

        if not prov:
            prov = self._find_provider_for_model(mdl) or self._find_provider_for_model(fallback)
        if not prov:
            return "", mdl or fallback

        owner = self._find_provider_for_model(mdl) if mdl else ""
        if owner and owner != prov:
            logger.warning(
                "PROVIDER-MODEL-MISMATCH: model '%s' belongs to provider '%s' (active '%s') — switching provider.",
                mdl,
                owner,
                prov,
            )
            prov = owner

        if not mdl:
            provider_map = self.model_hierarchy.get(prov) if isinstance(self.model_hierarchy, dict) else {}
            if isinstance(provider_map, dict):
                mdl = str(provider_map.get("logic") or provider_map.get("balanced") or provider_map.get("speed") or "")
            if not mdl:
                mdl = fallback

        return prov, mdl

    def _resolve_planner_model(self, *, provider: str, requested_model: Optional[str]) -> str:
        if requested_model:
            requested = str(requested_model)
            if str(provider or "").lower() != "ollama":
                return requested
            if not self._is_reasoning_priority_ollama_node():
                return requested
            if not self._is_degraded_ollama_allrounder(requested):
                return requested
            model_catalog = load_model_catalog()
            candidates = self._extract_reasoning_model_candidates(model_catalog)
            preferred = self._pick_preferred_reasoning_model(candidates)
            return preferred or requested

        default_model = str(self.model_hierarchy[provider]["logic"])
        if str(provider or "").lower() != "ollama":
            return default_model

        try:
            if not self._is_reasoning_priority_ollama_node():
                return default_model

            model_catalog = load_model_catalog()
            candidates = self._extract_reasoning_model_candidates(model_catalog)
            preferred = self._pick_preferred_reasoning_model(candidates)
            if preferred:
                return preferred
        except Exception:
            logger.debug("Planner model override for reasoning node skipped.", exc_info=True)

        return default_model

    @staticmethod
    def _extract_reasoning_model_candidates(model_catalog: Dict[str, Any]) -> List[str]:
        candidates: List[tuple[float, str]] = []
        for model_id, meta in (model_catalog or {}).items():
            if not isinstance(meta, dict):
                continue
            if str(meta.get("provider") or "").lower() != "ollama":
                continue
            if str(meta.get("reasoning_capability") or "").lower() != "high":
                continue
            size_score = OrchestratorExecutionEngine._extract_model_size_b(str(model_id))
            if size_score < 12.0:
                continue
            candidates.append((size_score, str(model_id)))

        candidates.sort(key=lambda item: (-item[0], item[1]))
        return [model_id for _, model_id in candidates]

    @staticmethod
    def _pick_preferred_reasoning_model(candidates: List[str]) -> str:
        preferred_ids = ["mistral-nemo:12b", "qwen2.5:14b", "gemma2:27b"]
        for preferred in preferred_ids:
            if preferred in candidates:
                return preferred
        return candidates[0] if candidates else ""

    @staticmethod
    def _is_degraded_ollama_allrounder(model_id: str) -> bool:
        normalized = str(model_id or "").strip().lower()
        base_model = normalized.split("@", 1)[0]
        return base_model == "llama3.1:8b"

    @staticmethod
    def _extract_model_size_b(model_id: str) -> float:
        normalized = str(model_id or "").lower()
        match = re.search(r"(\d+(?:\.\d+)?)b", normalized)
        if not match:
            return 0.0
        try:
            return float(match.group(1))
        except Exception:
            return 0.0

    def _is_reasoning_priority_ollama_node(self) -> bool:
        config = load_config_data()
        nodes_raw = config.get("ollama_nodes") if isinstance(config, dict) else None
        nodes = [node for node in (nodes_raw or []) if isinstance(node, dict)]
        if not nodes:
            return False

        active_node = next((node for node in nodes if bool(node.get("active"))), nodes[0])
        node_id = str(active_node.get("id") or "").lower()
        node_name = str(active_node.get("name") or "").lower()
        node_url = str(active_node.get("url") or "").strip()
        node_host = str(urlparse(node_url).hostname or "").lower() if node_url else ""
        if any("rolf" in token for token in (node_id, node_name, node_host) if token):
            return True

        local_host = str(os.getenv("COMPUTERNAME") or os.getenv("HOSTNAME") or "").lower()
        return "rolf" in local_host

    async def run_tool_loop(
        self,
        *,
        orchestrator_context: OrchestratorContext,
        tool_executor,
        gateway_kwargs: Dict[str, Any],
        fallback_summary: str,
        current_limit: int,
        bypass_policy_this_turn: bool,
        set_policy_pending,
        chat_id: Optional[int],
        agent_flow_error: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResponse:
        current_iteration = 0
        response = None
        latest_ui_command = None
        font_fallback_notice = None
        factcheck_modifications_detected = None
        latest_tool_calls: List[Dict[str, Any]] = []
        all_used_skills: List[str] = []
        canonical_maps_link: Optional[str] = None
        country_not_found_detected = False
        # 💎 AGGREGATOR FIX: Buffer für alle Tool-Resultate
        results_buffer: List[Dict[str, Any]] = []
        # 💎 COST-AGGREGATION FIX: Akkumuliere Kosten über alle Iterationen
        aggregated_tokens_input = 0
        aggregated_tokens_output = 0
        aggregated_total_cost = 0.0
        websearch_fallback_attempted = False

        gateway_kwargs = dict(gateway_kwargs)
        reason_and_respond_fn = gateway_kwargs.pop("reason_and_respond_fn", None)
        if not callable(reason_and_respond_fn):
            reason_and_respond_fn = llm_gateway.reason_and_respond
        user_selected_provider = str(gateway_kwargs.get("provider") or "").strip().lower()
        user_selected_model = str(gateway_kwargs.get("model") or "").strip()
        user_selected_provider, user_selected_model = self._normalize_provider_model_pair(
            provider=user_selected_provider,
            model=user_selected_model,
            fallback_model=user_selected_model,
        )
        current_call_model = user_selected_model
        current_call_provider = user_selected_provider
        had_tool_round = False
        # Gemini: interner Multi-Runden-Loop im Gateway umgeht Dispatcher [GEMINI-FIX] + Hard-Loop-Breaker.
        if reason_and_respond_fn is not llm_gateway.reason_and_respond:
            gateway_kwargs["_gemini_engine_owned_tool_loop"] = True
        if not isinstance(gateway_kwargs.get("chat_history"), list):
            gateway_kwargs["chat_history"] = [dict(item) for item in orchestrator_context.history]

        if agent_flow_error:
            gateway_kwargs["chat_history"].append(
                {
                    "role": "system",
                    "content": (
                        "AGENT-FALLBACK: Der Agent-Flow ist fehlgeschlagen "
                        f"(code={agent_flow_error['code']}). Führe den Standard-Lifecycle robust weiter."
                    ),
                }
            )

        # 🔥 MOA-HARD-LOCK: execute only after dispatcher smalltalk decision.
        # This keeps greeting/smalltalk turns out of MoA routing entirely.
        _allow_moa_hard_lock = bool(gateway_kwargs.get("_allow_moa_hard_lock"))
        _pre_skill_ids = gateway_kwargs.get("allowed_skill_ids") or []
        _pre_provider = current_call_provider or gateway_kwargs.get("provider") or ""
        _pre_base_model = current_call_model or gateway_kwargs.get("model") or ""
        if _allow_moa_hard_lock and _pre_skill_ids and _pre_provider:
            for _sid in _pre_skill_ids:
                _resolved = self._resolve_model_for_skill(_sid, _pre_provider, _pre_base_model)
                if _resolved and _resolved != _pre_base_model:
                    logger.warning(
                        f"🔥 MOA-HARD-LOCK: Overriding base model '{_pre_base_model}' "
                        f"with Skill-Model '{_resolved}' for tool loop execution."
                    )
                    current_call_provider, current_call_model = self._normalize_provider_model_pair(
                        provider=_pre_provider,
                        model=_resolved,
                        fallback_model=_pre_base_model,
                    )
                    # 🔐 AUTH-ISOLATION (MOA-HARD-LOCK): Bei Provider-Switch frischen API-Key laden
                    if current_call_provider and _pre_provider and current_call_provider != _pre_provider:
                        logger.warning(
                            f"AUTH-ISOLATION (MOA-HARD-LOCK): Provider-Switch erkannt ({_pre_provider} -> {current_call_provider}). "
                            f"Lade neuen API-Key für '{current_call_provider}'."
                        )
                        fresh_key = _reload_api_key_for_provider(current_call_provider)
                        if fresh_key:
                            gateway_kwargs["api_key"] = fresh_key
                        else:
                            # 🔐 CRITICAL: Kein Key → Switch ABBRECHEN, original Provider behalten
                            logger.error(
                                f"AUTH-ISOLATION: Kein API-Key für '{current_call_provider}' gefunden! "
                                f"Breche Provider-Switch ab, bleibe bei '{_pre_provider}'."
                            )
                            current_call_provider = _pre_provider
                            current_call_model = _pre_base_model
                    break  # First skill with tier wins

        # IRON-GATE: State for price_comparison output auditing
        _iron_gate_correction_done = False
        _ig_budget = (gateway_kwargs.get("_user_budget_info") or {}).get("limit")

        while current_iteration < current_limit:
            if had_tool_round and user_selected_model:
                # Restore user model for synthesis turn after tool execution.
                current_call_provider = user_selected_provider
                current_call_model = user_selected_model
            current_call_provider, current_call_model = self._normalize_provider_model_pair(
                provider=current_call_provider or gateway_kwargs.get("provider"),
                model=current_call_model,
                fallback_model=user_selected_model,
            )
            prompt_cache_decision = clone_decision_for_route(
                decision_from_gateway_kwargs(gateway_kwargs),
                provider=current_call_provider,
                model=current_call_model or user_selected_model,
            )
            if prompt_cache_decision is not None:
                gateway_kwargs["_prompt_cache_decision"] = prompt_cache_decision
            # 🔐 AUTH-ISOLATION: Bei Provider-Switch frischen API-Key laden
            original_provider = str(gateway_kwargs.get("provider") or "").strip().lower()
            if current_call_provider and original_provider and current_call_provider != original_provider:
                logger.warning(
                    f"AUTH-ISOLATION: Provider-Switch erkannt ({original_provider} -> {current_call_provider}). "
                    f"Lade neuen API-Key für '{current_call_provider}'."
                )
                fresh_key = _reload_api_key_for_provider(current_call_provider)
                if fresh_key:
                    gateway_kwargs["api_key"] = fresh_key
                else:
                    # 🔐 CRITICAL: Kein Key → Switch ABBRECHEN, original Provider behalten
                    logger.error(
                        f"AUTH-ISOLATION: Kein API-Key für '{current_call_provider}' gefunden! "
                        f"Breche Provider-Switch ab, bleibe bei '{original_provider}'."
                    )
                    current_call_provider = original_provider
                    current_call_model = user_selected_model
            # 💎 AUDIT-LOOP-FORCED-START (sync):
            # If forced_tool_args + force_tool_name are present on the first iteration,
            # synthesize the initial tool_calls and skip the LLM round entirely.
            # This replaces the old fake-assistant-message injection that caused
            # OpenAI 400 BadRequest by polluting the message history.
            _forced_tool_args = gateway_kwargs.get("forced_tool_args") if current_iteration == 0 else None
            _forced_tool_name = str(gateway_kwargs.get("force_tool_name") or "").strip() if current_iteration == 0 else ""
            if _forced_tool_args and _forced_tool_name:
                _provider_lc = str(current_call_provider or gateway_kwargs.get("provider") or "").lower()
                _normalized_name = (
                    _forced_tool_name.replace(".", "_") if _provider_lc == "openai" else _forced_tool_name
                )
                _synth_call_id = f"call_{uuid.uuid4().hex[:16]}"
                _synth_tool_call = {
                    "id": _synth_call_id,
                    "type": "function",
                    "function": {
                        "name": _normalized_name,
                        "arguments": json.dumps(_forced_tool_args, ensure_ascii=False),
                    },
                }
                response = {
                    "type": "tool_code",
                    "text": "",
                    "tool_calls": [_synth_tool_call],
                    "raw_assistant_response": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [_synth_tool_call],
                    },
                    "usage": {},
                    "cost": {},
                    "agent_payload": None,
                }
                logger.info(
                    "💎 AUDIT-LOOP-FORCED-START (sync): Skipping LLM call on iteration %d; "
                    "injecting pre-filled tool-call for %s (normalized: %s, provider=%s)",
                    current_iteration, _forced_tool_name, _normalized_name, _provider_lc,
                )
                # Consume forced args so subsequent iterations run the normal LLM flow.
                gateway_kwargs.pop("forced_tool_args", None)
                gateway_kwargs.pop("force_tool_name", None)
                gateway_kwargs.pop("forced_tool", None)
            else:
                call_kwargs = dict(gateway_kwargs)
                call_kwargs["provider"] = current_call_provider
                call_kwargs["model"] = current_call_model or user_selected_model
                # 💎 VIDEO-FIX: Filter out unsupported parameters for non-stream gateways
                # force_tool_name is only supported in streaming path, not in reason_and_respond
                call_kwargs.pop("force_tool_name", None)
                call_kwargs.pop("forced_tool", None)
                call_kwargs.pop("forced_tool_args", None)
                call_kwargs.pop("_prompt_cache_decision", None)
                try:
                    response = await reason_and_respond_fn(**call_kwargs)
                except Exception:
                    logger.error("Error in orchestrator.execution_engine.run_tool_loop: synthesis crash", exc_info=True)
                    # 💎 AUDIT-LOOP-FALLBACK-SHAPE: build a complete LLM-response shape
                    # so downstream logic (cost aggregation, fact extraction trigger,
                    # response finalizer) never dereferences missing fields.
                    response = {
                        "type": "text",
                        "text": fallback_summary,
                        "tool_calls": [],
                        "raw_assistant_response": {
                            "role": "assistant",
                            "content": fallback_summary,
                        },
                        "usage": {},
                        "cost": {},
                        "agent_payload": None,
                    }
                    break

            # 💎 COST-AGGREGATION FIX: Extrahiere und addiere Usage/Cost aus jeder Iteration
            if isinstance(response, dict):
                prompt_cache_decision = decision_from_gateway_kwargs(gateway_kwargs)
                if prompt_cache_decision is not None:
                    response["usage"] = merge_decision_into_usage(response.get("usage") or {}, prompt_cache_decision)
                usage_data = response.get("usage") or {}
                cost_data = response.get("cost") or {}
                
                # Addiere Tokens (handle verschiedene Key-Namen)
                input_tokens = usage_data.get("prompt_tokens") or usage_data.get("input_tokens") or 0
                output_tokens = usage_data.get("completion_tokens") or usage_data.get("output_tokens") or 0
                total_cost = cost_data.get("total_cost") or 0.0
                
                aggregated_tokens_input += int(input_tokens)
                aggregated_tokens_output += int(output_tokens)
                aggregated_total_cost += float(total_cost)
                
                logger.debug(
                    "COST-AGGREGATION: Iteration %d - Input: %d, Output: %d, Cost: %.4f€ | Running: %.4f€",
                    current_iteration, input_tokens, output_tokens, total_cost, aggregated_total_cost
                )

                # 💎 PER-ITERATION COST PERSISTENCE: save with the model active in this iteration
                if float(total_cost) > 0 and self.db is not None:
                    try:
                        from backend.services.cost_service import create_cost_entry
                        _iter_model = current_call_model or user_selected_model or "unknown"
                        _iter_provider = current_call_provider or gateway_kwargs.get("provider") or "unknown"
                        _iter_tokens_saved = int(
                            (prompt_cache_decision.estimated_tokens_saved if prompt_cache_decision is not None else 0) or 0
                        )
                        create_cost_entry(
                            db=self.db,
                            amount=float(total_cost),
                            model=_iter_model,
                            provider=_iter_provider,
                            source_type="conversation",
                            input_tokens=int(input_tokens),
                            output_tokens=int(output_tokens),
                            tokens_saved=_iter_tokens_saved,
                        )
                        # 💎 COST-PERSISTENCE FIX: Explizites db.commit() nach create_cost_entry
                        # Dies stellt sicher, dass Kosten auch im Meta-Agent-Kontext persistieren
                        self.db.commit()
                        logger.info(
                            "COST-PERSIST: Iteration %d saved %.6f€ for model '%s' (tokens_saved=%d)",
                            current_iteration, total_cost, _iter_model, _iter_tokens_saved
                        )
                    except Exception:
                        logger.warning("COST-PERSIST: Failed to save iteration cost", exc_info=True)

            if isinstance(response, dict) and response.get("ui_command"):
                latest_ui_command = response["ui_command"]
            # 💎 OpenAI-Silo: Interner Tool-Loop gibt _internal_tool_results zurück
            _internal_results = response.get("_internal_tool_results") if isinstance(response, dict) else None
            if isinstance(_internal_results, list):
                for _itr in _internal_results:
                    if isinstance(_itr, dict):
                        results_buffer.append(_itr)
                        _skill_name = str(_itr.get("name") or "").strip()
                        if _skill_name and _skill_name not in all_used_skills:
                            all_used_skills.append(_skill_name)
            tool_calls = response.get("tool_calls") if isinstance(response, dict) else []
            latest_tool_calls = tool_calls if isinstance(tool_calls, list) else []
            
            # 💎 MODEL-TIER-OVERRIDE: Check if any tool has optimal_model_tier and upgrade model accordingly
            # This must happen AFTER we get tool_calls from the response and BEFORE we break if empty
            if tool_calls and current_iteration == 0:
                for tool_call in tool_calls:
                    function = tool_call.get("function") or {}
                    tool_name = function.get("name", "")
                    if tool_name:
                        resolved_skill = tool_manager.get_skill_id(tool_name)
                        provider = current_call_provider or gateway_kwargs.get("provider", "")
                        requested_model = current_call_model or user_selected_model
                        optimal_model = self._resolve_model_for_skill(
                            resolved_skill, provider, requested_model
                        )
                        if optimal_model and optimal_model != requested_model:
                            current_call_provider, current_call_model = self._normalize_provider_model_pair(
                                provider=provider,
                                model=optimal_model,
                                fallback_model=requested_model,
                            )
                            logger.info(
                                "TOOL-LOOP: Model upgraded for skill '%s' from '%s' to '%s'",
                                resolved_skill, requested_model, optimal_model
                            )
                            
                            # Log fallback_trigger for tool-loop model upgrade
                            import asyncio
                            from backend.services.logging.logger_core import log_event
                            from backend.data.schemas_logging import LogEventCreate
                            try:
                                asyncio.create_task(log_event(LogEventCreate(
                                    event_type="fallback_trigger",
                                    status="success",
                                    payload={
                                        "input_hash": str(hash(resolved_skill)),
                                        "output_summary": f"Model upgraded from {requested_model} to {optimal_model}",
                                        "error_code": None
                                    }
                                )))
                            except Exception as log_exc:
                                logger.error(f"Failed to log fallback_trigger: {log_exc}")
                            
                            break  # Only upgrade once based on first skill
            
            if not tool_calls:
                # --- IRON-GATE: Audit price_comparison synthesis before exiting ---
                _price_skill_used = any(
                    s in ("system.price_comparison", "price_comparison_tool")
                    for s in all_used_skills
                )
                if _price_skill_used and not _iron_gate_correction_done:
                    _ig_text = (
                        str(response.get("text") or "")
                        if isinstance(response, dict) else str(response or "")
                    )
                    _ig_violations = self._audit_price_response(_ig_text, _ig_budget)
                    if _ig_violations:
                        _iron_gate_correction_done = True
                        _correction = self._build_iron_gate_correction(
                            _ig_violations, _ig_budget,
                        )
                        gateway_kwargs["chat_history"].append({
                            "role": "system",
                            "content": _correction,
                        })
                        logger.warning(
                            "IRON-GATE: %d Verstöße erkannt → Correction-Turn. %s",
                            len(_ig_violations), _ig_violations,
                        )
                        current_iteration += 1
                        continue
                break
            had_tool_round = True

            # --- BUDGET-TRANSIT: Re-inject budget into price_comparison args ---
            _budget_info = gateway_kwargs.get("_user_budget_info")
            if _budget_info and isinstance(_budget_info, dict):
                _budget_raw = str(_budget_info.get("raw") or "")
                for tool_call in tool_calls:
                    _fn = tool_call.get("function") or {}
                    if _fn.get("name") == "price_comparison_tool" and _budget_raw:
                        _pc_args_raw = _fn.get("arguments") or "{}"
                        try:
                            _pc_args = json.loads(_pc_args_raw)
                        except Exception:
                            _pc_args = {}
                        _pn = str(_pc_args.get("product_name") or "")
                        if _pn and _budget_raw.lower() not in _pn.lower():
                            _pc_args["product_name"] = f"{_pn} {_budget_raw}"
                            _fn["arguments"] = json.dumps(_pc_args, ensure_ascii=False)
                            logger.info(
                                "BUDGET-TRANSIT: Re-injected budget '%s' into product_name: '%s'",
                                _budget_raw, _pc_args["product_name"],
                            )

            # 💎 HARD-LOOP-BREAKER: Prüfe auf Duplikat-Tool-Calls vor Ausführung
            _track_tool_call_fn = gateway_kwargs.get("_track_tool_call_fn")
            _duplicate_detected = False
            _duplicate_tool_name = ""
            if callable(_track_tool_call_fn):
                for tool_call in tool_calls:
                    function = tool_call.get("function") or {}
                    tool_name = function.get("name", "")
                    args_raw = function.get("arguments") or "{}"
                    try:
                        args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                    except Exception:
                        args = {}
                    is_duplicate = _track_tool_call_fn(tool_name, args)
                    if is_duplicate:
                        _duplicate_detected = True
                        _duplicate_tool_name = tool_name
                        # KRITISCH: Log auf ERROR-Level damit es IMMER sichtbar ist
                        logger.error(
                            "[HARD-LOOP-BREAKER] LOOP BLOCKED for tool: %s. "
                            "Force-exiting tool loop immediately!",
                            tool_name
                        )
                        break
            
            if _duplicate_detected:
                # KRITISCH: Soffortiger Exit - KEINE weitere Iteration, KEINE Tool-Ausführung
                force_loop_exit = True
                # Nutze die letzte Antwort oder erstelle eine finale Meldung
                final_response_text = (
                    "Das Dokument wurde erfolgreich erstellt. "
                    "Das PDF ist in Ihrer Dokumentenliste verfügbar."
                )
                if isinstance(response, dict) and response.get("text"):
                    # Behalte vorherigen Kontext bei wenn vorhanden
                    final_response_text = response["text"]
                
                logger.error(
                    "[HARD-LOOP-BREAKER] Emergency exit triggered. "
                    "Returning final response after blocking duplicate %s",
                    _duplicate_tool_name
                )
                
                return ExecutionResponse(
                    text=final_response_text,
                    tool_calls=latest_tool_calls,
                    is_agent_flow=False,
                    agent_payload={"blocked_duplicate": _duplicate_tool_name, "loop_broken": True}
                )

            for tool_call in tool_calls:
                function = tool_call.get("function") or {}
                if function.get("name") == "edit_pdf_text_in_place":
                    args_raw = function.get("arguments") or "{}"
                    try:
                        args = json.loads(args_raw)
                    except Exception:
                        logger.error(
                            "Error in orchestrator.execution_engine.run_tool_loop: invalid tool call args JSON",
                            exc_info=True,
                        )
                        args = {}
                    raw_mods = args.get("modifications")
                    if isinstance(raw_mods, list):
                        factcheck_modifications_detected = len(raw_mods) > 0
                    if not args.get("edit_mode"):
                        args["edit_mode"] = "rebuild_v1"
                    function["arguments"] = json.dumps(args, ensure_ascii=False)
                logger.error(
                    "💎 TOOL CALL ATTEMPT: %s with args %s",
                    function.get("name"),
                    function.get("arguments"),
                )

            # Extract context data for logging
            provider = str(gateway_kwargs.get("provider") or "").lower()
            model = str(gateway_kwargs.get("model") or "")
            session_id = str(gateway_kwargs.get("chat_id") or gateway_kwargs.get("session_id") or "")

            # Log tool start events
            for tc in tool_calls:
                fn = tc.get("function") or {}
                skill_name = str(fn.get("name") or "").strip()
                try:
                    await log_event(LogEventCreate(
                        session_id=session_id,
                        provider=provider,
                        model=model,
                        skill=skill_name,
                        event_type="tool_start",
                        payload={"arguments": fn.get("arguments")}
                    ))
                except Exception as log_exc:
                    logger.error(f"Failed to log tool_start event: {log_exc}")

            try:
                start_time = time.time()
                tool_results = await tool_executor.execute_tool_calls(
                    tool_calls,
                    bypass_policy=bypass_policy_this_turn,
                )
                latency_ms = int((time.time() - start_time) * 1000)
                if bypass_policy_this_turn:
                    bypass_policy_this_turn = False
            except Exception as exc:
                latency_ms = int((time.time() - start_time) * 1000)
                logger.error("Error in orchestrator.execution_engine.run_tool_loop: tool execution crash", exc_info=True)
                response = {"text": f"Die Korrektur ist fehlgeschlagen. Grund: {exc}"}
                
                # Log tool end events with error status
                for tc in tool_calls:
                    fn = tc.get("function") or {}
                    skill_name = str(fn.get("name") or "").strip()
                    try:
                        await log_event(LogEventCreate(
                            session_id=session_id,
                            provider=provider,
                            model=model,
                            skill=skill_name,
                            event_type="tool_end",
                            status="error",
                            payload={"error": str(exc)},
                            latency_ms=latency_ms
                        ))
                    except Exception as log_exc:
                        logger.error(f"Failed to log tool_end event: {log_exc}")
                break

            # Log tool end events with success status
            for tr in (tool_results or []):
                if isinstance(tr, dict):
                    skill_name = str(tr.get("name") or "").strip()
                    try:
                        await log_event(LogEventCreate(
                            session_id=session_id,
                            provider=provider,
                            model=model,
                            skill=skill_name,
                            event_type="tool_end",
                            status="success",
                            payload={"result": tr.get("content")},
                            latency_ms=latency_ms
                        ))
                    except Exception as log_exc:
                        logger.error(f"Failed to log tool_end event: {log_exc}")

            # 💎 PDF-SUCCESS-TRACKER: Tracken ob PDF bereits erfolgreich war für Loop-Break
            _pdf_already_succeeded = False
            # 💎 SELF-CORRECTION TRACKER: Speichere Tool-Status für Retry-Logik
            _kpi_tool_status = gateway_kwargs.get("_kpi_tool_status", {})
            _normalize_tool_args_fn = gateway_kwargs.get("_normalize_tool_args_fn")
            for _tr in (tool_results or []):
                logger.error("💎 TOOL CALL RESULT: %s", _tr)
                if isinstance(_tr, dict):
                    _skill_name = str(_tr.get("name") or "").strip()
                    if _skill_name and _skill_name not in all_used_skills:
                        all_used_skills.append(_skill_name)
                    # 💎 SELF-CORRECTION: Speichere Tool-Status für Retry-Logik
                    _raw_content = _tr.get("_raw_content") or _tr.get("content") or "{}"
                    try:
                        _parsed = json.loads(_raw_content) if isinstance(_raw_content, str) else dict(_raw_content or {})
                        _status = str(_parsed.get("status", "")).lower()
                        # Wenn Status "error" enthält, speichere für Self-Correction
                        if "error" in _status or "invalid" in _status:
                            # Extrahiere Tool-Name und Arguments aus dem Tool-Call
                            _tool_args = _tr.get("arguments", {})
                            if callable(_normalize_tool_args_fn):
                                _cache_key = _normalize_tool_args_fn(_skill_name, _tool_args)
                                _kpi_tool_status[_cache_key] = _status
                                logger.info(
                                    "[SELF-CORRECTION-TRACKER] Tool %s returned error status: %s. "
                                    "Storing for potential retry.",
                                    _skill_name, _status
                                )
                    except Exception:
                        pass
                    # Prüfe auf erfolgreiches PDF
                    if _skill_name.lower() == "system.create_pdf":
                        _raw = _tr.get("_raw_content") or _tr.get("content") or "{}"
                        try:
                            _parsed = json.loads(_raw)
                            if isinstance(_parsed, dict) and _parsed.get("status") == "ok":
                                _pdf_already_succeeded = True
                                logger.error(
                                    "[PDF-SUCCESS-TRACKER] PDF already created successfully. "
                                    "Will break loop after this iteration."
                                )
                        except Exception:
                            pass

            # 💎 AGGREGATOR FIX: Sammle alle Tool-Resultate im Buffer
            if tool_results:
                for tr in tool_results:
                    if isinstance(tr, dict):
                        results_buffer.append(tr)

            # 💎 REDUNDANT SYNTHESIS LOOP FIX: Check if any tool result is final response
            # If is_final_response=True, skip synthesis and use tool message directly
            if tool_results:
                for tr in tool_results:
                    if not isinstance(tr, dict):
                        continue
                    raw_content = tr.get("_raw_content") or tr.get("content") or "{}"
                    try:
                        parsed = json.loads(raw_content) if isinstance(raw_content, str) else dict(raw_content or {})
                    except Exception:
                        continue
                    if isinstance(parsed, dict) and parsed.get("is_final_response") is True:
                        final_message = parsed.get("message") or ""
                        logger.info(
                            "💎 REDUNDANT-SYNTHESIS-SKIP: Tool marked as final response. "
                            "Skipping synthesis, using tool message directly. Returning immediately."
                        )
                        # Build video modal request if applicable
                        derived_modal = self._build_video_modal_request_from_tool_results(results_buffer)
                        # IMMEDIATE RETURN to prevent any further synthesis
                        return ExecutionResponse(
                            text=final_message,
                            tool_calls=[],
                            is_agent_flow=False,
                            modal_request=derived_modal,
                            all_tool_results=results_buffer,
                        )

            if tool_results:
                user_prompt = str(gateway_kwargs.get("user_prompt") or "")
                pdf_requested = "pdf" in user_prompt.lower()
                image_done = any(
                    isinstance(tool_result, dict)
                    and str(tool_result.get("name") or "").strip().lower() == "system.generate_image"
                    for tool_result in tool_results
                )
                pdf_done = any(
                    isinstance(tool_result, dict)
                    and str(tool_result.get("name") or "").strip().lower() == "system.create_pdf"
                    for tool_result in tool_results
                )
                pdf_success = False
                for tool_result in tool_results:
                    if not isinstance(tool_result, dict):
                        continue
                    if str(tool_result.get("name") or "").strip().lower() != "system.create_pdf":
                        continue
                    raw_content = tool_result.get("_raw_content") or tool_result.get("content") or "{}"
                    try:
                        parsed_content = json.loads(raw_content)
                    except Exception:
                        continue
                    if isinstance(parsed_content, dict) and parsed_content.get("status") == "ok":
                        pdf_success = True
                        break
                if image_done and not pdf_requested:
                    logger.info("DIAMOND-STOP: Bild fertig, kein PDF angefordert -> Stop.")
                    return ExecutionResponse(text="Bild generiert.", tool_calls=[], is_agent_flow=False)
                if image_done and pdf_requested:
                    logger.info("DIAMOND-CONTINUE: Bild fertig, PDF-Erstellung folgt...")
                if pdf_requested and pdf_done and pdf_success:
                    logger.error("[PDF-SUCCESS-TRACKER] DIAMOND-STOP: PDF fertig -> Stoppe Tool-Loop.")
                    return ExecutionResponse(text="PDF erstellt.", tool_calls=[], is_agent_flow=False)
                
                # 💎 HARD-LOOP-BREAKER Fallback: Wenn PDF bereits erfolgreich war in diesem Turn
                if _pdf_already_succeeded and pdf_requested:
                    logger.error(
                        "[HARD-LOOP-BREAKER] EMERGENCY STOP: PDF was already created in this turn. "
                        "Breaking loop to prevent duplicate execution."
                    )
                    return ExecutionResponse(
                        text="PDF wurde erfolgreich erstellt.",
                        tool_calls=latest_tool_calls,
                        is_agent_flow=False,
                        agent_payload={"loop_broken_by": "pdf_success_tracker"}
                    )

            assistant_message = response.get("raw_assistant_response") or response.get("message")
            if assistant_message and isinstance(assistant_message, dict):
                content = assistant_message.get("content")
                if isinstance(content, str):
                    assistant_message["content"] = force_sanitize_links(content)
            if assistant_message:
                gateway_kwargs["chat_history"].append(assistant_message)
            for tool_result in tool_results:
                if isinstance(tool_result, dict):
                    content = tool_result.get("content")
                    if isinstance(content, str):
                        tool_result.setdefault("_raw_content", content)
                if isinstance(tool_result, dict):
                    content = tool_result.get("content")
                    if isinstance(content, str):
                        tool_result["content"] = force_sanitize_links(content)
                gateway_kwargs["chat_history"].append(tool_result)
            _sctx = gateway_kwargs.get("_suggestion_context")
            if isinstance(_sctx, dict) and isinstance(gateway_kwargs.get("chat_history"), list):
                from backend.services.orchestrator.suggestion_engine import (
                    SuggestionContextV1,
                    refresh_suggestion_system_message_after_tools,
                )

                refresh_suggestion_system_message_after_tools(
                    gateway_kwargs["chat_history"],
                    results_buffer,
                    cast(SuggestionContextV1, _sctx),
                )
            current_iteration += 1

            tool_failure_message = None
            websearch_failure_detected = False
            websearch_failure_text = ""
            video_search_failure_detected = False
            video_search_failure_text = ""
            for tool_result in tool_results:
                try:
                    raw_payload = tool_result.get("_raw_content") or tool_result.get("content", "{}")
                    parsed = json.loads(raw_payload)
                except Exception:
                    logger.error(
                        "Error in orchestrator.execution_engine.run_tool_loop: invalid tool result JSON",
                        exc_info=True,
                    )
                    response = {"text": "Die Werkzeugantwort konnte nicht verarbeitet werden (ungültiges JSON)."}
                    tool_failure_message = "Ungültige Tool-Antwort (JSON-Parsing fehlgeschlagen)."
                    break

                if isinstance(parsed, dict) and (
                    parsed.get("status") == "permission_required"
                    or (isinstance(parsed.get("error"), dict) and parsed.get("error", {}).get("code") == "USER_CONSENT_NEEDED")
                ):
                    pending_payload = {
                        "pending": True,
                        "blocked_skill_id": str((parsed.get("data") or {}).get("skill_id") or tool_result.get("_skill_id") or tool_result.get("name") or "").strip(),
                        "blocked_arguments": (parsed.get("data") or {}).get("arguments") or tool_result.get("_arguments_json") or {},
                        "resolved_name": str((parsed.get("data") or {}).get("resolved_name") or tool_result.get("name") or "").strip(),
                    }
                    set_policy_pending(chat_id, pending_payload)
                    continue
                if isinstance(parsed, dict) and parsed.get("error"):
                    tool_name = str(tool_result.get("name") or "").strip()
                    error_obj = parsed.get("error")
                    error_code = ""
                    error_message = ""
                    if isinstance(error_obj, dict):
                        error_code = str(error_obj.get("code") or "").strip()
                        error_message = str(error_obj.get("message") or "").strip()
                    else:
                        error_message = str(error_obj or "").strip()
                    if tool_name == "system.country_info" and error_code == "NOT_FOUND":
                        country_not_found_detected = True
                    if tool_name == "video.search":
                        video_search_failure_detected = True
                        video_search_failure_text = error_message or str(error_obj)
                    if tool_name in {"system.websearch", "websearch_wrapper"}:
                        lowered_error = f"{error_code} {error_message}".lower()
                        if any(
                            token in lowered_error
                            for token in (
                                "500",
                                "internal server error",
                                "openai native web search failed",
                                "server_error",
                            )
                        ):
                            websearch_failure_detected = True
                            websearch_failure_text = error_message or str(error_obj)
                    tool_failure_message = parsed.get("error")
                    break
                if isinstance(parsed, dict) and parsed.get("font_fallback") and not font_fallback_notice:
                    font_fallback_notice = parsed.get("font_fallback")
                maps_link = (
                    parsed.get("data", {}).get("maps_link")
                    if isinstance(parsed.get("data"), dict)
                    else None
                )
                if isinstance(maps_link, str) and maps_link:
                    canonical_maps_link = force_sanitize_links(maps_link)
                    logger.info("SANITIZER: Canonical maps link stored: %s", canonical_maps_link)
                elif not canonical_maps_link:
                    match = MAPS_LINK_REGEX.search(raw_payload)
                    if match:
                        canonical_maps_link = force_sanitize_links(match.group(1))
                        logger.info(
                            "SANITIZER: Canonical maps link extracted via regex: %s",
                            canonical_maps_link,
                        )

            if tool_failure_message:
                if video_search_failure_detected:
                    logger.error(
                        "VIDEO-SEARCH-FALLBACK: video.search failed (%s). Retrying with system.websearch in same turn.",
                        video_search_failure_text or "unknown error",
                    )
                    fallback_tool_calls: List[Dict[str, Any]] = []
                    for _tc in (tool_calls or []):
                        _fn = _tc.get("function") if isinstance(_tc, dict) else {}
                        _name = str((_fn or {}).get("name") or "").strip().lower()
                        if _name != "video.search":
                            continue
                        _args_raw = (_fn or {}).get("arguments") or "{}"
                        try:
                            _args = json.loads(_args_raw) if isinstance(_args_raw, str) else dict(_args_raw or {})
                        except Exception:
                            _args = {}
                        _query = str(_args.get("query") or gateway_kwargs.get("user_prompt") or "").strip()
                        _tc_copy = dict(_tc)
                        _fn_copy = dict(_fn or {})
                        _fn_copy["name"] = "system.websearch"
                        _fn_copy["arguments"] = json.dumps({"query": _query}, ensure_ascii=False)
                        _tc_copy["function"] = _fn_copy
                        fallback_tool_calls.append(_tc_copy)
                    if fallback_tool_calls:
                        try:
                            fallback_results = await tool_executor.execute_tool_calls(
                                fallback_tool_calls,
                                bypass_policy=bypass_policy_this_turn,
                            )
                        except Exception:
                            logger.error(
                                "VIDEO-SEARCH-FALLBACK: system.websearch fallback crashed.",
                                exc_info=True,
                            )
                            fallback_results = []
                        if fallback_results:
                            non_video_results = [
                                tr
                                for tr in (tool_results or [])
                                if str(tr.get("name") or "").strip().lower() != "video.search"
                            ]
                            tool_results = non_video_results + [tr for tr in fallback_results if isinstance(tr, dict)]
                            tool_failure_message = None
                            logger.error(
                                "VIDEO-SEARCH-FALLBACK: system.websearch returned %d result(s). Continuing loop.",
                                len(fallback_results),
                            )
                if (
                    not websearch_fallback_attempted
                    and websearch_failure_detected
                    and str(gateway_kwargs.get("provider") or "").strip().lower() == "openai"
                ):
                    websearch_fallback_attempted = True
                    logger.error(
                        "WEBSEARCH-FALLBACK: OpenAI websearch failed (%s). Retrying tool call via Gemini.",
                        websearch_failure_text or "unknown error",
                    )
                    fallback_tool_calls: List[Dict[str, Any]] = []
                    for _tc in (tool_calls or []):
                        _fn = _tc.get("function") if isinstance(_tc, dict) else {}
                        _name = str((_fn or {}).get("name") or "").strip().lower()
                        if _name not in {"system.websearch", "websearch_wrapper"}:
                            continue
                        _args_raw = (_fn or {}).get("arguments") or "{}"
                        try:
                            _args = json.loads(_args_raw) if isinstance(_args_raw, str) else dict(_args_raw or {})
                        except Exception:
                            _args = {}
                        _args["provider"] = "gemini"
                        _args["model"] = "gemini-3-flash-preview"
                        _tc_copy = dict(_tc)
                        _fn_copy = dict(_fn or {})
                        _fn_copy["arguments"] = json.dumps(_args, ensure_ascii=False)
                        _tc_copy["function"] = _fn_copy
                        fallback_tool_calls.append(_tc_copy)

                    if fallback_tool_calls:
                        prev_force_provider = tool_executor.additional_context.get("websearch_fallback_provider")
                        tool_executor.additional_context["websearch_fallback_provider"] = "gemini"
                        try:
                            fallback_results = await tool_executor.execute_tool_calls(
                                fallback_tool_calls,
                                bypass_policy=bypass_policy_this_turn,
                            )
                        except Exception:
                            logger.error(
                                "WEBSEARCH-FALLBACK: Gemini retry crashed during tool execution.",
                                exc_info=True,
                            )
                            fallback_results = []
                        finally:
                            if prev_force_provider is None:
                                tool_executor.additional_context.pop("websearch_fallback_provider", None)
                            else:
                                tool_executor.additional_context["websearch_fallback_provider"] = prev_force_provider

                        if fallback_results:
                            # Replace failed websearch entries with fallback results.
                            non_websearch_results = [
                                tr
                                for tr in (tool_results or [])
                                if str(tr.get("name") or "").strip().lower()
                                not in {"system.websearch", "websearch_wrapper"}
                            ]
                            tool_results = non_websearch_results + [tr for tr in fallback_results if isinstance(tr, dict)]
                            tool_failure_message = None
                            logger.error(
                                "WEBSEARCH-FALLBACK: Gemini retry returned %d result(s). Continuing loop.",
                                len(fallback_results),
                            )

                if tool_failure_message:
                    _err = tool_failure_message
                    if isinstance(_err, dict):
                        _err = str(_err.get("message") or _err.get("code") or _err)
                    else:
                        _err = str(_err)
                    response = {"text": f"Die Aktion konnte nicht abgeschlossen werden: {_err}"}
                    break

        # 💎 WEBSEARCH COST PERSISTENCE: Persistiere Websearch-Kosten aus results_buffer
        # Runs after the while loop so it catches both OpenAI internal-tool-loop results
        # (_internal_tool_results) and direct outer-loop tool results from other providers.
        if results_buffer and self.db is not None:
            _ws_skill_names = {"system.websearch", "websearch_wrapper"}
            _ws_persist_count = 0
            for _rb_tr in results_buffer:
                if not isinstance(_rb_tr, dict):
                    continue
                _rb_name = (
                    str(_rb_tr.get("skill_id") or _rb_tr.get("_skill_id") or _rb_tr.get("name") or "")
                    .strip()
                    .lower()
                )
                if _rb_name in _ws_skill_names:
                    _ws_persist_count += 1
            if _ws_persist_count > 0:
                try:
                    from backend.services.cost_calculator import calculate_cost
                    from backend.services.cost_service import create_cost_entry
                    _ws_usage, _ws_cost = calculate_cost("websearch", {"query_count": 1})
                    _ws_cost_per_query = _ws_cost.get("total_cost", 0.0) if isinstance(_ws_cost, dict) else 0.0
                    if _ws_cost_per_query <= 0:
                        _ws_cost_per_query = 0.009009
                    for _i in range(_ws_persist_count):
                        create_cost_entry(
                            db=self.db,
                            amount=_ws_cost_per_query,
                            model="websearch",
                            provider=str(gateway_kwargs.get("provider") or "openai"),
                            source_type="websearch",
                            context_details="query_count=1",
                        )
                    logger.info(
                        "WEBSEARCH-COST-PERSIST: Saved %d websearch entries @ %.6f€ each",
                        _ws_persist_count, _ws_cost_per_query
                    )
                except Exception:
                    logger.warning("WEBSEARCH-COST-PERSIST: Failed to save websearch costs", exc_info=True)

        if response is None:
            response = {"text": fallback_summary}
        if isinstance(response, dict) and not response.get("modal_request"):
            derived_modal = self._build_video_modal_request_from_tool_results(results_buffer)
            if derived_modal:
                response["modal_request"] = derived_modal

        text_value = fallback_summary
        if isinstance(response, dict):
            text_value = str(response.get("text") or fallback_summary)
        else:
            text_value = str(response or fallback_summary)

        text_value = force_sanitize_links(text_value)

        # --- IRON-GATE: Post-Loop Safety-Net ---
        # If the correction-turn also failed, hard-replace the output.
        _price_skill_used_final = any(
            s in ("system.price_comparison", "price_comparison_tool")
            for s in all_used_skills
        )
        if _price_skill_used_final:
            _ig_final_violations = self._audit_price_response(text_value, _ig_budget)
            if _ig_final_violations:
                logger.error(
                    "IRON-GATE FINAL: Antwort auch nach Correction nicht compliant. "
                    "%d Verstöße: %s — Ersetze mit sicherem Fallback.",
                    len(_ig_final_violations), _ig_final_violations,
                )
                _budget_hint = (
                    f" unter {_ig_budget:.0f}€" if _ig_budget is not None else ""
                )
                # Versuche, Daten aus den Tool-Resultaten zu extrahieren
                _ig_fallback_lines = [
                    f"Ich habe Preise{_budget_hint} auf idealo.de und geizhals.de gesucht, "
                    "konnte aber keine regelkonforme Zusammenfassung erstellen.",
                    "",
                    "Bitte prüfe die Ergebnisse direkt:",
                ]
                _ig_fallback_links_added = False
                for _tr in results_buffer:
                    _tr_content = _tr.get("_raw_content") or _tr.get("content") or "{}"
                    try:
                        _tr_parsed = json.loads(_tr_content)
                        _tr_data = _tr_parsed.get("data") or _tr_parsed
                        _tr_query = _tr_data.get("query") or ""
                        if _tr_query:
                            _ig_fallback_lines.append(
                                f"- [**{_tr_query}** auf idealo.de]"
                                f"(https://www.idealo.de/preisvergleich/MainSearchProductCategory.html"
                                f"?q={_tr_query.replace(' ', '+')})"
                            )
                            _ig_fallback_links_added = True
                    except Exception:
                        continue
                if not _ig_fallback_links_added:
                    _user_query = str(gateway_kwargs.get("user_prompt") or "Produkt")
                    _ig_fallback_lines.append(
                        f"- [**Suche auf idealo.de**]"
                        f"(https://www.idealo.de/preisvergleich/MainSearchProductCategory.html"
                        f"?q={_user_query[:80].replace(' ', '+')})"
                    )
                text_value = "\n".join(_ig_fallback_lines)

        # --- DETERMINISTIC RENDERER ENFORCEMENT ---
        # If any used skill has deterministic_renderer=true, verify output is human text (not JSON)
        if all_used_skills:
            for skill_id in all_used_skills:
                if tool_manager.get_deterministic_renderer(skill_id):
                    # Check for JSON markers in the output
                    if "{" in text_value and "}" in text_value:
                        logger.error(
                            "DETERMINISTIC RENDERER VIOLATION: Skill '%s' has deterministic_renderer=true "
                            "but output contains JSON braces. Output truncated: %s",
                            skill_id, text_value[:200]
                        )
                        # Force fallback error message instead of raw JSON
                        text_value = (
                            f"[RENDERER-FEHLER] Das Skill '{skill_id}' hat unformatiertes JSON zurückgegeben "
                            f"statt menschlichen Text. Bitte wiederhole die Anfrage."
                        )
                    break  # Only check first skill with deterministic_renderer

        provider = gateway_kwargs.get("provider") if isinstance(gateway_kwargs, dict) else None
        if provider == "ollama" and (not text_value or not str(text_value).strip()):
            text_value = (
                "Ich konnte die Route leider nicht berechnen, bitte versuche es mit einer anderen Zielangabe."
            )

        if any(keyword in text_value for keyword in ("Short URL", "Kurzlink")):
            if canonical_maps_link:
                text_value = (
                    f"Hier ist der Google Maps Link zur Route: {canonical_maps_link}."
                )
            else:
                text_value = (
                    "Die automatisierte Antwort enthielt erwartungsgemäß keinen Kurzlink mehr."
                    " Bitte nutze den Skill system.routing oder setze eine vollständige Google-Maps-URL ein."
                )

        if country_not_found_detected:
            logger.info(
                "COUNTRY-GUARD (ExecutionEngine): country_info returned NOT_FOUND. Marking response to skip fact extraction."
            )
            if isinstance(response, dict):
                response["skip_fact_extraction"] = True

        tool_loop_agent_payload = None
        if all_used_skills:
            tool_loop_agent_payload = {
                "name": "Tool Loop",
                "required_skills": list(all_used_skills),
                "mode": "tool_loop",
            }
        if all_used_skills:
            logger.info("TOOL_LOOP: Skills executed in legacy path: %s", all_used_skills)

        text_value = append_tool_attributions_from_tools(text_value, results_buffer)

        return ExecutionResponse(
            text=text_value,
            agent_payload=tool_loop_agent_payload,
            tool_calls=latest_tool_calls,
            is_agent_flow=bool(tool_loop_agent_payload),
            raw_response=response,
            ui_command=latest_ui_command,
            font_fallback_notice=font_fallback_notice,
            factcheck_modifications_detected=factcheck_modifications_detected,
            # 💎 AGGREGATOR FIX: Alle gesammelten Tool-Resultate zurückgeben
            all_tool_results=results_buffer,
            # 💎 COST-AGGREGATION FIX: Summierte Usage/Cost zurückgeben
            usage={
                "input_tokens": aggregated_tokens_input,
                "output_tokens": aggregated_tokens_output,
                "total_tokens": aggregated_tokens_input + aggregated_tokens_output
            },
            cost={"total_cost": aggregated_total_cost}
        )

    async def run_tool_loop_stream(
        self,
        *,
        orchestrator_context: OrchestratorContext,
        tool_executor,
        gateway_kwargs: Dict[str, Any],
        fallback_summary: str,
        current_limit: int,
        bypass_policy_this_turn: bool,
        set_policy_pending,
        chat_id: Optional[int],
        agent_flow_error: Optional[Dict[str, Any]] = None,
        result_holder: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[StreamEvent]:
        """Stream provider chunks: text_delta/usage sofort; tool_delta gepuffert; tool_start/tool_end bei Ausführung."""
        # 💎 CU-4: Sende pending status_update Event (wenn vorhanden)
        # Dies wurde im chat_orchestrator._execute_generation gesetzt
        pending_status_update = gateway_kwargs.get("_pending_status_update")
        if pending_status_update:
            logger.info("[CU-4] Yielding pending status_update event")
            yield pending_status_update

        current_iteration = 0
        response: Any = None
        latest_ui_command = None
        font_fallback_notice = None
        factcheck_modifications_detected = None
        latest_tool_calls: List[Dict[str, Any]] = []
        all_used_skills: List[str] = []
        results_buffer: List[Dict[str, Any]] = []
        aggregated_tokens_input = 0
        aggregated_tokens_output = 0
        aggregated_total_cost = 0.0
        country_not_found_detected = False

        gateway_kwargs = dict(gateway_kwargs)
        gateway_kwargs.pop("reason_and_respond_fn", None)
        user_selected_provider = str(gateway_kwargs.get("provider") or "").strip().lower()
        user_selected_model = str(gateway_kwargs.get("model") or "").strip()
        user_selected_provider, user_selected_model = self._normalize_provider_model_pair(
            provider=user_selected_provider,
            model=user_selected_model,
            fallback_model=user_selected_model,
        )
        current_call_provider = user_selected_provider
        current_call_model = user_selected_model
        had_tool_round = False
        if not isinstance(gateway_kwargs.get("chat_history"), list):
            gateway_kwargs["chat_history"] = [dict(item) for item in orchestrator_context.history]

        if agent_flow_error:
            gateway_kwargs["chat_history"].append(
                {
                    "role": "system",
                    "content": (
                        "AGENT-FALLBACK: Der Agent-Flow ist fehlgeschlagen "
                        f"(code={agent_flow_error['code']}). Führe den Standard-Lifecycle robust weiter."
                    ),
                }
            )

        _allow_moa_hard_lock = bool(gateway_kwargs.get("_allow_moa_hard_lock"))
        _pre_skill_ids = gateway_kwargs.get("allowed_skill_ids") or []
        _pre_provider = current_call_provider or gateway_kwargs.get("provider") or ""
        _pre_base_model = current_call_model or gateway_kwargs.get("model") or ""
        if _allow_moa_hard_lock and _pre_skill_ids and _pre_provider:
            for _sid in _pre_skill_ids:
                _resolved = self._resolve_model_for_skill(_sid, _pre_provider, _pre_base_model)
                if _resolved and _resolved != _pre_base_model:
                    logger.warning(
                        "🔥 MOA-HARD-LOCK (stream): Overriding base model '%s' with Skill-Model '%s'.",
                        _pre_base_model,
                        _resolved,
                    )
                    current_call_provider, current_call_model = self._normalize_provider_model_pair(
                        provider=_pre_provider,
                        model=_resolved,
                        fallback_model=_pre_base_model,
                    )
                    # 🔐 AUTH-ISOLATION (stream MOA-HARD-LOCK)
                    if current_call_provider and _pre_provider and current_call_provider != _pre_provider:
                        fresh_key = _reload_api_key_for_provider(current_call_provider)
                        if fresh_key:
                            gateway_kwargs["api_key"] = fresh_key
                            logger.warning(
                                "AUTH-ISOLATION (stream MOA): Switched key for '%s'",
                                current_call_provider,
                            )
                        else:
                            logger.error(
                                "AUTH-ISOLATION (stream MOA): No key for '%s', aborting switch.",
                                current_call_provider,
                            )
                            current_call_provider = _pre_provider
                            current_call_model = _pre_base_model
                    break

        stream_fatal = False
        while current_iteration < current_limit and not stream_fatal:
            if had_tool_round and user_selected_model:
                current_call_provider = user_selected_provider
                current_call_model = user_selected_model
            current_call_provider, current_call_model = self._normalize_provider_model_pair(
                provider=current_call_provider or gateway_kwargs.get("provider"),
                model=current_call_model,
                fallback_model=user_selected_model,
            )
            prompt_cache_decision = clone_decision_for_route(
                decision_from_gateway_kwargs(gateway_kwargs),
                provider=current_call_provider,
                model=current_call_model or user_selected_model,
            )
            if prompt_cache_decision is not None:
                gateway_kwargs["_prompt_cache_decision"] = prompt_cache_decision
            # 🔐 AUTH-ISOLATION (stream loop): Key-Refresh bei Provider-Switch
            _stream_orig_provider = str(gateway_kwargs.get("provider") or "").strip().lower()
            if current_call_provider and _stream_orig_provider and current_call_provider != _stream_orig_provider:
                _stream_fresh_key = _reload_api_key_for_provider(current_call_provider)
                if _stream_fresh_key:
                    gateway_kwargs["api_key"] = _stream_fresh_key
                    logger.warning(
                        "AUTH-ISOLATION (stream): Switched key for '%s'",
                        current_call_provider,
                    )
                else:
                    logger.error(
                        "AUTH-ISOLATION (stream): No key for '%s', aborting switch.",
                        current_call_provider,
                    )
                    current_call_provider = _stream_orig_provider
                    current_call_model = user_selected_model
            gateway_kwargs["provider"] = current_call_provider
            gateway_kwargs["model"] = current_call_model or user_selected_model
            provider_key = str(current_call_provider or gateway_kwargs.get("provider") or "").lower()
            tools_llm = _stream_tools_list_for_llm(gateway_kwargs)
            messages = list(gateway_kwargs.get("chat_history") or [])
            if provider_key in ("gemini", "google"):
                from backend.services.orchestrator.execution_dispatcher import _normalize_gemini_tool_messages

                messages = _normalize_gemini_tool_messages(messages)
            gateway_kwargs["chat_history"] = messages

            round_text_parts: List[str] = []
            openai_acc: Dict[int, Dict[str, Any]] = {}
            gemini_calls: List[Dict[str, Any]] = []

            # 💎 AUDIT-LOOP-FORCED-START (stream):
            # Replace old fake-assistant-message injection (OpenAI 400) with a clean
            # initial-loop-state: synthesize tool_calls and skip the LLM stream round.
            _forced_tool_args_stream = (
                gateway_kwargs.get("forced_tool_args") if current_iteration == 0 else None
            )
            _forced_tool_name_stream = (
                str(gateway_kwargs.get("force_tool_name") or "").strip() if current_iteration == 0 else ""
            )
            _forced_tool_calls_stream: Optional[List[Dict[str, Any]]] = None
            if _forced_tool_args_stream and _forced_tool_name_stream:
                _normalized_name_stream = (
                    _forced_tool_name_stream.replace(".", "_")
                    if provider_key == "openai"
                    else _forced_tool_name_stream
                )
                _synth_call_id_stream = f"call_{uuid.uuid4().hex[:16]}"
                _forced_tool_calls_stream = [
                    {
                        "id": _synth_call_id_stream,
                        "type": "function",
                        "function": {
                            "name": _normalized_name_stream,
                            "arguments": json.dumps(_forced_tool_args_stream, ensure_ascii=False),
                        },
                    }
                ]
                logger.info(
                    "💎 AUDIT-LOOP-FORCED-START (stream): Skipping LLM stream on iteration %d; "
                    "injecting pre-filled tool-call for %s (normalized: %s, provider=%s)",
                    current_iteration,
                    _forced_tool_name_stream,
                    _normalized_name_stream,
                    provider_key,
                )
                # Consume forced args so subsequent iterations run the normal LLM flow.
                gateway_kwargs.pop("forced_tool_args", None)
                gateway_kwargs.pop("force_tool_name", None)
                gateway_kwargs.pop("forced_tool", None)

            # 💎 VIDEO-FORCE: Only force tool_choice on first iteration to prevent infinite loops
            _active_force_tool = None
            if current_iteration == 0 and _forced_tool_calls_stream is None:
                _active_force_tool = str(gateway_kwargs.get("force_tool_name") or "").strip() or None
                logger.info("💎 VIDEO-FORCE (stream): gateway_kwargs.get('force_tool_name')=%s, extracted _active_force_tool=%s", gateway_kwargs.get("force_tool_name"), _active_force_tool)
                if _active_force_tool:
                    logger.info("💎 VIDEO-FORCE (stream): Forcing tool_choice=%s on iteration %d", _active_force_tool, current_iteration)
                    logger.info("💎 VIDEO-FORCE (stream): Passing force_tool_name=%s to _async_iter_llm_stream", _active_force_tool)

            _wf_ref = gateway_kwargs.get("_workflow")
            if _wf_ref is not None:
                try:
                    _wf_ref.gemini_stream_raw_model_parts = []
                except Exception:
                    pass

            if _forced_tool_calls_stream is None:
                try:
                    async for ev in _async_iter_llm_stream(gateway_kwargs, tools_llm, force_tool_name=_active_force_tool):
                        if ev.type == "text_delta":
                            if ev.content:
                                round_text_parts.append(str(ev.content))
                            yield ev
                        elif ev.type == "tool_delta":
                            if provider_key in ("gemini", "google"):
                                c = ev.content if isinstance(ev.content, dict) else {}
                                if c.get("name"):
                                    gemini_calls.append(_gemini_tool_delta_to_call(c))
                            else:
                                frag = ev.content if isinstance(ev.content, dict) else {}
                                _stream_merge_openai_tool_delta(openai_acc, frag)
                        elif ev.type == "usage":
                            prompt_cache_decision = decision_from_gateway_kwargs(gateway_kwargs)
                            if prompt_cache_decision is not None and isinstance(ev.content, dict):
                                u_blob_for_cache = dict(ev.content)
                                u_blob_for_cache["usage"] = merge_decision_into_usage(
                                    u_blob_for_cache.get("usage") or {},
                                    prompt_cache_decision,
                                )
                                ev = StreamEvent(type=ev.type, content=u_blob_for_cache, metadata=ev.metadata)
                            yield ev
                            u_blob = ev.content if isinstance(ev.content, dict) else {}
                            u = u_blob.get("usage") or {}
                            cst = u_blob.get("cost") or {}
                            aggregated_tokens_input += int(u.get("input_tokens") or u.get("prompt_tokens") or 0)
                            aggregated_tokens_output += int(u.get("output_tokens") or u.get("completion_tokens") or 0)
                            aggregated_total_cost += float(cst.get("total_cost") or 0.0)
                            if float(cst.get("total_cost") or 0) > 0 and self.db is not None:
                                try:
                                    from backend.services.cost_service import create_cost_entry
                                    _stream_tokens_saved = int(
                                        (prompt_cache_decision.estimated_tokens_saved if prompt_cache_decision is not None else 0) or 0
                                    )
                                    create_cost_entry(
                                        db=self.db,
                                        amount=float(cst.get("total_cost") or 0.0),
                                        model=str(current_call_model or user_selected_model or "unknown"),
                                        provider=str(current_call_provider or gateway_kwargs.get("provider") or "unknown"),
                                        source_type="conversation",
                                        input_tokens=int(u.get("input_tokens") or u.get("prompt_tokens") or 0),
                                        output_tokens=int(u.get("output_tokens") or u.get("completion_tokens") or 0),
                                        tokens_saved=_stream_tokens_saved,
                                    )
                                    # 💎 COST-PERSISTENCE FIX: Explizites db.commit() nach create_cost_entry (Streaming)
                                    self.db.commit()
                                except Exception:
                                    logger.warning("COST-PERSIST (stream): iteration save failed", exc_info=True)
                        elif ev.type == "error":
                            yield ev
                            response = {"text": fallback_summary}
                            stream_fatal = True
                            break
                        elif ev.type in ("finish", "done"):
                            if ev.type == "done":
                                pass
                    if stream_fatal:
                        break
                except Exception:
                    logger.error("run_tool_loop_stream: provider stream crashed", exc_info=True)
                    yield StreamEvent(type="error", content=fallback_summary, metadata={"fatal": True})
                    response = {"text": fallback_summary}
                    break

            if _forced_tool_calls_stream is not None:
                tool_calls = list(_forced_tool_calls_stream)
            else:
                tool_calls = gemini_calls if provider_key in ("gemini", "google") else _stream_finalize_openai_tool_slots(openai_acc)
            round_text = "".join(round_text_parts)

            if tool_calls and current_iteration == 0:
                for tool_call in tool_calls:
                    function = tool_call.get("function") or {}
                    tool_name = function.get("name", "")
                    if tool_name:
                        resolved_skill = tool_manager.get_skill_id(tool_name)
                        prov = current_call_provider or gateway_kwargs.get("provider", "")
                        requested_model = current_call_model or user_selected_model
                        optimal_model = self._resolve_model_for_skill(resolved_skill, prov, requested_model)
                        if optimal_model and optimal_model != requested_model:
                            current_call_provider, current_call_model = self._normalize_provider_model_pair(
                                provider=prov,
                                model=optimal_model,
                                fallback_model=requested_model,
                            )
                            logger.info(
                                "TOOL-LOOP-STREAM: Model upgraded for skill '%s' from '%s' to '%s'",
                                resolved_skill,
                                requested_model,
                                optimal_model,
                            )
                            break

            latest_tool_calls = list(tool_calls) if isinstance(tool_calls, list) else []

            if not tool_calls:
                text_value = round_text if round_text.strip() else fallback_summary
                text_value = force_sanitize_links(text_value)
                response = {"text": text_value, "usage": {}, "cost": {}}
                break
            had_tool_round = True

            _track_tool_call_fn = gateway_kwargs.get("_track_tool_call_fn")
            _duplicate_detected = False
            _duplicate_tool_name = ""
            if callable(_track_tool_call_fn):
                for tool_call in tool_calls:
                    function = tool_call.get("function") or {}
                    tool_name = function.get("name", "")
                    args_raw = function.get("arguments") or "{}"
                    try:
                        args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                    except Exception:
                        args = {}
                    if _track_tool_call_fn(tool_name, args):
                        _duplicate_detected = True
                        _duplicate_tool_name = tool_name
                        logger.error("[HARD-LOOP-BREAKER] (stream) duplicate blocked: %s", tool_name)
                        break

            if _duplicate_detected:
                final_response_text = round_text.strip() or (
                    "Das Dokument wurde erfolgreich erstellt. "
                    "Das PDF ist in Ihrer Dokumentenliste verfügbar."
                )
                er = ExecutionResponse(
                    text=final_response_text,
                    tool_calls=latest_tool_calls,
                    is_agent_flow=False,
                    agent_payload={"blocked_duplicate": _duplicate_tool_name, "loop_broken": True},
                    raw_response={"text": final_response_text, "blocked_duplicate": _duplicate_tool_name},
                    usage={
                        "input_tokens": aggregated_tokens_input,
                        "output_tokens": aggregated_tokens_output,
                        "total_tokens": aggregated_tokens_input + aggregated_tokens_output,
                    },
                    cost={"total_cost": aggregated_total_cost},
                    all_tool_results=results_buffer,
                )
                if result_holder is not None:
                    result_holder["execution_result"] = er
                yield StreamEvent(
                    type="stream_complete",
                    content={"text": er.text},
                    metadata={"blocked_duplicate": _duplicate_tool_name},
                )
                return

            _budget_info = gateway_kwargs.get("_user_budget_info")
            if _budget_info and isinstance(_budget_info, dict):
                _budget_raw = str(_budget_info.get("raw") or "")
                for tool_call in tool_calls:
                    _fn = tool_call.get("function") or {}
                    if _fn.get("name") == "price_comparison_tool" and _budget_raw:
                        _pc_args_raw = _fn.get("arguments") or "{}"
                        try:
                            _pc_args = json.loads(_pc_args_raw)
                        except Exception:
                            _pc_args = {}
                        _pn = str(_pc_args.get("product_name") or "")
                        if _pn and _budget_raw.lower() not in _pn.lower():
                            _pc_args["product_name"] = f"{_pn} {_budget_raw}"
                            _fn["arguments"] = json.dumps(_pc_args, ensure_ascii=False)

            for tool_call in tool_calls:
                function = tool_call.get("function") or {}
                if function.get("name") == "edit_pdf_text_in_place":
                    args_raw = function.get("arguments") or "{}"
                    try:
                        args = json.loads(args_raw)
                    except Exception:
                        args = {}
                    raw_mods = args.get("modifications")
                    if isinstance(raw_mods, list):
                        factcheck_modifications_detected = len(raw_mods) > 0
                    if not args.get("edit_mode"):
                        args["edit_mode"] = "rebuild_v1"
                    function["arguments"] = json.dumps(args, ensure_ascii=False)
                logger.error(
                    "💎 TOOL CALL ATTEMPT: %s with args %s",
                    function.get("name"),
                    function.get("arguments"),
                )

            for tc in tool_calls:
                fn = tc.get("function") or {}
                yield StreamEvent(
                    type="tool_start",
                    content=None,
                    metadata={"name": fn.get("name"), "id": tc.get("id")},
                )

            # Extract context data for logging
            provider = str(gateway_kwargs.get("provider") or "").lower()
            model = str(gateway_kwargs.get("model") or "")
            session_id = str(gateway_kwargs.get("chat_id") or gateway_kwargs.get("session_id") or "")

            # Log tool start events (streaming)
            for tc in tool_calls:
                fn = tc.get("function") or {}
                skill_name = str(fn.get("name") or "").strip()
                try:
                    await log_event(LogEventCreate(
                        session_id=session_id,
                        provider=provider,
                        model=model,
                        skill=skill_name,
                        event_type="tool_start",
                        payload={"arguments": fn.get("arguments")}
                    ))
                except Exception as log_exc:
                    logger.error(f"Failed to log tool_start event: {log_exc}")

            tool_results: List[Dict[str, Any]] = []
            try:
                start_time = time.time()
                tool_results = await tool_executor.execute_tool_calls(
                    tool_calls,
                    bypass_policy=bypass_policy_this_turn,
                )
                latency_ms = int((time.time() - start_time) * 1000)
                tool_results = tool_results or []
                if bypass_policy_this_turn:
                    bypass_policy_this_turn = False
            except Exception as exc:
                latency_ms = int((time.time() - start_time) * 1000)
                logger.error("run_tool_loop_stream: tool execution crash", exc_info=True)
                response = {"text": f"Die Korrektur ist fehlgeschlagen. Grund: {exc}"}
                
                # Log tool end events with error status (streaming)
                for tc in tool_calls:
                    fn = tc.get("function") or {}
                    skill_name = str(fn.get("name") or "").strip()
                    try:
                        await log_event(LogEventCreate(
                            session_id=session_id,
                            provider=provider,
                            model=model,
                            skill=skill_name,
                            event_type="tool_end",
                            status="error",
                            payload={"error": str(exc)},
                            latency_ms=latency_ms
                        ))
                    except Exception as log_exc:
                        logger.error(f"Failed to log tool_end event: {log_exc}")
                break

            for tc in tool_calls:
                fn = tc.get("function") or {}
                yield StreamEvent(
                    type="tool_end",
                    content={"ok": True},
                    metadata={"name": fn.get("name"), "id": tc.get("id")},
                )

            # Log tool end events with success status (streaming)
            for tr in tool_results:
                if isinstance(tr, dict):
                    skill_name = str(tr.get("name") or "").strip()
                    try:
                        await log_event(LogEventCreate(
                            session_id=session_id,
                            provider=provider,
                            model=model,
                            skill=skill_name,
                            event_type="tool_end",
                            status="success",
                            payload={"result": tr.get("content")},
                            latency_ms=latency_ms
                        ))
                    except Exception as log_exc:
                        logger.error(f"Failed to log tool_end event: {log_exc}")

            if tool_results:
                # 💎 SELF-CORRECTION TRACKER: Speichere Tool-Status für Retry-Logik (Stream)
                _kpi_tool_status = gateway_kwargs.get("_kpi_tool_status", {})
                _normalize_tool_args_fn = gateway_kwargs.get("_normalize_tool_args_fn")
                for tr in tool_results:
                    logger.error("💎 TOOL CALL RESULT: %s", tr)
                    if isinstance(tr, dict):
                        results_buffer.append(tr)
                        _sn = str(tr.get("name") or "").strip()
                        if _sn and _sn not in all_used_skills:
                            all_used_skills.append(_sn)
                        # 💎 SELF-CORRECTION: Speichere Tool-Status für Retry-Logik
                        _raw_content = tr.get("_raw_content") or tr.get("content", "{}")
                        try:
                            _parsed = json.loads(_raw_content) if isinstance(_raw_content, str) else dict(_raw_content or {})
                            _status = str(_parsed.get("status", "")).lower()
                            # Wenn Status "error" enthält, speichere für Self-Correction
                            if "error" in _status or "invalid" in _status:
                                # Extrahiere Tool-Name und Arguments aus dem Tool-Call
                                _tool_args = tr.get("arguments", {})
                                if callable(_normalize_tool_args_fn):
                                    _cache_key = _normalize_tool_args_fn(_sn, _tool_args)
                                    _kpi_tool_status[_cache_key] = _status
                                    logger.info(
                                        "[SELF-CORRECTION-TRACKER] (stream) Tool %s returned error status: %s. "
                                        "Storing for potential retry.",
                                        _sn, _status
                                    )
                        except Exception:
                            pass
                        # 💎 PATH-SENTINEL: Emit permission_required to frontend so consent modal opens
                        try:
                            _raw = tr.get("_raw_content") or tr.get("content", "{}")
                            _parsed = json.loads(_raw) if isinstance(_raw, str) else dict(_raw or {})
                            if isinstance(_parsed, dict) and _parsed.get("status") == "permission_required":
                                yield StreamEvent(
                                    type="tool_result",
                                    content={"result": _parsed},
                                    metadata={"name": _sn, "tool_call_id": tr.get("tool_call_id")},
                                )
                        except Exception:
                            pass
                        # 💎 VIDEO-LIST-METADATA: Extrahiere video.search List-Mode Daten für Frontend
                        if _sn == "video.search":
                            try:
                                raw_payload = tr.get("_raw_content") or tr.get("content", "{}")
                                parsed = json.loads(raw_payload) if isinstance(raw_payload, str) else dict(raw_payload or {})
                                if isinstance(parsed, dict) and parsed.get("status") == "ok":
                                    data = parsed.get("data") if isinstance(parsed.get("data"), dict) else {}
                                    mode = str(data.get("mode") or "").strip().lower()
                                    if mode == "list" and isinstance(data.get("videos"), list):
                                        yield StreamEvent(
                                            type="metadata",
                                            content={
                                                "videos": data.get("videos"),
                                                "count": data.get("count", 0),
                                                "mode": "list",
                                                "query": data.get("query")
                                            },
                                            metadata={"source": "video.search.list_mode"}
                                        )
                                        logger.info("💎 VIDEO-LIST-METADATA: Sent %d videos to frontend", len(data.get("videos", [])))
                            except Exception:
                                logger.warning("💎 VIDEO-LIST-METADATA: Failed to extract video list data", exc_info=True)

            if tool_results:
                for tool_result in tool_results:
                    try:
                        raw_payload = tool_result.get("_raw_content") or tool_result.get("content", "{}")
                        parsed = json.loads(raw_payload)
                    except Exception:
                        continue
                    if isinstance(parsed, dict) and parsed.get("error"):
                        tool_name = str(tool_result.get("name") or "").strip()
                        error_obj = parsed.get("error")
                        error_code = ""
                        if isinstance(error_obj, dict):
                            error_code = str(error_obj.get("code") or "").strip()
                        if tool_name == "system.country_info" and error_code == "NOT_FOUND":
                            country_not_found_detected = True

            assistant_message: Dict[str, Any] = {
                "role": "assistant",
                "content": round_text if round_text.strip() else None,
                "tool_calls": [
                    {"id": tc["id"], "type": "function", "function": tc["function"]} for tc in tool_calls
                ],
            }
            if isinstance(assistant_message.get("content"), str):
                assistant_message["content"] = force_sanitize_links(assistant_message["content"])
            _wf_for_parts = gateway_kwargs.get("_workflow")
            _raw_mp = getattr(_wf_for_parts, "gemini_stream_raw_model_parts", None) if _wf_for_parts is not None else None
            if provider_key in ("gemini", "google") and isinstance(_raw_mp, list) and _raw_mp:
                assistant_message["_gemini_raw_model_parts"] = list(_raw_mp)
            gateway_kwargs["chat_history"].append(assistant_message)
            for tool_result in tool_results or []:
                if isinstance(tool_result, dict):
                    content = tool_result.get("content")
                    if isinstance(content, str):
                        tool_result.setdefault("_raw_content", content)
                if isinstance(tool_result, dict):
                    content = tool_result.get("content")
                    if isinstance(content, str):
                        tool_result["content"] = force_sanitize_links(content)
                gateway_kwargs["chat_history"].append(tool_result)

            # 💎 GEMINI-RESPONSE-TRIGGER: Force Gemini to generate text after tool execution
            # Gemini unlike OpenAI often stops after tool calls without generating summary text
            if provider_key in ("gemini", "google"):
                gateway_kwargs["chat_history"].append({
                    "role": "system",
                    "content": "[System-Instruction]: The tool execution was successful. You MUST now provide a final, natural language response to the user summarizing this result."
                })

            _sctx = gateway_kwargs.get("_suggestion_context")
            if isinstance(_sctx, dict) and isinstance(gateway_kwargs.get("chat_history"), list):
                from backend.services.orchestrator.suggestion_engine import (
                    SuggestionContextV1,
                    refresh_suggestion_system_message_after_tools,
                )

                refresh_suggestion_system_message_after_tools(
                    gateway_kwargs["chat_history"],
                    results_buffer,
                    cast(SuggestionContextV1, _sctx),
                )

            response = {"text": round_text, "tool_calls": tool_calls}
            current_iteration += 1

        if response is None:
            response = {"text": fallback_summary}
        if isinstance(response, dict) and not response.get("modal_request"):
            derived_modal = self._build_video_modal_request_from_tool_results(results_buffer)
            if derived_modal:
                response["modal_request"] = derived_modal

        text_value = fallback_summary
        if isinstance(response, dict):
            text_value = str(response.get("text") or fallback_summary)
        else:
            text_value = str(response or fallback_summary)
        
        # 💎 GEMINI-FALLBACK: If text is still empty/whitespace after tool execution,
        # try to extract meaningful text from successful tool results
        if not text_value or not text_value.strip() or text_value == fallback_summary:
            if had_tool_round and results_buffer:
                # Look for successful tool results to construct a meaningful response
                successful_results = []
                for tr in results_buffer:
                    if not isinstance(tr, dict):
                        continue
                    try:
                        raw = tr.get("_raw_content") or tr.get("content", "{}")
                        parsed = json.loads(raw) if isinstance(raw, str) else dict(raw or {})
                        if isinstance(parsed, dict) and parsed.get("status") == "ok":
                            msg = parsed.get("message") or parsed.get("output")
                            if msg:
                                successful_results.append(str(msg))
                    except Exception:
                        continue
                if successful_results:
                    text_value = "\n\n".join(successful_results)
                    logger.info("💎 GEMINI-FALLBACK: Constructed response from %d tool results", len(successful_results))
        
        text_value = force_sanitize_links(text_value)
        text_value = append_tool_attributions_from_tools(text_value, results_buffer)

        if country_not_found_detected and isinstance(response, dict):
            response["skip_fact_extraction"] = True

        tool_loop_agent_payload = None
        if all_used_skills:
            tool_loop_agent_payload = {
                "name": "Tool Loop",
                "required_skills": list(all_used_skills),
                "mode": "tool_loop",
            }

        er = ExecutionResponse(
            text=text_value,
            agent_payload=tool_loop_agent_payload,
            tool_calls=latest_tool_calls,
            is_agent_flow=bool(tool_loop_agent_payload),
            raw_response=response if isinstance(response, dict) else {"text": text_value},
            ui_command=latest_ui_command,
            font_fallback_notice=font_fallback_notice,
            factcheck_modifications_detected=factcheck_modifications_detected,
            all_tool_results=results_buffer,
            usage={
                "input_tokens": aggregated_tokens_input,
                "output_tokens": aggregated_tokens_output,
                "total_tokens": aggregated_tokens_input + aggregated_tokens_output,
            },
            cost={"total_cost": aggregated_total_cost},
        )
        if result_holder is not None:
            result_holder["execution_result"] = er
        yield StreamEvent(type="stream_complete", content={"text": er.text}, metadata={})

    @staticmethod
    def _build_atomic_planner_prompt(
        user_text: str,
        step_outputs: List[str],
        failed_steps: Optional[List[str]] = None,
    ) -> str:
        has_success = bool(step_outputs)
        has_failed = bool(failed_steps)
        if not has_success and not has_failed:
            return user_text

        blocks: List[str] = [f"{user_text}\n"]
        if has_success:
            completed_block = "\n".join(f"- {entry}" for entry in step_outputs)
            blocks.append(
                "BISHERIGE TOOL-ERGEBNISSE (bereits erledigt):\n"
                f"{completed_block}\n"
            )
        if has_failed:
            failed_block = "\n".join(f"- {entry}" for entry in (failed_steps or []))
            blocks.append(
                "FINAL FEHLGESCHLAGENE SCHRITTE (NICHT WIEDERHOLEN):\n"
                f"{failed_block}\n"
            )
        blocks.append("Plane nur die noch offenen naechsten Schritte.")
        return "\n".join(blocks)

    @staticmethod
    def _extract_step_error(step_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(step_result, dict):
            return None
        raw_response = step_result.get("raw_response")
        if not isinstance(raw_response, dict):
            return None

        tool_errors = raw_response.get("tool_errors")
        if isinstance(tool_errors, list):
            for item in tool_errors:
                if isinstance(item, dict) and isinstance(item.get("error"), dict):
                    error_obj = item.get("error")
                    if error_obj:
                        return error_obj

        tool_calls = raw_response.get("tool_calls")
        if not isinstance(tool_calls, list):
            return None

        for tool_call in tool_calls:
            function = tool_call.get("function") if isinstance(tool_call, dict) else {}
            args_raw = (function or {}).get("arguments")
            if not isinstance(args_raw, str):
                continue
            try:
                args = json.loads(args_raw)
            except Exception:
                continue
            if not isinstance(args, dict):
                continue
            error_obj = args.get("error")
            if isinstance(error_obj, dict) and error_obj:
                return error_obj
        return None

    @staticmethod
    def _step_has_tool_call(step_result: Dict[str, Any]) -> bool:
        if not isinstance(step_result, dict):
            return False
        raw_response = step_result.get("raw_response")
        if not isinstance(raw_response, dict):
            return False
        tool_calls = raw_response.get("tool_calls")
        if isinstance(tool_calls, list) and len(tool_calls) > 0:
            return True
        if raw_response.get("executed_tool_call") is True:
            return True
        # In der Agent-Runtime (max_tool_rounds=1) signalisiert dieses Feld,
        # dass mindestens eine Tool-Runde durchlaufen wurde.
        if raw_response.get("tool_limit_reached") is True:
            return True
        return False

    @staticmethod
    def _build_atomic_final_text(user_text: str, step_outputs: List[str]) -> str:
        if not step_outputs:
            return "Ich habe keine weiteren offenen Aufgaben gefunden."
        if len(step_outputs) == 1:
            single_output = str(step_outputs[0] or "").strip()
            match = re.match(r"^\[[^\]]+\]\s*(.+)$", single_output, flags=re.DOTALL)
            if match:
                return match.group(1).strip()
            return single_output
        lines = ["Abgeschlossen. Ergebnis aus den atomaren Schritten:"]
        lines.extend(f"- {entry}" for entry in step_outputs)
        lines.append(f"Anfrage: {user_text}")
        return "\n".join(lines)

    async def _run_atomic_clean_synthesis(
        self,
        *,
        user_text: str,
        step_outputs: List[str],
        provider: str,
        model: str,
        api_key: str,
        chat_id: Optional[int],
        completed_skills: List[str],
    ) -> str:
        if not step_outputs:
            return "Ich habe keine weiteren offenen Aufgaben gefunden."

        facts_block = "\n".join(f"- {entry}" for entry in step_outputs)
        synthesis_messages = [
            {
                "role": "system",
                "content": (
                    "Du hast alle geplanten Aufgaben ausgeführt. Es gibt keine weiteren Tools mehr. "
                    "Formuliere jetzt die finale Antwort an den Nutzer. Sende kein JSON, sende nur Text.\n\n"
                    "Nutze dafuer ausschliesslich die folgenden Fakten aus Tool-Ergebnissen.\n\n"
                    f"FAKTEN:\n{facts_block}"
                ),
            },
            {"role": "user", "content": user_text},
        ]

        synthesis_executor = ToolExecutor(
            db=self.db,
            api_key=api_key or "",
            provider=provider,
            model=model,
            additional_context={
                "chat_id": chat_id,
                "allowed_skill_ids": list(completed_skills),
                "provider": provider,
                "model": model,
            },
        )

        try:
            synthesis_response = await llm_gateway.reason_and_respond(
                provider=provider,
                model=model,
                api_key=api_key or "",
                chat_history=synthesis_messages,
                context_manager=self.context_manager,
                db=self.db,
                user_prompt=user_text,
                chat_id=chat_id or 0,
                tool_executor=synthesis_executor,
                disable_tools=True,
                allowed_skill_ids=[],
                max_tool_rounds=1,
            )
            synthesis_text = str((synthesis_response or {}).get("text") or "").strip()
            if synthesis_text:
                return synthesis_text
        except Exception:
            logger.error("ATOMIC SYNTHESIS FAILED: fallback to deterministic summary", exc_info=True)

        return self._build_atomic_final_text(user_text, step_outputs)

    async def _run_final_synthesis(
        self,
        *,
        user_text: str,
        step_outputs: List[str],
        provider: str,
        model: str,
        api_key: str,
        chat_id: Optional[int],
        completed_skills: List[str],
        final_model: Optional[str] = None,  # 💎 FINAL-MODEL-FIX: Aufgewertetes Modell aus Tool-Loop
    ) -> str:
        # 💎 FINAL-MODEL-FIX: Nutze das aufgewertete Modell wenn verfügbar
        synthesis_model = final_model if final_model else model
        if final_model and final_model != model:
            logger.info(
                "FINAL-SYNTHESIS-MODEL-OVERRIDE: Using upgraded model '%s' instead of original '%s'",
                final_model, model
            )
        return await self._run_atomic_clean_synthesis(
            user_text=user_text,
            step_outputs=step_outputs,
            provider=provider,
            model=synthesis_model,  # 💎 FINAL-MODEL-FIX: Aufgewertetes Modell nutzen
            api_key=api_key,
            chat_id=chat_id,
            completed_skills=completed_skills,
        )

    @staticmethod
    def _skill_label(skill_id: str) -> str:
        mapping = {
            "system.country_info": "CountryInfo",
            "system.routing": "Routing",
        }
        return mapping.get(str(skill_id or "").strip(), str(skill_id or "").strip())

    @staticmethod
    def _is_pdf_create_skill(skill_id: str) -> bool:
        normalized = str(skill_id or "").strip().lower()
        return normalized in {"system.create_pdf", "create_pdf", "knowledge.create_pdf"}

    @staticmethod
    def _is_pdf_creation_request(user_text: str) -> bool:
        text = str(user_text or "").lower()
        return ("pdf" in text or "dokument" in text) and any(
            token in text for token in ["erstelle", "create", "generiere", "schreibe"]
        )

