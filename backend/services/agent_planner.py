import json
import logging
import re
from typing import Any, Dict, List

from backend.data.schemas import AgentSpec
from backend.services import llm_gateway
from backend.services.tool_manager import tool_manager
from backend.utils import intent_classifier

logger = logging.getLogger("janus_backend")

_PRICE_QUERY_KEYWORDS = frozenset([
    "preis", "kostet", "kosten", "teuer", "kaufen", "angebot",
    "g\u00fcnstiger", "g\u00fcnstigster", "bestpreis", "preisvergleich",
    "geschenk", "schenken", "modell", "varianten",
])


class AgentPlanner:
    """Plans a specialized agent spec for complex user requests."""

    _DEFAULT_MODEL_HIERARCHY: Dict[str, Dict[str, str]] = {
        "openai": {
            "vision": "gpt-4o",
            "logic": "gpt-5.2",
            "speed": "gpt-5.2",
        },
        "gemini": {
            "vision": "gemini-3-flash-preview",
            "logic": "gemini-3-pro-preview",
            "speed": "gemini-3-flash-preview",
        },
        "ollama": {
            "logic": "llama3.1:8b",
            "vision": "llava",
            "fast": "llama3.1:8b",
            "speed": "llama3.1:8b",
        },
    }

    def __init__(self, model_hierarchy: Dict[str, Dict[str, str]] | None = None):
        self.model_hierarchy = dict(model_hierarchy or self._DEFAULT_MODEL_HIERARCHY)

    def set_model_hierarchy(self, model_hierarchy: Dict[str, Dict[str, str]] | None) -> None:
        if isinstance(model_hierarchy, dict) and model_hierarchy:
            self.model_hierarchy = dict(model_hierarchy)

    def should_use_agent(self, user_prompt: str) -> bool:
        text = str(user_prompt or "").strip().lower()
        if not text:
            return False
        complexity_markers = [
            "durchsuche",
            "analysiere",
            "erstelle",
            "und",
            "zusammenfassung",
            "mehrschritt",
            "pipeline",
        ]
        return sum(1 for marker in complexity_markers if marker in text) >= 2

    async def plan(
        self,
        *,
        user_prompt: str,
        capability_groups: Dict[str, List[str]],
        relevant_skill_ids: List[str] | None = None,
        provider: str,
        model: str,
        api_key: str,
    ) -> AgentSpec:
        if self._is_lockdown_prompt(user_prompt):
            return AgentSpec(
                name="Task-Spezialist",
                goal="Finale Synthese nach erfolgreicher PDF-Erstellung",
                required_skills=[],
                instructions="Keine weiteren Tools planen. Finalantwort aus bereits vorliegenden Ergebnissen erstellen.",
                max_iterations=1,
            )

        scoped_groups = self._scope_capability_groups(
            capability_groups=capability_groups,
            relevant_skill_ids=relevant_skill_ids,
        )
        model_profile = self._resolve_model_profile(provider=provider, model=model)
        provider_key = str(model_profile.get("provider", "") or "").lower()

        if provider_key == "openai":
            logger.info("AGENT-PLANNER: Nutze Prompting Engine V2 (OpenAI XML-Dialekt)")
            planner_prompt = self._build_planner_prompt_v2(
                user_prompt=user_prompt,
                capability_groups=scoped_groups,
                model_profile=model_profile,
            )
        else:
            planner_prompt = self._build_planner_prompt(
                user_prompt=user_prompt,
                capability_groups=scoped_groups,
                model_profile=model_profile,
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
                    # --- SANITIZER FUER LOKALE MODELLE ---
                    # Wenn 'instructions' als Liste kommt, wandeln wir sie in einen String um.
                    if "instructions" in payload and isinstance(payload["instructions"], list):
                        payload["instructions"] = " ".join([str(item) for item in payload["instructions"]])

                    # Optional: Auch 'goal' sanitizen, falls das Modell hier denselben Fehler macht.
                    if "goal" in payload and isinstance(payload["goal"], list):
                        payload["goal"] = " ".join([str(item) for item in payload["goal"]])

                    # required_skills von String auf Liste normalisieren.
                    if "required_skills" in payload and isinstance(payload["required_skills"], str):
                        skill_str = payload["required_skills"].strip()
                        payload["required_skills"] = [skill_str] if skill_str else []

                    validated = AgentSpec.model_validate(payload)
                    return self._normalize_plan(
                        validated,
                        user_prompt=user_prompt,
                        capability_groups=scoped_groups,
                        max_iterations_cap=int(model_profile.get("max_iterations_cap") or 8),
                    )
        except Exception as exc:
            logger.warning("AGENT-PLANNER: LLM planning fallback activated: %s", exc)

        return self._heuristic_plan(
            user_prompt,
            scoped_groups,
            max_iterations_cap=int(model_profile.get("max_iterations_cap") or 8),
        )

    def _normalize_plan(
        self,
        spec: AgentSpec,
        *,
        user_prompt: str,
        capability_groups: Dict[str, List[str]],
        max_iterations_cap: int = 8,
    ) -> AgentSpec:
        available_skills = {
            str(skill).strip()
            for skills in (capability_groups or {}).values()
            for skill in (skills or [])
            if str(skill).strip()
        }
        normalized_required: List[str] = []
        seen = set()
        for skill in list(spec.required_skills or []):
            skill_id = str(skill or "").strip()
            if not skill_id or skill_id in seen:
                continue
            if available_skills and skill_id not in available_skills:
                continue
            seen.add(skill_id)
            normalized_required.append(skill_id)

        lowered = str(user_prompt or "").lower()
        if self._is_single_goal_pdf_request(lowered):
            pdf_skill = self._select_pdf_create_skill(
                available_skills=available_skills,
                planned_skills=normalized_required,
            )
            normalized_required = [pdf_skill] if pdf_skill else []
            final_goal = str(spec.goal).strip() if spec.goal else str(user_prompt or "").strip()
            if not final_goal:
                final_goal = "Erstelle das gewünschte PDF gemäß Nutzerauftrag."
            final_instructions = str(spec.instructions).strip() if spec.instructions else "Führe die geplanten Schritte sequentiell aus."
            if not final_instructions:
                final_instructions = "Führe die geplanten Schritte sequentiell aus."
            return AgentSpec(
                name=str(spec.name or "Agent").strip() or "Agent",
                goal=final_goal,
                required_skills=normalized_required,
                instructions=final_instructions,
                max_iterations=1,
            )

        # --- C8: PRICE GUARDRAIL (hard override) ---
        if self._is_price_query(lowered):
            price_skill = "system.price_comparison"
            if not available_skills or price_skill in available_skills:
                logger.info("AGENT-PLANNER: Price-Guardrail aktiv – system.price_comparison erzwungen, system.websearch gesperrt")
                return AgentSpec(
                    name="Preis-Spezialist",
                    goal=str(spec.goal or user_prompt).strip() or user_prompt,
                    required_skills=[price_skill],
                    instructions="Rufe ausschlie\u00dflich system.price_comparison auf. system.websearch ist f\u00fcr diese Anfrage verboten.",
                    max_iterations=1,
                )

        if self._is_routing_prompt(lowered):
            self._append_skill_if_allowed("system.routing", normalized_required, seen, available_skills)
        if intent_classifier.is_country_info_intent(lowered) and not intent_classifier.is_generic_country_prompt(lowered):
            self._append_skill_if_allowed("system.country_info", normalized_required, seen, available_skills)
        normalized_required = self._prioritize_geo_sequence(normalized_required)

        if not normalized_required:
            for skills in (capability_groups or {}).values():
                for skill in (skills or []):
                    skill_id = str(skill or "").strip()
                    if not skill_id or skill_id in seen:
                        continue
                    seen.add(skill_id)
                    normalized_required.append(skill_id)
                    if len(normalized_required) >= 2:
                        break
                if len(normalized_required) >= 2:
                    break

        safe_cap = max(1, min(8, int(max_iterations_cap or 8)))
        bounded_iterations = max(1, min(safe_cap, int(spec.max_iterations or 1)))
        if len(normalized_required) >= 2:
            bounded_iterations = max(2, min(safe_cap, bounded_iterations))
        final_goal = str(spec.goal).strip() if spec.goal else str(user_prompt or "").strip()
        if not final_goal:
            final_goal = "Erfülle den Nutzerauftrag präzise."
        final_instructions = str(spec.instructions).strip() if spec.instructions else "Führe die geplanten Schritte sequentiell aus."
        if not final_instructions:
            final_instructions = "Führe die geplanten Schritte sequentiell aus."

        return AgentSpec(
            name=str(spec.name or "Agent").strip() or "Agent",
            goal=final_goal,
            required_skills=normalized_required,
            instructions=final_instructions,
            max_iterations=bounded_iterations,
        )

    @staticmethod
    def _append_skill_if_allowed(skill_id: str, target: List[str], seen: set, allowed: set) -> None:
        sid = str(skill_id or "").strip()
        if not sid or sid in seen:
            return
        if allowed and sid not in allowed:
            return
        seen.add(sid)
        target.append(sid)

    @staticmethod
    def _is_price_query(prompt_lower: str) -> bool:
        """Returns True if the user prompt contains price-related keywords."""
        text = str(prompt_lower or "")
        return any(kw in text for kw in _PRICE_QUERY_KEYWORDS)

    @staticmethod
    def _is_routing_prompt(prompt_lower: str) -> bool:
        routing_markers = ["route", "distanz", "fahrzeit", "von", "nach", "kilometer", "km"]
        return any(marker in prompt_lower for marker in routing_markers)

    @staticmethod
    def _prioritize_geo_sequence(required_skills: List[str]) -> List[str]:
        ordered = [str(skill or "").strip() for skill in (required_skills or []) if str(skill or "").strip()]
        if "system.country_info" in ordered and "system.routing" in ordered:
            remainder = [s for s in ordered if s not in {"system.country_info", "system.routing"}]
            return ["system.country_info", "system.routing", *remainder]
        return ordered

    def _scope_capability_groups(
        self,
        *,
        capability_groups: Dict[str, List[str]],
        relevant_skill_ids: List[str],
    ) -> Dict[str, List[str]]:
        allowed = {str(skill_id) for skill_id in (relevant_skill_ids or []) if str(skill_id).strip()}
        if not allowed:
            return dict(capability_groups or {})

        scoped: Dict[str, List[str]] = {}
        for capability, skills in (capability_groups or {}).items():
            selected = [skill for skill in (skills or []) if skill in allowed]
            if selected:
                scoped[str(capability)] = selected
        return scoped

    def _build_planner_prompt(
        self,
        *,
        user_prompt: str,
        capability_groups: Dict[str, List[str]],
        model_profile: Dict[str, Any],
    ) -> str:
        capability_lines = []
        for cap, skills in sorted(capability_groups.items()):
            skill_details = []
            for skill_id in skills:
                metadata = tool_manager.get_skill_metadata(skill_id)
                desc = metadata.description if metadata and metadata.description else "Keine Beschreibung verfügbar."
                skill_details.append(f"{skill_id}: {desc}")
            capability_lines.append(f"- {cap}: {'; '.join(skill_details)}")

        capability_block = "\n".join(capability_lines) if capability_lines else "- (keine Capabilities verfügbar)"
        max_iterations_cap = int(model_profile.get("max_iterations_cap") or 8)
        is_local = bool(model_profile.get("is_local"))
        local_marker = "LOCAL_COMPACT" if is_local else "STANDARD_FULL"
        max_iter_rule = f"- max_iterations zwischen 1 und {max_iterations_cap}."
        compact_rule = (
            "- Sei kompakt und ausgabestabil. Kurze, klare Instructions im JSON sind erlaubt; keine Prosa außerhalb des JSON."
            if is_local
            else "- Erlaube kurze, präzise Instructions im JSON, aber keine Prosa außerhalb des JSON."
        )
        return (
            "Du bist der Janus Agent Planner."
            f"\nPLANNER_MODE: {local_marker}"
            "\nErstelle exakt ein JSON Objekt ohne Markdown mit den Feldern:"
            " name, goal, required_skills, instructions, max_iterations."
            "\nRegeln:"
            "\n- required_skills nur als Skill-IDs (domain.action)."
            "\n- Wähle nur Skills aus den verfügbaren Capability-Gruppen."
            f"\n{max_iter_rule}"
            "\n- Plane sequentiell: pro Iteration nur EIN Skill-Call."
            "\n- Wenn mehrere required_skills geplant sind, setze max_iterations mindestens auf 2."
            "\n- Bei reinem PDF-Erstellen ohne explizite Folge-Aktion plane nur den Erstellungs-Skill und stoppe danach."
            "\n- Nutze für Distanzen/Fahrzeiten IMMER system.routing."
            "\n- Nutze die Websuche nur für Informationen, die nicht berechnet werden können."
            "\n- Für Preisanfragen ('Was kostet', 'Preis', 'teuer', 'kaufen') MUSS system.price_comparison genutzt werden; system.websearch ist hierfür VERBOTEN."
            f"\n{compact_rule}"
            "\n\nUSER-PROMPT:\n"
            f"{user_prompt}\n\n"
            "VERFÜGBARE CAPABILITY-GRUPPEN:\n"
            f"{capability_block}"
        )

    def _build_planner_prompt_v2(
        self,
        user_prompt: str,
        capability_groups: Dict[str, List[str]],
        model_profile: Dict[str, Any],
    ) -> str:
        from .prompting.core.model import OutputContractDirective
        from .prompting.runtime.builder import PromptBuilder

        builder = PromptBuilder()
        builder.add_block("system_role", "Du bist der Janus Agent Planner.", priority=1)

        builder.add_block(
            "grounding_rules",
            "- Wähle nur Skills aus den verfügbaren Capability-Gruppen.\n"
            "- Plane sequentiell: pro Iteration nur EIN Skill-Call.\n"
            "- Für Preisanfragen ('Was kostet', 'Preis', 'teuer', 'kaufen') MUSS system.price_comparison genutzt werden; system.websearch ist hierfür VERBOTEN.",
            priority=2,
        )

        builder.add_block(
            "output_contract",
            OutputContractDirective(
                format="json",
                fields=["name", "goal", "required_skills", "instructions", "max_iterations"],
            ),
            priority=1,
        )

        builder.add_block("user_prompt", f"AUFGABE:\n{user_prompt}", priority=1, required=True)
        
        cap_lines = []
        for cap, skills in sorted(capability_groups.items()):
            skill_details = []
            for skill_id in skills:
                metadata = tool_manager.get_skill_metadata(skill_id)
                desc = metadata.description if metadata and metadata.description else "Keine Beschreibung verfügbar."
                skill_details.append(f"{skill_id}: {desc}")
            cap_lines.append(f"- {cap}: {'; '.join(skill_details)}")

        builder.add_block(
            "user_prompt",
            "VERFÜGBARE SKILLS:\n" + "\n".join(cap_lines),
            priority=8,
        )

        provider_name = model_profile.get("provider", "openai")
        model_name = model_profile.get("model", "gpt-5.4-nano")
        return builder.compile(provider=provider_name, model_id=model_name)

    def _extract_text_payload(self, raw: object) -> str:
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
                    if "name" not in payload:
                        payload["name"] = "Agent"
                    if not payload.get("goal"):
                        payload["goal"] = "Task execution"
                    if not payload.get("instructions"):
                        payload["instructions"] = "Follow the plan."
                    if "required_skills" not in payload:
                        payload["required_skills"] = []
                    if "max_iterations" not in payload:
                        payload["max_iterations"] = 1
                    return payload
            except Exception:
                pass

        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", clean):
            start_idx = match.start()
            try:
                candidate, _end = decoder.raw_decode(clean[start_idx:])
                if isinstance(candidate, dict):
                    return candidate
            except Exception:
                continue

        return {}

    def _heuristic_plan(
        self,
        user_prompt: str,
        capability_groups: Dict[str, List[str]],
        max_iterations_cap: int = 8,
    ) -> AgentSpec:
        lowered = str(user_prompt or "").lower()
        required_skills: List[str] = []

        if self._is_single_goal_pdf_request(lowered):
            available_skills = {
                str(skill).strip()
                for skills in (capability_groups or {}).values()
                for skill in (skills or [])
                if str(skill).strip()
            }
            pdf_skill = self._select_pdf_create_skill(
                available_skills=available_skills,
                planned_skills=[],
            )
            if pdf_skill:
                heuristic_spec = AgentSpec(
                    name="Task-Spezialist",
                    goal=user_prompt,
                    required_skills=[pdf_skill],
                    instructions="Arbeite strikt zielorientiert, nutze nur erforderliche Skills und liefere ein präzises Ergebnis.",
                    max_iterations=1,
                )
                return self._normalize_plan(
                    heuristic_spec,
                    user_prompt=user_prompt,
                    capability_groups=capability_groups,
                    max_iterations_cap=max_iterations_cap,
                )

        # --- C8: PRICE GUARDRAIL (heuristic path) ---
        if self._is_price_query(lowered):
            available_for_price = {
                str(skill).strip()
                for skills in (capability_groups or {}).values()
                for skill in (skills or [])
                if str(skill).strip()
            }
            price_skill = "system.price_comparison"
            if not available_for_price or price_skill in available_for_price:
                logger.info("AGENT-PLANNER: Price-Guardrail (heuristic) aktiv – system.price_comparison erzwungen")
                return AgentSpec(
                    name="Preis-Spezialist",
                    goal=user_prompt,
                    required_skills=[price_skill],
                    instructions="Rufe ausschlie\u00dflich system.price_comparison auf. system.websearch ist f\u00fcr diese Anfrage verboten.",
                    max_iterations=1,
                )

        if self._is_routing_prompt(lowered):
            required_skills.append("system.routing")
        if intent_classifier.is_country_info_intent(lowered) and not intent_classifier.is_generic_country_prompt(lowered):
            required_skills.append("system.country_info")
        required_skills = self._prioritize_geo_sequence(required_skills)
        if not required_skills and any(token in lowered for token in ["dokument", "pdf", "suche", "kairo"]):
            required_skills.append("knowledge.query")
        if not required_skills and any(token in lowered for token in ["erstelle", "datei", "textdatei", "speichere"]):
            required_skills.append("filesystem.create_file")
        if (
            not required_skills
            and "filesystem.list_directory" not in required_skills
            and any(token in lowered for token in ["durchsuche", "ordner"])
        ):
            required_skills.append("filesystem.list_directory")

        if not required_skills:
            # fallback: choose first skills from available capabilities
            for skills in capability_groups.values():
                for skill in skills:
                    required_skills.append(skill)
                    if len(required_skills) >= 2:
                        break
                if len(required_skills) >= 2:
                    break

        heuristic_spec = AgentSpec(
            name="Task-Spezialist",
            goal=user_prompt,
            required_skills=required_skills,
            instructions="Arbeite strikt zielorientiert, nutze nur erforderliche Skills und liefere ein präzises Ergebnis.",
            max_iterations=max(1, min(5, int(max_iterations_cap or 5))),
        )
        return self._normalize_plan(
            heuristic_spec,
            user_prompt=user_prompt,
            capability_groups=capability_groups,
            max_iterations_cap=max_iterations_cap,
        )

    def _resolve_model_profile(self, *, provider: str, model: str) -> Dict[str, Any]:
        provider_key = str(provider or "").strip().lower()
        model_name = str(model or "").strip().lower()
        is_local = provider_key == "ollama" or ":" in model_name

        high_reasoning_markers = ["gpt-5", "gpt-4o", "gemini-3-pro", "gemini-2.5-pro", "27b", "70b", "72b", "mixtral"]
        medium_reasoning_markers = ["gemini-3-flash", "gpt-5-nano", "14b", "12b", "9b", "8b", "llama3.1"]

        capability = "base"
        if any(marker in model_name for marker in high_reasoning_markers):
            capability = "high"
        elif any(marker in model_name for marker in medium_reasoning_markers):
            capability = "medium"

        if not model_name:
            default_model = self.model_hierarchy.get(provider_key, {}).get("logic") or ""
            model_name = str(default_model).lower()

        if is_local:
            cap_map = {"high": 6, "medium": 4, "base": 4}
        else:
            cap_map = {"high": 8, "medium": 8, "base": 6}

        return {
            "provider": provider_key,
            "model": model_name,
            "is_local": is_local,
            "capability": capability,
            "max_iterations_cap": cap_map.get(capability, 4),
        }

    @staticmethod
    def _is_lockdown_prompt(prompt: str) -> bool:
        return "LOCKDOWN_MODE: CREATE_PDF_DONE" in str(prompt or "")

    @staticmethod
    def _is_pdf_create_skill(skill_id: str) -> bool:
        normalized = str(skill_id or "").strip().lower()
        return normalized in {"system.create_pdf", "create_pdf", "knowledge.create_pdf"}

    def _select_pdf_create_skill(self, *, available_skills: set[str], planned_skills: List[str]) -> str:
        preferred = ["system.create_pdf", "create_pdf", "knowledge.create_pdf"]
        for skill_id in preferred:
            if available_skills and skill_id in available_skills:
                return skill_id
        for skill_id in planned_skills:
            if self._is_pdf_create_skill(skill_id):
                return str(skill_id).strip()
        if not available_skills:
            return "system.create_pdf"
        return ""

    @staticmethod
    def _is_single_goal_pdf_request(prompt_lower: str) -> bool:
        text = str(prompt_lower or "")
        wants_pdf = (
            any(token in text for token in ["pdf", "dokument"])
            and any(token in text for token in ["erstelle", "erstelle", "create", "generiere", "schreibe"])
        )
        if not wants_pdf:
            return False

        explicit_followup_tokens = [
            "lies",
            "lesen",
            "read",
            "oeffne",
            "öffne",
            "open",
            "bearbeite",
            "edit",
            "aendere",
            "ändere",
            "modif",
            "korrig",
            "analys",
            "durchsuche",
        ]
        return not any(token in text for token in explicit_followup_tokens)
