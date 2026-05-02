import logging
from typing import Dict, List, Optional, Set, TYPE_CHECKING

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
    """Semantic skill discovery constrained by CapabilityRegistry or explicit allow-lists."""

    def __init__(self, capability_registry: Optional["CapabilityRegistry"] = None) -> None:
        self._capability_registry = capability_registry

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

    def get_relevant_skills(
        self,
        user_prompt: str,
        top_k: int = 10,
        *,
        allowed_skill_ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Rank skills via Chroma; optional scope = registry universe and/or explicit allow-list."""
        prompt = str(user_prompt or "").strip()
        if not prompt:
            return []

        allowed = {
            str(sid).strip()
            for sid in (allowed_skill_ids or [])
            if str(sid or "").strip()
        }
        registry_universe = self._registry_skill_universe()
        universe = allowed if allowed else registry_universe

        if is_realtime_search_query(prompt):
            blocked_skills = get_blocked_skills_for_query(prompt)
            semantic_hits = [
                skill
                for skill in self._semantic_search(prompt=prompt, top_k=top_k)
                if skill not in blocked_skills
            ]
            semantic_hits = self._within_universe(semantic_hits, universe)
            ranked = prioritize_skills_for_query(prompt, semantic_hits, top_k=3)
        else:
            semantic_hits = self._semantic_search(prompt=prompt, top_k=top_k)
            semantic_hits = self._within_universe(semantic_hits, universe)
            ranked = semantic_hits

        unique: List[str] = []
        seen: Set[str] = set()
        for skill_id in ranked:
            sid = str(skill_id or "").strip()
            if not sid or sid in seen:
                continue
            seen.add(sid)
            unique.append(sid)

        return unique[:15]

    @staticmethod
    def _within_universe(skills: List[str], universe: Optional[Set[str]]) -> List[str]:
        if not universe:
            return list(skills or [])
        return [s for s in (skills or []) if str(s or "").strip() in universe]

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
