from __future__ import annotations

import re
from datetime import date

from .models import PageFetchResult, SearchCandidate, VerifiedSource
from .evidence_policy import evidence_rejection_reason
from .query_planner import extract_subject, is_simple_news_query, query_domain
from .source_classifier import classify_source
from .url_normalizer import host_for_url, is_blocked_url, normalize_url, path_for_url


GENERIC_PATHS = {
    "",
    "/",
    "/news",
    "/blog",
    "/press",
    "/presse",
    "/aktuelles",
    "/nachrichten",
    "/de/news",
    "/de-de/news",
    "/recent-news",
    "/de-de/recent-news",
    "/news/latest",
    "/source/emea/alle-anzeigen",
}

MIN_PAGE_TEXT_LENGTH = 160
GENERIC_LAST_SEGMENTS = {
    "news",
    "blog",
    "press",
    "presse",
    "aktuelles",
    "nachrichten",
    "reports",
    "announcements",
}

GERMAN_SOURCE_HINTS = (
    ".de",
    ".at",
    ".ch",
    "/de/",
    "/de-de/",
    "heise",
    "golem",
    "computerwoche",
    "t3n",
    "tagesschau",
    "spiegel",
    "zeit",
    "winfuture",
    "computerbase",
    "borncity",
    "game.de",
    "gameswirtschaft",
    "gamestar",
    "gamepro",
    "pcgames",
    "ntower",
    "sevengamer",
    "filmstarts",
    "kino-zeit",
    "moviejones",
    "filmportal",
    "deutsche-filmakademie",
    "de.ign.com",
)

LOW_VALUE_HOST_MARKERS = (
    "medium.com",
    "reddit.",
    "youtube.",
    "youtu.be",
    "facebook.",
    "instagram.",
    "pinterest.",
    "36kr.com",
    "dict.leo.org",
    "linguee.de",
    "dict.cc",
    "langenscheidt.com",
    "kleiner-kalender.de",
)

FINANCIAL_NEWS_HOST_MARKERS = (
    "ad-hoc-news.de",
    "aktiencheck.de",
    "finanznachrichten.de",
    "finanzen.net",
    "finanzen.ch",
    "finanztreff.de",
    "marketscreener.com",
    "onvista.de",
    "wallstreet-online.de",
    "boerse.de",
    "boerse-online.de",
    "deraktionaer.de",
    "comdirect.de",
    "fool.com",
    "marketbeat.com",
    "simplywall.st",
    "ig.com",
    "investing.com",
    "phemex.com",
)

FINANCIAL_PATH_MARKERS = (
    "/aktien/",
    "/boerse/",
    "/boersen/",
    "/borsen/",
    "/stock/",
    "/stocks/",
    "/markets/",
    "/market/",
    "/news-views-markets/",
    "/nachrichten-aktien/",
)

TRUSTED_COMPANY_RESULTS_HOST_MARKERS = (
    "nvidia.com",
    "blogs.nvidia.de",
    "microsoft.com",
    "news.microsoft.com",
    "apple.com",
    "openai.com",
    "heise.de",
    "computerbase.de",
    "golem.de",
    "manager-magazin.de",
    "tagesschau.de",
    "spiegel.de",
)

OFFICIAL_SOURCE_MARKERS = {
    "microsoft": ("microsoft.com", "news.microsoft.com"),
    "openai": ("openai.com",),
    "apple": ("apple.com", "developer.apple.com", "newsroom.apple.com"),
    "nvidia": ("nvidia.com", "blogs.nvidia.de"),
}

PAYWALL_MARKERS = (
    "handelsblatt.",
    "faz.net",
    "welt.de",
)

GAMING_SOURCE_HOST_MARKERS = (
    "game.de",
    "gameswirtschaft.de",
    "gamestar.de",
    "gamepro.de",
    "pcgames.de",
    "ntower.de",
    "computerbase.de",
    "heise.de",
    "golem.de",
    "de.ign.com",
    "eurogamer.de",
    "spieletipps.de",
    "news.xbox.com",
)

FILM_SOURCE_HOST_MARKERS = (
    "filmstarts.de",
    "kino.de",
    "kino-zeit.de",
    "moviejones.de",
    "filmportal.de",
    "deutsche-filmakademie.de",
    "kinocheck.de",
    "techrush.de",
)

GERMAN_WORDS = {
    "der",
    "die",
    "das",
    "und",
    "ist",
    "mit",
    "fuer",
    "für",
    "eine",
    "einen",
    "nach",
    "von",
    "zu",
    "auf",
    "sich",
    "wird",
}


def _tokens(text: str) -> list[str]:
    stop_words = {
        "news",
        "aktuell",
        "aktuelle",
        "aktueller",
        "neues",
        "meldung",
        "meldungen",
        "nachrichten",
        "neuigkeiten",
        "deutsch",
        "artikel",
        "detailseite",
    }
    return [
        token
        for token in re.findall(r"[a-z0-9äöüß][a-z0-9äöüß._-]{2,}", str(text or "").casefold())
        if token not in stop_words
    ]


def _host_matches(host: str, marker: str) -> bool:
    value = str(marker or "").casefold().strip(".")
    if not value:
        return False
    return host == value or host.endswith("." + value)


def _looks_german(text: str, hint: str = "") -> bool:
    lowered = f"{hint} {text[:1500]}".casefold()
    if any(marker in lowered for marker in GERMAN_SOURCE_HINTS):
        return True
    hits = sum(1 for word in GERMAN_WORDS if re.search(rf"\b{re.escape(word)}\b", lowered))
    return hits >= 4


def _has_german_source_hint(url: str, host: str, language_hint: str) -> bool:
    haystack = f"{url} {host} {language_hint}".casefold()
    return any(marker in haystack for marker in GERMAN_SOURCE_HINTS)


def _is_german_query(query: str) -> bool:
    lowered = str(query or "").casefold()
    return any(
        marker in lowered
        for marker in (
            "was gibt es neues",
            "aktuelle nachricht",
            "aktuelle meldung",
            "nachrichten",
            "neuigkeiten",
            "deutsch",
        )
    )


def _is_general_company_news_query(query: str) -> bool:
    lowered = str(query or "").casefold()
    if not is_simple_news_query(lowered):
        return False
    finance_markers = (
        "aktie",
        "aktien",
        "kurs",
        "boerse",
        "börse",
        "dividende",
        "analyst",
        "analysten",
        "quartalszahl",
        "quartalszahlen",
        "gewinn",
        "umsatz",
        "chart",
        "trading",
    )
    return not any(marker in lowered for marker in finance_markers)


def _is_financial_news_source(host: str, path: str, title: str, snippet: str) -> bool:
    if any(_host_matches(host, marker) for marker in FINANCIAL_NEWS_HOST_MARKERS):
        return True
    lowered = f"{title} {snippet}".casefold()
    finance_title_markers = (
        " aktie",
        "aktie ",
        "aktienkurs",
        "kursziel",
        "kurs analyse",
        "kurs-analyse",
        "dividende",
        "analyst",
        "analysten",
        "quartalszahlen",
        "rekordquartal",
    )
    if any(marker in lowered for marker in finance_title_markers):
        return True
    if "prognose" in lowered and any(marker in lowered for marker in (" aktie", "aktie ", "kurs", "umsatz", "gewinn")):
        return True
    if any(marker in path for marker in FINANCIAL_PATH_MARKERS):
        company_context = any(marker in lowered for marker in ("aktie", "stock", "dividende", "analyst", "kurs"))
        return company_context
    return False


def _is_company_results_article(title: str, snippet: str) -> bool:
    lowered = f"{title} {snippet}".casefold()
    result_markers = (
        "quartalszahlen",
        "quartal",
        "geschaeftsjahr",
        "geschäftsjahr",
        "ergebnis",
        "ergebnisse",
        "zahlen",
        "rekordumsatz",
        "umsatzwachstum",
        "financial results",
        "earnings",
        "q1",
        "q2",
        "q3",
        "q4",
    )
    business_markers = (
        "umsatz",
        "gewinn",
        "milliarden",
        "rechenzentren",
        "ki",
        "ai",
        "chip",
        "chips",
        "blackwell",
        "rubin",
    )
    return any(marker in lowered for marker in result_markers) and any(marker in lowered for marker in business_markers)


def _is_trusted_company_results_host(host: str) -> bool:
    return any(_host_matches(host, marker) for marker in TRUSTED_COMPANY_RESULTS_HOST_MARKERS)


def _is_official_source(host: str, subject: str) -> bool:
    subject_tokens = _tokens(subject)
    for token in subject_tokens:
        for marker in OFFICIAL_SOURCE_MARKERS.get(token, ()):
            if _host_matches(host, marker):
                return True
    return False


def _is_unofficial_brand_host(host: str, subject: str) -> bool:
    if _is_official_source(host, subject):
        return False
    for token in _tokens(subject):
        if token in OFFICIAL_SOURCE_MARKERS and token in host:
            return True
    return False


def _is_detail_page(url: str) -> bool:
    path = path_for_url(url)
    if path in GENERIC_PATHS:
        return False
    stripped = path.strip("/")
    if not stripped:
        return False
    if stripped in {item.strip("/") for item in GENERIC_PATHS}:
        return False
    segments = [segment for segment in stripped.split("/") if segment]
    if segments and segments[-1] in GENERIC_LAST_SEGMENTS:
        return False
    if len(segments) >= 2:
        return True
    return bool(re.search(r"\d{4}|[-_][a-z0-9]{4,}", stripped))


def _looks_like_generic_news_listing(url: str, title: str) -> bool:
    path = path_for_url(url)
    lowered_title = str(title or "").casefold()
    host = host_for_url(url)
    if _host_matches(host, "imdb.com") and path.startswith("/calendar"):
        return True
    generic_path_prefixes = (
        "/thema/",
        "/themen/",
        "/topic/",
        "/topics/",
        "/lp/",
        "/category/press-releases",
        "/financial-info/financial-reports",
        "/investor/financial",
        "/kino/kinoprogramm",
        "/film/filmstarts.html",
        "/filmstarts/all/",
        "/kinofilme/kinofilme-",
        "/filme/kinofilme-",
        "/filmstarts/aktuell-im-kino",
        "/filme/jahre/",
        "/filme/aktuell/",
        "/filme-imkino/vorpremiere",
        "/filme-imkino/kinos",
        "/filme-vorschau",
        "/filme/filmstarts",
        "/aktuell/festivalberichte",
        "/news/events",
        "/news/cinema/month/",
        "/whats-new",
        "/community/",
        "/forum/",
        "/forums/",
        "/thread/",
    )
    if any(path.startswith(prefix) for prefix in generic_path_prefixes):
        return True
    if "/recent-news" in path:
        return True
    if "alle-anzeigen" in path:
        return True
    if path.startswith("/filmstarts/") and "moviejones" in host:
        return True
    if path.startswith("/filmstarts/") and any(
        _host_matches(host, marker) for marker in ("kinocheck.de", "filmstarts.de")
    ):
        return True
    if "/category/press-releases" in path:
        return True
    if path in {"/news/openai", "/news/microsoft", "/news/apple", "/news/nvidia"}:
        return True
    if "grafikkartentreiber" in path and "treiber" in lowered_title:
        return True
    if "/lp/" in path:
        return True
    if "/region/" in path and any(_host_matches(host, marker) for marker in ("microsoft.com", "news.microsoft.com")):
        return True
    if re.search(r"/news/aktien/[^/]+-news-[a-z]{2}[a-z0-9]+$", path):
        return True
    generic_title_markers = (
        "aktuelle nachrichten zur",
        "aktuelle nachrichten zu",
        "aktuelle news zur",
        "aktuelle news zu",
        "aktuelle nachrichten und hintergründe",
        "news & infos",
        "financial reports",
        "alle kinofilme",
    )
    if any(marker in lowered_title for marker in ("gewinnspiel", "community", "forum", "alle kinofilme", "festivalberichte")):
        return True
    listing_markers = (" aktie", " stock", " share")
    return any(marker in lowered_title for marker in generic_title_markers) and any(
        marker in lowered_title for marker in listing_markers
    )


def _has_domain_source_hint(domain: str, host: str) -> bool:
    if domain == "gaming":
        return any(_host_matches(host, marker) for marker in GAMING_SOURCE_HOST_MARKERS)
    if domain == "film":
        return any(_host_matches(host, marker) for marker in FILM_SOURCE_HOST_MARKERS)
    return True


def _broad_domain_is_primary_topic(domain: str, host: str, path: str, title: str) -> bool:
    if domain not in {"gaming", "film"}:
        return True
    if _has_domain_source_hint(domain, host):
        return True
    haystack = f"{path} {title}".casefold()
    if domain == "gaming":
        markers = (
            "gaming",
            "games",
            "game",
            "spiele",
            "spiel",
            "gta",
            "xbox",
            "playstation",
            "nintendo",
            "switch",
            "steam",
            "pc-spiel",
            "konsole",
            "publisher",
            "studio",
        )
        return any(marker in haystack for marker in markers)
    markers = ("film", "filme", "kino", "kinostart", "trailer", "festival", "streaming", "filmpreis")
    return any(marker in haystack for marker in markers)


def _looks_like_low_signal_page(title: str, text: str) -> bool:
    lowered = f"{title} {text[:1800]}".casefold()
    if "beispielhafter link basierend" in lowered:
        return True
    low_signal_markers = (
        "meistgelesene news",
        "top 100 meistgesuchte",
        "kurse analysen",
        "newsletter abonnieren",
        "no result view all result",
        "alle meldungen",
        "alle nachrichten",
    )
    hits = sum(1 for marker in low_signal_markers if marker in lowered)
    return hits >= 2


def _subject_prominence_score(subject: str, title: str, snippet: str, page: PageFetchResult) -> float:
    tokens = [
        token
        for token in _tokens(subject)
        if token not in {"inc", "corp", "ltd", "ag"} and not re.fullmatch(r"\d{4}", token)
    ]
    if not tokens:
        return 1.0
    title_snippet = f"{title} {snippet}".casefold()
    early_page = str(page.text or "")[:700].casefold()
    score = 0.0
    for token in tokens:
        if token in title_snippet:
            score += 1.0
        elif token in early_page:
            score += 0.35
    return min(1.0, score / max(len(tokens), 1))


def _topic_match_score(query: str, candidate: SearchCandidate, page: PageFetchResult) -> float:
    domain = query_domain(query)
    if domain == "gaming":
        query_tokens = {
            "gaming",
            "games",
            "game",
            "spiel",
            "spiele",
            "computerspiel",
            "playstation",
            "xbox",
            "nintendo",
            "switch",
            "steam",
            "release",
            "releases",
            "branche",
            "studio",
            "studios",
            "publisher",
            "ki",
            "pc",
            "konsole",
            "konsolen",
            "gta",
        }
    elif domain == "film":
        query_tokens = {
            "film",
            "filme",
            "kino",
            "kinostart",
            "kinostarts",
            "trailer",
            "streaming",
            "festival",
            "festivals",
            "produktion",
            "produktionen",
            "box",
            "office",
            "schauspiel",
        }
    else:
        subject = extract_subject(query)
        query_tokens = set(_tokens(subject))
    if not query_tokens:
        query_tokens = set(_tokens(query))
    haystack = f"{candidate.title} {candidate.snippet} {page.title} {page.text[:2500]}".casefold()
    if not query_tokens:
        return 0.0
    matches = sum(1 for token in query_tokens if token in haystack)
    if domain in {"gaming", "film"}:
        return min(1.0, matches / 3.0)
    return matches / max(len(query_tokens), 1)


def _looks_stale_for_broad_briefing(query: str, final_url: str, title: str, snippet: str, page: PageFetchResult) -> bool:
    if query_domain(query) not in {"gaming", "film"}:
        return False
    current_year = date.today().year
    text = f"{final_url} {title} {snippet} {page.published_at or ''}".casefold()
    if str(current_year) in text:
        return False
    stale_years = {str(year) for year in range(current_year - 6, current_year)}
    return any(year in text for year in stale_years)


def _is_streaming_guide_for_cinema_query(query: str, title: str, snippet: str) -> bool:
    query_lower = str(query or "").casefold()
    if query_domain(query) != "film" or not any(marker in query_lower for marker in ("kino", "kinostart")):
        return False
    primary_text = f"{title} {snippet}".casefold()
    streaming_markers = (
        "neu auf netflix",
        "streaming guide",
        "streaming-guide",
        "streamingstarts",
        "streaming-starts",
        "netflix",
        "prime video",
        "disney+",
        "paramount+",
        "sky/wow",
    )
    if not any(marker in primary_text for marker in streaming_markers):
        return False
    cinema_evidence_markers = (
        "kinostart",
        "kinostarts",
        "im kino",
        "kinofilm",
        "filmtrailer",
        "neuer trailer",
        "neue trailer",
        "filmankuendigung",
        "filmankündigung",
    )
    return not any(marker in primary_text for marker in cinema_evidence_markers)


def verify_source(query: str, candidate: SearchCandidate, page: PageFetchResult) -> VerifiedSource:
    final_url = normalize_url(page.final_url or candidate.url)
    reasons: list[str] = []
    classification = classify_source(candidate, page)
    if not final_url:
        reasons.append("missing_url")
    if is_blocked_url(final_url):
        reasons.append("blocked_url")
    if page.status_code != 200:
        reasons.append("not_http_200")
    host = host_for_url(final_url)
    path = path_for_url(final_url)
    subject = extract_subject(query)
    is_general_news = _is_general_company_news_query(query)
    is_official = _is_official_source(host, subject)
    if any(_host_matches(host, marker) for marker in LOW_VALUE_HOST_MARKERS):
        reasons.append("low_value_host")
    if any(_host_matches(host, marker) for marker in PAYWALL_MARKERS):
        reasons.append("paywall_host")
    if page.error:
        reasons.append("fetch_error")
    if page.status_code == 200 and len(str(page.text or "").strip()) < MIN_PAGE_TEXT_LENGTH:
        reasons.append("thin_page")

    is_detail = _is_detail_page(final_url)
    if not is_detail:
        reasons.append("not_detail_page")

    title = page.title or candidate.title or host or "Quelle"
    snippet = candidate.snippet or page.text[:260]
    is_financial_source = _is_financial_news_source(host, path, title, snippet)
    is_results_article = _is_company_results_article(title, snippet)
    if is_general_news and is_financial_source and not is_official and not (
        is_results_article and _is_trusted_company_results_host(host)
    ):
        reasons.append("financial_news_source")
    if _looks_like_generic_news_listing(final_url, title):
        reasons.append("generic_news_listing")
    if _looks_like_low_signal_page(title, page.text):
        reasons.append("low_signal_page")
    evidence_reason = evidence_rejection_reason(query, classification)
    if evidence_reason:
        reasons.append(evidence_reason)
    domain = query_domain(query)
    if not _broad_domain_is_primary_topic(domain, host, path, title):
        reasons.append("domain_not_primary_topic")
    if _looks_stale_for_broad_briefing(query, final_url, title, snippet, page):
        reasons.append("stale_broad_briefing_source")
    if _is_streaming_guide_for_cinema_query(query, title, snippet):
        reasons.append("streaming_guide_for_cinema_query")
    language_hint = f"{page.language_hint} {final_url}"
    is_german = _looks_german(f"{title} {snippet} {page.text}", language_hint)
    language = "de" if is_german else "unknown"
    has_german_source_hint = _has_german_source_hint(final_url, host, page.language_hint)
    if _is_unofficial_brand_host(host, subject):
        reasons.append("unofficial_brand_host")
    if _is_german_query(query) and (not is_german or not has_german_source_hint) and not is_official:
        reasons.append("non_german_non_official_source")
    topic_score = _topic_match_score(query, candidate, page)
    if topic_score < 0.34:
        reasons.append("weak_topic_match")
    subject_prominence = _subject_prominence_score(subject, title, snippet, page)
    if is_general_news and domain == "generic" and not is_official and subject_prominence < 0.55:
        reasons.append("subject_not_primary_topic")

    source_quality = 0.0
    if page.status_code == 200:
        source_quality += 0.25
    if is_detail:
        source_quality += 0.25
    if is_german:
        source_quality += 0.20
    source_quality += min(topic_score, 1.0) * 0.25
    if host.endswith((".de", ".at", ".ch")):
        source_quality += 0.05
    if is_official:
        source_quality += 0.08
    if any(_host_matches(host, marker) for marker in PAYWALL_MARKERS):
        source_quality -= 0.25
    if any(_host_matches(host, marker) for marker in LOW_VALUE_HOST_MARKERS):
        source_quality -= 0.40
    if is_general_news and is_financial_source and not is_official and not (
        is_results_article and _is_trusted_company_results_host(host)
    ):
        source_quality -= 0.35
    if _is_unofficial_brand_host(host, subject):
        source_quality -= 0.45
    if _is_german_query(query) and (not is_german or not has_german_source_hint) and not is_official:
        source_quality -= 0.30
    if "domain_not_primary_topic" in reasons:
        source_quality -= 0.45
    if "streaming_guide_for_cinema_query" in reasons:
        source_quality -= 0.45
    if is_general_news and domain == "generic" and not is_official and subject_prominence < 0.55:
        source_quality -= 0.45
    if classification.evidence_score >= 0.7:
        source_quality += 0.08
    elif classification.evidence_score < 0.35:
        source_quality -= 0.25
    source_quality = max(0.0, min(source_quality, 1.0))

    return VerifiedSource(
        url=candidate.url,
        canonical_url=final_url,
        title=title[:180],
        source_label=host or candidate.title or "Quelle",
        snippet=snippet[:360],
        page_excerpt=page.text[:900],
        language=language,
        published_at=page.published_at,
        is_reachable=page.status_code == 200,
        is_detail_page=is_detail,
        topic_match_score=round(topic_score, 3),
        source_quality_score=round(source_quality, 3),
        provider=candidate.provider,
        rank=candidate.rank,
        source_type=classification.source_type,
        evidence_score=classification.evidence_score,
        rejection_reasons=tuple(reasons),
    )


def is_verified(source: VerifiedSource) -> bool:
    return (
        source.is_reachable
        and source.is_detail_page
        and source.topic_match_score >= 0.34
        and source.source_quality_score >= 0.55
        and not source.rejection_reasons
    )


def sort_verified_sources(sources: list[VerifiedSource]) -> list[VerifiedSource]:
    return sorted(
        sources,
        key=lambda item: (
            item.language != "de",
            -item.source_quality_score,
            -item.topic_match_score,
            item.rank,
        ),
    )
