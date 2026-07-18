"""YouTube/action turns must not be swallowed by Help how-to fast-path."""

from __future__ import annotations

from types import SimpleNamespace

from backend.services.chat_orchestrator import ChatOrchestrator
from backend.services.orchestrator.intent_engine import IntentEngine


YOUTUBE_PROMPT = (
    "Suche auf YouTube nach einem Video zu 'Python Tutorial für Anfänger'. "
    "Nutze den Video-Skill, keine allgemeine Websuche. Gib Titel und Kanal an."
)


def test_youtube_tutorial_prompt_is_video_not_how_to():
    intents = IntentEngine().detect_all_intents(YOUTUBE_PROMPT)
    assert intents.is_video_intent is True
    assert intents.is_how_to is False
    assert intents.primary_intent in {"video", "video_list"}


def test_resolve_help_intent_vetoes_video_action_turns():
    orch = ChatOrchestrator.__new__(ChatOrchestrator)
    intents = SimpleNamespace(
        is_model_query=False,
        is_capability_overview=False,
        is_how_to=True,
        is_navigation_query=False,
        is_video_intent=True,
        is_video_list_intent=True,
        is_video_understanding_intent=False,
        is_filesystem_intent=False,
        is_weather_intent=False,
        is_calendar_intent=False,
        is_calendar_creation=False,
        is_calendar_mutation=False,
        is_wikipedia_intent=False,
        is_news_intent=False,
        is_shopping_intent=False,
        is_local_business_intent=False,
        is_routing_geo_intent=False,
        is_session_search_intent=False,
    )
    assert orch._resolve_help_intent(intents) is None


def test_resolve_help_intent_keeps_pure_how_to():
    orch = ChatOrchestrator.__new__(ChatOrchestrator)
    intents = SimpleNamespace(
        is_model_query=False,
        is_capability_overview=False,
        is_how_to=True,
        is_navigation_query=False,
        is_video_intent=False,
        is_video_list_intent=False,
        is_video_understanding_intent=False,
        is_filesystem_intent=False,
        is_weather_intent=False,
        is_calendar_intent=False,
        is_calendar_creation=False,
        is_calendar_mutation=False,
        is_wikipedia_intent=False,
        is_news_intent=False,
        is_shopping_intent=False,
        is_local_business_intent=False,
        is_routing_geo_intent=False,
        is_session_search_intent=False,
    )
    assert orch._resolve_help_intent(intents) == "how_to"
