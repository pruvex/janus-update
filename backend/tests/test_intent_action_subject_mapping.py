from backend.data.schemas_intent import ActionSubjectResult
from backend.services.orchestrator.intent_aux_classifier import (
  classify_with_regex_fallback,
  map_action_subject_to_legacy_flags,
)


def _result(action, subject, confidence=0.9, evidence="test"):
  return ActionSubjectResult(
    action=action,
    subject=subject,
    confidence=confidence,
    evidence=evidence,
    source="aux_llm",
  )


def test_recall_maps_to_personal_recall_flag():
  mapped = map_action_subject_to_legacy_flags(_result("recall", "contact"))
  assert mapped["is_personal_recall"] is True
  assert mapped["is_fact_telling"] is False


def test_tell_fact_maps_to_fact_telling_flag():
  mapped = map_action_subject_to_legacy_flags(_result("tell_fact", "contact"))
  assert mapped["is_fact_telling"] is True
  assert mapped["is_personal_recall"] is False


def test_mutate_and_create_map_to_calendar_flags():
  mutate = map_action_subject_to_legacy_flags(_result("mutate", "calendar"))
  create = map_action_subject_to_legacy_flags(_result("create", "calendar"))
  assert mutate["is_calendar_mutation"] is True
  assert create["is_calendar_creation"] is True


def test_self_subject_maps_to_self_referential_flag():
  mapped = map_action_subject_to_legacy_flags(_result("tell_fact", "self"))
  assert mapped["is_self_referential"] is True


def test_clarify_or_low_confidence_maps_to_ambiguous():
  clarify = map_action_subject_to_legacy_flags(_result("clarify", "none", confidence=0.4))
  low = map_action_subject_to_legacy_flags(_result("general", "none", confidence=0.4))
  assert clarify["is_ambiguous"] is True
  assert low["is_ambiguous"] is True


def test_contact_fact_telling_regex_mapping():
  result = classify_with_regex_fallback("Chris mag Kimchi")
  mapped = map_action_subject_to_legacy_flags(result)
  assert result.action == "tell_fact"
  assert result.subject == "contact"
  assert mapped["is_fact_telling"] is True


def test_pet_fact_regex_mapping():
  result = classify_with_regex_fallback("olis katze garfield mag keinen thunfisch")
  mapped = map_action_subject_to_legacy_flags(result)
  assert result.action == "tell_fact"
  assert result.subject == "pet"
  assert mapped["is_fact_telling"] is True


def test_contact_recall_regex_mapping():
  result = classify_with_regex_fallback("was mag chris?")
  mapped = map_action_subject_to_legacy_flags(result)
  assert result.action == "recall"
  assert result.subject == "contact"
  assert mapped["is_personal_recall"] is True
