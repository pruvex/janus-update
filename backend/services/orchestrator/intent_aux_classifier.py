"""
Auxiliary action/subject classifier for intent engine phase M1.

This slice defines the contract, provider wrapper, regex fallback, and mapping
helpers. It is intentionally not wired into detect_all_intents() yet.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import threading
import time
from typing import Any, Awaitable, Callable, Mapping, Optional

from backend.data.schemas_intent import (
    ActionSubjectResult,
    IntentAction,
    IntentSubject,
    validate_action_subject_payload,
)
from backend.services.orchestrator.intent_config import (
    IntentAuxClassifierConfig,
    get_intent_aux_classifier_config,
    is_aux_classifier_enabled,
)

logger = logging.getLogger(__name__)

ProviderCallable = Callable[[str, Mapping[str, Any]], Awaitable[str]]

_RECALL_RE = re.compile(
    r"\b(?:was\s+(?:weißt|weisst)\s+du(?:\s+alles)?\s+(?:über|ueber)|"
    r"was\s+mag|was\s+m(?:ö|oe)gen|was\s+hasst|welche\s+(?:vorlieben|abneigungen)|"
    r"was\s+sind\s+.*(?:vorlieben|abneigungen)|"
    r"wer\s+ist|wie\s+hei(?:ß|ss)t)\b",
    re.IGNORECASE,
)
_PET_FACT_RE = re.compile(
    r"\b[\wäöüÄÖÜß-]{2,}s\s+(?:hund|katze|haustier)\s+[\wäöüÄÖÜß-]{2,}\s+ist\b",
    re.IGNORECASE,
)
_PET_KEYWORD_RE = re.compile(r"\b(?:hund|katze|haustier|podenco)\b", re.IGNORECASE)
_CONTACT_FACT_RE = re.compile(
    r"\b[A-ZÄÖÜ][\wäöüÄÖÜß-]{1,}\s+"
    r"(?:mag|liebt|hasst|bevorzugt|wohnt|lebt|hat|besitzt|verbringt\s+gerne|"
    r"verbringt\s+gern|spielt\s+gerne|spielt\s+gern|ist|kocht|sammelt|hoert|hört|"
    r"trinkt|schaut|fotografiert|joggt)\b",
    re.IGNORECASE,
)
_SELF_FACT_RE = re.compile(
    r"\b(?:ich\s+(?:habe|bin|mag|liebe|hasse|wohne|arbeite)|"
    r"mein(?:e)?\s+|mein\s+name\s+ist)\b",
    re.IGNORECASE,
)
_SELF_RECALL_RE = re.compile(
    r"\b(?:was\s+habe\s+ich|welches\s+habe\s+ich|wann\s+habe\s+ich|"
    r"wo\s+habe\s+ich|mein(?:e)?\s+letzt)\b",
    re.IGNORECASE,
)
_CALENDAR_MUTATE_RE = re.compile(
    r"\b(?:verschiebe|verschieb|lösche|loesche|entferne|storniere)\b.*\btermin\b",
    re.IGNORECASE,
)
_CALENDAR_CREATE_RE = re.compile(
    r"\b(?:neuen?\s+termin|termin\s+anlegen|termin\s+erstellen|"
    r"kalendereintrag|eintrag\s+anlegen)\b",
    re.IGNORECASE,
)
_SEARCH_RE = re.compile(
    r"\b(?:wetter|nachrichten|wikipedia|recherchiere|suche\s+nach|"
    r"was\s+sind\s+die\s+nachrichten|aktuell)\b",
    re.IGNORECASE,
)
_GREETING_RE = re.compile(r"^\s*(?:hallo|hi|hey|moin|guten\s+(?:tag|morgen|abend))\b", re.IGNORECASE)

AUX_CLASSIFIER_SYSTEM_PROMPT = """Klassifiziere die Nutzeräußerung für einen deutschen Personal Assistant.

Antworte NUR als JSON:
{"action":"...","subject":"...","confidence":0.0-1.0,"evidence":"..."}

action:
- recall: Nutzer fragt nach gespeichertem Wissen über Person/Tier/Sich
- tell_fact: Nutzer teilt neuen Fakt mit (keine Frage)
- mutate: bestehenden Kalendertermin ändern/verschieben/löschen
- create: neuen Termin anlegen
- search: externe/aktuelle Infos (Wetter, News, Wikipedia, Web)
- general: Smalltalk, Meinung, Identitätsfrage an Assistenten
- clarify: echte Mehrdeutigkeit, keine sichere Zuordnung

subject:
- self, contact, pet, calendar, none

Regeln:
- "Was weißt du über X" → recall + contact
- "Olis Hund Tasso ist ein Podenco" → tell_fact + pet (NICHT contact)
- "Chris mag Pizza" → tell_fact + contact
- Eigennamen allein ≠ search
"""


def _extract_provider_text(response: Any) -> str:
    """Normalize common llm_gateway response shapes to plain text."""
    if not isinstance(response, Mapping):
        return ""

    for key in ("text", "content", "result"):
        value = response.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    raw = response.get("raw_assistant_response")
    if isinstance(raw, Mapping):
        content = raw.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

    return ""


async def _default_provider_callable(user_text: str, context: Mapping[str, Any]) -> str:
    """Bounded default provider wrapper for the auxiliary classifier."""
    from backend.services import llm_gateway

    provider = str(context.get("provider") or "openai")
    model_id = str(context.get("model_id") or "gpt-5.4-nano")
    system_prompt = str(context.get("system_prompt") or AUX_CLASSIFIER_SYSTEM_PROMPT)
    max_output_tokens = int(context.get("max_output_tokens") or 20)

    response = await llm_gateway.call_llm(
        provider=provider,
        model_id=model_id,
        api_key="",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": str(user_text or "")},
        ],
        max_tokens=max_output_tokens,
        temperature=0.0,
        force_no_tools=True,
    )
    return _extract_provider_text(response)


class AuxClassifierCircuitBreaker:
    """Fail closed after repeated provider failures."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 120) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._state = "CLOSED"

    def can_execute(self) -> bool:
        if self._state == "CLOSED":
            return True
        if self._state == "OPEN":
            if time.time() - self._last_failure_time > self._recovery_timeout:
                self._state = "HALF_OPEN"
                return True
            return False
        return True

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = "CLOSED"

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._failure_threshold:
            self._state = "OPEN"

    def get_state(self) -> dict[str, Any]:
        return {
            "state": self._state,
            "failure_count": self._failure_count,
            "threshold": self._failure_threshold,
            "recovery_timeout": self._recovery_timeout,
        }


def classify_with_regex_fallback(user_text: str) -> ActionSubjectResult:
    """Deterministic regex fallback used when aux is disabled or provider fails."""
    text = (user_text or "").strip()
    lowered = text.lower()

    if not text:
        return ActionSubjectResult(
            action="clarify",
            subject="none",
            confidence=0.2,
            evidence="empty input",
            source="regex_fallback",
        )

    if _GREETING_RE.search(text):
        return ActionSubjectResult(
            action="general",
            subject="none",
            confidence=0.75,
            evidence="greeting",
            source="regex_fallback",
        )

    if _CALENDAR_MUTATE_RE.search(text):
        return ActionSubjectResult(
            action="mutate",
            subject="calendar",
            confidence=0.78,
            evidence="calendar mutation",
            source="regex_fallback",
        )

    if _CALENDAR_CREATE_RE.search(text):
        return ActionSubjectResult(
            action="create",
            subject="calendar",
            confidence=0.78,
            evidence="calendar creation",
            source="regex_fallback",
        )

    if _SEARCH_RE.search(text):
        return ActionSubjectResult(
            action="search",
            subject="none",
            confidence=0.72,
            evidence="external search",
            source="regex_fallback",
        )

    if _SELF_RECALL_RE.search(text) or (
        _RECALL_RE.search(text) and any(token in lowered for token in ("mein", "meine", "ich"))
    ):
        return ActionSubjectResult(
            action="recall",
            subject="self",
            confidence=0.7,
            evidence="self recall",
            source="regex_fallback",
        )

    if _RECALL_RE.search(text):
        subject: IntentSubject = "pet" if _PET_KEYWORD_RE.search(text) else "contact"
        return ActionSubjectResult(
            action="recall",
            subject=subject,
            confidence=0.74,
            evidence="contact recall",
            source="regex_fallback",
        )

    if _PET_FACT_RE.search(text) or (
        _PET_KEYWORD_RE.search(text) and not text.endswith("?")
    ):
        return ActionSubjectResult(
            action="tell_fact",
            subject="pet",
            confidence=0.76,
            evidence="pet fact",
            source="regex_fallback",
        )

    if _SELF_FACT_RE.search(text):
        return ActionSubjectResult(
            action="tell_fact",
            subject="self",
            confidence=0.74,
            evidence="self fact",
            source="regex_fallback",
        )

    if _CONTACT_FACT_RE.search(text):
        return ActionSubjectResult(
            action="tell_fact",
            subject="contact",
            confidence=0.73,
            evidence="contact fact",
            source="regex_fallback",
        )

    if text.endswith("?"):
        return ActionSubjectResult(
            action="clarify",
            subject="none",
            confidence=0.45,
            evidence="ambiguous question",
            source="regex_fallback",
        )

    return ActionSubjectResult(
        action="general",
        subject="none",
        confidence=0.55,
        evidence="default general",
        source="regex_fallback",
    )


def map_action_subject_to_legacy_flags(result: ActionSubjectResult) -> dict[str, bool]:
    """Compatibility mapping from classifier output to legacy intent booleans."""
    action = result.action
    subject = result.subject

    mapped = {
        "is_personal_recall": action == "recall",
        "is_fact_telling": action == "tell_fact",
        "is_calendar_mutation": action == "mutate",
        "is_calendar_creation": action == "create",
        "is_self_referential": subject == "self",
        "is_ambiguous": action == "clarify" or result.confidence < 0.55,
    }
    return mapped


class AuxiliaryIntentClassifier:
    """Bounded auxiliary classifier with provider wrapper and regex fallback."""

    def __init__(
        self,
        *,
        config: Optional[IntentAuxClassifierConfig] = None,
        provider_callable: Optional[ProviderCallable] = None,
        circuit_breaker: Optional[AuxClassifierCircuitBreaker] = None,
    ) -> None:
        self._config = config or get_intent_aux_classifier_config()
        self._provider_callable = provider_callable or _default_provider_callable
        self._circuit_breaker = circuit_breaker or AuxClassifierCircuitBreaker(
            failure_threshold=self._config.circuit_failure_threshold,
            recovery_timeout=self._config.circuit_recovery_timeout_seconds,
        )

    async def classify(
        self,
        user_text: str,
        *,
        calendar_snapshot: Optional[Mapping[str, Any]] = None,
    ) -> ActionSubjectResult:
        if not self._config.enabled:
            return classify_with_regex_fallback(user_text)

        if not self._circuit_breaker.can_execute():
            logger.info("[INTENT AUX] circuit open, using regex fallback")
            return classify_with_regex_fallback(user_text)

        try:
            provider_payload = await self._provider_callable(
                user_text,
                {
                    "calendar_snapshot": dict(calendar_snapshot or {}),
                    "provider": self._config.provider,
                    "model_id": self._config.model_id,
                    "system_prompt": AUX_CLASSIFIER_SYSTEM_PROMPT,
                    "max_output_tokens": self._config.max_output_tokens,
                },
            )
            validated = validate_action_subject_payload(provider_payload)
            if validated is None:
                self._circuit_breaker.record_failure()
                return classify_with_regex_fallback(user_text)

            self._circuit_breaker.record_success()
            return validated.model_copy(update={"source": "aux_llm"})
        except Exception as exc:
            logger.warning("[INTENT AUX] provider failure, fail closed to regex: %s", exc)
            self._circuit_breaker.record_failure()
            return classify_with_regex_fallback(user_text)


_default_classifier = AuxiliaryIntentClassifier()


def _run_coroutine_sync(coro: Awaitable[ActionSubjectResult]) -> ActionSubjectResult:
    """Bridge async classifier execution into sync intent-engine call sites."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    outcome: dict[str, Any] = {}

    def _runner() -> None:
        try:
            outcome["result"] = asyncio.run(coro)
        except Exception as exc:  # pragma: no cover - defensive bridge
            outcome["error"] = exc

    thread = threading.Thread(target=_runner, name="intent-aux-classifier-sync", daemon=True)
    thread.start()
    thread.join()

    if "error" in outcome:
        raise outcome["error"]
    return outcome["result"]


async def classify(
    user_text: str,
    *,
    calendar_snapshot: Optional[Mapping[str, Any]] = None,
    provider_callable: Optional[ProviderCallable] = None,
    config: Optional[IntentAuxClassifierConfig] = None,
) -> ActionSubjectResult:
    """Module-level classify entry used by tests and future integration."""
    if provider_callable is not None or config is not None:
        classifier = AuxiliaryIntentClassifier(
            config=config,
            provider_callable=provider_callable,
        )
        return await classifier.classify(user_text, calendar_snapshot=calendar_snapshot)
    return await _default_classifier.classify(user_text, calendar_snapshot=calendar_snapshot)


def classify_sync(
    user_text: str,
    *,
    calendar_snapshot: Optional[Mapping[str, Any]] = None,
    provider_callable: Optional[ProviderCallable] = None,
    config: Optional[IntentAuxClassifierConfig] = None,
) -> ActionSubjectResult:
    """Synchronous bridge used by the current sync intent-engine surface."""
    return _run_coroutine_sync(
        classify(
            user_text,
            calendar_snapshot=calendar_snapshot,
            provider_callable=provider_callable,
            config=config,
        )
    )


def parse_provider_json(raw_text: str) -> Optional[ActionSubjectResult]:
    """Parse raw provider text, including fenced JSON blocks."""
    text = (raw_text or "").strip()
    if not text:
        return None

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return validate_action_subject_payload(payload)


__all__ = [
    "AUX_CLASSIFIER_SYSTEM_PROMPT",
    "AuxClassifierCircuitBreaker",
    "AuxiliaryIntentClassifier",
    "classify",
    "classify_sync",
    "classify_with_regex_fallback",
    "is_aux_classifier_enabled",
    "map_action_subject_to_legacy_flags",
    "parse_provider_json",
]
