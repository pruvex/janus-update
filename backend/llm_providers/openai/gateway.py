import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.llm_providers.ollama_adapter import build_compact_synthesis_messages
from backend.llm_providers.shared.base_gateway import BaseProviderGateway
from backend.llm_providers.shared.utils import (
    _extract_release_line_title,
    _extract_tool_payload,
    _extract_websearch_sources_for_link_repair,
    _find_best_source_for_release_title,
    _normalize_match_key,
)

from .service import OpenAIServiceProvider

logger = logging.getLogger("janus_backend")

_RESEARCH_SYNTHESIS_RULE = (
    "AUFGABE: Preisvergleich aus Web-Snippets. Keine Einleitung. Kein Schluss. Nur Bulletpoints.\n\n"

    "SCHRITT 1 – HARD-BAN:\n"
    "Ignoriere ALLE Preise von News-Seiten und Shops (chip.de, netzwelt.de, euronics.de, "
    "alternate.de, saturn.de, mediamarkt.de, computeruniverse.net, notebooksbilliger.de etc.), "
    "solange ein Snippet von idealo.de ODER geizhals.de existiert. "
    "Existiert kein Preisvergleichs-Snippet, schreibe: '- [Produkt]: Preis nicht verfügbar'\n\n"

    "SCHRITT 2 – DAS DUELL (für jede Variante):\n"
    "Vergleiche den idealo.de-Preis mit dem geizhals.de-Preis für dieselbe Variante. "
    "Nenne NUR den günstigsten Preis der beiden. "
    "Merke dir, welche Quelle gewonnen hat – du brauchst sie für das Format.\n\n"

    "SCHRITT 3 – VARIANTEN-PFLICHT:\n"
    "Jede Produktvariante (Standard / Bundle / OLED / Lite / Digital / Pro) = eigener Bulletpoint. "
    "Niemals zusammenfassen. Wenn du 3 Varianten siehst, schreibst du 3 Bulletpoints.\n\n"

    "SCHRITT 4 – PFLICHT-FORMAT (Zeichen für Zeichen einhalten):\n"
    "- [Produktname] ([Variante]): ab [Preis] € (Stand: 27.03.2026) ([gewinner-quelle.de])\n"
    "Beispiel:\n"
    "- Nintendo Switch 2 (Standard): ab 424,90 € (Stand: 27.03.2026) (geizhals.de)\n"
    "- Nintendo Switch 2 (Mario Kart Bundle): ab 459,00 € (Stand: 27.03.2026) (idealo.de)\n\n"

    "SCHRITT 5 – PREIS-INTEGRITÄT:\n"
    "Übernimm den Preis EXAKT aus dem Snippet. '424,90 €' bleibt '424,90 €'. Keine Rundung. "
    "Preise über 1.500 € für Consumer-Elektronik = Datenfehler (Artikelnummer/Katalog). Ignorieren.\n\n"

    "ABSOLUT VERBOTEN:\n"
    "- Markdown-Links [Text](URL) oder nackte URLs im Text.\n"
    "- Jeder einleitende Satz ('Hier sind...', 'Aktuell...', 'Basierend auf...', 'Ich habe...').\n"
    "- Jeder abschließende Satz ('Wenn du willst...', 'Soll ich...', 'Hast du Fragen?', 'Ich hoffe...').\n"
    "- Die Antwort endet SOFORT nach dem letzten Bulletpoint. Kein weiteres Zeichen."
)

_LOCALIZATION_DIRECTIVES = (
    "LOKALISIERUNG: Du operierst in Deutschland. Antworte standardmäßig auf Deutsch. Verwende Euro (€) als Standardwährung und metrische Einheiten (Kilometer, Grad Celsius). Frage den Nutzer NICHT nach Land oder Währung, außer er bittet explizit darum. Triff stattdessen Annahmen basierend auf dem Standort Deutschland, inklusive lokaler Feiertage, Öffnungszeiten und Steuerlogiken.",
    "SMART ASSUMPTIONS: Stelle bei Preis- oder Informationsfragen KEINE Rückfragen zu Land oder Währung, wenn der Nutzer nichts spezifiziert. Nutze standardmäßig Deutschland und Euro und formuliere deine Antwort als 'Basierend auf dem deutschen Markt kostet [Produkt] derzeit [Preis].' Sei proaktiv statt nachzufragen.",
    "LOKALISIERUNGS-REGEL: Du operierst für einen Nutzer in Deutschland. Wenn nach Preisen, Kosten oder Währungen gefragt wird, nutze IMMER Euro (€) und deutsche Marktpreise als Standard. Nenne dem Nutzer den Preis basierend auf diesen Annahmen und frage NICHT nach Land oder Währung, es sei denn, der Nutzer fragt explizit nach einem anderen Land.",
)


class OpenAIGateway(BaseProviderGateway):
    def __init__(self) -> None:
        self.service = OpenAIServiceProvider()

    @staticmethod
    def _sanitize_generate_response_kwargs(kwargs: Optional[Dict[str, Any]], *explicit_keys: str) -> Dict[str, Any]:
        sanitized = dict(kwargs or {})
        for key in explicit_keys:
            sanitized.pop(key, None)
        return sanitized

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
        tool_limit_reached: bool = False,
        allow_pdf_enrichment: bool = False,
        provider_service: Optional[OpenAIServiceProvider] = None,
        force_tool_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Zentraler Einstiegspunkt für das OpenAI-Silo.
        Unterstützt sowohl die direkte Synthese als auch den vollständigen Tool-Loop.
        """
        # 1. Wenn tool_results fehlen -> Führe den Tool-Loop hier im Silo aus
        if tool_results is None:
            logger.info("OpenAI Silo: Führe vollständigen Tool-Loop aus.")
            return await self._run_full_tool_loop(
                provider=provider,
                model=model,
                api_key=api_key,
                chat_history=chat_history,
                user_prompt=user_prompt,
                tool_executor=tool_executor,
                allowed_skill_ids=allowed_skill_ids,
                max_tool_rounds=max_tool_rounds,
                image_data=image_data,
                db=db,
                force_tool_name=force_tool_name,
            )

        # 2. Wenn tool_results vorhanden -> Bestehende Synthese-Logik
        logger.info("OpenAI Silo Gateway aktiv: finalisiere Research-Synthese.")
        final_messages = self.build_research_synthesis_messages(chat_history)
        
        # Robustes Kwargs-Handling
        active_service = provider_service or self.service
        response = await active_service.generate_response(
            api_key=api_key,
            model=model,
            messages=final_messages,
            tools=None,
        )

        gateway_helpers = self._gateway_helpers()
        response["tool_limit_reached"] = tool_limit_reached
        response["skip_fact_extraction"] = gateway_helpers._should_skip_fact_extraction_for_tool_results(tool_results)
        response = gateway_helpers._apply_routing_quality_guards(
            response,
            chat_history,
            allow_pdf_enrichment=allow_pdf_enrichment,
        )
        response = self.ensure_release_list_links_in_text_response(
            response,
            user_prompt=user_prompt,
            tool_results=tool_results,
        )
        response = self.ensure_combined_release_response_structure(
            response,
            user_prompt=user_prompt,
            tool_results=tool_results,
        )
        response.setdefault("provider", provider)
        response.setdefault("model", model)
        return response

    async def _run_full_tool_loop(self, **kwargs) -> Dict[str, Any]:
        """
        Interne Implementierung des Tool-Loops für OpenAI.

        💎 MoA-Integration: Wenn der primäre Skill einen optimal_model_tier hat,
        wird für den Tool-Loop ein günstigeres/schnelleres Modell verwendet.
        Die finale Text-Synthese erfolgt IMMER mit dem user_base_model (Persona-Wahrung).
        """
        from backend.llm_providers.shared.utils import (
            _filter_tools_by_skill_ids,
            _build_tool_definitions_for_llm,
            _prevalidate_tool_calls,
            _apply_routing_quality_guards
        )
        from backend.llm_providers.shared.moa import resolve_moa_model
        import json

        passthrough_kwargs = dict(kwargs or {})
        provider = passthrough_kwargs.pop("provider", None)
        model = passthrough_kwargs.pop("model", None)
        api_key = passthrough_kwargs.pop("api_key", None)
        chat_history = passthrough_kwargs.pop("chat_history", [])
        user_prompt = passthrough_kwargs.pop("user_prompt", "")
        allowed_skill_ids = passthrough_kwargs.pop("allowed_skill_ids", None)
        tool_executor = passthrough_kwargs.pop("tool_executor", None)
        max_tool_rounds = passthrough_kwargs.pop("max_tool_rounds", 5)
        image_data = passthrough_kwargs.pop("image_data", None)
        db = passthrough_kwargs.pop("db", None)
        # 💎 VIDEO-FORCE: Extract force_tool_name for first-round tool_choice override
        _force_tool_name = str(passthrough_kwargs.pop("force_tool_name", "") or "").strip() or None

        # 💎 MoA-Routing: Bestimme das optimale Modell für den Tool-Loop
        # HONOR OVERRIDE: If execution_engine already upgraded the model, use that
        user_base_model = model
        
        # Check if model was already overridden by execution_engine (contains upgrade marker)
        forced_model = None
        if chat_history and len(chat_history) > 0:
            # Look for model override in system messages
            for msg in chat_history:
                if msg.get("role") == "system" and "MODEL_OVERRIDE:" in str(msg.get("content", "")):
                    match = re.search(r"MODEL_OVERRIDE:\s*(\S+)", str(msg.get("content", "")))
                    if match:
                        forced_model = match.group(1)
                        logger.info("💎 OpenAI-Silo: Model override detected from execution_engine: %s", forced_model)
                        break
        
        if forced_model:
            tool_execution_model = forced_model
            moa_active = True
        else:
            tool_execution_model, moa_active = resolve_moa_model(
                provider=provider,
                user_base_model=user_base_model,
                allowed_skill_ids=allowed_skill_ids,
            )

        # 💎 DIAMOND WEBSEARCH OVERRIDE: system.websearch hat Vertragsrecht auf
        # seinen optimal_model_tier – unabhängig davon, an welcher Position er in
        # allowed_skill_ids steht.  Behebt den Nano-Zwang bei gemischten Skill-Listen.
        if allowed_skill_ids and "system.websearch" in allowed_skill_ids:
            _ws_model, _ws_moa = resolve_moa_model(
                provider=provider,
                user_base_model=user_base_model,
                allowed_skill_ids=["system.websearch"],
            )
            if _ws_moa:
                tool_execution_model = _ws_model
                moa_active = True
                logger.info(
                    "💎 WEBSEARCH-SKILL-OVERRIDE: Using model: %s for synthesis "
                    "(tier via system.websearch JSON contract) [Provider: %s]",
                    _ws_model,
                    provider,
                )

        current_round = 0
        current_chat_history = list(chat_history)
        # 💎 Sammle alle Tool-Resultate für den Renderer (WebSearch-Links)
        _all_tool_results: List[Dict[str, Any]] = []
        # 💎 COST-ACCUMULATION: Sammle Kosten über alle internen Runden (Planning + Synthesis)
        _loop_cost_eur = 0.0
        _loop_input_tokens = 0
        _loop_output_tokens = 0

        while current_round < max_tool_rounds:
            current_round += 1
            
            all_available_tools = _filter_tools_by_skill_ids(allowed_skill_ids)
            tools_for_call = _build_tool_definitions_for_llm(all_available_tools)

            # Robustes Kwargs-Handling für den Service-Call
            loop_kwargs = passthrough_kwargs.get("passthrough_kwargs")
            if loop_kwargs is None:
                loop_kwargs = {}
            loop_kwargs = self._sanitize_generate_response_kwargs(
                loop_kwargs,
                "api_key",
                "model",
                "messages",
                "tools",
                "image_data",
            )

            # 💎 VIDEO-FORCE: Only force tool_choice on first round
            _round_force = _force_tool_name if current_round == 1 else None
            response = await self.service.generate_response(
                api_key=api_key,
                model=tool_execution_model,
                messages=current_chat_history,
                tools=tools_for_call,
                image_data=image_data if current_round == 1 else None,
                force_tool_name=_round_force,
                **loop_kwargs
            )

            # Accumulate cost from this round
            _r_cost = response.get("cost") or {}
            _r_usage = response.get("usage") or {}
            _loop_cost_eur += float(_r_cost.get("total_cost", 0.0))
            _loop_input_tokens += int(_r_usage.get("input_tokens", 0))
            _loop_output_tokens += int(_r_usage.get("output_tokens", 0))

            if response.get("type") != "tool_code":
                if _round_force and current_round == 1:
                    forced_tool_call = self.build_forced_fallback_tool_call(
                        {
                            "skill_id": _round_force,
                            "provider_tool_name": _round_force,
                        },
                        user_prompt=user_prompt,
                        chat_history=current_chat_history,
                        fallback_text=str(response.get("text") or ""),
                    )
                    if forced_tool_call:
                        forced_preflight = _prevalidate_tool_calls([forced_tool_call], user_prompt=user_prompt)
                        forced_validated_calls = forced_preflight["valid_calls"]
                        if forced_validated_calls:
                            logger.warning(
                                "OPENAI-FORCED-TOOL-FALLBACK: Model returned text despite forced tool '%s'; executing deterministic fallback.",
                                _round_force,
                            )
                            executor_results = await tool_executor.execute_tool_calls(forced_validated_calls)
                            for _tr in (executor_results or []):
                                if isinstance(_tr, dict):
                                    _all_tool_results.append(_tr)
                            raw_forced_assistant_response = {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": forced_tool_call.get("id"),
                                        "type": "function",
                                        "function": {
                                            "name": str(forced_tool_call.get("function", {}).get("name") or "").replace(".", "_"),
                                            "arguments": forced_tool_call.get("function", {}).get("arguments", "{}"),
                                        },
                                    }
                                ],
                            }
                            current_chat_history = self.service.prepare_history_for_second_call(
                                chat_history=current_chat_history,
                                raw_assistant_response=raw_forced_assistant_response,
                                tool_results=executor_results,
                            )
                            continue
                # 💎 MoA-Rücksprung: Wenn Tool-Modell != User-Modell,
                # verwerfe den Text des Tool-Modells und synthetisiere mit dem User-Basismodell.
                if moa_active:
                    logger.info(
                        "💎 SKILL-MOA RÜCKSPRUNG: Tool-Loop abgeschlossen mit '%s'. "
                        "Synthetisiere finale Antwort mit smartem Tool-Modell '%s'.",
                        tool_execution_model,
                        tool_execution_model,
                    )
                    logger.info("💎 Using model: %s for synthesis", tool_execution_model)
                    # --- SMART SYNTHESIS FIX ---
                    # FIX: 'provider_service' war nicht definiert. Es muss 'self.service' heißen.
                    
                    # 💎 DIAMOND FIX: Wende die Research-Regeln auch im MoA-Pfad an!
                    if allowed_skill_ids and "system.websearch" in allowed_skill_ids:
                        synthesis_messages = self.build_research_synthesis_messages(current_chat_history)
                    else:
                        synthesis_messages = current_chat_history

                    synthesis_response = await self.service.generate_response(
                        api_key=api_key,
                        model=tool_execution_model,
                        messages=synthesis_messages, # <--- Nutzt jetzt die Diamond-Regeln
                        tools=None,
                        image_data=None,
                    )
                    synthesis_response = _apply_routing_quality_guards(synthesis_response, current_chat_history)
                    synthesis_response["moa_tool_model"] = tool_execution_model
                    synthesis_response["moa_synthesis_model"] = tool_execution_model
                    synthesis_response["_internal_tool_results"] = _all_tool_results
                    # Add synthesis call cost to accumulated loop cost
                    _syn_cost = synthesis_response.get("cost") or {}
                    _syn_usage = synthesis_response.get("usage") or {}
                    _loop_cost_eur += float(_syn_cost.get("total_cost", 0.0))
                    _loop_input_tokens += int(_syn_usage.get("input_tokens", 0))
                    _loop_output_tokens += int(_syn_usage.get("output_tokens", 0))
                    synthesis_response["cost"] = {"total_cost": _loop_cost_eur}
                    synthesis_response["usage"] = {
                        "input_tokens": _loop_input_tokens,
                        "output_tokens": _loop_output_tokens,
                    }
                    # 💎 PERSISTENCE-FIX: Speichere akkumulierte Kosten für gpt-4o-mini
                    if db is not None and _loop_cost_eur > 0:
                        try:
                            from backend.services.cost_service import create_cost_entry
                            create_cost_entry(
                                db=db,
                                amount=_loop_cost_eur,
                                model=tool_execution_model,
                                provider=str(provider or "openai"),
                                source_type="conversation",
                                input_tokens=_loop_input_tokens,
                                output_tokens=_loop_output_tokens,
                            )
                            logger.info("GATEWAY-COST-PERSIST: Saved %.6f€ for %s", _loop_cost_eur, tool_execution_model)
                        except Exception:
                            logger.warning("GATEWAY-COST-PERSIST: Failed to save cost", exc_info=True)
                    return synthesis_response

                response = _apply_routing_quality_guards(response, current_chat_history)
                response["_internal_tool_results"] = _all_tool_results
                # Merged cost already accumulated (this is the final round)
                response["cost"] = {"total_cost": _loop_cost_eur}
                response["usage"] = {
                    "input_tokens": _loop_input_tokens,
                    "output_tokens": _loop_output_tokens,
                }
                # 💎 PERSISTENCE-FIX: Speichere akkumulierte Kosten für gpt-4o-mini
                if db is not None and _loop_cost_eur > 0:
                    try:
                        from backend.services.cost_service import create_cost_entry
                        create_cost_entry(
                            db=db,
                            amount=_loop_cost_eur,
                            model=tool_execution_model,
                            provider=str(provider or "openai"),
                            source_type="conversation",
                            input_tokens=_loop_input_tokens,
                            output_tokens=_loop_output_tokens,
                        )
                        logger.info("GATEWAY-COST-PERSIST: Saved %.6f€ for %s", _loop_cost_eur, tool_execution_model)
                    except Exception:
                        logger.warning("GATEWAY-COST-PERSIST: Failed to save cost", exc_info=True)
                return response

            tool_calls = response.get("tool_calls", [])
            preflight = _prevalidate_tool_calls(tool_calls, user_prompt=user_prompt)
            validated_tool_calls = preflight["valid_calls"]
            
            if not validated_tool_calls:
                return response

            executor_results = await tool_executor.execute_tool_calls(validated_tool_calls)
            # 💎 Tool-Resultate für Renderer sammeln
            for _tr in (executor_results or []):
                if isinstance(_tr, dict):
                    _all_tool_results.append(_tr)
                    # --- START DEBUG INSERTION: RAW WEBSEARCH SKILL RESPONSE DATA ---
                    if _tr.get("skill_id") == "system.websearch" and _tr.get("status") == "ok":
                        logger.info("--- DEBUG: Printing raw websearch tool result data ---")
                        try:
                            # Wir wollen das 'data' Feld der SkillResponse sehen
                            logger.info(json.dumps(_tr.get("data"), indent=2, ensure_ascii=False))
                        except TypeError:
                            logger.info(str(_tr.get("data"))) # Fallback für nicht-serialisierbare Daten
                        logger.info("--- END DEBUG: RAW WEBSEARCH SKILL RESPONSE DATA ---\n")
                    # --- END DEBUG INSERTION ---

            current_chat_history = self.service.prepare_history_for_second_call(
                chat_history=current_chat_history,
                raw_assistant_response=response.get("raw_assistant_response"),
                tool_results=executor_results
            )

        return {"text": "Maximale Tool-Runden erreicht.", "tool_limit_reached": True, "_internal_tool_results": _all_tool_results}

    @staticmethod
    def collect_research_system_overrides(messages: List[Dict[str, Any]]) -> List[str]:
        overrides: List[str] = []
        seen: set[str] = set()
        markers = (
            "Websearch-Synthese-Modus",
            "Die Websuche war erfolgreich. Antworte jetzt final ohne weitere Tools.",
            "VERPFLICHTENDE LISTEN-REGEL",
            "anklickbaren Markdown-Link",
            "pro Spiel exakt dieses Format",
            "SKILL-DIRECTIVE",
        )
        for message in messages or []:
            if not isinstance(message, dict) or str(message.get("role") or "") != "system":
                continue
            content = str(message.get("content") or "").strip()
            if not content or content == _RESEARCH_SYNTHESIS_RULE or content in _LOCALIZATION_DIRECTIVES:
                continue
            if not any(marker in content for marker in markers):
                continue
            if content in seen:
                continue
            seen.add(content)
            overrides.append(content)
        return overrides[-2:]

    @classmethod
    def build_research_synthesis_messages(cls, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        system_prompt_parts = [_RESEARCH_SYNTHESIS_RULE]
        system_prompt_parts.extend(cls.collect_research_system_overrides(messages))
        
        # 💎 DIAMOND FIX: Explizites Verbot von Markdown-Links und Meta-Talk
        system_prompt_parts.append(
            "ABSOLUT VERBOTEN: Markdown-Links ([Text](URL)) oder nackte URLs im Text. "
            "ABSOLUT VERBOTEN: Rückfragen oder Höflichkeitsfloskeln wie 'Wenn du willst...', 'Soll ich...', 'Hast du Fragen?'."
        )
        
        return build_compact_synthesis_messages(
            messages,
            system_prompt="\n\n".join(system_prompt_parts),
            keep_last=4,
        )

    @staticmethod
    def is_pure_websearch_flow(
        provider: str,
        allowed_skill_ids: Optional[List[str]],
        forced_tool: Optional[Dict[str, Any]],
    ) -> bool:
        if str(provider or "").lower() != "openai":
            return False
        allowed = sorted(
            {
                str(skill_id or "").strip()
                for skill_id in (allowed_skill_ids or [])
                if str(skill_id or "").strip()
            }
        )
        if allowed != ["system.websearch"]:
            return False
        return str((forced_tool or {}).get("skill_id") or "").strip().lower() == "system.websearch"

    @staticmethod
    def build_websearch_first_round_messages(user_prompt: str) -> List[Dict[str, Any]]:
        prompt = str(user_prompt or "").strip()
        return [
            {
                "role": "system",
                "content": (
                    "Du bist Janus im kompakten Websearch-Dispatch-Modus. "
                    "Antworte nicht im Fließtext. Rufe ausschließlich system.websearch für die aktuelle Nutzerfrage auf."
                ),
            },
            {"role": "user", "content": prompt},
        ]

    @classmethod
    def build_forced_fallback_tool_call(
        cls,
        forced_tool: Dict[str, Any],
        user_prompt: str,
        chat_history: List[Dict[str, Any]],
        fallback_text: str = "",
    ) -> Optional[Dict[str, Any]]:
        gateway_helpers = cls._gateway_helpers()
        skill_id = str(forced_tool.get("skill_id") or "").strip().lower()
        provider_tool_name = str(forced_tool.get("provider_tool_name") or "").strip() or skill_id

        if skill_id == "system.websearch":
            args = {
                "query": gateway_helpers._build_websearch_fallback_query(user_prompt, fallback_text),
            }
            return {
                "id": "fallback_forced_websearch",
                "type": "function",
                "function": {
                    "name": provider_tool_name,
                    "arguments": json.dumps(args, ensure_ascii=False),
                },
            }

        if skill_id == "system.wikipedia_summary":
            query = cls._extract_wikipedia_fallback_query(user_prompt)
            if not query:
                return None
            args = {
                "query": query,
                "lang": "de",
            }
            return {
                "id": "fallback_forced_wikipedia_summary",
                "type": "function",
                "function": {
                    "name": provider_tool_name,
                    "arguments": json.dumps(args, ensure_ascii=False),
                },
            }

        if skill_id == "system.rss_news":
            source = cls._extract_rss_fallback_source(user_prompt)
            if not source:
                return None
            args = {
                "source": source,
            }
            return {
                "id": "fallback_forced_rss_news",
                "type": "function",
                "function": {
                    "name": provider_tool_name,
                    "arguments": json.dumps(args, ensure_ascii=False),
                },
            }

        if skill_id == "system.generate_image":
            title = re.sub(
                r"\.pdf$",
                "",
                gateway_helpers._extract_requested_pdf_filename(user_prompt),
                flags=re.IGNORECASE,
            ).replace("_", " ").strip() or "Bericht"
            title = gateway_helpers._extract_story_topic_from_prompt(user_prompt, title)
            total_images = max(1, int(forced_tool.get("total_image_count") or 1))
            image_index = max(1, int(forced_tool.get("image_index") or 1))
            prompt = gateway_helpers._build_story_scene_image_prompt(
                user_prompt=user_prompt,
                title=title,
                image_index=image_index,
                total_images=total_images,
            )
            args = {
                "prompt": prompt,
                "size": "1024x1024",
                "quality": "low",
                "response_format": "url",
            }
            return {
                "id": "fallback_forced_generate_image",
                "type": "function",
                "function": {
                    "name": provider_tool_name,
                    "arguments": json.dumps(args, ensure_ascii=False),
                },
            }

        if skill_id == "system.create_pdf":
            markdown_images = gateway_helpers._extract_markdown_images_from_history(chat_history)
            if not markdown_images:
                return None

            filename = gateway_helpers._extract_requested_pdf_filename(user_prompt)
            title = re.sub(r"\.pdf$", "", filename, flags=re.IGNORECASE).replace("_", " ").strip() or "Bericht"
            story_text = str(fallback_text or "").strip()
            if len(story_text) < 30 or gateway_helpers._is_instruction_like_fallback_text(story_text):
                story_text = gateway_helpers._synthesize_story_text_for_pdf_fallback(
                    user_prompt=user_prompt,
                    title=title,
                    image_count=len(markdown_images),
                )

            layout_profile = gateway_helpers._select_layout_profile_for_pdf_fallback(user_prompt, story_text)
            text_parts = gateway_helpers._split_text_for_image_placement(story_text, len(markdown_images))
            content_lines: List[str] = [f"# {title}", ""]
            for idx, markdown_image in enumerate(markdown_images):
                if idx < len(text_parts):
                    content_lines.append(text_parts[idx])
                    content_lines.append("")
                content_lines.append(markdown_image)
                content_lines.append("")
            if len(text_parts) > len(markdown_images):
                content_lines.extend(text_parts[len(markdown_images) :])

            content = "\n".join(content_lines).strip()
            max_px = gateway_helpers._extract_requested_max_image_px(user_prompt)
            image_width_mm = 0
            if max_px:
                image_width_mm = max(20, min(180, int(round(max_px * 25.4 / 96))))

            args = {
                "content": content,
                "filename": filename,
                "location": "Documents",
                "include_image": True,
                "image_width": image_width_mm,
                "layout_profile": layout_profile,
                "source_prompt": str(user_prompt or "").strip(),
            }
            first_image_ref = gateway_helpers._extract_image_ref_from_markdown(markdown_images[0])
            if first_image_ref:
                args["image_path"] = first_image_ref
            return {
                "id": "fallback_forced_create_pdf",
                "type": "function",
                "function": {
                    "name": provider_tool_name,
                    "arguments": json.dumps(args, ensure_ascii=False),
                },
            }

        return None

    @staticmethod
    def _extract_wikipedia_fallback_query(user_prompt: str) -> str:
        query = re.sub(r"\s+", " ", str(user_prompt or "")).strip(" ?!.,:;\"'")
        query = re.sub(
            r"^(wer|was)\s+(ist|war|sind|waren)\s+",
            "",
            query,
            flags=re.IGNORECASE,
        )
        query = re.sub(
            r"^(erkläre|erklaere|beschreibe|definiere)\s+",
            "",
            query,
            flags=re.IGNORECASE,
        )
        query = re.sub(
            r"^(gib mir|zeige mir|such[e]?\s+mir)\s+(eine\s+)?(wikipedia[- ]?)?(zusammenfassung\s+)?(zu|über|ueber)\s+",
            "",
            query,
            flags=re.IGNORECASE,
        )
        return query.strip(" ?!.,:;\"'")

    @staticmethod
    def _extract_rss_fallback_source(user_prompt: str) -> Optional[str]:
        lowered = str(user_prompt or "").lower()
        for source in ("spiegel", "gamestar", "tagesschau", "zeit", "heise", "reuters", "bbc"):
            if source in lowered:
                return source
        return None

    @classmethod
    def ensure_release_list_links_in_text_response(
        cls,
        response: Dict[str, Any],
        *,
        user_prompt: str,
        tool_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not isinstance(response, dict) or not cls._is_game_release_websearch_prompt(user_prompt):
            return response

        text = str(response.get("text") or "")
        if not text.strip():
            return response

        sources = _extract_websearch_sources_for_link_repair(tool_results)
        if not sources:
            return response

        lines = text.splitlines()
        updated_lines: List[str] = []
        changed = False

        for line in lines:
            stripped = line.strip()
            if not re.match(r"^[-*+]\s+", stripped):
                updated_lines.append(line)
                continue

            title = _extract_release_line_title(stripped)
            if not title:
                updated_lines.append(line)
                continue

            matched_url = _find_best_source_for_release_title(title, sources)
            line_without_link = re.sub(r"\s*—\s*\[Mehr erfahren\]\([^)]+\)", "", line).rstrip()

            if matched_url:
                updated_lines.append(f"{line_without_link} — [Mehr erfahren]({matched_url})")
                changed = True
            else:
                updated_lines.append(f"{line_without_link} — (Keine spezifische Quelle gefunden)")
                changed = True

        if not changed:
            return response

        updated_response = dict(response)
        updated_response["text"] = "\n".join(updated_lines)
        logger.info("OPENAI LINK-REPAIR: Links in der Release-Liste wurden semantisch korrigiert.")
        return updated_response

    @classmethod
    def ensure_combined_release_response_structure(
        cls,
        response: Dict[str, Any],
        *,
        user_prompt: str,
        tool_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not isinstance(response, dict) or not cls._is_combined_game_release_websearch_prompt(user_prompt):
            return response
        text = str(response.get("text") or "").strip()
        if not text:
            return response

        lines = [line.rstrip() for line in text.splitlines()]
        release_lines: List[str] = []
        narrative_lines: List[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(r"^[-*+]\s+", stripped) and ("[Mehr erfahren](" in stripped or "—" in stripped):
                release_lines.append(stripped)
                continue
            if stripped.lower().startswith("## vollständige release-liste") or stripped.lower().startswith("## überblick"):
                continue
            narrative_lines.append(stripped)

        overview_bullets = cls._build_combined_release_overview_bullets(user_prompt, tool_results)
        structured_lines: List[str] = ["## Überblick"]
        if narrative_lines:
            structured_lines.extend(narrative_lines[:4])
        if overview_bullets:
            structured_lines.extend(overview_bullets)
        structured_lines.append("")
        structured_lines.append("## Vollständige Release-Liste")
        if release_lines:
            structured_lines.extend(release_lines)
        else:
            structured_lines.append("- Im Material konnte keine sicher extrahierbare vollständige Release-Liste deterministisch nachgebaut werden.")

        new_text = "\n".join(structured_lines).strip()
        if new_text == text:
            return response
        updated_response = dict(response)
        updated_response["text"] = new_text
        logger.info("OPENAI STRUCTURE-GUARD: Kombinierte Release-Antwort in Überblick+Liste-Struktur normalisiert.")
        return updated_response

    @classmethod
    def _collect_websearch_evidence_lines(cls, tool_results: List[Dict[str, Any]], max_items: int = 80) -> List[str]:
        collected: List[str] = []
        seen: set[str] = set()
        for result in tool_results or []:
            payload = _extract_tool_payload(result)
            if not payload or payload.get("status") != "ok":
                continue
            data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
            facts = data.get("facts") if isinstance(data.get("facts"), list) else []
            text_value = str(data.get("text") or "").strip()
            sources = data.get("sources") if isinstance(data.get("sources"), list) else []
            candidates: List[str] = []
            candidates.extend(str(fact or "").strip() for fact in facts)
            if text_value:
                candidates.extend(
                    str(part or "").strip()
                    for part in re.split(r"(?:\n+|(?<=[\.!?])\s+)", text_value)
                )
            for source in sources:
                if not isinstance(source, dict):
                    continue
                title = str(source.get("title") or "").strip()
                snippet = str(source.get("snippet") or "").strip()
                if title:
                    candidates.append(title)
                if snippet:
                    candidates.append(snippet)
            for candidate in candidates:
                normalized = _normalize_match_key(candidate)
                if not normalized or normalized in seen or len(candidate) < 12:
                    continue
                seen.add(normalized)
                collected.append(candidate)
                if len(collected) >= max_items:
                    return collected
        return collected

    @classmethod
    def _select_relevant_evidence_lines(
        cls,
        evidence_lines: List[str],
        *,
        required_tokens: Tuple[str, ...],
        preferred_tokens: Tuple[str, ...] = (),
        max_items: int = 3,
    ) -> List[str]:
        selected: List[str] = []
        seen: set[str] = set()
        for line in evidence_lines:
            lowered = str(line or "").lower()
            if required_tokens and not all(token in lowered for token in required_tokens):
                continue
            if preferred_tokens and not any(token in lowered for token in preferred_tokens):
                continue
            normalized = _normalize_match_key(line)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            selected.append(str(line).strip())
            if len(selected) >= max_items:
                break
        return selected

    @classmethod
    def _build_combined_release_overview_bullets(cls, user_prompt: str, tool_results: List[Dict[str, Any]]) -> List[str]:
        lowered = str(user_prompt or "").lower()
        evidence_lines = cls._collect_websearch_evidence_lines(tool_results)
        overview: List[str] = []
        asks_launch = any(token in lowered for token in ("launch", "veröffentlicht", "veroeffentlicht", "wann wurde"))
        asks_price = any(token in lowered for token in ("preis", "preise", "uvp", "straßenpreis", "strassenpreis"))
        asks_top = any(token in lowered for token in ("top 3", "top3", "beliebteste", "beliebtesten", "highlight", "highlights"))

        if asks_launch:
            launch_lines = cls._select_relevant_evidence_lines(
                evidence_lines,
                required_tokens=("switch",),
                preferred_tokens=("launch", "release", "veröff", "veroeff", "erschien", "erscheint"),
                max_items=1,
            )
            overview.append(
                f"- **Konsolen-Launch:** {launch_lines[0]}" if launch_lines else "- **Konsolen-Launch:** Im Material nicht eindeutig belegt."
            )

        if asks_price:
            price_lines = cls._select_relevant_evidence_lines(
                evidence_lines,
                required_tokens=(),
                preferred_tokens=("€", "euro", "uvp", "preis", "preise", "straßenpreis", "strassenpreis"),
                max_items=2,
            )
            if price_lines:
                overview.append(f"- **Preis/UVP:** {price_lines[0]}")
                if len(price_lines) > 1:
                    overview.append(f"- **Straßenpreis:** {price_lines[1]}")
            else:
                overview.append("- **Preis/UVP:** Im Material nicht eindeutig belegt.")

        if asks_top:
            ranking_lines = cls._select_relevant_evidence_lines(
                evidence_lines,
                required_tokens=(),
                preferred_tokens=("top", "beliebt", "popular", "ranking", "highlight", "verkauf", "vorbestell"),
                max_items=3,
            )
            if ranking_lines:
                for idx, line in enumerate(ranking_lines, start=1):
                    overview.append(f"- **Top {idx}:** {line}")
            else:
                overview.append("- **Top 3:** Im Material liegt kein eindeutig belastbares Ranking vor.")
        return overview

    @staticmethod
    def _is_game_release_websearch_prompt(user_prompt: str) -> bool:
        lowered = str(user_prompt or "").strip().lower()
        if not lowered:
            return False
        months = (
            "januar", "februar", "märz", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "dezember",
            "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december",
        )
        is_game_query = any(token in lowered for token in ("spiele", "games", "nintendo", "switch", "playstation", "xbox", "pc"))
        is_release_query = any(token in lowered for token in ("erscheinen", "release", "veröffentlich", "nächsten monat", "kommenden monat", "termin")) or any(month in lowered for month in months)
        return is_game_query and is_release_query

    @classmethod
    def _is_combined_game_release_websearch_prompt(cls, user_prompt: str) -> bool:
        lowered = str(user_prompt or "").strip().lower()
        if not cls._is_game_release_websearch_prompt(lowered):
            return False
        return any(
            token in lowered
            for token in (
                "preis",
                "preise",
                "uvp",
                "straßenpreis",
                "strassenpreis",
                "top 3",
                "top3",
                "beliebteste",
                "beliebtesten",
                "highlight",
                "highlights",
                "launch",
                "veröffentlicht",
                "veroeffentlicht",
                "wann wurde",
            )
        )
