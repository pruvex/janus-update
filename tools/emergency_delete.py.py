import sqlite3
import os

# Pfad zur DB anpassen, falls abweichend
DB_PATH = "C:/KI/Janus-Projekt/backend/data/janus_memory.db"

def delete_memory_id(memory_id):
    if not os.path.exists(DB_PATH):
        print(f"Fehler: Datenbank nicht gefunden unter {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Prüfen, ob ID existiert
        cursor.execute("SELECT id, evidence FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        
        if row:
            print(f"Lösche Memory ID {row[0]}: {row[1][:50]}...")
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            print("Erfolgreich gelöscht.")
        else:
            print(f"Kein Eintrag mit ID {memory_id} gefunden.")
            
        conn.close()
    except Exception as e:
        print(f"Datenbankfehler: {e}")

if __name__ == "__main__":
    delete_memory_id(296)