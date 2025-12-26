import requests


def check_connection(url, name):
    try:
        print(f"Prüfe Verbindung zu {name} ({url})...")
        response = requests.get(url, timeout=5)
        print(f"✅ {name}: Erfolg! Status Code: {response.status_code}")
    except Exception as e:
        print(f"❌ {name}: FEHLER! {e}")


if __name__ == "__main__":
    print("--- START NETZWERK-DIAGNOSE ---")
    check_connection("https://www.google.com", "Google (Allgemein)")
    check_connection(
        "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41", "Wetter API"
    )
    check_connection("https://de.wikipedia.org/wiki/Python_(Programmiersprache)", "Wikipedia")
    print("--- ENDE ---")
