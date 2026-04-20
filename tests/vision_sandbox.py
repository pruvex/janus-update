# tests/vision_sandbox.py
import sys
import os
import time

print("--- START VISION SANDBOX ---")
print("Lade Bibliotheken... (das kann beim ersten Mal dauern)")

try:
    import face_recognition
    import cv2
    import numpy as np
    import dlib
    print(f"✅ Bibliotheken geladen.")
    print(f"   - dlib Version: {dlib.__version__}")
    print(f"   - face_recognition Version: {face_recognition.__version__}")
    print(f"   - OpenCV Version: {cv2.__version__}")
    print(f"   - GPU Nutzung möglich (dlib): {dlib.DLIB_USE_CUDA}")
except ImportError as e:
    print(f"❌ FEHLER: Eine Bibliothek fehlt: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ KRITISCHER FEHLER beim Import: {e}")
    sys.exit(1)

def test_image_analysis(image_path):
    if not os.path.exists(image_path):
        print(f"⚠️ Datei nicht gefunden: {image_path}")
        return

    print(f"\nAnalysiere Bild: {image_path}")
    start_time = time.time()

    # 1. Bild laden (face_recognition nutzt RGB, OpenCV nutzt BGR)
    # Wir nutzen face_recognition.load_image_file, das ist sicherer für den Anfang
    try:
        image = face_recognition.load_image_file(image_path)
    except Exception as e:
        print(f"❌ Fehler beim Laden des Bildes: {e}")
        return

    # 2. Gesichter finden (HOG Methode - schneller, CPU-freundlich)
    # model='cnn' wäre genauer, braucht aber GPU/CUDA, sonst sehr langsam.
    print("   Suche Gesichter (HOG)...")
    face_locations = face_recognition.face_locations(image, model="hog")
    
    duration_detection = time.time() - start_time
    print(f"   ⏱️ Detektion dauerte: {duration_detection:.4f}s")

    if not face_locations:
        print("   ❌ Kein Gesicht gefunden.")
        return

    print(f"   ✅ {len(face_locations)} Gesicht(er) gefunden!")

    # 3. Encoding generieren (Der "Fingerabdruck" des Gesichts)
    print("   Generiere Encodings...")
    face_encodings = face_recognition.face_encodings(image, face_locations)

    duration_total = time.time() - start_time

    for i, encoding in enumerate(face_encodings):
        print(f"   👤 Gesicht #{i+1}:")
        print(f"      - Position: {face_locations[i]}")
        print(f"      - Vektor-Größe: {len(encoding)} Dimensionen (sollte 128 sein)")
        print(f"      - Vektor-Auszug: {encoding[:5]} ...") # Nur die ersten 5 Werte zeigen

    print(f"\n✅ ERFOLG: Pipeline funktioniert. Gesamtzeit: {duration_total:.4f}s")


if __name__ == "__main__":
    # Wir suchen nach einem Testbild.
    # Du kannst hier einen festen Pfad eintragen oder das Skript fragt dich.
    
    target_img = input("\nBitte Pfad zu einem Bild mit Gesicht eingeben (oder Enter für 'test_face.jpg'): ").strip()
    if not target_img:
        target_img = "test_face.jpg"
    
    # Entferne Anführungszeichen, falls User Pfad kopiert hat
    target_img = target_img.replace('"', '').replace("'", "")

    test_image_analysis(target_img)
    print("\n--- ENDE VISION SANDBOX ---")
