from __future__ import annotations

import re
from datetime import date


NEWS_MARKERS = (
    "was gibt es neues",
    "aktuelle nachrichten",
    "aktuelle meldung",
    "news",
    "nachrichten",
    "neuigkeiten",
    "aktuell",
    "neues",
    "latest",
    "kino",
    "kinostarts",
    "filmstarts",
    "film-news",
    "film news",
    "movie",
    "movies",
    "release dates",
    "gaming",
    "games",
    "earnings",
    "results",
    "quarter",
    "quartal",
    "quartalszahlen",
    "geschaeftsjahr",
    "geschäftsjahr",
)


def is_simple_news_query(query: str) -> bool:
    lowered = str(query or "").casefold()
    return any(marker in lowered for marker in NEWS_MARKERS)


def extract_subject(query: str) -> str:
    value = re.sub(r"\s+", " ", str(query or "")).strip(" ?!.")
    patterns = (
        r"^was gibt es neues zu\s+(.+)$",
        r"^was gibt es neues von\s+(.+)$",
        r"^was gibt es neues vom\s+(.+)$",
        r"^was gibt es neues im\s+(.+)$",
        r"^was gibt es neues in\s+(.+)$",
        r"^aktuelle nachrichten zu\s+(.+)$",
        r"^aktuelle meldungen zu\s+(.+)$",
        r"^news zu\s+(.+)$",
        r"^neuigkeiten zu\s+(.+)$",
    )
    lowered = value.casefold()
    for pattern in patterns:
        match = re.match(pattern, lowered, flags=re.IGNORECASE)
        if match:
            raw = value[match.start(1):match.end(1)]
            return raw.strip(" ?!.")
    return value


def query_domain(query: str) -> str:
    lowered = str(query or "").casefold()
    if any(marker in lowered for marker in ("kino", "kinostart", "filmstart", "film-news", "film news", "movie", "movies")):
        return "film"
    if any(marker in lowered for marker in ("gaming", "games", "spiele", "spiel")):
        return "gaming"
    return "generic"


def is_broad_briefing_query(query: str) -> bool:
    lowered = str(query or "").casefold()
    return query_domain(query) in {"film", "gaming"} and any(
        marker in lowered
        for marker in (
            "was gibt es neues",
            "aktuelle nachrichten",
            "neues",
            "news",
            "neuigkeiten",
            "latest",
        )
    )


def build_briefing_search_queries(query: str) -> tuple[str, ...]:
    domain = query_domain(query)
    year = date.today().year
    if domain == "gaming":
        return (
            f"{year} aktuelle Gaming News Deutschland GameStar GamePro GTA 6 PlayStation Xbox Nintendo",
            f"{year} aktuelle Spiele Releases Deutschland PC Konsole PC Games ntower",
            f"{year} aktuelle Games Branche Deutschland KI Steam Nintendo PlayStation Xbox GamesWirtschaft heise",
            f"{year} neue Spiele Trailer Release News Deutschland konkrete Titel GamePro GameStar PCGames",
        )
    if domain == "film":
        return (
            f"{year} Kino News Deutschland Filmtrailer konkrete Filme Moviejones KinoCheck Filmstarts Nachrichten",
            f"{year} neue Filmankuendigungen Kinofilm Deutschland konkrete Filmtitel IGN Filmstarts KinoCheck",
            f"{year} Kinostarts Deutschland Highlights Mai Juni konkrete Filme Kino News Detailartikel",
            f"{year} neue Film News Trailer Deutschland konkrete Titel Filmstarts KinoCheck Kino-Zeit",
        )
    if domain == "film":
        return (
            f"{year} neue Kinofilme Kinostarts Deutschland konkrete Filmtitel Filmstarts Kino-Zeit",
            f"{year} neue Filmtrailer Filmnews Deutschland konkrete Trailer Moviejones KinoCheck",
            f"{year} neue Filmankündigungen Kino Deutschland konkrete Filme IGN Deutschland Moviejones",
        )
    return (build_single_news_search_query(query),)


def build_company_search_queries(query: str) -> tuple[str, ...]:
    subject = extract_subject(query)
    year = date.today().year
    subject_lower = subject.casefold()
    queries = [
        f"{subject} {year} aktuelle Nachrichten deutsch Detailartikel Fachmedium",
        f"{subject} {year} offizielle Newsroom Pressemitteilung deutsch Detailseite",
        f"{subject} {year} Produkt KI Partnerschaft Sicherheit Deutschland Artikel",
    ]
    if "nvidia" in subject_lower:
        queries = [
            f"Nvidia {year} aktuelle Nachrichten deutsch Fachartikel KI Chips Blackwell",
            f"Nvidia {year} offizielle Newsroom financial results AI data center",
            f"Nvidia {year} Deutschland KI Fabrik Telekom Fachartikel",
        ]
    elif "openai" in subject_lower:
        queries = [
            f"OpenAI {year} aktuelle Nachrichten deutsch Detailartikel KI Modell Sora",
            f"OpenAI {year} Deutschland Standort Partnerschaft deutsch Fachartikel",
            f"OpenAI {year} offizielle Newsroom Produkt Modell Sicherheit",
        ]
    elif "microsoft" in subject_lower:
        queries = [
            f"Microsoft {year} aktuelle Nachrichten deutsch Detailartikel KI Copilot",
            f"Microsoft {year} Deutschland Cloud Sicherheit Fachartikel",
            f"Microsoft {year} offizielle Newsroom Pressemitteilung deutsch Detailseite",
        ]
    elif "apple" in subject_lower:
        queries = [
            f"Apple {year} aktuelle Nachrichten deutsch Detailartikel iPhone Mac",
            f"Apple {year} WWDC iOS Hardware deutsch Fachartikel",
            f"Apple {year} offizielle Newsroom Pressemitteilung deutsch Detailseite",
        ]
    return tuple(queries)


def build_single_news_search_query(query: str) -> str:
    subject = extract_subject(query)
    domain = query_domain(query)
    if domain == "film":
        return f"{subject} aktuelle Kinonews Filmnews Deutschland deutsch Detailartikel"
    if domain == "gaming":
        return f"{subject} aktuelle Gaming News Deutschland deutsch Detailartikel"
    return f"{subject} aktuelle Meldung deutsch Artikel Detailseite"
