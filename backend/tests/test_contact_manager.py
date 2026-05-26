from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from backend.services.contact_manager import extract_and_save_contact


@pytest.mark.asyncio
async def test_extract_and_save_contact_no_name_error():
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

        # Mock the database session to prevent actual DB operations
        with patch("backend.data.database.get_db") as mock_get_db:
            mock_db_session = MagicMock()

            def db_generator_mock():
                yield mock_db_session

            mock_get_db.return_value = db_generator_mock()

            # Mock crud.create_contact
            with patch(
                "backend.data.crud.create_contact", new_callable=AsyncMock
            ) as mock_create_contact:
                mock_create_contact.return_value = AsyncMock(id=1, name="Test Contact")

                # Mock crud.search_contacts_by_name
                with patch(
                    "backend.data.crud.search_contacts_by_name", return_value=[]
                ) as mock_search_contacts:
                    # Call the function that previously raised NameError
                    await extract_and_save_contact(
                        text_block="Some text with contact info",
                        api_key="dummy_key",
                        provider="gemini",
                        model="gemini-3-flash-preview",
                    )
                    # If no NameError is raised, the test passes
                    assert mock_call_llm.called
                    assert mock_create_contact.called
                    assert mock_search_contacts.called
