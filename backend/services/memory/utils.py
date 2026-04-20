"""Utility functions for memory services - pure logic without Janus service dependencies."""

# ═══════════════════════════════════════════════════════════════════════════
# META-NOISE FILTER — Verhindert Extraktion von Meta-Instruktionen als Fakten
# ═══════════════════════════════════════════════════════════════════════════

NOISE_KEYWORDS = [
    "regel", "anweisung", "vorgabe", "notiere", "merke dir wie",
    "beschreiben sollst", "wie du", "wie man", "wie ich", "wie wir",
    "richtlinie", "instruktion", "vorschrift", "protokoll",
    "bedingung", "anforderung", "spezifikation", "kriterium"
]


def _is_meta_noise(text: str) -> bool:
    """Prüft ob Text Meta-Instruktionen enthält (z.B. 'Merke dir die Regeln für X').
    
    Args:
        text: Der zu prüfende Text.
        
    Returns:
        True wenn der Text Meta-Instruktionen enthält, sonst False.
    """
    text_lower = str(text or "").lower()
    return any(keyword in text_lower for keyword in NOISE_KEYWORDS)
