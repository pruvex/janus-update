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

        combined = mandatory_filtered + boosted_filtered + semantic_hits
        combined = self._deduplicate(combined)
        combined = [s for s in combined if s not in forbidden]

        if combined and set(combined) != set(mandatory_filtered):
            logger.debug(
                "SKILL-SELECTOR: intent=%s mandatory=%s total=%d",
                getattr(intent_result, "primary_intent", None),
                mandatory_filtered,
                len(combined),
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
        forbidden: List[str] = []
        if getattr(intent_result, "is_calendar_intent", False) or primary == "calendar":
            mandatory = ["calendar.list_events", "calendar.find_slots", "calendar.find_and_update_event"]
            forbidden = ["system.create_pdf"]
        elif getattr(intent_result, "is_shopping_intent", False) or primary == "shopping":
            mandatory = ["system.price_comparison"]
            forbidden = ["system.websearch"]
        return {"mandatory": mandatory, "boosted": [], "forbidden": forbidden}

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
