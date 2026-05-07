"""Capability Registry — FEAT-HELP-001.

Auto-Discovery Loader for the Janus Help & Capability System.
Validates Registry entries against discovered skills and logs orphans.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger("janus_backend")


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for both script and PyInstaller .exe.
    
    In PyInstaller, sys._MEIPASS contains the temp extraction folder.
    In normal Python, we use the file system relative to this module.
    
    Args:
        relative_path: Path relative to project root (e.g., 'backend/data/capability_registry.json')
    
    Returns:
        Absolute path to the resource.
    """
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    if hasattr(sys, '_MEIPASS'):
        # Running as compiled .exe - resources are in _MEIPASS
        return os.path.join(sys._MEIPASS, relative_path)
    
    # Running as script - resolve relative to this file's location
    # __file__ is in backend/services/, so go up 2 levels to get to project root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_dir, relative_path)


class CapabilityRegistry:
    """Registry for Janus capabilities with Auto-Discovery from skills.
    
    Loads a static registry JSON and validates skill_refs against
    discovered skills in the skills directory. Logs warnings for
    orphaned references.
    
    Attributes:
        registry_path: Path to the static capability_registry.json.
        skills_dir: Directory containing skill JSON files (recursively scanned).
        _registry: Loaded registry data.
        _available_skills: Set of discovered skill IDs from skills_dir.
    """

    # Known categories for UX display; unknowns are folded into "Sonstiges" (TASK-069.10)
    ALLOWED_CATEGORIES = {
        "Kommunikation & Chat",
        "Wissen & Recherche",
        "Aufgaben & Produktivität",
        "Kalender & Termine",
        "Dateien & Dokumente",
        "Bilder & Medien",
        "Analyse & Auswertung",
        "Entwicklung & Automatisierung",
        "Einstellungen & System",
        "Updates & Installation",
        "Sonstiges",
    }

    def __init__(self, registry_path: str, skills_dir: str) -> None:
        """Initialize the registry with paths.
        
        Args:
            registry_path: Path to capability_registry.json.
            skills_dir: Path to skills directory (e.g., backend/skills).
        """
        self.registry_path = Path(registry_path)
        self.skills_dir = Path(skills_dir)
        self._registry: Dict[str, Any] = {}
        self._available_skills: set = set()

    def load(self) -> None:
        """Load registry and discover skills, validating references.
        
        This method:
        1. Loads the static registry JSON.
        2. Recursively scans skills_dir for all skill JSON files.
        3. Extracts skill IDs from the "skill" field.
        4. Validates skill_refs in registry against discovered skills.
        5. Logs CAPABILITY_REGISTRY_ORPHAN for missing references.
        """
        # Load static registry
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                self._registry = json.load(f)
            logger.info("[CAPABILITY-REGISTRY] Loaded registry: %s", self.registry_path)
        except FileNotFoundError:
            logger.error("[CAPABILITY-REGISTRY] Registry file not found: %s", self.registry_path)
            self._registry = {"version": "0.0.0", "categories": {}}
        except json.JSONDecodeError as e:
            logger.error("[CAPABILITY-REGISTRY] Invalid JSON in registry: %s", e)
            self._registry = {"version": "0.0.0", "categories": {}}

        # Discover skills from filesystem
        self._discover_skills()

        # Validate skill_refs
        self._validate_skill_refs()

    def _discover_skills(self) -> None:
        """Recursively scan skills_dir and collect all skill IDs."""
        self._available_skills = set()

        if not self.skills_dir.exists():
            logger.warning("[CAPABILITY-REGISTRY] Skills directory not found: %s", self.skills_dir)
            return

        # Recursively find all JSON files
        for skill_file in self.skills_dir.rglob("*.json"):
            try:
                with open(skill_file, "r", encoding="utf-8") as f:
                    skill_data = json.load(f)

                # Extract skill ID from "skill" field
                skill_id = skill_data.get("skill")
                if skill_id:
                    self._available_skills.add(skill_id)
                    logger.debug("[CAPABILITY-REGISTRY] Discovered skill: %s from %s", skill_id, skill_file)

            except (json.JSONDecodeError, IOError) as e:
                logger.warning("[CAPABILITY-REGISTRY] Failed to parse skill file %s: %s", skill_file, e)

        logger.info("[CAPABILITY-REGISTRY] Discovered %d skills", len(self._available_skills))

    def _validate_skill_refs(self) -> None:
        """Validate skill_refs in registry against discovered skills.
        
        Logs CAPABILITY_REGISTRY_ORPHAN for each skill_ref that doesn't
        exist in the discovered skills set.
        """
        categories = self._registry.get("categories", {})
        orphan_count = 0

        for category_id, category in categories.items():
            abilities = category.get("abilities", [])
            for ability in abilities:
                skill_refs = ability.get("skill_refs", [])
                for ref in skill_refs:
                    if ref not in self._available_skills:
                        logger.warning(
                            "[CAPABILITY-REGISTRY] CAPABILITY_REGISTRY_ORPHAN: "
                            "ability '%s' in category '%s' references unknown skill '%s'",
                            ability.get("id", "unknown"),
                            category_id,
                            ref
                        )
                        orphan_count += 1

        if orphan_count == 0:
            logger.info("[CAPABILITY-REGISTRY] All skill_refs validated — no orphans found.")
        else:
            logger.warning("[CAPABILITY-REGISTRY] Found %d orphaned skill references.", orphan_count)

    def _get_i18n_value(self, field: Any, language: str, default_lang: str = "de") -> str:
        """Extract i18n value from a field that may be a dict or plain string.
        
        Args:
            field: Either a string or a dict {lang: value}.
            language: Preferred language code.
            default_lang: Fallback language code.
        
        Returns:
            The localized string value.
        """
        if isinstance(field, str):
            return field
        if isinstance(field, dict):
            # Try preferred language first
            if language in field:
                return field[language]
            # Fallback to default language
            if default_lang in field:
                return field[default_lang]
            # Return first available
            if field:
                return next(iter(field.values()))
        return ""

    def get_verified_capabilities_for_overview(self, language: str = "de") -> List[Dict]:
        """Get a filtered, mapped, and deduplicated list of verified capabilities for the overview.

        TASK-069.2: Provides a flat list of validated capabilities for UX display.

        Args:
            language: The language for localized strings.

        Returns:
            A list of dictionaries, each representing a verified capability.
            Each dict contains: id, name, description, category, status, confidence.
        """
        verified_capabilities = []
        seen_ids = set()

        if not self._registry or "categories" not in self._registry:
            return []

        for cat_id, cat_data in self._registry["categories"].items():
            category_name = self._get_i18n_value(cat_data.get("display_name"), language, "de")
            if not category_name:
                category_name = "Sonstiges"
            # Normalize unknown categories to "Sonstiges" (TASK-069.10)
            if category_name not in self.ALLOWED_CATEGORIES:
                category_name = "Sonstiges"

            for ability_data in cat_data.get("abilities", []):
                capability_id = ability_data.get("id")
                capability_name = self._get_i18n_value(ability_data.get("label"), language, "de")
                capability_description = self._get_i18n_value(ability_data.get("how_to"), language, "de")
                status = ability_data.get("status")
                confidence = ability_data.get("confidence")

                # Validate required fields (TASK-069.2)
                if not all([capability_id, capability_name, capability_description, status is not None, confidence is not None]):
                    logger.warning(
                        "[CAPABILITY-REGISTRY] Skipping capability '%s' due to missing required fields.",
                        capability_id or "UNKNOWN",
                    )
                    continue

                # Filter by status and confidence (TASK-069.2)
                if status != "verified" or not isinstance(confidence, (int, float)) or confidence < 0.7:
                    logger.debug(
                        "[CAPABILITY-REGISTRY] Skipping capability '%s' due to status '%s' or confidence '%.2f'.",
                        capability_id, status, confidence,
                    )
                    continue

                # Deduplication (TASK-069.2)
                if capability_id in seen_ids:
                    logger.debug(
                        "[CAPABILITY-REGISTRY] Skipping duplicate capability ID '%s'.", capability_id
                    )
                    continue

                seen_ids.add(capability_id)

                verified_capabilities.append({
                    "id": capability_id,
                    "name": capability_name,
                    "description": capability_description,
                    "category": category_name,
                    "status": status,
                    "confidence": confidence,
                })
        return verified_capabilities

    def get_overview(self, language: str = "de") -> Dict[str, Any]:
        """Get capability overview for all categories.
        
        Args:
            language: Preferred language for display names and descriptions.
        
        Returns:
            Dictionary with category summaries including display_name,
            description, icon, and ability count.
        """
        categories = self._registry.get("categories", {})
        overview = {}

        for cat_id, cat_data in categories.items():
            overview[cat_id] = {
                "id": cat_id,
                "display_name": self._get_i18n_value(cat_data.get("display_name"), language),
                "description": self._get_i18n_value(cat_data.get("description"), language),
                "icon": cat_data.get("icon", ""),
                "ability_count": len(cat_data.get("abilities", [])),
                "abilities": [
                    {
                        "id": ability.get("id"),
                        "label": self._get_i18n_value(ability.get("label"), language),
                    }
                    for ability in cat_data.get("abilities", [])
                ]
            }

        return {
            "version": self._registry.get("version", "0.0.0"),
            "language": language,
            "categories": overview
        }

    def get_how_to(self, ability_id: str, language: str = "de") -> Optional[str]:
        """Get how-to instruction for a specific ability.
        
        Args:
            ability_id: The unique ability identifier (e.g., "file.upload").
            language: Preferred language for the instruction.
        
        Returns:
            The how-to instruction text, or None if ability not found.
        """
        categories = self._registry.get("categories", {})

        for category in categories.values():
            for ability in category.get("abilities", []):
                if ability.get("id") == ability_id:
                    how_to = ability.get("how_to", {})
                    return self._get_i18n_value(how_to, language)

        return None

    def get_navigation(self, query: str, language: str = "de") -> Optional[Dict[str, Any]]:
        """Find navigation target based on query keywords.
        
        Performs case-insensitive substring matching against category IDs,
        display names, and UI location keys.
        
        Args:
            query: The user's navigation query.
            language: Preferred language for labels.
        
        Returns:
            Navigation result with action payload, or None if no match.
        """
        query_lower = query.lower()
        categories = self._registry.get("categories", {})

        for cat_id, category in categories.items():
            # Check category ID
            if cat_id.lower() in query_lower:
                return self._build_navigation_result(category, language)

            # Check display name
            display_name = self._get_i18n_value(category.get("display_name"), language).lower()
            if display_name and display_name in query_lower:
                return self._build_navigation_result(category, language)

            # Check UI location keys and labels
            ui_locations = category.get("ui_locations", {})
            for loc_key, loc_data in ui_locations.items():
                if loc_key.lower() in query_lower:
                    return self._build_navigation_result(category, language)
                # Also check the localized label
                loc_label = self._get_i18n_value(loc_data.get("label"), language).lower()
                if loc_label and loc_label in query_lower:
                    return self._build_navigation_result(category, language)

            # Check ability labels
            for ability in category.get("abilities", []):
                label = self._get_i18n_value(ability.get("label"), language).lower()
                ability_id = ability.get("id", "").lower()
                if label in query_lower or ability_id.replace(".", " ") in query_lower:
                    return self._build_navigation_result(category, language)

        return None

    def _build_navigation_result(self, category: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Build navigation result from a category."""
        ui_locations = category.get("ui_locations", {})

        # Return first available UI location with action
        for loc_key, loc_data in ui_locations.items():
            action = loc_data.get("action", {})
            if action:
                return {
                    "category": category.get("display_name", {}).get(language, ""),
                    "location_key": loc_key,
                    "label": self._get_i18n_value(loc_data.get("label"), language),
                    "action": action
                }

        # Fallback: return category without specific action
        return {
            "category": self._get_i18n_value(category.get("display_name"), language),
            "location_key": None,
            "label": None,
            "action": None
        }

    def all_categories(self) -> List[str]:
        """Return list of all category IDs."""
        return list(self._registry.get("categories", {}).keys())

    def get_capability_groups(
        self,
        allowed_skill_ids: Optional[List[str]] = None,
    ) -> Dict[str, List[str]]:
        """Return planner-facing capability groups from the static registry only."""
        allowed = {
            str(skill_id).strip()
            for skill_id in (allowed_skill_ids or [])
            if str(skill_id).strip()
        }
        groups: Dict[str, List[str]] = {}
        categories = self._registry.get("categories", {})
        for category_id, category in categories.items():
            skill_refs: List[str] = []
            for ability in category.get("abilities", []):
                for skill_id in ability.get("skill_refs", []):
                    sid = str(skill_id or "").strip()
                    if not sid:
                        continue
                    if sid not in self._available_skills:
                        continue
                    if allowed and sid not in allowed:
                        continue
                    if sid not in skill_refs:
                        skill_refs.append(sid)
            if skill_refs:
                groups[str(category_id)] = skill_refs
        return groups

    def get_intent_skill_policy(self, intent_result: Any) -> Dict[str, List[str]]:
        """Return {mandatory, boosted, forbidden} skill lists derived from IntentDetectionResult.

        Mandatory skills are inserted at the front of the selector output regardless of vector
        scores. Forbidden skills are removed from the candidate list. Boosted skills are
        promoted over semantic hits but not guaranteed.
        """
        mandatory: List[str] = []
        boosted: List[str] = []
        forbidden: List[str] = []

        def _flag(name: str) -> bool:
            return bool(getattr(intent_result, name, False))

        primary = str(getattr(intent_result, "primary_intent", "") or "")

        # Diamond: PDF nur noch bei explizitem Wunsch, Bild+PDF-Pipeline oder komplexem Dokument-Metaflow.
        pdf_allowed = (
            _flag("is_multitask_image_pdf")
            or _flag("is_complex_document_request")
            or _flag("is_explicit_pdf_intent")
        )
        if not pdf_allowed:
            forbidden += ["system.create_pdf"]

        if _flag("is_routing_geo_intent") or primary == "routing_geo":
            boosted += ["system.routing"]

        if _flag("is_weather_intent") or primary == "weather":
            # Mandatory: SkillSelector universe comes from registry skill_refs; weather must stay
            # available even when boosted-only skills would otherwise be dropped from the tool list.
            mandatory += ["system.weather"]

        if _flag("is_calendar_intent") or primary == "calendar":
            mandatory += ["calendar.list_events", "calendar.find_slots", "calendar.find_and_update_event"]
            forbidden += ["system.create_pdf", "knowledge.edit_pdf", "system.generate_image"]

        if _flag("is_shopping_intent") or primary == "shopping":
            mandatory += ["system.price_comparison"]
            forbidden += ["system.websearch"]

        if _flag("is_local_business_intent") or primary == "local_business":
            mandatory += ["system.local_business"]

        if _flag("is_video_understanding_intent") or primary == "video_understanding":
            mandatory += ["video.understand", "system.video_understanding"]

        if _flag("is_video_list_intent") or primary == "video_list":
            mandatory += ["video.search", "system.video_search"]
        elif _flag("is_video_intent") or primary == "video":
            mandatory += ["video.search", "system.video_search"]
            boosted += ["system.websearch"]

        # 💎 TASK-005: BACKLOG-005 - Filesystem-Intent hat Vorrang vor Bild-Intent
        # Wenn Filesystem-Intent erkannt wurde, hat er Vorrang vor Bild-Intent
        is_filesystem = _flag("is_filesystem_intent") or primary == "filesystem"
        is_image = _flag("is_image_intent") or primary == "image"
        if is_filesystem and is_image:
            # Filesystem-Intent hat Vorrang, Bild-Intent wird ignoriert
            is_image = False

        # 💎 TASK-005: BACKLOG-005 - Filesystem-Intent fügt Filesystem-Tools hinzu
        # Wenn Filesystem-Intent erkannt wurde, füge Filesystem-Tools als mandatory hinzu
        if is_filesystem:
            # Filesystem-Tools als mandatory hinzufügen
            boosted += [
                "filesystem.create_directory",
                "filesystem.create_file",
                "filesystem.delete_directory",
                "filesystem.delete_file",
                "filesystem.find_files",
                "filesystem.list_directory",
                "filesystem.list_workspaces",
                "filesystem.move_file",
                "filesystem.move_files",
                "filesystem.read_file",
                "filesystem.rename_file",
            ]

        if is_image and not _flag("is_multitask_image_pdf"):
            mandatory += ["system.generate_image"]

        if _flag("is_multitask_image_pdf"):
            mandatory += ["system.generate_image", "system.create_pdf"]

        if _flag("is_personal_recall") or _flag("is_self_referential"):
            mandatory += ["system.memory_read", "memory.read"]
            forbidden += ["system.websearch", "system.rss_news"]

        # Canonicalise: keep first occurrence, drop dupes, filter against available skills.
        def _unique(lst: List[str]) -> List[str]:
            seen: set = set()
            result = []
            for s in lst:
                sid = str(s or "").strip()
                if sid and sid not in seen:
                    seen.add(sid)
                    result.append(sid)
            return result

        return {
            "mandatory": _unique(mandatory),
            "boosted": _unique(boosted),
            "forbidden": _unique(forbidden),
        }

    def get_planner_scope(
        self,
        intent_result: Any,
        allowed_skill_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Build a registry-only skill scope for the Agent Planner."""
        groups = self.get_capability_groups(allowed_skill_ids=allowed_skill_ids)
        allowed = sorted({
            skill
            for skills in groups.values()
            for skill in skills
            if str(skill or "").strip()
        })
        primary_intent = str(getattr(intent_result, "primary_intent", "") or "").strip()
        return {
            "primary_intent": primary_intent,
            "capability_groups": groups,
            "allowed_skill_ids": allowed,
        }

    def get_provider_details(self, provider_id: str, language: str = "de") -> Optional[Dict[str, Any]]:
        """Get provider details by ID.

        Args:
            provider_id: The provider identifier (e.g., "openai", "gemini", "anthropic", "ollama").
            language: Preferred language for localized fields.

        Returns:
            Provider data with display name, strengths, and weaknesses, or None if not found.
        """
        provider_details = self._registry.get("provider_details", {})
        if provider_id not in provider_details:
            return None

        provider = provider_details[provider_id]
        return {
            "id": provider_id,
            "display_name": self._get_i18n_value(provider.get("display_name"), language),
            "strengths": self._get_i18n_value(provider.get("strengths"), language),
            "weaknesses": self._get_i18n_value(provider.get("weaknesses"), language)
        }

    def get_model_tier_details(self, tier_id: str, language: str = "de") -> Optional[Dict[str, Any]]:
        """Get model tier details by ID.

        Args:
            tier_id: The tier identifier (e.g., "nano", "mini", "logic", "pro", "gemini-3-pro").
            language: Preferred language for localized fields.

        Returns:
            Tier data with use_cases and cost_label, or None if not found.
        """
        model_tiers = self._registry.get("model_tiers", {})
        if tier_id not in model_tiers:
            return None

        tier = model_tiers[tier_id]
        return {
            "id": tier_id,
            "use_cases": self._get_i18n_value(tier.get("use_cases"), language),
            "cost_label": self._get_i18n_value(tier.get("cost_label"), language)
        }

    def get_model_profile(self, model_name: str, language: str = "de") -> Optional[Dict[str, Any]]:
        """Get model profile by model name with intelligent mapping.

        Args:
            model_name: The model name (e.g., "gpt-5.4-mini", "gemini-3-flash-preview").
            language: Preferred language for localized fields.

        Returns:
            Profile data with level, ux_category, short_description, strengths, ideal_for,
            weaknesses, cost_profile, or None if not found.
        """
        model_profiles = self._registry.get("model_profiles", {})
        model_lower = model_name.lower()

        # Direct mapping
        if model_name in model_profiles:
            profile = model_profiles[model_name]
            return {
                "id": model_name,
                "level": profile.get("level", 1),
                "ux_category": profile.get("ux_category", "Balance"),
                "short_description": self._get_i18n_value(profile.get("short_description"), language),
                "strengths": self._get_i18n_value(profile.get("strengths"), language),
                "ideal_for": self._get_i18n_value(profile.get("ideal_for"), language),
                "weaknesses": self._get_i18n_value(profile.get("weaknesses"), language),
                "cost_profile": self._get_i18n_value(profile.get("cost_profile"), language)
            }

        # Intelligent mapping for GPT-5.4 variants
        if "gpt-5.4" in model_lower:
            if "nano" in model_lower:
                profile_key = "gpt-5.4-nano"
            elif "mini" in model_lower:
                profile_key = "gpt-5.4-mini"
            elif "logic" in model_lower or "standard" in model_lower:
                profile_key = "gpt-5.4-standard"
            elif "pro" in model_lower:
                profile_key = "gpt-5.4-pro"
            else:
                # Default to standard for unknown gpt-5.4 variants
                profile_key = "gpt-5.4-standard"

            if profile_key in model_profiles:
                profile = model_profiles[profile_key]
                return {
                    "id": profile_key,
                    "level": profile.get("level", 1),
                    "ux_category": profile.get("ux_category", "Balance"),
                    "short_description": self._get_i18n_value(profile.get("short_description"), language),
                    "strengths": self._get_i18n_value(profile.get("strengths"), language),
                    "ideal_for": self._get_i18n_value(profile.get("ideal_for"), language),
                    "weaknesses": self._get_i18n_value(profile.get("weaknesses"), language),
                    "cost_profile": self._get_i18n_value(profile.get("cost_profile"), language)
                }

        # Intelligent mapping for Gemini variants
        if "gemini" in model_lower:
            if "flash" in model_lower:
                profile_key = "gemini-3-flash-preview"
            elif "pro" in model_lower:
                profile_key = "gemini-3-pro"
            else:
                # Default to pro for unknown gemini variants
                profile_key = "gemini-3-pro"

            if profile_key in model_profiles:
                profile = model_profiles[profile_key]
                return {
                    "id": profile_key,
                    "level": profile.get("level", 1),
                    "ux_category": profile.get("ux_category", "Balance"),
                    "short_description": self._get_i18n_value(profile.get("short_description"), language),
                    "strengths": self._get_i18n_value(profile.get("strengths"), language),
                    "ideal_for": self._get_i18n_value(profile.get("ideal_for"), language),
                    "weaknesses": self._get_i18n_value(profile.get("weaknesses"), language),
                    "cost_profile": self._get_i18n_value(profile.get("cost_profile"), language)
                }

        return None

    def get_category(self, category_id: str, language: str = "de") -> Optional[Dict[str, Any]]:
        """Get full category data by ID.
        
        Args:
            category_id: The category identifier.
            language: Preferred language for localized fields.
        
        Returns:
            Full category data with localized strings, or None.
        """
        categories = self._registry.get("categories", {})
        if category_id not in categories:
            return None

        cat = categories[category_id]
        return {
            "id": category_id,
            "display_name": self._get_i18n_value(cat.get("display_name"), language),
            "description": self._get_i18n_value(cat.get("description"), language),
            "icon": cat.get("icon"),
            "abilities": [
                {
                    "id": ability.get("id"),
                    "label": self._get_i18n_value(ability.get("label"), language),
                    "how_to": self._get_i18n_value(ability.get("how_to"), language),
                    "skill_refs": ability.get("skill_refs", [])
                }
                for ability in cat.get("abilities", [])
            ],
            "ui_locations": cat.get("ui_locations", {})
        }
