import json

from backend.services.orchestrator.execution_engine import (
    _build_dynamic_fallback_summary,
    _build_memory_read_fallback_response,
    _build_memory_read_fallback_response_v2,
    _should_force_memory_read_fallback,
    _build_memory_write_fallback_response,
    _should_force_memory_write_fallback,
)


def test_openai_authentication_error_gets_actionable_user_message():
    message = _build_dynamic_fallback_summary(
        exception=RuntimeError("AuthenticationError: status=401 invalid_api_key"),
        provider="openai",
        model="gpt-5.4-nano",
    )

    assert "OpenAI-API-Key" in message
    assert "neu eintragen" in message
    assert "robusten Neuaufbau" not in message


def test_memory_read_fallback_builds_stable_contact_recall_response():
    message = _build_memory_read_fallback_response(
        "Was weiÃŸt du Ã¼ber Chris Gier?",
        [
            {
                "name": "memory.read",
                "_skill_id": "memory.read",
                "content": json.dumps(
                    {
                        "status": "ok",
                        "data": {
                            "memories": [
                                {"fact": "Chris ist vegetarier."},
                                {"fact": "Chris ist vegetarier"},
                            ]
                        },
                    }
                ),
            }
        ],
    )

    assert "Über Chris Gier" in message
    assert "- Chris ist vegetarier." in message
    assert message.count("Chris ist vegetarier") == 1


def test_memory_read_fallback_filters_foreign_contact_facts_for_oli_query():
    message = _build_memory_read_fallback_response(
        "Was weiÃŸt du Ã¼ber Oli?",
        [
            {
                "name": "memory.read",
                "_skill_id": "memory.read",
                "content": json.dumps(
                    {
                        "status": "ok",
                        "data": {
                            "memories": [
                                {"fact": "Oli wohnt in KÃ¶ln Stammheim."},
                                {"fact": "Oli heiÃŸt Oliver Schwab."},
                                {"fact": "Chris gier liebt star wars."},
                                {"fact": "Chris gier liebt kimchi."},
                            ]
                        },
                    }
                ),
            }
        ],
    )

    assert "Über Oli" in message
    assert "- Oli wohnt in KÃ¶ln Stammheim." in message
    assert "- Oli heiÃŸt Oliver Schwab." in message
    assert "Chris gier liebt star wars" not in message
    assert "Chris gier liebt kimchi" not in message


def test_memory_read_fallback_v2_builds_pet_overview_summary():
    message = _build_memory_read_fallback_response_v2(
        "was wei\u00dft du \u00fcber olis haustiere?",
        [
            {
                "name": "memory.read",
                "_skill_id": "memory.read",
                "content": json.dumps(
                    {
                        "status": "ok",
                        "data": {
                            "memories": [
                                {"fact": "Oliver Schwab hat einen Hund namens tasso."},
                                {"fact": "Hund Tasso ist ein podenco."},
                                {"fact": "Hund Tasso frisst gerne thunfisch."},
                                {"fact": "Oliver Schwab hat eine Katze namens garfield."},
                                {"fact": "Katze Garfield mag Thunfisch \u00fcberhaupt nicht."},
                                {"fact": "Aber garfield mag keinen thunfisch."},
                            ]
                        },
                    }
                ),
            }
        ],
    )

    assert message.startswith("\u00dcber Olis Haustiere wei\u00df ich:")
    assert "Olis Haustiere" in message
    assert "Tasso (Hund)" in message
    assert "ist ein podenco" in message
    assert "frisst gerne thunfisch" in message
    assert "Garfield (Katze)" in message
    assert "mag Thunfisch \u00fcberhaupt nicht" in message
    assert "Garfield mag keinen thunfisch" not in message


def test_memory_read_force_fallback_for_pet_overview_query():
    assert _should_force_memory_read_fallback(
        "was wei\u00dft du \u00fcber olis haustiere?",
        [
            {
                "name": "memory.read",
                "_skill_id": "memory.read",
                "content": json.dumps(
                    {
                        "status": "ok",
                        "data": {
                            "memories": [
                                {"fact": "Olis katze heißt garfield."},
                                {"fact": "Garfield mag keinen thunfisch."},
                            ]
                        },
                    }
                ),
            }
        ],
    )


def test_memory_read_force_fallback_for_contact_recall_query():
    assert _should_force_memory_read_fallback(
        "Was weißt du über Chris Gier?",
        [
            {
                "name": "memory.read",
                "_skill_id": "memory.read",
                "content": json.dumps(
                    {
                        "status": "ok",
                        "data": {
                            "memories": [
                                {"fact": "Chris Gier liebt Kimchi."},
                                {"fact": "Chris Gier ist Vegetarier."},
                            ]
                        },
                    },
                    ensure_ascii=False,
                ),
            }
        ],
    )


def test_memory_write_fallback_confirms_address_book_contact_apply():
    message = _build_memory_write_fallback_response(
        [
            {
                "name": "memory.write",
                "_skill_id": "memory.write",
                "_arguments_json": {"fact": "Chris Gier liebt Star Wars und Kimchi."},
                "content": json.dumps(
                    {
                        "status": "ok",
                        "data": {
                            "operation": "saved",
                            "contact_proposal": {"status": "applied"},
                        },
                    }
                ),
            }
        ],
    )

    assert "lokalen Gedächtnis und im Adressbuch" in message
    assert "Chris Gier liebt Star Wars und Kimchi" in message


def test_memory_write_fallback_confirms_when_contact_fact_is_already_known():
    message = _build_memory_write_fallback_response(
        [
            {
                "name": "memory.write",
                "_skill_id": "memory.write",
                "_arguments_json": {"fact": "Oliver Schwab hat einen Hund."},
                "content": json.dumps(
                    {
                        "status": "ok",
                        "data": {
                            "operation": "saved",
                            "contact_proposal": {
                                "status": "ignored",
                                "reason": "already_applied",
                                "known_fact_summary": "den Hund Tasso, ein podenco",
                            },
                        },
                    }
                ),
            }
        ],
    )

    assert "bereits aus dem Adressbuch" in message
    assert "Hund Tasso" in message
    assert "podenco" in message


def test_memory_write_force_fallback_for_applied_contact_update():
    assert _should_force_memory_write_fallback(
        [
            {
                "name": "memory.write",
                "_skill_id": "memory.write",
                "content": json.dumps(
                    {
                        "status": "ok",
                        "data": {
                            "operation": "saved",
                            "contact_proposal": {"status": "applied"},
                        },
                    }
                ),
            }
        ]
    )


def test_memory_write_force_fallback_for_already_known_contact_fact():
    assert _should_force_memory_write_fallback(
        [
            {
                "name": "memory.write",
                "_skill_id": "memory.write",
                "content": json.dumps(
                    {
                        "status": "ok",
                        "data": {
                            "operation": "saved",
                            "contact_proposal": {
                                "status": "ignored",
                                "reason": "already_applied",
                            },
                        },
                    }
                ),
            }
        ]
    )
