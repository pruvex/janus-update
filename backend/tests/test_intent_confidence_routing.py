from backend.data.schemas_intent import ActionSubjectResult
from backend.services.orchestrator.execution_dispatcher import _should_soft_route_ambiguous_intent
from backend.services.orchestrator.intent_config import IntentAuxClassifierConfig
from backend.services.orchestrator.intent_engine import IntentDetectionResult, IntentEngine
from backend.services.orchestrator import intent_engine as intent_engine_module


def test_aux_fact_telling_medium_confidence_clears_ambiguity(monkeypatch):
    engine = IntentEngine()
    result = IntentDetectionResult(is_ambiguous=True, ambiguity_confidence=0.62)
    aux_result = ActionSubjectResult(
        action="tell_fact",
        subject="contact",
        confidence=0.61,
        evidence="contact fact",
        source="aux_llm",
    )

    monkeypatch.setattr(intent_engine_module, "is_aux_classifier_enabled", lambda: True)
    monkeypatch.setattr(
        intent_engine_module,
        "get_intent_aux_classifier_config",
        lambda: IntentAuxClassifierConfig(enabled=True),
    )
    monkeypatch.setattr(intent_engine_module.intent_aux_classifier, "classify_sync", lambda *args, **kwargs: aux_result)

    engine._apply_aux_classifier_merge(result, "Chris mag Kimchi")

    assert result.is_fact_telling is True
    assert result.is_ambiguous is False
    assert result.routing_confidence == 0.61
    assert result.vetoed_intents["ambiguity"] == "aux_classifier_medium_confidence_routing"


def test_aux_calendar_mutation_medium_confidence_clears_ambiguity(monkeypatch):
    engine = IntentEngine()
    result = IntentDetectionResult(is_ambiguous=True, ambiguity_confidence=0.66)
    aux_result = ActionSubjectResult(
        action="mutate",
        subject="calendar",
        confidence=0.70,
        evidence="calendar mutation",
        source="aux_llm",
    )

    monkeypatch.setattr(intent_engine_module, "is_aux_classifier_enabled", lambda: True)
    monkeypatch.setattr(
        intent_engine_module,
        "get_intent_aux_classifier_config",
        lambda: IntentAuxClassifierConfig(enabled=True),
    )
    monkeypatch.setattr(intent_engine_module.intent_aux_classifier, "classify_sync", lambda *args, **kwargs: aux_result)

    engine._apply_aux_classifier_merge(result, "verschiebe den Termin morgen")

    assert result.is_calendar_intent is True
    assert result.is_calendar_mutation is True
    assert result.is_ambiguous is False
    assert result.routing_confidence == 0.70


def test_aux_contact_recall_can_override_wikipedia_guardrail(monkeypatch):
    engine = IntentEngine()
    result = IntentDetectionResult(is_wikipedia_intent=True, is_ambiguous=True, ambiguity_confidence=0.83)
    aux_result = ActionSubjectResult(
        action="recall",
        subject="contact",
        confidence=0.64,
        evidence="contact recall",
        source="aux_llm",
    )

    monkeypatch.setattr(intent_engine_module, "is_aux_classifier_enabled", lambda: True)
    monkeypatch.setattr(
        intent_engine_module,
        "get_intent_aux_classifier_config",
        lambda: IntentAuxClassifierConfig(enabled=True),
    )
    monkeypatch.setattr(intent_engine_module.intent_aux_classifier, "classify_sync", lambda *args, **kwargs: aux_result)

    engine._apply_aux_classifier_merge(result, "was ist toms lieblingsgetraenk?")

    assert result.is_personal_recall is True
    assert result.is_wikipedia_intent is False
    assert result.is_ambiguous is False
    assert result.vetoed_intents["wikipedia"] == "personal_recall_contact_statement"


def test_calendar_read_with_medium_routing_confidence_clears_ambiguity(monkeypatch):
    engine = IntentEngine()
    result = IntentDetectionResult(
        is_calendar_intent=True,
        is_ambiguous=True,
        ambiguity_confidence=0.70,
    )
    aux_result = ActionSubjectResult(
        action="general",
        subject="none",
        confidence=0.55,
        evidence="calendar read confidence",
        source="aux_llm",
    )

    monkeypatch.setattr(intent_engine_module, "is_aux_classifier_enabled", lambda: True)
    monkeypatch.setattr(
        intent_engine_module,
        "get_intent_aux_classifier_config",
        lambda: IntentAuxClassifierConfig(enabled=True),
    )
    monkeypatch.setattr(intent_engine_module.intent_aux_classifier, "classify_sync", lambda *args, **kwargs: aux_result)

    engine._apply_aux_classifier_merge(result, "um 14 uhr einkaufen beim netto")

    assert result.is_calendar_intent is True
    assert result.is_ambiguous is False
    assert result.vetoed_intents["ambiguity"] == "calendar_read_confidence_routing"


def test_medium_ambiguity_soft_routes_without_hard_block():
    result = IntentDetectionResult(is_ambiguous=True, ambiguity_confidence=0.61, routing_confidence=0.61)

    route = _should_soft_route_ambiguous_intent(result, "um 14 uhr einkaufen beim netto")

    assert route == "medium_ambiguity_soft_route"


def test_high_ambiguity_still_blocks_without_supported_route():
    result = IntentDetectionResult(is_ambiguous=True, ambiguity_confidence=0.91, routing_confidence=0.20)

    route = _should_soft_route_ambiguous_intent(result, "welchen meinst du genau eigentlich")

    assert route == "hard_block"
