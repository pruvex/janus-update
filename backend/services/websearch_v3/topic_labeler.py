from __future__ import annotations

from .models import SupportedFact, VerifiedSource


TOPIC_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Recht & Regulierung",
        (
            "klage",
            "gericht",
            "rechtsstreit",
            "regulierung",
            "kartell",
            "behorde",
            "behörde",
            "gesetz",
            "copyright",
            "datenschutz",
        ),
    ),
    (
        "Finanzen & Markt",
        (
            "aktie",
            "boerse",
            "börse",
            "quartalszahlen",
            "umsatz",
            "gewinn",
            "prognose",
            "boersengang",
            "börsengang",
            "bewertung",
            "investment",
        ),
    ),
    (
        "Sicherheit & Forschung",
        (
            "sicherheit",
            "safety",
            "security",
            "forschung",
            "research",
            "studie",
            "risiko",
            "alignment",
            "frontier",
        ),
    ),
    (
        "Partnerschaft & Kunden",
        (
            "partnerschaft",
            "kooperation",
            "zusammenarbeit",
            "allianz",
            "joint",
            "oem",
        ),
    ),
    (
        "Produkt & Technik",
        (
            "modell",
            "model",
            "gpt",
            "copilot",
            "cloud",
            "ki",
            "ai",
            "app",
            "api",
            "plattform",
            "chip",
            "software",
            "update",
            "release",
        ),
    ),
)


FINANCE_MARKERS = (
    "aktie",
    "dax",
    "boerse",
    "börse",
    "quartalszahlen",
    "umsatz",
    "gewinn",
    "boersengang",
    "börsengang",
    "bewertung",
    "investment",
)

LEGAL_MARKERS = (
    "klage",
    "gericht",
    "rechtsstreit",
    "regulierung",
    "kartell",
    "behorde",
    "behörde",
    "gesetz",
    "copyright",
    "datenschutz",
)

PARTNERSHIP_MARKERS = (
    "partnerschaft",
    "kooperation",
    "zusammenarbeit",
    "allianz",
    "joint",
    "oem",
)

PRODUCT_MARKERS = (
    "modell",
    "model",
    "gpt",
    "copilot",
    "cloud",
    "ki",
    "ai",
    "app",
    "api",
    "plattform",
    "chip",
    "software",
    "update",
    "release",
)

PUBLIC_SECTOR_MARKERS = (
    "digitalminister",
    "minister",
    "landesportal",
    "mittelstand",
    "münchen",
    "munich",
    "staat",
    "regierung",
)

FILM_HOST_MARKERS = (
    "filmstarts.de",
    "kino.de",
    "kino-zeit.de",
    "moviejones.de",
    "filmportal.de",
    "kinocheck.de",
    "de.ign.com",
)

FILM_MARKERS = (
    "kino",
    "kinostart",
    "filmstart",
    "film",
    "trailer",
    "streaming",
    "produktion",
)

GAMING_HOST_MARKERS = (
    "gamestar.de",
    "gamepro.de",
    "pcgames.de",
    "gameswirtschaft.de",
    "ntower.de",
    "de.ign.com",
    "eurogamer.de",
    "heldenderfreizeit.com",
)

GAMING_MARKERS = (
    "gaming",
    "game",
    "games",
    "spiel",
    "spiele",
    "playstation",
    "xbox",
    "nintendo",
    "switch",
    "steam",
    "gta",
)


def label_source_topic(source: VerifiedSource) -> str:
    title = str(source.title or "").casefold()
    snippet = str(source.snippet or "").casefold()
    label = str(source.source_label or "").casefold()
    url = str(source.canonical_url or source.url or "").casefold()
    haystack = f"{title} {snippet}".casefold()
    source_hint = f"{label} {url}"
    is_film_source = any(marker in source_hint for marker in FILM_HOST_MARKERS)
    is_gaming_source = any(marker in source_hint for marker in GAMING_HOST_MARKERS)
    has_film_marker = any(marker in haystack for marker in FILM_MARKERS)
    has_gaming_marker = any(marker in haystack for marker in GAMING_MARKERS)
    if is_film_source or (has_film_marker and not has_gaming_marker):
        if "trailer" in haystack:
            return "Trailer & Filmnews"
        if any(
            marker in haystack
            for marker in ("kinostart", "filmstart", "release-termin", "release termin", "startet", "mai 2026", "juni 2026")
        ):
            return "Kinostarts"
        return "Film & Kino"
    if is_gaming_source or has_gaming_marker:
        if any(marker in haystack for marker in ("release", "erscheint", "launch", "termin")):
            return "Spiele-Releases"
        if any(marker in haystack for marker in ("playstation", "xbox", "nintendo", "switch", "steam")):
            return "Plattformen"
        return "Gaming"
    if any(marker in title for marker in FINANCE_MARKERS):
        return "Finanzen & Markt"
    if any(marker in title for marker in LEGAL_MARKERS):
        return "Recht & Regulierung"
    if any(marker in title for marker in PUBLIC_SECTOR_MARKERS):
        return "Politik & Standort"
    if any(marker in title for marker in PARTNERSHIP_MARKERS):
        return "Partnerschaft & Kunden"
    if any(marker in title for marker in PRODUCT_MARKERS):
        return "Produkt & Technik"
    for label, markers in TOPIC_RULES:
        marker_hits = sum(1 for marker in markers if marker in haystack)
        if label == "Finanzen & Markt" and marker_hits < 2:
            continue
        if marker_hits:
            return label
    return "Aktuelles"


def with_topic_label(fact: SupportedFact) -> SupportedFact:
    return SupportedFact(
        title=fact.title,
        summary=fact.summary,
        source=fact.source,
        topic_label=label_source_topic(fact.source),
    )
