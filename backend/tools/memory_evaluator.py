import asyncio
import json
import logging
import sys
import os

# Pfad-Anpassung, damit die backend-Module gefunden werden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.data.database import SessionLocal
from backend.services import memory_extractor
import keyring

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("janus_evaluator")

async def run_eval():
    db = SessionLocal()
    # Hole API-Key (Anpassung an deinen Provider/Keyring-Namen)
    api_key = keyring.get_password("Janus-Projekt", "openai") 
    
    if not api_key:
        print("❌ Fehler: API Key nicht im Keyring gefunden.")
        return

    with open("tests/memory_gold_standard.json", "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    passed_count = 0
    for case in test_cases:
        print(f"\n▶️ Teste: {case['name']}")
        
        # WICHTIG: Nutze die existierende Extraktions-Funktion
        extracted = await memory_extractor.extract_and_save_fact_from_interaction(
            db=db,
            user_msg=case['input_user'],
            assistant_msg=case['input_assistant'],
            api_key=api_key,
            provider="openai", 
            model_id="gpt-5.2",
            chat_id=999 # Test-Chat ID
        )

        # Validierung
        success = False
        if extracted:
            for fact in extracted:
                subj = fact.get("subject_name", "").lower()
                key = fact.get("canonical_key", "").lower()
                
                if case['expected_subject'] in subj and any(case['expected_canonical_contains'] in f.get('canonical_key', '') for f in extracted):
                    success = True
                    break
        
        if success:
            print("✅ BESTANDEN")
            passed_count += 1
        else:
            print(f"❌ FEHLGESCHLAGEN. Extrahierte Fakten: {extracted}")

    print(f"\n📊 Ergebnis: {passed_count}/{len(test_cases)} Tests bestanden.")
    db.close()

if __name__ == "__main__":
    asyncio.run(run_eval())
