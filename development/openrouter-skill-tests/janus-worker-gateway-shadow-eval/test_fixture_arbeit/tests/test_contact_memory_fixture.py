"""Contract tests for the bounded contact-memory shadow-eval fixture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "contact_memory_fixture.json"

REQUIRED_TOP_LEVEL_KEYS = {
    "fixture_meta",
    "contract",
    "sync_policy",
    "primary_recall_scenario",
    "field_classification_examples",
    "blocked_auto_sync_examples",
    "untrusted_memory_examples",
    "conflict_scenario",
    "duplicate_preservation_scenario",
    "notes",
}

ALLOWED_TARGET_FIELDS = frozenset(
    {"preferences", "dislikes", "personal_details", "hobbies"}
)
BLOCKED_CATEGORIES = frozenset(
    {
        "political",
        "health",
        "address",
        "phone",
        "relationship",
        "religion",
        "finance",
    }
)
TRUSTED_ORIGINS = frozenset({"direct_user_utterance", "confirmed_contact_knowledge"})


def load_contact_memory_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def example_by_id(items: list[dict[str, Any]], example_id: str) -> dict[str, Any]:
    return next(item for item in items if item["id"] == example_id)


def assert_has_short_label(example: dict[str, Any]) -> None:
    assert example["short_label"].strip(), "reviewer short_label must be non-empty"


def derive_expected_state_from_facts(
    facts: list[dict[str, Any]],
    *,
    allowed_fields: frozenset[str] = ALLOWED_TARGET_FIELDS,
) -> dict[str, list[str]]:
    derived = {field: [] for field in allowed_fields}
    for fact in facts:
        if fact["sync_eligible"]:
            derived[fact["target_field"]].append(fact["value"])
    return derived


@pytest.fixture(name="fixture")
def fixture_payload() -> dict[str, Any]:
    return load_contact_memory_fixture()


# --- Fixture envelope and reviewer metadata ---


def test_fixture_has_expected_top_level_contract(fixture: dict[str, Any]) -> None:
    assert REQUIRED_TOP_LEVEL_KEYS.issubset(fixture.keys())
    assert fixture["fixture_meta"]["fixture_version"] == "1.4"


def test_fixture_declares_sandbox_scope(fixture: dict[str, Any]) -> None:
    meta = fixture["fixture_meta"]

    assert meta["scope"] == "fixture-only sandbox data"
    assert meta["connected_to_live_janus"] is False
    assert meta["primary_scenario_id"] == "chris_gier_recall_reconciliation"
    assert meta["review_focus"].strip()
    assert len(meta["review_checklist"]) >= 3


def test_fixture_meta_lists_reviewer_section_order(fixture: dict[str, Any]) -> None:
    section_order = fixture["fixture_meta"]["section_review_order"]

    assert section_order[0] == "sync_policy"
    assert section_order[-1] == "notes"
    assert set(section_order) == REQUIRED_TOP_LEVEL_KEYS - {"contract", "fixture_meta"}


def test_contract_documents_each_top_level_section(fixture: dict[str, Any]) -> None:
    contract = fixture["contract"]

    for key in REQUIRED_TOP_LEVEL_KEYS - {"contract"}:
        assert key in contract
        assert contract[key].strip()


# --- Sync policy contract ---


def test_sync_policy_matches_spec10_safe_fields_and_blocks(fixture: dict[str, Any]) -> None:
    policy = fixture["sync_policy"]

    assert set(policy["allowed_target_fields"]) == ALLOWED_TARGET_FIELDS
    assert set(policy["blocked_categories"]) == BLOCKED_CATEGORIES
    assert set(policy["trusted_origins"]) == TRUSTED_ORIGINS


# --- Primary recall happy path ---


def test_primary_recall_scenario_starts_with_empty_address_book(fixture: dict[str, Any]) -> None:
    scenario = fixture["primary_recall_scenario"]
    address_book = scenario["address_book_before"]

    assert scenario["contact_name"] == "Chris Gier"
    assert scenario["user_prompt"] == "Was weisst du ueber Chris Gier?"
    assert scenario["reconciliation_trigger"] == "contact_recall"
    assert scenario["short_label"].strip()
    assert scenario["narrative"].strip()
    assert len(scenario["reconciliation_steps"]) >= 3
    assert address_book["name"] == "Chris Gier"
    for field in ALLOWED_TARGET_FIELDS:
        assert address_book[field] == []


@pytest.mark.parametrize(
    ("example_id", "target_field"),
    [
        pytest.param("pref_star_wars", "preferences", id="star_wars"),
        pytest.param("pref_kimchi", "preferences", id="kimchi"),
    ],
)
def test_confirmed_memory_facts_are_sync_eligible(
    fixture: dict[str, Any],
    example_id: str,
    target_field: str,
) -> None:
    facts = fixture["primary_recall_scenario"]["confirmed_memory_facts"]
    matched = example_by_id(facts, example_id)

    assert_has_short_label(matched)
    assert matched["sync_eligible"] is True
    assert matched["trust"] == "confirmed_contact_knowledge"
    assert matched["origin"] == "confirmed_contact_knowledge"
    assert matched["target_field"] == target_field
    assert matched["value"].strip()


def test_primary_recall_expected_state_matches_confirmed_facts(
    fixture: dict[str, Any],
) -> None:
    scenario = fixture["primary_recall_scenario"]
    expected = scenario["expected_after_reconciliation"]
    derived = derive_expected_state_from_facts(scenario["confirmed_memory_facts"])

    assert {fact["value"] for fact in scenario["confirmed_memory_facts"]} == {
        "Star Wars",
        "Kimchi",
    }
    for field in ALLOWED_TARGET_FIELDS:
        assert expected[field] == derived[field]


# --- Field routing examples ---


@pytest.mark.parametrize(
    ("example_id", "target_field", "must_not_target_field"),
    [
        pytest.param(
            "dietary_to_personal_details",
            "personal_details",
            "preferences",
            id="dietary",
        ),
        pytest.param("hobby_to_hobbies", "hobbies", "preferences", id="hobby"),
        pytest.param("dislike_to_dislikes", "dislikes", "preferences", id="dislike"),
    ],
)
def test_field_classification_examples_target_safe_non_preference_fields(
    fixture: dict[str, Any],
    example_id: str,
    target_field: str,
    must_not_target_field: str,
) -> None:
    examples = fixture["field_classification_examples"]
    example = example_by_id(examples, example_id)

    assert_has_short_label(example)
    assert example["sync_eligible"] is True
    assert example["target_field"] == target_field
    assert example["must_not_target_field"] == must_not_target_field
    assert example["value"].strip()
    assert example["rationale"].strip()


def test_phrase_preservation_example_keeps_hobby_phrase_intact(
    fixture: dict[str, Any],
) -> None:
    example = example_by_id(
        fixture["field_classification_examples"],
        "phrase_preserved_in_hobbies",
    )

    assert_has_short_label(example)
    assert example["target_field"] == "hobbies"
    assert example["value"] == "Zeit im Garten"
    assert example["must_not_split_into"] == ["Zeit", "Garten"]


# --- Negative sync paths ---


@pytest.mark.parametrize("block_reason", sorted(BLOCKED_CATEGORIES))
def test_blocked_auto_sync_examples_cover_every_blocked_category(
    fixture: dict[str, Any],
    block_reason: str,
) -> None:
    blocked = fixture["blocked_auto_sync_examples"]
    matched = [example for example in blocked if example["block_reason"] == block_reason]

    assert len(matched) == 1, f"expected one blocked example for {block_reason!r}"
    example = matched[0]
    assert_has_short_label(example)
    assert example["sync_eligible"] is False
    assert example["id"].startswith("blocked_")


def test_untrusted_memory_examples_stay_out_of_address_book(fixture: dict[str, Any]) -> None:
    untrusted = fixture["untrusted_memory_examples"]

    assert len(untrusted) >= 1
    for example in untrusted:
        assert_has_short_label(example)
        assert example["sync_eligible"] is False
        assert example["origin"] == "model_generated"
        assert example["block_reason"] == "untrusted_origin"
        assert example["rationale"].strip()


def test_conflict_scenario_requires_user_prompt_not_auto_sync(
    fixture: dict[str, Any],
) -> None:
    scenario = fixture["conflict_scenario"]

    assert scenario["short_label"].strip()
    assert scenario["sync_eligible"] is False
    assert scenario["expected_behavior"] == "ask_user"
    assert scenario["address_book_before"]["preferences"] != [
        scenario["memory_fact"]["value"]
    ]
    assert scenario["rationale"].strip()


def test_duplicate_preservation_scenario_keeps_existing_value(
    fixture: dict[str, Any],
) -> None:
    scenario = fixture["duplicate_preservation_scenario"]
    memory_value = scenario["memory_fact"]["value"]

    assert scenario["short_label"].strip()
    assert scenario["sync_eligible"] is False
    assert scenario["expected_behavior"] == "preserve_existing"
    assert memory_value in scenario["address_book_before"]["preferences"]
    assert scenario["rationale"].strip()


def test_notes_remain_fixture_only(fixture: dict[str, Any]) -> None:
    notes = fixture["notes"]

    assert notes
    joined = " ".join(notes).lower()
    assert "shadow" in joined
    assert "not wired" in joined
