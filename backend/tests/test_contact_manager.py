from unittest.mock import AsyncMock, patch

import pytest
from backend.data import contact_schemas, crud, models
from backend.services import contact_manager
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
