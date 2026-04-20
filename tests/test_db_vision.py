# tests/test_db_vision.py
import sys
import os
import numpy as np

# --- PFAD REPARATUR START ---
# Wir holen uns den absoluten Pfad dieses Skripts
current_script_path = os.path.abspath(__file__)
# Der Ordner, in dem das Skript liegt (tests)
tests_dir = os.path.dirname(current_script_path)
# Der Projekt-Ordner (eine Ebene höher: Janus-Projekt)
project_root = os.path.dirname(tests_dir)

# Wir fügen den Projekt-Ordner an die ERSTE Stelle des Suchpfads
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"Projekt-Root erkannt als: {project_root}")
# --- PFAD REPARATUR ENDE ---

# Jetzt sollten die Imports klappen
try:
    from backend.data.database import SessionLocal, init_db
    from backend.data import crud_vision
except ImportError as e:
    print(f"❌ IMMER NOCH IMPORT FEHLER: {e}")
    print("Stelle sicher, dass im Ordner 'backend' eine leere Datei '__init__.py' liegt!")
    sys.exit(1)

def test_database():
    print("--- TEST DB VISION ---")
    
    # 1. DB Initialisieren (Tabellen erstellen)
    init_db()
    db = SessionLocal()
    
    try:
        # 2. Fake Encoding erstellen (einfach Zufallszahlen, 128 Dimensionen)
        fake_encoding = np.random.rand(128)
        name = "Test-Maggie"
        
        # 3. Speichern prüfen
        print(f"Versuche, {name} zu speichern...")
        existing = crud_vision.get_person_by_name(db, name)
        if not existing:
            person = crud_vision.create_person(db, name, fake_encoding, {"hair": "red"})
            print(f"✅ Gespeichert: ID {person.id}")
        else:
            print(f"ℹ️ {name} existiert schon.")

        # 4. Laden prüfen
        print("Lade alle Gesichter...")
        faces = crud_vision.get_all_known_faces(db)
        
        if name in faces:
            print(f"✅ {name} erfolgreich aus DB geladen.")
            print(f"   Vektor-Typ: {type(faces[name])}")
            print(f"   Vektor-Länge: {len(faces[name])}")
        else:
            print(f"❌ {name} nicht gefunden!")

    except Exception as e:
        print(f"❌ FEHLER: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_database()