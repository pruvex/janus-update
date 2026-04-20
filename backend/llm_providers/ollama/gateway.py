import logging
from typing import Any, Dict, List, Optional

from ..shared.base_gateway import BaseProviderGateway
from .service import OllamaServiceProvider
from .adapter import (
    apply_synthesis_call_contract,
    build_compact_synthesis_messages,
    match_intent_to_skills,
)
from backend.services.tool_manager import tool_manager
from backend.services.request_budget import (
    get_phase_budget,
    should_skip_expensive_synthesis,
)

logger = logging.getLogger("janus_backend")

_OLLAMA_SYNTHESIS_LITE_SYSTEM_PROMPT = (
    "Du bist Janus, ein intelligenter und hilfreicher Assistent. Antworte natürlich, höflich und auf Deutsch.\n\n"
    "### STRIKTE WÄHRUNGS-DIREKTIVE ###\n"
    "Du bist ein europäischer Finanzassistent. Deine Aufgabe ist es, den Preis in EURO zu finden. Halte dich an folgende Regeln:\n\n"
    "1. PRIORISIERE EURO: Durchsuche die Websuche-Ergebnisse explizit nach Preisen in Euro (€). Nenne diesen Preis und das Datum (heute ist der 26.03.2026).\n\n"
    "2. FALLBACK MIT WARNUNG: Wenn du absolut keinen Preis in Euro findest, aber einen in einer anderen Währung (z.B. US-Dollar), dann nenne diesen Preis und gib die Währung explizit an (Beispiel: '1.936 US-Dollar').\n\n"
    "3. IGNORIERE DEIN WISSEN: Verlasse dich nur auf die Preise und Daten in den aktuellen Suchergebnissen. Konvertiere keine Währungen selbstständig.\n\n"
    "Beantworte die Anfrage des Nutzers jetzt sofort mit diesen Regeln.\n\n"
    "🚨 FORMATIERUNGS-REGELN FÜR TOOL-ERGEBNISSE (ZUSAMMENFASSUNG):\n"
    "Wenn dir Tool-Ergebnisse mit Orten, Restaurants oder Geschäften vorliegen, MUSST du folgendes Markdown-Format verwenden:\n\n"
    "Schreibe einen netten Einleitungssatz (z.B. 'Hier ist eine schöne Auswahl für dich:').\n"
    "Pro Ort nutzt du exakt dieses Template:\n"
    "### 🍽️ [Name des Ortes]\n"
    "- 📍 **Adresse:** [Adresse]\n"
    "- 🕒 **Öffnungszeiten:** [Zeiten, falls vorhanden]\n"
    "- 📞 **Telefon:** [Nummer, falls vorhanden]\n"
    "- 🌐 [Website besuchen](Link-zur-Website) | 📅 [Tisch reservieren](Link-zur-Reservierung)\n\n"
    "WICHTIG: \n"
    "1. Übersetze rohe Datenbank-Tags (wie 'italian' oder 'pizza') in natürliche Sprache (z.B. 'Ein gemütliches italienisches Restaurant'). Schreibe niemals einfach 'italian'!\n"
    "2. Baue echte klickbare Markdown-Links. Schreibe niemals nur das Wort 'Link'. Wenn keine Website da ist, lass die Zeile weg.\n"
    "3. Sei proaktiv: Wenn du 4 Orte hast, präsentiere sie schön übersichtlich.\n\n"
    "Wenn Routing-Daten aus Tools vorliegen, nenne pro Etappe zwingend: Start, Ziel, Distanz, Dauer und Google-Maps-Link.\n"
    "Verwende niemals system.rss_news für Echtzeit-Preisanfragen (Aktien, Gold, Währungen). RSS-Feeds sind für Schlagzeilen, nicht für aktuelle Preisdaten.\n"
    "Verwende für alle Anfragen nach Preisen, Kursen oder aktuellen Marktdaten strikt system.websearch.\n"
    "Wenn der User nach aktuellen Kursen, Preisen oder Marktdaten fragt, MUSS system.websearch genutzt werden. Andere Tools wie Wikipedia oder RSS sind dafür nicht geeignet.\n"
    "Wenn du deterministische Fakten oder eine deterministische Antwort von einem Renderer erhältst, integriere diese Fakten in eine höfliche, direkte Antwort an den Benutzer und beende den Task.\n\n"
    "Halte deine Antworten kurz, präzise und direkt auf den Punkt."
)


class OllamaGateway(BaseProviderGateway):
    def __init__(self):
        self.service = OllamaServiceProvider()

    def _limit_tools(
        self,
        tool_definitions: List[Dict[str, Any]],
        limit: int = 10,
        user_prompt: str = "",
    ) -> List[Dict[str, Any]]:
        """Priorisiert fuer lokale Modelle die wichtigsten Tool-Familien bei begrenztem Kontextbudget.

        When *user_prompt* is provided the Capability-Layer intent matcher boosts
        tools whose skill family matches the detected intent keywords, so the
        limited tool list always contains the most relevant skills for the request.
        """
        if len(tool_definitions) <= limit:
            return tool_definitions

        prompt_lower = str(user_prompt or "").lower()
        price_or_market_markers = [
            "preis",
            "preise",
            "kurs",
            "kurse",
            "goldpreis",
            "aktienkurs",
            "wechselkurs",
            "marktdaten",
            "feinunze",
            "spotpreis",
            "wÃ¤hrung",
            "waehrung",
        ]
        is_price_or_market_query = any(marker in prompt_lower for marker in price_or_market_markers)

        intent_boosted: set[str] = set()
        if user_prompt:
            intent_boosted = set(match_intent_to_skills(user_prompt, top_k=4))
            if is_price_or_market_query:
                intent_boosted.add("system.websearch")
                intent_boosted.discard("system.rss_news")
            if intent_boosted:
                logger.info(
                    "INTENT-MATCHER: Boosted skills for Ollama tool-limit: %s",
                    sorted(intent_boosted),
                )

        def _priority(tool_def: Dict[str, Any]) -> tuple[int, str]:
            tool_name = str(tool_def.get("name") or "")
            tool_skill_id = str(tool_manager.get_skill_id(tool_name) or "")
            if is_price_or_market_query:
                if tool_name == "system.websearch" or tool_skill_id == "system.websearch":
                    return (-2, tool_name)
                if tool_name == "system.rss_news" or tool_skill_id == "system.rss_news":
                    return (10, tool_name)
            if tool_skill_id in intent_boosted or tool_name in intent_boosted:
                return (0, tool_name)
            if tool_name == "system.websearch":
                return (1, tool_name)
            if tool_skill_id == "system.routing":
                return (2, tool_name)
            if tool_name == "system.local_business" or tool_skill_id == "system.local_business":
                return (3, tool_name)
            if tool_name.startswith("filesystem."):
                return (4, tool_name)
            if tool_name.startswith("memory."):
                return (5, tool_name)
            return (6, tool_name)

        prioritized = sorted(tool_definitions, key=_priority)
        return prioritized[:limit]

    def _ensure_forced_visible(
        self,
        tool_definitions: List[Dict[str, Any]],
        all_tool_definitions: List[Dict[str, Any]],
        forced_tool: Optional[Dict[str, Any]],
        *,
        limit: int,
    ) -> List[Dict[str, Any]]:
        if not tool_definitions or not forced_tool:
            return tool_definitions
        forced_name = str(forced_tool.get("skill_id") or forced_tool.get("provider_tool_name") or "").strip()
        if not forced_name:
            return tool_definitions
        if any(str(item.get("name") or "").strip() == forced_name for item in tool_definitions if isinstance(item, dict)):
            return tool_definitions
        source_match = None
        for item in all_tool_definitions:
            if not isinstance(item, dict):
                continue
            item_name = str(item.get("name") or "").strip()
            item_skill_id = str(tool_manager.get_skill_id(item_name) or "").strip()
            if forced_name in {item_name, item_skill_id}:
                source_match = item
                break
        if source_match is None:
            return tool_definitions
        updated = list(tool_definitions)
        if len(updated) >= limit and updated:
            updated = updated[:-1]
        updated.append(source_match)
        return updated

    def _build_synthesis_messages(self, messages: List[Dict[str, Any]], keep_last: int = 3) -> List[Dict[str, Any]]:
        """Erstellt einen kompakten Synthesis-Kontext fuer lokale Ollama-Modelle."""
        return build_compact_synthesis_messages(
            messages,
            system_prompt=_OLLAMA_SYNTHESIS_LITE_SYSTEM_PROMPT,
            keep_last=keep_last,
        )

    @staticmethod
    def prepare_tools(tool_definitions: List[Dict[str, Any]], user_prompt: str = "") -> List[Dict[str, Any]]:
        """Static method for tool preparation in the monolith."""
        gateway = OllamaGateway()
        return gateway._limit_tools(tool_definitions, limit=10, user_prompt=user_prompt)

    async def reason_and_respond(
        self,
        provider: str,
        model: str,
        api_key: str,
        chat_history: List[Dict[str, Any]],
        context_manager: Any,
        db: Any,
        user_prompt: str,
        chat_id: int,
        tool_executor: Any,
        allowed_skill_ids: Optional[List[str]] = None,
        max_tool_rounds: int = 5,
        tools_override: Optional[List[Dict[str, Any]]] = None,
        disable_tools: bool = False,
        image_data: Optional[str] = None,
        background_tasks: Any = None,
        bypass_policy: bool = False,
        tool_results: Optional[List[Dict[str, Any]]] = None,
        request_budget: Any = None,
        validated_tool_definitions: Optional[List[Dict[str, Any]]] = None,
        current_round: int = 1,
        forced_tool: Optional[Dict[str, Any]] = None,
        all_tool_definitions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Ollama-specific reasoning with budget guards and synthesis orchestration.
        Unterstützt sowohl die erste Runde als auch die Synthese.
        """
        validated_tool_definitions = validated_tool_definitions or []
        all_tool_definitions = all_tool_definitions or []
        # 3. Delegiere Orchestrierung an das Silo
        logger.info(f"OLLAMA-SILO: Starte reasoning (Round {current_round}).")

        # Wenn der Router bereits tool_results liefert, springen wir direkt zur Synthese
        if tool_results is not None and current_round == 1:
            logger.info("OLLAMA-SILO: Tool-Ergebnisse bereits vorhanden, wechsle in Synthese-Modus.")
            # Wir simulieren hier, dass wir in einer höheren Runde sind
            current_round = 2 


        # Budget-Guard
        if request_budget and should_skip_expensive_synthesis(request_budget, provider=provider):
            logger.warning("OLLAMA-BUDGET-GUARD: Budget erschöpft.")
            return {"text": "Budget erschöpft.", "budget_guarded": True}

        # Tool-Limitierung
        limited_tool_definitions = validated_tool_definitions
        if current_round == 1 and not disable_tools:
            limited_tool_definitions = self._limit_tools(validated_tool_definitions, limit=10, user_prompt=user_prompt)
            limited_tool_definitions = self._ensure_forced_visible(
                limited_tool_definitions,
                all_tool_definitions,
                forced_tool,
                limit=10,
            )

        # Status bestimmen
        has_tool_results_in_history = any(str(msg.get("role") or "") == "tool" for msg in chat_history)
        is_final_answer_phase = (current_round > 1 or tool_results is not None) and (has_tool_results_in_history or tool_results)

        messages_for_call = chat_history
        tools_for_call = limited_tool_definitions if current_round == 1 and not disable_tools else None
        call_type_for_api = None

        if is_final_answer_phase:
            tools_for_call = None
            messages_for_call = self._build_synthesis_messages(chat_history, keep_last=3)
            call_type_for_api = "synthesis"
            logger.info("OLLAMA-SILO: Synthese-Phase aktiv.")

        api_call_params = {
            "provider": provider,
            "api_key": api_key, "model": model, "messages": messages_for_call,
            "image_data": image_data if current_round == 1 else None,
        }
        # 💎 Tools IMMER mitgeben wenn verfügbar (nicht nur für bestimmte Modelle)
        if tools_for_call:
            api_call_params["tools"] = tools_for_call
            api_call_params["tool_choice"] = "auto"

        if request_budget:
            api_call_params["request_deadline_seconds"] = get_phase_budget(
                request_budget,
                provider=provider,
                phase="synthesis" if call_type_for_api == "synthesis" else "tool_round",
            )

        if call_type_for_api:
            api_call_params = apply_synthesis_call_contract(api_call_params, call_type=call_type_for_api)

        # Finaler Aufruf
        response = await self.service.generate_response(**api_call_params)
        return response
