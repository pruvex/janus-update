from datetime import datetime
from unittest.mock import patch

from backend.services.tool_argument_sanitizer import sanitize_tool_arguments


def test_sanitize_tool_arguments_restores_local_business_query_and_location_for_ollama():
    result = sanitize_tool_arguments(
        "system.local_business",
        {
            "query": "highly rated italian restaurants",
            "location": "Berlin Prenzlauer Berg",
            "limit": 4,
        },
        provider="ollama",
        original_user_text="Finde mir exakt 4 gute italienische Restaurants in Berlin Prenzlauer Berg.",
    )

    assert result["query"] == "italienische Restaurants"
    assert result["location"] == "Berlin Prenzlauer Berg"
    assert result["limit"] == 4


def test_sanitize_tool_arguments_leaves_non_ollama_arguments_unchanged():
    args = {
        "query": "highly rated italian restaurants",
        "location": "Berlin Prenzlauer Berg",
        "limit": 4,
    }

    result = sanitize_tool_arguments(
        "system.local_business",
        args,
        provider="openai",
        original_user_text="Finde mir exakt 4 gute italienische Restaurants in Berlin Prenzlauer Berg.",
    )

    assert result == args


def test_sanitize_tool_arguments_rewrites_stale_websearch_month_from_relative_user_prompt():
    with patch("backend.services.tool_argument_sanitizer.datetime") as datetime_mock:
        datetime_mock.utcnow.return_value = datetime(2026, 3, 18, 12, 0, 0)
        result = sanitize_tool_arguments(
            "system.websearch",
            {
                "query": "Nintendo Switch 2 Spiele Dezember 2025 Deutschland Release",
                "provider": "openai",
            },
            provider="openai",
            original_user_text="Welche Switch 2 Spiele erscheinen nächsten Monat in Deutschland?",
        )

    assert result["query"] == "Nintendo Switch 2 upcoming games release April 2026 Deutschland"


def test_sanitize_tool_arguments_appends_resolved_month_for_relative_websearch_query_without_date():
    with patch("backend.services.tool_argument_sanitizer.datetime") as datetime_mock:
        datetime_mock.utcnow.return_value = datetime(2026, 3, 18, 12, 0, 0)
        result = sanitize_tool_arguments(
            "system.websearch",
            {
                "query": "Nintendo Switch 2 kommende Spiele Deutschland Release",
                "provider": "openai",
            },
            provider="openai",
            original_user_text="Welche Switch 2 Spiele erscheinen nächsten Monat in Deutschland?",
        )

    assert result["query"] == "Nintendo Switch 2 upcoming games release April 2026 Deutschland"


def test_sanitize_tool_arguments_preserves_price_and_top3_for_combined_switch_2_release_query():
    with patch("backend.services.tool_argument_sanitizer.datetime") as datetime_mock:
        datetime_mock.utcnow.return_value = datetime(2026, 3, 18, 12, 0, 0)
        result = sanitize_tool_arguments(
            "system.websearch",
            {
                "query": "Nintendo Switch 2 kommende Spiele Release Deutschland",
                "provider": "openai",
            },
            provider="openai",
            original_user_text="Welche Switch 2 Spiele erscheinen nächsten Monat in Deutschland, was ist die UVP und was sind die Top 3 Titel?",
        )

    assert result["query"] == "Nintendo Switch 2 upcoming games release April 2026 Deutschland Preis UVP Top 3 Highlights beliebteste Spiele"


def test_sanitize_tool_arguments_restores_top3_marker_from_user_text_when_missing_in_query():
    with patch("backend.services.tool_argument_sanitizer.datetime") as datetime_mock:
        datetime_mock.utcnow.return_value = datetime(2026, 3, 18, 12, 0, 0)
        result = sanitize_tool_arguments(
            "system.websearch",
            {
                "query": "Nintendo Switch 2 upcoming games release April 2026 Deutschland",
                "provider": "openai",
            },
            provider="openai",
            original_user_text="Welche Switch 2 Spiele erscheinen nächsten Monat in Deutschland und was sind die Top 3 Highlights?",
        )

    assert "Top 3" in result["query"]
    assert "Highlights" in result["query"]


def test_sanitize_tool_arguments_preserves_realistic_live_prompt_intents_for_switch_2_release_query():
    with patch("backend.services.tool_argument_sanitizer.datetime") as datetime_mock:
        datetime_mock.utcnow.return_value = datetime(2026, 3, 18, 12, 0, 0)
        result = sanitize_tool_arguments(
            "system.websearch",
            {
                "query": "Nintendo Switch 2 upcoming games release April 2026 Deutschland Preis UVP",
                "provider": "openai",
            },
            provider="openai",
            original_user_text="wann wurde die switch 2 in deutschland veröffentloicht? was sit die uvp und was die aktuellen strassenpreise? welches sind die 3 beliebtesten spiele auf der switch 2? mach mit eine liste mit den neuerscheinungen in deutschland für die switch 2 im nächsten monat",
        )

    assert "Preis" in result["query"]
    assert "UVP" in result["query"]
    assert "Straßenpreise" in result["query"]
    assert "Top 3" in result["query"]
    assert "beliebteste Spiele" in result["query"]
    assert "Launch Deutschland" in result["query"]


def test_sanitize_tool_arguments_rewrites_relative_week_reference():
    with patch("backend.services.tool_argument_sanitizer.datetime") as datetime_mock:
        datetime_mock.utcnow.return_value = datetime(2026, 3, 18, 12, 0, 0)
        datetime_mock.side_effect = lambda *args, **kwargs: datetime(2026, 3, 18, 12, 0, 0)
        result = sanitize_tool_arguments(
            "system.websearch",
            {
                "query": "Switch 2 Spiele KW 01 2025", 
                "provider": "openai",
            },
            provider="openai",
            original_user_text="Welche Switch 2 Spiele erscheinen nächste Woche?",
        )

    assert result["query"] == "Nintendo Switch 2 upcoming games release Kalenderwoche 13 2026"


def test_sanitize_tool_arguments_rewrites_relative_year_reference():
    with patch("backend.services.tool_argument_sanitizer.datetime") as datetime_mock:
        datetime_mock.utcnow.return_value = datetime(2026, 3, 18, 12, 0, 0)
        result = sanitize_tool_arguments(
            "system.websearch",
            {
                "query": "Switch 2 Spiele 2024",
                "provider": "openai",
            },
            provider="openai",
            original_user_text="Welche Switch 2 Spiele erscheinen dieses Jahr?",
        )

    assert result["query"] == "Nintendo Switch 2 upcoming games release 2026"


def test_sanitize_tool_arguments_appends_relative_quarter_reference():
    with patch("backend.services.tool_argument_sanitizer.datetime") as datetime_mock:
        datetime_mock.utcnow.return_value = datetime(2026, 3, 18, 12, 0, 0)
        result = sanitize_tool_arguments(
            "system.websearch",
            {
                "query": "Switch 2 Pipeline",
                "provider": "openai",
            },
            provider="openai",
            original_user_text="Welche Switch 2 Spiele erscheinen im kommenden Quartal?",
        )

    assert result["query"] == "Nintendo Switch 2 upcoming games release Q2 2026"


def test_sanitize_tool_arguments_restores_price_query_from_original_user_text():
    with patch("backend.services.tool_argument_sanitizer.datetime") as datetime_mock:
        datetime_mock.utcnow.return_value = datetime(2026, 3, 18, 12, 0, 0)
        result = sanitize_tool_arguments(
            "system.websearch",
            {
                "query": "current price of gold per troy ounce 2025 USD",
                "provider": "openai",
            },
            provider="openai",
            original_user_text="wieviel kostet aktuell eine feinunze gold?",
        )

    assert result["query"] == "wieviel kostet aktuell eine feinunze gold?"


def test_sanitize_tool_arguments_canonicalizes_switch_2_price_query():
    with patch("backend.services.tool_argument_sanitizer.datetime") as datetime_mock:
        datetime_mock.utcnow.return_value = datetime(2026, 3, 18, 12, 0, 0)
        result = sanitize_tool_arguments(
            "system.websearch",
            {
                "query": "wieviel kostet eine switch 2?",
                "provider": "openai",
            },
            provider="openai",
            original_user_text="wieviel kostet eine switch 2?",
        )

    assert result["query"] == "Nintendo Switch 2 Preis Euro"
