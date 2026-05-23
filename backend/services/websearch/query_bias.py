from __future__ import annotations

import re
from typing import Any, Optional
from urllib.parse import parse_qs, unquote, urlparse

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
_RANKING_LIST_KEYWORDS = {
    "top",
    "topliste",
    "ranking",
    "rangliste",
    "beste",
    "besten",
    "beruehmteste",
    "berühmteste",
    "bekannteste",
    "beliebteste",
    "beliebtesten",
    "wichtigste",
    "groesste",
    "größte",
    "fuehrende",
    "führende",
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
_GERMAN_SOURCE_SUFFIX = "deutschsprachige Quellen Deutschland site:de"
_GERMAN_QUERY_MARKERS = {
    "wer",
    "was",
    "wie",
    "welche",
    "welcher",
    "welches",
    "wann",
    "warum",
    "wieso",
    "wo",
    "sind",
    "ist",
    "gibt",
    "heute",
    "aktuell",
    "deutsch",
    "deutschland",
}


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
    normalized = normalized.replace("site:de site:deutschsprachige", "site:deutschsprachige")
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


def _germanize_news_query(query: str) -> str:
    germanized = str(query or "").strip()
    if not germanized:
        return germanized
    replacements = (
        (r"\blatest\s+news\b", "aktuelle Nachrichten Neuigkeiten"),
        (r"\bnews\b", "Nachrichten Neuigkeiten"),
        (r"\bupdates\b", "Aktuelles Neuigkeiten"),
        (r"\bannouncements\b", "Ankuendigungen Neuigkeiten"),
    )
    for pattern, replacement in replacements:
        germanized = re.sub(pattern, replacement, germanized, flags=re.IGNORECASE)
    if not re.search(r"\b(nachrichten|neuigkeiten|aktuelles|aktuell|meldungen)\b", germanized, flags=re.IGNORECASE):
        germanized = f"{germanized} aktuelle Nachrichten Neuigkeiten"
    return _normalize_bias_query(germanized)


def _is_game_release_query(lowered_query: str) -> bool:
    return _contains_keyword(lowered_query, _GAME_RELEASE_KEYWORDS) and _contains_keyword(
        lowered_query, _GAME_CONTEXT_KEYWORDS
    )


def _is_ranking_list_query(lowered_query: str) -> bool:
    if re.search(r"\btop\s*\d+\b", lowered_query):
        return True
    return any(re.search(rf"\b{re.escape(keyword)}\b", lowered_query) for keyword in _RANKING_LIST_KEYWORDS)


def _is_likely_german_query(lowered_query: str) -> bool:
    if any(char in lowered_query for char in "äöüß"):
        return True
    return any(re.search(rf"\b{re.escape(marker)}\b", lowered_query) for marker in _GERMAN_QUERY_MARKERS)


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

    if (
        (
            _is_ranking_list_query(lowered)
            or _is_likely_german_query(lowered)
            or _contains_keyword(lowered, _NEWS_KEYWORDS)
        )
        and "deutschsprachige" not in lowered
        and "english sources" not in lowered
        and "englische quellen" not in lowered
    ):
        _append_unique_part(suffix_parts, _GERMAN_SOURCE_SUFFIX)

    return _normalize_bias_query(" ".join(part for part in suffix_parts if part))


def augment_query_with_local_bias(query: str) -> str:
    working_query = str(query or "").strip()
    if _contains_keyword(working_query.lower(), _NEWS_KEYWORDS):
        working_query = _germanize_news_query(working_query)
    suffix = build_query_suffix(query)
    if not suffix:
        return _normalize_bias_query(working_query)
    if suffix in working_query:
        return _normalize_bias_query(working_query)
    return _normalize_bias_query(f"{working_query} {suffix}".strip())


def build_release_hint(query: str) -> Optional[str]:
    lowered = (query or "").lower()
    if _is_game_release_query(lowered):
        return (
            "Bevorzuge offizielle Quellen wie nintendo.de oder etablierte deutsche Spieleseiten "
            "(z.B. spieletipps.de, gameswirtschaft.de), um Release-Daten zu bestätigen."
        )
    return None


def build_german_source_preference_hint() -> str:
    return (
        "QUELLENSPRACHE: Janus laeuft fuer Nutzer in Deutschland. "
        "Bevorzuge deutschsprachige Quellen, deutsche/deutschsprachige Fachmedien und deutschsprachige "
        "Versionen offizieller Seiten. Nutze englische oder internationale Quellen nur, wenn keine "
        "gleichwertige deutschsprachige Quelle verfuegbar ist oder die offizielle Quelle fachlich klar besser ist."
    )


def normalize_source_url(url: str) -> str:
    value = str(url or "").strip()
    if not value:
        return ""
    if value.startswith(("data:", "about:", "javascript:")):
        return ""
    try:
        parsed = urlparse(value)
    except Exception:
        return value
    domain = parsed.netloc.casefold().removeprefix("www.")
    path = parsed.path.casefold()
    if not parsed.scheme.startswith("http"):
        return ""
    if domain == "w3.org" and path.rstrip("/") in {"/2000/svg", "/1999/xhtml"}:
        return ""
    if domain.endswith("w3.org") and path.startswith("/2000/svg"):
        return ""
    if path.endswith((".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico")):
        return ""
    is_google_search_domain = domain in {"google.com", "google.de"} or domain.endswith(".google.com") or domain.endswith(".google.de")
    is_google_search_path = path.startswith(("/search", "/url"))
    if is_google_search_domain and is_google_search_path:
        params = parse_qs(parsed.query)
        for key in ("url", "q", "u"):
            for candidate in params.get(key, []):
                target = unquote(str(candidate or "").strip())
                if target.startswith(("http://", "https://")):
                    target_domain = urlparse(target).netloc.casefold().removeprefix("www.")
                    if not target_domain.endswith(("google.com", "google.de")):
                        return target
        return ""
    return value


def is_likely_weak_source(source: dict[str, Any]) -> bool:
    url = str(source.get("url") or source.get("uri") or source.get("source_url") or "").strip().lower()
    domain = ""
    if url:
        try:
            domain = urlparse(url).netloc.casefold().removeprefix("www.")
        except Exception:
            domain = ""
    weak_domains = (
        "imago-images.de",
        "imago-images.com",
        "gettyimages.",
        "alamy.",
        "shutterstock.",
        "pinterest.",
        "youtube.",
    )
    return any(marker in domain for marker in weak_domains)


def is_likely_german_source(source: dict[str, Any]) -> bool:
    url = normalize_source_url(str(source.get("url") or source.get("uri") or source.get("source_url") or "").strip()).lower()
    title = str(source.get("title") or source.get("name") or "").casefold()
    snippet = str(source.get("snippet") or source.get("text") or "").casefold()
    domain = ""
    if url:
        try:
            domain = urlparse(url).netloc.casefold().removeprefix("www.")
        except Exception:
            domain = ""
    if domain.endswith((".de", ".at", ".ch")) or domain.startswith("de.") or ".de." in domain:
        return True
    combined = f"{title} {snippet}"
    if any(char in combined for char in "äöüß"):
        return True
    german_markers = (
        "deutschland",
        "deutsch",
        "bundesliga",
        "testbericht",
        "kaufberatung",
        "erscheinung",
        "veröffentlicht",
        "erscheint",
        "quelle",
    )
    return any(marker in combined for marker in german_markers)


def prioritize_german_sources(
    sources: list[dict[str, Any]],
    *,
    max_items: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Prefer German-language sources without dropping available fallback links."""
    valid_sources: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for source in sources or []:
        if not isinstance(source, dict):
            continue
        cleaned_url = normalize_source_url(str(source.get("url") or source.get("uri") or source.get("source_url") or ""))
        if not cleaned_url or cleaned_url in seen_urls:
            continue
        seen_urls.add(cleaned_url)
        cleaned_source = dict(source)
        cleaned_source["url"] = cleaned_url
        if "uri" in cleaned_source:
            cleaned_source["uri"] = cleaned_url
        valid_sources.append(cleaned_source)
    if not valid_sources:
        return []
    target_count = max_items or len(valid_sources)
    strong_sources = [source for source in valid_sources if not is_likely_weak_source(source)]
    weak_sources = [source for source in valid_sources if is_likely_weak_source(source)]
    german_sources = [source for source in strong_sources if is_likely_german_source(source)]
    non_german_sources = [source for source in strong_sources if not is_likely_german_source(source)]
    if not german_sources:
        return (strong_sources + weak_sources)[:target_count]

    return (german_sources + non_german_sources + weak_sources)[:target_count]


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
