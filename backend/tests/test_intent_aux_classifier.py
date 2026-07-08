import json

import pytest

from backend.data.schemas_intent import ActionSubjectResult, validate_action_subject_payload
from backend.services.orchestrator import intent_config
from backend.services.orchestrator.intent_aux_classifier import (
    AuxClassifierCircuitBreaker,
    AuxiliaryIntentClassifier,
    _extract_provider_text,
    classify,
    classify_sync,
    classify_with_regex_fallback,
    parse_provider_json,
)
from backend.services.orchestrator.intent_config import IntentAuxClassifierConfig


def test_action_subject_result_rejects_invalid_action():
  with pytest.raises(Exception):
    ActionSubjectResult(
      action="invalid",
      subject="contact",
      confidence=0.9,
      evidence="x",
      source="aux_llm",
    )


def test_action_subject_result_trims_evidence_to_80_chars():
  result = ActionSubjectResult(
    action="tell_fact",
    subject="contact",
    confidence=0.9,
    evidence="x" * 120,
    source="aux_llm",
  )
  assert len(result.evidence) == 80


def test_validate_action_subject_payload_fail_closed_on_bad_json():
  assert validate_action_subject_payload('{"action":"recall"}') is None
  assert validate_action_subject_payload({"action": "nope", "subject": "none", "confidence": 0.5, "evidence": "x"}) is None


def test_parse_provider_json_accepts_fenced_payload():
  raw = """```json
{"action":"recall","subject":"contact","confidence":0.91,"evidence":"was mag chris"}
```"""
  parsed = parse_provider_json(raw)
  assert parsed is not None
  assert parsed.action == "recall"
  assert parsed.subject == "contact"
  assert parsed.source == "aux_llm"


def test_extract_provider_text_prefers_primary_fields():
  assert _extract_provider_text({"text": "alpha", "content": "beta"}) == "alpha"
  assert _extract_provider_text({"content": "beta"}) == "beta"
  assert _extract_provider_text({"result": "gamma"}) == "gamma"
  assert _extract_provider_text({"raw_assistant_response": {"content": "delta"}}) == "delta"
  assert _extract_provider_text({}) == ""


@pytest.mark.asyncio
async def test_classify_uses_regex_fallback_when_flag_disabled(monkeypatch):
  monkeypatch.setattr(intent_config, "INTENT_AUX_CLASSIFIER_ENABLED", False)
  config = IntentAuxClassifierConfig(enabled=False)

  async def provider_should_not_run(_text, _ctx):
    raise AssertionError("provider must not run when flag is off")

  result = await classify(
    "Chris mag Pizza",
    provider_callable=provider_should_not_run,
    config=config,
  )
  assert result.source == "regex_fallback"
  assert result.action == "tell_fact"
  assert result.subject == "contact"


@pytest.mark.asyncio
async def test_classify_uses_provider_when_enabled():
  async def fake_provider(_text, _ctx):
    return json.dumps(
      {
        "action": "recall",
        "subject": "contact",
        "confidence": 0.88,
        "evidence": "was mag chris",
      }
    )

  config = IntentAuxClassifierConfig(enabled=True)
  result = await classify("was mag chris?", provider_callable=fake_provider, config=config)
  assert result.source == "aux_llm"
  assert result.action == "recall"
  assert result.confidence == 0.88


@pytest.mark.asyncio
async def test_classify_fail_closed_on_invalid_provider_output():
  async def bad_provider(_text, _ctx):
    return '{"action":"recall","subject":"contact","confidence":"high"}'

  config = IntentAuxClassifierConfig(enabled=True)
  result = await classify("was mag chris?", provider_callable=bad_provider, config=config)
  assert result.source == "regex_fallback"


@pytest.mark.asyncio
async def test_classify_fail_closed_on_provider_exception():
  async def exploding_provider(_text, _ctx):
    raise RuntimeError("provider down")

  config = IntentAuxClassifierConfig(enabled=True)
  result = await classify("was mag chris?", provider_callable=exploding_provider, config=config)
  assert result.source == "regex_fallback"
  assert result.action == "recall"


def test_circuit_breaker_opens_after_repeated_failures():
  breaker = AuxClassifierCircuitBreaker(failure_threshold=3, recovery_timeout=120)
  assert breaker.can_execute() is True
  breaker.record_failure()
  breaker.record_failure()
  assert breaker.can_execute() is True
  breaker.record_failure()
  assert breaker.can_execute() is False
  assert breaker.get_state()["state"] == "OPEN"


@pytest.mark.asyncio
async def test_classifier_uses_regex_when_circuit_open():
  breaker = AuxClassifierCircuitBreaker(failure_threshold=1, recovery_timeout=120)
  breaker.record_failure()

  async def provider_should_not_run(_text, _ctx):
    raise AssertionError("provider must not run when circuit is open")

  classifier = AuxiliaryIntentClassifier(
    config=IntentAuxClassifierConfig(enabled=True),
    provider_callable=provider_should_not_run,
    circuit_breaker=breaker,
  )
  result = await classifier.classify("Chris mag Pizza")
  assert result.source == "regex_fallback"


def test_classify_sync_bridges_async_provider():
  async def fake_provider(_text, _ctx):
    return json.dumps(
      {
        "action": "create",
        "subject": "calendar",
        "confidence": 0.84,
        "evidence": "termin anlegen",
      }
    )

  result = classify_sync(
    "lege einen termin an",
    provider_callable=fake_provider,
    config=IntentAuxClassifierConfig(enabled=True),
  )
  assert result.source == "aux_llm"
  assert result.action == "create"


def test_regex_fallback_pet_fact_not_contact():
  result = classify_with_regex_fallback("Olis Hund Tasso ist ein Podenco")
  assert result.action == "tell_fact"
  assert result.subject == "pet"


def test_regex_fallback_contact_recall():
  result = classify_with_regex_fallback("was weisst du ueber chris?")
  assert result.action == "recall"
  assert result.subject == "contact"
