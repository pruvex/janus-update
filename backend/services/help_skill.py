"""Help Skill Handler — FEAT-HELP-001.

Deterministic help response generator using CapabilityRegistry.
NO LLM calls — pure template rendering from Registry data.

Invariant: This module NEVER imports or calls the LLM Gateway.
"""

import logging
from typing import Optional, List

from backend.services.capability_registry import CapabilityRegistry
from backend.services.orchestrator.help_schemas import HelpInput, HelpOutput, HelpAction

logger = logging.getLogger("janus_backend")


class HelpSkill:
    """Help skill handler for answering user help queries.
    
    This handler operates entirely deterministically using the CapabilityRegistry.
    No LLM calls are made — responses are built from templates and registry data.
    
    Attributes:
        registry: CapabilityRegistry instance for data lookup.
    """

    # Fallback message when no information is available
    FALLBACK_MESSAGE = "Dazu habe ich keine Information."

    # Deterministic category display order for capability overview (TASK-069.4)
    CATEGORY_ORDER = [
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
    ]

    def __init__(self, registry: CapabilityRegistry) -> None:
        """Initialize HelpSkill with a CapabilityRegistry.
        
        Args:
            registry: The capability registry to query for help data.
        """
        self.registry = registry

    def handle(
        self,
        *,
        query: str,
        intent_type: str,
        context: Optional[dict] = None,
        language: str = "de",
        current_model: Optional[str] = None,
        current_provider: Optional[str] = None
    ) -> HelpOutput:
        """Handle a help query deterministically.

        This method NEVER calls an LLM. All responses are generated
        from registry data and templates.

        Args:
            query: The user's help query text.
            intent_type: One of "capability_overview", "how_to", "navigation", "model_query".
            context: Optional context (e.g., chat_id).
            language: ISO 639-1 language code (default: "de").
            current_model: Optional current model name (e.g., "gpt-4o").
            current_provider: Optional current provider ID (e.g., "openai").

        Returns:
            HelpOutput with answer, suggestions, actions, and fallback flag.
        """
        logger.info(
            "[HELP-SKILL] Handling query '%s...' with intent '%s' (lang=%s, model=%s, provider=%s)",
            query[:50],
            intent_type,
            language,
            current_model,
            current_provider
        )

        if intent_type == "capability_overview":
            return self._handle_capability_overview(query, language)
        elif intent_type == "how_to":
            return self._handle_how_to(query, language)
        elif intent_type == "navigation":
            return self._handle_navigation(query, language)
        elif intent_type == "model_query":
            return self._handle_model_query(query, language, current_model, current_provider)
        else:
            logger.warning("[HELP-SKILL] Unknown intent_type: %s", intent_type)
            return HelpOutput(
                answer=self.FALLBACK_MESSAGE,
                suggestions=[],
                actions=[],
                source_category=None,
                fallback_used=True
            )

    def _handle_capability_overview(self, query: str, language: str) -> HelpOutput:
        """Generate deterministic capability overview markdown.

        TASK-069.4: Uses filtered registry data, fixed category order,
        alphabetical sorting, and exact Markdown format.

        Args:
            query: The user's query (e.g., "Was kannst du?").
            language: Target language for the response.

        Returns:
            HelpOutput with rendered Markdown answer.
        """
        capabilities = self.registry.get_verified_capabilities_for_overview(language)

        if not capabilities:
            return HelpOutput(
                answer="Ich kann meine Fähigkeiten aktuell nicht zuverlässig anzeigen. Bitte versuche es später erneut.",
                suggestions=[],
                actions=[],
                source_category="capability_overview",
                fallback_used=True
            )

        # Group by category (normalization already handled by Registry, TASK-069.10)
        from collections import defaultdict
        grouped = defaultdict(list)
        for cap in capabilities:
            grouped[cap["category"]].append(cap)

        # Sort categories by CATEGORY_ORDER; unknowns come after "Sonstiges"
        order_index = {name: idx for idx, name in enumerate(self.CATEGORY_ORDER)}
        sorted_categories = sorted(
            grouped.keys(),
            key=lambda cat: order_index.get(cat, len(self.CATEGORY_ORDER))
        )

        # Build Markdown
        lines = [
            "## Das kann ich aktuell",
            "",
            "Ich kann dir aktuell in diesen Bereichen helfen:",
            "",
        ]

        for category in sorted_categories:
            lines.append(f"### {category}")
            # Sort capabilities alphabetically by name
            caps = sorted(grouped[category], key=lambda c: c["name"])
            for cap in caps:
                lines.append(f"- **{cap['name']}:** {cap['description']}")
            lines.append("")

        answer = "\n".join(lines)

        return HelpOutput(
            answer=answer,
            suggestions=[],
            actions=[],
            source_category="capability_overview",
            fallback_used=False
        )

    def _handle_how_to(self, query: str, language: str) -> HelpOutput:
        """Extract ability from query and return how-to instruction.
        
        Uses simple keyword matching against ability labels and IDs.
        
        Args:
            query: The user's how-to query (e.g., "Wie lade ich Dateien hoch?").
            language: Target language for the response.
        
        Returns:
            HelpOutput with how-to instruction or fallback.
        """
        query_lower = query.lower()
        categories = self.registry.all_categories()

        # Search through all categories for matching ability
        for category_id in categories:
            category = self.registry.get_category(category_id, language)
            if not category:
                continue

            for ability in category.get("abilities", []):
                ability_id = ability.get("id", "")
                label = ability.get("label", "").lower()
                how_to = ability.get("how_to", "")

                # Match by ability ID (e.g., "file.upload") or label
                # Extract simple keywords from ID (e.g., "upload" from "file.upload")
                ability_keywords = ability_id.replace(".", " ").lower().split()

                # Check if any keyword or label appears in query
                matches = (
                    any(kw in query_lower for kw in ability_keywords) or
                    label in query_lower or
                    any(part in query_lower for part in label.split())
                )

                if matches and how_to:
                    # Build answer with category context
                    category_name = category.get("display_name", category_id)
                    lines = [
                        f"Hier ist die Anleitung für **{ability.get('label', ability_id)}** ({category_name}):",
                        "",
                        f"👉 {how_to}"
                    ]

                    # Add follow-up suggestions
                    suggestions = [
                        "Was kannst du sonst noch?",
                        f"Wo finde ich {category_name}?"
                    ]

                    return HelpOutput(
                        answer="\n".join(lines),
                        suggestions=suggestions,
                        actions=[],
                        source_category=category_id,
                        fallback_used=False
                    )

        # No matching ability found
        return HelpOutput(
            answer=self.FALLBACK_MESSAGE,
            suggestions=["Was kannst du alles?"],
            actions=[],
            source_category=None,
            fallback_used=True
        )

    def _handle_navigation(self, query: str, language: str) -> HelpOutput:
        """Find UI location matching the query and return navigation action.
        
        Uses CapabilityRegistry.get_navigation() with keyword matching.
        
        Args:
            query: The user's navigation query (e.g., "Wo finde ich Dateien?").
            language: Target language for the response.
        
        Returns:
            HelpOutput with navigation answer and UI action.
        """
        nav_result = self.registry.get_navigation(query, language)

        if not nav_result:
            return HelpOutput(
                answer=self.FALLBACK_MESSAGE,
                suggestions=["Was kannst du alles?"],
                actions=[],
                source_category=None,
                fallback_used=True
            )

        # Build navigation answer
        category_name = nav_result.get("category", "")
        location_label = nav_result.get("label", "")
        action = nav_result.get("action")

        if action:
            lines = [
                f"Ich öffne **{category_name}** für dich:",
                "",
                f"👉 {location_label}"
            ]

            help_action = HelpAction(
                type=action.get("type", "open_module"),
                payload=action.get("payload", {})
            )

            return HelpOutput(
                answer="\n".join(lines),
                suggestions=["Was kann ich hier tun?"],
                actions=[help_action],
                source_category="navigation",
                fallback_used=False
            )
        else:
            # No specific action available
            lines = [
                f"**{category_name}** findest du im System.",
                "",
                "Nutze die Seitennavigation oder das Hauptmenü."
            ]

            return HelpOutput(
                answer="\n".join(lines),
                suggestions=["Was kannst du alles?"],
                actions=[],
                source_category="navigation",
                fallback_used=True
            )

    def _get_overview_intro(self, language: str) -> str:
        """Get localized intro text for capability overview."""
        intros = {
            "de": "Ich bin Janus, dein persönliches KI-Betriebssystem. Meine Aufgabe ist es, dir bei alltäglichen Aufgaben zu helfen. In Janus kannst du API-Keys verschiedener Provider hinterlegen und nahtlos mit den besten Modellen (OpenAI, Gemini, Anthropic, lokal) arbeiten.\n\n**Besonders: Mein Cross-Chat & Cross-Provider Identitäts-Gedächtnis** — Ich merke mir Informationen über dich über alle Chats und Provider hinweg, sodass ich dich besser kennenlernen kann.\n\nIch kann dir bei folgenden Dingen helfen:\n",
            "en": "I am Janus, your personal AI operating system. My task is to help you with everyday tasks. In Janus, you can add API keys from various providers and seamlessly work with the best models (OpenAI, Gemini, Anthropic, local).\n\n**Especially: My Cross-Chat & Cross-Provider Identity Memory** — I remember information about you across all chats and providers, so I can get to know you better.\n\nI can help you with the following:\n",
        }
        return intros.get(language, intros["de"])

    def _handle_model_query(self, query: str, language: str, current_model: Optional[str], current_provider: Optional[str]) -> HelpOutput:
        """Handle model introspection queries ("Welches Modell?", "Mit wem schreibe ich?").

        Args:
            query: The user's query.
            language: Target language for the response.
            current_model: Current model name (e.g., "gpt-5.4-trinity-logic").
            current_provider: Current provider ID (e.g., "openai").

        Returns:
            HelpOutput with model information or fallback.
        """
        # If we have model/provider information, provide detailed response
        if current_model and current_provider:
            provider_details = self.registry.get_provider_details(current_provider, language)
            model_profile = self.registry.get_model_profile(current_model, language)

            if provider_details and model_profile:
                # Format: [Modellname] [Level-Blitze] ([UX-Kategorie])
                level = model_profile.get("level", 1)
                ux_category = model_profile.get("ux_category", "Balance")
                level_blitze = "⚡" * level

                # Format: [Original-ID] ([Branding]) for gpt-5.4 models
                display_model = current_model
                if current_model.lower().startswith("gpt-5.4"):
                    display_model = f"{current_model} (Janus Trinity)"

                lines = [
                    f"**{display_model}** {level_blitze} ({ux_category})",
                    "",
                    f"🧠 **Kurzbeschreibung**",
                    f"👉 {model_profile['short_description']}",
                    "",
                    f"🚀 **Stärken**",
                ]

                # Split strengths by comma and format each as bullet
                strengths = model_profile.get("strengths", "")
                for strength in strengths.split(", "):
                    lines.append(f"👉 {strength}")

                lines.append("")
                lines.append(f"🎯 **Ideal für**")

                # Split ideal_for by comma and format each as bullet
                ideal_for = model_profile.get("ideal_for", "")
                for item in ideal_for.split(", "):
                    lines.append(f"👉 {item}")

                lines.append("")
                lines.append(f"⚠️ **Schwächen**")

                # Split weaknesses by comma and format each as bullet
                weaknesses = model_profile.get("weaknesses", "")
                for weakness in weaknesses.split(", "):
                    lines.append(f"👉 {weakness}")

                lines.append("")
                lines.append(f"💰 **Kosten-Profil**")

                # Split cost_profile by comma and format each as bullet
                cost_profile = model_profile.get("cost_profile", "")
                for cost in cost_profile.split(", "):
                    lines.append(f"👉 {cost}")

                lines.append("")

                return HelpOutput(
                    answer="\n".join(lines),
                    suggestions=["Was kannst du?", "Wechsle zu Gemini", "Nutze ein lokales Modell"],
                    actions=[],
                    source_category="model_query",
                    fallback_used=False
                )

        # Fallback: Generic response without specific model info
        lines = [
            "Ich arbeite mit einem KI-Modell aus dem Janus-Ökosystem.",
            "",
            "In Janus kannst du zwischen verschiedenen Providern wählen:",
            "- **OpenAI (GPT-5.4 Trinity)**: Ultimative Logik & Code",
            "- **Google Gemini (Gemini 3)**: 1M Context, Video-Analyse",
            "- **Anthropic Claude**: Nuanciertes Reasoning, kreatives Schreiben",
            "- **Ollama (Lokal)**: 100% Privacy, Offline",
        ]
        return HelpOutput(
            answer="\n".join(lines),
            suggestions=["Was kannst du?", "Nutze GPT-5.4 Trinity", "Wechsle zu Gemini"],
            actions=[],
            source_category="model_query",
            fallback_used=True
        )


# Factory function for dependency injection
def create_help_skill(registry: CapabilityRegistry) -> HelpSkill:
    """Create a HelpSkill instance with the given registry.
    
    Args:
        registry: Initialized CapabilityRegistry.
    
    Returns:
        Configured HelpSkill instance.
    """
    return HelpSkill(registry)
