import logging
import json
import os
import asyncio
import re
import time
import uuid
import keyring
from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass

from backend.services.vision_helper import analyze_image_strict_provider, analyze_image_with_cloud
from backend.services.vision_service import vision_service
from backend.services.vision.profiles import openai_profile, gemini_profile

from sqlalchemy.orm import Session

from backend.data import crud, schemas
from backend.data.models import Message
from backend.services import cost_service
from backend.services.agent_planner import AgentPlanner
from backend.services.agent_runtime import AgentRuntime
from backend.services.skill_selector import SkillSelector
from backend.services.context_manager import ContextManager
from backend.services.tool_executor import ToolExecutor
from backend.services.chat.tool_selector import ToolSelector
from backend.services.chat.context_builder import ContextBuilder
from backend.services.orchestrator.context_manager import OrchestratorContextManager
from backend.services.orchestrator.execution_engine import OrchestratorExecutionEngine
from backend.services.orchestrator.chat_request_workflow_state import ChatRequestWorkflowState
from backend.services.orchestrator.live_portrait_pipeline import (
    _AMBIENTE_CONFIDENCE_THRESHOLD,
    _apply_plugin_confidence_gates,
    _build_enriched_reporter_facts,
    _build_live_slot_fact_block,
    process_visual_content as _process_visual_content_pipeline,
)
from backend.services.orchestrator.prompt_directives import DIRECTIVES, PromptDirective
from backend.services.orchestrator.meta_agent_pipeline import (
    build_meta_phase2_json_only_prompt as _build_meta_phase2_json_only_prompt_pipeline,
    build_meta_pdf_failure_message as _build_meta_pdf_failure_message_pipeline,
    build_meta_pdf_markdown_content as _build_meta_pdf_markdown_content_pipeline,
    build_meta_pdf_success_message as _build_meta_pdf_success_message_pipeline,
    build_meta_production_prompt as _build_meta_production_prompt_pipeline,
    build_meta_research_prompt as _build_meta_research_prompt_pipeline,
    collect_meta_requested_sections as _collect_meta_requested_sections_pipeline,
    collect_meta_topic_instructions as _collect_meta_topic_instructions_pipeline,
    extract_requested_pdf_filename as _extract_requested_pdf_filename_pipeline,
    extract_pdf_paths_from_text as _extract_pdf_paths_from_text_pipeline,
    extract_phase2_synopsis as _extract_phase2_synopsis_pipeline,
    run_meta_agent_direct_pdf_generation as _run_meta_agent_direct_pdf_generation_pipeline,
    run_meta_agent_production_fallback as _run_meta_agent_production_fallback_pipeline,
    run_meta_agent_research_fallback as _run_meta_agent_research_fallback_pipeline,
    has_meta_topic_coverage_gaps as _has_meta_topic_coverage_gaps_pipeline,
    is_meta_phase1_facts_weak as _is_meta_phase1_facts_weak_pipeline,
    meta_phase1_missing_research_skills as _meta_phase1_missing_research_skills_pipeline,
    normalize_meta_facts as _normalize_meta_facts_pipeline,
)
from backend.services.orchestrator.storybook_pipeline import run_storybook_macro as _run_storybook_macro_pipeline
from backend.services.orchestrator.status_sync import OrchestratorStatusSync
from backend.services.orchestrator.schemas import AuditContext, ExecutionResponse
from backend.services.orchestrator.intent_engine import intent_engine, META_TOPIC_INSTRUCTION_MAP
from backend.services.capability_registry import CapabilityRegistry, get_resource_path
from backend.services.help_skill import create_help_skill
from backend.services.orchestrator.intercept_handler import apply_image_intent_skill_guardrails, handle_local_requests
from backend.services.orchestrator.policy_handler import handle_policy_consent_phase
from backend.services.orchestrator.prompt_registry import apply_verbosity_control, prompt_registry
from backend.services.orchestrator.identity_manager import identity_manager
from backend.data.schemas import ExtractedFact
from backend.services.vision.utils import fuse_vision_results, clean_for_chat
from backend.utils import intent_classifier
from backend.utils.config_loader import initialize_file_from_template, load_config_data, save_config_data

logger = logging.getLogger("janus_backend")


# ═══════════════════════════════════════════════════════════════════════════════
# Diamond: Intent Detection Delegation
# ═══════════════════════════════════════════════════════════════════════════════
# Alle Intent-Erkennungen sind nun in intent_engine.py zentralisiert.
# Legacy-Wrapper für kompatibles Verhalten:
# ═══════════════════════════════════════════════════════════════════════════════

def _is_fact_telling_pattern(user_text: str) -> bool:
    """BUG-SYS-019: Delegiert an IntentEngine."""
    return intent_engine.is_fact_telling_pattern(user_text)


def apply_directives(memory_context_string: str, directives: List[PromptDirective]) -> List[PromptDirective]:
    active: List[PromptDirective] = []
    context = str(memory_context_string or "")
    for directive in directives:
        try:
            if directive.detector(context):
                active.append(directive)
        except Exception:
            logger.warning("DIRECTIVE detector failed: %s", directive.name, exc_info=True)
    return active


_ENABLE_STRICT_LITERAL_BACKFILL = str(os.getenv("JANUS_ENABLE_STRICT_LITERAL_BACKFILL", "1")).strip().lower() in {"1", "true", "yes", "on"}
_USE_FULL_FACTS_IN_LIVE_REPORTER = str(os.getenv("JANUS_USE_FULL_FACTS_IN_LIVE_REPORTER", "1")).strip().lower() in {"1", "true", "yes", "on"}
_ENABLE_DETERMINISTIC_LIVE_REPORTER = str(os.getenv("JANUS_ENABLE_DETERMINISTIC_LIVE_REPORTER", "1")).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_exclusion_terms(terms: Any) -> List[str]:
    if not isinstance(terms, list):
        return []

    normalized: List[str] = []
    for raw_term in terms:
        term = str(raw_term or "").strip().lower()
        if not term:
            continue
        term = re.sub(r"^kein(?:e|en|em|er)?\s+", "", term)
        term = re.sub(r"^keine\s+", "", term)
        term = term.strip()
        if term:
            normalized.append(term)
    return normalized


def _sanitize_value_by_exclusions(value: Any, normalized_exclusions: List[str]) -> Any:
    if not normalized_exclusions:
        return value
    if isinstance(value, dict):
        return {k: _sanitize_value_by_exclusions(v, normalized_exclusions) for k, v in value.items()}
    if isinstance(value, list):
        cleaned_list = []
        for item in value:
            cleaned_item = _sanitize_value_by_exclusions(item, normalized_exclusions)
            if isinstance(cleaned_item, str) and not cleaned_item.strip():
                continue
            cleaned_list.append(cleaned_item)
        return cleaned_list
    if isinstance(value, str):
        text = value
        lowered = text.lower()
        if any(token in lowered for token in normalized_exclusions):
            return ""
        return text
    return value




def _is_policy_consent_choice(user_text_clean: str) -> bool:
    """Delegiert an IntentEngine."""
    return intent_engine.is_policy_consent_choice(user_text_clean)


def _is_one_time_policy_choice(user_text_clean: str) -> bool:
    """Delegiert an IntentEngine."""
    return intent_engine.is_one_time_policy_choice(user_text_clean)


def _is_policy_prompt_text(text: str) -> bool:
    """Delegiert an IntentEngine."""
    return intent_engine.is_policy_prompt_text(text)





























@dataclass
class RequestContext:
    """Per-request context for phased handle_chat_request."""
    request: schemas.ChatRequest
    background_tasks: Optional[Any] = None
    identity_fact: Any = None
    selected_slots: Optional[List[Any]] = None
    memory_context_string: str = ""
    formatted_fact_coupons: str = ""
    workflow: Any = None
    final_response: str = ""


class ChatOrchestrator:
    """
    Diamond ChatOrchestrator - Reine Steuerzentrale (Dirigent).
    
    Alle Intent-Erkennungen, Identity-Logik und Keyword-Listen sind
    in dedizierte Services (intent_engine, identity_manager) ausgelagert.
    """
    # KLASSEN-VARIABLE (Global für alle Instanzen / Nachrichten)
    FACTCHECK_PROMPT_PENDING: set[int] = set()
    # Meta-Agent Topic-Keywords: dieselbe Quelle wie intent_engine (Single Source of Truth)
    META_TOPIC_INSTRUCTION_MAP = META_TOPIC_INSTRUCTION_MAP

    @staticmethod
    def _is_name_mentioned_in_current_stm(chat_history: List[Message]) -> bool:
        """
        Diamond: Delegiert an IdentityManager.
        Check if user mentioned their name in recent messages.
        """
        return identity_manager.is_name_mentioned_in_history(chat_history)

    @staticmethod
    def _extract_realtime_identity_name(user_text: str) -> Optional[str]:
        """
        Diamond: Delegiert an IdentityManager.
        Rolf-Bug Fix: Extract user name from the CURRENT message.
        """
        return identity_manager.extract_realtime_identity_name(user_text)

    MODEL_HIERARCHY = {
        "openai": {
            "vision": "gpt-4o",
            "logic": "gpt-5.4",
            "speed": "gpt-5.4-nano",
            "balanced": "gpt-5.4-mini",
        },
        "gemini": {
            "vision": "gemini-3-flash-preview",
            "logic": "gemini-3-pro-preview",
            "speed": "gemini-3-flash-preview",
            "balanced": "gemini-3-flash-preview",
        },
        "ollama": {
            "vision": "llava",
            "logic": "llama3.1:8b",
            "speed": "llama3.1:8b",
            "fast": "llama3.1:8b",
            "balanced": "qwen2.5:14b",
        },
    }
    META_RESEARCH_PROMPT_MAX_TOKENS = 140
    META_PHASE2_FACTS_MAX_TOKENS = 280
    META_PHASE2_REQUEST_FALLBACK_MAX_TOKENS = 180
    META_PHASE2_REQUIREMENTS_MAX_TOKENS = 220
    META_PROVIDER_PROFILE_DEFAULT = {
        "phase1_max_tokens": META_RESEARCH_PROMPT_MAX_TOKENS,
        "phase2_facts_max_tokens": META_PHASE2_FACTS_MAX_TOKENS,
        "phase2_request_fallback_max_tokens": META_PHASE2_REQUEST_FALLBACK_MAX_TOKENS,
        "phase2_requirements_max_tokens": META_PHASE2_REQUIREMENTS_MAX_TOKENS,
        "phase2_allow_planner": True,
    }
    META_PROVIDER_PROFILES = {
        "ollama": {
            "phase1_max_tokens": 140,
            "phase2_facts_max_tokens": 280,
            "phase2_request_fallback_max_tokens": 180,
            "phase2_requirements_max_tokens": 220,
            "phase2_allow_planner": True,
        },
        "gemini": {
            "phase1_max_tokens": 120,
            "phase2_facts_max_tokens": 240,
            "phase2_request_fallback_max_tokens": 150,
            "phase2_requirements_max_tokens": 190,
            "phase2_allow_planner": False,
        },
        "openai": {
            "phase1_max_tokens": 130,
            "phase2_facts_max_tokens": 220,
            "phase2_request_fallback_max_tokens": 160,
            "phase2_requirements_max_tokens": 200,
            "phase2_allow_planner": True,
        },
    }
    META_SCANDINAVIA_COUNTRY_TARGETS: List[Tuple[str, str]] = [
        ("Schweden", "Stockholm"),
        ("Norwegen", "Oslo"),
        ("Dänemark", "Kopenhagen"),
        ("Finnland", "Helsinki"),
        ("Island", "Reykjavik"),
    ]

    def __init__(
        self,
        *,
        db: Session,
        context_manager: ContextManager,
        model_catalog: Any,
        config_file_path: str,
        template_config_file_path: str,
        personalities_file_path: str,
        template_personalities_file_path: str,
    ):
        self.db = db
        self.context_manager = context_manager
        self.model_catalog = model_catalog
        self.config_file_path = config_file_path
        self.template_config_file_path = template_config_file_path
        self.personalities_file_path = personalities_file_path
        self.template_personalities_file_path = template_personalities_file_path

        self.tool_selector = ToolSelector()
        self.context_builder = ContextBuilder(db)
        self.orchestrator_context = OrchestratorContextManager(db)
        self.status_sync = OrchestratorStatusSync(db)
        # Help System + CapabilityRegistry (FEAT-HELP-001) — vor SkillSelector, damit
        # get_relevant_skills nur Registry-validierte Skill-Refs sieht (keine DOMAIN_KEYWORDS).
        registry_path = get_resource_path("backend/data/capability_registry.json")
        skills_dir = get_resource_path("backend/skills")
        self.capability_registry = CapabilityRegistry(registry_path, skills_dir)
        self.capability_registry.load()
        self.help_skill = create_help_skill(self.capability_registry)
        self.skill_selector = SkillSelector(capability_registry=self.capability_registry)
        self.agent_planner = AgentPlanner(model_hierarchy=self.MODEL_HIERARCHY)
        self.agent_runtime = AgentRuntime(db=db, context_manager=context_manager)
        self.execution_engine = OrchestratorExecutionEngine(
            db=db,
            context_manager=context_manager,
            model_hierarchy=self.MODEL_HIERARCHY,
            agent_planner=self.agent_planner,
            agent_runtime=self.agent_runtime,
            skill_selector=self.skill_selector,
            capability_registry=self.capability_registry,
        )
        self._policy_pending_data: Dict[int, Optional[Dict[str, Any]]] = {}

    def _get_policy_pending_data(self, chat_id: Optional[int]) -> Optional[Dict[str, Any]]:
        if chat_id is None:
            return None
        value = self._policy_pending_data.get(int(chat_id))
        return value if isinstance(value, dict) else None

    def _set_policy_pending_data(self, chat_id: Optional[int], payload: Optional[Dict[str, Any]]) -> None:
        if chat_id is None:
            return
        key = int(chat_id)
        if payload is None:
            self._policy_pending_data.pop(key, None)
            return
        self._policy_pending_data[key] = dict(payload)

    def _set_policy_pending(self, chat_id: Optional[int], enabled: bool) -> None:
        if chat_id is None:
            return
        key = int(chat_id)
        if enabled:
            self._policy_pending_data.setdefault(key, {"pending": True})
        else:
            existing = self._policy_pending_data.get(key)
            if isinstance(existing, dict) and existing.get("blocked_skill_id"):
                updated = dict(existing)
                updated["pending"] = False
                self._policy_pending_data[key] = updated
            else:
                self._policy_pending_data.pop(key, None)

    def _load_config(self) -> Dict[str, Any]:
        initialize_file_from_template(self.template_config_file_path, self.config_file_path)
        try:
            config = load_config_data()
        except Exception:
            logger.error("CONFIG LOAD failed, using empty fallback", exc_info=True)
            config = {}
        return dict(config or {})

    def _load_active_personality(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        initialize_file_from_template(self.template_personalities_file_path, self.personalities_file_path)
        config_data = dict(config or {})
        active_id = str(config_data.get("active_personality") or "ai_assistant").strip() or "ai_assistant"
        personalities: List[Dict[str, Any]] = []
        try:
            with open(self.personalities_file_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    personalities = [item for item in loaded if isinstance(item, dict)]
        except Exception:
            logger.error("PERSONALITIES LOAD failed, trying template fallback", exc_info=True)

        if not personalities:
            try:
                with open(self.template_personalities_file_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, list):
                        personalities = [item for item in loaded if isinstance(item, dict)]
            except Exception:
                logger.error("PERSONALITIES TEMPLATE LOAD failed", exc_info=True)

        active = next((item for item in personalities if str(item.get("id") or "").strip() == active_id), None)
        if active is None:
            active = next((item for item in personalities if str(item.get("id") or "").strip()), None)
        if active is None:
            active = {
                "id": "ai_assistant",
                "prompt": prompt_registry.get_directive("personality_fallback_prompt"),
            }

        if str(active.get("id") or "").strip() != active_id:
            config_data["active_personality"] = str(active.get("id") or "ai_assistant").strip() or "ai_assistant"
            try:
                save_config_data(config_data)
            except Exception:
                logger.error("CONFIG SAVE failed while normalizing active personality", exc_info=True)

        return dict(active)

    @staticmethod
    def _extract_tool_result_payload(tool_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(tool_result, dict):
            return {}
        content = tool_result.get("content")
        if isinstance(content, dict):
            return dict(content)
        raw = str(content or "").strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {
                "status": "error",
                "error": {"message": raw},
            }

    @staticmethod
    def _build_policy_resume_text(payload: Optional[Dict[str, Any]], blocked_skill_id: str, mode: str) -> str:
        payload_dict = payload if isinstance(payload, dict) else {}
        status = str(payload_dict.get("status") or "").strip().lower()
        data = payload_dict.get("data") if isinstance(payload_dict.get("data"), dict) else {}
        error = payload_dict.get("error") if isinstance(payload_dict.get("error"), dict) else {}
        skill_label = str(blocked_skill_id or "Aktion").strip() or "Aktion"

        if status == "ok":
            text = str(data.get("message") or data.get("text") or "").strip()
            if text:
                return text
            if mode == "grant":
                return f"Freigabe für `{skill_label}` erteilt und Aktion erfolgreich ausgeführt."
            return f"Aktion `{skill_label}` erfolgreich ausgeführt."

        error_message = str(error.get("message") or payload_dict.get("message") or "").strip()
        if error_message:
            if mode == "grant":
                return f"Freigabe für `{skill_label}` wurde verarbeitet, aber die Aktion ist fehlgeschlagen: {error_message}"
            return f"Aktion `{skill_label}` konnte nicht ausgeführt werden: {error_message}"

        if mode == "grant":
            return f"Freigabe für `{skill_label}` wurde verarbeitet, aber es liegt kein verwertbares Ergebnis vor."
        return f"Aktion `{skill_label}` lieferte kein verwertbares Ergebnis."

    async def _process_visual_content(
        self,
        content: Optional[List[Any]],
        provider: str,
        profile: Any,
        image_name_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await _process_visual_content_pipeline(
            self.db,
            content,
            provider,
            profile,
            image_name_hint,
        )

    @staticmethod
    def _is_large_local_model(model_name: str) -> bool:
        normalized = str(model_name or "").strip().lower()
        if not normalized:
            return False
        if "gemma2" in normalized or "gemma-2" in normalized:
            return True
        size_match = re.search(r"(\d+(?:\.\d+)?)\s*b\b", normalized)
        if not size_match:
            return False
        try:
            return float(size_match.group(1)) >= 20.0
        except Exception:
            return False

    def _resolve_help_intent(self, intents) -> Optional[str]:
        """Resolve Help intent type from IntentDetectionResult.

        Priority: model_query > capability_overview > how_to > navigation
        Returns None if no help intent is detected.

        Args:
            intents: IntentDetectionResult from intent_engine.detect_all_intents

        Returns:
            One of "model_query", "capability_overview", "how_to", "navigation", or None.
        """
        if intents.is_model_query:
            return "model_query"
        if intents.is_capability_overview:
            return "capability_overview"
        if intents.is_how_to:
            return "how_to"
        if intents.is_navigation_query:
            return "navigation"
        return None

    def _get_provider_from_model(self, model: str) -> Optional[str]:
        """Detect provider from model name prefix/pattern.

        Args:
            model: Model name (e.g., "gpt-5.4-trinity-logic", "gemini-3").

        Returns:
            Provider ID (e.g., "openai", "gemini", "anthropic", "ollama") or None.
        """
        if not model:
            return None

        model_lower = str(model).strip().lower()

        if model_lower.startswith("gpt-"):
            return "openai"
        elif model_lower.startswith("gemini-"):
            return "gemini"
        elif model_lower.startswith("claude-"):
            return "anthropic"
        elif ":" in model_lower or model_lower.startswith("llama") or model_lower.startswith("llava"):
            return "ollama"

        return None

    @staticmethod
    def _should_force_direct_meta_pdf_generation(model_name: str) -> bool:
        normalized = str(model_name or "").strip().lower()
        return "mistral-nemo" in normalized or "mistral nemo" in normalized

    @staticmethod
    def _truncate_for_token_budget(text: str, max_tokens: int | None = None) -> str:
        if max_tokens <= 0:
            return ""
        raw = str(text or "").strip()
        if not raw:
            return ""
        tokens = raw.split()
        if len(tokens) <= max_tokens:
            return raw
        return " ".join(tokens[:max_tokens])

    @classmethod
    def _get_meta_provider_profile(cls, provider: str) -> Dict[str, Any]:
        key = str(provider or "").strip().lower()
        profile = cls.META_PROVIDER_PROFILES.get(key) or cls.META_PROVIDER_PROFILE_DEFAULT
        return dict(profile)

    @staticmethod
    def _prompt_role_from_db_role(db_role: str) -> str:
        """Map stored DB roles to prompt roles without lossy legacy aliases."""
        return "assistant" if str(db_role or "").strip().lower() == "assistant" else "user"

    @staticmethod
    def is_complex_document_request(prompt: str) -> bool:
        """Diamond: Delegiert an IntentEngine."""
        return intent_engine.detect_complex_document_request(prompt)

    @classmethod
    def _collect_meta_topic_instructions(cls, prompt_text: str) -> List[str]:
        return _collect_meta_topic_instructions_pipeline(cls, prompt_text)

    @staticmethod
    def _build_meta_research_prompt(prompt: str, max_tokens: int | None = None) -> str:
        return _build_meta_research_prompt_pipeline(ChatOrchestrator, prompt, max_tokens)

    @staticmethod
    def _build_meta_production_prompt(research_output: str) -> str:
        return _build_meta_production_prompt_pipeline(research_output)

    @staticmethod
    def _extract_requested_pdf_filename(prompt: str) -> str:
        return _extract_requested_pdf_filename_pipeline(prompt)

    @classmethod
    def _build_meta_phase2_json_only_prompt(
        cls,
        phase1_context: str,
        requested_filename: str = "",
        original_user_text: str = "",
        meta_profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        return _build_meta_phase2_json_only_prompt_pipeline(
            cls,
            phase1_context,
            requested_filename=requested_filename,
            original_user_text=original_user_text,
            meta_profile=meta_profile,
        )

    @staticmethod
    def _is_meta_phase1_facts_weak(facts: List[str]) -> bool:
        return _is_meta_phase1_facts_weak_pipeline(facts)

    @classmethod
    def _collect_meta_requested_sections(cls, prompt_text: str) -> List[str]:
        return _collect_meta_requested_sections_pipeline(cls, prompt_text)

    @classmethod
    def _has_meta_topic_coverage_gaps(cls, facts: List[str], prompt_text: str) -> bool:
        return _has_meta_topic_coverage_gaps_pipeline(cls, facts, prompt_text)

    @staticmethod
    def _extract_pdf_paths_from_text(text: str) -> List[str]:
        return _extract_pdf_paths_from_text_pipeline(text)

    @staticmethod
    def _normalize_meta_facts(phase1_context: str) -> List[str]:
        return _normalize_meta_facts_pipeline(phase1_context)

    @classmethod
    def _build_meta_pdf_success_message(cls, *, phase1_context: str, phase2_text: str) -> str:
        return _build_meta_pdf_success_message_pipeline(
            phase1_context=phase1_context,
            phase2_text=phase2_text,
        )

    @staticmethod
    def _extract_phase2_synopsis(text: str) -> List[str]:
        return _extract_phase2_synopsis_pipeline(text)

    @classmethod
    def _build_meta_pdf_failure_message(cls, *, phase1_context: str) -> str:
        return _build_meta_pdf_failure_message_pipeline(phase1_context=phase1_context)

    @classmethod
    def _build_meta_pdf_markdown_content(cls, *, phase1_context: str, original_user_text: str) -> str:
        return _build_meta_pdf_markdown_content_pipeline(
            cls,
            phase1_context=phase1_context,
            original_user_text=original_user_text,
        )

    async def _run_meta_agent_direct_pdf_generation(
        self,
        *,
        phase1_context: str,
        requested_filename: str,
        original_user_text: str,
        request: schemas.ChatRequest,
        api_key: str,
    ) -> ExecutionResponse:
        return await _run_meta_agent_direct_pdf_generation_pipeline(
            self,
            phase1_context=phase1_context,
            requested_filename=requested_filename,
            original_user_text=original_user_text,
            request=request,
            api_key=api_key,
        )

    @staticmethod
    def _meta_phase1_missing_research_skills(execution: Optional[ExecutionResponse]) -> bool:
        return _meta_phase1_missing_research_skills_pipeline(execution)

    @staticmethod
    def _should_force_scandinavia_country_coverage(user_text: str) -> bool:
        prompt = str(user_text or "").lower()
        if not prompt:
            return False
        if "skandinav" in prompt:
            return True
        capital_hits = [
            name
            for name in ["stockholm", "oslo", "kopenhagen", "helsinki", "reykjavik"]
            if name in prompt
        ]
        return len(capital_hits) >= 3

    @staticmethod
    def _format_population(value: Any) -> str:
        try:
            amount = int(value)
        except Exception:
            return str(value or "n/a")
        return f"{amount:,}".replace(",", ".")

    @staticmethod
    def _country_query_candidates(country_name: str) -> List[str]:
        normalized = str(country_name or "").strip()
        alias_map = {
            "Schweden": ["Schweden", "Sweden"],
            "Norwegen": ["Norwegen", "Norway"],
            "Dänemark": ["Dänemark", "Daenemark", "Denmark"],
            "Finnland": ["Finnland", "Finland"],
            "Island": ["Island", "Iceland"],
        }
        candidates = alias_map.get(normalized)
        if candidates:
            return candidates
        return [normalized] if normalized else []

    @staticmethod
    def _normalize_geo_name(value: str) -> str:
        normalized = str(value or "").strip().lower()
        normalized = (
            normalized.replace("ä", "ae")
            .replace("ö", "oe")
            .replace("ü", "ue")
            .replace("ß", "ss")
            .replace("å", "a")
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
        )
        return re.sub(r"[^a-z0-9]+", "", normalized)

    @classmethod
    def _capital_matches_expected(cls, *, actual_capital: str, expected_capital: str) -> bool:
        expected_norm = cls._normalize_geo_name(expected_capital)
        actual_norm = cls._normalize_geo_name(actual_capital)
        if not expected_norm:
            return True
        if not actual_norm:
            return False
        variant_map = {
            "kopenhagen": {"copenhagen"},
            "reykjavik": {"reykjavik"},
        }
        allowed = {expected_norm}
        allowed.update(variant_map.get(expected_norm, set()))
        return actual_norm in allowed

    async def _collect_scandinavia_country_facts(
        self,
        *,
        request: schemas.ChatRequest,
        api_key: str,
    ) -> List[str]:
        facts: List[str] = []
        for country, expected_capital in self.META_SCANDINAVIA_COUNTRY_TARGETS:
            resolved_line = ""
            for query_country in self._country_query_candidates(country):
                executor = ToolExecutor(
                    db=self.db,
                    api_key=api_key,
                    provider=request.provider,
                    model=request.model,
                    additional_context={
                        "chat_id": request.chat_id,
                        "trace_id": str(uuid.uuid4()),
                        "allowed_skill_ids": ["system.country_info"],
                        "provider": request.provider,
                        "model": request.model,
                    },
                )
                tool_call = {
                    "id": f"meta-country-{self._normalize_geo_name(country)}-{self._normalize_geo_name(query_country)}",
                    "function": {
                        "name": "system.country_info",
                        "arguments": json.dumps({"country": query_country, "language": "de"}, ensure_ascii=False),
                    },
                }
                try:
                    results = await executor.execute_tool_calls([tool_call])
                except Exception:
                    logger.warning(
                        "META-AGENT PHASE 1: Deterministischer country_info-Aufruf fehlgeschlagen (%s).",
                        query_country,
                        exc_info=True,
                    )
                    continue
                if not results:
                    continue
                raw_content = str((results[0] or {}).get("content") or "")
                try:
                    payload = json.loads(raw_content)
                except Exception:
                    payload = {}
                if not isinstance(payload, dict) or payload.get("status") != "ok":
                    continue
                data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
                country_name = str(data.get("name") or country)
                capital = str(data.get("capital") or expected_capital or "n/a")
                if not self._capital_matches_expected(actual_capital=capital, expected_capital=expected_capital):
                    logger.warning(
                        "META-AGENT PHASE 1: country_info-Mismatch fuer %s (query=%s, capital=%s).",
                        country,
                        query_country,
                        capital,
                    )
                    continue
                population = self._format_population(data.get("population"))
                region = str(data.get("region") or "n/a")
                resolved_line = (
                    f"[system.country_info] {country_name}: Hauptstadt {capital}, "
                    f"Einwohner ca. {population}, Region {region}."
                )
                break
            if resolved_line and resolved_line not in facts:
                facts.append(resolved_line)
            elif not resolved_line:
                logger.warning(
                    "META-AGENT PHASE 1: Keine belastbaren country_info-Daten fuer %s gefunden.",
                    country,
                )
        if facts:
            logger.info(
                "META-AGENT PHASE 1: Deterministische country_info-Anreicherung aktiv (facts=%s).",
                len(facts),
            )
        return facts

    async def _run_meta_agent_research_fallback(
        self,
        *,
        user_text: str,
        request: schemas.ChatRequest,
        api_key: str,
        skip_final_synthesis: bool = False,
        meta_profile: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResponse:
        return await _run_meta_agent_research_fallback_pipeline(
            self,
            user_text=user_text,
            request=request,
            api_key=api_key,
            skip_final_synthesis=skip_final_synthesis,
            meta_profile=meta_profile,
        )

    async def _run_meta_agent_production_fallback(
        self,
        *,
        phase1_context: str,
        requested_filename: str,
        original_user_text: str,
        request: schemas.ChatRequest,
        api_key: str,
        meta_profile: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResponse:
        return await _run_meta_agent_production_fallback_pipeline(
            self,
            phase1_context=phase1_context,
            requested_filename=requested_filename,
            original_user_text=original_user_text,
            request=request,
            api_key=api_key,
            meta_profile=meta_profile,
        )

    def _resolve_audit_filename(self, chat_id: Optional[int], messages: List[str]) -> str:
        return self.orchestrator_context.resolve_audit_filename(chat_id, messages)

    def _persist_orchestrator_kpi(
        self,
        *,
        provider: str,
        model: Optional[str],
        chat_id: Optional[int],
        is_meta_agent_run: bool,
        t_phase1_research_ms: Optional[float],
        t_phase2_pdf_ms: Optional[float],
        t_final_response_ms: float,
        retry_path: str,
        retry_count: int,
        success: bool,
        error_code: Optional[str],
    ) -> None:
        try:
            crud.create_orchestrator_kpi(
                self.db,
                provider=provider,
                model=model,
                chat_id=chat_id,
                is_meta_agent_run=is_meta_agent_run,
                t_phase1_research_ms=t_phase1_research_ms,
                t_phase2_pdf_ms=t_phase2_pdf_ms,
                t_final_response_ms=t_final_response_ms,
                retry_path=retry_path,
                retry_count=retry_count,
                success=success,
                error_code=error_code,
            )
        except Exception:
            logger.warning("ORCHESTRATOR KPI persist failed", exc_info=True)

    def _get_recent_memories_raw(self, limit: int = 20, exclude_vision_for_unknown: bool = False) -> List[ExtractedFact]:
        return self.orchestrator_context.get_recent_memories_raw(
            limit=limit,
            exclude_vision_for_unknown=exclude_vision_for_unknown,
        )

    def _save_cost_from_response(self, response: Dict, model: str, provider: str, source_type: str):
        """Extracts cost and usage from LLM response and saves it to the database."""
        if "cost" in response and "usage" in response:
            try:
                cost_data = response["cost"]
                usage_data = response["usage"]
                cost_service.create_cost_entry(
                    db=self.db,
                    amount=cost_data.get("total_cost", 0.0),
                    model=model,
                    provider=provider,
                    source_type=source_type,
                    input_tokens=usage_data.get("prompt_tokens", 0) or usage_data.get("input_tokens", 0),
                    output_tokens=usage_data.get("completion_tokens", 0) or usage_data.get("output_tokens", 0)
                )
            except Exception as e:
                logger.error(f"Failed to save cost entry: {e}")



    async def _run_storybook_macro(self, user_prompt: str, request: schemas.ChatRequest, api_key: str) -> ExecutionResponse:
        return await _run_storybook_macro_pipeline(self.db, user_prompt, request, api_key)

    def _classify_request(self, request: schemas.ChatRequest, background_tasks: Any = None) -> RequestContext:
        ctx = RequestContext(request=request, background_tasks=background_tasks)
        ctx.workflow = ChatRequestWorkflowState()
        wf = ctx.workflow
        request = ctx.request
        wf.orchestrator_context = self.orchestrator_context.assemble_history(
            chat_id=request.chat_id,
            role_mapper=self._prompt_role_from_db_role,
            limit=8,
        )
        wf.request_started_at = time.perf_counter()
        wf.kpi_phase1_started_at = None
        wf.kpi_phase2_started_at = None
        wf.kpi_phase1_research_ms = None
        wf.kpi_phase2_pdf_ms = None
        wf.kpi_retry_paths = []
        wf.kpi_success = True
        wf.kpi_error_code = None
        wf.bypass_policy_this_turn = False
        wf.is_policy_response = False
        wf.is_meta_agent_run = False
        wf.planner_prefers_agent = False
        logger.info('ORCHESTRATOR START (Goldstandard-Architektur)')
        from backend.services.memory_identity import load_identity_slot as _load_identity
        wf._identity = _load_identity(self.db)
        wf.user_text = request.prompt or (request.content[0].text if request.content and request.content[0].type == 'text' else '')
        wf._identity_from_current_msg = False
        if wf._identity.name is None:
            wf._realtime_name = ChatOrchestrator._extract_realtime_identity_name(wf.user_text)
            if wf._realtime_name:
                wf._identity.name = wf._realtime_name
                wf._identity.source = 'realtime_regex'
                wf._identity_from_current_msg = True
                logger.info('[IDENTITY REALTIME] Name %r detected in current message — overriding identity slot', wf._realtime_name)
        wf.requested_pdf_filename = self._extract_requested_pdf_filename(wf.user_text)
        wf.user_text_clean = wf.user_text.strip().lower()
        # 💎 CU-2: Verwende intent_engine.detect_storybook_intent mit Ausschlusskriterien
        wf.is_storybook_macro = intent_engine.detect_storybook_intent(wf.user_text_clean)
        wf.decision_tokens = ['1', '2', '3', '1.', '2.', '3.']
        wf.factcheck_tokens = ['1', '2', '1.', '2.']
        wf.policy_injection_message = None
        wf.is_audit_request = 'SYSTEM-INSTRUKTION FÜR DATEI-UPLOAD' in wf.user_text
        wf.is_numeric_decision = wf.user_text_clean in wf.decision_tokens
        wf.factcheck_prompt_pending = request.chat_id in ChatOrchestrator.FACTCHECK_PROMPT_PENDING
        wf.is_policy_question = False
        wf.last_model_text = ''
        wf.api_key = getattr(request, 'api_key', None) or keyring.get_password('Janus-Projekt', request.provider)
        wf.request_provider = str(getattr(request, 'provider', '') or '').lower()
        if wf.request_provider == 'ollama' and (not wf.api_key):
            wf.api_key = 'ollama'
        wf.policy_pending_data = self._get_policy_pending_data(request.chat_id)
        wf.is_waiting_for_consent = wf.policy_pending_data is not None
        wf.relevant_skill_ids = []
        wf.skip_llm_generation = False
        wf.is_factcheck_decision = not wf.is_policy_question and wf.factcheck_prompt_pending and (wf.user_text_clean in wf.factcheck_tokens)
        wf.is_factcheck_yes = wf.is_factcheck_decision and wf.user_text_clean in ['1', '1.']
        wf.is_factcheck_no = wf.is_factcheck_decision and wf.user_text_clean in ['2', '2.']
        wf.is_audit_decision = not wf.is_policy_question and wf.is_numeric_decision and (not wf.is_factcheck_decision)
        wf.is_realtime_search_query = any((token in wf.user_text_clean for token in ('websuche', 'internet', 'preis', 'release', 'erscheinen', 'veröffentlicht', 'games', 'spiele', 'termin')))
        wf.high_output_required = wf.is_audit_request or wf.is_audit_decision or wf.is_factcheck_yes or wf.is_realtime_search_query
        wf.original_filename = self._resolve_audit_filename(request.chat_id, [wf.user_text, wf.last_model_text])
        wf.skip_llm_generation = False
        wf.facts = {}
        wf.cloud_vision_result = {}
        wf.vision_result = None
        wf.vision_data = {}
        res = {}
        wf.event = 'DEFAULT'
        wf.event_data = {}
        wf.relevant_facts = []
        wf.memory_context_string = ''
        wf.final_text_to_generate = ''
        wf.final_facts = {}
        wf.final_ui_command = None
        wf.agent_response_payload = None
        wf.direct_dispatch_image_url = None
        wf.direct_dispatch_handled = False
        wf.agent_flow_error = None
        wf.run_tool_loop_result = None
        wf.audit_context_to_save = AuditContext(doc_name=wf.original_filename or '', status=None, details={})
        wf.config = self._load_config()
        try:
            wf.suggestion_mode = int(crud.get_default_user_suggestion_mode(self.db))
        except Exception:
            wf.suggestion_mode = 1
        logger.info(f"[SUGGESTION-ENGINE] Current mode active: {wf.suggestion_mode}")
        wf.active_personality = self._load_active_personality(wf.config)
        wf.base_system_prompt = wf.active_personality.get(
            "prompt", prompt_registry.get_directive("personality_fallback_prompt")
        )
        wf.system_prompt_for_llm = apply_verbosity_control(wf.base_system_prompt)
        wf.user_text_for_prompt = (wf.user_text or '').strip().lower()
        wf.user_prompt_lower = (wf.user_text or '').strip().lower()
        # Kalender-Snapshot vor Intent: Contextual Boost (TASK-062) gegen Event-Titel/Ort.
        try:
            from backend.services.calendar.calendar_memory import load_calendar_snapshot
            wf.calendar_snapshot = load_calendar_snapshot(self.db)
        except Exception as _cal_early_err:
            logger.debug("[CAL-SNAPSHOT] Vorab-Ladefehler (Intent): %s", _cal_early_err)
            wf.calendar_snapshot = getattr(wf, "calendar_snapshot", None)
        # 💎 Single Dispatch Contract: genau eine Intent-Erkennung pro User-Turn
        wf.intent_detection_result = intent_engine.detect_all_intents(
            wf.user_text, calendar_snapshot=wf.calendar_snapshot
        )
        inc = wf.intent_detection_result
        wf.is_calendar_intent = bool(getattr(inc, "is_calendar_intent", False))
        wf.is_multitask_image_pdf = inc.is_multitask_image_pdf
        wf.is_shopping_intent_early = inc.is_shopping_intent
        self._is_shopping_intent_flag = wf.is_shopping_intent_early
        wf.dialog_mode = 'DEFAULT'
        wf.v_profile = openai_profile if request.provider == 'openai' else gemini_profile
        wf.has_image = False
        wf.base64_image = ''
        wf.image_data = None
        wf.has_tool_trigger = inc.has_tool_trigger
        wf.is_large_ollama_model = str(request.provider or '').lower() == 'ollama' and self._is_large_local_model(getattr(request, 'model', ''))
        wf.is_ollama_vague_smalltalk = inc.is_ollama_vague_smalltalk
        wf.is_simple_document_check_prompt = inc.is_simple_document_check
        wf.is_local_planner_early_exit = False

        wf.help_intent_type = self._resolve_help_intent(inc)
        
        # Help Fast-Path: Skip LLM for help queries (§4.3)
        if wf.help_intent_type and not wf.has_image and not wf.is_policy_response:
            logger.info(
                "[HELP-FAST-PATH] Detected help intent '%s' for query '%s...' — skipping LLM",
                wf.help_intent_type,
                wf.user_text[:50]
            )
            # Validate provider against model to prevent mismatch (e.g., "Gemini von OpenAI")
            current_model = request.model if hasattr(request, 'model') else None
            current_provider = request.provider if hasattr(request, 'provider') else None

            # Always detect provider from model name to ensure PROVIDER-COHERENCE
            # This prevents misdirection (e.g., Gemini model with provider='openai')
            if current_model:
                detected_provider = self._get_provider_from_model(current_model)
                if detected_provider:
                    # Override current_provider if model name indicates a different provider
                    if current_provider != detected_provider:
                        logger.info(
                            "[PROVIDER-COHERENCE] Corrected provider from '%s' to '%s' based on model '%s'",
                            current_provider,
                            detected_provider,
                            current_model
                        )
                        current_provider = detected_provider

            wf.help_result = self.help_skill.handle(
                query=wf.user_text,
                intent_type=wf.help_intent_type,
                context={"chat_id": request.chat_id},
                language="de",
                current_model=current_model,
                current_provider=current_provider
            )
            wf.final_text_to_generate = wf.help_result.answer
            # Convert HelpAction to ui_command format
            if wf.help_result.actions:
                first_action = wf.help_result.actions[0]
                wf.final_ui_command = {
                    "type": first_action.type,
                    "payload": first_action.payload
                }
            else:
                wf.final_ui_command = None
            wf.skip_llm_generation = True
            wf.use_agent_factory = False
        else:
            wf.use_agent_factory = not wf.has_image and (not wf.is_policy_response) and (not wf.is_policy_question) and (not wf.is_audit_request) and (not wf.is_factcheck_decision) and (not intent_classifier.is_greeting(wf.user_text)) and (not intent_classifier.is_identity_query(wf.user_text)) and (not intent_classifier.is_opinion_query(wf.user_text)) and (not wf.is_ollama_vague_smalltalk) and (not wf.is_simple_document_check_prompt) and (not wf.is_local_planner_early_exit) and (wf.planner_prefers_agent or inc.is_complex_document_request)
        wf._is_personal_recall = inc.is_self_referential
        wf.user_text_lower = str(wf.user_text or '').lower()
        wf.is_local_business_intent = inc.is_local_business_intent
        wf.is_shopping_intent = getattr(self, '_is_shopping_intent_flag', False)
        wf.is_video_intent = inc.is_video_intent
        wf.is_video_understanding_intent = inc.is_video_understanding_intent
        if inc.named_channel_video:
            logger.info(
                "💎 CHANNEL-LOCK-INTENT: Kanalbezug erkannt (von/Kanal/…) — video.search mit Channel-Resolve priorisieren.",
            )
        wf.is_personal_recall = inc.is_personal_recall
        # Diamond: Meta-Agent und Image Intent via IntentDetectionResult (Single Dispatch Contract)
        wf.is_meta_agent_candidate = inc.is_complex_document_request and (not wf.has_image) and (not wf.is_policy_response) and (not wf.is_policy_question) and (not wf.is_audit_request) and (not wf.is_factcheck_decision)
        wf.image_intent_keywords = list(intent_engine.image_intent_keywords)
        wf.image_name_hint = ''
        wf.chat_title = ''
        wf.is_eval_reporting = False
        wf.image_name_hint_l = wf.image_name_hint.lower()
        wf.chat_title_l = wf.chat_title.lower()
        wf.vision_mode = 'eval' if any((token in wf.image_name_hint_l or token in wf.chat_title_l for token in ['supercluster-', 'cluster', 'stresstest', 'e2e'])) else 'live'
        wf.relevant_facts = self._get_recent_memories_raw(limit=20, exclude_vision_for_unknown=wf.event == 'PERSON_UNKNOWN')
        wf.original_filename = (wf.original_filename or 'dokument').strip()
        wf.dialog_mode = 'DEFAULT'
        wf.system_prompt = prompt_registry.get_directive("default_system_prompt")
        wf.disable_tools = False
        wf.llm_input = {'text': wf.user_text}
        wf.user_selected_model = request.model
        wf.user_text_clean = wf.user_text.strip().lower()
        wf.is_numeric_decision = wf.user_text_clean in wf.decision_tokens
        wf.is_audit_decision = wf.is_numeric_decision and (not wf.is_factcheck_decision)
        wf.original_document_name = f'{wf.original_filename}.pdf' if wf.original_filename else None
        wf.audit_target_filename = wf.original_document_name or 'aegypten.pdf'
        wf.final_text = ''
        wf.response = {'text': wf.final_text} if wf.skip_llm_generation else {}
        wf.factcheck_modifications_detected = None
        wf.final_image_url = wf.direct_dispatch_image_url
        wf.required_terms_by_image = {'supercluster-21.jpg': ['Trenchcoat', 'Regenschirm', 'Leder'], 'supercluster-22.jpg': ['Wollmantel', 'Beanie', 'Nebel'], 'supercluster-23.jpg': ['Daunenjacke', 'Strickmütze'], 'supercluster-24.jpg': ['Zopfstrick', 'Lederstiefel'], 'supercluster-25.jpg': ['Denim', 'Dreitagebart'], 'supercluster-26.jpg': ['Armbanduhr', 'Dreitagebart'], 'supercluster-27.jpg': ['Pferdeschwanz', 'Leggings'], 'supercluster-28.jpg': ['Rollkragenpullover', 'Bibliothek'], 'supercluster-29.jpg': ['Spitze', 'Lochmuster'], 'supercluster-30.jpg': ['Perle', 'Halskette'], 'supercluster-31.jpg': ['Satin', 'Bomberjacke'], 'supercluster-32.jpg': ['Leder-Aktentasche', 'Patina'], 'supercluster-33.jpg': ['Streifen', 'Sommerkleid'], 'supercluster-34.jpg': ['Cargo-Hose', 'Arbeitsstiefel'], 'supercluster-35.jpg': ['Sweatshirt', 'Zeitschrift'], 'supercluster-36.jpg': ['Anzug', 'Abenddämmerung'], 'supercluster-37.jpg': ['Streifenmuster', 'Strickschal'], 'supercluster-38.jpg': ['Satin', 'Blazer'], 'supercluster-39.jpg': ['Drachen-Print', 'Blumenmotive'], 'supercluster-40.jpg': ['Leoparden-Muster', 'Faux Fur']}
        wf.image_key = str(wf.image_name_hint or '').lower()
        wf.placeholder_md_pattern = '!\\[[^\\]]*\\]\\(\\s*Generated Image\\s*\\)'
        wf.final_text = re.sub('\\n{3,}', '\n\n', wf.final_text).strip()
        # Diamond: Identity tracking via IdentityManager (STM must be DB Message rows, not orchestrator history dicts)
        _stm_msgs_for_identity: List[Message] = []
        if request.chat_id is not None:
            _stm_msgs_for_identity = (
                self.db.query(Message)
                .filter(Message.chat_id == request.chat_id)
                .order_by(Message.id.desc())
                .limit(12)
                .all()
            )[::-1]
        # Ohne chat_id kein „plain chat“-Identity-Pfad (vermeidet None in Identity-Tracking).
        wf._is_plain_chat = (
            (not wf.is_eval_reporting)
            and (not wf.is_audit_request)
            and (request.chat_id != 9999)
            and (wf._identity.name is None)
            and (request.chat_id is not None)
            and (not identity_manager.is_identity_already_asked(request.chat_id))
            and (not ChatOrchestrator._is_name_mentioned_in_current_stm(_stm_msgs_for_identity))
        )
        wf.parity_dir = os.getenv('JANUS_PARITY_CAPTURE_DIR')
        wf.execution_for_persist = ExecutionResponse(text=wf.final_text, image_url=wf.final_image_url, agent_payload=wf.agent_response_payload, tool_calls=[], is_agent_flow=bool(wf.agent_response_payload))
        wf.aggregated_usage = {}
        wf.aggregated_cost = {}
        wf.total_search_cost = 0.0
        wf.execution_for_persist = ExecutionResponse(text=wf.final_text, image_url=wf.final_image_url, agent_payload=wf.agent_response_payload, tool_calls=[], is_agent_flow=bool(wf.agent_response_payload), usage=wf.aggregated_usage, cost=wf.aggregated_cost)
        wf.execution_for_api = wf.execution_for_persist
        wf.vision_data = None
        wf.learned_name = None
        wf.skip_fact_extraction = bool(isinstance(wf.response, dict) and wf.response.get('skip_fact_extraction'))
        # 💎 ANTI-HALLUCINATION: Skip fact extraction during audit intent to prevent learning from hallucinations
        if getattr(request, "audit_file", None):
            wf.skip_fact_extraction = True
            logger.info("💎 ANTI-HALLUCINATION: Skipping fact extraction for audit_file=%s", request.audit_file)
        wf.display_text = wf.final_text
        wf.clean_comp = wf.final_text.strip()
        wf.audit_data = None
        wf.status_persisted = False
        ctx.identity_fact = wf._identity
        return ctx

    async def _try_early_exit(self, ctx: RequestContext) -> Optional[Dict]:
        wf = ctx.workflow
        request = ctx.request
        policy_response = await handle_policy_consent_phase(self, ctx)
        if policy_response is not None:
            return policy_response
        if wf.is_factcheck_decision and request.chat_id is not None:
            ChatOrchestrator.FACTCHECK_PROMPT_PENDING.discard(request.chat_id)
        # CHAIN-OF-COMMAND nur bei Bild+PDF-Multitask — nicht in normale Chats injizieren (Gemini Signal/Rauschen).
        if wf.is_multitask_image_pdf:
            wf.system_prompt_for_llm += prompt_registry.get_directive("chain_of_command_multitask_image_pdf")
        self._user_budget_info: Optional[dict] = None
        if wf.is_shopping_intent_early:
            from backend.tools.finance_tools import _extract_budget_limit
            wf._detected_budget = _extract_budget_limit(wf.user_text)
            if wf._detected_budget is not None:
                wf._budget_re_match = re.search('((?:bis|unter|max(?:imal)?|budget|höchstens)\\s*\\d{1,6}(?:[.,]\\d{1,2})?\\s*(?:€|euro|eur)|\\d{1,6}(?:[.,]\\d{1,2})?\\s*(?:€|euro|eur)\\s*(?:budget|limit|max|obergrenze))', wf.user_text, re.IGNORECASE)
                wf._budget_raw = wf._budget_re_match.group(0).strip() if wf._budget_re_match else f'bis {wf._detected_budget:.0f}€'
                self._user_budget_info = {'limit': wf._detected_budget, 'raw': wf._budget_raw}
                logger.info("BUDGET-TRANSIT: Budget %.2f erkannt aus User-Text, raw='%s'", wf._detected_budget, wf._budget_raw)
        if wf.is_shopping_intent_early:
            wf.system_prompt_for_llm += prompt_registry.get_directive("shopping_advisory_guardrail")
        if wf.api_key:
            logger.info('API-Key-Fingerprint (%s): %s...%s', request.provider, wf.api_key[:5], wf.api_key[-5:])
        if wf.is_storybook_macro and wf.api_key:
            logger.info('STORYBOOK INTENT ERKANNT: Starte Diamond-Macro.')
            wf.execution_for_api = await self._run_storybook_macro(wf.user_text, request, wf.api_key)
            self.status_sync.persist_assistant_message(request.chat_id, wf.execution_for_api)
            return self.status_sync.build_api_response(execution_response=wf.execution_for_api)
        for part in request.content or []:
            if part.type == 'image_url':
                wf.raw_data = part.image_url if isinstance(part.image_url, str) else getattr(part.image_url, 'url', '')
                if not isinstance(wf.raw_data, str):
                    wf.raw_data = ''
                wf.image_data = wf.raw_data
                if wf.raw_data.startswith('data:image/'):
                    wf.has_image = True
                    logger.info('Bild-Check: Valides Bildformat erkannt.')
                    wf.base64_image = wf.raw_data.split(',', 1)[1]
                else:
                    logger.warning('Bild-Check abgelehnt! Ungültiger Header: %s...', (wf.raw_data or '')[0:30])
                    wf.image_data = None
                    wf.has_image = False
                    wf.base64_image = ''
                break
        if str(request.provider or '').lower() == 'ollama':
            if len(wf.user_prompt_lower.split()) < 4 and (not wf.has_tool_trigger) and (not wf.is_large_ollama_model):
                wf.is_ollama_vague_smalltalk = True
            elif any((phrase in wf.user_prompt_lower for phrase in intent_engine.ollama_smalltalk_phrases)) and (not wf.has_tool_trigger):
                wf.is_ollama_vague_smalltalk = True
        if str(request.provider or '').lower() == 'ollama':
            try:
                wf.is_local_planner_early_exit = bool(intent_classifier.should_skip_planner(wf.user_text))
            except Exception:
                wf.is_local_planner_early_exit = False
        if wf.user_prompt_lower == 'hello':
            wf.planner_prefers_agent = True
        if str(request.provider or '').lower() == 'ollama' and wf.has_tool_trigger and (not wf.has_image) and (not wf.is_policy_response) and (not wf.is_policy_question) and (not wf.is_audit_request) and (not wf.is_factcheck_decision):
            wf.use_agent_factory = True
        if str(request.provider or '').lower() == 'ollama' and (not wf.has_image) and intent_classifier.is_identity_query(wf.user_text):
            wf.final_text_to_generate = prompt_registry.get_directive("ollama_identity_fast_path")
            wf.skip_llm_generation = True
            wf.disable_tools = True
            logger.info('IDENTITY FAST-PATH aktiv (ollama): direkte Janus-Selbstvorstellung ohne LLM-Call.')
        elif str(request.provider or '').lower() == 'ollama' and (not wf.has_image) and intent_classifier.is_greeting(wf.user_text):
            wf.user_text_lower = str(wf.user_text or '').lower()
            if 'wie geht' in wf.user_text_lower or 'wie gehts' in wf.user_text_lower:
                wf.final_text_to_generate = prompt_registry.get_directive("ollama_greeting_how_are_you")
            else:
                wf.final_text_to_generate = prompt_registry.get_directive("ollama_greeting_default")
            wf.skip_llm_generation = True
            wf.disable_tools = True
            logger.info('SMALLTALK FAST-PATH aktiv (ollama): direkte Kurzantwort ohne LLM-Call.')
        elif str(request.provider or '').lower() == 'ollama' and (not wf.has_image) and intent_classifier.is_opinion_query(wf.user_text):
            wf.final_text_to_generate = prompt_registry.get_directive("ollama_opinion_ducks")
            wf.skip_llm_generation = True
            wf.disable_tools = True
            logger.info('SMALLTALK FAST-PATH aktiv (ollama): Meinungsklärung ohne LLM-Call.')
        try:
            wf.relevant_skill_ids = self.skill_selector.get_relevant_skills(
                wf.user_text, intent_result=wf.intent_detection_result
            )
        except Exception as exc:
            logger.debug('SkillSelector fallback (keine Filterung): %s', exc)
            wf.relevant_skill_ids = []
        
        # File Extension Guard: Always allow knowledge skills when file extensions are detected
        _FILE_EXTENSIONS = (
            '.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
            '.mp4', '.mp3', '.wav', '.flac', '.zip', '.rar', '.7z',
            '.json', '.xml', '.csv', '.md', '.html', '.css', '.js',
            '.py', '.java', '.c', '.cpp', '.h', '.php', '.rb', '.go',
            '.ts', '.tsx', '.jsx', '.vue', '.svelte', '.sql', '.db',
        )
        text_lower = (wf.user_text or '').lower()
        has_file_extension = any(ext in text_lower for ext in _FILE_EXTENSIONS)
        if has_file_extension:
            for skill in ['knowledge.query', 'knowledge.code_search']:
                if skill not in wf.relevant_skill_ids:
                    wf.relevant_skill_ids.append(skill)
            logger.debug(
                "[FILE-EXTENSION-GUARD] Added knowledge skills to relevant_skill_ids: %s",
                [s for s in ['knowledge.query', 'knowledge.code_search'] if s in wf.relevant_skill_ids]
            )
        
        # PDF Routing Guard: Prevent filesystem.read_file for PDF files, ensure knowledge skills
        if '.pdf' in text_lower:
            if 'filesystem.read_file' in wf.relevant_skill_ids:
                wf.relevant_skill_ids.remove('filesystem.read_file')
                logger.debug("[PDF-ROUTING-GUARD] Removed filesystem.read_file (PDF detected)")
            # Ensure knowledge.query or knowledge.read_full_text is included
            for knowledge_skill in ['knowledge.query', 'knowledge.read_full_text']:
                if knowledge_skill not in wf.relevant_skill_ids:
                    wf.relevant_skill_ids.append(knowledge_skill)
            logger.debug(
                "[PDF-ROUTING-GUARD] Added knowledge skills for PDF: %s",
                [s for s in ['knowledge.query', 'knowledge.read_full_text'] if s in wf.relevant_skill_ids]
            )
        if wf._is_personal_recall and (not wf.is_video_intent):
            wf._websearch_skills = {'system.websearch', 'system.rss_news'}
            wf._before = len(wf.relevant_skill_ids)
            wf.relevant_skill_ids = [s for s in wf.relevant_skill_ids if s not in wf._websearch_skills]
            logger.info('[PRECEDENCE-GUARD-035] Personal recall detected — removed websearch from tools (%d → %d skills): %r', wf._before, len(wf.relevant_skill_ids), wf.user_text[:60])
        if wf.is_local_business_intent:
            logger.info("DIAMOND GUARDRAIL: Lokale Suche erkannt. Forciere 'system.local_business' und blockiere allgemeine Textantworten ohne Tool.")
            wf.relevant_skill_ids = ['system.local_business']
        if wf.is_shopping_intent and (not wf.is_personal_recall):
            logger.info(
                "SHOPPING-GUARDRAIL: Kaufberatung erkannt (Intent=%s, Recall=%s, primary=%s). Forciere 'system.price_comparison'.",
                wf.is_shopping_intent,
                wf.is_personal_recall,
                getattr(wf.intent_detection_result, "primary_intent", None),
            )
            wf.relevant_skill_ids = ['system.price_comparison']
        elif wf.is_video_intent and (not wf.is_local_business_intent):
            logger.info(
                "VIDEO-GUARDRAIL: Video-/YouTube-Intent — priorisiere 'video.search' und halte 'system.websearch' als Fallback.",
            )
            wf.relevant_skill_ids = ["video.search", "system.websearch"]
        if wf.is_video_understanding_intent:
            logger.info(
                "VIDEO-UNDERSTANDING-GUARDRAIL: Video-Understanding-Intent erkannt — priorisiere 'video.understand'.",
            )
            if "video.understand" not in wf.relevant_skill_ids:
                wf.relevant_skill_ids.append("video.understand")
        local_image_response = await handle_local_requests(self, ctx)
        if local_image_response is not None:
            return local_image_response
        return None

    async def _build_memory_context(self, ctx: RequestContext) -> RequestContext:
        """Load memory slots (includes [HEALTH-INJECTOR] via ``retrieve_diamond_slots``) before ``_execute_generation`` / tool loop."""
        wf = ctx.workflow
        request = ctx.request
        apply_image_intent_skill_guardrails(wf)
        if wf.is_meta_agent_candidate:
            # 💎 GLOBAL VETO: Prüfe globale negative Keywords vor Meta-Agent-Start
            if wf.intent_detection_result and wf.intent_detection_result.meta_agent_global_veto:
                veto_reason = "meta_agent_global_veto"
                logger.warning("[GLOBAL VETO] Meta-Agent blocked by negative keyword: %s. Skipping meta_agent_run.", veto_reason)
                wf.is_meta_agent_run = False
                wf.is_meta_agent_candidate = False
                return ctx
            wf.is_meta_agent_run = True
            wf.meta_profile = self._get_meta_provider_profile(request.provider)
            wf.meta_fast_path = self._is_large_local_model(request.model)
            logger.info('META-AGENT PHASE 1 START (Recherche)')
            wf.kpi_phase1_started_at = time.perf_counter()
            wf.all_dynamic_skills = self.skill_selector.get_relevant_skills(
                wf.user_text, intent_result=wf.intent_detection_result
            )
            wf.is_small = any((m in str(request.model or '').lower() for m in ['nano', 'mini']))
            if wf.is_small:
                wf.dynamic_skills = ['system.websearch']
                logger.info("NANO-GUARD: Begrenze Skills auf 'system.websearch' für stabile Planung.")
            else:
                wf.recherche_domains = {'system.websearch', 'system.wikipedia_summary', 'system.rss_news', 'knowledge.query', 'system.country_info'}
                wf.dynamic_skills = [s for s in wf.all_dynamic_skills if s in wf.recherche_domains]
                if not wf.dynamic_skills:
                    wf.dynamic_skills = ['system.websearch']
            if wf.meta_fast_path:
                ctx.workflow.mark_retry_path('meta_phase1_forced')
                wf.phase1_execution = await self._run_meta_agent_research_fallback(user_text=wf.user_text, request=request, api_key=wf.api_key or '', skip_final_synthesis=True, meta_profile=wf.meta_profile)
            else:
                wf.phase1_execution = await self.execution_engine.run_agent_factory(enabled=True, chat_id=request.chat_id, user_text=self._build_meta_research_prompt(wf.user_text, wf.meta_profile.get('phase1_max_tokens')), relevant_skill_ids=wf.dynamic_skills, provider=request.provider, model=request.model, api_key=wf.api_key or '', intent_result=wf.intent_detection_result)
            if wf.kpi_phase1_started_at is not None:
                wf.kpi_phase1_research_ms = round((time.perf_counter() - wf.kpi_phase1_started_at) * 1000.0, 2)
            if wf.phase1_execution.is_agent_flow:
                logger.info('META-AGENT PHASE 2 START (Produktion)')
                wf.kpi_phase2_started_at = time.perf_counter()
                wf.phase1_context = str(wf.phase1_execution.text or '').strip()
                wf.pdf_only_skill = ['system.create_pdf']
                if wf.meta_fast_path:
                    ctx.workflow.mark_retry_path('meta_phase2_forced')
                    wf.phase2_execution = await self._run_meta_agent_production_fallback(phase1_context=wf.phase1_context, requested_filename=wf.requested_pdf_filename, original_user_text=wf.user_text, request=request, api_key=wf.api_key or '', meta_profile=wf.meta_profile)
                else:
                    wf.phase2_prompt = self._build_meta_phase2_json_only_prompt(wf.phase1_context, requested_filename=wf.requested_pdf_filename, original_user_text=wf.user_text, meta_profile=wf.meta_profile)
                    wf.model_name_lower = str(request.model or '').lower()
                    if any((marker in wf.model_name_lower for marker in ['nano', 'mini'])):
                        wf.fname = wf.requested_pdf_filename or 'finanzcheck_heute.pdf'
                        wf.phase2_prompt = prompt_registry.get_directive("meta_phase2_mandatory_pdf").format(
                            fname=wf.fname, phase1_context=wf.phase1_context
                        )
                    wf.phase2_execution = await self.execution_engine.run_agent_factory(enabled=True, chat_id=request.chat_id, user_text=wf.phase2_prompt, relevant_skill_ids=wf.pdf_only_skill, provider=request.provider, model=request.model, api_key=wf.api_key or '', intent_result=wf.intent_detection_result)
                if wf.phase2_execution.is_agent_flow:
                    wf.agent_response_payload = wf.phase2_execution.agent_payload
                    wf.final_text_to_generate = self._build_meta_pdf_success_message(phase1_context=wf.phase1_context, phase2_text=str(wf.phase2_execution.text or ''))
                    wf.skip_llm_generation = True
                    wf.use_agent_factory = False
                else:
                    wf.direct_pdf_execution = await self._run_meta_agent_direct_pdf_generation(phase1_context=wf.phase1_context, requested_filename=wf.requested_pdf_filename, original_user_text=wf.user_text, request=request, api_key=wf.api_key or '')
                    if wf.direct_pdf_execution.is_agent_flow:
                        wf.agent_response_payload = wf.direct_pdf_execution.agent_payload
                        wf.final_text_to_generate = self._build_meta_pdf_success_message(phase1_context=wf.phase1_context, phase2_text=str(wf.direct_pdf_execution.text or ''))
                    wf.skip_llm_generation = True
                    wf.use_agent_factory = False
                if wf.kpi_phase2_started_at is not None:
                    wf.kpi_phase2_pdf_ms = round((time.perf_counter() - wf.kpi_phase2_started_at) * 1000.0, 2)
            else:
                wf.kpi_success = False
                wf.kpi_error_code = 'META_AGENT_PHASE1_FAILED'
                logger.warning('META-AGENT PHASE 1 fehlgeschlagen, fallback auf Standard-Agent-Flow.')
        if wf.use_agent_factory:
            wf.agent_execution = await self.execution_engine.run_agent_factory(enabled=True, chat_id=request.chat_id, user_text=wf.user_text, relevant_skill_ids=wf.relevant_skill_ids, provider=request.provider, model=request.model, api_key=wf.api_key or '', intent_result=wf.intent_detection_result)
            if wf.agent_execution.is_agent_flow:
                wf.agent_response_payload = wf.agent_execution.agent_payload
                wf.final_text_to_generate = str(wf.agent_execution.text or 'Agent-Ausführung abgeschlossen.')
                wf.skip_llm_generation = True
                logger.info('Agent-Factory Ergebnis in Lifecycle integriert (kein Early-Return). trace_id=%s', (wf.agent_response_payload or {}).get('trace_id'))
            else:
                wf.fallback_agent_text = str(wf.agent_execution.text or '').strip() or prompt_registry.get_directive(
                    "agent_factory_fallback_message"
                )
                wf.final_text_to_generate = wf.fallback_agent_text
                wf.skip_llm_generation = True
                if wf.agent_execution.error:
                    wf.agent_flow_error = wf.agent_execution.error
                    wf.kpi_success = False
                    wf.kpi_error_code = str(wf.agent_flow_error.get('code') or 'AGENT_FACTORY_FAILED')
                    logger.error('AGENT_FACTORY_FAILED: fallback=atomic_message code=%s message=%s', wf.agent_flow_error.get('code'), wf.agent_flow_error.get('message'), exc_info=True)
                else:
                    logger.warning('AGENT_FACTORY_NO_FLOW: fallback=atomic_message')
        if request.chat_id:
            wf.chat_row = crud.get_chat_by_id(self.db, request.chat_id)
            wf.chat_title = str(getattr(wf.chat_row, 'title', '') or '')
            wf.match = re.search('((?:[A-Za-z0-9_.\\- ]+[\\\\/])?[A-Za-z0-9_.\\- ]+\\.(?:jpe?g))', wf.chat_title, re.IGNORECASE)
            if wf.match:
                wf.image_name_hint = wf.match.group(1).strip()
        if wf.has_image:
            logger.info('Starte Vision-Pipeline...')
            identity_manager.clear_unknown_face(request.chat_id)
            wf.local_task = self._process_visual_content(request.content, request.provider, wf.v_profile, wf.image_name_hint)
            wf.cloud_task = analyze_image_with_cloud(wf.base64_image, request.provider, wf.api_key)
            vision_result, cloud_vision_result = await asyncio.gather(wf.local_task, wf.cloud_task)
            wf.vision_result = wf.vision_result or {'local_recognition_result': {}}
            wf.cloud_vision_result = wf.cloud_vision_result or {}
            wf.vision_data = wf.vision_result
            res = wf.vision_result.get('local_recognition_result', {}) if isinstance(wf.vision_result, dict) else {}
            wf.context = {}
            if isinstance(res, dict):
                wf.context = res.get('context', {})
            logger.info('Vision-Ergebnis: %s Keys gefunden', len(res))
            if identity_manager.has_unknown_face_buffered(request.chat_id):
                wf.match = re.search('(?:ist|is|sit|heißt|nenne sie|das ist|das sind|ich bin|wäre)\\s+([a-zA-ZäöüÄÖÜß]+)', wf.user_text, re.IGNORECASE)
                if wf.match:
                    wf.event = 'PERSON_NAMED'
                    wf.event_data['name'] = wf.match.group(1).capitalize()
                    logger.info("LERN-TRIGGER AKTIVIERT: Versuche Name '%s' an Gesichtsbild zu binden.", wf.event_data['name'])
            if res:
                wf.event_data['fact_sheet'] = res.get('fact_sheet', {})
                wf.event_data['tags'] = res.get('local_description', '')
                if res.get('identified_names'):
                    wf.event = 'PERSON_IDENTIFIED'
                    wf.event_data['name'] = res['identified_names'][0]
                    logger.info('SOFORT-ERKENNUNG: %s', wf.event_data['name'])
                else:
                    wf.event = 'PERSON_UNKNOWN'
                    if res.get('found_faces'):
                        identity_manager.store_unknown_face(request.chat_id, {'encoding': res['unknown_encodings'][0]})
            wf.cloud_description = ''
            wf.visual_profile_str = ''
            if wf.cloud_vision_result:
                wf.cloud_description = json.dumps(wf.cloud_vision_result, ensure_ascii=False)
                wf.visual_profile_str = wf.cloud_description.strip()
                logger.info('CLOUD-HYBRID: Objektprofil uebernommen (%s chars).', len(wf.visual_profile_str))
            elif wf.base64_image:
                wf.cloud_description = await analyze_image_strict_provider(request.provider, wf.api_key, wf.base64_image, self.db, wf.v_profile)
                wf.visual_profile_str = wf.cloud_description.strip()
                logger.info('CLOUD: Fallback-Profil uebernommen (%s chars).', len(wf.visual_profile_str))
            wf.event_data['cloud_description'] = wf.cloud_description
            wf.event_data['visual_profile_str'] = wf.visual_profile_str
            wf.event_data['cloud_vision_result'] = wf.cloud_vision_result
        else:
            logger.info('Kein Bild gefunden - Text-Only Modus')
        if wf.dialog_mode == 'CONFIRM_LEARNING':
            wf.system_prompt_for_llm = prompt_registry.get_directive("confirm_learning_system_template").format(
                name=wf.event_data.get("name") or ""
            )
            for part in request.content:
                if part.type == 'image_url':
                    if isinstance(part.image_url, str):
                        wf.base64_image = part.image_url.split(',')[1]
                    elif part.image_url.url:
                        wf.base64_image = part.image_url.url.split(',')[1]
                    break
            wf.vision_result = await self._process_visual_content(request.content, request.provider, wf.v_profile, wf.image_name_hint)
            wf.vision_data = wf.vision_result
            res = wf.vision_result.get('local_recognition_result', {})
            if res:
                wf.event_data['fact_sheet'] = res.get('fact_sheet', {})
                wf.event_data['tags'] = res.get('local_description', '')
                if res.get('identified_names'):
                    wf.event = 'PERSON_IDENTIFIED'
                    wf.event_data['name'] = res['identified_names'][0]
                    wf.event_data['tags'] = res.get('local_description', '')
                    logger.info('SOFORT-ERKENNUNG: %s', wf.event_data['name'])
                else:
                    wf.event = 'PERSON_UNKNOWN'
                    if res.get('found_faces'):
                        identity_manager.store_unknown_face(request.chat_id, {'encoding': res['unknown_encodings'][0]})
            wf.cloud_description = ''
            wf.visual_profile_str = ''
            if wf.base64_image:
                wf.cloud_description = await analyze_image_strict_provider(request.provider, wf.api_key, wf.base64_image, self.db, wf.v_profile)
                wf.visual_profile_str = wf.cloud_description.strip()
                logger.info('CLOUD: Profil uebernommen (%s chars).', len(wf.visual_profile_str))
            wf.event_data['cloud_description'] = wf.cloud_description
            wf.event_data['visual_profile_str'] = wf.visual_profile_str
        if identity_manager.has_unknown_face_buffered(request.chat_id):
            wf.match = re.search('(?:ist|is|sit|heißt|nenne sie|das ist|das sind|ich bin|wäre)\\s+([a-zA-ZäöüÄÖÜß]+)', wf.user_text, re.IGNORECASE)
            if wf.match:
                wf.event = 'PERSON_NAMED'
                wf.event_data['name'] = wf.match.group(1).capitalize()
                logger.info("LERN-TRIGGER AKTIVIERT: Versuche Name '%s' an Gesichtsbild zu binden.", wf.event_data['name'])
        crud.create_message(self.db, request.chat_id, 'user', (wf.vision_data.get('markdown', '') if wf.vision_data else '') + wf.user_text)
        if not wf.user_selected_model:
            wf.chosen_model = self.MODEL_HIERARCHY[request.provider]['speed']
        else:
            wf.chosen_model = wf.user_selected_model
        logger.info(
            "MoA-Routing aktiv: Basis-Modell=%r, Skill-Tier hat Vorrang wenn verfügbar.",
            wf.chosen_model,
        )
        if wf.event == 'PERSON_NAMED':
            wf.dialog_mode = 'CONFIRM_LEARNING'
            wf.final_text_to_generate = prompt_registry.get_directive("confirm_person_name_template").format(
                name=wf.event_data["name"]
            )
            wf.target_name = wf.event_data['name']
            wf.profile_to_save = wf.event_data.get('visual_profile_str', '')
            wf.tags_to_save = wf.event_data.get('tags', '')
            _uf = identity_manager.get_unknown_face(request.chat_id)
            encoding = (_uf or {}).get("encoding") if isinstance(_uf, dict) else None
            if encoding is not None:
                vision_service.start_save_person_background(
                    name=wf.target_name,
                    encoding=encoding,
                    chat_id=request.chat_id,
                    profile_str=wf.profile_to_save,
                    tags=wf.tags_to_save
                )
            # Clear unknown face buffer via IdentityManager
            identity_manager.clear_unknown_face(request.chat_id)
        elif wf.event == 'PERSON_IDENTIFIED':
            from backend.data import crud_vision
            identity_manager.clear_unknown_face(request.chat_id)
            wf.is_first_meeting = False
            if wf.event_data.get('name'):
                wf.fact_count = crud_vision.get_person_fact_count(self.db, wf.event_data['name'])
                if wf.fact_count == 0:
                    wf.is_first_meeting = True
            wf.dialog_mode = 'GREET_KNOWN'
            wf.disable_tools = True
            wf.llm_input = {'name': wf.event_data.get('name', 'Gast'), 'features': ', '.join(vision_service.get_tags_from_string(wf.event_data.get('tags', ''))) if wf.event_data.get('tags') else 'viele nette Details', 'cloud_desc': wf.event_data.get('cloud_description', ''), 'is_first_meeting': wf.is_first_meeting}
        elif wf.event == 'PERSON_UNKNOWN':
            if wf.has_image and (not res.get('feature_report')):
                logger.error('❌ Vision-Analyse lieferte keine Ergebnisse trotz Bild!')
                wf.final_text_to_generate = prompt_registry.get_directive("vision_no_person_detected")
            else:
                logger.info('Portrait-Modus: Feature Report mit %s Kategorien', len(res.get('feature_report', {})))
                wf.facts = fuse_vision_results(res, wf.event_data.get('cloud_vision_result', {}), vision_mode=wf.vision_mode)
                wf.final_facts = wf.facts
                if wf.has_image and res.get('found_faces') and (not res.get('identified_names')):
                    wf.saved_traits = await asyncio.to_thread(self.save_visual_traits, 'unbekannt', wf.event_data.get('tags', ''), res.get('feature_report', {}), wf.event_data.get('cloud_vision_result', {}), wf.final_facts.get('SOURCE_OF_TRUTH', {}), request.chat_id or 0, 0.35)
                    logger.info('SPEICHER-FILTER: %s cloud-bestaetigte Visual-Traits gespeichert (mit SOURCE_OF_TRUTH).', wf.saved_traits)
                wf.is_eval_reporting = wf.vision_mode == 'eval' or str(wf.image_name_hint or '').lower().startswith('supercluster-') or 'e2e' in wf.chat_title_l
                if not wf.is_eval_reporting:
                    wf.clip_verified = _build_clip_verified_elements(res.get('feature_report', {}), wf.final_facts)
                    if wf.clip_verified:
                        wf.final_facts = dict(wf.final_facts)
                        wf.final_facts['VERIFIZIERTE_ELEMENTE_PFLICHT'] = wf.clip_verified
                        logger.info('CLIP-first verified elements injected: %s', wf.clip_verified)
                wf.reporter_facts = _build_enriched_reporter_facts(wf.final_facts, res.get('feature_report', {}), wf.event_data.get('cloud_vision_result', {}) if isinstance(wf.event_data, dict) else {})
                wf.plugin_gate_debug = {'confirmed': [], 'watch': [], 'withheld': {}}
                wf.maturity_entries = []
                if not wf.is_eval_reporting:
                    reporter_facts, plugin_gate_debug, maturity_entries = _apply_plugin_confidence_gates(wf.reporter_facts, res.get('feature_report', {}), wf.final_facts, wf.event_data.get('cloud_vision_result', {}) if isinstance(wf.event_data, dict) else {})
                    logger.info('PLUGIN_GATE status: confirmed=%s watch=%s withheld=%s', wf.plugin_gate_debug.get('confirmed', []), wf.plugin_gate_debug.get('watch', []), wf.plugin_gate_debug.get('withheld', {}))
                    logger.debug('PLUGIN maturity entries: %s (ambiente_threshold=%.2f)', wf.maturity_entries, _AMBIENTE_CONFIDENCE_THRESHOLD)
                wf.reporter_fact_source = wf.reporter_facts if wf.is_eval_reporting or _USE_FULL_FACTS_IN_LIVE_REPORTER else _build_live_slot_fact_block(wf.reporter_facts)
                if wf.is_eval_reporting:
                    wf.cleaned_fact_block = wf.final_facts
                else:
                    wf.cleaned_fact_block = {clean_for_chat(key): clean_for_chat(value) if isinstance(value, str) else value for key, value in wf.reporter_fact_source.items()}
                wf.required_verified_terms = wf.final_facts.get('VERIFIZIERTE_ELEMENTE_PFLICHT', [])
                wf.exclusion_terms = wf.final_facts.get('AUSSCHLUSS_PFLICHT', [])
                if not isinstance(wf.required_verified_terms, list):
                    wf.required_verified_terms = []
                if not isinstance(wf.exclusion_terms, list):
                    wf.exclusion_terms = []
                wf.normalized_exclusions = _normalize_exclusion_terms(wf.exclusion_terms)
                wf.cleaned_fact_block = _sanitize_value_by_exclusions(wf.cleaned_fact_block, wf.normalized_exclusions)
                wf.verified_lines = []
                if wf.required_verified_terms:
                    wf.verified_lines.append('Muss enthalten: ' + ', '.join((str(term) for term in wf.required_verified_terms if term)))
                if wf.exclusion_terms:
                    wf.verified_lines.append('Darf nicht enthalten: ' + ', '.join((str(term) for term in wf.exclusion_terms if term)))
                wf.verified_block = '\n'.join(wf.verified_lines).strip()
                wf.final_text_to_generate = prompt_registry.get_directive("verified_elements_live_reporter_preamble")
                wf.skip_llm_generation = False
                logger.info('Hybrid-Reporter Prompt erstellt: %s Facts', len(wf.final_facts))
        else:
            from backend.services.memory_budget import MEMORY_V2_ENABLED, TokenBudget, select_slots_by_budget, format_memory_context, extract_fact_coupons, format_fact_coupons
            from backend.services.memory_manager import retrieve_diamond_slots
            wf._active_directives = []
            wf._active_directive_names = set()
            wf._has_negative_preferences = False
            if MEMORY_V2_ENABLED:
                try:
                    wf.model_limit = 8000
                    logger.info(
                        "[MEMORY-PRECEDE] retrieve_diamond_slots (health injector + slots) before tool loop, chat_id=%s",
                        request.chat_id,
                    )
                    wf.slots = retrieve_diamond_slots(self.db, request.chat_id, wf.user_text, max_tokens=wf.model_limit)
                    wf._model_lower = str(request.model or '').lower()
                    wf._is_small_model = any((tag in wf._model_lower for tag in ('nano', 'mini', 'flash')))
                    wf._memory_ratio = 0.5 if wf._is_small_model else 0.3
                    wf.budget = TokenBudget(max_tokens=wf.model_limit, memory_ratio=wf._memory_ratio)
                    if wf._is_small_model:
                        logger.info('[BUDGET] Small model detected (%s) — memory_ratio=%.2f', request.model, wf._memory_ratio)
                    wf.selected = select_slots_by_budget(wf.slots, wf.budget)
                    from backend.services.memory_identity import ensure_identity_in_slots as _ensure_id
                    wf.selected = _ensure_id(wf.selected, wf._identity)
                    wf.memory_context_string = format_memory_context(wf.selected)
                    wf._active_directives = apply_directives(wf.memory_context_string, DIRECTIVES)
                    wf._active_directive_names = {d.name for d in wf._active_directives}
                    wf._has_negative_preferences = 'negative_preferences' in wf._active_directive_names
                    for _directive in wf._active_directives:
                        if _directive.name == 'medical_warning':
                            logger.warning('%s Health slots detected — critical warning active', _directive.log_tag)
                        elif _directive.name == 'family_context':
                            logger.info('[FAMILY-CONTEXT-021] Family relations detected in memory context')
                        else:
                            logger.info('%s Negative preferences found in memory context', _directive.log_tag)
                    wf._id_tag = f'+identity({wf._identity.name})' if wf._identity.name else ''
                    logger.info(f'[CONTEXT V2] Budget-aware: {len(wf.selected)} slots, {wf.budget.used_memory}/{wf.budget.memory_budget} tk{wf._id_tag}')
                    wf._fact_coupons = extract_fact_coupons(wf.selected, wf.user_text)
                    wf._formatted_coupons = format_fact_coupons(wf._fact_coupons)
                    if wf._fact_coupons:
                        logger.info(f'[FACT COUPONS] Generated {len(wf._fact_coupons)} deterministic coupons')
                except Exception as v2_err:
                    logger.error(f'[CONTEXT V2] Fehler im V2-Pfad, Fallback auf V1: {v2_err}', exc_info=True)
                    wf.memory_context_string = self.context_builder._get_memory_context(wf.relevant_facts)
            else:
                wf.memory_context_string = self.context_builder._get_memory_context(wf.relevant_facts)
                logger.info('[CONTEXT V1] Memory V2 disabled, using legacy context')
            if not wf._active_directives and wf.memory_context_string:
                wf._active_directives = apply_directives(wf.memory_context_string, DIRECTIVES)
                wf._active_directive_names = {d.name for d in wf._active_directives}
                wf._has_negative_preferences = 'negative_preferences' in wf._active_directive_names
                for _directive in wf._active_directives:
                    if _directive.name == 'medical_warning':
                        logger.warning('%s Health slots detected — critical warning active', _directive.log_tag)
                    elif _directive.name == 'family_context':
                        logger.info('[FAMILY-CONTEXT-021] Family relations detected in memory context')
                    else:
                        logger.info('%s Negative preferences found in memory context', _directive.log_tag)
            try:
                from backend.services.calendar.calendar_memory import (
                    load_calendar_snapshot,
                    render_calendar_context,
                    render_proactive_calendar_guidance,
                )
                if getattr(wf, "calendar_snapshot", None) is None:
                    wf.calendar_snapshot = load_calendar_snapshot(self.db)
                wf.calendar_context_string = render_calendar_context(
                    wf.calendar_snapshot,
                    wf.user_text,
                    now=wf._now_local,
                )
                wf.calendar_proactive_guidance = render_proactive_calendar_guidance(
                    wf.calendar_snapshot,
                    wf.user_text,
                    now=wf._now_local,
                )
                if wf.calendar_context_string:
                    wf.memory_context_string = (
                        f"{wf.memory_context_string}\n\n{wf.calendar_context_string}"
                        if wf.memory_context_string
                        else wf.calendar_context_string
                    )
                    logger.info(
                        "[CALENDAR-MEMORY] Injected calendar snapshot context (%d chars)",
                        len(wf.calendar_context_string),
                    )
            except Exception as calendar_ctx_err:
                logger.warning(
                    "[CALENDAR-MEMORY] Context injection skipped: %s",
                    calendar_ctx_err,
                    exc_info=True,
                )
            wf.stripped_input = wf.user_text.strip()
            wf.is_menu_selection = (wf.stripped_input in ['1', '2', '3'] or wf.stripped_input in ['1.', '2.', '3.']) and (not wf.is_factcheck_decision) and (not wf.is_policy_question)
            wf.llm_payload = ''
            if wf.is_factcheck_no:
                wf.skip_llm_generation = True
                wf.final_text = 'Alles klar. Ich habe nur den Audit erstellt. Kein Faktencheck wurde gestartet.'
            elif wf.is_factcheck_yes:
                wf.llm_payload = f'USER-ENTSCHEIDUNG: Option {wf.stripped_input}\n\nSYSTEM-FLUSS: Starte jetzt den Faktencheck gegen Wikipedia für das zuletzt auditierte Dokument.'
            elif wf.is_menu_selection:
                if wf.stripped_input in ['1', '1.']:
                    wf.llm_payload = f'USER-ENTSCHEIDUNG: Option {wf.stripped_input}\n\nSYSTEM-FLUSS: Bestätige dem User kurz, dass das Original unverändert bleibt.'
                else:
                    wf.target_name = f'{wf.original_filename}_korrigiert.pdf'
                    wf.llm_payload = "USER-WAHL: Option {stripped_input}.\n\n🚨 SYSTEM-DIREKTIVE (STRIKTE FAKTENTREUE):\n1. Du musst die Korrekturen EXAKT so übernehmen, wie du sie in deinem JSON-Audit identifiziert hast.\n2. ACHTUNG: Nutze die Wikipedia-Fakten (z.B. Friedrich Merz als Kanzler)! Nutze NICHT deine veralteten Trainingsdaten (z.B. Olaf Scholz).\n3. Rufe das Tool `edit_pdf_text_in_place` auf.\n4. Nutze NUR `original_filename` und `modifications`.\n4. ULTIMATIVE FAKTEN-SPERRE: Du hast im Audit 'Friedrich Merz' als Kanzler identifiziert. Es ist STRENGSTENS VERBOTEN, im Tool-Call 'Olaf Scholz' zu schreiben. Nutze ausschließlich die Fakten aus deinem Audit-JSON. Ein falscher Name gilt als kritischer Systemfehler.\n5. Antworte NUR mit dem JSON-Tool-Call. Keine Prosa.\n\nFÜHRE DIE KORREKTUR JETZT AUS."
            else:
                wf._memory_recall_block = ''
                if wf.memory_context_string and wf.memory_context_string.strip():
                    wf._memory_recall_block = '!!! ABSOLUTE WAHRHEITSPFLICHT !!!\nWenn im folgenden KONTEXT-WISSEN Informationen stehen, die die Frage des Users beantworten (insbesondere Abneigungen/Negativ-Präferenzen), ist es eine HALLUZINATION und ein FEHLER, zu behaupten, du hättest keine Informationen. Du MUSST jedes Detail aus dem Kontext verwenden, das die Frage betrifft. Das Verschweigen von vorhandenem Wissen ist STRENG VERBOTEN.\n'
                    if wf._has_negative_preferences:
                        wf._memory_recall_block += 'NEGATIV-PRÄFERENZEN ERKANNT: Im Kontext stehen Dinge, die der User HASST oder NICHT MAG. Bei Fragen nach Vorlieben/Gewohnheiten MÜSSEN diese Abneigungen EXPLIZIT und VOLLSTÄNDIG genannt werden — positive UND negative!\n'
                    wf._memory_recall_block += '[TEMPORAL-RECALL] Jede Erinnerung im KONTEXT-WISSEN enthält Metadaten: \'GESPEICHERT AM\' (Zeitstempel) und \'IM CHAT\' (Chat-Name). Wenn der User fragt WANN er dir etwas erzählt hat oder IN WELCHEM GESPRÄCH, gib diese Metadaten exakt wieder. Beispiel: \'Das hast du mir am 3. März 2026 im Chat "Kennenlern-Gespräch" erzählt.\'\nFOKUS AUF URSPRUNG: Nenne primär den Zeitpunkt der ERSTEN Erwähnung eines Fakts. Wiederholte Bestätigungen desselben Fakts sind NICHT separat aufzulisten. Erwähne sie nur, wenn sie neue Details enthalten oder der User explizit nach allen Erwähnungen fragt.\n!!! DYNAMISCHE KONSISTENZ-PFLICHT !!!: Die Chat-Titel im folgenden KONTEXT-WISSEN sind die EINZIGE \'Single Source of Truth\'. Wenn sich ein Chat-Name gegenüber früher im Gesprächsverlauf geändert hat, MUSST du zwingend den NEUEN Namen aus dem KONTEXT-WISSEN verwenden. Ignoriere veraltete Chat-Namen aus dem bisherigen Gesprächsverlauf — sie sind OBSOLET.\n'
                    if wf.calendar_proactive_guidance:
                        wf._memory_recall_block += wf.calendar_proactive_guidance + '\n'
                    wf._memory_recall_block += '\n'
                wf.llm_payload = f"ACHTUNG: Die folgenden Daten enthalten 'Dauerhafte Merkmale' und 'Einmalige Beobachtungen'. NUTZE FÜR BESCHREIBUNGEN NUR DIE DAUERHAFTEN MERKMALE (Physis). IGNORIERE FOLGENDES BEI BESCHREIBUNGEN VON PERSONEN: 'Mantel', 'Jacke', 'Schal', 'T-Shirt', 'Anzug', 'Krawatte', 'Kleid', 'Hose', 'Rock', 'Schuhe'. AKZENTUIERE HINGEGEN: 'Brille', 'Sonnenbrille', 'Kopfhörer', 'Headset', 'Smartwatch', 'Piercing', 'auffällige Kette'.\n{wf._memory_recall_block}KONTEXT-WISSEN (AUS DB):\n{wf.memory_context_string}\n\nUSER-ANFRAGE: {wf.user_text}\n\nAUFGABE: Bestätige kurz, wenn der User eine Information ergänzt. Erstelle ein Porträt nur bei expliziter Anfrage des Users. Wenn der User nach spezifischen Accessoires fragt (z.B. 'Trägt er Kopfhörer?'), durchsuche die Kategorie 'Aussehen_Situativ'. Wenn der User nur 'Beschreibe ihn' fragt, ignoriere diese Kategorie."
            if not wf.skip_llm_generation:
                wf.final_text_to_generate = wf.llm_payload
            if not wf.skip_llm_generation and wf.is_factcheck_yes:
                wf.final_text_to_generate += '\n\n--- SYSTEM-BEFEHL: AUTO-AUDIT & JSON-AUSGABE ---\nFühre einen Faktencheck des Dokuments gegen Wikipedia durch. Deine Antwort MUSS ausschließlich ein einziges JSON-Objekt sein, ohne begleitenden Text. Das JSON MUSS diesem Schema folgen:\n\n```json\n{\n  "audit_summary": "Ein für Menschen lesbarer Bericht über deine Funde. Identifiziere jeden Fehler und schlage eine Korrektur vor. Beende diesen Text zwingend mit den 3 Aktions-Optionen.",\n  "modifications_list": [\n    {\n      "search": "Der exakte, wörtliche Text aus der PDF, der fehlerhaft ist.",\n      "replace": "Der neue, korrigierte Text. Bei Löschung leer lassen."\n    }\n  ]\n}\n```\n\n🚨 KRITISCHE REGELN FÜR `modifications_list`:\n1. Jeder gefundene Fehler MUSS ein Eintrag in der Liste sein.\n2. Der `search`-Wert muss ein **EXAKTES, WÖRTLICHES KOPIAT** des Textes aus der PDF sein. Nicht paraphrasieren! Das ist der häufigste Fehler.\n3. Der `replace`-Wert enthält die Korrektur oder einen leeren String zum Löschen.\nPRODUZIERE JETZT AUSSCHLIESSLICH DIESES JSON-OBJEKT.'
            elif not wf.skip_llm_generation and wf.is_audit_request:
                wf.final_text_to_generate += '\n\n--- SYSTEM-BEFEHL: DOKUMENT-AUDIT OHNE FAKTENCHECK ---\nErstelle einen präzisen Audit-Bericht zum hochgeladenen Dokument. Nutze dafür ausschließlich den Dokumentinhalt und KEINEN Wikipedia-Abgleich in diesem Schritt.\n\nDeine Antwort soll enthalten:\n1. ### Zusammenfassung\n2. ### Die 3 wichtigsten Punkte\n\nWICHTIG: Füge am Ende exakt diese Auswahl hinzu:\nMöchtest du jetzt einen Faktencheck durchführen?\n1. Ja\n2. Nein'
        ctx.memory_context_string = wf.memory_context_string
        if getattr(wf, 'selected', None) is not None:
            ctx.selected_slots = list(wf.selected)
        ctx.formatted_fact_coupons = str(getattr(wf, '_formatted_coupons', '') or '')
        return ctx

    async def _execute_generation(self, ctx: RequestContext) -> RequestContext:
        from backend.services.orchestrator.execution_dispatcher import execute_generation

        # 💎 PROVIDER-COHERENCE FIX: Preventive Provider Check BEFORE Gateway call
        # If request.model belongs to Provider X, request.provider must be set to X immediately
        model = str(getattr(ctx.request, "model", "") or "").strip().lower()
        provider = str(getattr(ctx.request, "provider", "") or "").strip().lower()

        if model:
            # Detect provider from model prefix/pattern
            detected_provider = None
            if model.startswith("gpt-"):
                detected_provider = "openai"
            elif model.startswith("gemini-"):
                detected_provider = "gemini"
            elif model.startswith("claude-"):
                detected_provider = "anthropic"
            elif ":" in model or model.startswith("llama") or model.startswith("llava"):
                detected_provider = "ollama"

            if detected_provider and detected_provider != provider:
                logger.info(
                    "[PROVIDER-COHERENCE] Model '%s' belongs to provider '%s', but request.provider is '%s'. "
                    "Auto-correcting provider to '%s'.",
                    model,
                    detected_provider,
                    provider,
                    detected_provider,
                )
                ctx.request.provider = detected_provider

                # 💎 AUTH-COHERENCE FIX: Always reload API key for healed provider
                # Critical: If provider was corrected, the old key belongs to the wrong provider
                import keyring
                new_api_key = None
                if detected_provider == 'ollama':
                    # Ollama uses placeholder key
                    new_api_key = 'ollama'
                    logger.info(
                        "[AUTH-COHERENCE] Loading key for %s: %s...",
                        detected_provider,
                        new_api_key[:4],
                    )
                else:
                    new_api_key = keyring.get_password('Janus-Projekt', detected_provider)
                    if new_api_key:
                        logger.info(
                            "[AUTH-COHERENCE] Loading key for %s: %s...",
                            detected_provider,
                            new_api_key[:4],
                        )
                    else:
                        logger.error(
                            "[AUTH-COHERENCE] No key found in keyring for provider: %s",
                            detected_provider,
                        )
                if new_api_key:
                    ctx.request.api_key = new_api_key

        logger.info(
            "[ORCH-PIPELINE] _execute_generation → execution_dispatcher.execute_generation "
            "(chat_id=%s provider=%s model=%s)",
            getattr(ctx.request, "chat_id", None),
            getattr(ctx.request, "provider", None),
            getattr(ctx.request, "model", None),
        )
        
        # Log routing decision with selected model in payload
        from backend.services.logging.logger_core import log_event
        from backend.data.schemas_logging import LogEventCreate
        try:
            await log_event(LogEventCreate(
                session_id=str(getattr(ctx.request, "chat_id", "") or ""),
                provider=str(getattr(ctx.request, "provider", "") or "").lower(),
                model=str(getattr(ctx.request, "model", "") or "").lower(),
                event_type="routing_decision",
                status="success",
                payload={
                    "input_hash": str(hash(str(getattr(ctx.request, "prompt", "") or ""))),
                    "output_summary": f"Routed to provider={ctx.request.provider}, model={ctx.request.model}",
                    "error_code": None
                }
            ))
        except Exception as log_exc:
            logger.error(f"Failed to log routing_decision: {log_exc}")

        # 💎 CU-4: Sende status_update Event für UI-Feedback bei langen Anfragen
        from backend.services.orchestrator.stream_protocol import StreamEvent
        # Schätze Token-Anzahl für Entscheidung
        prompt_text = str(getattr(ctx.request, "prompt", "") or "")
        estimated_tokens = len(prompt_text.split())  # Grobe Schätzung: ~1 Token pro Wort
        is_long_request = estimated_tokens > 1000  # >1000 Wörter = lange Anfrage

        if is_long_request:
            logger.info(f"[CU-4] Long request detected ({estimated_tokens} tokens), sending thinking_long_request status")
            # Sende Event über den Generator (wird im execution_dispatcher verarbeitet)
            status_event = StreamEvent(
                type="status_update",
                content={"status": "thinking_long_request"}
            )
            # Speichere im ctx, damit execution_dispatcher es in gateway_kwargs übergeben kann
            ctx._pending_status_update = status_event

        return await execute_generation(
            ctx,
            db=self.db,
            context_manager=self.context_manager,
            orchestrator_context_manager=self.orchestrator_context,
            execution_engine=self.execution_engine,
            skill_selector=self.skill_selector,
            prompt_role_from_db_role=self._prompt_role_from_db_role,
            set_policy_pending_data=self._set_policy_pending_data,
            user_budget_info=getattr(self, '_user_budget_info', None),
        )

    async def _finalize_response(self, ctx: RequestContext) -> Dict:
        from backend.services.orchestrator.response_finalizer import finalize_response

        return await finalize_response(
            ctx,
            db=self.db,
            background_tasks=ctx.background_tasks,
            status_sync=self.status_sync,
            model_hierarchy=self.MODEL_HIERARCHY,
            orchestrator_cls=ChatOrchestrator,
        )

    async def handle_chat_request(self, request: schemas.ChatRequest, background_tasks: Any = None) -> Dict:
        # Set trace_id for this request context
        from backend.services.logging.logger_core import set_trace_id, generate_trace_id
        trace_id = str(request.chat_id) if request.chat_id else generate_trace_id()
        set_trace_id(trace_id)
        
        try:
            ctx = self._classify_request(request, background_tasks)
            early = await self._try_early_exit(ctx)
            if early is not None:
                return early
            ctx = await self._build_memory_context(ctx)
            ctx = await self._execute_generation(ctx)
            return await self._finalize_response(ctx)
        except Exception as exc:
            # Log error event to Supabase
            try:
                from backend.services.logging.logger_core import log_event
                from backend.data.schemas_logging import LogEventCreate
                
                await log_event(LogEventCreate(
                    session_id=str(request.chat_id or ""),
                    provider=str(request.provider or "").lower(),
                    model=str(request.model or ""),
                    event_type="error",
                    status="error",
                    payload={"error": str(exc), "request_type": "chat_request"}
                ))
            except Exception as log_exc:
                logger.error(f"Failed to log error event: {log_exc}")
            raise

    def _iter_modal_request_stream_events(self, ctx: Any):
        """Nach ``finalize_response_async``: StreamEvent(s), damit SSE-Clients ``modal_request`` wie POST /chat erhalten."""
        from backend.services.orchestrator.stream_protocol import StreamEvent

        wf = getattr(ctx, "workflow", None)
        if wf is None:
            return
        ex = getattr(wf, "execution_for_api", None)
        if ex is None:
            return
        mr = getattr(ex, "modal_request", None)
        if mr is None:
            return
        try:
            payload = mr.model_dump(mode="json")
        except Exception:
            payload = None
        if not isinstance(payload, dict):
            return
        yield StreamEvent(type="modal_request", content=payload)

    async def handle_chat_request_stream(
        self,
        request: schemas.ChatRequest,
        background_tasks: Any = None,
    ):
        """Stream-Pfad: classify + memory → commit/expunge → Tool-Loop-Stream → finalize_async (frische Session)."""
        from backend.services.orchestrator.execution_dispatcher import (
            apply_post_generation_tail,
            apply_run_tool_loop_result_to_workflow,
            execute_generation_prepare_gateway,
        )
        from backend.services.orchestrator.response_finalizer import finalize_response_async
        from backend.services.orchestrator.stream_protocol import StreamEvent

        try:
            ctx = self._classify_request(request, background_tasks)
            early = await self._try_early_exit(ctx)
            if early is not None:
                wf = ctx.workflow
                if isinstance(early, ExecutionResponse):
                    wf.final_text = str(early.text or "")
                    wf.execution_for_api = early
                elif isinstance(early, dict):
                    wf.final_text = str(early.get("text") or early.get("message") or "")
                else:
                    wf.final_text = str(early)
                wf.run_tool_loop_result = None
                wf.response = {}
                yield StreamEvent(type="stream_complete", content={"text": wf.final_text})
                await finalize_response_async(
                    ctx,
                    model_hierarchy=self.MODEL_HIERARCHY,
                    orchestrator_cls=ChatOrchestrator,
                )
                for ev in self._iter_modal_request_stream_events(ctx):
                    yield ev
                return

            # 💎 STREAM-SWITCH: Video-Listen → Block-Response für stabile Markdown-Links
            _wf_check = ctx.workflow
            _idr = getattr(_wf_check, "intent_detection_result", None)
            if _idr is not None and _idr.is_video_list_intent:
                logger.info("💎 STREAM-SWITCH: Video-List-Intent erkannt → Block-Response für stabile Links")
                ctx = await self._build_memory_context(ctx)
                ctx = await self._execute_generation(ctx)
                result = await self._finalize_response(ctx)
                wf = ctx.workflow

                # Extract text from result
                if isinstance(result, ExecutionResponse):
                    block_text = str(result.text or "")
                elif isinstance(result, dict):
                    block_text = str(result.get("text") or result.get("message") or "")
                else:
                    block_text = str(result)

                # 💎 Extract video-list metadata from tool results for frontend cards
                _video_meta = None
                _all_tr = []
                if isinstance(result, ExecutionResponse):
                    _all_tr = result.all_tool_results or []
                elif isinstance(result, dict):
                    _all_tr = result.get("all_tool_results") or []
                for _tr in _all_tr:
                    if not isinstance(_tr, dict):
                        continue
                    _raw = _tr.get("_raw_content") or _tr.get("content", "{}")
                    try:
                        _parsed = json.loads(_raw) if isinstance(_raw, str) else dict(_raw or {})
                    except Exception:
                        continue
                    if isinstance(_parsed, dict) and _parsed.get("status") == "ok":
                        _data = _parsed.get("data") if isinstance(_parsed.get("data"), dict) else {}
                        if str(_data.get("mode") or "").strip().lower() == "list" and isinstance(_data.get("videos"), list):
                            _video_meta = {
                                "videos": _data["videos"],
                                "count": _data.get("count", 0),
                                "mode": "list",
                                "query": _data.get("query"),
                            }
                            break

                if _video_meta:
                    yield StreamEvent(
                        type="metadata",
                        content=_video_meta,
                        metadata={"source": "video.search.list_mode"},
                    )
                    logger.info("💎 STREAM-SWITCH: Sent %d videos metadata to frontend", len(_video_meta.get("videos", [])))

                yield StreamEvent(type="stream_complete", content={"text": block_text})
                for ev in self._iter_modal_request_stream_events(ctx):
                    yield ev
                return

            ctx = await self._build_memory_context(ctx)
            ctx = await execute_generation_prepare_gateway(
                ctx,
                db=self.db,
                context_manager=self.context_manager,
                orchestrator_context_manager=self.orchestrator_context,
                skill_selector=self.skill_selector,
                prompt_role_from_db_role=self._prompt_role_from_db_role,
                user_budget_info=getattr(self, "_user_budget_info", None),
            )
            wf = ctx.workflow
            req = ctx.request

            self.db.commit()
            self.db.expunge_all()
            wf.executor = ToolExecutor(
                self.db,
                wf.api_key,
                req.provider,
                req.model,
                additional_context={
                    "chat_id": req.chat_id,
                    "trace_id": getattr(wf, "request_trace_id", str(uuid.uuid4())),
                    "original_user_text": wf.user_text,
                    "provider": req.provider,
                    "model": req.model,
                },
            )
            if getattr(wf, "gateway_kwargs", None):
                wf.gateway_kwargs["db"] = self.db
                wf.gateway_kwargs["tool_executor"] = wf.executor
                wf.gateway_kwargs["chat_history"] = wf.messages
                wf.gateway_kwargs["_workflow"] = wf

            if wf.skip_llm_generation:
                wf.final_text = wf.final_text or wf.final_text_to_generate
                if not isinstance(getattr(wf, "response", None), dict):
                    wf.response = {}
                yield StreamEvent(type="stream_complete", content={"text": wf.final_text})
                apply_post_generation_tail(ctx)
                ctx.final_response = str(wf.final_text or "")
                await finalize_response_async(
                    ctx,
                    model_hierarchy=self.MODEL_HIERARCHY,
                    orchestrator_cls=ChatOrchestrator,
                )
                for ev in self._iter_modal_request_stream_events(ctx):
                    yield ev
                return

            result_holder: Dict[str, Any] = {}
            async for ev in self.execution_engine.run_tool_loop_stream(
                orchestrator_context=wf.orchestrator_context,
                tool_executor=wf.executor,
                gateway_kwargs=wf.gateway_kwargs,
                fallback_summary=wf.fallback_summary,
                current_limit=wf.current_limit,
                bypass_policy_this_turn=wf.bypass_policy_this_turn,
                set_policy_pending=self._set_policy_pending_data,
                chat_id=req.chat_id,
                agent_flow_error=wf.agent_flow_error,
                result_holder=result_holder,
            ):
                yield ev

            wf.run_tool_loop_result = result_holder.get("execution_result")
            apply_run_tool_loop_result_to_workflow(ctx)
            apply_post_generation_tail(ctx)
            ctx.final_response = str(wf.final_text or "")
            await finalize_response_async(
                ctx,
                model_hierarchy=self.MODEL_HIERARCHY,
                orchestrator_cls=ChatOrchestrator,
            )
            for ev in self._iter_modal_request_stream_events(ctx):
                yield ev
        except Exception as exc:
            # Log error event to Supabase
            try:
                from backend.services.logging.logger_core import log_event
                from backend.data.schemas_logging import LogEventCreate
                
                await log_event(LogEventCreate(
                    session_id=str(request.chat_id or ""),
                    provider=str(request.provider or "").lower(),
                    model=str(request.model or ""),
                    event_type="error",
                    status="error",
                    payload={"error": str(exc), "request_type": "chat_request_stream"}
                ))
            except Exception as log_exc:
                logger.error(f"Failed to log error event: {log_exc}")
            
            # Yield error event to stream
            yield StreamEvent(
                type="error",
                content={"error": str(exc)},
                metadata={"error_type": "exception"}
            )
            raise

    def _trigger_fact_extraction(
        self,
        chat_id,
        user_text,
        final_text,
        api_key,
        provider,
        model_id: Optional[str] = None,
        learned_name: Optional[str] = None,
        skip_fact_extraction: bool = False,
    ):
        from backend.services.orchestrator.response_finalizer import trigger_fact_extraction as _trigger

        _trigger(
            chat_id,
            user_text,
            final_text,
            api_key,
            provider,
            model_id=model_id,
            learned_name=learned_name,
            skip_fact_extraction=skip_fact_extraction,
            model_hierarchy=self.MODEL_HIERARCHY,
        )
