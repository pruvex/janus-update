"""Test calendar routing fix - shopping guardrail bypass for calendar intents."""

import pytest
from types import SimpleNamespace

from backend.services.orchestrator.execution_dispatcher import (
    _build_routing_turn_skill_ids,
    _is_calendar_routing_combo,
    _is_contact_relationship_recall_query,
    _should_force_routing_tool_choice,
    _suppress_identity_for_address_book_contact_recall,
)
from backend.services.capability_registry import CapabilityRegistry
from backend.services.orchestrator import intent_engine as intent_engine_module
from backend.services.orchestrator.intent_engine import (
    IntentDetectionResult,
    IntentEngine,
    calendar_user_text_overlap_snapshot,
)


class TestCalendarRoutingFix:
    """Test that calendar intents bypass shopping guardrail."""
    
    @pytest.fixture
    def intent_engine(self):
        return IntentEngine()
    
    def test_shopping_intent_vetoed_by_calendar_keywords(self, intent_engine):
        """Shopping intent should be vetoed when calendar keywords are present."""
        # Calendar + shopping context (should be vetoed)
        assert not intent_engine.detect_shopping_intent("um 14 uhr einkaufen beim netto")
        assert not intent_engine.detect_shopping_intent("termin: einkaufen morgen")
        assert not intent_engine.detect_shopping_intent("trage ein: einkaufen am montag um 15 uhr")
        
        # Price-focused queries should still work (override veto)
        assert intent_engine.detect_shopping_intent("was kostet einkaufen beim netto")
        assert intent_engine.detect_shopping_intent("wie viel kostet der einkauf")
    
    def test_calendar_intent_detection(self, intent_engine):
        """Calendar intent should be detected correctly."""
        assert intent_engine.detect_calendar_intent("um 14 uhr einkaufen beim netto")
        assert intent_engine.detect_calendar_intent("termin morgen um 15 uhr")
        assert intent_engine.detect_calendar_intent("trage ein: meeting am dienstag")
        assert intent_engine.detect_calendar_intent("termin erstellen für nächste woche")
        
        # Non-calendar queries
        assert not intent_engine.detect_calendar_intent("was kostet das")
        assert not intent_engine.detect_calendar_intent("kaufen bei amazon")

    def test_aux_classifier_flag_off_keeps_legacy_detect_all_intents(self, intent_engine, monkeypatch):
        monkeypatch.setattr(intent_engine_module, "is_aux_classifier_enabled", lambda: False)
        monkeypatch.setattr(
            intent_engine_module.intent_aux_classifier,
            "classify_sync",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("aux must stay off")),
        )

        result = intent_engine.detect_all_intents("Chris mag Pizza")
        assert result.is_fact_telling
        assert not result.is_personal_recall

    def test_aux_classifier_medium_conflict_routes_to_clarify(self, intent_engine, monkeypatch):
        monkeypatch.setattr(intent_engine_module, "is_aux_classifier_enabled", lambda: True)

        class FakeConfig:
            medium_confidence_threshold = 0.55
            high_confidence_threshold = 0.80

        monkeypatch.setattr(intent_engine_module, "get_intent_aux_classifier_config", lambda: FakeConfig())
        monkeypatch.setattr(
            intent_engine_module.intent_aux_classifier,
            "classify_sync",
            lambda *_args, **_kwargs: intent_engine_module.ActionSubjectResult(
                action="recall",
                subject="contact",
                confidence=0.70,
                evidence="was mag chris",
                source="aux_llm",
            ),
        )

        result = intent_engine.detect_all_intents("Chris mag Pizza")
        assert result.is_fact_telling
        assert result.is_ambiguous
        assert result.vetoed_intents.get("aux_classifier") == "aux_legacy_conflict"

    def test_aux_classifier_high_confidence_marks_calendar_mutation(self, intent_engine, monkeypatch):
        monkeypatch.setattr(intent_engine_module, "is_aux_classifier_enabled", lambda: True)

        class FakeConfig:
            medium_confidence_threshold = 0.55
            high_confidence_threshold = 0.80

        monkeypatch.setattr(intent_engine_module, "get_intent_aux_classifier_config", lambda: FakeConfig())
        monkeypatch.setattr(
            intent_engine_module.intent_aux_classifier,
            "classify_sync",
            lambda *_args, **_kwargs: intent_engine_module.ActionSubjectResult(
                action="mutate",
                subject="calendar",
                confidence=0.92,
                evidence="spaeter legen",
                source="aux_llm",
            ),
        )

        text = "Kannst du Aldi naechsten Samstag spaeter legen?"
        result = intent_engine.detect_all_intents(text, calendar_snapshot=ALD_SNAPSHOT)
        assert result.is_calendar_intent
        assert result.is_calendar_mutation

    def test_weather_dog_walk_with_mit_is_not_calendar(self, intent_engine):
        """Regression: bare 'mit' in a weather walk question must not route to calendar."""
        text = "brauche ich in 51067 einen regenschirm, wenn ich um halb 9 mit dem hund raus gehe?"

        assert intent_engine.detect_weather_intent(text)
        assert not intent_engine.detect_calendar_intent(text)

        result = intent_engine.detect_all_intents(text)
        assert result.is_weather_intent
        assert not result.is_calendar_intent
        assert result.primary_intent == "weather"
    
    def test_shopping_intent_without_calendar_keywords(self, intent_engine):
        """Shopping intent should work normally without calendar keywords."""
        assert intent_engine.detect_shopping_intent("kaufen bei amazon")
        assert intent_engine.detect_shopping_intent("was kostet das bei otto")
        assert intent_engine.detect_shopping_intent("günstige offers bei zalando")


# --- TASK-062: contextual intent boost vs. Kalender-Snapshot ----------------------------

ALD_SNAPSHOT = {
    "events": [
        {
            "title": "Einkauf Aldi Süd",
            "location": "",
            "start": "2026-05-03T18:30:00+02:00",
            "end": "2026-05-03T19:30:00+02:00",
        }
    ]
}


class TestCalendarSnapshotIntentBoost:
    def test_overlap_helper_detects_shared_token_with_title(self):
        assert calendar_user_text_overlap_snapshot(
            "Kannst du Aldi nächsten Samstag später legen?",
            ALD_SNAPSHOT,
        )

    def test_detect_all_intents_boosts_calendar_from_snapshot_without_calendar_lexemes(self):
        engine = IntentEngine()
        text = "Kannst du Aldi nächsten Samstag später legen?"
        assert calendar_user_text_overlap_snapshot(text, ALD_SNAPSHOT)
        base = engine.detect_all_intents(text, calendar_snapshot=None)
        boosted = engine.detect_all_intents(text, calendar_snapshot=ALD_SNAPSHOT)
        assert not base.is_calendar_intent
        assert boosted.is_calendar_intent
        assert boosted.primary_intent == "calendar"

    def test_snapshot_boost_suppressed_when_strong_price_shopping_signal(self):
        engine = IntentEngine()
        result = engine.detect_all_intents(
            "Was kostet Milch bei Aldi?",
            calendar_snapshot=ALD_SNAPSHOT,
        )
        assert result.is_shopping_intent
        assert not result.is_calendar_intent

    def test_routing_geo_suppresses_calendar_snapshot_boost(self):
        """Entfernungsfrage: kein Kalender trotz Überlappung mit Event-Ort/-titel."""
        engine = IntentEngine()
        snap = {
            "events": [
                {
                    "title": "Meeting München",
                    "location": "Köln",
                    "start": "2026-05-10T10:00:00+02:00",
                    "end": "2026-05-10T11:00:00+02:00",
                }
            ]
        }
        text = "wie weit ist es von köln nach münchen?"
        assert calendar_user_text_overlap_snapshot(text, snap)
        result = engine.detect_all_intents(text, calendar_snapshot=snap)
        assert result.is_routing_geo_intent
        assert not result.is_calendar_intent
        assert result.primary_intent == "routing_geo"


class TestWeatherSnapshotIntentSuppress:
    """Wetterfragen: kein Kalender-Snapshot-Boost bei Orts-Overlap (Parität zu routing_geo)."""

    def test_weather_suppresses_calendar_snapshot_boost(self):
        engine = IntentEngine()
        snap = {
            "events": [
                {
                    "title": "Meeting München",
                    "location": "Köln",
                    "start": "2026-05-10T10:00:00+02:00",
                    "end": "2026-05-10T11:00:00+02:00",
                }
            ]
        }
        text = "und wie ist das wetter in münchen?"
        assert calendar_user_text_overlap_snapshot(text, snap)
        result = engine.detect_all_intents(text, calendar_snapshot=snap)
        assert result.is_weather_intent
        assert not result.is_calendar_intent
        assert result.primary_intent == "weather"


class TestNewsIntentPrecision:
    @pytest.fixture
    def intent_engine(self):
        return IntentEngine()

    def test_contact_preference_with_word_zeit_is_not_news_intent(self, intent_engine):
        result = intent_engine.detect_all_intents("der chris verbringt gerne zeit im garten")

        assert result.is_fact_telling
        assert not result.is_news_intent
        assert result.primary_intent is None

    def test_contact_preference_with_news_source_word_vetoes_news_intent(self, intent_engine):
        result = intent_engine.detect_all_intents("Chris mag den Spiegel")

        assert result.is_fact_telling
        assert not result.is_news_intent
        assert result.primary_intent is None
        assert result.vetoed_intents.get("news") == "fact_telling_contact_statement"

    def test_contact_hobby_statement_with_game_title_stays_fact_telling(self, intent_engine):
        result = intent_engine.detect_all_intents("Nathan spielt gerne League of Legends")

        assert result.is_fact_telling
        assert not result.is_news_intent
        assert result.primary_intent is None
        assert result.vetoed_intents.get("ambiguity") == "fact_telling_contact_statement"

    def test_die_zeit_and_zeit_online_remain_news_sources(self, intent_engine):
        assert intent_engine.detect_news_intent("was schreibt die Zeit heute?")
        assert intent_engine.detect_news_intent("Zeit Online Nachrichten zu KI")


class TestContactKnowledgeRecallIntent:
    @pytest.fixture
    def intent_engine(self):
        return IntentEngine()

    def test_contact_preference_question_is_personal_recall_not_fact_telling(self, intent_engine):
        result = intent_engine.detect_all_intents("was mag chris?")

        assert result.is_personal_recall
        assert not result.is_fact_telling
        assert result.primary_intent == "personal_recall"

    def test_contact_knowledge_question_is_personal_recall(self, intent_engine):
        result = intent_engine.detect_all_intents("was weißt du alles über chris?")

        assert result.is_personal_recall
        assert result.primary_intent == "personal_recall"


    def test_contact_knowledge_question_bypasses_external_and_ambiguity(self, intent_engine):
        result = intent_engine.detect_all_intents("was wei\u00dft du alles \u00fcber chris?")

        assert result.is_personal_recall
        assert not result.is_wikipedia_intent
        assert not result.is_ambiguous
        assert result.primary_intent == "personal_recall"
        assert result.vetoed_intents.get("ambiguity") == "personal_recall_contact_statement"

    def test_full_contact_knowledge_question_is_personal_recall_without_clarification(self, intent_engine):
        result = intent_engine.detect_all_intents("was wei\u00dft du \u00fcber chris gier?")

        assert result.is_personal_recall
        assert not result.is_ambiguous
        assert result.primary_intent == "personal_recall"

    def test_multi_contact_preference_question_is_personal_recall_without_clarification(self, intent_engine):
        result = intent_engine.detect_all_intents("was mögen chris und oli?")

        assert result.is_personal_recall
        assert not result.is_ambiguous
        assert result.primary_intent == "personal_recall"

    def test_relationship_contact_question_bypasses_wikipedia_and_ambiguity(self, intent_engine):
        result = intent_engine.detect_all_intents("wer ist nathans freundin?")

        assert result.is_personal_recall
        assert not result.is_wikipedia_intent
        assert not result.is_ambiguous
        assert result.primary_intent == "personal_recall"
        assert result.vetoed_intents.get("wikipedia") == "personal_recall_contact_statement"
        assert result.vetoed_intents.get("ambiguity") == "personal_recall_contact_statement"

    def test_relationship_contact_name_question_bypasses_wikipedia_and_ambiguity(self, intent_engine):
        result = intent_engine.detect_all_intents("wie heisst nathans freundin?")

        assert result.is_personal_recall
        assert not result.is_wikipedia_intent
        assert not result.is_ambiguous
        assert result.primary_intent == "personal_recall"

    def test_calendar_wikipedia_combo_is_not_video_understanding_or_personal_recall(self, intent_engine):
        query = (
            "Was steht heute in meinem Kalender und gib mir eine Wikipedia-Zusammenfassung zu Berlin."
        )

        result = intent_engine.detect_all_intents(query)

        assert result.is_calendar_intent
        assert result.is_wikipedia_intent
        assert not result.is_personal_recall
        assert not result.is_video_understanding_intent
        assert result.primary_intent == "calendar"
        assert intent_engine.detect_routine_request_skills(query) == frozenset(
            {"calendar.list_events", "system.wikipedia_summary"}
        )

    def test_relationship_contact_recall_helper_detects_possessive_question(self):
        assert _is_contact_relationship_recall_query("wer ist nathans freundin?")
        assert _is_contact_relationship_recall_query("wie heisst nathans freundin?")
        assert not _is_contact_relationship_recall_query("wer ist nikola tesla?")

    def test_contact_fact_statement_bypasses_ambiguity_clarification(self, intent_engine):
        result = intent_engine.detect_all_intents("OLI LIEBT Big bang theory")

        assert result.is_fact_telling
        assert not result.is_ambiguous
        assert result.ambiguity_confidence == 0.0
        assert result.vetoed_intents.get("ambiguity") == "fact_telling_contact_statement"

    def test_pronoun_contact_fact_followup_bypasses_ambiguity_clarification(self, intent_engine):
        result = intent_engine.detect_all_intents("und er hat einen Hund")

        assert result.is_fact_telling
        assert not result.is_ambiguous
        assert result.ambiguity_confidence == 0.0
        assert result.vetoed_intents.get("ambiguity") == "fact_telling_contact_statement"

    def test_pronoun_contact_fact_followup_with_besitzt_bypasses_ambiguity_clarification(self, intent_engine):
        result = intent_engine.detect_all_intents("und er besitzt einen Hund")

        assert result.is_fact_telling
        assert not result.is_ambiguous
        assert result.ambiguity_confidence == 0.0
        assert result.vetoed_intents.get("ambiguity") == "fact_telling_contact_statement"

    def test_named_pet_attribute_contact_fact_bypasses_ambiguity_clarification(self, intent_engine):
        result = intent_engine.detect_all_intents("olis hund tasso ist ein podenco")

        assert result.is_fact_telling
        assert not result.is_ambiguous
        assert result.ambiguity_confidence == 0.0
        assert result.vetoed_intents.get("ambiguity") == "fact_telling_contact_statement"

    def test_address_book_contact_recall_suppresses_user_identity_directive(self):
        address_context = "**Adressbuch:**\nKontakt: Christoph Gier (Nickname: Cris)"

        assert _suppress_identity_for_address_book_contact_recall(
            "was wei\u00dft du \u00fcber chris gier?",
            address_context,
        )
        assert not _suppress_identity_for_address_book_contact_recall(
            "was ist mein name?",
            address_context,
        )

    def test_contact_recall_without_concrete_address_book_hit_keeps_identity_directive(self):
        prompt_rule_only = (
            "[ADRESSBUCH-KONTAKTE]\n"
            'Wenn unter "**Adressbuch:**" genau passende Kontaktinformationen zur Anfrage stehen.'
        )

        assert not _suppress_identity_for_address_book_contact_recall(
            "was wei\u00dft du \u00fcber chris gier?",
            prompt_rule_only,
        )

    def test_self_recall_keeps_identity_directive_even_with_address_book_context(self):
        address_context = "**Adressbuch:**\nKontakt: Christoph Gier (Nickname: Cris)"

        assert not _suppress_identity_for_address_book_contact_recall(
            "was wei\u00dft du \u00fcber mich?",
            address_context,
        )


class TestDiamondPdfToolPolicy:
    """create_pdf nur bei explizitem Wunsch / Meta-Flow (CapabilityRegistry)."""

    @pytest.fixture
    def registry(self):
        return CapabilityRegistry(registry_path="/dev/null", skills_dir="/dev/null")

    def test_create_pdf_forbidden_by_default(self, registry):
        pol = registry.get_intent_skill_policy(IntentDetectionResult())
        assert "system.create_pdf" in pol["forbidden"]

    def test_create_pdf_allowed_when_explicit(self, registry):
        pol = registry.get_intent_skill_policy(
            IntentDetectionResult(is_explicit_pdf_intent=True)
        )
        assert "system.create_pdf" not in pol["forbidden"]

    def test_create_pdf_allowed_for_multitask_image_pdf(self, registry):
        pol = registry.get_intent_skill_policy(
            IntentDetectionResult(is_multitask_image_pdf=True)
        )
        assert "system.create_pdf" not in pol["forbidden"]

    def test_routing_geo_boosts_system_routing(self, registry):
        pol = registry.get_intent_skill_policy(
            IntentDetectionResult(is_routing_geo_intent=True, primary_intent="routing_geo")
        )
        assert "system.routing" in pol["boosted"]

    def test_weather_mandates_system_weather(self, registry):
        pol = registry.get_intent_skill_policy(
            IntentDetectionResult(is_weather_intent=True, primary_intent="weather")
        )
        assert "system.weather" in pol["mandatory"]

    def test_weather_policy_does_not_offer_calendar_tools_on_overlap(self, registry):
        pol = registry.get_intent_skill_policy(
            IntentDetectionResult(
                is_weather_intent=True,
                is_calendar_intent=True,
                primary_intent="weather",
            )
        )

        assert "system.weather" in pol["mandatory"]
        assert "calendar.list_events" not in pol["mandatory"]

    def test_personal_recall_policy_mandates_memory_and_forbids_external_search(self, registry):
        pol = registry.get_intent_skill_policy(
            IntentDetectionResult(is_personal_recall=True, primary_intent="personal_recall")
        )

        assert "memory.read" in pol["mandatory"]
        assert "system.websearch" in pol["forbidden"]
        assert "system.rss_news" in pol["forbidden"]


class TestCalendarRoutingDispatchGuard:
    """Mixed calendar+routing turns must not trap Gemini in routing-only force loops."""

    MIXED_PROMPT = (
        "Welche Termine habe ich heute und wie weit ist es von Berlin nach Hamburg?"
    )

    def test_mixed_prompt_detects_calendar_and_routing_intents(self):
        engine = IntentEngine()
        result = engine.detect_all_intents(self.MIXED_PROMPT)

        assert result.is_calendar_intent
        assert result.is_routing_geo_intent
        assert result.primary_intent == "calendar"

    def test_is_calendar_routing_combo_true_only_for_calendar_read_turn(self):
        assert _is_calendar_routing_combo(
            SimpleNamespace(
                is_calendar_intent=True,
                is_calendar_mutation=False,
                is_calendar_creation=False,
            )
        ) is True
        assert _is_calendar_routing_combo(
            SimpleNamespace(
                is_calendar_intent=True,
                is_calendar_mutation=True,
                is_calendar_creation=False,
            )
        ) is False
        assert _is_calendar_routing_combo(None) is False

    def test_build_routing_turn_skill_ids_keeps_calendar_skills_for_mixed_turn(self):
        result = _build_routing_turn_skill_ids(
            [
                "calendar.list_events",
                "calendar.find_and_update_event",
                "system.routing",
                "knowledge.query",
            ],
            calendar_intent=True,
        )

        assert result == [
            "calendar.list_events",
            "calendar.find_and_update_event",
            "system.routing",
        ]

    def test_build_routing_turn_skill_ids_clamps_to_routing_for_pure_routing(self):
        assert _build_routing_turn_skill_ids(
            ["calendar.list_events", "system.routing"],
            calendar_intent=False,
        ) == ["system.routing"]

    def test_should_force_routing_tool_choice_false_for_mixed_calendar_routing(self):
        assert _should_force_routing_tool_choice(
            SimpleNamespace(
                primary_intent="calendar",
                is_routing_geo_intent=True,
                is_calendar_intent=True,
                is_calendar_mutation=False,
                is_calendar_creation=False,
            )
        ) is False

    def test_should_force_routing_tool_choice_true_for_pure_routing(self):
        assert _should_force_routing_tool_choice(
            SimpleNamespace(
                primary_intent="routing_geo",
                is_routing_geo_intent=True,
                is_calendar_intent=False,
                is_calendar_mutation=False,
                is_calendar_creation=False,
            )
        ) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
