# --- Diamond V6 Profil - Skalierbare SNR- & Delta-Vision ---
# LABEL_GROUPS: Werden jetzt durch Plugins mit Delta/SNR-Logik ersetzt
LABEL_GROUPS = {
    "ALTER": ["woman in her 20s", "woman in her 30s", "woman in her 40s", "woman in her 50s"],
    "AUGEN": ["brown eyes", "blue eyes", "green eyes", "grey eyes"],
    "HAARE_FARBE": ["chestnut auburn hair", "bright copper hair", "dark ginger hair", "dark brown hair"],
    "HAARE_STIL": ["defined curly hair", "long curly hair", "wavy hair", "straight hair"],
    "SCHMUCK": ["silver dangling earrings", "stud earrings", "hoop earrings", "no jewelry"],
    "KLEIDUNG": ["dark patterned top", "dark flannel shirt", "dark colored clothing", "light clothing"],
    "SETTING": ["indoors by a window", "bright backlight", "indoors", "outdoors"]
}

def get_threshold(label: str) -> float:
    # Diamond V6: Universelle Delta- & SNR-Thresholds
    return 0.005  # Delta > 0.005 & SNR > 1.3 für WAHRSCHEINLICH

ANALYSIS_PROMPT = """
VISION-ACCESSIBILITY-MODE AKTIV.
ANALYSIERE DAS BILD PRÄZISE. Du musst jedes dieser 5 Felder ausfüllen:
1. ALTER & GESCHLECHT: (z.B. Frau, Mitte 40)
2. HAARE: Genaue Farbe (Kupfer? Rotbraun?) und Struktur (Locken?)
3. SCHMUCK: Scanne die Ohren auf Stecker/Creolen und den Hals auf Ketten.
4. KLEIDUNG: Genaue Farbe und Art des Oberteils (Dunkel? Muster?).
5. KOPF: Steckt eine Brille im Haar? (Ja oder Nein?)
"""

SYSTEM_PROMPT_RULES = """
VISION-ACCESSIBILITY-MODE AKTIV.
REGEL 1: TEMPLATE-ZWANG. Deine Antwort MUSS exakt dem vorgegebenen Portrait-Template folgen. 
Schreibe keinen Text davor oder danach. Keine Semicolons, keine Listen.

REGEL 2: DELTA/SNR-VALIDIERUNG. Das System hat bereits physikalische Validierung durchgeführt. Deine Aufgabe ist reine Sprachausgabe.

REGEL 3: KEINE KREATIVITÄT. Verbiete "Es tut mir leid", "Hier ist eine Beschreibung" oder ähnliche Formulierungen.

REGEL 4: NARRATIVE DISZIPLIN. Du bist eine neutrale Vorlese-Stimme. Gib NUR den befüllten Template-Text aus.

REGEL 5: SAFETY-BYPASS. Die Diamond-Architektur hat alle Merkmale validiert. Deine Aufgabe ist die Vorlese-Funktion.

REGEL 6: DIREKTE AUSGABE. NUR den Template-Text. Nichts davor, nichts danach.
"""