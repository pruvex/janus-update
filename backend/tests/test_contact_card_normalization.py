import pytest

from backend.data import crud, models
from backend.data import contact_schemas
from backend.tools.memory_tools import handle_memory_write


def test_contact_normalization_semantically_dedupes_preferences_and_details(db_session):
    created = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Chris Gier",
            nickname="Cris",
            preferences=[
                "star wars",
                "Chris ist ein grosser star-wars-fan",
                "star-wars-modelle",
                "vegetarisches essen",
            ],
            personal_details=[
                "vegetarier",
                "Chris mag star wars.",
            ],
            category="Privat",
        ),
    )
    assert created is not None

    loaded = crud.get_contact(db_session, created.id)

    assert loaded is not None
    assert loaded.preferences == ["star wars", "star wars modelle bauen"]
    assert loaded.personal_details == ["vegetarier"]


def test_contact_normalization_moves_residence_detail_into_address_and_keeps_real_details(db_session):
    created = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            address=None,
            personal_details=[
                "wohnt in Köln Stammheim",
                "vegetarier",
            ],
            category="Privat",
        ),
    )
    assert created is not None

    loaded = crud.get_contact(db_session, created.id)

    assert loaded is not None
    assert loaded.address == "Köln Stammheim"
    assert loaded.personal_details == ["vegetarier"]


def test_contact_normalization_moves_residence_note_into_address_and_keeps_other_notes(db_session):
    created = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            address=None,
            personal_details=["vegetarier"],
            notes="wohnt in Köln-Stammheim\nHat einen Hund",
            category="Privat",
        ),
    )
    assert created is not None

    loaded = crud.get_contact(db_session, created.id)

    assert loaded is not None
    assert loaded.address == "Köln Stammheim"
    assert loaded.personal_details == ["vegetarier"]
    assert loaded.notes == "Hat einen Hund"


def test_contact_normalization_strips_trailing_quote_and_parenthesis_from_address(db_session):
    created = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            address='köln stammheim“)',
            category="Privat",
        ),
    )
    assert created is not None

    loaded = crud.get_contact(db_session, created.id)

    assert loaded is not None
    assert loaded.address == "köln stammheim"


def test_contact_normalization_merges_generic_and_named_pet_details(db_session):
    created = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            personal_details=[
                "hat einen Hund",
                "Olis hund heißt tasso",
                "Oli hat auch eine katze",
                "hat eine Katze",
            ],
            category="Privat",
        ),
    )
    assert created is not None

    loaded = crud.get_contact(db_session, created.id)

    assert loaded is not None
    assert loaded.personal_details == ["hat einen Hund namens tasso", "hat eine Katze"]


def test_contact_normalization_accepts_question_mark_pet_name_variant(db_session):
    created = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            personal_details=[
                "hat eine Katze",
                "Olis katze hei?t garfield",
            ],
            category="Privat",
        ),
    )
    assert created is not None

    loaded = crud.get_contact(db_session, created.id)

    assert loaded is not None
    assert loaded.personal_details == ["hat eine Katze namens garfield"]


def test_contact_normalization_merges_raw_pet_trait_into_owner_facing_detail(db_session):
    created = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            personal_details=[
                "hat einen Hund namens tasso",
                "Tasso ist ein podenco",
                "Hund Tasso ist ein podenco",
            ],
            category="Privat",
        ),
    )
    assert created is not None

    loaded = crud.get_contact(db_session, created.id)

    assert loaded is not None
    assert loaded.personal_details == [
        "hat einen Hund namens tasso",
        "Hund Tasso ist ein podenco",
    ]


def test_contact_normalization_collapses_pet_wording_variants_and_redundant_named_cat_lines(db_session):
    created = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            personal_details=[
                "hat einen Hund namens tasso",
                "Hund Tasso frisst gerne thunfisch",
                "Hund Tasso frisst gern thunfisch",
                "Hund Tasso frisst gerne hunfisch",
                "hat eine Katze namens garfield",
                "Garfield mag Thunfisch \u00fcberhaupt nicht",
                "Katze Garfield ist die katze von oli",
                "Katze Garfield ist eine katze",
            ],
            category="Privat",
        ),
    )
    assert created is not None

    loaded = crud.get_contact(db_session, created.id)

    assert loaded is not None
    assert loaded.personal_details == [
        "hat einen Hund namens tasso",
        "Hund Tasso frisst gerne thunfisch",
        "hat eine Katze namens garfield",
        "Katze Garfield mag Thunfisch \u00fcberhaupt nicht",
    ]


@pytest.mark.asyncio
async def test_contact_normalization_recovers_missing_pet_dislike_from_memory(db_session):
    created = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            preferences=[],
            personal_details=[
                "hat einen Hund namens tasso",
                "hat eine Katze namens garfield",
                "Hund Tasso ist ein podenco",
                "Hund Tasso frisst gerne thunfisch",
            ],
            category="Privat",
        ),
    )
    assert created is not None

    chat = models.Chat(title="Pet recovery normalization")
    db_session.add(chat)
    db_session.commit()
    chat_id = chat.id
    write_result = await handle_memory_write(
        params={
            "fact": "Garfield mag Thunfisch überhaupt nicht",
            "subject_name": "Garfield",
            "category": "Haustier-Details",
        },
        db=db_session,
        chat_id=chat_id,
        original_user_text="garfield mag thunfisch überhaupt nicht",
    )
    if hasattr(write_result, "model_dump"):
        write_result = write_result.model_dump()
    assert write_result["status"] == "ok"

    db_contact = db_session.query(models.Contact).filter(models.Contact.id == created.id).first()
    assert db_contact is not None
    db_contact.preferences = ["thunfisch überhaupt nicht"]
    db_contact.personal_details = [
        "hat einen Hund namens tasso",
        "hat eine Katze namens garfield",
        "Hund Tasso ist ein podenco",
        "Hund Tasso frisst gerne thunfisch",
    ]
    db_session.commit()

    loaded = crud.get_contact(db_session, created.id)

    assert loaded is not None
    assert loaded.preferences == []
    assert loaded.personal_details == [
        "hat einen Hund namens tasso",
        "hat eine Katze namens garfield",
        "Hund Tasso ist ein podenco",
        "Hund Tasso frisst gerne thunfisch",
        "Katze Garfield mag Thunfisch überhaupt nicht",
    ]
