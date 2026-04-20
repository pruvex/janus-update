import pytest
import json
import keyring
import os
from sqlalchemy.orm import Session
from backend.data.database import SessionLocal, engine, Base # engine und Base hinzugefügt
from backend.services import memory_extractor

@pytest.mark.asyncio
async def test_memory_gold_standard():
    # NEU: Sicherstellen, dass die Tabellen existieren (erstellt die janus.db neu)
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    api_key = keyring.get_password("Janus-Projekt", "openai")
    
    if not api_key:
        pytest.fail("API Key 'openai' nicht im Keyring gefunden.")

    path = "tests/memory_gold_standard.json"
    with open(path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    for case in test_cases:
        extracted = await memory_extractor.extract_and_save_fact_from_interaction(
            db=db,
            user_msg=case['input_user'],
            assistant_msg=case['input_assistant'],
            api_key=api_key,
            provider="openai", 
            model_id="gpt-5.2",
            chat_id=999
        )

        found_subject = any(case['expected_subject'] in f.get("subject_name", "").lower() for f in extracted)
        
        # Prüfe, ob das erwartete Key-Fragment in IRGENDEINEM der extrahierten Keys vorkommt
        found_key = False
        for f in extracted:
            full_key = f.get("canonical_key", "").lower()
            if case['expected_canonical_contains'] in full_key:
                found_key = True
                break

        assert found_subject, f"Subjekt '{case['expected_subject']}' nicht erkannt. Gefunden: {extracted}"
        assert found_key, f"Key-Fragment '{case['expected_canonical_contains']}' nicht in den Keys gefunden. Gefunden: {[f.get('canonical_key') for f in extracted]}"
    
    db.close()