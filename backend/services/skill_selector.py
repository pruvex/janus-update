import logging
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

import chromadb

from backend.services import vector_service
from backend.services.skill_router import (
    get_blocked_skills_for_query,
    is_realtime_search_query,
    prioritize_skills_for_query,
)

if TYPE_CHECKING:
    from backend.services.capability_registry import CapabilityRegistry

logger = logging.getLogger("janus_backend")


class SkillSelector:
    """Intent-driven skill discovery constrained by CapabilityRegistry.

    Selection order:
      1. Mandatory skills (from intent policy) — always present, placed first.
      2. Boosted skills   (from intent policy) — promoted before semantic hits.
      3. Semantic hits    (ChromaDB)           — optional enrichment.
    Registry universe and ``allowed_skill_ids`` are applied as hard filters throughout.
    Forbidden skills from the policy are removed from every bucket.
    """

    def __init__(self, capability_registry: Optional["CapabilityRegistry"] = None) -> None:
        self._capability_registry = capability_registry

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_relevant_skills(
        self,
        user_prompt: str,
        top_k: int = 10,
        *,
        intent_result: Optional[Any] = None,
        allowed_skill_ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Return a deduplicated, intent-bootstrapped skill list.

        Mandatory tools from the intent policy precede Chroma hits.
        The registry universe acts as a ceiling; ``allowed_skill_ids`` (if given)
        narrows it further.
        """
        prompt = str(user_prompt or "").strip()
        if not prompt:
            return []

        # --- Policy from intent (zero cost: pure logic) ---
        policy = self._intent_policy(intent_result)
        mandatory: List[str] = policy["mandatory"]
        boosted: List[str] = policy["boosted"]
        forbidden: Set[str] = set(policy["forbidden"])

        # --- Universe: registry ∩ allowed_skill_ids ---
        registry_universe = self._registry_skill_universe()
        explicit_allowed: Set[str] = {
            str(sid).strip()
            for sid in (allowed_skill_ids or [])
            if str(sid or "").strip()
        }
        # Combined universe: if caller passed allowed list, intersect; else registry only.
        universe: Optional[Set[str]] = (
            explicit_allowed & registry_universe
            if (explicit_allowed and registry_universe)
            else explicit_allowed or registry_universe
        )

        # --- Semantic search for optional tools ---
        if is_realtime_search_query(prompt):
            blocked_skills = get_blocked_skills_for_query(prompt)
            semantic_hits = [
                skill
                for skill in self._semantic_search(prompt=prompt, top_k=top_k)
                if skill not in blocked_skills
            ]
            semantic_hits = self._within_universe(semantic_hits, universe)
            semantic_hits = prioritize_skills_for_query(prompt, semantic_hits, top_k=3)
        else:
            semantic_hits = self._semantic_search(prompt=prompt, top_k=top_k)
            semantic_hits = self._within_universe(semantic_hits, universe)

        # --- Merge: mandatory → boosted → semantic ---
        # Mandatory and boosted must pass universe check too (they may not be indexed in Chroma).
        mandatory_filtered = self._within_universe(mandatory, universe) or mandatory  # keep even if not in universe
        boosted_filtered = self._within_universe(boosted, universe)

        # 💎 DIAMOND-CORE-ROUTING-FIX
        # Wir prüfen sowohl Objekt-Attribute als auch Dictionary-Keys für maximale Robustheit
        intent_name = ""
        if hasattr(intent_result, "primary_intent"):
            intent_name = str(intent_result.primary_intent)
        elif isinstance(intent_result, dict):
            intent_name = str(intent_result.get("primary_intent", ""))

        if "routing" in intent_name.lower() or primary == "routing_geo":
            if "system.routing" not in mandatory:
                mandatory.append("system.routing")
                # Use module-level logger directly
                try:
                    logger.info(f"!!! DIAMOND-FIX-TRIGGERED !!! Routing forced. Intent: {intent_name}")
                except NameError:
                    # Fallback if logger is not in scope
                    logging.getLogger("janus_backend").info(f"!!! DIAMOND-FIX-TRIGGERED !!! Routing forced. Intent: {intent_name}")

        combined = mandatory_filtered + boosted_filtered + semantic_hits
        combined = self._deduplicate(combined)
        combined = [s for s in combined if s not in forbidden]

        if combined and set(combined) != set(mandatory_filtered):
            # 💎 TASK-004: BACKLOG-004 - Logging für gewählte Tools basierend auf Intent
            primary_intent = getattr(intent_result, "primary_intent", None)
            is_filesystem = getattr(intent_result, "is_filesystem_intent", False)
            is_calendar = getattr(intent_result, "is_calendar_intent", False)
            logger.info(
                "[SKILL-SELECTOR] Selected %d skills (intent=%s, filesystem=%s, calendar=%s): mandatory=%s, total=%s",
                len(combined),
                primary_intent,
                is_filesystem,
                is_calendar,
                mandatory_filtered,
                combined[:5]  # Log nur die ersten 5 Skills um Log-Overflow zu vermeiden
            )
        elif combined:
            logger.debug(
                "[SKILL-SELECTOR] Only mandatory skills selected: %s",
                mandatory_filtered
            )

        return combined[:max(top_k, len(mandatory_filtered))]  # never truncate mandatory tools

    def filter_capability_groups(
        self,
        capability_groups: Dict[str, List[str]],
        allowed_skill_ids: List[str],
    ) -> Dict[str, List[str]]:
        allowed = {str(skill_id) for skill_id in (allowed_skill_ids or []) if str(skill_id).strip()}
        if not allowed:
            return dict(capability_groups or {})

        filtered: Dict[str, List[str]] = {}
        for capability, skills in (capability_groups or {}).items():
            scoped = [skill for skill in (skills or []) if skill in allowed]
            if scoped:
                filtered[str(capability)] = scoped
        return filtered

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _intent_policy(self, intent_result: Optional[Any]) -> Dict[str, List[str]]:
        if intent_result is None:
            return {"mandatory": [], "boosted": [], "forbidden": []}
        if self._capability_registry is not None and hasattr(
            self._capability_registry, "get_intent_skill_policy"
        ):
            return self._capability_registry.get_intent_skill_policy(intent_result)
        # Fallback: minimal hardcoded safety net when no registry is wired.
        primary = str(getattr(intent_result, "primary_intent", "") or "")
        mandatory: List[str] = []
        boosted_fb: List[str] = []
        forbidden: List[str] = []
        pdf_ok = (
            bool(getattr(intent_result, "is_multitask_image_pdf", False))
            or bool(getattr(intent_result, "is_complex_document_request", False))
            or bool(getattr(intent_result, "is_explicit_pdf_intent", False))
        )
        if not pdf_ok:
            forbidden.append("system.create_pdf")
        if bool(getattr(intent_result, "is_routing_geo_intent", False)) or primary in ["routing_geo", "routing", "geo"] or "routing" in primary:
            # BACKLOG-029: Routing-Intent must be mandatory to force tool call instead of LLM knowledge
            mandatory.append("system.routing")
            logger.info(f"DEBUG-MANDATORY: Added system.routing to mandatory list. Current list: {mandatory}")
        if bool(getattr(intent_result, "is_weather_intent", False)) or primary == "weather":
            # BACKLOG-029: Weather-Intent must be mandatory to force tool call instead of LLM knowledge
            mandatory.append("system.weather")
        if bool(getattr(intent_result, "is_wikipedia_intent", False)) or primary == "wikipedia":
            # BACKLOG-031: Wikipedia-Intent must be mandatory to force tool call instead of LLM knowledge
            mandatory.append("system.wikipedia_summary")
        if bool(getattr(intent_result, "is_news_intent", False)) or primary == "news":
            # BACKLOG-031: News-Intent must be mandatory to force tool call instead of LLM knowledge
            mandatory.append("system.rss_news")
        # 💎 TASK-005: BACKLOG-005 - Filesystem-Intent hat Vorrang vor Bild-Intent
        # Wenn Filesystem-Intent erkannt wurde, hat er Vorrang vor Bild-Intent
        is_filesystem = getattr(intent_result, "is_filesystem_intent", False) or primary == "filesystem"
        is_image = getattr(intent_result, "is_image_intent", False) or primary == "image"
        if is_filesystem and is_image:
            logger.info(
                "[SKILL-SELECTOR] Filesystem-Intent overrides Image-Intent (filesystem=%s, image=%s)",
                is_filesystem,
                is_image
            )
            # Filesystem-Intent hat Vorrang, Bild-Intent wird ignoriert
            is_image = False
        # 💎 TASK-004: BACKLOG-004 - Filesystem-Intent zu Filesystem-Tools mappen
        if is_filesystem:
            # Filesystem-Intents sollten Filesystem-Tools bevorzugen
            # (Hinweis: Aktuell gibt es keine Filesystem-Tools im Fallback,
            #  aber die Registry könnte sie bereitstellen)
            logger.debug(
                "[SKILL-SELECTOR] Filesystem intent detected, relying on registry for filesystem tools"
            )
        elif is_image:
            # Bild-Intent nur wenn nicht durch Filesystem-Intent überschrieben
            mandatory = ["system.generate_image"]
        elif getattr(intent_result, "is_calendar_intent", False) or primary == "calendar":
            mandatory = ["calendar.list_events", "calendar.find_slots", "calendar.find_and_update_event"]
            forbidden.append("system.create_pdf")
        elif getattr(intent_result, "is_shopping_intent", False) or primary == "shopping":
            mandatory = ["system.price_comparison"]
            forbidden.append("system.websearch")
        return {"mandatory": mandatory, "boosted": boosted_fb, "forbidden": forbidden}

    def _registry_skill_universe(self) -> Optional[Set[str]]:
        if self._capability_registry is None:
            return None
        groups = self._capability_registry.get_capability_groups(allowed_skill_ids=None)
        return {
            str(sid).strip()
            for skills in (groups or {}).values()
            for sid in skills or []
            if str(sid or "").strip()
        }

    @staticmethod
    def _within_universe(skills: List[str], universe: Optional[Set[str]]) -> List[str]:
        if not universe:
            return list(skills or [])
        return [s for s in (skills or []) if str(s or "").strip() in universe]

    @staticmethod
    def _deduplicate(skills: List[str]) -> List[str]:
        seen: Set[str] = set()
        result: List[str] = []
        for s in skills or []:
            sid = str(s or "").strip()
            if sid and sid not in seen:
                seen.add(sid)
                result.append(sid)
        return result

    def _semantic_search(self, *, prompt: str, top_k: int) -> List[str]:
        if vector_service.is_model_loading():
            logger.info("SKILL-SELECTOR: %s", vector_service.warmup_status_text())
            return []
        try:
            client = chromadb.PersistentClient(path=vector_service.CHROMA_PATH)
            collection = client.get_collection(name="janus_skill_index")
            results = collection.query(
                query_texts=[prompt],
                n_results=max(1, int(top_k)),
                include=["metadatas"],
            )
            metadatas = (results.get("metadatas") or [[]])[0]
            skills = [
                str(item.get("skill_id"))
                for item in metadatas
                if isinstance(item, dict) and str(item.get("skill_id") or "").strip()
            ]
            return skills
        except Exception as exc:
            logger.debug("SKILL-SELECTOR: semantische Suche fallback (%s)", exc)
            return []
