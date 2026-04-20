import re
import logging
from typing import Literal, cast
from backend.services import llm_gateway

# ----------------------------
# Normalization helpers
# ----------------------------

_PUNCT_RE = re.compile(r"[^\w\säöüÄÖÜß-]+", re.UNICODE)

def _normalize(prompt: str) -> str:
    """
    Lowercase, trim, remove punctuation noise, collapse whitespace.
    Keeps umlauts/ß and hyphen.
    """
    p = (prompt or "").strip().lower()
    p = _PUNCT_RE.sub(" ", p)
    p = re.sub(r"\s+", " ", p).strip()
    return p

def _word_count(prompt: str) -> int:
    p = _normalize(prompt)
    return 0 if not p else len(p.split())


# ----------------------------
# Original functions (kept for compatibility if used elsewhere)
# ----------------------------

def is_contact_info_submission(prompt: str) -> bool:
    """
    Prüft, ob ein Prompt primär die Übermittlung von Kontaktinformationen zum Ziel hat.
    """
    prompt_lower = prompt.lower()
    keywords = ["email", "e-mail", "adresse", "telefon", "nummer", "anschrift", "website", "lautet"]
    patterns = [r"[\w\.-]+@[\w\.-]+\.\w{2,}", r"\b\d{5,}\b"]
    if any(keyword in prompt_lower for keyword in keywords) and any(re.search(pattern, prompt_lower) for pattern in patterns):
        return True
    start_phrases = ["die email von", "die adresse von", "die nummer von"]
    if any(prompt_lower.startswith(phrase) for phrase in start_phrases):
        return True
    return False

def is_creative_writing_request(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    if is_image_generation_request(prompt):
        return False
    creative_keywords = ["schreib", "erzähl", "dichte", "gedicht", "geschichte", "haiku", "erfinde", "reime", "songtext", "ballade", "märchen", "dialog"]
    return any(keyword in prompt_lower for keyword in creative_keywords)

def is_feature_suggestion_query(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    keywords = ["tts", "text-to-speech", "sprachausgabe", "vorlesen", "neues modul", "feature", "funktion", "könnten wir einbauen", "was hältst du davon", "wie wäre es mit", "spendieren"]
    return any(keyword in prompt_lower for keyword in keywords)

def is_personalizable_query(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    keywords = ["empfehl", "vorschlag", "schlag mir vor", "was soll ich", "finde ein", "suche ein", "restaurant", "hotel", "sehenswürdigkeit", "urlaub", "reise", "ausflug", "film", "buch", "musik", "aktivität"]
    negative_keywords = ["speicher", "pdf", "datei"]
    if any(keyword in prompt_lower for keyword in negative_keywords):
        return False
    return any(keyword in prompt_lower for keyword in keywords)

def is_image_generation_request(prompt: str) -> bool:
    prompt_lower = prompt.lower().strip()
    image_keywords = ["zeichne", "male", "erzeuge ein bild", "erstelle ein bild", "generiere ein bild", "bild von", "foto von", "photo von"]
    return any(prompt_lower.startswith(keyword) for keyword in image_keywords)


def _is_image_generation_request(prompt: str) -> bool:
    """Legacy alias retained for older patches/tests."""
    return is_image_generation_request(prompt)


def is_country_info_intent(prompt: str) -> bool:
    prompt_lower = (prompt or "").lower()
    country_keywords = [
        "hauptstadt",
        "einwohner",
        "bevölkerung",
        "bevoelkerung",
        "währung",
        "waehrung",
        "country",
        "population",
        "capital",
        "currency",
    ]
    if any(keyword in prompt_lower for keyword in country_keywords):
        return True

    # "Land" nur als eigenständiges Wort werten (nicht als Teil wie in "Mailand").
    return bool(re.search(r"\bland\b", prompt_lower))


def is_generic_country_prompt(prompt: str) -> bool:
    prompt_lower = (prompt or "").lower().strip()
    generic_patterns = [
        r"\berzähl\s+mir\s+.*\büber\s+ein\s+land\b",
        r"\berzaehl\s+mir\s+.*\bueber\s+ein\s+land\b",
        r"\babout\s+a\s+country\b",
        r"\ba\s+country\b",
        r"\bein\s+land\b",
        r"\birgendein\s+land\b",
    ]
    return any(re.search(pattern, prompt_lower) for pattern in generic_patterns)

def is_web_search_intent(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    search_keywords = ["suche", "finde", "recherchiere", "was ist der preis von", "wieviel kostet", "wer hat gewonnen", "was sind die nachrichten", "aktuell", "neueste", "release", "erscheinungsdatum", "welche spiele", "wer ist", "was ist die hauptstadt", "wie hoch ist", "wetter in", "nachrichten über"]
    question_starters = ["wer", "was", "wann", "wo", "warum", "wie", "welche"]

    # Country-Facts sollen NICHT automatisch in Websearch laufen.
    if is_country_info_intent(prompt_lower):
        return False

    if any(prompt_lower.startswith(start) for start in question_starters) and any(keyword in prompt_lower for keyword in search_keywords):
        return True
    if any(prompt_lower.startswith(keyword) for keyword in ["suche nach", "finde mir", "recherchiere"]):
        return True
    return False

# --- NEW, ROBUST INTENT FUNCTIONS FOR "FAST LANE" ---

_THANKS_RE = re.compile(
    r"^(?:"
    r"danke|dankeschön|danke schoen|vielen dank|tausend dank|thx|thanks"
    r")(?:\s+(?:dir|euch|janus|assistant|bot))?$"
)

def is_thanks(prompt: str) -> bool:
    p = _normalize(prompt)
    return bool(_THANKS_RE.match(p))

_GREETING_RE = re.compile(
    r"^(?:"
    r"hi|hallo|hey|moin|servus|grüß dich|gruesse? dich|guten morgen|guten tag|guten abend"
    r")(?:\s+(?:janus|assistant|bot|du|ihr))?$"
)

_GREETING_PREFIX_RE = re.compile(
    r"^(?:hi|hallo|hey|moin|servus|grüß dich|gruesse? dich|guten morgen|guten tag|guten abend)\b"
)

_SMALLTALK_FOLLOWUP_RE = re.compile(
    r"\b(?:wie geht(?:s| es)? dir|wie laeufts|wie läufts|was geht|alles gut)\b"
)

_TASKY_KEYWORDS = {
    "erstelle",
    "mach",
    "mache",
    "baue",
    "schreib",
    "suche",
    "finde",
    "liste",
    "öffne",
    "oeffne",
    "lösche",
    "loesche",
    "delete",
    "create",
    "run",
}

_OPINION_RE = re.compile(
    r"\b(?:findest du|magst du|wie stehst du zu|was hältst du von|wie denkst du über|schätzt du)\b"
)

def is_greeting(prompt: str) -> bool:
    p = _normalize(prompt)
    if bool(_GREETING_RE.match(p)):
        return True
    words = p.split()
    if any(token in _TASKY_KEYWORDS for token in words):
        return False

    if _SMALLTALK_FOLLOWUP_RE.search(p):
        return _word_count(p) <= 8

    if not _GREETING_PREFIX_RE.match(p):
        return False

    return _word_count(p) <= 6


def is_opinion_query(prompt: str) -> bool:
    p = _normalize(prompt)
    if _OPINION_RE.search(p):
        return _word_count(p) <= 12
    return False

_IDENTITY_RE = re.compile(
    r"^(?:\s*"
    r"(?:wer|was)\s+bist\s+du(?:\s+eigentlich)?"
    r"|stell\s+dich\s+vor"
    r"|erzähl\s+mir\s+von\s+dir"
    r"|was\s+kannst\s+du(?:\s+eigentlich)?"
    r"|wie\s+arbeitest\s+du"
    r"|was\s+ist\s+deine\s+(?:rolle|aufgabe|funktion)"
    r"|deine\s+(?:rolle|aufgabe|funktion|stärken|faehigkeiten|fähigkeiten)"
    r")\s*$"
)

def is_identity_query(prompt: str) -> bool:
    p = _normalize(prompt)
    p = re.sub(r"\s+bitte$", "", p).strip()
    return bool(_IDENTITY_RE.match(p))

# Legacy confirmation for compatibility
def is_confirmation(prompt: str) -> bool:
    keywords = ["richtig", "stimmt", "korrekt", "bestätigt", "ja"]
    prompt_lower = prompt.lower().strip().replace(".", "").replace("!", "").replace(",", "")
    if any(keyword in prompt_lower for keyword in keywords):
        return True
    return False

_CONFIRMATION_ONLY_RE = re.compile(
    r"^(?:"
    r"ja|jep|jup|jo|ok|okay|passt|genau|korrekt|richtig|stimmt"
    r"|nein|nee|nope|doch"
    r")$"
)

def is_confirmation_only(prompt: str) -> bool:
    p = _normalize(prompt)
    if _word_count(p) > 2:
        return False
    return bool(_CONFIRMATION_ONLY_RE.match(p))

async def classify_intent_with_llm(
    user_text: str, 
    api_key: str, 
    provider: str = "openai"
) -> Literal['FAKTEN_ANGABE', 'FRAGE_ODER_BEFEHL', 'BEGRUESSUNG']:
    """
    Classifies user intent using an LLM for high accuracy.
    Returns one of: 'FAKTEN_ANGABE', 'FRAGE_ODER_BEFEHL', 'BEGRUESSUNG'
    """
    # First try fast heuristics for greetings and thanks
    if is_greeting(user_text):
        return 'BEGRUESSUNG'
    
    if is_thanks(user_text):
        return 'BEGRUESSUNG'
    
    # For very short inputs, use heuristics to avoid LLM calls
    if len(user_text.strip()) < 10:
        if any(user_text.lower().startswith(x) for x in ['hi', 'hallo', 'hey', 'moin']):
            return 'BEGRUESSUNG'
        if '?' in user_text:
            return 'FRAGE_ODER_BEFEHL'
    
    # Use LLM for classification
    system_prompt = """Du bist ein textbasierter Klassifizierer. Deine einzige Aufgabe ist es, die Absicht des Benutzers zu erkennen. 
    Antworte ausschließlich mit einem der folgenden drei Wörter: 'FAKTEN_ANGABE', 'FRAGE_ODER_BEFEHL', 'BEGRUESSUNG'.

    - 'FAKTEN_ANGABE': Der Benutzer teilt eine Information über sich, seine Vorlieben oder seine Umgebung mit.
    - 'FRAGE_ODER_BEFEHL': Der Benutzer stellt eine Frage oder gibt eine Anweisung, etwas zu tun.
    - 'BEGRUESSUNG': Eine einfache Begrüßung wie 'Hallo' oder 'Hi'.
    
    User-Text: """
    
    try:
        # Use a fast model for classification
        model_id = "gpt-5.4-nano" if provider == "openai" else "gemini-3-flash-preview"
        
        response = await llm_gateway.call_llm(
            provider=provider,
            model_id=model_id,
            api_key=api_key,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f'"{user_text}"\nKlassifizierung:'}
            ],
            max_tokens=10,
            temperature=0.0
        )
        
        result = response.get("text", "").strip().upper()
        
        # Validate and return the result
        if result in ['FAKTEN_ANGABE', 'FRAGE_ODER_BEFEHL', 'BEGRUESSUNG']:
            return cast(Literal['FAKTEN_ANGABE', 'FRAGE_ODER_BEFEHL', 'BEGRUESSUNG'], result)
            
    except Exception as e:
        logging.error(f"Error in LLM-based intent classification: {e}")
    
    # Fallback to traditional classifier if LLM fails
    return 'FRAGE_ODER_BEFEHL'

def is_fact_submission(prompt: str) -> bool:
    """
    Legacy function for backward compatibility.
    Uses simple heuristics to detect fact submissions.
    """
    p_norm = _normalize(prompt)

    # Negative keywords: phrases that indicate a question or command, not a statement.
    question_keywords = [
        "wer", "was", "wann", "wo", "wie", "warum", "welche", "kannst du", "sollte"
    ]
    if any(p_norm.startswith(kw) for kw in question_keywords):
        return False

    # Positive keywords: phrases that strongly indicate a fact submission.
    fact_patterns = [
        r"mein(e)?\s\w+\s(heißt|ist)",          # "mein hund heißt", "meine katze ist"
        r"ich\s(habe|bin|wohne|liebe|hasse|brauche)", # "ich habe eine katze", "ich bin allergisch"
        r"\w+\s(ist|hat)\s(eine|ein|keine|kein)",  # "hubert hat eine allergie"
        r"für\s(mich|uns)\s(ist|sind|war|waren|wird|werden)"  # "für mich ist performance wichtig"
    ]
    
    if any(re.search(pattern, p_norm) for pattern in fact_patterns):
        # If it's a fact but very long, it might be a complex request in disguise.
        if _word_count(p_norm) < 15:  # Slightly increased length limit
            return True
            
    return False

def should_skip_planner(prompt: str, api_key: str = "", provider: str = "") -> bool:
    """
    Returns True if the user request is trivial and can bypass the Planner.
    """
    # If we have API credentials, use the LLM-based classifier
    if api_key and provider:
        try:
            # Use a simple sync call to the LLM classifier
            import asyncio
            loop = asyncio.get_event_loop()
            intent = loop.run_until_complete(
                classify_intent_with_llm(prompt, api_key, provider)
            )
            return intent in ['BEGRUESSUNG', 'FAKTEN_ANGABE']
        except Exception as e:
            logging.warning(f"LLM classification failed, falling back to heuristics: {e}")
    
    # Fallback to traditional heuristics
    return any([
        is_greeting(prompt),
        is_thanks(prompt),
        is_identity_query(prompt),
        is_confirmation_only(prompt),
        is_fact_submission(prompt)  # Include fact submissions in fast lane
    ])

    return False
