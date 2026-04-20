"""
Deterministischer Post-Processor für Memory Metadaten.
Wendet Regeln an, um priority, ttl, tags, memory_type zu setzen.

Memory System V2.1.0 - Diamond Standard
"""

import logging
import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Callable, Dict, List, Optional

from backend.services.memory_observability import memory_metrics

logger = logging.getLogger("janus_backend")


# ═══════════════════════════════════════════════════════════════════════════
# PRONOUN-BLEED GUARD (V2.1.0 Diamond) — Deterministischer Regex-Filter
# Entfernt deutsche Pronomen/Filler am Anfang von object_value.
# Lebt hier im Enricher, damit ALLE Einstiegspunkte (Extractor, memory_write
# Tool, Legacy-Pfade) den Sanitizer durchlaufen.
# ═══════════════════════════════════════════════════════════════════════════
_PRONOUN_BLEED_RE = re.compile(
    r'^(?:'
    # Pronomen + Verben
    r'ich\s+|bin\s+|nenn(?:e?)\s+|mich\s+|mein(?:e?|em?|er?|es?)?\s+|'
    r'er\s+ist\s+|sie\s+ist\s+|du\s+bist\s+|wir\s+sind\s+|heisse\s+|heiße\s+|'
    # Filler-Wörter die am Anfang von object_value nichts verloren haben
    r'übrigens\s+|tatsächlich\s+|wirklich\s+|eigentlich\s+|'
    r'halt\s+|also\s+|ja\s+|eben\s+|einfach\s+|quasi\s+'
    r')+',
    re.IGNORECASE,
)


def sanitize_object_value(value: str) -> str:
    """
    Entfernt Pronomen-Bleed am Anfang eines object_value.
    'ich maximilian' → 'maximilian'
    'bin software-entwickler' → 'software-entwickler'
    'mein bruder' → 'bruder'
    """
    if not value:
        return value
    cleaned = _PRONOUN_BLEED_RE.sub('', value).strip()
    if not cleaned:
        return value
    return cleaned


# ═══════════════════════════════════════════════════════════════════════════
# REGEL-DEFINITIONEN (Diese Regeln sind das Herzstück des Systems)
# ═══════════════════════════════════════════════════════════════════════════

PriorityRule = Callable[[Dict[str, Any]], bool]


@dataclass
class PriorityRuleEntry:
    condition: PriorityRule
    priority: float
    description: str


# Höchste Priorität zuerst (erste Match gewinnt)
PRIORITY_RULES: List[PriorityRuleEntry] = [
    # CORE_IDENTITY: Physische Identitätsmerkmale (Name, Aussehen)
    PriorityRuleEntry(
        lambda f: f.get("category") == "Physis" and
                  f.get("predicate") in ["name_is", "heisst", "heißt", "ist"],
        0.95,
        "Core Identity: Name oder fundamentale Identität"
    ),
    # CORE_PHYSICAL: Physische Merkmale (Haare, Augen, Teint)
    PriorityRuleEntry(
        lambda f: f.get("category") == "Physis" and
                  f.get("predicate") in ["hat_frisur", "hat_augenfarbe", "hat_teint", "hat"],
        0.90,
        "Core Physical: Wiedererkennbare physische Merkmale"
    ),
    # CORE_RELATIONSHIP: Nahe Bezugspersonen
    PriorityRuleEntry(
        lambda f: f.get("category") == "Beziehungen" and
                  f.get("predicate") in ["name_is", "heisst", "ist", "hat_beziehung"],
        0.85,
        "Core Relationship: Nahestehende Personen"
    ),
    # PET_IDENTITY: Haustier-Identität (für viele User sehr wichtig)
    PriorityRuleEntry(
        lambda f: f.get("category") == "Haustier-Details" and
                  f.get("predicate") in ["name_is", "heisst", "ist"],
        0.88,
        "Pet Identity: Haustier-Namen und Rassen"
    ),
    # STYLE_IDENTITY: Wiederkehrende Style-Elemente
    PriorityRuleEntry(
        lambda f: f.get("category") == "Stil" and
                  "traegt" in f.get("predicate", ""),
        0.75,
        "Style Identity: Accessoires/Schmuck (wiedererkennbar)"
    ),
    # BUG-MEM-022: HEALTH_FACTS auf 0.95 erhöht (GLOBAL-UNLOCK TRIGGER!)
    # Allergien, Erkrankungen dürfen NIEMALS verdrängt werden
    # WICHTIG: 0.95 = GLOBAL-UNLOCK Threshold (>=0.8) für Health-Safety
    PriorityRuleEntry(
        lambda f: f.get("category") == "Gesundheit",
        0.95,
        "Health: Medizinische Informationen (Sicherheits-kritisch, GLOBAL-UNLOCK)"
    ),
    # TEMPORAL: Termine und Zeitpunkte
    PriorityRuleEntry(
        lambda f: f.get("category") == "Termine",
        0.60,
        "Temporal: Termine mit Ablaufdatum"
    ),
    # NEGATIVE PREFERENCES: Explizite Abneigungen (hasst, mag nicht) — UX-kritisch
    PriorityRuleEntry(
        lambda f: f.get("category") == "Vorlieben" and any(
            kw in (f.get("object_value", "") + " " + f.get("predicate", "") + " " + f.get("fact", "")).lower()
            for kw in ("hasst", "hass", "mag_nicht", "mag nicht", "verabscheut",
                       "nicht leiden", "nicht ausstehen", "ekelt", "abneigung",
                       "trinkt_kein", "trinkt kein", "isst_kein", "isst kein")
        ),
        0.70,
        "Negative Preferences: Abneigungen (UX-kritisch, darf nie verschwiegen werden)"
    ),
    # PREFERENCES: Vorlieben (positive)
    PriorityRuleEntry(
        lambda f: f.get("category") == "Vorlieben",
        0.55,
        "Preferences: Mag/Mag nicht (Standard)"
    ),
    # DEFAULT
    PriorityRuleEntry(
        lambda f: True,
        0.50,
        "Default: Standard-Priorität"
    ),
]


# TTL-Regeln (in Sekunden)
TTL_RULES = {
    "Termine": int(timedelta(days=30).total_seconds()),
    "Allgemein": None,  # Permanent
    "Physis": None,     # Permanent
    "Beziehungen": None,
    "Stil": None,
    "Haustier-Details": None,
    "Gesundheit": None,
    "Beruf": None,
    "Vorlieben": int(timedelta(days=365).total_seconds()),  # 1 Jahr
}


# Tag-Mappings
TAG_RULES = {
    "Physis": ["appearance", "identity"],
    "Stil": ["fashion", "identity"],
    "Haustier-Details": ["pet", "identity"],
    "Beziehungen": ["contact", "social"],
    "Termine": ["calendar", "temporal"],
    "Gesundheit": ["health", "medical"],
    "Beruf": ["career", "professional"],
    "Vorlieben": ["preference", "personal"],
    "Allgemein": ["general"],
}


# Priority Caps pro Quelle (GUARD)
PRIORITY_CAPS: Dict[str, float] = {
    "system": 1.0,              # Internes System (unbeschränkt)
    "system.legacy_migration": 0.95,
    "system.extractor": 0.95,
    "system.memory_write": 0.95,
    "system.memory_update": 0.95,
    "skill.save_core_memory": 0.90,
    "skill.save_fact": 0.85,
    "skill.external": 0.70,     # Generisches externes Skill-Cap
    "skill.websearch": 0.60,    # Websuche-Ergebnisse: weniger wichtig
    "user.explicit": 0.95,      # User sagt "Das ist wichtig"
    "user.implicit": 0.75,      # User erwähnt nebenbei
}


# ═══════════════════════════════════════════════════════════════════════════
# HAUPT-FUNKTIONEN
# ═══════════════════════════════════════════════════════════════════════════

def calculate_priority(fact: Dict[str, Any]) -> float:
    """
    Berechnet Priority basierend auf Regeln.
    Erste passende Regel gewinnt.
    """
    for rule in PRIORITY_RULES:
        if rule.condition(fact):
            logger.debug(f"Priority Rule matched: {rule.description} -> {rule.priority}")
            return rule.priority
    return 0.50  # Fallback (sollte nie erreicht werden wegen Default-Rule)


def calculate_ttl(category: str) -> Optional[float]:
    """TTL in Sekunden oder None für permanent."""
    return TTL_RULES.get(category)


def calculate_tags(fact: Dict[str, Any]) -> List[str]:
    """Tags aus Kategorie + dynamischen Regeln."""
    category = fact.get("category", "Allgemein")
    tags = list(TAG_RULES.get(category, ["general"]))

    # Dynamische Tag-Erweiterung
    if fact.get("source_type") == "vision":
        tags.append("visual")

    if fact.get("predicate", "").startswith("traegt"):
        tags.append("wearing")

    if "name" in fact.get("predicate", ""):
        tags.append("naming")

    # Deduplizieren
    return list(set(tags))


def determine_memory_type(priority: float, ttl: Optional[float]) -> str:
    """
    Bestimmt memory_type aus Priority und TTL.
    """
    if priority >= 0.85:
        return "CORE"
    elif ttl is not None:
        return "TEMPORAL"
    else:
        return "GENERAL"


def apply_priority_guard(raw_priority: float, source_skill: str) -> float:
    """
    Hard-Cap auf Priority basierend auf Quelle.
    Loggt Warnung wenn Clamping stattfand.
    """
    cap = PRIORITY_CAPS.get(source_skill, 0.60)  # Default 0.6 für unbekannte Quellen
    clamped = min(raw_priority, cap)

    if clamped < raw_priority:
        logger.warning(
            f"[PRIORITY GUARD] {source_skill} requested {raw_priority}, "
            f"clamped to {clamped} (cap: {cap})"
        )

    return clamped


def enrich_fact(
    fact: Dict[str, Any],
    source_skill: str = "system.extractor",
    user_requested: bool = False
) -> Dict[str, Any]:
    """
    Haupt-Funktion: Reichert einen rohen Fakt mit Metadaten an.

    Args:
        fact: Roher Fakt von LLM (mit fact, category, canonical_key, etc.)
        source_skill: ID des Skills, der den Fakt erzeugt hat
        user_requested: True wenn User explizit "Merke dir das" gesagt hat

    Returns:
        Angereicherter Fakt mit priority, ttl, tags, memory_type
    """
    # 0. PRONOUN-BLEED GUARD: Sanitize object_value vor allem anderen
    raw_obj = fact.get("object_value", "")
    if raw_obj:
        cleaned_obj = sanitize_object_value(raw_obj)
        if cleaned_obj != raw_obj:
            logger.info(
                "[ENRICHER PRONOUN-BLEED] object_value sanitized: %r → %r",
                raw_obj, cleaned_obj,
            )
            fact["object_value"] = cleaned_obj

    # 0b. FOOD/DRINK CATEGORY GUARD: Essen/Trinken-Fakten MÜSSEN "Vorlieben" sein
    _food_drink_keywords = (
        "tee", "kaffee", "bier", "wein", "wasser", "saft", "cola", "limo",
        "getränk", "trinkt", "trinken", "essen", "pizza", "pasta", "schokolade",
        "kuchen", "fleisch", "vegan", "vegetarisch", "alkohol", "milch",
        "smoothie", "cocktail", "whisky", "rum", "wodka",
    )
    _combined_text = " ".join([
        fact.get("object_value", ""),
        fact.get("predicate", ""),
        fact.get("fact", ""),
    ]).lower()
    current_cat = fact.get("category", "")
    if current_cat not in ("Vorlieben", "Gesundheit") and any(
        kw in _combined_text for kw in _food_drink_keywords
    ):
        logger.info(
            "[ENRICHER FOOD-GUARD] Category %r → 'Vorlieben' (food/drink keyword in: %s)",
            current_cat, _combined_text[:80],
        )
        fact["category"] = "Vorlieben"

    # 1. Priority berechnen
    calculated_priority = calculate_priority(fact)

    # 2. User-Override (wenn User explizit sagt es ist wichtig)
    if user_requested:
        calculated_priority = max(calculated_priority, 0.90)
        source_skill = "user.explicit"

    # 3. Priority Guard anwenden
    final_priority = apply_priority_guard(calculated_priority, source_skill)

    # 4. TTL berechnen
    category = fact.get("category", "Allgemein")
    ttl_seconds = calculate_ttl(category)

    # Override: Core Memories haben kein TTL
    if final_priority >= 0.85:
        ttl_seconds = None

    # 5. Tags berechnen
    tags = calculate_tags(fact)

    # 6. Memory Type bestimmen
    memory_type = determine_memory_type(final_priority, ttl_seconds)

    # 7. An Fakt anhängen
    fact["priority"] = final_priority
    fact["ttl"] = ttl_seconds
    fact["tags"] = tags
    fact["memory_type"] = memory_type
    fact["source_skill"] = source_skill
    fact["user_editable"] = True  # Default, kann später geändert werden

    logger.info(
        "[ENRICHER] priority=%.2f, memory_type=%s, tags=%s, source=%s",
        final_priority, memory_type, tags, source_skill
    )
    memory_metrics.increment("writes_enriched")

    return fact
