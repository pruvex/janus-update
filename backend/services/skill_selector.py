import logging
import re
from typing import Dict, List, Set

import chromadb

from backend.services import vector_service
from backend.services.skill_router import (
    skill_router,
    get_blocked_skills_for_query,
    is_realtime_search_query,
    prioritize_skills_for_query,
)

logger = logging.getLogger("janus_backend")


class SkillSelector:
    """Hierarchical skill discovery: semantic retrieval + domain prioritization."""

    DOMAIN_KEYWORDS: Dict[str, List[str]] = {
        "communication": ["mail", "email", "e-mail", "inbox", "nachricht"],
        "filesystem": [
            "datei", "dateien", "file", "files",
            "ordner", "folder", "folders",
            "verzeichnis", "verzeichnisse", "directory", "directories",
            "pfad", "pfade", "path",
            "auflisten", "list",
        ],
        "knowledge": ["dokument", "pdf", "wissen", "suche", "recherche"],
        "calendar": ["kalender", "termin", "meeting", "event"],
        "system": [
            "web",
            "wetter",
            "wiki",
            "route",
            "news",
            "restaurant",
            "restaurants",
            "pizzeria",
            "apotheke",
            "arzt",
            "ärzte",
            "supermarkt",
            "baumarkt",
            "museum",
            "kino",
            "hotel",
            "café",
            "cafe",
            "bar",
            "geschäft",
            "geschäfte",
            "poi",
            "pois",
            "land",
            "hauptstadt",
            "einwohner",
            "bevölkerung",
            "bevoelkerung",
            "währung",
            "waehrung",
            "country",
            "capital",
            "population",
            "currency",
        ],
        "memory": ["erinner", "memory", "historie"],
        "contacts": ["kontakt", "adresse", "telefon"],
    }

    def get_relevant_skills(self, user_prompt: str, top_k: int = 10) -> List[str]:
        prompt = str(user_prompt or "").strip()
        if not prompt:
            return []

        if is_realtime_search_query(prompt):
            blocked_skills = get_blocked_skills_for_query(prompt)
            semantic_hits = [skill for skill in self._semantic_search(prompt=prompt, top_k=top_k) if skill not in blocked_skills]
            domain_hits = [skill for skill in self._domain_priorities(prompt=prompt) if skill not in blocked_skills]
            relevant = prioritize_skills_for_query(prompt, domain_hits + semantic_hits, top_k=3)

            unique: List[str] = []
            seen: Set[str] = set()
            for skill_id in relevant:
                sid = str(skill_id or "").strip()
                if not sid or sid in seen:
                    continue
                seen.add(sid)
                unique.append(sid)
            return unique[:15]

        relevant: List[str] = []
        semantic_hits = self._semantic_search(prompt=prompt, top_k=top_k)
        domain_hits = self._domain_priorities(prompt=prompt)

        # Stage-2 domain check can reprioritize semantic hits for clear keywords.
        if domain_hits:
            relevant.extend(domain_hits)
            relevant.extend(semantic_hits)
        else:
            relevant.extend(semantic_hits)

        unique: List[str] = []
        seen: Set[str] = set()
        for skill_id in relevant:
            sid = str(skill_id or "").strip()
            if not sid or sid in seen:
                continue
            seen.add(sid)
            unique.append(sid)

        return unique[:15]

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

    def _domain_priorities(self, *, prompt: str) -> List[str]:
        lowered = prompt.lower()
        prioritized_domains: List[str] = []
        # Detect drive-letter paths (C:\, D:/, etc.) or UNC paths -> filesystem intent
        has_path_pattern = bool(re.search(r"[a-zA-Z]:[\\/]|\\\\[a-zA-Z0-9]", prompt))
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(self._contains_keyword(lowered, keyword) for keyword in keywords):
                prioritized_domains.append(domain)

        if has_path_pattern and "filesystem" not in prioritized_domains:
            prioritized_domains.insert(0, "filesystem")

        if not prioritized_domains:
            return []

        all_skill_ids = skill_router.get_skill_ids()
        domain_skills: List[str] = []
        for domain in prioritized_domains:
            prefix = f"{domain}."
            domain_skills.extend([skill for skill in all_skill_ids if skill.startswith(prefix)])
        return domain_skills

    def _contains_keyword(self, lowered_prompt: str, keyword: str) -> bool:
        token = str(keyword or "").strip().lower()
        if not token:
            return False
        pattern = r"\b" + re.escape(token) + r"\b"
        return bool(re.search(pattern, lowered_prompt))
