import re

# Note: The function _get_most_recent_image_path_from_history is NOT moved here
# because it depends on `schemas` which is a data-layer component, and utils
# should generally not depend on higher-level components.


def is_contact_info_submission(prompt: str) -> bool:
    """
    Prüft, ob ein Prompt primär die Übermittlung von Kontaktinformationen zum Ziel hat.
    """
    prompt_lower = prompt.lower()

    # Schlüsselwörter, die stark auf Kontaktinfos hindeuten
    keywords = ["email", "e-mail", "adresse", "telefon", "nummer", "anschrift", "website", "lautet"]

    # Muster, die typisch für Kontaktinfos sind
    patterns = [
        r"[\w\.-]+@[\w\.-]+\.\w{2,}",  # E-Mail
        r"\b\d{5,}\b",  # Telefonnummern-Teile oder PLZ
    ]

    # Die Anfrage ist wahrscheinlich eine Kontakt-Info, wenn sie Schlüsselwörter UND Muster enthält
    # ODER wenn sie mit typischen Phrasen beginnt.
    if any(keyword in prompt_lower for keyword in keywords) and any(
        re.search(pattern, prompt_lower) for pattern in patterns
    ):
        return True

    start_phrases = ["die email von", "die adresse von", "die nummer von"]
    if any(prompt_lower.startswith(phrase) for phrase in start_phrases):
        return True

    return False


def is_creative_writing_request(prompt: str) -> bool:
    """Prüft, ob ein Prompt eine kreative Schreibaufgabe ist, aber KEINE Bildgenerierung."""
    prompt_lower = prompt.lower()

    # Wenn es eine explizite Bild-Anfrage ist, ist es keine Schreib-Anfrage.
    if _is_image_generation_request(prompt):
        return False

    creative_keywords = [
        "schreib",
        "erzähl",
        "dichte",
        "gedicht",
        "geschichte",
        "haiku",
        "erfinde",
        "reime",
        "songtext",
        "ballade",
        "märchen",
        "dialog",
    ]
    return any(keyword in prompt_lower for keyword in creative_keywords)


def is_confirmation(prompt: str) -> bool:
    """Prüft, ob ein User-Prompt eine positive Bestätigung ist. Toleriert Tippfehler."""
    # Liste von Schlüsselwörtern, die eine Bestätigung signalisieren
    keywords = ["richtig", "stimmt", "korrekt", "bestätigt", "ja"]

    prompt_lower = prompt.lower().strip().replace(".", "").replace("!", "").replace(",", "")

    # Prüfe, ob eines der Schlüsselwörter im Prompt enthalten ist.
    # Dies funktioniert auch bei Tippfehlern in anderen Wörtern (z.B. "ja das timmt")
    if any(keyword in prompt_lower for keyword in keywords):
        return True

    return False


def is_identity_query(prompt: str) -> bool:
    """Prüft, ob ein User-Prompt eine Frage zur Identität oder den Fähigkeiten der KI ist."""
    prompt_lower = prompt.lower().strip()
    keywords = [
        "wer bist du",
        "was bist du",
        "deine rolle",
        "deine aufgabe",
        "was ist deine funktion",
        "stell dich vor",
        # --- ERWEITERUNG ---
        "deine stärken",
        "was kannst du",
        "wie arbeitest du",
        "was sind deine fähigkeiten",
        "erzähl mir von dir",
    ]
    # Prüft, ob der Prompt eine der Phrasen enthält
    return any(keyword in prompt_lower for keyword in keywords)


def is_feature_suggestion_query(prompt: str) -> bool:
    """Prüft, ob ein User-Prompt ein Vorschlag für ein neues Feature ist."""
    prompt_lower = prompt.lower()
    keywords = [
        "tts",
        "text-to-speech",
        "sprachausgabe",
        "vorlesen",
        "neues modul",
        "feature",
        "funktion",
        "könnten wir einbauen",
        "was hältst du davon",
        "wie wäre es mit",
        "spendieren",
    ]
    return any(keyword in prompt_lower for keyword in keywords)


def is_greeting(prompt: str) -> bool:
    """Prüft, ob ein User-Prompt eine einfache Begrüßung ist."""
    greetings = ["hallo", "hi", "hey", "guten morgen", "guten tag", "guten abend"]
    prompt_lower = prompt.lower().strip().replace(".", "").replace("!", "").replace(",", "")
    return prompt_lower in greetings


def is_personalizable_query(prompt: str) -> bool:
    """Prüft, ob ein Prompt von der Anreicherung mit persönlichen Präferenzen profitieren würde."""
    prompt_lower = prompt.lower()
    # Kürzere Wortstämme, um Tippfehler ("empgiehl") abzufangen
    keywords = [
        "empfehl",
        "vorschlag",
        "schlag mir vor",
        "was soll ich",
        "finde ein",
        "suche ein",
        "restaurant",
        "hotel",
        "sehenswürdigkeit",
        "urlaub",
        "reise",
        "ausflug",
        "film",
        "buch",
        "musik",
        "aktivität",
    ]
    negative_keywords = ["speicher", "pdf", "datei"]
    if any(keyword in prompt_lower for keyword in negative_keywords):
        return False

    return any(keyword in prompt_lower for keyword in keywords)


def _extract_creative_style(prompt: str) -> str:
    """Extrahiert den gewünschten kreativen Stil aus dem Prompt."""
    prompt_lower = prompt.lower()
    if "haiku" in prompt_lower:
        return "haiku"
    if "gedicht" in prompt_lower or "poesie" in prompt_lower:
        return "gedicht"
    if "geschichte" in prompt_lower or "erzählung" in prompt_lower:
        return "geschichte"
    if "ballade" in prompt_lower:
        return "ballade"
    if "songtext" in prompt_lower:
        return "songtext"
    # Weitere Stile können hier hinzugefügt werden
    return "poetisch"  # Standard-Stil, wenn nichts Spezifisches gefunden wird


def _is_image_unrelated_task(prompt: str) -> bool:
    """
    Prüft mit Schlüsselwörtern, ob ein Prompt eine aufgabenorientierte, nicht-visuelle Aufgabe ist
    (wie Dateioperationen oder Websuche), bei der der visuelle Kontext stören würde.
    """
    prompt_lower = prompt.lower()

    # Schlüsselwörter für Aufgaben, die KEINEN Bildkontext wollen
    task_keywords = [
        # Dateioperationen
        "datei",
        "file",
        "ordner",
        "folder",
        "verzeichnis",
        "directory",
        "speicher",
        "save",
        "schreibe",
        "write",
        "lese",
        "read",
        "kopiere",
        "copy",
        "verschiebe",
        "move",
        "lösche",
        "delete",
        "benenne",
        "rename",
        "führe aus",
        "execute",
        # Websuche
        "suche",
        "search",
        "finde",
        "find",
        "preis",
        "price",
        "kostet",
        "costs",
        "gewonnen",
        "won",
        "ergebnis",
        "result",
        "nachrichten",
        "news",
        "wetter",
        "weather",
    ]

    if any(keyword in prompt_lower for keyword in task_keywords):
        return True

    return False


def _is_explicitly_image_related_task(prompt: str) -> bool:
    """
    Prüft, ob ein Prompt eine explizite Frage zum visuellen Inhalt eines Bildes ist.
    Diese Funktion hat Vorrang vor _is_image_unrelated_task.
    """
    prompt_lower = prompt.lower()

    # Schlüsselwörter für Aufgaben, die den Bildkontext ZWINGEND benötigen
    image_keywords = [
        "beschreibe",
        "erkennst",
        "was siehst du",
        "was ist das",
        "was ist auf dem bild",
        "analysiere das bild",
        "erkläre das bild",
        "identifiziere",
        "was für ein",
    ]

    if any(keyword in prompt_lower for keyword in image_keywords):
        return True

    return False


def _is_image_generation_request(prompt: str) -> bool:
    """Prüft, ob ein Prompt eine explizite Bildgenerierungsaufgabe ist."""
    prompt_lower = prompt.lower().strip()
    image_keywords = [
        "zeichne",
        "male",
        "erzeuge ein bild",
        "erstelle ein bild",
        "generiere ein bild",
        "bild von",
        "foto von",
        "photo von",
    ]
    return any(prompt_lower.startswith(keyword) for keyword in image_keywords)


def is_web_search_intent(prompt: str) -> bool:
    """
    Prüft, ob der Prompt eine klare Absicht zur Websuche hat.
    Dies wird verwendet, um das 'perform_websearch'-Tool zu erzwingen.
    """
    prompt_lower = prompt.lower()
    
    # Schlüsselwörter, die stark auf eine Suche nach externen, aktuellen Infos hindeuten
    search_keywords = [
        "suche",
        "finde",
        "recherchiere",
        "was ist der preis von",
        "wieviel kostet",
        "wer hat gewonnen",
        "was sind die nachrichten",
        "aktuell",
        "neueste",
        "release",
        "erscheinungsdatum",
        "welche spiele",
        "wer ist",
        "was ist die hauptstadt",
        "wie hoch ist",
        "wetter in",
        "nachrichten über"
    ]

    # Wenn der Prompt mit einer Frage beginnt und ein Such-Schlüsselwort enthält,
    # ist die Absicht sehr wahrscheinlich eine Websuche.
    question_starters = ["wer", "was", "wann", "wo", "warum", "wie", "welche"]
    
    if any(prompt_lower.startswith(start) for start in question_starters) and any(keyword in prompt_lower for keyword in search_keywords):
        return True
        
    # Auch direkte Befehle abdecken
    if any(prompt_lower.startswith(keyword) for keyword in ["suche nach", "finde mir", "recherchiere"]):
        return True

    return False
