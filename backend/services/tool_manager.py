# backend/services/tool_manager.py
import inspect
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from backend.data.schemas import SkillMetadata
from pydantic import BaseModel

logger = logging.getLogger("janus_backend")


class ToolDefinition:
    """Repräsentiert ein einzelnes Werkzeug und dessen Metadaten für das LLM."""

    def __init__(
        self,
        func: Callable,
        args_schema: Optional[BaseModel] = None,
        description: Optional[str] = None,
        skill_metadata: Optional[SkillMetadata] = None,
        name: Optional[str] = None,  # NEU: Expliziter Skill-Name
    ):
        self.func = func
        self.args_schema = args_schema
        self.name = name if name else func.__name__  # NEU: Name-Override
        self.skill_metadata = skill_metadata
        base_description = description or inspect.getdoc(func) or ""
        self.description = self._enrich_description(base_description)
        self.llm_definition = self._build_llm_definition()

    def _enrich_description(self, base_description: str) -> str:
        if not self.skill_metadata:
            return base_description

        md = self.skill_metadata
        metadata_lines = [
            f"Latency: {md.latency_class}",
            f"Tags: {', '.join(md.tags) if md.tags else '-'}",
            f"Capabilities: {', '.join(md.capabilities) if md.capabilities else '-'}",
            f"Agent-ready: {'yes' if md.is_agent_ready else 'no'}",
            f"Max calls per turn: {md.max_calls_per_turn}",
        ]
        if md.examples:
            metadata_lines.append(f"Example: {json.dumps(md.examples[0], ensure_ascii=False)}")

        block = "\n".join(metadata_lines)
        return f"{base_description}\n\n[Skill Metadata]\n{block}".strip()

    def _build_llm_definition(self):
        """Erstellt eine absolut saubere JSON-Definition, die für alle LLMs sicher ist."""
        schema = {"type": "object", "properties": {}}
        if self.args_schema:
            try:
                if hasattr(self.args_schema, "model_json_schema") and callable(self.args_schema.model_json_schema):
                    schema = self.args_schema.model_json_schema()
                elif hasattr(self.args_schema, "schema") and callable(self.args_schema.schema):
                    schema = self.args_schema.schema()
                elif isinstance(self.args_schema, dict):
                    schema = self.args_schema
            except Exception as e:
                logger.error(f"Kritischer Schema-Fehler für Tool '{self.name}': {e}")
        
        return {
            "name": str(self.name),
            "description": str(self.description),
            "parameters": schema,
        }


class ToolManager:
    """Singleton-Service zur Verwaltung aller verfügbaren Tools."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolManager, cls).__new__(cls)
            cls._instance.tools: Dict[str, ToolDefinition] = {}
            (
                cls._instance._skill_mapping,
                cls._instance._skill_capabilities,
                cls._instance._skill_metadata_overrides,
            ) = cls._instance._load_skill_catalog()
            cls._instance._skill_metadata = cls._instance._build_skill_metadata()
            cls._instance._apply_metadata_overrides()
            cls._instance._output_schemas: Dict[str, Any] = {}
            cls._instance._tool_definitions_cache: Dict[Tuple[bool, frozenset], List[Dict[str, Any]]] = {}
            mapping_count = len(cls._instance._skill_mapping)
            logger.info(f"SKILL-SYSTEM: Mapping für [{mapping_count}] Tools geladen.")
            logger.info("ToolManager initialized.")
        return cls._instance

    def _apply_metadata_overrides(self) -> None:
        for skill_id, override in self._skill_metadata_overrides.items():
            base = self._skill_metadata.get(skill_id, SkillMetadata())
            merged = base.model_dump()
            for field in override.model_fields_set:
                merged[field] = getattr(override, field)
            # Preserve fields that are explicitly set in base but not in override
            # This handles cases like optimal_model_tier where override has None
            for field, value in base.model_dump().items():
                if field not in override.model_fields_set and value is not None:
                    merged[field] = value
            if self._skill_capabilities.get(skill_id):
                merged["capabilities"] = self._skill_capabilities.get(skill_id, [])
            self._skill_metadata[skill_id] = SkillMetadata(**merged)

        for skill_id, capabilities in self._skill_capabilities.items():
            metadata = self._skill_metadata.get(skill_id)
            if metadata:
                payload = metadata.model_dump()
                payload["capabilities"] = capabilities
                # Preserve all existing fields, only update capabilities
                self._skill_metadata[skill_id] = SkillMetadata(**payload)

    def _build_skill_metadata(self) -> Dict[str, SkillMetadata]:
        return {
            "knowledge.query": SkillMetadata(
                latency_class="normal",
                tags=["knowledge", "rag", "search"],
                capabilities=["document_analysis", "semantic_search", "fact_lookup"],
                examples=[
                    {
                        "input": {"query_text": "Kairo", "n_results": 5},
                        "output": {"status": "ok", "data": {"hit_count": 1}},
                    }
                ],
            ),
            "knowledge.edit_pdf": SkillMetadata(
                latency_class="slow",
                tags=["knowledge", "pdf", "edit"],
                capabilities=["document_edit", "correction_batch"],
                examples=[
                    {
                        "input": {
                            "original_filename": "audit.pdf",
                            "modifications": [{"search": "foo", "replace": "bar"}],
                        },
                        "output": {"status": "ok", "data": {"quality_gate": "passed"}},
                    }
                ],
            ),
            "filesystem.list_directory": SkillMetadata(
                latency_class="fast",
                tags=["filesystem", "list", "workspace"],
                capabilities=["file_read", "workspace_discovery"],
                examples=[
                    {
                        "input": {"path": ".", "pattern": "*.pdf"},
                        "output": {"status": "ok", "data": {"output": "..."}},
                    }
                ],
            ),
            "filesystem.list": SkillMetadata(
                latency_class="fast",
                tags=["filesystem", "list", "workspace"],
                capabilities=["file_read", "workspace_discovery"],
                examples=[
                    {
                        "input": {"path": "."},
                        "output": {"status": "ok", "data": {"output": "..."}},
                    }
                ],
            ),
        }

    def _extract_mapping_entry(
        self,
        legacy_name: str,
        raw_value: Any,
    ) -> Tuple[str, List[str], Optional[SkillMetadata]]:
        if isinstance(raw_value, str):
            return str(raw_value), [], None

        if isinstance(raw_value, dict):
            skill_id = str(
                raw_value.get("skill")
                or raw_value.get("skill_id")
                or raw_value.get("name")
                or legacy_name
            ).strip()

            capabilities = [
                str(item).strip()
                for item in raw_value.get("capabilities", [])
                if str(item).strip()
            ]

            metadata = None
            metadata_fields = {
                key: raw_value[key]
                for key in [
                    "examples",
                    "latency_class",
                    "tags",
                    "capabilities",
                    "version",
                    "sandbox_level",
                    "depends_on",
                    "is_agent_ready",
                    "max_calls_per_turn",
                    "optimal_model_tier",
                    "timeout_ms",
                    "synthesis_directives",
                ]
                if key in raw_value
            }
            if "output_schema" in raw_value and isinstance(raw_value["output_schema"], dict):
                metadata_fields["output_schema_hint"] = raw_value["output_schema"]
            if metadata_fields:
                metadata_fields.setdefault("capabilities", capabilities)
                try:
                    metadata = SkillMetadata(**metadata_fields)
                except Exception as exc:
                    logger.warning(
                        "SKILL-SYSTEM: Ungültige Metadaten für Mapping '%s': %s",
                        legacy_name,
                        exc,
                    )

            return skill_id, capabilities, metadata

        return str(raw_value), [], None

    def _load_skill_catalog_from_file(
        self,
        file_path: Path,
    ) -> Tuple[Dict[str, str], Dict[str, List[str]], Dict[str, SkillMetadata]]:
        try:
            with file_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)

            if isinstance(data, dict) and "legacy_name" in data:
                legacy_name = str(data.get("legacy_name") or "").strip()
                skill_key = str(data.get("skill") or "").strip()
                if legacy_name:
                    data = {legacy_name: data, skill_key: data} if skill_key else {legacy_name: data}
                else:
                    data = {}
            elif isinstance(data, dict) and "skill" in data and "version" in data:
                # Single-skill descriptor format (e.g. backend/skills/system/websearch.json)
                # Wrap under the skill_id so _extract_mapping_entry can read all fields.
                skill_key = str(data.get("skill") or "").strip()
                if skill_key:
                    data = {skill_key: data}
                else:
                    data = {}

            mapping: Dict[str, str] = {}
            capabilities: Dict[str, Set[str]] = {}
            metadata_overrides: Dict[str, SkillMetadata] = {}

            for legacy_name, raw_value in (data or {}).items():
                legacy = str(legacy_name)
                skill_id, caps, metadata = self._extract_mapping_entry(legacy, raw_value)
                mapping[legacy] = skill_id
                if caps:
                    capabilities.setdefault(skill_id, set()).update(caps)
                if metadata is not None:
                    metadata_overrides[skill_id] = metadata

            capabilities_clean = {
                skill_id: sorted(values)
                for skill_id, values in capabilities.items()
            }
            return mapping, capabilities_clean, metadata_overrides
        except Exception as exc:
            logger.warning(
                "SKILL-SYSTEM: Fehler beim Laden der Skill-Datei '%s': %s",
                file_path,
                exc,
            )
            return {}, {}, {}

    def _load_skill_catalog(self) -> Tuple[Dict[str, str], Dict[str, List[str]], Dict[str, SkillMetadata]]:
        root = Path(__file__).resolve().parents[2]
        skills_root = root / "backend" / "skills"

        mapping: Dict[str, str] = {}
        capabilities: Dict[str, Set[str]] = {}
        metadata_overrides: Dict[str, SkillMetadata] = {}

        if skills_root.exists():
            skill_files = sorted(skills_root.rglob("*.json"))
            for skill_file in skill_files:
                file_mapping, file_caps, file_meta = self._load_skill_catalog_from_file(skill_file)
                mapping.update(file_mapping)
                for skill_id, caps in file_caps.items():
                    capabilities.setdefault(skill_id, set()).update(caps)
                metadata_overrides.update(file_meta)

        if not mapping:
            legacy_mapping_file = root / "documentation" / "skill_mapping.json"
            if legacy_mapping_file.exists():
                file_mapping, file_caps, file_meta = self._load_skill_catalog_from_file(legacy_mapping_file)
                mapping.update(file_mapping)
                for skill_id, caps in file_caps.items():
                    capabilities.setdefault(skill_id, set()).update(caps)
                metadata_overrides.update(file_meta)
            else:
                logger.warning(
                    "SKILL-SYSTEM: Weder Catalog-Ordner '%s' noch Mapping-Datei '%s' gefunden.",
                    skills_root,
                    legacy_mapping_file,
                )

        capabilities_clean = {
            skill_id: sorted(values)
            for skill_id, values in capabilities.items()
        }
        return mapping, capabilities_clean, metadata_overrides

    def register_tool(
        self,
        func: Callable,
        args_schema: Optional[BaseModel] = None,
        description: Optional[str] = None,
        name: Optional[str] = None,  # NEU: Expliziter Name für Skill-ID
    ):
        """Registriert ein neues Tool."""
        tool_name = name if name else str(func.__name__)  # NEU: Name-Override priorisieren
        skill_name = self.get_skill_id(tool_name)
        skill_metadata = self.get_skill_metadata(skill_name)
        tool = ToolDefinition(func, args_schema, description, skill_metadata=skill_metadata, name=tool_name)
        skill_id = self.get_skill_id(tool_name)
        self.tools[skill_id] = tool  # Registrierung unter Skill-ID (z.B. knowledge.query)
        for alias in self._tool_name_aliases(tool_name, skill_id):
            self.tools[alias] = tool
        self._tool_definitions_cache.clear()
        if tool.name not in self._skill_mapping:
            logger.warning("SKILL-SYSTEM: Kein Mapping für Tool '%s'.", tool.name)

    @staticmethod
    def _dot_underscore_variants(name: str) -> List[str]:
        raw = str(name or "").strip()
        candidates = [raw]
        if raw:
            candidates.append(raw.replace(".", "_"))
            candidates.append(raw.replace("_", "."))
        seen = set()
        return [item for item in candidates if item and not (item in seen or seen.add(item))]

    def _legacy_suffix_candidates(self, name: str) -> List[str]:
        raw = str(name or "").strip()
        candidates: List[str] = []
        for delimiter in (".", "_"):
            if delimiter in raw:
                suffix = raw.split(delimiter, 1)[1]
                candidates.extend(self._dot_underscore_variants(suffix))
        seen = set()
        return [item for item in candidates if item and not (item in seen or seen.add(item))]

    def _tool_name_aliases(self, tool_name: str, skill_id: str) -> List[str]:
        aliases: List[str] = []
        for name in (tool_name, skill_id):
            aliases.extend(self._dot_underscore_variants(name))
        seen = set()
        return [item for item in aliases if item and not (item in seen or seen.add(item))]

    def get_skill_id(self, name: str) -> str:
        candidate = str(name or "").strip()
        for variant in self._dot_underscore_variants(candidate):
            if variant in self._skill_mapping:
                return self._skill_mapping[variant]
        for suffix in self._legacy_suffix_candidates(candidate):
            if suffix in self._skill_mapping:
                mapped = self._skill_mapping[suffix]
                if mapped != candidate:
                    logger.info("SKILL-ALIAS: Gemischter Toolname '%s' auf Skill '%s' aufgeloest.", candidate, mapped)
                return mapped
        safe_candidate = candidate.replace(".", "_")
        known_skill_ids = set(self._skill_mapping.values()) | set(self._skill_metadata.keys())
        for skill_id in known_skill_ids:
            skill_id_str = str(skill_id or "").strip()
            if skill_id_str and skill_id_str.replace(".", "_") == safe_candidate:
                return skill_id_str
        return candidate

    def get_skill_metadata(self, name: str) -> SkillMetadata:
        skill_id = self.get_skill_id(name)
        metadata = self._skill_metadata.get(skill_id)
        if metadata:
            return metadata
        capabilities = self._skill_capabilities.get(skill_id, [])
        return SkillMetadata(capabilities=capabilities)

    def get_max_calls_per_turn(self, name: str) -> int:
        metadata = self.get_skill_metadata(name)
        return int(metadata.max_calls_per_turn)

    def get_sandbox_level(self, name: str) -> str:
        metadata = self.get_skill_metadata(name)
        return str(metadata.sandbox_level)

    def get_capability_groups(self) -> Dict[str, List[str]]:
        groups: Dict[str, Set[str]] = {}
        for skill_id in set(self._skill_mapping.values()) | set(self._skill_metadata.keys()):
            metadata = self.get_skill_metadata(skill_id)
            for capability in metadata.capabilities:
                key = str(capability).strip()
                if not key:
                    continue
                groups.setdefault(key, set()).add(skill_id)
        return {cap: sorted(skills) for cap, skills in groups.items()}

    def get_skill_mapping(self) -> Dict[str, str]:
        """Liefert das geladene Legacy->Skill Mapping als Metadaten."""
        return dict(self._skill_mapping)

    def is_legacy_name(self, name: str) -> bool:
        """Prüft, ob ein Name ein Legacy-Toolname mit Skill-Nachfolger ist."""
        legacy_name = str(name or "")
        return legacy_name in self._skill_mapping and bool(self._skill_mapping.get(legacy_name))

    def get_skill_name_for_legacy(self, legacy_name: str) -> Optional[str]:
        """Liefert den kanonischen Skillnamen zu einem Legacy-Toolnamen."""
        return self._skill_mapping.get(str(legacy_name or ""))

    def get_tool(self, name: str, warn_if_legacy: bool = False) -> Optional[ToolDefinition]:
        """Holt ein Tool anhand des Namens und löst Legacy-Aliase transparent auf."""
        tool_name = str(name or "").strip()

        lookup_names: List[str] = []
        lookup_names.extend(self._dot_underscore_variants(tool_name))
        resolved_skill_id = self.get_skill_id(tool_name)
        lookup_names.extend(self._dot_underscore_variants(resolved_skill_id))
        lookup_names.extend(self._legacy_suffix_candidates(tool_name))

        seen = set()
        lookup_names = [item for item in lookup_names if item and not (item in seen or seen.add(item))]

        for lookup_name in lookup_names:
            if self.is_legacy_name(lookup_name):
                actual_skill_id = self.get_skill_name_for_legacy(lookup_name)
                tool = self.tools.get(actual_skill_id) or self.tools.get(str(actual_skill_id or "").replace(".", "_"))
                if tool:
                    if warn_if_legacy:
                        logger.info(
                            "SKILL-ALIAS: Toolname '%s' wurde ueber Legacy-Alias '%s' auf '%s' aufgeloest.",
                            tool_name,
                            lookup_name,
                            actual_skill_id,
                        )
                    return tool

            tool = self.tools.get(lookup_name)
            if tool:
                return tool

        return None

    def get_timeout_seconds(self, name: str) -> Optional[float]:
        """Liefert den Timeout in Sekunden aus den Skill-Metadaten. None = kein Timeout."""
        metadata = self.get_skill_metadata(name)
        timeout_ms = getattr(metadata, "timeout_ms", None)
        if isinstance(timeout_ms, (int, float)) and timeout_ms > 0:
            return float(timeout_ms) / 1000.0
        return None

    def set_output_schema(self, skill_id: str, schema_class: Any) -> None:
        """Registriert ein Pydantic-OutputModel zur zentralen Executor-Validierung."""
        self._output_schemas[str(skill_id)] = schema_class
        logger.debug("SKILL-SYSTEM: Output-Schema '%s' registriert für '%s'.", schema_class.__name__, skill_id)

    def get_output_schema(self, skill_id: str) -> Optional[Any]:
        """Liefert das registrierte OutputModel oder None."""
        return self._output_schemas.get(str(skill_id))

    def get_synthesis_directives(self, skill_id: str) -> Optional[str]:
        """Liefert die synthesis_directives eines Skills oder None."""
        metadata = self.get_skill_metadata(skill_id)
        return getattr(metadata, "synthesis_directives", None)

    def get_output_schema_hint(self, skill_id: str) -> Optional[Dict]:
        """Liefert den output_schema_hint (JSON-Dict) eines Skills oder None."""
        metadata = self.get_skill_metadata(skill_id)
        return getattr(metadata, "output_schema_hint", None)

    def get_deterministic_renderer(self, skill_id: str) -> bool:
        """Liefert den deterministic_renderer Flag eines Skills (default: False)."""
        metadata = self.get_skill_metadata(skill_id)
        return bool(getattr(metadata, "deterministic_renderer", False))

    def get_optimal_model_tier(self, skill_id: str, provider: str) -> str:
        """
        Liefert den optimalen MoA-Tier für einen Skill und Provider.
        - Wenn optimal_model_tier ein Dict ist: provider-spezifischer Wert, sonst Fallback "logic"
        - Wenn optimal_model_tier ein String ist (legacy): wird dieser Wert für alle Provider verwendet
        - Wenn None: Fallback "logic"
        """
        metadata = self.get_skill_metadata(skill_id)
        tier_config = getattr(metadata, "optimal_model_tier", "logic")  # Fallback auf logic
        
        if isinstance(tier_config, dict):
            return tier_config.get(provider, "logic")  # Provider-spezifisch mit Fallback
        return tier_config  # Legacy String-Fall

    def get_all_tools(self) -> Dict[str, ToolDefinition]:
        """Gibt alle registrierten Tool-Objekte zurück."""
        return self.tools

    def _candidate_names_for_tool(self, tool: ToolDefinition) -> Set[str]:
        """Alle Namen (kanonischer Skill-ID, Registrierungsname, Legacy-Aliase), unter denen dieses Tool erreichbar ist."""
        canon = self.get_skill_id(tool.name)
        candidates: Set[str] = {canon, str(tool.name or "").strip()}
        candidates.discard("")
        for legacy, sid in self._skill_mapping.items():
            if sid == canon:
                candidates.add(str(legacy).strip())
        candidates.discard("")
        return candidates

    @staticmethod
    def _tool_definitions_cache_key(allowed_skill_ids: Optional[List[str]]) -> Tuple[bool, frozenset]:
        """
        Cache-Key: frozenset der normalisierten IDs; erstes Tuple-Element markiert,
        ob eine explizite (truthy) Einschränkungsliste übergeben wurde (vermeidet Kollision mit leeren Einträgen).
        """
        if not allowed_skill_ids:
            return (False, frozenset())
        return (
            True,
            frozenset(str(s).strip() for s in allowed_skill_ids if str(s).strip()),
        )

    def get_tool_definitions(self, allowed_skill_ids: List[str] = None) -> List[Dict[str, Any]]:
        key = self._tool_definitions_cache_key(allowed_skill_ids)
        cached = self._tool_definitions_cache.get(key)
        if cached is not None:
            return list(cached)

        definitions: List[Dict[str, Any]] = []
        unique_tools = {id(tool): tool for tool in self.tools.values()}
        allowed_set: Optional[Set[str]] = (
            {str(s).strip() for s in allowed_skill_ids if str(s).strip()} if allowed_skill_ids else None
        )

        for tool in unique_tools.values():
            if allowed_set is not None:
                if self._candidate_names_for_tool(tool).isdisjoint(allowed_set):
                    continue

            canonical_name = self.get_skill_id(tool.name)
            # Guard: Sanitize tool name and description for Gemini compatibility
            # Gemini requires alphanumeric (a-z, A-Z, 0-9) or underscores (_) in tool names
            safe_name = canonical_name if canonical_name and isinstance(canonical_name, str) else "unknown_tool"
            # Replace dots with underscores to ensure alphanumeric compliance
            safe_name = safe_name.replace(".", "_").replace("-", "_")
            if not safe_name or not safe_name.replace("_", "").isalnum():
                safe_name = f"tool_{len(definitions)}"
            
            safe_description = tool.description if tool.description and isinstance(tool.description, str) else "No description available"

            if canonical_name != safe_name:
                logger.warning(f"[D21-TOOL-DEF-GUARD] Tool name '{canonical_name}' sanitized to '{safe_name}' for Gemini compatibility")

            definitions.append({
                "type": "function",
                "function": {
                    "name": safe_name,
                    "description": safe_description,
                    "parameters": tool.llm_definition["parameters"],
                },
            })
        self._tool_definitions_cache[key] = definitions
        return list(definitions)


# Global Singleton Instance
tool_manager = ToolManager()
