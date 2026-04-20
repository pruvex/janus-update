# tests/test_service_full.py
import sys
import os

# Pfad-Fix
current_script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_script_path))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.data.database import SessionLocal, init_db # init_db hinzugefügt
from backend.services.vision_service import vision_service
from backend.data import crud_vision

def test_full_pipeline():
    print("--- TEST VISION SERVICE (FRESH DB) ---")
    
    # SCHRITT 0: Tabellen erstellen, falls sie fehlen
    print("Initialisiere Datenbank-Tabellen...")
    init_db()
    
    img_path = os.path.join(project_root, "test_face.jpg")
    if not os.path.exists(img_path):
        print("❌ test_face.jpg fehlt!")
        return

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    db = SessionLocal()
    
    try:
        print("1. Analyse (Lern-Phase)...")
        result = vision_service.process_image(img_bytes, db)
        
        if not result["found_faces"]:
            print("❌ Kein Gesicht auf test_face.jpg gefunden!")
            return
            
        if result["unknown_encodings"]:
            print("   Gesicht gefunden. Speichere als 'Echte-Maggie'...")
            raw_encoding = result["unknown_encodings"][0]
            crud_vision.create_person(db, "Echte-Maggie", raw_encoding)
            print("✅ 'Echte-Maggie' gespeichert.")

        print("\n2. Analyse (Erkennungs-Phase)...")
        result_new = vision_service.process_image(img_bytes, db)
        
        print("   Ergebnis:", result_new["identified_names"])
        
        if "Echte-Maggie" in result_new["identified_names"]:
            print("✅✅✅ ERFOLG: Person wurde wiedererkannt!")
        else:
            print("❌ FEHLER: Person wurde nicht erkannt.")

    except Exception as e:
        print(f"❌ FEHLER: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_full_pipeline()
