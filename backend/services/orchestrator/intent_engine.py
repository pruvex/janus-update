"""Diamond Intent Engine - Extrahierte Keyword-Listen und Intent-Erkennung.

Zentralisiert alle Keyword-basierten Intent-Erkennungen für den Orchestrator.
Keine harten Strings mehr im Orchestrator - nur noch saubere Service-Calls.
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional, Union, Set
from dataclasses import dataclass, field
from backend.utils import intent_classifier

logger = logging.getLogger("janus_backend")

# ═══════════════════════════════════════════════════════════════════════════════
# Intent Engine V2 — Normalisierung, Wortgrenzen, Shopping/Calendar-Signale
# ═══════════════════════════════════════════════════════════════════════════════

_WORD_BOUNDARY_CACHE: Dict[str, re.Pattern] = {}


def _normalize_text(value: str) -> str:
    text = str(value or "").casefold()
    text = re.sub(r"[^\w\s€$£.-]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _contains_phrase(text_norm: str, phrase: str) -> bool:
    phrase_norm = _normalize_text(phrase)
    if not phrase_norm:
        return False
    pattern = _WORD_BOUNDARY_CACHE.get(phrase_norm)
    if pattern is None:
        pattern = re.compile(rf"(?<!\w){re.escape(phrase_norm)}(?!\w)", re.IGNORECASE)
        _WORD_BOUNDARY_CACHE[phrase_norm] = pattern
    return bool(pattern.search(text_norm))


def _contains_any_phrase(text_norm: str, phrases: Union[Tuple[str, ...], List[str]]) -> bool:
    return any(_contains_phrase(text_norm, phrase) for phrase in phrases)


_PRICE_RE = re.compile(
    r"(?:\b\d{1,6}(?:[.,]\d{1,2})?\s*(?:€|euro|eur|\$|usd|£|gbp)\b|"
    r"(?:was kostet|wie viel kostet|wie teuer|preis(?:vergleich)?))",
    re.IGNORECASE,
)
_CALENDAR_TIME_RE = re.compile(
    r"(?:"
    r"(?:\bum\s*)?\b\d{1,2}(?::|\.|\s+uhr\b)(?:\d{2})?\b|\b\d{1,2}\s*uhr\b"
    r"|\b\d{1,2}-\s*uhr\b|\b\d{1,2}-uhr\b"
    r"|\b\d{1,2}\s*h\b"
    r"|\b\d{1,2}:\d{2}\s*h\b|\b\d{1,2}:\d{2}\b"
    r")",
    re.IGNORECASE,
)
_RELEASE_TERMIN_RE = re.compile(
    r"\b(?:erscheinungstermin|release[- ]?termin|veröffentlichungstermin|veroeffentlichungstermin)\b",
    re.IGNORECASE,
)

# Contextual Intent Boost (TASK-062): Keywords im User-Treffer gegen Kalender-Snapshot (Titel/Location).
_CALENDAR_SNAPSHOT_STOPWORDS = frozenset({
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einer", "eines", "einem",
    "und", "oder", "aber", "mit", "bei", "zum", "zur", "von", "vom", "zu", "im", "in", "an", "am", "auf",
    "ist", "sind", "war", "waren", "hat", "haben", "hast", "habe",
    "kann", "kannst", "können", "koennen", "muss", "musst", "müssen", "muessen", "soll", "sollte",
    "nicht", "noch", "nur", "wie", "was", "wer", "wo", "wann", "warum",
    "mal", "bitte", "mir", "mich", "ich", "du", "dir", "dich", "uns", "euch", "ihr", "sie",
    "morgen", "heute", "gestern", "jetzt", "schon", "auch", "dann", "wenn",
    "mein", "meine", "meinen", "dein", "deine",
    "termin", "termine", "kalender",
    # Generic time/preposition tokens that make bad mutation targets:
    "uhr", "auf", "nach", "mit", "bis", "dann", "gleich", "halt",
    # Action verbs — never a mutation target (TASK-065 extension):
    "nehmen", "nehme", "nimm",
    "bringen", "bringe", "bring",
    "tun", "tue", "mach", "machen", "mache",
    "denken", "denke", "denk",
    "gehen", "gehe", "geh",
    "holen", "hole", "hol",
    "legen", "lege", "leg",
    "stellen", "stelle", "stell",
    "kaufen", "kaufe", "kauf",
    "vergessen", "vergesse", "vergiss",
})


def _calendar_snapshot_anchor_tokens(text_norm: str) -> Set[str]:
    """Nutzer-/Event-Zeichenkette nach Normalisierung in bedeutsame Tokens (min. Länge, ohne Stoppwörter)."""
    tokens: Set[str] = set()
    if not text_norm:
        return tokens
    for raw in text_norm.split():
        w = raw.strip("-_.").strip()
        if len(w) < 3 or w.isdigit():
            continue
        if w in _CALENDAR_SNAPSHOT_STOPWORDS:
            continue
        tokens.add(w)
    return tokens


def calendar_user_text_overlap_snapshot(user_text: str, calendar_snapshot: Any) -> bool:
    """True wenn mind. ein Anchor-Token des Users im kombinierten Titel/Ort eines Snapshot-Events vorkommt."""
    if not user_text or not calendar_snapshot:
        return False
    events = calendar_snapshot.get("events") if isinstance(calendar_snapshot, dict) else None
    if not isinstance(events, list) or not events:
        return False
    text_norm = _normalize_text(user_text)
    if not text_norm or _RELEASE_TERMIN_RE.search(text_norm):
        return False
    utoks = _calendar_snapshot_anchor_tokens(text_norm)
    if not utoks:
        return False
    for event in events:
        if not isinstance(event, dict):
            continue
        title = event.get("title") or ""
        loc = event.get("location") or ""
        hay = _normalize_text(f"{title} {loc}")
        if not hay:
            continue
        etoks = _calendar_snapshot_anchor_tokens(hay)
        if utoks & etoks:
            return True
        if 10 <= len(hay) <= 120 and _contains_phrase(text_norm, hay):
            return True
    return False


# Diamond: Entfernung/Route zwischen Orten darf nicht durch reinen Snapshot-Worttreffer
# als Kalender-Intent „hochgezogen“ werden (False Positives z.B. Stadtnamen in Events).
_ROUTING_GEO_MARKERS = re.compile(
    r"(wie\s+weit|wie\s+lange\s+(?:dauert\s+(?:die\s+fahrt|es|die\s+autofahrt)|"
    r"braucht\s+man(?:\s+dafür)?|brauchst\s+du)|entfernung|reichweite|luftlinie|"
    r"fahrzeit|fahrstrecke|fahrdauer|reisezeit|reisedauer|distanz|"
    r"kilometer\b|\bkm\b|wie\s+viele\s+kilometer|routen?\b|"
    r"(?:auto|fahr|geh|zu\s+fuß|zu\s+fuss)(?:strecke|weg|zeit)\b|"
    r"driving\s+time|driving\s+distance|how\s+far|how\s+long\s+(?:to\s+drive|does\s+it\s+take))",
    re.IGNORECASE,
)
_ROUTING_VON_NACH_DE = re.compile(r"\bvon\s+[^\n,?\.!]{1,52}\s+nach\b", re.IGNORECASE)
_ROUTING_FROM_TO_EN = re.compile(r"\bfrom\s+[^\n,?\.!]{1,52}\s+to\b", re.IGNORECASE)
_ROUTING_ZWISCHEN_UND = re.compile(
    r"\bzwischen\s+[^\n,?\.!]{1,52}\s+und\b",
    re.IGNORECASE,
)

_EXPLICIT_PDF_INTENT = re.compile(
    r"(?:"
    r"\bals\s+pdf\b|\bzu\s+pdf\b|\bpdf\s+(?:datei|file|erstell|erzeug|generier|export)\w*\b|"
    r"\bexport(?:iere|ieren)?\s+(?:als\s+)?pdf\b|\bcreate\s+(?:a\s+)?pdf\b|"
    r"\bsave\s+as\s+pdf\b|\bprint(?:able)?\s+pdf\b|"
    r"\b(?:erstell|generier|exportier|mach(?:\s+mir)?|schreib)\w*.{0,48}\bpdf\b|"
    r"\bpdf\b.{0,24}\b(?:bitte|dafür|davon|hier(?:für)?)\b|"
    r"\bdruckfassung\s+als\s+pdf\b|\bspeichern\s+als\s+pdf\b"
    r")",
    re.IGNORECASE,
)

SHOPPING_ACTION_MARKERS: Tuple[str, ...] = (
    "kaufen",
    "kaufe",
    "einkaufen",
    "einkauf",
    "bestellen",
    "bestelle",
    "shoppen",
    "shopping",
    "offers",
    "günstige",
    "guenstige",
    "kaufberatung",
    "preisvergleich",
    "angebot",
    "angebote",
    "deal",
    "deals",
    "rabatt",
)

SHOPPING_PRODUCT_MARKERS: Tuple[str, ...] = (
    "iphone",
    "ipad",
    "macbook",
    "galaxy",
    "playstation",
    "xbox",
    "switch",
    "airpods",
    "headset",
    "kopfhörer",
    "kopfhoerer",
    "laptop",
    "notebook",
    "tablet",
    "smartphone",
    "fernseher",
    "tv",
    "monitor",
    "kamera",
    "konsole",
    "konsolen",
    "armbanduhr",
    "smartwatch",
    "watch",
)

SHOPPING_VENDOR_MARKERS: Tuple[str, ...] = (
    "amazon",
    "ebay",
    "otto",
    "zalando",
    "idealo",
    "geizhals",
    "billiger.de",
    "netto",
    "aldi",
    "lidl",
    "rewe",
    "edeka",
    "kaufland",
    "dm",
)

CALENDAR_COMMAND_MARKERS: Tuple[str, ...] = (
    "termin erstellen",
    "termin anlegen",
    "termin hinzufügen",
    "termin hinzufuegen",
    "termin plane ich",
    "plane einen termin",
    "plane mir einen termin",
    "plan einen termin",
    "trage ein",
    "eintragen",
    "einplanen",
    "in den kalender",
    "kalender eintrag",
    "kalendereintrag",
    "meeting planen",
    "planen bitte",
    "verschiebe",
    "absagen",
    "lösche den termin",
    "loesche den termin",
    "erinnere mich",
    "habe ich",
    "was habe ich",
    "was steht an",
    "steht an",
    "meine termine",
    "meine termine",
    "meinen termin",
    "meinen terminen",
    "bring",
    "ergänze",
    "ergänzen",
    "hinzufügen",
    # Mutation / reminder triggers (TASK-062-b)
    "vergessen",
    "denk an",
    "denke an",
    "erinnere",
    "notier",
    "notiere",
    "notiere das",
    "notier das",
    "trag ein",
    "nicht vergessen",
    "auf die liste",
    # BACKLOG-050: Calendar update/mutation triggers
    "update",
    "aktualisieren",
    "aktualisiere",
    "ändern",
    "aendern",
    "ändere",
    "aendere",
    # ASCII-Umlaut-Fallbacks (für Eingaben ohne Umlaute)
    "ergaenze",
    "ergaenzen",
    "hinzufuegen",
    "loesche den termin",
)

CALENDAR_OBJECT_MARKERS: Tuple[str, ...] = (
    "termin",
    "meeting",
    "kalender",
    "kalendereintrag",
    "verabredung",
    # BACKLOG-054: English calendar keyword for Gemini provider parity
    "calendar",
)

CALENDAR_DATE_MARKERS: Tuple[str, ...] = (
    "heute",
    "morgen",
    "übermorgen",
    "uebermorgen",
    "montag",
    "dienstag",
    "mittwoch",
    "donnerstag",
    "freitag",
    "samstag",
    "sonntag",
    "nächste woche",
    "naechste woche",
)

CALENDAR_ACTIVITY_MARKERS: Tuple[str, ...] = (
    "einkaufen",
    "einkauf",
    "besorgen",
    "holen gehen",
)


_MUTATION_PREP_RE = re.compile(
    r"\b(?:beim?|an\s+(?:den?|die|das)?\s*|am|zum?|zur|für|bei|nach|vor|im|den?\s+|die\s+|das\s+)\s*",
    re.IGNORECASE,
)

_MUTATION_STRIP_PREFIXES: Tuple[str, ...] = (
    "beim",
    "bei dem",
    "bei der",
    "bei",
    "beim sport",
    "am",
    "zum",
    "zur",
    "für",
    "nach",
    "vor",
    "im",
    "für den",
    "für die",
    "für das",
    "den termin",
    "die termin",
    "das termin",
)

_CALENDAR_CREATION_MARKERS: Tuple[str, ...] = (
    # Explicit creation verbs
    "erstelle einen termin",
    "erstell einen termin",
    "erstelle termin",
    "erstell termin",
    "neuen termin erstellen",
    "termin erstellen",
    "termin anlegen",
    "termin hinzufügen",
    "termin hinzufuegen",
    # Plan / schedule
    "plan mir ein",
    "plan mir einen",
    "plane mir ein",
    "plane mir einen",
    "plane einen termin",
    "plane ein meeting",
    "plan ein meeting",
    "einplanen",
    "in den kalender eintragen",
    "in den kalender einplanen",
    "kalender eintrag erstellen",
    "kalendereintrag erstellen",
    # Set / schedule markers
    "setz einen termin",
    "setze einen termin",
    "setz termin",
    "trage ein",
    "trag ein",
    "füge einen termin hinzu",
    "fuege einen termin hinzu",
    # English fallbacks (used in mixed-language queries)
    "create event",
    "add event",
    "schedule event",
    "schedule meeting",
)

_MUTATION_VERBS_AND_TRIGGERS: Tuple[str, ...] = (
    "vergessen", "denk an", "denke an", "erinnere", "erinnere mich",
    "notier", "notiere", "notiere das", "notier das",
    "nicht vergessen", "auf die liste",
    "trag ein", "trage ein", "eintragen",
    "bring", "ergänze", "ergänzen", "hinzufügen",
    # ASCII-Umlaut-Fallbacks für Eingaben ohne Umlaute
    "ergaenze", "ergaenzen", "hinzufuegen",
    "verschiebe", "absagen", "loesche", "lösche",
)


def _extract_mutation_target(user_text: str) -> Optional[str]:
    """Extrahiere das Kalender-Subjekt aus einem Mutations-Satz.

    Strategie:
    1. Suche nach Präpositional-Phrase nach Präpositionen (beim X, am X, für X).
    2. Falle auf den letzten bedeutsamen Nominal-Chunk zurück.

    Beispiele:
        "Handtuch vergessen beim Sport"    → "Sport"
        "Denk an den Aldi-Termin morgen"   → "Aldi"
        "Ergänze beim Zahnarzt: Röntgen"   → "Zahnarzt"
        "Erinnere mich an das Meeting"     → "Meeting"
    """
    if not user_text:
        return None
    text = str(user_text).strip()

    # 1. Suche nach "beim/am/zum/für/an … [Wort]"
    for m in _MUTATION_PREP_RE.finditer(text):
        rest = text[m.end():].strip()
        first_word = rest.split()[0] if rest.split() else None
        if first_word:
            # Strip trailing punctuation; split compound words on "-" and take first part
            first_word = re.sub(r"[^\wäöüÄÖÜß\-]", "", first_word)
            first_word = first_word.split("-")[0].strip()
            if len(first_word) >= 2 and first_word.lower() not in _CALENDAR_SNAPSHOT_STOPWORDS:
                return first_word.capitalize()

    # 2. Fallback: entferne Trigger-Wörter, nimm letzten Nominal-Chunk ≥3 Zeichen
    text_lower = text.lower()
    for trigger in sorted(_MUTATION_VERBS_AND_TRIGGERS, key=len, reverse=True):
        text_lower = text_lower.replace(trigger, " ")
    tokens = [
        t.strip(".,!?:;-").strip()
        for t in text_lower.split()
        if len(t.strip(".,!?:;-").strip()) >= 3
        and t.strip(".,!?:;-").strip() not in _CALENDAR_SNAPSHOT_STOPWORDS
    ]
    if tokens:
        return tokens[-1].capitalize()

    return None


def _has_uhr_product_signal(text_norm: str) -> bool:
    """`uhr` als Produkt-/Beratungssignal, aber nicht nach Uhrzeit (z.B. `14 uhr`, `14-uhr`)."""
    for m in re.finditer(r"\buhr\b", text_norm, flags=re.IGNORECASE):
        prefix = text_norm[max(0, m.start() - 14) : m.start()]
        if re.search(r"(?:^|\s)\d{1,2}\s*-?\s*$", prefix):
            continue
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# OLLAMA TRIGGERS & SMALLTALK
# ═══════════════════════════════════════════════════════════════════════════════

OLLAMA_TOOL_TRIGGERS: List[str] = [
    'wetter', 'suche', 'finde', 'lösche', 'loesche', 'erstelle', 'termin',
    'mail', 'datei', 'pdf', 'erinnere', 'news', 'bild', 'route', 'distanz',
    'hauptstadt', 'währung', 'waehrung', 'einwohner', 'entfernung', 'weit',
    'wie lange nach', 'abstand', 'dauer', 'von', 'nach'
]

OLLAMA_SMALLTALK_PHRASES: List[str] = [
    'wer bist du', 'was kannst du', 'wie geht es', 'hallo', 'hi', 'hey',
    'kennst du', 'erzähl mir von', 'erzaehl mir von', 'was weißt du über',
    'was weisst du ueber', 'deine meinung zu'
]


# ═══════════════════════════════════════════════════════════════════════════════
# LOCAL BUSINESS INTENT
# ═══════════════════════════════════════════════════════════════════════════════

LOCAL_BUSINESS_KEYWORDS: List[str] = [
    'restaurant', 'restaurants', 'pizzeria', 'italienisch', 'italienische',
    'italienisches', 'cafe', 'café', 'bar', 'apotheke', 'arzt', 'ärzte',
    'zahnarzt', 'supermarkt', 'baumarkt', 'museum', 'kino', 'hotel',
    'geschäft', 'geschäfte', 'geschaeft', 'laden', 'bäckerei', 'baeckerei',
    'shop', 'poi', 'pois',
]

LOCAL_SEARCH_MARKERS: List[str] = [
    ' in ', ' nähe ', ' naehe ', ' nähe?', 'wo ist', 'wo sind',
    'suche mir', 'finde mir', 'empfiehl', 'empfehl'
]


# ═══════════════════════════════════════════════════════════════════════════════
# PERSONAL RECALL KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════════

PERSONAL_RECALL_KEYWORDS: List[str] = [
    'mein', 'meine', 'ich habe', 'meinem', 'meinen', 'meiner',
    'mein letztes', 'meine letzte', 'mein vorheriges', 'meine vorherige',
    'was habe ich', 'welches habe ich', 'wann habe ich', 'wo habe ich'
]


# ═══════════════════════════════════════════════════════════════════════════════
# FILESYSTEM INTENT KEYWORDS (TASK-001: BACKLOG-004)
# ═══════════════════════════════════════════════════════════════════════════════

# Filesystem-spezifische Keywords die Calendar-Keywords überschreiben sollen
FILESYSTEM_ACTION_MARKERS: Tuple[str, ...] = (
    "erstell",
    "erstellen",
    "erstelle",
    "erzeuge",
    "erzeugen",
    "erzeuge einen",
    "erstellen einen",
    "erstelle einen",
    "erstell",
    "verschiebe",
    "verschieben",
    "verschieb",
    "bewege",
    "bewegen",
    "kopiere",
    "kopieren",
    "kopier",
    "lösche",
    "loesche",
    "löschen",
    "loesch",
    "entferne",
    "entfernen",
    "umbenenne",
    "umbenennen",
    "erstellen ordner",
    "erstelle ordner",
    "erstell ordner",
    "erzeuge ordner",
    "ordner erstellen",
    "ordner erzeugen",
    "dateien verschieben",
    "dateien verschiebe",
    "datei verschieben",
    "datei verschiebe",
)

FILESYSTEM_OBJECT_MARKERS: Tuple[str, ...] = (
    "desktop",
    "ordner",
    "datei",
    "dateien",
    "verzeichnis",
    "verzeichnisse",
    "ordnern",
    "bilder",
    "dokumente",
    "downloads",
    "schreibtisch",
)

FILESYSTEM_PATH_MARKERS: Tuple[str, ...] = (
    "auf dem desktop",
    "in ordner",
    "in den ordner",
    "ins verzeichnis",
    "in das verzeichnis",
    "vom desktop",
    "vom ordner",
    "aus dem ordner",
)


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE INTENT KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════════

IMAGE_KEYWORDS: List[str] = ['bild', 'foto', 'zeichne', 'male', 'generiere']
IMAGE_INTENT_KEYWORDS: List[str] = ['bild', 'foto', 'zeichne', 'male', 'gemälde', 'illustration']

# Video: explizite Plattform oder „Video“ + Kontext (Tutorial, Rezept, Zeig…)
_VIDEO_CONTEXT_MARKERS: Tuple[str, ...] = (
    "tutorial",
    "anleitung",
    "rezept",
    "kochen",
    "backen",
    "pizzateig",
    "flammkuchen",
    "pizza",
    "teig",
    "zeig",
    "such",
    "finde",
    "wie man",
    "how to",
    "youtube",
    "youtu.be",
    "clip",
    # 💎 C7-DISPATCH-LOGIC-FIX: temporal/list/topic markers
    "letzt",       # letzte/letzten/letztes
    "neuest",      # neueste/neuesten
    "aktuell",     # aktuelle/aktuellen
    "über",        # Videos über [Thema]
    "ueber",       # ASCII fallback
    "welch",       # welche/welches Videos
    "liste",       # Videoliste, liste mir
    "top ",        # top 5 videos
)

# 💎 C7-DISPATCH-LOGIC-FIX: Strong regex for explicit video-list queries.
# Fires for: "letzte 3 videos", "3 videos von X", "zeig mir videos",
# "welche videos", "neueste videos", "videos von KANAL", "KANAL videos"
_VIDEO_LIST_RE: re.Pattern = re.compile(
    r'(?:'
    r'(?:letzte|letzten|neueste|neuesten|aktuelle|aktuellen)\s+\d*\s*(?:videos?|clips?)'
    r'|\d+\s+(?:videos?|clips?)'
    r'|(?:videos?|clips?)\s+(?:von|from|über|ueber)\s+\S'
    r'|(?:zeig|such|finde|gib|nenne)\s+.*?(?:videos?|clips?)'
    r'|(?:welche[rs]?|was für|wieviele?)\s+.*?(?:videos?|clips?)'
    r')',
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════════════════════════
# VIDEO UNDERSTANDING INTENT MARKERS
# ═══════════════════════════════════════════════════════════════════════════════

_VIDEO_UNDERSTANDING_MARKERS: Tuple[str, ...] = (
    "fass zusammen",
    "fasse zusammen",
    "zusammenfassung",
    "zusammenfassen",
    "erkläre das video",
    "erkläre mir das video",
    "erklär das video",
    "was wird in dem video",
    "worum geht es in dem video",
    "video zusammenfassen",
    "video erklären",
    "schritte aus dem video",
    "anleitung aus dem video",
    "transcript",
    "transkript",
)


# ═══════════════════════════════════════════════════════════════════════════════
# STORYBOOK INTENT KEYWORDS (CU-2: False-Positive Fix)
# ═══════════════════════════════════════════════════════════════════════════════

STORYBOOK_POSITIVE_KEYWORDS: Tuple[str, ...] = (
    "erzähle eine geschichte",
    "erzaehle eine geschichte",
    "kinderbuch",
    "illustriere",
    "illustriere",
    "mit den charakteren",
    "schreibe ein abenteuer",
    "schreib ein abenteuer",
    "märchen",
    "maerchen",
    "geschichte",
)

STORYBOOK_NEGATIVE_KEYWORDS: Tuple[str, ...] = (
    # Analyse/Zusammenfassung Keywords - diese dürfen Storybook-Intent NICHT auslösen
    "fass zusammen",
    "fasse zusammen",
    "zusammenfassen",
    "zusammenfassung",
    "analysiere",
    "analysieren",
    "gib mir eine übersicht",
    "gib mir eine uebersicht",
    "übersicht",
    "uebersicht",
    "zusammenfassung des textes",
    "zusammenfassung dieses textes",
)


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL VETO SYSTEM - Striktes Ausschlusskriterien-System für alle Intents
# ═══════════════════════════════════════════════════════════════════════════════

GENERAL_NEGATIVE_KEYWORDS: Tuple[str, ...] = (
    # Siehe apply_global_veto: nur für veto_eligible_intents wirksam.
    # Analyse/Zusammenfassung - darf kreative Workflows nicht auslösen
    "fass zusammen",
    "fasse zusammen",
    "zusammenfassen",
    "zusammenfassung",
    "analysiere",
    "analysieren",
    "gib mir eine übersicht",
    "gib mir eine uebersicht",
    "zusammenfassung des textes",
    "zusammenfassung dieses textes",
    # Debugging/Testing - darf keine Produktions-Workflows auslösen
    "debug",
    "debugging",
    # System-Commands - darf keine Workflows auslösen
    "system check",
    "system prüfung",
    "diagnose",
)


# ═══════════════════════════════════════════════════════════════════════════════
# META AGENT KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════════

META_PRODUCTION_KEYWORDS: Tuple[str, ...] = (
    'pdf', 'dokument', 'datei', 'export', 'speichern als'
)

META_RESEARCH_KEYWORDS: Tuple[str, ...] = (
    'recherchiere', 'suche', 'preis', 'kurs', 'wert', 'hauptstadt', 'einwohner'
)

META_TOPIC_INSTRUCTION_MAP: Dict[str, Dict[str, Any]] = {
    "klima": {
        "keywords": ["klima", "klimazon", "wetter", "temperature"],
        "instruction": "Beschreibe vorherrschende Klimazonen und wie das aktuelle Wetter dort Einfluss auf Reisen haben kann.",
    },
    "handel": {
        "keywords": ["handel", "export", "import", "wirtschaft"],
        "instruction": "Nenne aktuelle Handelsbeziehungen zu Deutschland, Europa oder global sowie Auswirkungen auf die Logistik.",
    },
    "kultur": {
        "keywords": ["kultur", "denkmal", "museum", "sehens"],
        "instruction": "Gib drei Kulturdenkmäler oder bedeutende Bauwerke pro Hauptstadt an und wieso sie relevant sind.",
    },
    "politik": {
        "keywords": ["politik", "politisch", "regierung", "präsident", "kanzler", "minister", "fuehrungsstruktur"],
        "instruction": "Fasse die politische Führungsstruktur und aktuelle Themen in kurzen Sätzen zusammen.",
    },
    "logistik": {
        "keywords": ["logistik", "route", "transport", "lieferkette"],
        "instruction": "Kommentiere, wie sich das Logistiknetz zuletzt verändert hat (Investitionen, Störungen, Chancen).",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# HELP SYSTEM KEYWORDS (FEAT-HELP-001)
# ═══════════════════════════════════════════════════════════════════════════════

# Exact triggers for capability overview (TASK-069.1)
# Normalized: lowercase, trimmed, whitespace collapsed, terminal ? removed
HELP_CAPABILITY_OVERVIEW_TRIGGERS: Tuple[str, ...] = (
    "was kannst du",
    "welche fähigkeiten hast du",
    "zeig mir deine fähigkeiten",
    "zeige mir deine fähigkeiten",
)

HELP_HOW_TO_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r'wie\s+kann\s+ich', re.IGNORECASE),
    re.compile(r'wie\s+funktioniert', re.IGNORECASE),
    re.compile(r'anleitung\s+für', re.IGNORECASE),
    re.compile(r'wie\s+benutze\s+ich', re.IGNORECASE),
    re.compile(r'wie\s+geht', re.IGNORECASE),
    re.compile(r'wie\s+mache\s+ich', re.IGNORECASE),
    re.compile(r'tutorial\s+für', re.IGNORECASE),
    re.compile(r'how\s+to', re.IGNORECASE),
)

HELP_NAVIGATION_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r'wo\s+finde\s+ich', re.IGNORECASE),
    re.compile(r'wo\s+ist', re.IGNORECASE),
    re.compile(r'wo\s+sind\s+(?:meine|die)', re.IGNORECASE),
    re.compile(r'wo\s+kann\s+ich\s+.*\s+finden', re.IGNORECASE),
    re.compile(r'wie\s+komme\s+ich\s+zu', re.IGNORECASE),
    re.compile(r'öffne\s+die', re.IGNORECASE),
    re.compile(r'zeig\s+mir\s+die', re.IGNORECASE),
)

MODEL_INTROSPECTION_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r'\bwelches?\s+(?:ki[- ]?)?modell\b', re.IGNORECASE),
    re.compile(r'\bmit\s+welchem\s+modell\s+(?:schreibe|arbeite|redest|chatte|nutze)\b', re.IGNORECASE),
    re.compile(r'welcher?\s+ki', re.IGNORECASE),
    re.compile(r'wer\s+bist\s+du\s+gerade', re.IGNORECASE),
    re.compile(r'mit\s+wem\s+schreibe\s+ich', re.IGNORECASE),
    re.compile(r'mit\s+welchem\s+modell', re.IGNORECASE),
    re.compile(r'was\s+bist\s+du\s+für\s+ein', re.IGNORECASE),
    re.compile(r'welcher?\s+provider', re.IGNORECASE),
    re.compile(r'welche?\s+stärke', re.IGNORECASE),
    re.compile(r'deine?\s+stärke', re.IGNORECASE),
    re.compile(r'wer\s+bist\s+du', re.IGNORECASE),
    re.compile(r'identität', re.IGNORECASE),
)


# ═══════════════════════════════════════════════════════════════════════════════
# FACT-TELLING PATTERNS (BUG-SYS-019)
# ═══════════════════════════════════════════════════════════════════════════════

_FACT_TELLING_PATTERNS: List[re.Pattern] = [
    # Kernaussagen (keine ^-Anker mehr!)
    re.compile(r'(mein|meine)\s+', re.IGNORECASE),           # "Mein Hund heißt..."
    re.compile(r'(ich\s+habe)\s+', re.IGNORECASE),           # "Ich habe einen Bruder..."
    re.compile(r'(ich\s+bin)\s+', re.IGNORECASE),             # "Ich bin 30 Jahre alt..."
    re.compile(r'(ich\s+mag)\s+', re.IGNORECASE),            # "Ich mag Kaffee..."
    re.compile(r'(ich\s+liebe)\s+', re.IGNORECASE),          # "Ich liebe Schokolade..."
    re.compile(r'(ich\s+heiße|ich\s+heiße)\s+', re.IGNORECASE),  # "Ich heiße Max..."
    re.compile(r'(mein\s+name\s+ist)\s+', re.IGNORECASE),   # "Mein Name ist Max..."
    re.compile(r'(ich\s+arbeite\s+als)\s+', re.IGNORECASE), # "Ich arbeite als..."
    re.compile(r'(ich\s+wohne\s+in)\s+', re.IGNORECASE),    # "Ich wohne in..."
    
    # BUG-SYS-019-V2: Einleitungs-Muster
    re.compile(r'(hier\s+sind|hier\s+ist|ich\s+erzähle\s+dir|merke\s+dir|infos?\s+über\s+mich|ein\s+paar\s+infos)', re.IGNORECASE),
]


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-REFERENCE GUARD (BUG-MEM-021)
# ═══════════════════════════════════════════════════════════════════════════════

SELF_REF_REGEX: re.Pattern = re.compile(
    r'(wer|was|wie|welche|wann).*(ich|mein|meine|meiner|meinem|mich|mir)',
    re.IGNORECASE,
)


# ═══════════════════════════════════════════════════════════════════════════════
# POLICY & CONSENT KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════════

POLICY_CONSENT_CHOICES: List[str] = [
    "1", "1.", "einmalig", "ja", "erlauben",
    "2", "2.", "immer",
    "3", "3.", "abbrechen", "nein",
]

ONE_TIME_POLICY_CHOICES: List[str] = ["1", "1.", "einmalig", "ja", "erlauben"]

POLICY_PROMPT_TOKENS: List[str] = [
    "diese aktion erfordert eine freigabe",
    "möchtest du die aktion 1. einmalig erlauben, 2. in zukunft immer ohne nachfragen erlauben, oder 3. abbrechen",
    "moechtest du die aktion 1. einmalig erlauben, 2. in zukunft immer ohne nachfragen erlauben, oder 3. abbrechen",
]


# ═══════════════════════════════════════════════════════════════════════════════
# INTENT ENGINE CLASS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class IntentDetectionResult:
    """Ergebnis einer Intent-Erkennung."""
    is_shopping_intent: bool = False
    is_calendar_intent: bool = False
    is_calendar_mutation: bool = False
    is_calendar_creation: bool = False
    mutation_target: Optional[str] = None   # Extrahiertes Subjekt der Mutation (z.B. "Sport", "Aldi")
    is_local_business_intent: bool = False
    is_personal_recall: bool = False
    is_image_intent: bool = False
    is_multitask_image_pdf: bool = False
    has_tool_trigger: bool = False
    is_ollama_vague_smalltalk: bool = False
    is_fact_telling: bool = False
    is_self_referential: bool = False
    is_policy_consent: bool = False
    is_one_time_policy: bool = False
    is_complex_document_request: bool = False
    is_simple_document_check: bool = False
    is_video_intent: bool = False
    is_video_list_intent: bool = False
    is_video_understanding_intent: bool = False
    # Help System Intents (FEAT-HELP-001)
    is_capability_overview: bool = False
    is_how_to: bool = False
    is_navigation_query: bool = False
    # Model Introspection (FEAT-HELP-002)
    is_model_query: bool = False
    # Routing / Entfernung (Diamond: vs. Kalender-Snapshot-Boost)
    is_routing_geo_intent: bool = False
    # Wetter / Temperatur (Diamond: vs. Kalender-Snapshot-Boost bei Ortsnamen)
    is_weather_intent: bool = False
    # PDF nur bei explizitem Wunsch (Diamond: kein proaktives create_pdf)
    is_explicit_pdf_intent: bool = False
    # Filesystem Intent (TASK-001: BACKLOG-004)
    is_filesystem_intent: bool = False
    # Wikipedia / Knowledge (BACKLOG-031: mandatory tool routing)
    is_wikipedia_intent: bool = False
    # News / RSS (BACKLOG-031: mandatory tool routing)
    is_news_intent: bool = False
    # 💎 BACKLOG-037: Ambiguity-Detection für Gemini
    is_ambiguous: bool = False
    ambiguity_confidence: float = 0.0  # 0.0-1.0, höher = ambiger

    primary_intent: Optional[str] = None
    vetoed_intents: Dict[str, str] = field(default_factory=dict)

    summary_global_veto: bool = False
    meta_agent_global_veto: bool = False
    named_channel_video: bool = False


class IntentEngine:
    """Central intent detection for the chat orchestrator (keyword lists and light NLP).

    The orchestrator calls these helpers instead of embedding raw strings or regex.
    Use the module singleton :data:`intent_engine` for the shared instance.
    """

    def __init__(self) -> None:
        """Wire keyword lists and compiled patterns used by detection methods."""
        self.ollama_tool_triggers = OLLAMA_TOOL_TRIGGERS
        self.ollama_smalltalk_phrases = OLLAMA_SMALLTALK_PHRASES
        self.local_business_keywords = LOCAL_BUSINESS_KEYWORDS
        self.local_search_markers = LOCAL_SEARCH_MARKERS
        self.personal_recall_keywords = PERSONAL_RECALL_KEYWORDS
        self.image_keywords = IMAGE_KEYWORDS
        self.image_intent_keywords = IMAGE_INTENT_KEYWORDS
        self.production_keywords = META_PRODUCTION_KEYWORDS
        self.research_keywords = META_RESEARCH_KEYWORDS
        self.topic_instruction_map = META_TOPIC_INSTRUCTION_MAP
        self.policy_consent_choices = POLICY_CONSENT_CHOICES
        self.one_time_policy_choices = ONE_TIME_POLICY_CHOICES
        self.policy_prompt_tokens = POLICY_PROMPT_TOKENS
        self.fact_telling_patterns = _FACT_TELLING_PATTERNS
        self.self_ref_regex = SELF_REF_REGEX
        # 💎 CU-2: Storybook Intent Keywords
        self.storybook_positive_keywords = STORYBOOK_POSITIVE_KEYWORDS
        self.storybook_negative_keywords = STORYBOOK_NEGATIVE_KEYWORDS
        # 💎 Global Veto System - Striktes Ausschlusskriterien-System für alle Intents
        self.general_negative_keywords = GENERAL_NEGATIVE_KEYWORDS
        # 💎 TASK-001: BACKLOG-004 - Filesystem Intent Keywords
        self.filesystem_action_markers = FILESYSTEM_ACTION_MARKERS
        self.filesystem_object_markers = FILESYSTEM_OBJECT_MARKERS
        self.filesystem_path_markers = FILESYSTEM_PATH_MARKERS

    def _has_price_signal(self, text_norm: str) -> bool:
        return bool(_PRICE_RE.search(text_norm))

    def _has_strong_shopping_signal(self, text_norm: str) -> bool:
        has_price = self._has_price_signal(text_norm)
        has_action = _contains_any_phrase(text_norm, SHOPPING_ACTION_MARKERS)
        has_product = _contains_any_phrase(text_norm, SHOPPING_PRODUCT_MARKERS)
        has_vendor = _contains_any_phrase(text_norm, SHOPPING_VENDOR_MARKERS)
        has_uhr_product = _has_uhr_product_signal(text_norm)
        productish = bool(has_product or has_vendor or has_uhr_product)
        return bool(
            ((has_action or has_price) and productish)
            or (has_price and has_action)
        )

    def _has_calendar_command_signal(self, text_norm: str) -> bool:
        has_command = _contains_any_phrase(text_norm, CALENDAR_COMMAND_MARKERS)
        has_object = _contains_any_phrase(text_norm, CALENDAR_OBJECT_MARKERS)
        has_date = _contains_any_phrase(text_norm, CALENDAR_DATE_MARKERS)
        has_time = bool(_CALENDAR_TIME_RE.search(text_norm))
        has_when = bool(has_date or has_time)
        has_activity_for_slot = bool(
            has_when and _contains_any_phrase(text_norm, CALENDAR_ACTIVITY_MARKERS),
        )
        return bool(
            has_command
            or (has_object and has_when)
            or has_activity_for_slot
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Global Veto System
    # ─────────────────────────────────────────────────────────────────────────

    def apply_global_veto(self, user_text: str, intent_name: str = "unknown") -> tuple[bool, str]:
        """Negative Keywords nur für ausgewählte kreative/workflows (Whitelist), nicht global für jeden Caller."""
        if not user_text:
            return False, ""

        intent_slug = str(intent_name or "unknown").lower().strip()
        veto_eligible_intents = frozenset(
            {"storybook", "meta_agent", "summary", "image", "complex_document"},
        )
        if intent_slug not in veto_eligible_intents:
            return False, ""

        text_norm = _normalize_text(user_text)

        # Check for global negative keywords (wortgrenzentreu via _contains_phrase)
        for kw in self.general_negative_keywords:
            if _contains_phrase(text_norm, kw):
                logger.warning(
                    "[GLOBAL VETO] Intent '%s' blocked by negative keyword: '%s' in text: '%s'",
                    intent_name,
                    kw,
                    user_text[:100] + "..." if len(user_text) > 100 else user_text
                )
                return True, f"Negative keyword '{kw}' detected"

        return False, ""

    # ─────────────────────────────────────────────────────────────────────────
    # Shopping Intent
    # ─────────────────────────────────────────────────────────────────────────

    def detect_shopping_intent(self, user_text: str) -> bool:
        """True nur bei kommerzieller Produkt-/Preis-Recherche — Kalender/scheduling hat Vorrang."""
        if not user_text:
            return False
        text_norm = _normalize_text(user_text)
        if not text_norm:
            return False
        if self._has_calendar_command_signal(text_norm):
            logger.debug("[SHOPPING-VETO] Calendar/scheduling detected — commerce intent suppressed.")
            return False
        return self._has_strong_shopping_signal(text_norm)

    def detect_calendar_intent(self, user_text: str) -> bool:
        """True bei Scheduling/Kalender, nicht durch lose Zeitwörter allein."""
        if not user_text:
            return False
        text_norm = _normalize_text(user_text)
        if not text_norm:
            return False
        if _RELEASE_TERMIN_RE.search(text_norm):
            return False
        if self._has_strong_shopping_signal(text_norm) and not self._has_calendar_command_signal(text_norm):
            logger.debug("[CALENDAR-VETO] Strong commerce signal without calendar scheduling cues.")
            return False
        # 💎 TASK-001: BACKLOG-004 - Filesystem-Intent Veto
        # Wenn Filesystem-Intent stark ist, Calendar-Intent unterdrücken
        if self.detect_filesystem_intent(user_text):
            logger.info(
                "[FILESYSTEM-OVERRIDE] Calendar intent suppressed by filesystem intent in text: '%s'",
                user_text[:100] + "..." if len(user_text) > 100 else user_text
            )
            return False
        return self._has_calendar_command_signal(text_norm)

    # ─────────────────────────────────────────────────────────────────────────
    # Filesystem Intent (TASK-001: BACKLOG-004)
    # ─────────────────────────────────────────────────────────────────────────

    def detect_filesystem_intent(self, user_text: str) -> bool:
        """True bei Dateisystem-Operationen (Ordner erstellen, Dateien verschieben, etc.).

        Filesystem-Keywords haben Vorrang vor Calendar-Keywords um Fehlklassifikationen
        zu vermeiden (z.B. "Ordner erstellen" sollte nicht als Calendar-Intent erkannt werden).

        Ausnahme: Calendar-spezifische Objekte wie "termin", "meeting" haben Vorrang.
        """
        if not user_text:
            return False
        text_norm = _normalize_text(user_text)
        if not text_norm:
            return False

        # 💎 TASK-001: Calendar-spezifische Objekte haben Vorrang vor Filesystem
        # Wenn Calendar-Objekte wie "termin", "meeting" vorhanden sind, ist es kein Filesystem-Intent
        calendar_object_keywords = ("termin", "meeting", "kalendereintrag", "verabredung")
        has_calendar_object = _contains_any_phrase(text_norm, calendar_object_keywords)
        if has_calendar_object:
            logger.debug(
                "[FILESYSTEM-INTENT] Skipped: calendar object detected in text: '%s'",
                user_text[:100] + "..." if len(user_text) > 100 else user_text
            )
            return False

        has_action = _contains_any_phrase(text_norm, self.filesystem_action_markers)
        has_object = _contains_any_phrase(text_norm, self.filesystem_object_markers)
        has_path = _contains_any_phrase(text_norm, self.filesystem_path_markers)

        # Filesystem-Intent wenn: Action + Object ODER Action + Path
        is_filesystem = (has_action and has_object) or (has_action and has_path)

        if is_filesystem:
            logger.debug(
                "[FILESYSTEM-INTENT] Detected: action=%s, object=%s, path=%s in text: '%s'",
                has_action, has_object, has_path,
                user_text[:100] + "..." if len(user_text) > 100 else user_text
            )

        return is_filesystem

    # ─────────────────────────────────────────────────────────────────────────
    # Local Business Intent
    # ─────────────────────────────────────────────────────────────────────────
    
    def detect_local_business_intent(self, user_text: str) -> bool:
        """Return True for local POI-style queries (e.g. restaurant + “near me” markers)."""
        if not user_text:
            return False
        text_lower = user_text.lower()
        padded_text = f' {text_lower} '
        has_business_kw = any(kw in text_lower for kw in self.local_business_keywords)
        has_search_marker = any(
            marker in padded_text or marker in text_lower
            for marker in self.local_search_markers
        )
        return has_business_kw and has_search_marker
    
    # ─────────────────────────────────────────────────────────────────────────
    # Ollama Intents
    # ─────────────────────────────────────────────────────────────────────────
    
    def has_ollama_tool_trigger(self, user_text: str) -> bool:
        """Return True if the text contains tokens that usually warrant a tool-capable local model."""
        if not user_text:
            return False
        text_lower = user_text.lower()
        return any(trigger in text_lower for trigger in self.ollama_tool_triggers)
    
    def is_ollama_vague_smalltalk(self, user_text: str) -> bool:
        """Return True for short/vague phrasing that should not force tool routing on Ollama."""
        if not user_text:
            return False
        text_lower = user_text.lower()
        return any(phrase in text_lower for phrase in self.ollama_smalltalk_phrases)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Personal Recall
    # ─────────────────────────────────────────────────────────────────────────
    
    def detect_personal_recall(self, user_text: str) -> bool:
        """Return True when the user asks about their own memories or prior statements."""
        if not user_text:
            return False
        # Video-Anfragen duerfen nicht als Personal-Recall fehlklassifiziert werden.
        # Sonst blockiert der Precedence-Guard system.websearch fuer Video-Intents.
        if self.detect_video_intent(user_text):
            return False
        text_lower = user_text.lower()
        return any(kw in text_lower for kw in self.personal_recall_keywords)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Image Intent
    # ─────────────────────────────────────────────────────────────────────────
    
    def detect_image_intent(self, user_text: str) -> bool:
        """Return True if the user is asking for an image, drawing, or illustration."""
        if not user_text:
            return False
        text_lower = user_text.lower()
        return any(kw in text_lower for kw in self.image_intent_keywords)

    # ─────────────────────────────────────────────────────────────────────────
    # Storybook Intent (CU-2: False-Positive Fix)
    # ─────────────────────────────────────────────────────────────────────────

    def detect_storybook_intent(self, user_text: str, has_pdf: bool = False) -> bool:
        """
        Return True if the user wants a children's book with illustrations (Storybook Macro).

        CU-2: Fixed false-positive by adding exclusion criteria for analysis/summarization requests.
        Global Veto: Applies strict veto system across all intents to prevent false-positives.

        Args:
            user_text: The user's prompt text
            has_pdf: Whether the prompt mentions PDF (required for Storybook Macro)

        Returns:
            True only if positive keywords are present AND no negative keywords are present AND pdf is mentioned.
        """
        if not user_text:
            return False
        text_lower = user_text.lower()

        # 💎 GLOBAL VETO: Striktes Veto-System - prüft globale negative Keywords
        vetoed, veto_reason = self.apply_global_veto(user_text, "storybook")
        if vetoed:
            logger.warning("[GLOBAL VETO] Storybook intent blocked: %s", veto_reason)
            return False

        # 💎 CU-2: Negative Bedingungen (Ausschlusskriterien) - Analyse/Zusammenfassung darf NICHT auslösen
        has_negative = any(kw in text_lower for kw in self.storybook_negative_keywords)
        if has_negative:
            logger.debug("[CU-2] Storybook intent blocked by storybook-specific negative keyword")
            return False

        # Positive Bedingungen - kreative Aufforderungen müssen vorhanden sein
        has_positive = any(kw in text_lower for kw in self.storybook_positive_keywords)

        # Bild/Illustration muss erwähnt werden
        has_image = any(kw in text_lower for kw in ['bild', 'illustration', 'zeichn', 'illustrier'])

        # PDF muss erwähnt werden (für Storybook Macro)
        has_pdf_kw = 'pdf' in text_lower

        # Storybook-Intent nur bei allen Bedingungen: Positive + Bild + PDF
        result = has_positive and has_image and has_pdf_kw
        if result:
            logger.info("[CU-2] Storybook intent detected (positive=%s, image=%s, pdf=%s)", has_positive, has_image, has_pdf_kw)
        return result

    def detect_named_channel_video_intent(self, user_text: str) -> bool:
        """True wenn der Nutzer einen konkreten Kanal nennt (von X, Kanal X, …) — sofort Channel-Lock / video.search."""
        if not user_text:
            return False
        t = user_text.lower()
        p = f" {t} "
        if " vom kanal " in p or " from channel " in p:
            return True
        if re.search(r"(?:^|\s)(?:kanal|channel)\s+[a-z0-9]", t, re.IGNORECASE):
            return True
        if " von " in p:
            if any(
                k in t
                for k in (
                    "video",
                    "youtube",
                    "youtu",
                    "clip",
                    "neuest",
                    "letzt",
                    "aktuell",
                    "upload",
                    "livestream",
                    "stream",
                    "zeig",
                    "such",
                    "finde",
                )
            ):
                return True
        # 💎 C7-DISPATCH-LOGIC-FIX: Detect proper-noun channel adjacent to "video(s)"
        # e.g. "DICED videos", "videos DICED", "MrBeast clips"
        if re.search(r'(?:videos?|clips?)\s+[A-Z][A-Za-z0-9_-]{1,}', user_text):
            return True
        if re.search(r'[A-Z][A-Za-z0-9_-]{1,}\s+(?:videos?|clips?)', user_text):
            return True
        return False

    def detect_video_list_intent(self, user_text: str) -> bool:
        """True wenn der Nutzer explizit eine Video-LISTE will (mehrere Videos, Top N, letzte N, von Kanal).

        This is a stricter subset of detect_video_intent — it only fires for
        multi-video / list queries, not for single-video requests like
        'zeig mir ein Tutorial'.
        """
        if not user_text:
            return False
        t = user_text.lower()
        # Regex already covers: letzte N videos, N videos, videos von X,
        # zeig/such/finde + videos, welche videos
        if _VIDEO_LIST_RE.search(t):
            return True
        # Named channel + video(s) implies a list intent ("DICED videos")
        if self.detect_named_channel_video_intent(user_text):
            if "video" in t or "clip" in t:
                return True
        return False

    def should_disable_streaming(self, user_text: str) -> bool:
        """True wenn Streaming zugunsten einer Block-Antwort deaktiviert werden soll.

        Aktuell: Video-Listen-Intents → Block-Response für stabile Markdown-Links.
        """
        return self.detect_video_list_intent(user_text)

    def detect_video_intent(self, user_text: str) -> bool:
        """True wenn der Nutzer ein (YouTube-)Video, Tutorial-Clip oder explizit YouTube meint."""
        if not user_text:
            return False
        if self.detect_named_channel_video_intent(user_text):
            return True
        t = user_text.lower()
        if "youtube" in t or "youtu.be" in t:
            return True
        # 💎 C7-DISPATCH-LOGIC-FIX: Strong regex catches explicit video-list patterns
        if _VIDEO_LIST_RE.search(t):
            return True
        if "video" not in t and "clip" not in t:
            return False
        return any(m in t for m in _VIDEO_CONTEXT_MARKERS)

    def detect_video_understanding_intent(self, user_text: str) -> bool:
        """True wenn der Nutzer ein Video zusammenfassen, erklären oder Schritte extrahieren möchte."""
        if not user_text:
            return False
        t = user_text.lower()
        # Check exact markers
        if any(m in t for m in _VIDEO_UNDERSTANDING_MARKERS):
            return True
        # Check for split patterns: "fasse ... zusammen" or "fass ... zusammen"
        if ("fass" in t or "fasse" in t) and "zusammen" in t and "video" in t:
            return True
        return False

    def detect_multitask_image_pdf(self, user_text: str) -> bool:
        """Return True when the user wants both an image and a PDF in one turn."""
        if not user_text:
            return False
        text_lower = user_text.lower()
        has_image = any(kw in text_lower for kw in ['bild', 'foto'])
        has_pdf = 'pdf' in text_lower
        return has_image and has_pdf
    
    # ─────────────────────────────────────────────────────────────────────────
    # Fact-Telling (BUG-SYS-019)
    # ─────────────────────────────────────────────────────────────────────────
    
    def is_fact_telling_pattern(self, user_text: str) -> bool:
        """
        BUG-SYS-019: Erkennt wenn Nutzer persönliche Fakten teilt.
        
        Returns True wenn Pattern wie "Mein/Meine...", "Ich habe...",
        "Ich bin...", "Ich mag..." erkannt wird.
        """
        if not user_text:
            return False
        
        lines = user_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            for pattern in self.fact_telling_patterns:
                if pattern.search(line):
                    logger.debug(
                        "[INTENT-ENGINE] [BUG-SYS-019] Fact-telling pattern detected: %r (line: %r)",
                        pattern.pattern,
                        line[:50],
                    )
                    return True
        return False
    
    # ─────────────────────────────────────────────────────────────────────────
    # Self-Referential Guard (BUG-MEM-021)
    # ─────────────────────────────────────────────────────────────────────────
    
    def is_self_referential_query(self, user_text: str) -> bool:
        """Return True for self-referential questions (e.g. who/what/how + me/my) for recall guards."""
        if not user_text:
            return False
        return bool(self.self_ref_regex.search(user_text))
    
    # ─────────────────────────────────────────────────────────────────────────
    # Policy & Consent
    # ─────────────────────────────────────────────────────────────────────────
    
    def is_policy_consent_choice(self, user_text_clean: str) -> bool:
        """Return True if ``user_text_clean`` is one of the numbered policy consent replies."""
        return user_text_clean in self.policy_consent_choices
    
    def is_one_time_policy_choice(self, user_text_clean: str) -> bool:
        """Return True if the user chose a one-time allow path in a policy dialog."""
        return user_text_clean in self.one_time_policy_choices
    
    def is_policy_prompt_text(self, text: str) -> bool:
        """Return True if assistant text contains the standard policy-consent prompt tokens."""
        haystack = str(text or "").lower()
        return any(token in haystack for token in self.policy_prompt_tokens)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Complex Document Request (Meta-Agent)
    # ─────────────────────────────────────────────────────────────────────────
    
    def detect_complex_document_request(self, user_text: str) -> bool:
        """
        Erkennt komplexe Dokument-Anfragen (Production + Research Keywords).
        
        DIAMOND-FIX: "Erstelle" allein darf keinen PDF-Flow auslösen.
        Es muss explizit nach einem physischen Dateiformat gefragt werden.
        """
        if not user_text:
            return False
        
        text_lower = user_text.lower()
        has_production = any(keyword in text_lower for keyword in self.production_keywords)
        has_research = any(keyword in text_lower for keyword in self.research_keywords)
        
        return has_production and has_research
    
    def is_simple_document_check(self, user_text: str) -> bool:
        """Return True for very short “check this document” style prompts (planner fast-path)."""
        if not user_text:
            return False
        text_lower = user_text.lower()
        has_check = bool(re.search(r'\bpr[üu]f(?:e|en)?\b', text_lower))
        has_document = 'dokument' in text_lower
        is_short = len(text_lower.split()) <= 6
        return has_check and has_document and is_short
    
    # ─────────────────────────────────────────────────────────────────────────
    # Topic Instructions (Meta-Agent)
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_topic_instruction(self, user_text: str) -> Optional[str]:
        """Return the meta-agent topic instruction string when ``META_TOPIC_INSTRUCTION_MAP`` matches."""
        if not user_text:
            return None
        text_lower = user_text.lower()
        for topic_config in self.topic_instruction_map.values():
            if any(kw in text_lower for kw in topic_config["keywords"]):
                return topic_config["instruction"]
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # Help System Intents (FEAT-HELP-001)
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_intent_text(text: str) -> str:
        """Normalize user text for exact intent matching.

        Rules (TASK-069.1 / TASK-069.14):
        - casefold (robust lowercase for international characters)
        - trim leading/trailing whitespace
        - collapse multiple whitespace to single space
        - strip trailing punctuation (?, !, ., spaces) — handles multiple marks
        """
        if not text:
            return ""
        text = text.casefold().strip()
        text = re.sub(r"\s+", " ", text)
        # Strip trailing punctuation marks and spaces (TASK-069.14)
        text = text.rstrip("?!. ")
        return text

    def detect_capability_overview(self, user_text: str) -> bool:
        """Return True for capability overview queries ("Was kannst du?", "Features").

        TASK-069.1: Exact trigger list with normalization — no regex substring matching.
        """
        if not user_text:
            return False
        normalized = self._normalize_intent_text(user_text)
        return normalized in HELP_CAPABILITY_OVERVIEW_TRIGGERS

    def detect_how_to(self, user_text: str) -> bool:
        """Return True for how-to instructions requests ("Wie kann ich...", "Anleitung für")."""
        if not user_text:
            return False
        if intent_classifier.is_greeting(user_text):
            return False
        return any(pattern.search(user_text) for pattern in HELP_HOW_TO_PATTERNS)

    @staticmethod
    def detect_routing_geo_intent(user_text: str) -> bool:
        """True bei Entfernungs-/Routenfragen zwischen Orten (nicht Kalender-Inhalt).

        Unterdrückt fälschlichen Kalender-Snapshot-Boost, wenn nur Stadtnamen
        zufällig mit Event-Titeln überlappen.
        
        BACKLOG-036: Erweitert um einfache "von X" Muster ohne "nach" (z.B. "Wie weit ist Berlin von München?")
        """
        if not user_text or not user_text.strip():
            return False
        t = user_text.strip()
        if not _ROUTING_GEO_MARKERS.search(t):
            return False
        # BACKLOG-036: Prüfe auf "von X nach", "from X to", "zwischen X und" ODER einfaches "von X"
        return bool(
            _ROUTING_VON_NACH_DE.search(t)
            or _ROUTING_FROM_TO_EN.search(t)
            or _ROUTING_ZWISCHEN_UND.search(t)
            or re.search(r"\bvon\s+[^\n,?\.!]{1,52}\b", t)  # BACKLOG-036: Einfaches "von X" Muster
        )

    @staticmethod
    def detect_weather_intent(user_text: str) -> bool:
        """True bei Wetter-, Temperatur- oder Vorhersagefragen.

        Unterdrückt fälschlichen Kalender-Snapshot-Boost (z. B. „München“ im Event
        und gleichzeitige Wetterfrage zu München).
        """
        if not user_text or not user_text.strip():
            return False
        t = user_text.casefold()
        if re.search(r"\b(?:regen|regnen|regnet|niederschlag|regenschirm)\b", t):
            return True
        if re.search(r"\bwie\s+(?:ist|wird)\s+(?:das\s+)?wetter\b", t):
            return True
        if "wettervorhersage" in t:
            return True
        if re.search(r"\bwetterlage\b", t):
            return True
        if re.search(r"\bwetter\s+(?:in|für|bei|von|heute|morgen|übermorgen|aktuell|jetzt|gerade)\b", t):
            return True
        if re.search(r"\btemperatur\s+(?:in|für|bei|von|heute|morgen)\b", t):
            return True
        if re.search(
            r"\b(?:regen|regnet|niederschlag|gewitter|sturm|schnee|bewölkung|bewoelkung|sonne|kalt|warm)\b",
            t,
        ) and re.search(r"\b(?:in|für|bei)\b", t):
            return True
        if re.search(r"\bhow(?:'s|\s+is)\s+(?:the\s+)?weather\b", t):
            return True
        if re.search(r"\bweather\s+(?:forecast|in|for|today|tomorrow)\b", t):
            return True
        if re.search(r"\btemperature\b", t) and re.search(r"\b(?:in|for|at)\b", t):
            return True
        return False

    @staticmethod
    def detect_wikipedia_intent(user_text: str) -> bool:
        """True bei Wikipedia-/Wissensfragen über Personen, Konzepte, Ereignisse.
        
        BACKLOG-031: Erkennt Anfragen für system.wikipedia_summary Tool.
        """
        if not user_text or not user_text.strip():
            return False
        t = user_text.casefold()
        # Explizite Wikipedia-Marker
        if "wikipedia" in t:
            return True
        # Person- und Konzept-Fragen
        if re.search(r"\b(?:wer ist|wer war|was ist|was war|erzähl mir über|erzähle mir über|sag mir über|info über|informationen über)\b", t):
            return True
        # Biografie-Marker
        if re.search(r"\b(?:biografie|biographie|leben|geboren|gestorben)\b", t):
            return True
        # Wissensfragen
        if re.search(r"\b(?:was weißt du über|was weisst du über|erklär mir|erkläre mir)\b", t):
            return True
        # Historische Ereignisse
        if re.search(r"\b(?:wann geschah|wann passierte|historie|geschichte)\b", t):
            return True
        return False

    @staticmethod
    def detect_news_intent(user_text: str) -> bool:
        """True bei Nachrichten-/News-Abfragen.
        
        BACKLOG-031: Erkennt Anfragen für system.rss_news Tool.
        """
        if not user_text or not user_text.strip():
            return False
        t = user_text.casefold()
        # Explizite News-Marker
        if re.search(r"\b(?:news|nachrichten|neuigkeiten|schlagzeilen|aktuell|neueste|latest news)\b", t):
            return True
        # Was gibt es Neues-Muster
        if re.search(r"\bwas gibt es neues\b", t):
            return True
        # Heise/Tagesschau-spezifisch
        if re.search(r"\b(?:heise|tagesschau|spiegel|zeit)\b", t):
            return True
        # Tagesaktuelle Fragen
        if re.search(r"\b(?:heute|morgen|gestern)\s+.*\b(?:news|nachrichten)\b", t):
            return True
        return False

    @staticmethod
    def detect_explicit_pdf_intent(user_text: str) -> bool:
        """True, wenn der Nutzer ausdrücklich ein PDF-/Export-Ziel fordert."""
        if not user_text or not user_text.strip():
            return False
        return bool(_EXPLICIT_PDF_INTENT.search(user_text))

    def detect_navigation(self, user_text: str) -> bool:
        """Return True for navigation queries ("Wo finde ich...", "Wo ist...").

        Dateinamen mit Extensions (z.B. .pdf, .txt, .docx) sollen den Fast-Path
        NICHT triggern, sondern zum normalen filesystem Skill-Router gehen.
        """
        if not user_text:
            return False

        # Guard: Wenn Dateiendung erkannt wird → kein Navigation-Intent
        # (soll zum filesystem Skill-Router gehen)
        _FILE_EXTENSIONS = (
            '.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
            '.mp4', '.mp3', '.wav', '.flac', '.zip', '.rar', '.7z',
            '.json', '.xml', '.csv', '.md', '.html', '.css', '.js',
            '.py', '.java', '.c', '.cpp', '.h', '.php', '.rb', '.go',
            '.ts', '.tsx', '.jsx', '.vue', '.svelte', '.sql', '.db',
        )
        text_lower = user_text.lower()
        for ext in _FILE_EXTENSIONS:
            if ext in text_lower:
                logger.debug(
                    "[INTENT-ENGINE] Navigation blocked by file extension guard: %s in %r",
                    ext,
                    user_text[:60],
                )
                return False

        return any(pattern.search(user_text) for pattern in HELP_NAVIGATION_PATTERNS)

    def detect_model_introspektion(self, user_text: str) -> bool:
        """Return True for model introspection queries ("Welches Modell?", "Mit wem schreibe ich?")."""
        if not user_text:
            return False
        return any(pattern.search(user_text) for pattern in MODEL_INTROSPECTION_PATTERNS)

    def detect_calendar_mutation_intent(self, user_text: str) -> bool:
        """True wenn der User einen bestehenden Kalender-Eintrag mutieren will."""
        if not user_text:
            return False
        text_norm = _normalize_text(user_text)
        return _contains_any_phrase(text_norm, _MUTATION_VERBS_AND_TRIGGERS)

    def detect_calendar_creation_intent(self, user_text: str) -> bool:
        """True wenn der User einen *neuen* Kalender-Termin anlegen will.

        Wird VOR der Mutations-Erkennung geprüft, damit explizite Erstellungs-
        Phrasen nicht fälschlicherweise als Mutation klassifiziert werden.
        """
        if not user_text:
            return False
        text_norm = _normalize_text(user_text)
        return _contains_any_phrase(text_norm, _CALENDAR_CREATION_MARKERS)

    # ─────────────────────────────────────────────────────────────────────────
    # Combined Detection
    # ─────────────────────────────────────────────────────────────────────────
    
    def detect_all_intents(
        self,
        user_text: str,
        *,
        calendar_snapshot: Optional[Dict[str, Any]] = None,
    ) -> IntentDetectionResult:
        """Run the full intent battery once; hierarchische Auflösung Shopping vs. Kalender."""
        text_clean = user_text.strip().lower() if user_text else ""
        summary_global_veto, _ = self.apply_global_veto(user_text, "summary")
        meta_agent_global_veto, _ = self.apply_global_veto(user_text, "meta_agent")
        named_channel_video = bool(self.detect_named_channel_video_intent(user_text))

        calendar_lex = self.detect_calendar_intent(user_text)
        shopping_on = self.detect_shopping_intent(user_text)
        vetoed: Dict[str, str] = {}
        text_norm = _normalize_text(user_text) if user_text else ""

        routing_geo_on = self.detect_routing_geo_intent(user_text)
        weather_on = self.detect_weather_intent(user_text)
        wikipedia_on = self.detect_wikipedia_intent(user_text)
        news_on = self.detect_news_intent(user_text)
        snapshot_overlap = calendar_user_text_overlap_snapshot(user_text, calendar_snapshot)

        commerce_blocks_snapshot_calendar = (
            self._has_strong_shopping_signal(text_norm)
            and not self._has_calendar_command_signal(text_norm)
        )
        snapshot_calendar_on = (
            snapshot_overlap
            and not commerce_blocks_snapshot_calendar
            and not routing_geo_on
            and not weather_on
        )

        if snapshot_calendar_on:
            logger.info(
                "[CAL-SNAPSHOT-INTENT] Calendar intent boosted: User-Text overlappt Snapshot-Ereignis (Titel/Ort).",
            )
        elif snapshot_overlap and routing_geo_on:
            logger.info(
                "[CAL-SNAPSHOT-INTENT] Snapshot-Overlap verworfen — Routing-/Entfernungsfrage (routing_geo).",
            )
        elif snapshot_overlap and weather_on:
            logger.info(
                "[CAL-SNAPSHOT-INTENT] Snapshot-Overlap verworfen — Wetterfrage (weather).",
            )

        calendar_on = bool(calendar_lex or snapshot_calendar_on)

        if calendar_on and shopping_on:
            if self._has_calendar_command_signal(text_norm):
                shopping_on = False
                vetoed["shopping"] = "calendar_command"
            elif snapshot_calendar_on:
                shopping_on = False
                vetoed["shopping"] = "calendar_snapshot_anchor"
            else:
                calendar_on = False
                vetoed["calendar"] = "strong_shopping_signal"

        _is_creation = bool(calendar_on and self.detect_calendar_creation_intent(user_text))
        if _is_creation:
            logger.info("[CAL-CREATION] Kalender-Erstellungsabsicht erkannt.")

        # Mutation check: creation takes precedence — an explicit "erstelle Termin" phrase
        # must never also trigger is_calendar_mutation.
        _is_mutation = bool(
            calendar_on
            and not _is_creation
            and self.detect_calendar_mutation_intent(user_text)
        )
        _mutation_target = _extract_mutation_target(user_text) if _is_mutation else None
        if _is_mutation:
            logger.info(
                "[CAL-MUTATION] Kalender-Mutation erkannt — Subjekt: %r",
                _mutation_target,
            )

        # Fact-telling detection (BUG-SYS-019)
        _is_fact_telling = self.is_fact_telling_pattern(user_text)
        
        # 💎 BACKLOG-037: Ambiguity-Detection für Gemini
        _is_ambiguous, _ambiguity_confidence = detect_ambiguity_in_query(user_text)
        if _is_ambiguous:
            logger.info(
                "[AMBIGUITY-DETECTION] Ambige Anfrage erkannt: confidence=%.2f, query=%r",
                _ambiguity_confidence,
                user_text[:50],
            )
        
        # Guard: Calendar mutation beats fact-telling
        # If calendar mutation is detected, fact-telling pattern should not override
        # the intent to personal_recall. Calendar tools must be loaded even when
        # "mein/meine" is present in the user's text.
        if _is_mutation and _is_fact_telling:
            logger.info(
                "[INTENT-ENGINE] Calendar mutation detected — overriding fact-telling pattern "
                "(BUG-SYS-019 guard: mutation beats personal_recall)"
            )
            _is_fact_telling = False

        result = IntentDetectionResult(
            is_shopping_intent=shopping_on,
            is_calendar_intent=calendar_on,
            is_calendar_mutation=_is_mutation,
            is_calendar_creation=_is_creation,
            mutation_target=_mutation_target,
            is_local_business_intent=self.detect_local_business_intent(user_text),
            is_personal_recall=self.detect_personal_recall(user_text),
            is_image_intent=self.detect_image_intent(user_text),
            is_multitask_image_pdf=self.detect_multitask_image_pdf(user_text),
            has_tool_trigger=self.has_ollama_tool_trigger(user_text),
            is_ollama_vague_smalltalk=self.is_ollama_vague_smalltalk(user_text),
            is_fact_telling=_is_fact_telling,
            is_self_referential=self.is_self_referential_query(user_text),
            is_policy_consent=self.is_policy_consent_choice(text_clean),
            is_one_time_policy=self.is_one_time_policy_choice(text_clean),
            is_complex_document_request=self.detect_complex_document_request(user_text),
            is_simple_document_check=self.is_simple_document_check(user_text),
            is_video_intent=self.detect_video_intent(user_text),
            is_video_list_intent=self.detect_video_list_intent(user_text),
            is_video_understanding_intent=self.detect_video_understanding_intent(user_text),
            is_capability_overview=self.detect_capability_overview(user_text),
            is_how_to=self.detect_how_to(user_text),
            is_navigation_query=self.detect_navigation(user_text),
            is_model_query=self.detect_model_introspektion(user_text),
            is_routing_geo_intent=routing_geo_on,
            is_weather_intent=weather_on,
            is_wikipedia_intent=wikipedia_on,
            is_news_intent=news_on,
            is_explicit_pdf_intent=self.detect_explicit_pdf_intent(user_text),
            is_filesystem_intent=self.detect_filesystem_intent(user_text),
            is_ambiguous=_is_ambiguous,
            ambiguity_confidence=_ambiguity_confidence,
            vetoed_intents=vetoed,
            summary_global_veto=summary_global_veto,
            meta_agent_global_veto=meta_agent_global_veto,
            named_channel_video=named_channel_video,
        )

        precedence = (
            ("policy_consent", result.is_policy_consent),
            ("video_understanding", result.is_video_understanding_intent),
            ("multitask_image_pdf", result.is_multitask_image_pdf),
            # 💎 TASK-005: BACKLOG-005 - Filesystem-Intent hat Vorrang vor Bild-Intent
            ("filesystem", result.is_filesystem_intent),
            ("image", result.is_image_intent),
            ("calendar", result.is_calendar_intent),
            ("local_business", result.is_local_business_intent),
            ("shopping", result.is_shopping_intent),
            ("routing_geo", result.is_routing_geo_intent),
            ("weather", result.is_weather_intent),
            ("wikipedia", result.is_wikipedia_intent),
            ("news", result.is_news_intent),
            ("video_list", result.is_video_list_intent),
            ("video", result.is_video_intent),
            ("personal_recall", result.is_personal_recall),
            ("model_query", result.is_model_query),
            ("capability_overview", result.is_capability_overview),
            ("how_to", result.is_how_to),
            ("navigation", result.is_navigation_query),
            ("complex_document", result.is_complex_document_request),
        )
        result.primary_intent = next((name for name, active in precedence if active), None)
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# Gemini-spezifische Ambiguity-Detection (BACKLOG-037)
# ═══════════════════════════════════════════════════════════════════════════════

# Deiktische Referenzen die auf Ambiguity hindeuten
_AMBIGUITY_DEICTIC_MARKERS = frozenset({
    "dazu", "das", "dies", "diese", "jener", "jenem", "welche", "welcher", "welchen",
    "etwas", "irgendwas", "irgendwo", "irgendwie"
})

# Sehr kurze Anfragen die oft ambig sind
_AMBIGUITY_SHORT_QUERY_THRESHOLD = 4  # Wörter oder weniger


def detect_ambiguity_in_query(query: str) -> tuple[bool, float]:
    """
    Erkennt ambige Anfragen basierend auf deiktischen Markern und Länge.
    
    Returns:
        (is_ambiguous, confidence_score) wobei confidence_score 0.0-1.0 ist
        (1.0 = sehr ambig, 0.0 = nicht ambig)
    """
    if not query:
        return True, 1.0
    
    query_norm = _normalize_text(query)
    query_lower = query_norm.lower()
    words = query_lower.split()

    if re.search(r"\b(?:wetter|regen|regnen|regnet|niederschlag)\b", query_lower) and not re.search(
        r"\b(?:in|fÃ¼r|fuer|bei|von)\s+[a-zÃ¤Ã¶Ã¼ÃŸ][\wÃ¤Ã¶Ã¼ÃŸ.-]{2,}",
        query_lower,
    ):
        return True, 0.8

    # "das" is an article in explicit weather questions, not a deictic marker.
    if (
        re.search(r"\bwie\s+(?:ist|wird)\s+(?:das\s+)?wetter\b", query_lower)
        or re.search(r"\bwetter\s+(?:in|für|fuer|bei|von|heute|morgen|übermorgen|uebermorgen|aktuell|jetzt|gerade)\b", query_lower)
        or "wettervorhersage" in query_lower
    ):
        return False, 0.0
    
    # Check 1: Deiktische Marker (stärkste Ambiguity-Indikation - zuerst prüfen)
    has_deictic = any(
        re.search(rf"\b{re.escape(marker)}\b", query_lower)
        for marker in _AMBIGUITY_DEICTIC_MARKERS
    )
    if has_deictic:
        # Deiktische Marker erhöhen Ambiguity
        deictic_count = sum(
            1
            for marker in _AMBIGUITY_DEICTIC_MARKERS
            if re.search(rf"\b{re.escape(marker)}\b", query_lower)
        )
        confidence = min(0.9, 0.7 + (deictic_count * 0.1))
        return True, confidence
    
    # Check 2: Sehr kurze Anfragen
    if len(words) <= _AMBIGUITY_SHORT_QUERY_THRESHOLD:
        # Je kürzer, desto ambiger
        confidence = 1.0 - ((len(words) - 1) / _AMBIGUITY_SHORT_QUERY_THRESHOLD)
        return True, confidence
    
    # Check 3: Anfragen ohne klare Intent-Keywords
    # (keine Verben wie "suche", "finde", "erstelle", etc.)
    intent_verbs = {"suche", "finde", "erstell", "mach", "gib", "zeig", "sag", "schreib", "erstelle"}
    has_intent_verb = any(verb in query_lower for verb in intent_verbs)
    
    if not has_intent_verb and len(words) <= 6:
        # Kurze Anfrage ohne Intent-Verb = potentiell ambig
        return True, 0.7
    
    return False, 0.0


# Singleton-Instanz für globalen Zugriff
intent_engine = IntentEngine()
