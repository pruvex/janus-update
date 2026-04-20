from __future__ import annotations

from typing import Optional

_PRICE_KEYWORDS = {
    "preis",
    "preise",
    "cost",
    "kosten",
    "kostet",
    "was kostet",
    "wie teuer",
    "wert",
    "kurs",
    "gebuehr",
    "gebühr",
    "gebuehren",
    "gebühren",
    "quote",
    "tarif",
    "finanz",
    "börse",
    "boerse",
}
_NEWS_KEYWORDS = {
    "news",
    "neuigkeiten",
    "aktuell",
    "breaking",
    "meldung",
    "nachrichten",
    "update",
    "heute",
}
_GAME_RELEASE_KEYWORDS = {
    "release",
    "erscheint",
    "erscheinen",
    "veröffentlicht",
    "veroeffentlicht",
    "launch",
    "kommt raus",
    "erscheinung",
    "termin",
    "termine",
    "januar", "februar", "märz", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "dezember",
}
_GAME_CONTEXT_KEYWORDS = {
    "spiel",
    "spiele",
    "nintendo",
    "switch",
    "konsole",
    "playstation",
    "xbox",
    "pc-game",
    "gaming",
}
_PRICE_RELEASE_BIAS_KEYWORDS = {
    "preis",
    "preise",
    "kosten",
    "cost",
    "costs",
    "kurs",
    "wert",
    "gebühr",
    "gebuehr",
    "tarif",
    "release",
    "erscheint",
    "erscheinung",
    "veröffentlich",
    "veroeffentlich",
}
_LOCATION_TOKENS = {
    "deutschland",
    "österreich",
    "oesterreich",
    "schweiz",
    "usa",
    "vereinigten staaten",
    "frankreich",
    "italien",
    "spanien",
    "uk",
    "britain",
    "china",
    "india",
    "kanada",
    "canada",
    "euro",
    "eur",
    "usd",
    "gbp",
    "¥",
    "€",
    "$",
}

_RELEASE_SITE_SUFFIX = "(site:nintendo.de OR site:spieletipps.de OR site:gameswirtschaft.de OR site:gamepro.de OR site:de.ign.com OR site:eurogamer.de)"
_PRICE_SUFFIX = "Deutschland \"in Euro\" site:de"
_NEWS_SUFFIX = "Deutschland aktuell site:de"


def _contains_keyword(text: str, keywords: set[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _append_unique_part(parts: list[str], candidate: str) -> None:
    value = str(candidate or "").strip()
    if value and value not in parts:
        parts.append(value)


def _normalize_bias_query(query: str) -> str:
    normalized = str(query or "").strip()
    if not normalized:
        return normalized
    normalized = normalized.replace("site:de site:de", "site:de")
    normalized = normalized.replace("Deutschland Deutschland", "Deutschland")
    normalized = normalized.replace("Euro Euro", "Euro")
    normalized = normalized.replace('"in Euro" "in Euro"', '"in Euro"')
    normalized = " ".join(normalized.split())
    return normalized


def _has_currency_bias(lowered_query: str) -> bool:
    return any(token in lowered_query for token in (" in euro", '"in euro"', " euro", " eur", "€", " usd", " dollar"))


def _build_price_suffix(lowered_query: str) -> str:
    parts: list[str] = []
    if "deutschland" not in lowered_query:
        parts.append("Deutschland")
    if not _has_currency_bias(lowered_query):
        parts.append('"in Euro"')
    if "site:de" not in lowered_query:
        parts.append("site:de")
    return " ".join(parts)


def _build_news_suffix(lowered_query: str) -> str:
    parts: list[str] = []
    if "deutschland" not in lowered_query:
        parts.append("Deutschland")
    if "aktuell" not in lowered_query and "heute" not in lowered_query:
        parts.append("aktuell")
    if "site:de" not in lowered_query:
        parts.append("site:de")
    return " ".join(parts)


def _is_game_release_query(lowered_query: str) -> bool:
    return _contains_keyword(lowered_query, _GAME_RELEASE_KEYWORDS) and _contains_keyword(
        lowered_query, _GAME_CONTEXT_KEYWORDS
    )


def build_query_suffix(query: str) -> str:
    lowered = (query or "").lower()
    suffix_parts: list[str] = []

    if _contains_keyword(lowered, _PRICE_KEYWORDS):
        price_suffix = _build_price_suffix(lowered)
        if price_suffix:
            _append_unique_part(suffix_parts, price_suffix)

    if _contains_keyword(lowered, _NEWS_KEYWORDS):
        news_suffix = _build_news_suffix(lowered)
        if news_suffix:
            _append_unique_part(suffix_parts, news_suffix)

    if _is_game_release_query(lowered):
        release_sites = [
            "site:nintendo.de",
            "site:spieletipps.de",
            "site:gameswirtschaft.de",
            "site:gamepro.de",
            "site:de.ign.com",
            "site:eurogamer.de",
        ]
        if not any(site in lowered for site in release_sites):
            _append_unique_part(suffix_parts, _RELEASE_SITE_SUFFIX)

    return _normalize_bias_query(" ".join(part for part in suffix_parts if part))


def augment_query_with_local_bias(query: str) -> str:
    suffix = build_query_suffix(query)
    if not suffix:
        return _normalize_bias_query(query)
    if suffix in query:
        return _normalize_bias_query(query)
    return _normalize_bias_query(f"{query} {suffix}".strip())


def build_release_hint(query: str) -> Optional[str]:
    lowered = (query or "").lower()
    if _is_game_release_query(lowered):
        return (
            "Bevorzuge offizielle Quellen wie nintendo.de oder etablierte deutsche Spieleseiten "
            "(z.B. spieletipps.de, gameswirtschaft.de), um Release-Daten zu bestätigen."
        )
    return None


def enforce_german_market_bias(query: str) -> str:
    lowered = (query or "").lower()
    if not query:
        return query
    if any(token in lowered for token in _LOCATION_TOKENS):
        return query
    if not any(keyword in lowered for keyword in _PRICE_RELEASE_BIAS_KEYWORDS):
        return query
    bias_parts: list[str] = []
    if "deutschland" not in lowered:
        bias_parts.append("Deutschland")
    if not _has_currency_bias(lowered):
        bias_parts.append("Euro")
    if not bias_parts:
        return _normalize_bias_query(query)
    return _normalize_bias_query(f"{query} {' '.join(bias_parts)}".strip())
