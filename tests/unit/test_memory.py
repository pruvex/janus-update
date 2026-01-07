import pytest
import json
from unittest.mock import AsyncMock, patch
from backend.services.memory_extractor import extract_and_save_fact
from backend.data.schemas import FactExtractionResponse, ExtractedFact, MemoryCategory
from backend.data.database import Memory

@pytest.mark.asyncio
async def test_extraction_and_persistence(db_session):
    """
    Testet den kompletten Flow: String rein -> Mock LLM -> DB Save -> String raus.
    """
    
    # 1. Mock Response vorbereiten (So würde GPT-5 antworten)
    mock_fact_data = ExtractedFact(
        fact="Der Hund heißt Pody.",
        category=MemoryCategory.HAUSTIER_DETAILS,
        type="CORE_DETAIL",
        canonical_key="hat_name|pet:dog|pody",
        subject_role="pet",
        subject_name="pody",
        predicate="heißt",
        object_value="pody",
        evidence="mein hund heißt pody",
        expires_in_hours=None,
        subject_pet_type="dog",
        subject_relative_type=None
    )
    
    mock_response_obj = FactExtractionResponse(facts=[mock_fact_data])
    
    # 2. Den LLM-Provider patchen
    # Wir ersetzen 'llm_gateway.get_provider' durch unsere Attrappe
    with patch("backend.services.llm_gateway.get_provider") as mock_get_provider:
        # Der Mock Provider
        mock_provider_instance = AsyncMock()
        # Wenn generate_structured_response aufgerufen wird, gib unser Mock-Objekt zurück
        mock_provider_instance.generate_structured_response.return_value = (mock_response_obj, {"total_cost": 0.0})
        
        mock_get_provider.return_value = mock_provider_instance
        
        # 3. Action: Die echte Funktion aufrufen
        await extract_and_save_fact(
            db=db_session,
            chat_id=1,
            text_block="Mein Hund heißt Pody",
            main_api_key="fake-key", # Key ist egal, da gemockt
            provider="openai",
            model="gpt-5-nano"
        )
        
    # 4. Assert
    saved_memory = db_session.query(Memory).first()
    assert saved_memory is not None
    
    # FIX: Wir müssen das snippet (JSON) parsen
    data = json.loads(saved_memory.snippet)
    
    assert "Pody" in data["fact"]
    assert data["canonical_key"] == "hat_name|pet:dog|pody"
    assert saved_memory.category == "Haustier-Details"
