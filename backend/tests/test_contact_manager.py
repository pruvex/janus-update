import json
from unittest.mock import AsyncMock, patch

import pytest
from backend.data import contact_schemas, crud, models
from backend.services.chat.context_builder import ContextBuilder
from backend.services import contact_manager
from backend.services import memory_extractor
from backend.services.memory import save_memory_snippet
from backend.services.tool_executor import ToolExecutor
from backend.tools.memory_tools import handle_memory_write


def _db_gen(db_session):
    def _factory():
        yield db_session

    return _factory


@pytest.mark.asyncio
async def test_extract_and_save_contact_stages_private_contact_proposal(db_session):
    contact_manager._clear_pending_contact_proposals_for_tests()
    with patch("backend.services.llm_gateway.call_llm", new_callable=AsyncMock) as mock_call_llm:
        mock_call_llm.return_value = {
            "type": "text",
            "text": """
            [
              {
                "name": "Test Contact",
                "address": "123 Test St",
                "phone": "555-1234",
                "email": "test@example.com",
                "website": "www.test.com",
                "category": "Private",
                "notes": "Some notes"
              }
            ]
            """,
            "usage": {},
            "cost": {},
        }

        with patch(
            "backend.services.contact_manager.database.get_db_sync",
            side_effect=_db_gen(db_session),
        ):
            result = await contact_manager.extract_and_save_contact(
                text_block="Some text with contact info",
                api_key="dummy_key",
                provider="gemini",
                model="gemini-3-flash-preview",
                chat_id=77,
            )

    assert result["proposals_staged"] == 1
    assert result["proposal_id"]
    assert contact_manager.get_pending_contact_proposal(77) is not None
    assert crud.get_contacts(db_session, limit=20) == []


@pytest.mark.asyncio
async def test_extract_and_save_contact_routes_private_residence_note_into_address(db_session):
    contact_manager._clear_pending_contact_proposals_for_tests()
    with patch("backend.services.llm_gateway.call_llm", new_callable=AsyncMock) as mock_call_llm:
        mock_call_llm.return_value = {
            "type": "text",
            "text": """
            [
              {
                "name": "Oliver Schwab",
                "category": "Private",
                "notes": "wohnt in KÃ¶ln-Stammheim"
              }
            ]
            """,
            "usage": {},
            "cost": {},
        }

        with patch(
            "backend.services.contact_manager.database.get_db_sync",
            side_effect=_db_gen(db_session),
        ):
            result = await contact_manager.extract_and_save_contact(
                text_block="Oliver Schwab wohnt in KÃ¶ln-Stammheim",
                api_key="dummy_key",
                provider="gemini",
                model="gemini-3-flash-preview",
                chat_id=78,
            )
            confirm_result = contact_manager.confirm_pending_contact_proposal(78)

    created = crud.search_contacts_by_name(db_session, "Oliver Schwab")[0]
    assert result["proposals_staged"] == 1
    assert confirm_result["status"] == "applied"
    assert created.address == "KÃ¶ln Stammheim"
    assert created.notes is None


@pytest.mark.asyncio
async def test_extract_and_save_contact_routes_existing_contact_residence_update_into_address_without_note_residue(
    db_session,
):
    contact_manager._clear_pending_contact_proposals_for_tests()
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            category="Privat",
            contact_type="private_person",
            personal_details=["vegetarier"],
        ),
    )
    assert existing is not None

    with patch("backend.services.llm_gateway.call_llm", new_callable=AsyncMock) as mock_call_llm:
        mock_call_llm.return_value = {
            "type": "text",
            "text": """
            [
              {
                "name": "Oliver Schwab",
                "category": "Private",
                "notes": "wohnt in 'KÃƒÂ¶ln-Stammheim'."
              }
            ]
            """,
            "usage": {},
            "cost": {},
        }

        with patch(
            "backend.services.contact_manager.database.get_db_sync",
            side_effect=_db_gen(db_session),
        ):
            staged = await contact_manager.extract_and_save_contact(
                text_block="Oliver Schwab wohnt in 'KÃƒÂ¶ln-Stammheim'.",
                api_key="dummy_key",
                provider="gemini",
                model="gemini-3-flash-preview",
                chat_id=79,
            )
            pending = contact_manager.get_pending_contact_proposal(79)
            confirm_result = contact_manager.confirm_pending_contact_proposal(79)

    refreshed = crud.get_contact(db_session, existing.id)
    proposals = crud.list_contact_proposals(db_session, contact_id=existing.id)

    assert staged["proposals_staged"] == 1
    assert pending is not None
    assert pending["items"][0]["proposal_type"] == "update"
    assert pending["items"][0]["payload"]["address"] == "KÃƒÂ¶ln Stammheim"
    assert "notes" not in pending["items"][0]["payload"]
    assert confirm_result["status"] == "applied"
    assert refreshed is not None
    assert refreshed.address == "KÃƒÂ¶ln Stammheim"
    assert refreshed.personal_details == ["vegetarier"]
    assert proposals[0]["payload_json"]["payload"]["address"] == "KÃƒÂ¶ln Stammheim"


@pytest.mark.asyncio
async def test_rejected_contact_proposal_is_suppressed_until_new_evidence(db_session):
    contact_manager._clear_pending_contact_proposals_for_tests()
    with patch("backend.services.llm_gateway.call_llm", new_callable=AsyncMock) as mock_call_llm:
        mock_call_llm.return_value = {
            "type": "text",
            "text": """
            [
              {
                "name": "Max Beispiel",
                "phone": "555-0101",
                "category": "Private"
              }
            ]
            """,
            "usage": {},
            "cost": {},
        }

        with patch(
            "backend.services.contact_manager.database.get_db_sync",
            side_effect=_db_gen(db_session),
        ):
            first = await contact_manager.extract_and_save_contact(
                text_block="Bitte merke dir Max Beispiel 555-0101",
                api_key="dummy_key",
                provider="gemini",
                model="gemini-3-flash-preview",
                chat_id=91,
            )
            reject_result = contact_manager.reject_pending_contact_proposal(91)
            second = await contact_manager.extract_and_save_contact(
                text_block="Bitte merke dir Max Beispiel 555-0101",
                api_key="dummy_key",
                provider="gemini",
                model="gemini-3-flash-preview",
                chat_id=91,
            )

    assert first["proposals_staged"] == 1
    assert reject_result["status"] == "rejected"
    assert second["proposals_staged"] == 0
    assert second["suppressed"] == 1
    assert contact_manager.get_pending_contact_proposal(91) is None


@pytest.mark.asyncio
async def test_existing_contact_becomes_update_proposal_until_confirmed(db_session):
    contact_manager._clear_pending_contact_proposals_for_tests()
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Anna Beispiel",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    with patch("backend.services.llm_gateway.call_llm", new_callable=AsyncMock) as mock_call_llm:
        mock_call_llm.return_value = {
            "type": "text",
            "text": """
            [
              {
                "name": "Anna Beispiel",
                "phone": "555-0202",
                "category": "Private"
              }
            ]
            """,
            "usage": {},
            "cost": {},
        }

        with patch(
            "backend.services.contact_manager.database.get_db_sync",
            side_effect=_db_gen(db_session),
        ):
            staged = await contact_manager.extract_and_save_contact(
                text_block="Anna Beispiel hat jetzt die Nummer 555-0202",
                api_key="dummy_key",
                provider="gemini",
                model="gemini-3-flash-preview",
                chat_id=15,
            )
            before_confirm = crud.get_contact(db_session, existing.id)
            confirm_result = contact_manager.confirm_pending_contact_proposal(15)
            after_confirm = crud.get_contact(db_session, existing.id)

    assert staged["proposals_staged"] == 1
    assert before_confirm.phone is None
    assert confirm_result["status"] == "applied"
    assert after_confirm.phone == "555-0202"


@pytest.mark.asyncio
async def test_near_match_contact_is_staged_as_merge_proposal(db_session):
    contact_manager._clear_pending_contact_proposals_for_tests()
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Anna Beispiel",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    with patch("backend.services.llm_gateway.call_llm", new_callable=AsyncMock) as mock_call_llm:
        mock_call_llm.return_value = {
            "type": "text",
            "text": """
            [
              {
                "name": "Anna Beispel",
                "phone": "555-3333",
                "category": "Private"
              }
            ]
            """,
            "usage": {},
            "cost": {},
        }

        with patch(
            "backend.services.contact_manager.database.get_db_sync",
            side_effect=_db_gen(db_session),
        ):
            staged = await contact_manager.extract_and_save_contact(
                text_block="Anna Beispel hat jetzt die Nummer 555-3333",
                api_key="dummy_key",
                provider="gemini",
                model="gemini-3-flash-preview",
                chat_id=151,
            )

    proposals = crud.list_contact_proposals(db_session, contact_id=existing.id)
    pending = contact_manager.get_pending_contact_proposal(151)
    refreshed = crud.get_contact(db_session, existing.id)

    assert staged["proposals_staged"] == 1
    assert staged["suppressed"] == 0
    assert len(proposals) == 1
    assert proposals[0]["proposal_type"] == "merge"
    assert proposals[0]["contact_id"] == existing.id
    assert proposals[0]["payload_json"]["existing_name"] == "Anna Beispiel"
    assert proposals[0]["payload_json"]["payload"]["phone"] == "555-3333"
    assert pending is not None
    assert "Merge pruefen" in staged["user_message"]
    assert refreshed.phone is None


@pytest.mark.asyncio
async def test_confirmed_contact_proposal_syncs_confirmed_contact_knowledge_to_memory(db_session):
    contact_manager._clear_pending_contact_proposals_for_tests()
    with patch("backend.services.llm_gateway.call_llm", new_callable=AsyncMock) as mock_call_llm:
        mock_call_llm.return_value = {
            "type": "text",
            "text": """
            [
              {
                "name": "Clara Kontakt",
                "email": "clara@example.com",
                "category": "Private"
              }
            ]
            """,
            "usage": {},
            "cost": {},
        }

        with patch(
            "backend.services.contact_manager.database.get_db_sync",
            side_effect=_db_gen(db_session),
        ):
            await contact_manager.extract_and_save_contact(
                text_block="Bitte merke dir Clara Kontakt clara@example.com",
                api_key="dummy_key",
                provider="gemini",
                model="gemini-3-flash-preview",
                chat_id=23,
            )
            confirm_result = contact_manager.confirm_pending_contact_proposal(23)

    created_contact = crud.search_contacts_by_name(db_session, "Clara Kontakt")[0]
    memories = db_session.query(models.Memory).all()

    assert confirm_result["status"] == "applied"
    assert created_contact.memory_sync_status == "synced"
    assert any("clara@example.com" in str(memory.snippet or "") for memory in memories)


def test_confirmed_chat_fact_for_exact_existing_contact_updates_contact_without_pending_proposal(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Christoph Alpha Einzig",
            nickname="Cris",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=42,
        fact_object={
            "fact": "Christoph Alpha Einzig liebt Star Wars",
            "subject_name": "Christoph Alpha Einzig",
            "subject_role": "contact",
            "predicate": "mag",
            "object_value": "Star Wars",
            "category": "Vorlieben",
            "canonical_key": "christoph_alpha_einzig:contact:vorlieben:mag:star_wars",
        },
        source_type="text",
        source_metadata={"user_msg": "Christoph Alpha Einzig liebt Star Wars"},
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=42,
    )

    refreshed = crud.get_contact(db_session, existing.id)
    proposals = crud.list_contact_proposals(db_session, contact_id=existing.id)

    assert result["status"] == "applied"
    assert result["proposals_staged"] == 0
    assert refreshed is not None
    assert refreshed.preferences == ["star wars"]
    assert refreshed.proposal_status == "confirmed"
    assert refreshed.proposal_source_context == "direct_context"
    assert refreshed.proposal_last_outcome == "applied_from_confirmed_chat_fact"
    assert proposals == []


def test_confirmed_chat_fact_matches_existing_contact_via_nickname_alias_but_stages_political_dislike(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Christoph Gier",
            nickname="Cris",
            category="Privat",
            contact_type="private_person",
            preferences=["vegetarier", "star wars"],
        ),
    )
    assert existing is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=43,
        fact_object={
            "fact": "Chris hasst die AfD",
            "subject_name": "Chris",
            "subject_role": "contact",
            "predicate": "hasst",
            "object_value": "die AfD",
            "category": "Abneigungen",
            "canonical_key": "chris:contact:abneigungen:hasst:die_afd",
        },
        source_type="text",
        source_metadata={"user_msg": "Chris hasst die AfD"},
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=43,
    )

    refreshed = crud.get_contact(db_session, existing.id)
    proposals = crud.list_contact_proposals(db_session, contact_id=existing.id)

    assert result["proposals_staged"] == 1
    assert refreshed is not None
    assert refreshed.dislikes in (None, [])
    assert refreshed.proposal_status == "pending"
    assert refreshed.proposal_source_context == "memory_sync"
    assert refreshed.proposal_last_outcome == "suggested_from_memory"
    assert len(proposals) == 1
    assert proposals[0]["proposal_type"] == "memory_contact_update"
    assert proposals[0]["payload_json"]["payload"]["dislikes"] == ["die afd"]


def test_confirmed_contact_preference_from_garden_sentence_updates_existing_contact(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Christoph Gier",
            nickname="Cris",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=44,
        fact_object={
            "fact": "Chris verbringt gerne Zeit im Garten",
            "subject_name": "Chris",
            "subject_role": "contact",
            "predicate": "verbringt_gerne_zeit",
            "object_value": "Garten",
            "category": "Vorlieben",
            "canonical_key": "chris:vorlieben:verbringt_gerne_zeit:garten",
        },
        source_type="text",
        source_metadata={"user_msg": "der chris verbringt gerne zeit im garten"},
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=44,
    )

    refreshed = crud.get_contact(db_session, existing.id)
    proposals = crud.list_contact_proposals(db_session, contact_id=existing.id)

    assert result["status"] == "applied"
    assert result["proposals_staged"] == 0
    assert refreshed is not None
    assert refreshed.preferences == ["zeit im garten"]
    assert proposals == []


def test_confirmed_contact_hobby_sentence_updates_existing_contact(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Nathan Raimann",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=46,
        fact_object={
            "fact": "Nathan spielt gerne League of Legends",
            "subject_name": "Nathan",
            "subject_role": "contact",
            "predicate": "spielt_gerne",
            "object_value": "League of Legends",
            "category": "Vorlieben",
            "canonical_key": "nathan:vorlieben:spielt_gerne:league_of_legends",
        },
        source_type="text",
        source_metadata={"user_msg": "nathan spielt gerne league of legends"},
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=46,
    )

    refreshed = crud.get_contact(db_session, existing.id)
    proposals = crud.list_contact_proposals(db_session, contact_id=existing.id)

    assert result["status"] == "applied"
    assert result["proposals_staged"] == 0
    assert refreshed is not None
    assert refreshed.preferences == ["league of legends"]
    assert proposals == []


def test_confirmed_contact_dietary_preference_updates_existing_contact(db_session):
    existing = models.Contact(
        name="Christoph Gier",
        nickname="Cris",
        category="Privat",
        contact_type="private_person",
        preferences=["vegetarier", "star wars"],
        personal_details=[],
    )
    db_session.add(existing)
    db_session.commit()
    db_session.refresh(existing)

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=45,
        fact_object={
            "fact": "Chris ist Vegetarier",
            "subject_name": "Chris",
            "subject_role": "contact",
            "predicate": "ist",
            "object_value": "Vegetarier",
            "category": "Vorlieben",
            "canonical_key": "chris:vorlieben:ist:vegetarier",
        },
        source_type="text",
        source_metadata={"user_msg": "Chris ist Vegetarier"},
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=45,
    )

    refreshed = crud.get_contact(db_session, existing.id)
    proposals = crud.list_contact_proposals(db_session, contact_id=existing.id)

    assert result["status"] == "applied"
    assert result["proposals_staged"] == 0
    assert refreshed is not None
    assert refreshed.preferences == ["star wars"]
    assert refreshed.personal_details == ["vegetarier"]
    assert proposals == []


def test_memory_write_contact_fact_without_subject_updates_existing_contact_from_fact_text(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Chris Gier",
            nickname="Chris",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=46,
        fact_object={
            "fact": "Chris Gier liebt Star Wars und Kimchi.",
            "subject_name": None,
            "category": "Vorlieben",
            "canonical_key": "memory:chris_gier_liebt_star_wars_und_kimchi",
        },
        source_type="tool",
        source_metadata={
            "user_msg": "richtig und er liebt star wars und kimchi",
            "contact_sync_trusted": True,
            "contact_sync_origin": "direct_user_utterance",
        },
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=46,
    )

    refreshed = crud.get_contact(db_session, existing.id)
    proposals = crud.list_contact_proposals(db_session, contact_id=existing.id)

    assert result["status"] == "applied"
    assert result["proposals_staged"] == 0
    assert refreshed is not None
    assert refreshed.preferences == ["star wars", "kimchi"]
    assert proposals == []


def test_contact_name_fact_creates_new_contact_and_residence_detail_applies(db_session):
    naming_memory = save_memory_snippet(
        db=db_session,
        chat_id=48,
        fact_object={
            "fact": "Oli heißt Oliver Schwab",
            "subject_name": "Oli",
            "subject_role": "contact",
            "predicate": "heißt",
            "object_value": "Oliver Schwab",
            "category": "Beziehungen",
            "canonical_key": "oli:Beziehungen:heißt:oliver_schwab",
        },
        source_type="text",
        source_metadata={"user_msg": "mein freund oli (oliver schwab) wohnt in köln stammheim"},
    )
    assert naming_memory is not None

    create_result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=naming_memory,
        chat_id=48,
    )

    created = crud.search_contacts_by_name(db_session, "Oliver Schwab")
    assert create_result["status"] == "created"
    assert len(created) == 1
    assert created[0].nickname == "Oli"

    residence_memory = save_memory_snippet(
        db=db_session,
        chat_id=48,
        fact_object={
            "fact": "Oli wohnt in Köln-Stammheim",
            "subject_name": "Oli",
            "subject_role": "contact",
            "predicate": "wohnt_in",
            "object_value": "Köln-Stammheim",
            "category": "Allgemein",
            "canonical_key": "oli:Allgemein:wohnt_in:köln_stammheim",
        },
        source_type="text",
        source_metadata={"user_msg": "mein freund oli (oliver schwab) wohnt in köln stammheim"},
    )
    assert residence_memory is not None

    update_result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=residence_memory,
        chat_id=48,
    )

    refreshed = crud.search_contacts_by_name(db_session, "Oliver Schwab")[0]
    assert update_result["status"] == "applied"
    assert refreshed.address == "Köln Stammheim"
    assert refreshed.personal_details == []


def test_pet_detail_memory_updates_existing_contact_personal_details(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=47,
        fact_object={
            "fact": "Oliver Schwab hat einen Hund.",
            "subject_name": "Oliver Schwab",
            "subject_role": "contact",
            "predicate": "hat",
            "object_value": "Hund",
            "category": "Haustier-Details",
            "canonical_key": "oliver_schwab:contact:haustier_details:hat:hund",
        },
        source_type="tool",
        source_metadata={
            "user_msg": "und er hat einen Hund",
            "contact_sync_trusted": True,
            "contact_sync_origin": "direct_user_utterance",
        },
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=47,
    )

    refreshed = crud.get_contact(db_session, existing.id)

    assert result["status"] == "applied"
    assert refreshed is not None
    assert refreshed.personal_details == ["hat einen Hund"]


def test_pet_detail_memory_with_besitzt_updates_existing_contact_personal_details(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=48,
        fact_object={
            "fact": "Oliver Schwab besitzt einen Hund.",
            "subject_name": "Oliver Schwab",
            "subject_role": "contact",
            "predicate": "besitzt",
            "object_value": "Hund",
            "category": "Haustier-Details",
            "canonical_key": "oliver_schwab:contact:haustier_details:besitzt:hund",
        },
        source_type="tool",
        source_metadata={
            "user_msg": "und er besitzt einen Hund",
            "contact_sync_trusted": True,
            "contact_sync_origin": "direct_user_utterance",
        },
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=48,
    )

    refreshed = crud.get_contact(db_session, existing.id)

    assert result["status"] == "applied"
    assert refreshed is not None
    assert refreshed.personal_details == ["hat einen Hund"]


def test_pet_detail_evidence_text_does_not_backfill_residence_address():
    extracted = contact_manager._extract_contact_updates_from_memory_payload(
        {
            "fact": 'Der User: "und er hat einen Hund" (im Kontext von "Oliver Schwab wohnt in KÃ¶ln-Stammheim").',
            "subject_name": "Oliver Schwab",
            "category": "Haustier-Details",
            "predicate": "hat",
            "object_value": "Hund",
        }
    )

    assert extracted["updates"].get("address") is None
    assert extracted["updates"].get("personal_details") == ["hat einen Hund"]


def test_relationship_name_fact_updates_existing_contact_by_unique_first_name(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Nathan Raimann",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=49,
        fact_object={
            "fact": "Nathans Freundin heisst Elena.",
            "subject_name": "Nathan",
            "subject_role": "contact",
            "category": "Beziehungen",
            "canonical_key": "nathan:Beziehungen:freundin_heisst:elena",
        },
        source_type="text",
        source_metadata={"user_msg": "nathans freundin heisst elena"},
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=49,
    )

    refreshed = crud.get_contact(db_session, existing.id)
    synced_facts = [
        json.loads(memory.snippet).get("fact", "")
        for memory in db_session.query(models.Memory).all()
        if str(memory.source_type or "") == "contact_sync"
    ]

    assert result["status"] == "applied"
    assert refreshed is not None
    assert refreshed.personal_details == ["Freundin heisst Elena"]
    assert refreshed.memory_sync_status == "synced"
    assert any("freundin heisst elena" in fact.casefold() for fact in synced_facts)


def test_relationship_named_owner_fact_updates_existing_contact_by_unique_first_name(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Nathan Raimann",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=50,
        fact_object={
            "fact": "Nathan hat eine Freundin namens Elena.",
            "subject_name": "Nathan",
            "subject_role": "contact",
            "category": "Beziehungen",
            "canonical_key": "nathan:Beziehungen:hat_freundin:elena",
        },
        source_type="text",
        source_metadata={"user_msg": "nathan hat eine freundin namens elena"},
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=50,
    )

    refreshed = crud.get_contact(db_session, existing.id)
    synced_facts = [
        json.loads(memory.snippet).get("fact", "")
        for memory in db_session.query(models.Memory).all()
        if str(memory.source_type or "") == "contact_sync"
    ]

    assert result["status"] == "applied"
    assert refreshed is not None
    assert refreshed.personal_details == ["Freundin heisst Elena"]
    assert refreshed.memory_sync_status == "synced"
    assert any("freundin heisst elena" in fact.casefold() for fact in synced_facts)


@pytest.mark.asyncio
async def test_fact_extractor_normalizes_duplicate_contact_name_variants(db_session):
    chat = models.Chat(title="contact-name-dedupe")
    db_session.add(chat)
    db_session.commit()
    db_session.refresh(chat)

    extracted_items = [
        {
            "fact": "Oli heißt Oliver Schwab.",
            "category": "Beziehungen",
            "canonical_key": "oli:Beziehungen:heißt:oliver_schwab",
            "subject_role": "contact",
            "subject_name": "oli",
            "predicate": "heißt",
            "object_value": "oliver schwab",
            "priority": 0.55,
            "ttl": 31536000,
            "tags": ["identity"],
            "memory_type": "TEMPORAL",
            "source_skill": "system.extractor",
            "user_editable": True,
        },
        {
            "fact": "Oli heißt mit vollem Namen Oliver Schwab.",
            "category": "Allgemein",
            "canonical_key": "oli:Allgemein:heisst_voller_name:oliver_schwab",
            "subject_role": "contact",
            "subject_name": "oli",
            "predicate": "heisst_voller_name",
            "object_value": "oliver schwab",
            "priority": 0.55,
            "ttl": 31536000,
            "tags": ["identity"],
            "memory_type": "TEMPORAL",
            "source_skill": "system.extractor",
            "user_editable": True,
        },
    ]

    with patch(
        "backend.services.memory_extractor._resolve_provider_instance",
        return_value=object(),
    ), patch(
        "backend.services.memory_extractor._generate_fact_extraction_items_with_self_healing",
        new_callable=AsyncMock,
    ) as mock_extract, patch(
        "backend.services.memory_extractor.notification_manager.broadcast_refresh",
        new_callable=AsyncMock,
    ):
        mock_extract.return_value = extracted_items
        result = await memory_extractor.extract_and_save_fact_from_interaction(
            db=db_session,
            user_msg="mein freund oli (oliver schwab) wohnt in köln stammheim",
            assistant_msg="Alles klar: Oli (Oliver Schwab) wohnt in Köln-Stammheim.",
            api_key="dummy",
            provider="gemini",
            model_id="gemini-3-flash-preview",
            chat_id=chat.id,
            subject_hint="Oli",
        )

    saved_name_memories = (
        db_session.query(models.Memory)
        .filter(models.Memory.canonical_key == "oli:Allgemein:heisst:oliver_schwab")
        .all()
    )
    created = crud.search_contacts_by_name(db_session, "Oliver Schwab")

    assert len(result) == 2
    assert len(saved_name_memories) == 1
    assert len(created) == 1
    assert created[0].nickname == "Oli"


@pytest.mark.asyncio
async def test_memory_write_legacy_entries_arguments_update_contact(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Chris Gier",
            nickname="Chris",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    executor = ToolExecutor(
        db_session,
        api_key="",
        provider="gemini",
        model="gemini-3-flash-preview",
        additional_context={
            "chat_id": 47,
            "original_user_text": "richtig und er liebt star wars und kimchi",
        },
    )
    result = await executor.execute_tool_call(
        "memory.write",
        {
            "entries": [
                {
                    "text": "Chris Gier liebt Star Wars und Kimchi.",
                    "tags": ["Chris Gier", "Vorlieben"],
                    "priority": 0.8,
                }
            ]
        },
    )

    refreshed = crud.get_contact(db_session, existing.id)
    content = json.loads(result["content"])

    assert content["status"] == "ok"
    assert result["_arguments_json"]["entries"][0]["text"] == "Chris Gier liebt Star Wars und Kimchi."
    assert refreshed is not None
    assert refreshed.preferences == ["star wars", "kimchi"]


@pytest.mark.asyncio
async def test_fact_extractor_syncs_contact_fact_even_when_subject_role_is_missing(db_session):
    chat = models.Chat(title="contact-extractor-sync")
    db_session.add(chat)
    db_session.commit()
    db_session.refresh(chat)

    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Chris Gier",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    extracted_items = [
        {
            "fact": "Chris Gier liebt Kimchi.",
            "category": "Vorlieben",
            "canonical_key": "chris_gier:Vorlieben:liebt:kimchi",
            "subject_role": None,
            "subject_name": "chris gier",
            "predicate": "liebt",
            "object_value": "kimchi",
            "priority": 0.55,
            "ttl": 31536000,
            "tags": ["preference", "personal"],
            "memory_type": "TEMPORAL",
            "source_skill": "system.extractor",
            "user_editable": True,
        }
    ]

    with patch(
        "backend.services.memory_extractor._resolve_provider_instance",
        return_value=object(),
    ), patch(
        "backend.services.memory_extractor._generate_fact_extraction_items_with_self_healing",
        new_callable=AsyncMock,
    ) as mock_extract, patch(
        "backend.services.memory_extractor.notification_manager.broadcast_refresh",
        new_callable=AsyncMock,
    ):
        mock_extract.return_value = extracted_items
        result = await memory_extractor.extract_and_save_fact_from_interaction(
            db=db_session,
            user_msg="richtig und er liebt star wars und kimchi",
            assistant_msg="Was weißt du über Chris Gier?",
            api_key="dummy",
            provider="gemini",
            model_id="gemini-3-flash-preview",
            chat_id=chat.id,
            subject_hint="Chris Gier",
        )

    refreshed = crud.get_contact(db_session, existing.id)

    assert len(result) == 1
    assert result[0]["subject_role"] == "contact"
    assert refreshed is not None
    assert refreshed.preferences == ["kimchi"]


@pytest.mark.asyncio
async def test_fact_extractor_syncs_pet_name_detail_even_when_subject_role_is_missing(db_session):
    chat = models.Chat(title="contact-pet-name-sync")
    db_session.add(chat)
    db_session.commit()
    db_session.refresh(chat)

    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    extracted_items = [
        {
            "fact": "Olis hund heißt tasso",
            "category": "Haustier-Details",
            "canonical_key": "oli:Haustier-Details:hat_hund:tasso",
            "subject_role": None,
            "subject_name": "oli",
            "predicate": "hat_hund",
            "object_value": "tasso",
            "priority": 0.5,
            "ttl": None,
            "tags": ["pet", "identity"],
            "memory_type": "GENERAL",
            "source_skill": "system.extractor",
            "user_editable": True,
        }
    ]

    with patch(
        "backend.services.memory_extractor._resolve_provider_instance",
        return_value=object(),
    ), patch(
        "backend.services.memory_extractor._generate_fact_extraction_items_with_self_healing",
        new_callable=AsyncMock,
    ) as mock_extract, patch(
        "backend.services.memory_extractor.notification_manager.broadcast_refresh",
        new_callable=AsyncMock,
    ):
        mock_extract.return_value = extracted_items
        result = await memory_extractor.extract_and_save_fact_from_interaction(
            db=db_session,
            user_msg="olis hund heißt tasso",
            assistant_msg="Alles klar, ich habe mir das notiert.",
            api_key="dummy",
            provider="gemini",
            model_id="gemini-3-flash-preview",
            chat_id=chat.id,
        )

    refreshed = crud.get_contact(db_session, existing.id)

    assert len(result) == 1
    assert refreshed is not None
    assert refreshed.personal_details == ["hat einen Hund namens tasso"]


@pytest.mark.asyncio
async def test_fact_extractor_syncs_cat_name_detail_even_when_subject_role_is_missing(db_session):
    chat = models.Chat(title="contact-pet-cat-sync")
    db_session.add(chat)
    db_session.commit()
    db_session.refresh(chat)

    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    extracted_items = [
        {
            "fact": "Olis katze heißt garfield",
            "category": "Haustier-Details",
            "canonical_key": "oli:Haustier-Details:hat_katze:garfield",
            "subject_role": None,
            "subject_name": "oli",
            "predicate": "hat_katze",
            "object_value": "garfield",
            "priority": 0.5,
            "ttl": None,
            "tags": ["pet", "identity"],
            "memory_type": "GENERAL",
            "source_skill": "system.extractor",
            "user_editable": True,
        }
    ]

    with patch(
        "backend.services.memory_extractor._resolve_provider_instance",
        return_value=object(),
    ), patch(
        "backend.services.memory_extractor._generate_fact_extraction_items_with_self_healing",
        new_callable=AsyncMock,
    ) as mock_extract, patch(
        "backend.services.memory_extractor.notification_manager.broadcast_refresh",
        new_callable=AsyncMock,
    ):
        mock_extract.return_value = extracted_items
        result = await memory_extractor.extract_and_save_fact_from_interaction(
            db=db_session,
            user_msg="olis katze heißt garfield",
            assistant_msg="Alles klar, ich habe mir das notiert.",
            api_key="dummy",
            provider="gemini",
            model_id="gemini-3-flash-preview",
            chat_id=chat.id,
        )

    refreshed = crud.get_contact(db_session, existing.id)

    assert len(result) == 1
    assert refreshed is not None
    assert refreshed.personal_details == ["hat eine Katze namens garfield"]


def test_pet_detail_memory_prefers_richest_exact_duplicate_contact(db_session):
    primary = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
            address="Köln Stammheim",
            personal_details=["hat einen Hund namens tasso"],
        ),
    )
    duplicate_one = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
        ),
    )
    duplicate_two = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert primary is not None
    assert duplicate_one is not None
    assert duplicate_two is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=52,
        fact_object={
            "fact": "Olis katze heißt garfield",
            "subject_name": "oli",
            "subject_role": None,
            "predicate": "hat_katze",
            "object_value": "garfield",
            "category": "Haustier-Details",
            "canonical_key": "oli:Haustier-Details:hat_katze:garfield",
        },
        source_type="tool",
        source_metadata={
            "user_msg": "olis katze heißt garfield",
            "contact_sync_trusted": True,
            "contact_sync_origin": "direct_user_utterance",
        },
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=52,
    )

    refreshed_primary = crud.get_contact(db_session, primary.id)
    refreshed_duplicate_one = crud.get_contact(db_session, duplicate_one.id)
    refreshed_duplicate_two = crud.get_contact(db_session, duplicate_two.id)

    assert result["status"] == "applied"
    assert refreshed_primary is not None
    assert refreshed_primary.personal_details == [
        "hat einen Hund namens tasso",
        "hat eine Katze namens garfield",
    ]
    assert refreshed_duplicate_one is not None
    assert refreshed_duplicate_one.personal_details == []
    assert refreshed_duplicate_two is not None
    assert refreshed_duplicate_two.personal_details == []


def test_visible_contact_paths_collapse_empty_exact_duplicates_to_richest_contact(db_session):
    primary = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab Sichttest",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
            address="Köln Stammheim",
            personal_details=["hat einen Hund namens tasso"],
        ),
    )
    duplicate_one = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab Sichttest",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
        ),
    )
    duplicate_two = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab Sichttest",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert primary is not None
    assert duplicate_one is not None
    assert duplicate_two is not None

    def _session_override():
        yield db_session

    with patch.object(contact_manager.database, "get_db_sync", _session_override):
        listed = contact_manager.list_contacts()
        searched = contact_manager.search_contacts("Oliver Schwab Sichttest")

    oliver_from_list = [
        contact
        for contact in listed
        if str(contact.name or "").casefold() == "oliver schwab sichttest"
    ]
    oliver_from_search = [
        contact
        for contact in searched
        if str(contact.name or "").casefold() == "oliver schwab sichttest"
    ]

    assert len(oliver_from_list) == 1
    assert len(oliver_from_search) == 1
    assert oliver_from_list[0].id == primary.id
    assert oliver_from_search[0].id == primary.id
    assert oliver_from_list[0].personal_details == ["hat einen Hund namens tasso"]


def test_visible_contact_read_normalizes_live_pet_detail_typo_variant(db_session):
    created = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
            personal_details=[
                "hat einen Hund namens tasso",
                "Hund Tasso frisst gerne thunfisch",
                "Hund Tasso frisst gerne hunfisch",
            ],
        ),
    )
    assert created is not None

    loaded = crud.get_contact(db_session, created.id)

    assert loaded is not None
    assert loaded.personal_details == [
        "hat einen Hund namens tasso",
        "Hund Tasso frisst gerne thunfisch",
    ]


def test_pet_preference_memory_for_named_pet_updates_owner_contact_personal_details(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
            personal_details=["hat einen Hund namens tasso"],
        ),
    )
    assert existing is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=77,
        fact_object={
            "fact": "Tasso frisst gerne thunfisch",
            "subject_name": "tasso",
            "subject_role": "pet",
            "predicate": "frisst_gerne",
            "object_value": "thunfisch",
            "category": "Haustier-Details",
            "canonical_key": "tasso:Haustier-Details:frisst_gerne:thunfisch",
        },
        source_type="tool",
        source_metadata={
            "user_msg": "tasso frisst gerne thunfisch",
            "contact_sync_trusted": True,
            "contact_sync_origin": "direct_user_utterance",
        },
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=77,
    )

    refreshed = crud.get_contact(db_session, existing.id)

    assert result["status"] == "applied"
    assert refreshed is not None
    assert refreshed.personal_details == [
        "hat einen Hund namens tasso",
        "Hund Tasso frisst gerne thunfisch",
    ]


def test_pet_dislike_memory_for_named_pet_updates_owner_contact_personal_details(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
            personal_details=["hat eine Katze namens garfield"],
        ),
    )
    assert existing is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=77,
        fact_object={
            "fact": "Garfield mag Thunfisch \u00fcberhaupt nicht",
            "subject_name": "garfield",
            "subject_role": "pet",
            "predicate": "mag_nicht",
            "object_value": "thunfisch",
            "category": "Vorlieben",
            "canonical_key": "garfield:Vorlieben:mag_nicht:thunfisch",
        },
        source_type="tool",
        source_metadata={
            "user_msg": "garfield mag thunfisch \u00fcberhaupt nicht",
            "contact_sync_trusted": True,
            "contact_sync_origin": "direct_user_utterance",
        },
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=77,
    )

    refreshed = crud.get_contact(db_session, existing.id)

    assert result["status"] == "applied"
    assert refreshed is not None
    assert refreshed.dislikes == []
    assert refreshed.personal_details == [
        "hat eine Katze namens garfield",
        "Katze Garfield mag thunfisch \u00fcberhaupt nicht",
    ]


def test_pet_preference_memory_uses_pet_identity_memory_when_named_pet_not_yet_in_contact(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
            personal_details=["hat einen Hund"],
        ),
    )
    assert existing is not None

    owner_pet_memory = save_memory_snippet(
        db=db_session,
        chat_id=78,
        fact_object={
            "fact": "Olis hund heißt tasso",
            "subject_name": "oli",
            "subject_role": None,
            "predicate": "hat_hund",
            "object_value": "tasso",
            "category": "Haustier-Details",
            "canonical_key": "oli:Haustier-Details:hat_hund:tasso",
        },
        source_type="tool",
        source_metadata={
            "user_msg": "olis hund heißt tasso",
            "contact_sync_trusted": True,
            "contact_sync_origin": "direct_user_utterance",
        },
    )
    assert owner_pet_memory is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=78,
        fact_object={
            "fact": "Tasso frisst gerne thunfisch",
            "subject_name": "tasso",
            "subject_role": "pet",
            "predicate": "frisst_gerne",
            "object_value": "thunfisch",
            "category": "Haustier-Details",
            "canonical_key": "tasso:Haustier-Details:frisst_gerne:thunfisch",
        },
        source_type="tool",
        source_metadata={
            "user_msg": "tasso frisst gerne thunfisch",
            "contact_sync_trusted": True,
            "contact_sync_origin": "direct_user_utterance",
        },
    )
    assert saved_memory is not None

    helper_match = contact_manager._find_contact_by_pet_memory(db_session, "tasso")
    assert helper_match["primary"] is not None
    assert helper_match["mode"] == "exact"
    assert helper_match["pet_type"] == "hund"

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=78,
    )

    refreshed = crud.get_contact(db_session, existing.id)

    assert result["status"] == "applied"
    assert refreshed is not None
    assert refreshed.personal_details == [
        "hat einen Hund",
        "Hund Tasso frisst gerne thunfisch",
    ]


def test_pet_trait_memory_for_named_pet_keeps_single_owner_facing_detail(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
            personal_details=["hat einen Hund namens tasso"],
        ),
    )
    assert existing is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=79,
        fact_object={
            "fact": "Tasso ist ein podenco",
            "subject_name": "tasso",
            "subject_role": "pet",
            "predicate": "ist_rasse",
            "object_value": "podenco",
            "category": "Haustier-Details",
            "canonical_key": "tasso:Haustier-Details:ist_rasse:podenco",
        },
        source_type="tool",
        source_metadata={
            "user_msg": "olis hund tasso ist ein podenco",
            "contact_sync_trusted": True,
            "contact_sync_origin": "direct_user_utterance",
        },
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=79,
    )

    refreshed = crud.get_contact(db_session, existing.id)

    assert result["status"] == "applied"
    assert refreshed is not None
    assert refreshed.personal_details == [
        "hat einen Hund namens tasso",
        "Hund Tasso ist ein podenco",
    ]


def test_pet_preference_memory_without_subject_role_still_updates_owner_contact(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
            personal_details=["hat einen Hund namens tasso"],
        ),
    )
    assert existing is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=80,
        fact_object={
            "fact": "Tasso frisst gerne thunfisch",
            "subject_name": "tasso",
            "subject_role": None,
            "predicate": "frisst_gerne",
            "object_value": "thunfisch",
            "category": "Vorlieben",
            "canonical_key": "tasso:Vorlieben:frisst_gerne:thunfisch",
        },
        source_type="text",
        source_metadata={"user_msg": "tasso frisst gerne thunfisch"},
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=80,
    )

    refreshed = crud.get_contact(db_session, existing.id)

    assert result["status"] == "applied"
    assert refreshed is not None
    assert refreshed.preferences == []
    assert refreshed.personal_details == [
        "hat einen Hund namens tasso",
        "Hund Tasso frisst gerne thunfisch",
    ]


def test_live_encrypted_pet_preference_memory_uses_canonical_key_for_owner_contact(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
            personal_details=["hat einen Hund namens tasso"],
        ),
    )
    assert existing is not None

    saved_memory = models.Memory(
        chat_id=80,
        snippet="b'gAAAA_live_encrypted_payload'",
        canonical_key="tasso:Vorlieben:frisst_gern:thunfisch",
        category="Vorlieben",
        source_type="text",
        source_metadata={"user_msg": "tasso frisst gerne thunfisch"},
        tags=["personal", "preference"],
        source_skill="system.extractor",
        user_editable=True,
    )
    db_session.add(saved_memory)
    db_session.commit()
    db_session.refresh(saved_memory)

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=80,
    )

    refreshed = crud.get_contact(db_session, existing.id)

    assert result["status"] == "applied"
    assert refreshed is not None
    assert refreshed.preferences == []
    assert refreshed.personal_details == [
        "hat einen Hund namens tasso",
        "Hund Tasso frisst gerne thunfisch",
    ]


def test_pet_trait_memory_without_subject_role_still_updates_owner_contact(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
            personal_details=["hat einen Hund namens tasso"],
        ),
    )
    assert existing is not None

    saved_memory = save_memory_snippet(
        db=db_session,
        chat_id=81,
        fact_object={
            "fact": "Tasso ist ein podenco",
            "subject_name": "tasso",
            "subject_role": None,
            "predicate": "ist_rasse",
            "object_value": "podenco",
            "category": "Haustier-Details",
            "canonical_key": "tasso:Haustier-Details:ist_rasse:podenco",
        },
        source_type="text",
        source_metadata={"user_msg": "olis hund tasso ist ein podenco"},
    )
    assert saved_memory is not None

    result = contact_manager.stage_contact_update_from_memory(
        db_session,
        memory=saved_memory,
        chat_id=81,
    )

    refreshed = crud.get_contact(db_session, existing.id)

    assert result["status"] == "applied"
    assert refreshed is not None
    assert refreshed.personal_details == [
        "hat einen Hund namens tasso",
        "Hund Tasso ist ein podenco",
    ]


def test_explicit_lead_contact_subject_ignores_pet_led_phrases():
    assert memory_extractor._extract_explicit_lead_contact_subject(
        "olis hund tasso ist ein podenco"
    ) is None
    assert memory_extractor._extract_explicit_lead_contact_subject(
        "olivers katze garfield ist verschmust"
    ) is None


def test_explicit_lead_pet_subject_extracts_named_pet_from_contact_phrase():
    assert memory_extractor._extract_explicit_lead_pet_subject(
        "olis hund tasso ist ein podenco"
    ) == {
        "subject_name": "tasso",
        "subject_role": "pet",
        "subject_type": "dog",
    }
    assert memory_extractor._extract_explicit_lead_pet_subject(
        "olivers katze garfield ist verschmust"
    ) == {
        "subject_name": "garfield",
        "subject_role": "pet",
        "subject_type": "cat",
    }


@pytest.mark.asyncio
async def test_fact_extractor_drops_poisoned_user_identity_on_contact_recall(db_session):
    chat = models.Chat(title="contact-recall-identity-guard")
    db_session.add(chat)
    db_session.commit()
    db_session.refresh(chat)

    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Chris Gier",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    extracted_items = [
        {
            "fact": "Chris Gier liebt Kimchi.",
            "category": "Vorlieben",
            "canonical_key": "chris_gier:Vorlieben:liebt:kimchi",
            "subject_role": None,
            "subject_name": "chris gier",
            "predicate": "liebt",
            "object_value": "kimchi",
            "priority": 0.55,
            "ttl": 31536000,
            "tags": ["preference", "personal"],
            "memory_type": "TEMPORAL",
            "source_skill": "system.extractor",
            "user_editable": True,
        },
        {
            "fact": "Der Nutzer heißt Chris Gier",
            "category": "Physis",
            "canonical_key": "user:physis:heisst:name",
            "subject_role": None,
            "subject_name": "user",
            "predicate": "heißt",
            "object_value": "chris gier",
            "priority": 0.95,
            "ttl": None,
            "tags": ["identity"],
            "memory_type": "CORE",
            "source_skill": "system.extractor",
            "user_editable": True,
        },
    ]

    with patch(
        "backend.services.memory_extractor._resolve_provider_instance",
        return_value=object(),
    ), patch(
        "backend.services.memory_extractor._generate_fact_extraction_items_with_self_healing",
        new_callable=AsyncMock,
    ) as mock_extract, patch(
        "backend.services.memory_extractor.notification_manager.broadcast_refresh",
        new_callable=AsyncMock,
    ):
        mock_extract.return_value = extracted_items
        result = await memory_extractor.extract_and_save_fact_from_interaction(
            db=db_session,
            user_msg="Was weißt du alles über Chris Gier?",
            assistant_msg="Ich habe die Vorlieben für Star Wars und Kimchi ergänzt.",
            api_key="dummy",
            provider="gemini",
            model_id="gemini-3-flash-preview",
            chat_id=chat.id,
            subject_hint="Chris Gier",
        )

    refreshed = crud.get_contact(db_session, existing.id)
    identity_memories = (
        db_session.query(models.Memory)
        .filter(models.Memory.canonical_key == "user:physis:heisst:name")
        .all()
    )

    assert result == []
    assert refreshed is not None
    assert refreshed.preferences == []
    assert identity_memories == []


@pytest.mark.asyncio
async def test_fact_extractor_skips_contact_recall_turn_to_avoid_self_poisoning(db_session):
    chat = models.Chat(title="contact-recall-skip")
    db_session.add(chat)
    db_session.commit()
    db_session.refresh(chat)

    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
            preferences=["die serie the big bang theory"],
            personal_details=["wohnt in Köln Stammheim"],
        ),
    )
    assert existing is not None

    extracted_items = [
        {
            "fact": "Oli mag vegetarisches Essen",
            "category": "Vorlieben",
            "canonical_key": "oli:Vorlieben:mag:vegetarisches_essen",
            "subject_role": "contact",
            "subject_name": "oli",
            "predicate": "mag",
            "object_value": "vegetarisches essen",
            "priority": 0.55,
            "ttl": 31536000,
            "tags": ["preference", "personal"],
            "memory_type": "TEMPORAL",
            "source_skill": "system.extractor",
            "user_editable": True,
        }
    ]

    with patch(
        "backend.services.memory_extractor._resolve_provider_instance",
        return_value=object(),
    ), patch(
        "backend.services.memory_extractor._generate_fact_extraction_items_with_self_healing",
        new_callable=AsyncMock,
    ) as mock_extract, patch(
        "backend.services.memory_extractor.notification_manager.broadcast_refresh",
        new_callable=AsyncMock,
    ):
        mock_extract.return_value = extracted_items
        result = await memory_extractor.extract_and_save_fact_from_interaction(
            db=db_session,
            user_msg="und was mag oli?",
            assistant_msg="Oli mag vegetarisches Essen und Kimchi.",
            api_key="dummy",
            provider="gemini",
            model_id="gemini-3-flash-preview",
            chat_id=chat.id,
            subject_hint="Oli",
        )

    refreshed = crud.get_contact(db_session, existing.id)
    saved_memories = db_session.query(models.Memory).filter(models.Memory.chat_id == chat.id).all()

    assert result == []
    assert mock_extract.await_count == 0
    assert refreshed is not None
    assert refreshed.preferences == ["big bang theory"]
    assert saved_memories == []


@pytest.mark.asyncio
async def test_fact_extractor_skips_relationship_recall_turn_to_avoid_self_poisoning(db_session):
    chat = models.Chat(title="relationship-recall-skip")
    db_session.add(chat)
    db_session.commit()
    db_session.refresh(chat)

    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Nathan Raimann",
            category="Privat",
            contact_type="private_person",
            personal_details=["Freundin heisst Elena"],
        ),
    )
    assert existing is not None

    extracted_items = [
        {
            "fact": "Elena ist die Freundin von Nathan.",
            "category": "Beziehungen",
            "canonical_key": "elena:Beziehungen:ist_freundin_von:nathan",
            "subject_role": "contact",
            "subject_name": "elena",
            "predicate": "ist_freundin_von",
            "object_value": "nathan",
            "priority": 0.55,
            "ttl": 31536000,
            "tags": ["relationship", "personal"],
            "memory_type": "TEMPORAL",
            "source_skill": "system.extractor",
            "user_editable": True,
        }
    ]

    with patch(
        "backend.services.memory_extractor._resolve_provider_instance",
        return_value=object(),
    ), patch(
        "backend.services.memory_extractor._generate_fact_extraction_items_with_self_healing",
        new_callable=AsyncMock,
    ) as mock_extract, patch(
        "backend.services.memory_extractor.notification_manager.broadcast_refresh",
        new_callable=AsyncMock,
    ):
        mock_extract.return_value = extracted_items
        result = await memory_extractor.extract_and_save_fact_from_interaction(
            db=db_session,
            user_msg="wer ist nathans freundin?",
            assistant_msg="Nathans Freundin ist Elena.",
            api_key="dummy",
            provider="gemini",
            model_id="gemini-3-flash-preview",
            chat_id=chat.id,
            subject_hint="Nathan",
        )

    refreshed = crud.get_contact(db_session, existing.id)
    saved_memories = db_session.query(models.Memory).filter(models.Memory.chat_id == chat.id).all()

    assert result == []
    assert mock_extract.await_count == 0
    assert refreshed is not None
    assert refreshed.personal_details == ["Freundin heisst Elena"]
    assert saved_memories == []


@pytest.mark.asyncio
async def test_fact_extractor_preserves_explicit_lead_subject_against_similar_existing_contact(db_session):
    chat = models.Chat(title="lead-subject-guard")
    db_session.add(chat)
    db_session.commit()
    db_session.refresh(chat)

    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    extracted_items = [
        {
            "fact": "Oli liebt Big Bang Theory.",
            "category": "Vorlieben",
            "canonical_key": "oli:Vorlieben:liebt:big_bang_theory",
            "subject_role": "contact",
            "subject_name": "oli",
            "predicate": "liebt",
            "object_value": "big bang theory",
            "priority": 0.55,
            "ttl": 31536000,
            "tags": ["preference", "personal"],
            "memory_type": "TEMPORAL",
            "source_skill": "system.extractor",
            "user_editable": True,
        }
    ]

    with patch(
        "backend.services.memory_extractor._resolve_provider_instance",
        return_value=object(),
    ), patch(
        "backend.services.memory_extractor._generate_fact_extraction_items_with_self_healing",
        new_callable=AsyncMock,
    ) as mock_extract, patch(
        "backend.services.memory_extractor.notification_manager.broadcast_refresh",
        new_callable=AsyncMock,
    ):
        mock_extract.return_value = extracted_items
        result = await memory_extractor.extract_and_save_fact_from_interaction(
            db=db_session,
            user_msg="Olix liebt Big Bang Theory",
            assistant_msg="Alles klar, ich habe mir das notiert.",
            api_key="dummy",
            provider="gemini",
            model_id="gemini-3-flash-preview",
            chat_id=chat.id,
        )

    assert len(result) == 1
    assert result[0]["subject_name"] == "olix"
    assert result[0]["subject_role"] == "contact"

    saved = db_session.query(models.Memory).filter(models.Memory.chat_id == chat.id).all()
    assert len(saved) == 1
    payload = contact_manager._parse_memory_snippet_payload(saved[0].snippet)
    assert payload.get("subject_name") == "olix"
    assert "olix" in str(payload.get("canonical_key") or saved[0].canonical_key).lower()


def test_extract_explicit_lead_subject_supports_contact_hobby_sentence():
    assert (
        memory_extractor._extract_explicit_lead_contact_subject(
            "Nathan spielt gerne League of Legends"
        )
        == "nathan"
    )


def test_contact_read_normalizes_existing_dietary_preference_to_personal_detail(db_session):
    existing = models.Contact(
        name="Christoph Gier",
        nickname="Cris",
        category="Privat",
        contact_type="private_person",
        preferences=["vegetarier", "star wars"],
        personal_details=[],
    )
    db_session.add(existing)
    db_session.commit()
    db_session.refresh(existing)

    loaded = crud.get_contact(db_session, existing.id)
    assert loaded is not None
    assert loaded.preferences == ["star wars"]
    assert loaded.personal_details == ["vegetarier"]

    persisted = db_session.query(models.Contact).filter(models.Contact.id == existing.id).first()
    assert persisted.preferences == ["star wars"]
    assert persisted.personal_details == ["vegetarier"]


def test_address_book_context_resolves_contact_by_nickname_and_includes_preferences(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Christoph Gier",
            nickname="Cris",
            category="Privat",
            contact_type="private_person",
            preferences=["zeit im garten", "star wars"],
            dislikes=["die afd"],
            personal_details=["vegetarier"],
        ),
    )
    assert existing is not None

    address_context = ContextBuilder(db_session)._get_address_book_context("was mag chris?")

    assert "Kontakt: Christoph Gier" in address_context
    assert "Nickname: Cris" in address_context
    assert "Vorlieben: zeit im garten, star wars" in address_context
    assert "Abneigungen: die afd" in address_context
    assert "Details: vegetarier" in address_context


def test_address_book_context_does_not_match_similar_substring_aliases(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            category="Privat",
            contact_type="private_person",
            preferences=["kimchi"],
        ),
    )
    assert existing is not None

    address_context = ContextBuilder(db_session)._get_address_book_context("was mag olix?")

    assert address_context == ""


def test_system_prompt_uses_address_book_contact_without_identity_clarification(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Christoph Gier",
            nickname="Cris",
            category="Privat",
            contact_type="private_person",
            preferences=["zeit im garten", "star wars"],
            dislikes=["die afd"],
            personal_details=["vegetarier"],
        ),
    )
    assert existing is not None

    message = ContextBuilder(db_session).build_system_message(
        active_personality={"name": "Janus", "traits": ["hilfsbereit"], "communication_style": "klar"},
        user_prompt="was wei\u00dft du \u00fcber chris gier?",
    )
    content = message["content"]

    assert "[ADRESSBUCH-KONTAKTE]" in content
    assert "Frage dann NICHT, ob der Nutzer sich selbst oder eine andere Person meint" in content
    assert "Kontakt: Christoph Gier" in content
    assert "Vorlieben: zeit im garten, star wars" in content
    assert "Abneigungen: die afd" in content
    assert "Details: vegetarier" in content


@pytest.mark.asyncio
async def test_enrich_incomplete_contacts_skips_private_contact_type_even_if_category_looks_public(
    db_session,
):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Lena Privat",
            category="Business",
            contact_type="private_person",
        ),
    )
    assert existing is not None

    with patch.object(db_session, "close", return_value=None), patch(
        "backend.services.contact_manager.SessionLocal",
        return_value=db_session,
    ), patch(
        "backend.services.websearch.websearch.execute_websearch_service",
        new_callable=AsyncMock,
    ) as mock_websearch:
        await contact_manager.enrich_incomplete_contacts(
            contact_id=existing.id,
            api_key="dummy_key",
            provider="gemini",
            model="gemini-3-flash-preview",
            text_block="Lena Privat aus Berlin",
        )

    refreshed = crud.get_contact(db_session, existing.id)
    assert refreshed is not None
    assert mock_websearch.await_count == 0
    assert refreshed.phone is None
    assert refreshed.proposal_status == "confirmed"
    assert crud.list_contact_proposals(db_session, contact_id=existing.id) == []


@pytest.mark.asyncio
async def test_enrich_incomplete_contacts_stages_ambiguous_public_match(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Restaurant Evia",
            category="Business",
            contact_type="organization",
        ),
    )
    assert existing is not None

    with patch.object(db_session, "close", return_value=None), patch(
        "backend.services.contact_manager.SessionLocal",
        return_value=db_session,
    ), patch("keyring.get_password", return_value="web-key"), patch(
        "backend.services.contact_manager.main_load_model_catalog",
        return_value={"gemini-3-flash-preview": {"provider": "gemini"}},
    ), patch(
        "backend.services.logging.debug_engine.get_speed_tier_model",
        return_value=("gemini", "gemini-3-flash-preview"),
    ), patch(
        "backend.services.websearch.websearch.execute_websearch_service",
        new_callable=AsyncMock,
    ) as mock_websearch, patch(
        "backend.services.contact_manager._is_ambiguous_result",
        new_callable=AsyncMock,
    ) as mock_ambiguous:
        mock_websearch.return_value = {
            "text": "Evia Restaurant Hamburg, Evia Restaurant Berlin, Evia Restaurant Koeln",
            "urls": ["https://evia.example/a", "https://evia.example/b"],
        }
        mock_ambiguous.return_value = True

        await contact_manager.enrich_incomplete_contacts(
            contact_id=existing.id,
            api_key="dummy_key",
            provider="gemini",
            model="gemini-3-flash-preview",
            text_block="Reserviere bei Restaurant Evia in Berlin",
        )

    refreshed = crud.get_contact(db_session, existing.id)
    proposals = crud.list_contact_proposals(db_session, contact_id=existing.id)

    assert refreshed is not None
    assert refreshed.phone is None
    assert refreshed.proposal_status == "pending"
    assert refreshed.proposal_source_context == "web_enrichment"
    assert refreshed.proposal_last_outcome == "selection_required"
    assert len(proposals) == 1
    assert proposals[0]["proposal_type"] == "public_match_selection"
    assert proposals[0]["status"] == "pending"
    assert proposals[0]["payload_json"]["payload"]["reason"] == "ambiguous_public_match"


@pytest.mark.asyncio
async def test_enrich_incomplete_contacts_keeps_conflicting_public_data_as_proposal(db_session):
    existing = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Praxis Klarblick",
            category="Business",
            contact_type="organization",
            phone="030-111111",
            website="https://klarblick-alt.example",
        ),
    )
    assert existing is not None

    with patch.object(db_session, "close", return_value=None), patch(
        "backend.services.contact_manager.SessionLocal",
        return_value=db_session,
    ), patch("keyring.get_password", return_value="web-key"), patch(
        "backend.services.contact_manager.main_load_model_catalog",
        return_value={"gemini-3-flash-preview": {"provider": "gemini"}},
    ), patch(
        "backend.services.logging.debug_engine.get_speed_tier_model",
        return_value=("gemini", "gemini-3-flash-preview"),
    ), patch(
        "backend.services.websearch.websearch.execute_websearch_service",
        new_callable=AsyncMock,
    ) as mock_websearch, patch(
        "backend.services.contact_manager._is_ambiguous_result",
        new_callable=AsyncMock,
    ) as mock_ambiguous, patch(
        "backend.services.llm_gateway.call_llm",
        new_callable=AsyncMock,
    ) as mock_call_llm:
        mock_websearch.return_value = {
            "text": "Praxis Klarblick Telefon 030-222222 Adresse Marktstrasse 5 E-Mail kontakt@klarblick.de Website https://klarblick-neu.example",
            "urls": ["https://klarblick-neu.example"],
        }
        mock_ambiguous.return_value = False
        mock_call_llm.return_value = {
            "text": '{"phone": "030-222222", "email": "kontakt@klarblick.de", "address": "Marktstrasse 5", "website": "https://klarblick-neu.example"}'
        }

        await contact_manager.enrich_incomplete_contacts(
            contact_id=existing.id,
            api_key="dummy_key",
            provider="gemini",
            model="gemini-3-flash-preview",
            text_block="Praxis Klarblick in Berlin",
        )

    refreshed = crud.get_contact(db_session, existing.id)
    proposals = crud.list_contact_proposals(db_session, contact_id=existing.id)

    assert refreshed is not None
    assert refreshed.phone == "030-111111"
    assert refreshed.website == "https://klarblick-alt.example"
    assert refreshed.email == "kontakt@klarblick.de"
    assert refreshed.address == "Marktstrasse 5"
    assert refreshed.proposal_status == "pending"
    assert refreshed.proposal_source_context == "web_enrichment"
    assert refreshed.proposal_last_outcome == "conflict_requires_confirmation"
    assert len(proposals) == 1
    assert proposals[0]["proposal_type"] == "public_field_conflict"
    assert proposals[0]["payload_json"]["payload"]["conflicts"]["phone"]["suggested_value"] == "030-222222"
    assert proposals[0]["payload_json"]["payload"]["conflicts"]["website"]["suggested_value"] == "https://klarblick-neu.example"
    assert proposals[0]["payload_json"]["payload"]["missing_updates_applied"] == {
        "email": "kontakt@klarblick.de",
        "address": "Marktstrasse 5",
    }


def test_contact_create_schema_normalizes_structured_fields():
    contact = contact_schemas.ContactCreate(
        name="Schema Test",
        preferences="italienisch, ruhige Orte\nEspresso",
        dislikes=["Spam", " ", "Laerm"],
        personal_details=None,
        contact_type=None,
        proposal_status=None,
        memory_sync_status=None,
    )

    assert contact.contact_type == "private_person"
    assert contact.proposal_status == "confirmed"
    assert contact.memory_sync_status == "unlinked"
    assert contact.preferences == ["italienisch", "ruhige Orte", "Espresso"]
    assert contact.dislikes == ["Spam", "Laerm"]
    assert contact.personal_details == []


def test_contact_crud_roundtrip_persists_nickname_and_legacy_fields(db_session):
    created = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Clara Beispiel",
            nickname="Cla",
            personal_details=["Vegetarierin"],
            notes="Hat Allergie gegen Haselnuesse",
            category="Privat",
        ),
    )

    assert created is not None
    assert created.nickname == "Cla"
    assert created.personal_details == ["Vegetarierin"]
    assert created.notes == "Hat Allergie gegen Haselnuesse"

    loaded = crud.get_contact(db_session, created.id)

    assert loaded is not None
    assert loaded.nickname == "Cla"
    assert loaded.personal_details == ["Vegetarierin"]
    assert loaded.notes == "Hat Allergie gegen Haselnuesse"


def test_contact_update_keeps_legacy_fields_while_adding_nickname(db_session):
    created = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Tom Beispiel",
            personal_details=["mag Espresso"],
            notes="Laktoseintoleranz",
            category="Privat",
        ),
    )
    assert created is not None

    updated = crud.update_contact(
        db_session,
        created.id,
        {"nickname": "Tommi"},
    )

    assert updated is not None
    assert updated.nickname == "Tommi"

    loaded = crud.get_contact(db_session, created.id)
    assert loaded is not None
    assert loaded.nickname == "Tommi"
    assert loaded.personal_details == ["mag Espresso"]
    assert loaded.notes == "Laktoseintoleranz"


def test_contact_normalization_dedupes_personal_details_case_insensitive(db_session):
    created = crud.create_contact(
        db_session,
        contact_schemas.ContactCreate(
            name="Oliver Schwab",
            nickname="Oli",
            personal_details=["wohnt in Köln Stammheim", "wohnt in köln stammheim"],
            category="Privat",
        ),
    )
    assert created is not None

    loaded = crud.get_contact(db_session, created.id)

    assert loaded is not None
    assert loaded.address == "Köln Stammheim"
    assert loaded.personal_details == []
