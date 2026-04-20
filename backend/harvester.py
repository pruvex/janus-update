import os
import requests
import json
import time

# --- KONFIGURATION ---
ROOT_DIR = r"C:\KI\Janus-Projekt\backend\tests\vision_matrix\Tiere"
INPUT_FILE = "species_list.txt"
MAX_IMAGES_PER_SPECIES = 20
API_URL = "https://api.inaturalist.org/v1"
WAIT_TIME = 2.0  # Sekunden zwischen den Spezies (Rate-Limiting)

def sanitize(name):
    """Ersetzt Leerzeichen durch Unterstriche und säubert Pfadnamen."""
    return name.strip().replace(" ", "_")

def get_taxon_id(species_name):
    """Sucht die Taxon-ID für einen wissenschaftlichen Namen."""
    try:
        response = requests.get(f"{API_URL}/taxa", params={"q": species_name})
        data = response.json()
        if data["results"]:
            # Wir nehmen den ersten exakten Treffer oder den ersten Treffer
            return data["results"][0]["id"]
    except Exception as e:
        print(f" Fehler bei Taxon-Suche für {species_name}: {e}")
    return None

def download_species_data(species_name, target_path):
    """Lädt Bilder und Metadaten für eine Spezies herunter."""
    taxon_id = get_taxon_id(species_name)
    if not taxon_id:
        print(f" !!! Spezies nicht gefunden: {species_name}")
        return

    print(f" -> Suche Beobachtungen für {species_name} (ID: {taxon_id})...")
    
    params = {
        "taxon_id": taxon_id,
        "quality_grade": "research",
        "photo_license": "cc-by,cc-by-nc,cc0",
        "per_page": MAX_IMAGES_PER_SPECIES,
        "order_by": "votes" # Beste Bilder zuerst
    }

    try:
        response = requests.get(f"{API_URL}/observations", params=params)
        observations = response.json()["results"]
        
        if not observations:
            print(f" !!! Keine 'Research Grade' Bilder für {species_name} gefunden.")
            return

        download_count = 0
        for obs in observations:
            if "photos" in obs and obs["photos"]:
                photo = obs["photos"][0]
                # Priorität: Original -> Large
                img_url = photo["url"].replace("square", "original")
                if not img_url.endswith((".jpg", ".jpeg", ".png")):
                    img_url = photo["url"].replace("square", "large")

                file_id = obs["id"]
                file_name = f"{sanitize(species_name)}_{file_id}.jpg"
                file_path = os.path.join(target_path, file_name)
                json_path = file_path.replace(".jpg", ".json")

                # Überspringen wenn existiert
                if os.path.exists(file_path):
                    continue

                # Download Bild
                img_data = requests.get(img_url).content
                with open(file_path, 'wb') as f:
                    f.write(img_data)

                # Metadaten speichern
                metadata = {
                    "inaturalist_url": f"https://www.inaturalist.org/observations/{file_id}",
                    "photographer_name": obs.get("user", {}).get("login", "unknown"),
                    "location": f"Lat: {obs.get('location', 'N/A')}",
                    "observed_on": obs.get("observed_on", "unknown")
                }
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=4)

                download_count += 1
                if download_count >= MAX_IMAGES_PER_SPECIES:
                    break

        print(f" ✅ {download_count} Bilder für {species_name} gespeichert.")

    except Exception as e:
        print(f" Fehler beim Download für {species_name}: {e}")

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"!!! Fehler: Datei '{INPUT_FILE}' nicht gefunden.")
        return

    current_sub_path = ""
    path_stack = []

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line: continue

        # PFAD-LOGIK
        if line.startswith(">"):
            folder_name = line[1:].strip()
            if not folder_name: # Einzelner ">" setzt zurück
                path_stack = []
                current_sub_path = ""
                print(" -> Pfad auf Root zurückgesetzt.")
            else:
                path_stack.append(sanitize(folder_name))
                current_sub_path = os.path.join(*path_stack)
                print(f" -> Aktueller Pfad: {current_sub_path}")
            continue

        # SPEZIES-LOGIK
        species_name = line
        full_target_path = os.path.join(ROOT_DIR, current_sub_path, sanitize(species_name))
        os.makedirs(full_target_path, exist_ok=True)
        
        download_species_data(species_name, full_target_path)
        time.sleep(WAIT_TIME)

if __name__ == "__main__":
    print("=== JANUS UNIVERSAL BIO-HARVESTER v3.0 ===")
    main()