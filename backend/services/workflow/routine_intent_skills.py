"""Registry-backed skill-signature inference for routine semantic reuse."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from backend.services.orchestrator.intent_engine import IntentEngine

# Ordered probes: first match per skill_id wins; each skill at most once.
RoutineSkillProbe = tuple[str, Callable[["IntentEngine", str], bool]]

_ROUTINE_WEBSEARCH_RE = re.compile(
    r"\b(?:"
    r"recherchier(?:e|en)?|"
    r"suche(?:\s+im)?\s+(?:web|internet|online)|"
    r"im\s+internet|"
    r"online\s+suchen|"
    r"aktuelle(?:n|s)?\s+(?:infos?|informationen|nachrichten)|"
    r"was\s+kostet|"
    r"preis(?:vergleich)?|"
    r"marktdaten|"
    r"kurs(?:entwicklung)?"
    r")\b",
    re.IGNORECASE,
)


def routine_skill_probes() -> tuple[RoutineSkillProbe, ...]:
    return (
        ("calendar.list_events", _probe_calendar_list_events),
        ("system.weather", _probe_weather),
        ("system.routing", _probe_routing),
        ("system.wikipedia_summary", _probe_wikipedia),
        ("system.rss_news", _probe_rss_news),
        ("system.websearch", _probe_websearch),
        ("system.price_comparison", _probe_price_comparison),
        ("system.local_business", _probe_local_business),
        ("video.search", _probe_video_search),
    )


def detect_routine_request_skills(engine: "IntentEngine", user_text: str) -> frozenset[str]:
    text = str(user_text or "").strip()
    if not text or _is_routine_skill_inference_blocked(engine, text):
        return frozenset()

    skills: set[str] = set()
    for skill_id, probe in routine_skill_probes():
        if probe(engine, text):
            skills.add(skill_id)
    return frozenset(skills)


def _is_routine_skill_inference_blocked(engine: "IntentEngine", user_text: str) -> bool:
    if engine.detect_filesystem_intent(user_text):
        return True
    if engine.is_policy_consent_choice(str(user_text or "").strip().lower()):
        return True
    if engine.detect_personal_recall(user_text):
        # Possessives like "meine Termine" are not contact-recall turns.
        tool_backed = any(
            probe(engine, user_text)
            for skill_id, probe in routine_skill_probes()
            if skill_id != "calendar.list_events"
        ) or engine._detect_routine_calendar_signal(user_text)
        if tool_backed and (
            engine._detect_routine_calendar_signal(user_text)
            or engine._detect_routine_weather_signal(user_text)
            or engine.detect_routing_geo_intent(user_text)
            or engine.detect_wikipedia_intent(user_text)
            or engine.detect_news_intent(user_text)
        ):
            return False
        return True
    return False


def _probe_calendar_list_events(engine: "IntentEngine", user_text: str) -> bool:
    if not engine._detect_routine_calendar_signal(user_text):
        return False
    if engine.detect_calendar_mutation_intent(user_text):
        return False
    if engine.detect_calendar_creation_intent(user_text):
        return False
    return True


def _probe_weather(engine: "IntentEngine", user_text: str) -> bool:
    return engine._detect_routine_weather_signal(user_text)


def _probe_routing(engine: "IntentEngine", user_text: str) -> bool:
    return engine.detect_routing_geo_intent(user_text)


def _probe_wikipedia(engine: "IntentEngine", user_text: str) -> bool:
    return engine.detect_wikipedia_intent(user_text)


def _probe_rss_news(engine: "IntentEngine", user_text: str) -> bool:
    return engine.detect_news_intent(user_text)


def _probe_websearch(engine: "IntentEngine", user_text: str) -> bool:
    if engine.detect_news_intent(user_text) or engine.detect_shopping_intent(user_text):
        return False
    if engine.detect_wikipedia_intent(user_text):
        return False
    from backend.services.orchestrator.intent_engine import _fold_de_ascii, _normalize_text

    text_norm = _normalize_text(_fold_de_ascii(user_text))
    return bool(_ROUTINE_WEBSEARCH_RE.search(text_norm))


def _probe_price_comparison(engine: "IntentEngine", user_text: str) -> bool:
    return engine.detect_shopping_intent(user_text)


def _probe_local_business(engine: "IntentEngine", user_text: str) -> bool:
    return engine.detect_local_business_intent(user_text)


def _probe_video_search(engine: "IntentEngine", user_text: str) -> bool:
    return bool(
        engine.detect_video_intent(user_text)
        or engine.detect_named_channel_video_intent(user_text)
        or engine.detect_video_list_intent(user_text)
    )
