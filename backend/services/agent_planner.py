import json
import logging
import re
from typing import Any, Dict, List, Optional

from backend.data.schemas import AgentSpec, PlannerContext, PlannerProviderProfile
from backend.services import llm_gateway
from backend.services.tool_manager import tool_manager
from backend.services.orchestrator.intent_engine import IntentDetectionResult

logger = logging.getLogger("janus_backend")


class AgentPlanner:
    """Plans a minimal agent spec from the already detected intent contract."""

    _DETERMINISTIC_SKILL_CANDIDATES: Dict[str, List[str]] = {
        "shopping": ["system.price_comparison"],
        "calendar": ["calendar.list_events", "calendar.find_slots", "calendar.find_and_update_event"],
        "local_business": ["system.local_business"],
        "video_understanding": ["video.understand"],
        "video_list": ["video.search"],
        "video": ["video.search"],
        "image": ["system.generate_image"],
        "multitask_image_pdf": ["system.generate_image", "system.create_pdf"],
    }

    def __init__(self, model_hierarchy: Optional[Dict[str, Dict[str, str]]] = None):
        self.model_hierarchy = dict(model_hierarchy or {})

    def set_model_hierarchy(self, model_hierarchy: Dict[str, Dict[str, str]] | None) -> None:
        if isinstance(model_hierarchy, dict):
            self.model_hierarchy = dict(model_hierarchy)

    def should_use_agent(self, user_prompt: str, intent_result: Optional[IntentDetectionResult] = None) -> bool:
        if intent_result is None:
            return False
        return bool(
            getattr(intent_result, "has_tool_trigger", False)
            or getattr(intent_result, "is_complex_document_request", False)
            or getattr(intent_result, "primary_intent", None) in self._DETERMINISTIC_SKILL_CANDIDATES
        )

    async def plan(
        self,
        *,
        user_prompt: str,
        intent_result: IntentDetectionResult,
        planner_context: PlannerContext,
        provider_profile: PlannerProviderProfile,
        capability_registry: Any = None,
        capability_groups: Optional[Dict[str, List[str]]] = None,
        relevant_skill_ids: Optional[List[str]] = None,
        provider: str,
        model: str,
        api_key: str,
    ) -> AgentSpec:
        if self._is_lockdown_prompt(user_prompt) or planner_context.lockdown_after_pdf:
            return AgentSpec(
                name="Task-Spezialist",
                goal="Finale Synthese nach abgeschlossener Tool-Ausführung",
                required_skills=[],
                instructions="Keine weiteren Tools planen. Finalantwort aus bereits vorliegenden Ergebnissen erstellen.",
                max_iterations=1,
            )

        scoped_groups = self._scope_capability_groups(
            capability_groups=capability_groups,
            relevant_skill_ids=planner_context.allowed_skill_ids or relevant_skill_ids or [],
            forbidden_skill_ids=planner_context.forbidden_skill_ids,
        )
        if capability_registry is not None and hasattr(capability_registry, "get_planner_scope"):
            registry_scope = capability_registry.get_planner_scope(
                intent_result,
                allowed_skill_ids=planner_context.allowed_skill_ids or relevant_skill_ids or [],
            )
            registry_groups = registry_scope.get("capability_groups") if isinstance(registry_scope, dict) else None
            if registry_groups:
                scoped_groups = self._scope_capability_groups(
                    capability_groups=registry_groups,
                    relevant_skill_ids=planner_context.allowed_skill_ids or relevant_skill_ids or [],
                    forbidden_skill_ids=planner_context.forbidden_skill_ids,
                )

        deterministic = self._deterministic_plan(
            user_prompt=user_prompt,
            intent_result=intent_result,
            planner_context=planner_context,
            capability_groups=scoped_groups,
            provider_profile=provider_profile,
        )
        if deterministic is not None:
            return deterministic

        if not provider_profile.allow_llm_planning:
            return self._registry_fallback_plan(
                user_prompt=user_prompt,
                planner_context=planner_context,
                capability_groups=scoped_groups,
                max_iterations_cap=provider_profile.max_iterations_cap,
            )

        planner_prompt = self._build_planner_prompt(
            user_prompt=user_prompt,
            intent_result=intent_result,
            planner_context=planner_context,
            capability_groups=scoped_groups,
            provider_profile=provider_profile,
        )
        try:
            raw = await llm_gateway.simple_llm_generate_content(
                provider=provider,
                model=model,
                api_key=api_key,
                prompt=planner_prompt,
            )
            candidate = self._extract_text_payload(raw)
            if candidate:
                payload = self._extract_json(candidate)
                if payload:
                    payload = self._sanitize_payload(payload)
                    validated = AgentSpec.model_validate(payload)
                    return self._normalize_plan(
                        validated,
                        user_prompt=user_prompt,
                        planner_context=planner_context,
                        capability_groups=scoped_groups,
                        max_iterations_cap=provider_profile.max_iterations_cap,
                    )
        except Exception as exc:
            logger.warning("AGENT-PLANNER: LLM planning fallback activated: %s", exc)

        return self._registry_fallback_plan(
            user_prompt=user_prompt,
            planner_context=planner_context,
            capability_groups=scoped_groups,
            max_iterations_cap=provider_profile.max_iterations_cap,
        )

    def _deterministic_plan(
        self,
        *,
        user_prompt: str,
        intent_result: IntentDetectionResult,
        planner_context: PlannerContext,
        capability_groups: Dict[str, List[str]],
        provider_profile: PlannerProviderProfile,
    ) -> Optional[AgentSpec]:
        available = self._available_skills(capability_groups, planner_context)
        required = self._filter_skills(planner_context.required_skill_ids, available, planner_context)
        if required:
            return self._spec_for_skills(
                name="Intent-Spezialist",
                goal=user_prompt,
                skills=required,
                instructions=self._instructions_for(required, planner_context),
                max_iterations_cap=provider_profile.max_iterations_cap,
            )

        primary_intent = str(getattr(intent_result, "primary_intent", "") or "").strip()
        candidates = self._DETERMINISTIC_SKILL_CANDIDATES.get(primary_intent, [])
        selected = self._select_candidate_skills(candidates, available, planner_context)
        if selected:
            logger.info(
                "AGENT-PLANNER: Deterministic plan for primary_intent=%s skills=%s",
                primary_intent,
                selected,
            )
            return self._spec_for_skills(
                name="Intent-Spezialist",
                goal=user_prompt,
                skills=selected,
                instructions=self._instructions_for(selected, planner_context),
                max_iterations_cap=provider_profile.max_iterations_cap,
            )

        return None

    def _registry_fallback_plan(
        self,
        *,
        user_prompt: str,
        planner_context: PlannerContext,
        capability_groups: Dict[str, List[str]],
        max_iterations_cap: int,
    ) -> AgentSpec:
        available = self._available_skills(capability_groups, planner_context)
        priority = self._filter_skills(planner_context.priority_skill_ids, available, planner_context)
        selected = priority or list(available)[:2]
        return self._spec_for_skills(
            name="Task-Spezialist",
            goal=user_prompt,
            skills=selected,
            instructions=self._instructions_for(selected, planner_context),
            max_iterations_cap=max_iterations_cap,
        )

    def _normalize_plan(
        self,
        spec: AgentSpec,
        *,
        user_prompt: str,
        planner_context: PlannerContext,
        capability_groups: Dict[str, List[str]],
        max_iterations_cap: int = 8,
    ) -> AgentSpec:
        available = self._available_skills(capability_groups, planner_context)
        normalized_required = self._filter_skills(spec.required_skills or [], available, planner_context)
        if not normalized_required:
            normalized_required = self._filter_skills(planner_context.required_skill_ids, available, planner_context)
        if not normalized_required:
            normalized_required = list(available)[:2]

        safe_cap = max(1, min(12, int(max_iterations_cap or 8)))
        bounded_iterations = max(1, min(safe_cap, int(spec.max_iterations or 1)))
        if len(normalized_required) >= 2:
            bounded_iterations = max(2, min(safe_cap, bounded_iterations))

        final_goal = str(spec.goal).strip() if spec.goal else str(user_prompt or "").strip()
        final_instructions = str(spec.instructions).strip() if spec.instructions else ""
        if not final_instructions:
            final_instructions = self._instructions_for(normalized_required, planner_context)

        return AgentSpec(
            name=str(spec.name or "Agent").strip() or "Agent",
            goal=final_goal or "Erfülle den Nutzerauftrag präzise.",
            required_skills=normalized_required,
            instructions=final_instructions,
            max_iterations=bounded_iterations,
        )

    def _build_planner_prompt(
        self,
        *,
        user_prompt: str,
        intent_result: IntentDetectionResult,
        planner_context: PlannerContext,
        capability_groups: Dict[str, List[str]],
        provider_profile: PlannerProviderProfile,
    ) -> str:
        from .prompting.core.model import OutputContractDirective
        from .prompting.runtime.builder import PromptBuilder

        builder = PromptBuilder()
        builder.add_block("system_role", "Du bist der Janus Agent Planner.", priority=1, required=True)
        builder.add_block(
            "intent_contract",
            self._render_intent_contract(intent_result),
            priority=1,
            required=True,
        )
        builder.add_block(
            "grounding_rules",
            "- Erkenne keine Intents neu. Das IntentDetectionResult ist die einzige Wahrheit.\n"
            "- Wähle nur Skills aus dem Capability-Scope.\n"
            "- Plane sequentiell: pro Iteration genau EIN Skill-Call.\n"
            "- Nutze die kleinste ausreichende Skillmenge.",
            priority=1,
            required=True,
        )
        builder.add_block(
            "negative_constraints",
            self._render_negative_constraints(planner_context),
            priority=1,
            required=True,
        )
        builder.add_block(
            "capability_scope",
            self._render_capability_scope(capability_groups, planner_context),
            priority=2,
            required=True,
        )
        builder.add_block(
            "output_contract",
            OutputContractDirective(
                format="json",
                fields=["name", "goal", "required_skills", "instructions", "max_iterations"],
            ),
            priority=1,
            required=True,
        )
        builder.add_block("user_prompt", f"AUFGABE:\n{user_prompt}", priority=2, required=True)
        return builder.compile(
            provider=provider_profile.provider or "openai",
            model_id=provider_profile.planner_model,
            max_tokens=2400 if provider_profile.model_class in {"nano", "mini"} else 4000,
        )

    def _render_intent_contract(self, intent_result: IntentDetectionResult) -> str:
        active = []
        for key, value in vars(intent_result).items():
            if key.startswith("is_") and bool(value):
                active.append(key)
        return (
            f"primary_intent={getattr(intent_result, 'primary_intent', None)}\n"
            f"active_flags={', '.join(active) if active else '(none)'}\n"
            f"vetoed_intents={getattr(intent_result, 'vetoed_intents', {})}"
        )

    def _render_negative_constraints(self, planner_context: PlannerContext) -> str:
        lines = []
        if planner_context.forbidden_skill_ids:
            lines.append("FORBIDDEN_SKILLS: " + ", ".join(planner_context.forbidden_skill_ids))
        lines.extend(planner_context.negative_constraints or [])
        return "\n".join(lines) if lines else "Keine zusätzlichen Verbote."

    def _render_capability_scope(
        self,
        capability_groups: Dict[str, List[str]],
        planner_context: PlannerContext,
    ) -> str:
        lines = []
        for cap, skills in sorted((capability_groups or {}).items()):
            clean_skills = self._filter_skills(skills or [], None, planner_context)
            if not clean_skills:
                continue
            detail = []
            for skill_id in clean_skills:
                metadata = tool_manager.get_skill_metadata(skill_id)
                desc = metadata.description if metadata and metadata.description else "Keine Beschreibung verfügbar."
                detail.append(f"{skill_id}: {desc}")
            lines.append(f"- {cap}: {'; '.join(detail)}")
        return "\n".join(lines) if lines else "- (keine Capabilities verfügbar)"

    def _available_skills(
        self,
        capability_groups: Dict[str, List[str]],
        planner_context: PlannerContext,
    ) -> List[str]:
        allowed = {
            str(skill_id).strip()
            for skill_id in (planner_context.allowed_skill_ids or [])
            if str(skill_id).strip()
        }
        forbidden = {
            str(skill_id).strip()
            for skill_id in (planner_context.forbidden_skill_ids or [])
            if str(skill_id).strip()
        }
        ordered: List[str] = []
        seen = set()
        for skills in (capability_groups or {}).values():
            for skill in skills or []:
                sid = str(skill or "").strip()
                if not sid or sid in seen or sid in forbidden:
                    continue
                if allowed and sid not in allowed:
                    continue
                seen.add(sid)
                ordered.append(sid)
        if not ordered and allowed:
            ordered = [sid for sid in sorted(allowed) if sid not in forbidden]
        return ordered

    def _filter_skills(
        self,
        skills: List[str],
        available: Optional[List[str]],
        planner_context: PlannerContext,
    ) -> List[str]:
        available_set = set(available or [])
        forbidden = set(planner_context.forbidden_skill_ids or [])
        result: List[str] = []
        seen = set()
        for skill in skills or []:
            sid = str(skill or "").strip()
            if not sid or sid in seen or sid in forbidden:
                continue
            if available is not None and available_set and sid not in available_set:
                continue
            seen.add(sid)
            result.append(sid)
        return result

    def _select_candidate_skills(
        self,
        candidates: List[str],
        available: List[str],
        planner_context: PlannerContext,
    ) -> List[str]:
        selected = self._filter_skills(candidates, available, planner_context)
        if selected:
            return selected[:2]
        aliases = {}
        aliased = [aliases.get(skill, skill) for skill in candidates]
        return self._filter_skills(aliased, available, planner_context)[:2]

    def _spec_for_skills(
        self,
        *,
        name: str,
        goal: str,
        skills: List[str],
        instructions: str,
        max_iterations_cap: int,
    ) -> AgentSpec:
        clean = []
        seen = set()
        for skill in skills:
            sid = str(skill or "").strip()
            if sid and sid not in seen:
                seen.add(sid)
                clean.append(sid)
        safe_cap = max(1, min(12, int(max_iterations_cap or 8)))
        iterations = max(1, min(safe_cap, len(clean) or 1))
        return AgentSpec(
            name=name,
            goal=str(goal or "").strip() or "Erfülle den Nutzerauftrag präzise.",
            required_skills=clean,
            instructions=instructions,
            max_iterations=iterations,
        )

    def _instructions_for(self, skills: List[str], planner_context: PlannerContext) -> str:
        if not skills:
            return "Keine weiteren Tools planen. Finalantwort aus vorhandenen Ergebnissen erstellen."
        constraints = " ".join(planner_context.negative_constraints or [])
        skill_text = ", ".join(skills)
        base = f"Führe nur diese Skills sequentiell aus: {skill_text}. Pro Iteration genau ein Tool."
        if constraints:
            base += f" Beachte zwingend: {constraints}"
        return base

    def _scope_capability_groups(
        self,
        *,
        capability_groups: Optional[Dict[str, List[str]]],
        relevant_skill_ids: List[str],
        forbidden_skill_ids: List[str],
    ) -> Dict[str, List[str]]:
        allowed = {str(skill_id).strip() for skill_id in (relevant_skill_ids or []) if str(skill_id).strip()}
        forbidden = {str(skill_id).strip() for skill_id in (forbidden_skill_ids or []) if str(skill_id).strip()}
        scoped: Dict[str, List[str]] = {}
        for capability, skills in (capability_groups or {}).items():
            selected = []
            for skill in skills or []:
                sid = str(skill or "").strip()
                if not sid or sid in forbidden:
                    continue
                if allowed and sid not in allowed:
                    continue
                selected.append(sid)
            if selected:
                scoped[str(capability)] = selected
        return scoped

    @staticmethod
    def _sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        if "instructions" in payload and isinstance(payload["instructions"], list):
            payload["instructions"] = " ".join([str(item) for item in payload["instructions"]])
        if "goal" in payload and isinstance(payload["goal"], list):
            payload["goal"] = " ".join([str(item) for item in payload["goal"]])
        if "required_skills" in payload and isinstance(payload["required_skills"], str):
            skill_str = payload["required_skills"].strip()
            payload["required_skills"] = [skill_str] if skill_str else []
        return payload

    @staticmethod
    def _extract_text_payload(raw: object) -> str:
        if isinstance(raw, dict):
            if isinstance(raw.get("text"), str):
                return raw["text"]
            if isinstance(raw.get("content"), str):
                return raw["content"]
        if isinstance(raw, str):
            return raw
        return ""

    def _extract_json(self, text: str) -> Dict:
        clean = str(text or "").strip()
        if not clean:
            return {}

        fenced_blocks = re.findall(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", clean, flags=re.IGNORECASE)
        for block in fenced_blocks:
            try:
                payload = json.loads(block)
                if isinstance(payload, dict):
                    return payload
            except Exception:
                continue

        start_idx = clean.find("{")
        end_idx = clean.rfind("}")
        if start_idx != -1 and end_idx != -1:
            clean = clean[start_idx : end_idx + 1]

        clean = clean.strip().strip(".").strip("`").strip()
        if clean.startswith("{") and clean.endswith("}"):
            try:
                payload = json.loads(clean)
                if isinstance(payload, dict):
                    payload.setdefault("name", "Agent")
                    payload.setdefault("goal", "Task execution")
                    payload.setdefault("instructions", "Follow the plan.")
                    payload.setdefault("required_skills", [])
                    payload.setdefault("max_iterations", 1)
                    return payload
            except Exception:
                pass

        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", clean):
            try:
                candidate, _end = decoder.raw_decode(clean[match.start():])
                if isinstance(candidate, dict):
                    return candidate
            except Exception:
                continue

        return {}

    @staticmethod
    def _is_lockdown_prompt(prompt: str) -> bool:
        return "LOCKDOWN_MODE: CREATE_PDF_DONE" in str(prompt or "")
