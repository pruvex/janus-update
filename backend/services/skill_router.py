import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Set, Tuple

import chromadb

from backend.services import vector_service

from backend.services.tool_manager import ToolDefinition, tool_manager

logger = logging.getLogger("janus_backend")

REALTIME_SEARCH_TRIGGER_WORDS = ["preis", "kurs", "aktuell", "heute", "gold", "aktie", "währung"]
REALTIME_BLOCKED_SKILLS = {"system.wikipedia_summary", "system.rss_news"}
REALTIME_FORCED_SKILLS = ["system.websearch", "system.price_comparison"]


def _is_price_or_quote_query(query: str) -> bool:
    prompt = str(query or "").lower()
    markers = [
        "preis",
        "preise",
        "kurs",
        "kurse",
        "goldpreis",
        "aktienkurs",
        "wechselkurs",
        "währung",
        "waehrung",
        "marktdaten",
        "feinunze",
        "spotpreis",
    ]
    return any(marker in prompt for marker in markers)


def is_realtime_search_query(query: str) -> bool:
    prompt = str(query or "").strip().lower()
    if not prompt:
        return False
    if _is_price_or_quote_query(prompt):
        return True
    return any(trigger in prompt for trigger in REALTIME_SEARCH_TRIGGER_WORDS)


def get_blocked_skills_for_query(query: str) -> Set[str]:
    if is_realtime_search_query(query):
        return set(REALTIME_BLOCKED_SKILLS)
    return set()


def prioritize_skills_for_query(query: str, skills: List[str], top_k: int = 3) -> List[str]:
    ordered_skills = [str(skill or "").strip() for skill in (skills or []) if str(skill or "").strip()]
    if not is_realtime_search_query(query):
        return ordered_skills

    blocked = get_blocked_skills_for_query(query)
    filtered = [skill for skill in ordered_skills if skill not in blocked]

    prioritized: List[str] = []
    for forced_skill in REALTIME_FORCED_SKILLS:
        if forced_skill not in prioritized:
            prioritized.append(forced_skill)

    for skill in filtered:
        if skill not in prioritized:
            prioritized.append(skill)

    if "system.websearch" not in prioritized[:top_k]:
        prioritized = ["system.websearch"] + [skill for skill in prioritized if skill != "system.websearch"]

    return prioritized


class SkillNotFoundError(Exception):
    def __init__(self, requested_skill: str):
        super().__init__(f"Skill '{requested_skill}' ist nicht registriert.")
        self.requested_skill = requested_skill


class SkillRouter:
    """Resolves legacy and skill names to concrete tool handlers."""

    def __init__(self):
        self._startup_t0 = time.perf_counter()
        self._legacy_to_skill, self._skill_descriptions = self._load_skill_mapping()
        self._skill_to_legacy = {
            str(skill): str(legacy)
            for legacy, skill in self._legacy_to_skill.items()
            if skill
        }
        self._index_skills_for_discovery()
        startup_ms = int((time.perf_counter() - self._startup_t0) * 1000)
        logger.info("💎 [STARTUP] Skill-Router bereit (%s ms)", startup_ms)

    def _build_skill_description(self, skill_id: str, raw_value: Any) -> str:
        if isinstance(raw_value, dict):
            explicit = str(raw_value.get("description") or "").strip()
            if explicit:
                return explicit

            tags = [str(item).strip() for item in raw_value.get("tags", []) if str(item).strip()]
            capabilities = [
                str(item).strip()
                for item in raw_value.get("capabilities", [])
                if str(item).strip()
            ]
            snippets = [f"Skill {skill_id}"]
            if tags:
                snippets.append(f"Tags: {', '.join(tags)}")
            if capabilities:
                snippets.append(f"Capabilities: {', '.join(capabilities)}")
            return ". ".join(snippets)

        return f"Skill {skill_id}"

    def _normalize_skill_name(self, name: str) -> str:
        """Normalize provider-safe tool names to router skill notation."""
        return str(name or "").strip().replace("_", ".")

    def _index_skills_for_discovery(self) -> None:
        if not self._skill_descriptions:
            return

        try:
            skills_root = Path(__file__).resolve().parents[2] / "backend" / "skills"
            tool_registry_file = Path(__file__).resolve().parents[2] / "backend" / "tool_registry.py"
            cache_file = Path(vector_service.CHROMA_PATH) / "janus_skill_index_cache.json"
            cache_file.parent.mkdir(parents=True, exist_ok=True)

            skill_files = sorted(skills_root.rglob("*.json")) if skills_root.exists() else []
            skills_max_mtime = 0
            for fp in skill_files:
                try:
                    skills_max_mtime = max(skills_max_mtime, fp.stat().st_mtime_ns)
                except Exception:
                    continue
            tool_registry_mtime = int(tool_registry_file.stat().st_mtime_ns) if tool_registry_file.exists() else 0
            signature = {
                "skill_count": len(self._skill_descriptions),
                "skills_max_mtime_ns": int(skills_max_mtime),
                "tool_registry_mtime_ns": int(tool_registry_mtime),
            }

            client = chromadb.PersistentClient(path=vector_service.CHROMA_PATH)
            collection = client.get_or_create_collection(name="janus_skill_index")

            if cache_file.exists():
                try:
                    cached = json.loads(cache_file.read_text(encoding="utf-8"))
                    if (
                        isinstance(cached, dict)
                        and cached.get("signature") == signature
                        and isinstance(cached.get("entries"), list)
                    ):
                        ids: List[str] = []
                        embeddings: List[List[float]] = []
                        metadatas: List[Dict[str, Any]] = []
                        documents: List[str] = []
                        for row in cached["entries"]:
                            if not isinstance(row, dict):
                                continue
                            sid = str(row.get("skill_id") or "").strip()
                            emb = row.get("embedding")
                            doc = str(row.get("description") or "").strip()
                            if not sid or not isinstance(emb, list) or not doc:
                                continue
                            ids.append(sid)
                            embeddings.append(emb)
                            metadatas.append({"skill_id": sid})
                            documents.append(doc)
                        if ids:
                            collection.upsert(
                                ids=ids,
                                embeddings=embeddings,
                                metadatas=metadatas,
                                documents=documents,
                            )
                            logger.info("SKILL-ROUTER: janus_skill_index aus Datei-Cache geladen (%s Skills).", len(ids))
                            return
                except Exception:
                    logger.warning("SKILL-ROUTER: Cache-Load fehlgeschlagen, baue Index neu.", exc_info=True)

            # Non-blocking startup path: if embedding model is still warming, skip
            # synchronous embedding generation entirely and build index in background.
            vector_service.start_background_model_load()
            if vector_service.is_model_loading():
                logger.info("SKILL-ROUTER: Embeddings noch nicht bereit (%s).", vector_service.warmup_status_text())
                self._build_skill_index_async(signature=signature, cache_file=cache_file)
                return

            ids: List[str] = []
            embeddings: List[List[float]] = []
            metadatas: List[Dict[str, Any]] = []
            documents: List[str] = []
            cache_entries: List[Dict[str, Any]] = []

            for skill_id, description in sorted(self._skill_descriptions.items()):
                embedding_json = vector_service.generate_embedding(description, wait_for_model=False)
                if not embedding_json:
                    continue
                try:
                    embedding = json.loads(embedding_json)
                except Exception:
                    continue
                ids.append(skill_id)
                embeddings.append(embedding)
                metadatas.append({"skill_id": skill_id})
                documents.append(description)
                cache_entries.append(
                    {"skill_id": skill_id, "description": description, "embedding": embedding}
                )

            if ids:
                collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents,
                )
                logger.info("SKILL-ROUTER: %s Skills in 'janus_skill_index' indexiert.", len(ids))
                try:
                    cache_file.write_text(
                        json.dumps({"signature": signature, "entries": cache_entries}, ensure_ascii=False),
                        encoding="utf-8",
                    )
                except Exception:
                    logger.warning("SKILL-ROUTER: Konnte Skill-Index-Cache nicht schreiben.", exc_info=True)
            else:
                self._build_skill_index_async(signature=signature, cache_file=cache_file)
        except Exception as exc:
            logger.warning("SKILL-ROUTER: Skill-Index konnte nicht aufgebaut werden: %s", exc)

    def _build_skill_index_async(self, *, signature: Dict[str, Any], cache_file: Path) -> None:
        def _worker() -> None:
            try:
                ids: List[str] = []
                embeddings: List[List[float]] = []
                metadatas: List[Dict[str, Any]] = []
                documents: List[str] = []
                cache_entries: List[Dict[str, Any]] = []
                for skill_id, description in sorted(self._skill_descriptions.items()):
                    embedding_json = vector_service.generate_embedding(description, wait_for_model=True)
                    if not embedding_json:
                        continue
                    try:
                        embedding = json.loads(embedding_json)
                    except Exception:
                        continue
                    ids.append(skill_id)
                    embeddings.append(embedding)
                    metadatas.append({"skill_id": skill_id})
                    documents.append(description)
                    cache_entries.append(
                        {"skill_id": skill_id, "description": description, "embedding": embedding}
                    )
                if not ids:
                    return
                client = chromadb.PersistentClient(path=vector_service.CHROMA_PATH)
                collection = client.get_or_create_collection(name="janus_skill_index")
                collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents,
                )
                cache_file.write_text(
                    json.dumps({"signature": signature, "entries": cache_entries}, ensure_ascii=False),
                    encoding="utf-8",
                )
                logger.info("SKILL-ROUTER: Background-Indexierung abgeschlossen (%s Skills).", len(ids))
            except Exception:
                logger.warning("SKILL-ROUTER: Background-Indexierung fehlgeschlagen.", exc_info=True)

        threading.Thread(target=_worker, name="janus-skill-index-build", daemon=True).start()

    def _extract_skill_id(self, legacy_name: str, raw_value: Any) -> str:
        legacy = str(legacy_name)
        if isinstance(raw_value, str):
            return str(raw_value)
        if isinstance(raw_value, dict):
            return str(
                raw_value.get("skill")
                or raw_value.get("skill_id")
                or raw_value.get("name")
                or legacy
            )
        return str(raw_value)

    def _load_from_catalog_folder(self, skills_root: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
        mapping: Dict[str, str] = {}
        skill_descriptions: Dict[str, str] = {}
        depends_by_skill: Dict[str, List[str]] = {}

        for file_path in sorted(skills_root.rglob("*.json")):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning("SKILL-ROUTER: Katalogdatei '%s' konnte nicht geladen werden: %s", file_path, exc)
                continue

            entries: Dict[str, Any]
            if isinstance(data, dict) and "legacy_name" in data:
                legacy_name = str(data.get("legacy_name") or "").strip()
                entries = {legacy_name: data} if legacy_name else {}
            elif isinstance(data, dict):
                entries = data
            else:
                entries = {}

            for legacy_name, raw_value in entries.items():
                legacy = str(legacy_name)
                skill_id = self._extract_skill_id(legacy, raw_value)
                mapping[legacy] = skill_id
                skill_descriptions[skill_id] = self._build_skill_description(skill_id, raw_value)

                if isinstance(raw_value, dict):
                    depends = [
                        str(dep).strip()
                        for dep in raw_value.get("depends_on", [])
                        if str(dep).strip()
                    ]
                    if depends:
                        depends_by_skill.setdefault(skill_id, []).extend(depends)

        known_skills: Set[str] = set(mapping.values())
        for skill_id, deps in depends_by_skill.items():
            missing = sorted({dep for dep in deps if dep not in known_skills})
            if missing:
                logger.warning(
                    "SKILL-ROUTER: Skill '%s' hat fehlende Abhängigkeiten: %s",
                    skill_id,
                    ", ".join(missing),
                )

        return mapping, skill_descriptions

    def _load_skill_mapping(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        root = Path(__file__).resolve().parents[2]
        skills_root = root / "backend" / "skills"

        mapping: Dict[str, str] = {}
        descriptions: Dict[str, str] = {}
        if skills_root.exists():
            mapping, descriptions = self._load_from_catalog_folder(skills_root)

        if not mapping:
            skill_file = root / "documentation" / "skill_mapping.json"
            if not skill_file.exists():
                logger.warning(
                    "SKILL-ROUTER: Weder Catalog '%s' noch Mapping-Datei '%s' gefunden.",
                    skills_root,
                    skill_file,
                )
                return {}, {}

            try:
                with skill_file.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)

                for legacy_name, raw_value in (data or {}).items():
                    legacy = str(legacy_name)
                    skill_id = self._extract_skill_id(legacy, raw_value)
                    mapping[legacy] = skill_id
                    descriptions[skill_id] = self._build_skill_description(skill_id, raw_value)
            except Exception as exc:
                logger.warning("SKILL-ROUTER: Mapping konnte nicht geladen werden: %s", exc)
                return {}, {}

        logger.info("SKILL-ROUTER: Mapping für [%s] Skills geladen.", len(mapping))
        return mapping, descriptions

    def resolve_tool_name(self, skill_name: str) -> str:
        requested = str(skill_name or "").strip()
        if not requested:
            raise SkillNotFoundError(skill_name)
        normalized = self._normalize_skill_name(requested)

        if tool_manager.get_tool(requested, warn_if_legacy=True):
            return requested
        if normalized != requested and tool_manager.get_tool(normalized, warn_if_legacy=True):
            return normalized

        mapped_skill = self._legacy_to_skill.get(normalized) or self._legacy_to_skill.get(requested)
        if mapped_skill:
            for candidate_name, _tool in tool_manager.get_all_tools().items():
                if tool_manager.get_skill_id(candidate_name) == mapped_skill:
                    return str(candidate_name)

        # Skill-ID direkt auf registrierten Tool-Namen auflösen.
        for candidate_name, _tool in tool_manager.get_all_tools().items():
            if tool_manager.get_skill_id(candidate_name) in {requested, normalized}:
                return str(candidate_name)

        legacy_name = self._skill_to_legacy.get(normalized) or self._skill_to_legacy.get(requested)
        if legacy_name and tool_manager.get_tool(legacy_name):
            return legacy_name

        suffix = f".{normalized}"
        for skill_id in tool_manager.get_skill_mapping().values():
            if skill_id and skill_id.endswith(suffix):
                logger.warning(
                    "[ROUTER] Automatisches Mapping von '%s' auf '%s'.",
                    requested,
                    skill_id,
                )
                return skill_id

        # OpenAI-safe fallback ohne persistente Alias-Registrierung:
        # vergleicht den angefragten Namen gegen Skill-IDs in provider-safe Form.
        for candidate_name, _tool in tool_manager.get_all_tools().items():
            skill_id = str(tool_manager.get_skill_id(candidate_name) or "").strip()
            if skill_id and skill_id.replace(".", "_") == requested:
                return str(candidate_name)

        raise SkillNotFoundError(requested)

    def get_tool_definition(self, skill_name: str) -> ToolDefinition:
        resolved_name = self.resolve_tool_name(skill_name)
        tool_def = tool_manager.get_tool(resolved_name)
        if not tool_def:
            raise SkillNotFoundError(skill_name)
        return tool_def

    def get_skill(self, skill_name: str) -> str:
        """Return normalized mapped skill id for a requested name."""
        requested = str(skill_name or "").strip()
        if not requested:
            raise SkillNotFoundError(skill_name)
        normalized = self._normalize_skill_name(requested)
        resolved = self._legacy_to_skill.get(normalized) or self._legacy_to_skill.get(requested)
        if not resolved:
            raise SkillNotFoundError(skill_name)
        return str(resolved)

    def get_handler(self, skill_name: str) -> Callable:
        return self.get_tool_definition(skill_name).func

    def get_skill_ids(self) -> List[str]:
        return sorted(set(self._legacy_to_skill.values()))


skill_router = SkillRouter()
