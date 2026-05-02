"""Diamond Intent Engine - Extrahierte Keyword-Listen und Intent-Erkennung.

Zentralisiert alle Keyword-basierten Intent-Erkennungen für den Orchestrator.
Keine harten Strings mehr im Orchestrator - nur noch saubere Service-Calls.
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger("janus_backend")


# ═══════════════════════════════════════════════════════════════════════════════
# SHOPPING INTENT KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════════

SHOPPING_INTENT_KEYWORDS: List[str] = [
    'preis', 'kostet', 'kosten', 'teuer', 'günstig', 'günstiger', 'billig',
    'kaufen', 'kaufe', 'kauf', 'bestellen', 'bestelle', 'shoppen', 'shopping',
    'angebot', 'angebote', 'deal', 'deals', 'schnäppchen', 'rabatt', 'reduziert',
    'geschenk', 'geschenke', 'schenken', 'schenke', 'modell', 'modelle',
    'variante', 'varianten', 'version', 'spezifikation', 'spezifikationen',
    'vergleich', 'vergleichen', 'empfehlung', 'empfehlungen', 'welches', 'welcher',
    'soll ich', 'welches soll', 'rat', 'beratung', 'beraten'
]

SHOPPING_CONTEXT_MARKERS: List[str] = [
    '€', 'euro', 'eur', '$', 'usd', '£', 'gbp', 'amazon', 'ebay', 'otto',
    'zalando', 'idealo', 'geizhals', 'billiger.de', 'apple', 'samsung', 'sony',
    'nintendo', 'microsoft', 'dell', 'hp', 'lenovo', 'iphone', 'ipad', 'macbook',
    'galaxy', 'playstation', 'xbox', 'switch', 'airpods', 'headset', 'kopfhörer',
    'laptop', 'notebook', 'tablet', 'smartphone', 'uhr', 'watch', 'fernseher',
    'tv', 'monitor', 'kamera', 'konsol', 'was kostet', 'wie viel', 'wie teuer',
    'gibt es günstiger', 'wo gibt es', 'wo finde ich', 'wer bietet', 'wer hat',
    'wer verkauft'
]


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
    # Globale Ausschlusskriterien - diese Keywords blockieren ALLE Intents
    # Analyse/Zusammenfassung - darf keine kreativen Workflows auslösen
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
    # Debugging/Testing - darf keine Produktions-Workflows auslösen
    "debug",
    "debugging",
    "test",
    "testen",
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

HELP_CAPABILITY_OVERVIEW_PATTERNS: Tuple[re.Pattern, ...] = (
    re.compile(r'was\s+kannst\s+du', re.IGNORECASE),
    re.compile(r'was\s+kann\s+janus', re.IGNORECASE),
    re.compile(r'deine?\s+fähigkeiten', re.IGNORECASE),
    re.compile(r'deine?\s+features', re.IGNORECASE),
    re.compile(r'was\s+kann\s+das\s+system', re.IGNORECASE),
    re.compile(r'show\s+capabilities', re.IGNORECASE),
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
    re.compile(r'welches?\s+modell', re.IGNORECASE),
    re.compile(r'welcher?\s+ki', re.IGNORECASE),
    re.compile(r'wer\s+bist\s+du\s+gerade', re.IGNORECASE),
    re.compile(r'mit\s+wem\s+schreibe\s+ich', re.IGNORECASE),
    re.compile(r'mit\s+welchem\s+modell', re.IGNORECASE),
    re.compile(r'was\s+bist\s+du\s+für\s+ein', re.IGNORECASE),
    re.compile(r'welcher?\s+provider', re.IGNORECASE),
    re.compile(r'welche?\s+stärke', re.IGNORECASE),
    re.compile(r'deine?\s+stärke', re.IGNORECASE),
    re.compile(r'\bmodell\b', re.IGNORECASE),
    re.compile(r'\bgerade\b', re.IGNORECASE),
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


class IntentEngine:
    """Central intent detection for the chat orchestrator (keyword lists and light NLP).

    The orchestrator calls these helpers instead of embedding raw strings or regex.
    Use the module singleton :data:`intent_engine` for the shared instance.
    """

    def __init__(self) -> None:
        """Wire keyword lists and compiled patterns used by detection methods."""
        self.shopping_keywords = SHOPPING_INTENT_KEYWORDS
        self.shopping_context_markers = SHOPPING_CONTEXT_MARKERS
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
    
    # ─────────────────────────────────────────────────────────────────────────
    # Global Veto System
    # ─────────────────────────────────────────────────────────────────────────

    def apply_global_veto(self, user_text: str, intent_name: str = "unknown") -> tuple[bool, str]:
        """
        Apply global veto system to check for negative keywords that should block all intents.

        This is a strict veto system - if ANY negative keyword is present, the intent is vetoed
        regardless of positive keywords. This prevents false-positives across all workflows.

        Args:
            user_text: The user's prompt text
            intent_name: Name of the intent being checked (for logging)

        Returns:
            Tuple of (vetoed: bool, reason: str)
            - vetoed: True if veto should be applied (negative keyword found)
            - reason: String explaining why veto was applied
        """
        if not user_text:
            return False, ""

        text_lower = user_text.lower()

        # Check for global negative keywords
        for kw in self.general_negative_keywords:
            if kw in text_lower:
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
        """Return True if the user text looks like shopping/price research (keywords + price context).
        
        Veto: If calendar keywords are present (termin, uhr, dauer, morgen, montag, etc.),
        this cannot be an exclusive shopping intent unless it's primarily about prices ("was kostet").
        """
        if not user_text:
            return False
        text_lower = user_text.lower()
        has_shopping_kw = any(kw in text_lower for kw in self.shopping_keywords)
        has_context_marker = any(marker in text_lower for marker in self.shopping_context_markers)
        
        # Calendar intent veto - if calendar keywords are present, block shopping intent
        # unless it's primarily about price queries
        calendar_keywords = ['termin', 'uhr', 'dauer', 'morgen', 'montag', 'dienstag', 'mittwoch', 
                           'donnerstag', 'freitag', 'samstag', 'sonntag', 'woche', 'tag', 
                           'eintragen', 'trage ein', 'planen', 'termin', 'meeting']
        has_calendar_kw = any(kw in text_lower for kw in calendar_keywords)
        
        # Price-focused queries override the calendar veto
        price_focused = any(kw in text_lower for kw in ['was kostet', 'wie viel', 'wie teuer', 'preis'])
        
        if has_calendar_kw and not price_focused:
            logger.debug("[SHOPPING-VETO] Calendar keywords detected, blocking shopping intent")
            return False
        
        return has_shopping_kw and has_context_marker
    
    # ─────────────────────────────────────────────────────────────────────────
    # Calendar Intent
    # ─────────────────────────────────────────────────────────────────────────
    
    def detect_calendar_intent(self, user_text: str) -> bool:
        """Return True if the user text looks like a calendar/appointment request."""
        if not user_text:
            return False
        text_lower = user_text.lower()
        calendar_keywords = [
            'termin', 'uhr', 'dauer', 'morgen', 'montag', 'dienstag', 'mittwoch',
            'donnerstag', 'freitag', 'samstag', 'sonntag', 'woche', 'tag',
            'eintragen', 'trage ein', 'planen', 'meeting', 'termin', 'kalender',
            'termin erstellen', 'termin anlegen', 'termin hinzufügen'
        ]
        return any(kw in text_lower for kw in calendar_keywords)
    
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

    def detect_capability_overview(self, user_text: str) -> bool:
        """Return True for capability overview queries ("Was kannst du?", "Features")."""
        if not user_text:
            return False
        return any(pattern.search(user_text) for pattern in HELP_CAPABILITY_OVERVIEW_PATTERNS)

    def detect_how_to(self, user_text: str) -> bool:
        """Return True for how-to instructions requests ("Wie kann ich...", "Anleitung für")."""
        if not user_text:
            return False
        return any(pattern.search(user_text) for pattern in HELP_HOW_TO_PATTERNS)

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

    # ─────────────────────────────────────────────────────────────────────────
    # Combined Detection
    # ─────────────────────────────────────────────────────────────────────────
    
    def detect_all_intents(self, user_text: str) -> IntentDetectionResult:
        """Run the full intent battery once and return a structured :class:`IntentDetectionResult`."""
        text_clean = user_text.strip().lower() if user_text else ""

        return IntentDetectionResult(
            is_shopping_intent=self.detect_shopping_intent(user_text),
            is_local_business_intent=self.detect_local_business_intent(user_text),
            is_personal_recall=self.detect_personal_recall(user_text),
            is_image_intent=self.detect_image_intent(user_text),
            is_multitask_image_pdf=self.detect_multitask_image_pdf(user_text),
            has_tool_trigger=self.has_ollama_tool_trigger(user_text),
            is_ollama_vague_smalltalk=self.is_ollama_vague_smalltalk(user_text),
            is_fact_telling=self.is_fact_telling_pattern(user_text),
            is_self_referential=self.is_self_referential_query(user_text),
            is_policy_consent=self.is_policy_consent_choice(text_clean),
            is_one_time_policy=self.is_one_time_policy_choice(text_clean),
            is_complex_document_request=self.detect_complex_document_request(user_text),
            is_simple_document_check=self.is_simple_document_check(user_text),
            is_video_intent=self.detect_video_intent(user_text),
            is_video_list_intent=self.detect_video_list_intent(user_text),
            is_video_understanding_intent=self.detect_video_understanding_intent(user_text),
            # Help System Intents (FEAT-HELP-001)
            is_capability_overview=self.detect_capability_overview(user_text),
            is_how_to=self.detect_how_to(user_text),
            is_navigation_query=self.detect_navigation(user_text),
            # Model Introspection (FEAT-HELP-002)
            is_model_query=self.detect_model_introspektion(user_text)
        )


# Singleton-Instanz für globalen Zugriff
intent_engine = IntentEngine()
