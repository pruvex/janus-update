"""
Context Compressor Service - Phase 3: Smart Compression Proposal

Dieser Service implementiert die Regel-Engine zur Auswahl von Kompressions-Kandidaten
und die Erzeugung von Summary-Vorschlägen.

Key Design Principles:
- #DeterministicSkillTesting: Candidate Selection ist 100% deterministisch
- #ExclusionRules: System-Prompts, Tool-Schemas, Developer-Messages, letzte 5 Nachrichten
- #SafetyFirst: Keine Datenbank-Mutation in Phase 3 (nur Read/Propose)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from backend.services.context.context_counter import estimate_messages_tokens

logger = logging.getLogger("janus_backend")

# Konstanten für Exclusion-Rules
EXCLUDED_ROLES = {"system", "developer"}
RECENT_MESSAGE_THRESHOLD = 5  # Letzte 5 Nachrichten schützen


@dataclass(frozen=True)
class CompressionCandidate:
    """Ein identifizierter Kandidat für die Kompression."""

    index: int  # Original-Index in der Message-Liste
    role: str
    content: str
    estimated_tokens: int
    is_paired: bool = False  # Teil eines User/Assistant Paars?


@dataclass(frozen=True)
class CompressionProposal:
    """Das Ergebnis einer Proposal-Generierung."""

    candidates: list[CompressionCandidate]
    summary_preview: str
    estimated_tokens_current: int
    estimated_tokens_saved: int
    savings_percent: float
    protected_count: int  # Wie viele Nachrichten wurden geschützt
    compression_ratio: float  # Wie stark wurde komprimiert (Ziel: ~80%)


class CandidateSelector:
    """
    #DeterministicSkillTesting: Regel-basierte Auswahl von Kompressions-Kandidaten.

    Exclusion-Rules (in Prioritätsreihenfolge):
    1. KEINE System-Prompts (role == "system")
    2. KEINE Developer-Messages (role == "developer")
    3. KEINE Tool-Schemas (content enthält function_schema oder tool_definitions)
    4. KEINE letzten 5 Nachrichten (aktiver Kontext bleibt erhalten)
    5. FOKUS: Älteste User/Assistant Paare zuerst
    """

    # Marker für Tool-Schema Content
    TOOL_SCHEMA_MARKERS = [
        "function_schema",
        "tool_definitions",
        "tools:",
        '```json\n{',
        "available functions",
    ]

    def __init__(self):
        self.excluded_count = 0
        self.protected_count = 0

    def _is_tool_schema(self, content: str) -> bool:
        """Erkennt Tool-Schema Messages anhand von Markern."""
        content_lower = content.lower()
        return any(marker in content_lower for marker in self.TOOL_SCHEMA_MARKERS)

    def _is_excluded_role(self, role: str) -> bool:
        """Prüft ob die Rolle exkludiert werden soll."""
        return role.lower() in EXCLUDED_ROLES

    def select_candidates(
        self,
        messages: list[dict[str, Any]],
        target_token_reduction: int | None = None,
        is_overflow: bool = False,
    ) -> list[CompressionCandidate]:
        """
        Selektiert Kompressions-Kandidaten nach Diamond-Regeln.

        Args:
            messages: Liste von Messages (dict mit role, content)
            target_token_reduction: Optionales Ziel für Token-Einsparung
            is_overflow: Wenn True, nur die letzte Nachricht schützen (Notfallmodus)

        Returns:
            Liste von CompressionCandidate Objekten
        """
        if not messages:
            return []

        candidates: list[CompressionCandidate] = []
        total_messages = len(messages)

        # 💎 CU-2 Notfallmodus: Bei Overflow nur letzte Nachricht schützen
        effective_threshold = 1 if is_overflow else RECENT_MESSAGE_THRESHOLD

        # Schritt 1: Identifiziere geschützte Indizes
        protected_indices = set(range(max(0, total_messages - effective_threshold), total_messages))

        # Schritt 2: Iteriere von alt nach neu, identifiziere Kandidaten
        for i, msg in enumerate(messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Exclusion-Rule 1 & 2: System/Developer Messages
            if self._is_excluded_role(role):
                self.excluded_count += 1
                logger.debug("[COMPRESSOR] Excluded message %d: role=%s", i, role)
                continue

            # Exclusion-Rule 3: Tool Schemas
            if self._is_tool_schema(content):
                self.excluded_count += 1
                logger.debug("[COMPRESSOR] Excluded message %d: tool schema detected", i)
                continue

            # Exclusion-Rule 4: Letzte 5 Nachrichten
            if i in protected_indices:
                self.protected_count += 1
                logger.debug("[COMPRESSOR] Protected message %d: recent context", i)
                continue

            # Dies ist ein Kandidat
            est_tokens = estimate_messages_tokens([msg])
            candidates.append(
                CompressionCandidate(
                    index=i,
                    role=role,
                    content=content,
                    estimated_tokens=est_tokens,
                )
            )

        # Schritt 3: Paare identifizieren (User/Assistant Sequenzen)
        candidates = self._identify_pairs(candidates, messages)

        logger.info(
            "[COMPRESSOR] Selection complete: %d candidates, %d excluded, %d protected, %d total",
            len(candidates),
            self.excluded_count,
            self.protected_count,
            total_messages,
        )

        return candidates

    def _identify_pairs(
        self,
        candidates: list[CompressionCandidate],
        all_messages: list[dict[str, Any]],
    ) -> list[CompressionCandidate]:
        """
        Markiert Kandidaten als "gepaart" wenn sie Teil eines User/Assistant-Paars sind.
        Dies hilft bei der späteren Summary-Erzeugung.
        """
        candidate_indices = {c.index for c in candidates}
        result: list[CompressionCandidate] = []

        for cand in candidates:
            # Prüfe ob nächste Nachricht auch ein Kandidat ist und Assistant-Role hat
            next_idx = cand.index + 1
            is_paired = (
                cand.role == "user"
                and next_idx < len(all_messages)
                and next_idx in candidate_indices
                and all_messages[next_idx].get("role") == "assistant"
            )

            result.append(
                CompressionCandidate(
                    index=cand.index,
                    role=cand.role,
                    content=cand.content,
                    estimated_tokens=cand.estimated_tokens,
                    is_paired=is_paired,
                )
            )

        return result


class ProposalGenerator:
    """
    Erzeugt Summary-Vorschläge für identifizierte Kandidaten.
    Nutzt ein Speed-Tier Modell für schnelle Zusammenfassungen.
    """

    # Prompt-Template für Summary-Generierung
    SUMMARY_PROMPT = """Fasse die folgende Konversation prägnant zusammen.

 WICHTIG - Bewahre diese Elemente:
- Alle getroffenen Entscheidungen und Konklusionen
- Alle offenen TODOs oder Action-Items
- Alle wichtigen Fakten, Namen, Daten
- Alle Datei-Referenzen oder Code-Änderungen
- Tool-Calls und deren Ergebnisse

 NICHT bewahren:
- Floskeln wie "Basierend auf..." oder "Ich verstehe..."
- Wiederholungen
- Meta-Kommentare

Format: Bullet-Points für Fakten, nummerierte Liste für TODOs.

Nachrichten zum Zusammenfassen:
{messages}

Zusammenfassung:"""

    def __init__(self):
        self.selector = CandidateSelector()

    async def generate_proposal(
        self,
        messages: list[dict[str, Any]],
        chat_id: str | int | None = None,
        model: str | None = None,
    ) -> CompressionProposal | None:
        """
        Generiert einen Kompressions-Vorschlag für die gegebenen Messages.

        Args:
            messages: Vollständige Message-History
            chat_id: Optional für Logging/Telemetrie
            model: Ziel-Modell für Context-State-Berechnung (Overflow-Detection)

        Returns:
            CompressionProposal oder None wenn keine Kandidaten
        """
        # 💎 CU-2: Context-State berechnen für Overflow-Detection
        from backend.services.context.context_state import calculate_context_state

        context_state = calculate_context_state(
            chat_id=chat_id,
            provider=None,
            model=model,
            messages=messages,
        )

        is_overflow = context_state.status == "overflow" or context_state.usage_percent > 100.0

        # Dynamische Min-Message-Prüfung: Overflow=2, Normal=10
        min_required = 2 if is_overflow else 10
        if len(messages) < min_required:
            logger.info("[COMPRESSOR] Skipping: only %d messages, minimum %d required (overflow=%s)",
                        len(messages), min_required, is_overflow)
            return None

        # Schritt 1: Kandidaten selektieren (mit Overflow-Notfallmodus)
        candidates = self.selector.select_candidates(messages, is_overflow=is_overflow)
        if not candidates:
            logger.info("[COMPRESSOR] No candidates found after exclusion rules")
            return None

        # Schritt 2: Berechne Token-Ersparnis
        current_tokens = estimate_messages_tokens(messages)
        candidate_tokens = sum(c.estimated_tokens for c in candidates)

        # Schritt 3: Summary generieren (nur für Kandidaten)
        candidate_content = self._format_candidate_messages(candidates, messages)
        summary = await self._generate_summary(candidate_content, model)

        # Schritt 4: Schätzung der Einsparung
        # Summary ist typischerweise ~20% der Original-Tokens
        estimated_summary_tokens = max(
            int(candidate_tokens * 0.25),  # 25% der Kandidaten-Tokens
            len(summary.split()) * 1.3,  # Grobe Schätzung
        )
        tokens_saved = candidate_tokens - estimated_summary_tokens
        savings_percent = (tokens_saved / current_tokens * 100) if current_tokens > 0 else 0

        logger.info(
            "[COMPRESSOR] Proposal generated for chat=%s: %d candidates, %d tokens saved (%.1f%%)",
            chat_id,
            len(candidates),
            tokens_saved,
            savings_percent,
        )

        return CompressionProposal(
            candidates=candidates,
            summary_preview=summary,
            estimated_tokens_current=current_tokens,
            estimated_tokens_saved=tokens_saved,
            savings_percent=savings_percent,
            protected_count=self.selector.protected_count,
            compression_ratio=min(0.8, tokens_saved / candidate_tokens) if candidate_tokens > 0 else 0,
        )

    def _format_candidate_messages(
        self,
        candidates: list[CompressionCandidate],
        all_messages: list[dict[str, Any]],
    ) -> str:
        """Formatiert Kandidaten-Messages für den LLM Prompt."""
        lines: list[str] = []
        for i, cand in enumerate(candidates):
            # Füge auch die Assistant-Antwort hinzu wenn gepaart
            if cand.is_paired and cand.index + 1 < len(all_messages):
                assistant_msg = all_messages[cand.index + 1]
                lines.append(f"[{i+1}] User: {cand.content[:200]}...")
                lines.append(f"    Assistant: {assistant_msg.get('content', '')[:200]}...")
            else:
                lines.append(f"[{i+1}] {cand.role.capitalize()}: {cand.content[:300]}...")
        return "\n".join(lines)

    # 💎 CU-3: Speed-Tier Modelle pro Provider (günstigste Optionen)
    SPEED_TIER_MODELS = {
        "gemini": "gemini-3-flash-preview",  # NICHT gemini-2.5-flash-preview (existiert nicht!)
        "openai": "gpt-5.4-nano",  # Günstigstes OpenAI Modell
        "ollama": None,  # Wird dynamisch aus target_model bestimmt
    }

    async def _generate_summary(self, candidate_content: str, model: str | None = None) -> str:
        """
        Ruft das Speed-Tier Modell für die Zusammenfassung auf.

        💎 PROVIDER-AGNOSTIK: Nutzt dynamisch das günstigste Speed-Tier Modell des Providers
        des aktuellen Nutzer-Modells (target_model). Bei lokalen Modellen (Ollama) wird der
        letzte aktive Cloud-Provider aus der Config verwendet.
        """
        try:
            from backend.services.llm_gateway import call_llm
            from backend.utils.config_loader import load_model_catalog, load_config_data

            prompt = self.SUMMARY_PROMPT.format(messages=candidate_content)

            # 💎 PROVIDER-AGNOSTIK: Bestimme Provider und Speed-Tier Modell dynamisch
            provider = None
            model_id = None

            if model:
                # Prüfe Model-Katalog für Provider-Zuordnung
                try:
                    catalog = load_model_catalog()
                    if model in catalog:
                        model_info = catalog[model]
                        detected_provider = model_info.get("provider", "").lower()

                        if detected_provider == "openai":
                            provider = "openai"
                            model_id = self.SPEED_TIER_MODELS["openai"]
                            logger.debug("[COMPRESSOR] Using OpenAI Speed-Tier: %s", model_id)
                        elif detected_provider == "ollama":
                            # 💎 PROVIDER-AGNOSTIK: Für Ollama nutze den letzten Cloud-Provider aus Config
                            config = load_config_data()
                            last_cloud_provider = config.get("last_used_provider", "openai").lower()
                            
                            # Verwende nur Cloud-Provider (OpenAI oder Gemini), nicht Ollama
                            if last_cloud_provider in ["openai", "gemini"]:
                                provider = last_cloud_provider
                                model_id = self.SPEED_TIER_MODELS.get(last_cloud_provider)
                                logger.debug("[COMPRESSOR] Ollama detected, using last cloud provider: %s with %s", provider, model_id)
                            else:
                                # Fallback auf OpenAI wenn Config keinen gültigen Cloud-Provider hat
                                provider = "openai"
                                model_id = self.SPEED_TIER_MODELS["openai"]
                                logger.warning("[COMPRESSOR] Invalid last_used_provider '%s', falling back to OpenAI", last_cloud_provider)
                        elif detected_provider == "gemini":
                            provider = "gemini"
                            model_id = self.SPEED_TIER_MODELS["gemini"]
                            logger.debug("[COMPRESSOR] Using Gemini Speed-Tier: %s", model_id)
                        else:
                            # Unbekannter Provider -> Nutze last_used_provider aus Config
                            config = load_config_data()
                            last_provider = config.get("last_used_provider", "openai").lower()
                            provider = last_provider if last_provider in self.SPEED_TIER_MODELS else "openai"
                            model_id = self.SPEED_TIER_MODELS.get(provider, self.SPEED_TIER_MODELS["openai"])
                            logger.warning("[COMPRESSOR] Unknown provider '%s', using last_used_provider: %s", detected_provider, provider)
                    else:
                        # Modell nicht im Katalog -> Nutze last_used_provider aus Config (Provider-Agnostik)
                        config = load_config_data()
                        last_provider = config.get("last_used_provider", "openai").lower()
                        provider = last_provider if last_provider in self.SPEED_TIER_MODELS else "openai"
                        model_id = self.SPEED_TIER_MODELS.get(provider, self.SPEED_TIER_MODELS["openai"])
                        logger.warning("[COMPRESSOR] Model %s not in catalog, using last_used_provider: %s", model, provider)
                except Exception as catalog_err:
                    logger.warning("[COMPRESSOR] Could not lookup model catalog: %s", catalog_err)
                    # Fallback auf last_used_provider aus Config
                    config = load_config_data()
                    last_provider = config.get("last_used_provider", "openai").lower()
                    provider = last_provider if last_provider in self.SPEED_TIER_MODELS else "openai"
                    model_id = self.SPEED_TIER_MODELS.get(provider, self.SPEED_TIER_MODELS["openai"])

            # Fallback falls kein Provider bestimmt wurde
            if not provider or not model_id:
                config = load_config_data()
                last_provider = config.get("last_used_provider", "openai").lower()
                provider = last_provider if last_provider in self.SPEED_TIER_MODELS else "openai"
                model_id = self.SPEED_TIER_MODELS.get(provider, self.SPEED_TIER_MODELS["openai"])
                logger.warning("[COMPRESSOR] No provider determined, using last_used_provider fallback: %s", provider)

            logger.info("[COMPRESSOR] Generating summary with provider=%s model=%s", provider, model_id)

            result = await call_llm(
                provider=provider,
                model=model_id,
                api_key="",  # 💎 CU-2: #SelfHealingIdentity - Wird frisch aus keyring geladen
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,  # Niedrig für konsistente Fakten-Extraktion
            )

            # 💎 CU-2: Prüfe auf API_KEY_EXPIRED Fehler
            if isinstance(result, dict) and result.get("error_code") == "API_KEY_EXPIRED":
                logger.error("[COMPRESSOR] API Key expired for provider=%s", provider)
                return self._fallback_summary(candidate_content)

            # Extrahiere Content aus Response
            summary = result.get("content", "") if isinstance(result, dict) else str(result)

            return summary.strip() if summary else self._fallback_summary(candidate_content)

        except Exception as e:
            logger.error("[COMPRESSOR] Summary generation failed: %s", e, exc_info=True)
            return self._fallback_summary(candidate_content)

    def _fallback_summary(self, candidate_content: str) -> str:
        """
        Fallback wenn LLM nicht verfügbar: Extraktive Summary.
        Nimmt erste Zeile jeder Message als Key Point.
        """
        lines: list[str] = []
        for line in candidate_content.split("\n"):
            if line.strip().startswith("["):
                # Extrahiere erste Sätze bis zu einem Limit
                content = line.split(":", 1)[1].strip() if ":" in line else line
                first_sentence = content.split(".")[0][:100]
                if first_sentence:
                    lines.append(f"• {first_sentence}...")
        return "\n".join(lines[:10])  # Max 10 Bullet Points


# Singleton-Instanz für einfachen Zugriff
_proposal_generator: ProposalGenerator | None = None


def get_proposal_generator() -> ProposalGenerator:
    """Gibt die Singleton-Instanz des ProposalGenerators zurück."""
    global _proposal_generator
    if _proposal_generator is None:
        _proposal_generator = ProposalGenerator()
    return _proposal_generator


async def propose_compression(
    messages: list[dict[str, Any]],
    chat_id: str | int | None = None,
    model: str | None = None,
) -> CompressionProposal | None:
    """
    Öffentliche API für Kompressions-Vorschläge.

    Args:
        messages: Die zu komprimierenden Messages
        chat_id: Optional für Logging/Telemetrie
        model: Ziel-Modell für Context-State-Berechnung (Overflow-Detection)

    Returns:
        CompressionProposal oder None
    """
    generator = get_proposal_generator()
    return await generator.generate_proposal(messages, chat_id, model)
