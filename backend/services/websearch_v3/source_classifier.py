from __future__ import annotations

import re
from dataclasses import dataclass

from .models import PageFetchResult, SearchCandidate
from .url_normalizer import host_for_url, path_for_url


@dataclass(frozen=True)
class SourceClassification:
    source_type: str
    evidence_score: float
    signals: tuple[str, ...] = ()


def classify_source(candidate: SearchCandidate, page: PageFetchResult) -> SourceClassification:
    url = page.final_url or candidate.url
    host = host_for_url(url)
    path = path_for_url(url)
    title = page.title or candidate.title
    text = f"{title} {candidate.snippet} {page.text[:1400]}"
    lowered = text.casefold()
    signals: list[str] = []

    if _looks_like_search_page(host, path):
        return SourceClassification("search_page", 0.0, ("search_page",))
    if _looks_like_asset(path):
        return SourceClassification("asset", 0.0, ("asset",))
    if _looks_like_forum(host, path, lowered):
        return SourceClassification("community", 0.1, ("community",))
    if _looks_like_curated_briefing(path, title, lowered):
        return SourceClassification("curated_briefing", 0.74, ("curated_briefing",))
    if _looks_like_calendar_or_index(path, title, lowered):
        return SourceClassification("calendar_or_listing", 0.25, ("calendar_or_listing",))
    if _looks_like_topic_page(path, title):
        return SourceClassification("topic_listing", 0.25, ("topic_listing",))

    if _looks_like_official_release(host, path, lowered):
        signals.append("official_release")
        return SourceClassification("official_release", _score_detail_evidence(path, lowered, base=0.78), tuple(signals))
    if _looks_like_release_detail(path, lowered):
        signals.append("release_detail")
        return SourceClassification("release_detail", _score_detail_evidence(path, lowered, base=0.72), tuple(signals))
    if _looks_like_news_article(path, title, lowered):
        signals.append("news_article")
        return SourceClassification("news_article", _score_detail_evidence(path, lowered, base=0.68), tuple(signals))

    if len(path.strip("/").split("/")) >= 2:
        return SourceClassification("detail_page", _score_detail_evidence(path, lowered, base=0.55), ("detail_path",))
    return SourceClassification("unknown", 0.35, ())


def _looks_like_search_page(host: str, path: str) -> bool:
    return (
        host in {"google.com", "www.google.com", "bing.com", "www.bing.com", "duckduckgo.com"}
        or path.startswith("/search")
    )


def _looks_like_asset(path: str) -> bool:
    return bool(re.search(r"\.(?:svg|png|jpe?g|webp|gif|pdf)(?:$|\?)", path))


def _looks_like_forum(host: str, path: str, lowered: str) -> bool:
    return any(marker in host for marker in ("reddit.", "facebook.", "instagram.")) or any(
        marker in path for marker in ("/community/", "/forum/", "/forums/", "/thread/")
    ) or "login | registrieren" in lowered


def _looks_like_calendar_or_index(path: str, title: str, lowered: str) -> bool:
    title_lower = str(title or "").casefold()
    listing_path_markers = (
        "/calendar",
        "/monat.php",
        "/month/",
        "/filmstarts/",
        "/filme-imkino/",
        "/filme-vorschau",
        "/filme/jahre/",
        "/kinofilme/",
        "/news/cinema/month/",
        "/kino/kinoprogramm",
        "/financial-info/financial-reports",
        "/officeupdates/",
        "/release-notes/",
    )
    if any(marker in path for marker in listing_path_markers):
        return True
    listing_title_markers = (
        "alle kinofilme",
        "kinostarts der woche",
        "filme im kino",
        "filmstarts im mai",
        "aktuelle filmstarts",
        "financial reports",
        "release notes",
        "versionshinweise",
        "aktuelle nachrichten zu",
        "news & infos",
    )
    if any(marker in title_lower for marker in listing_title_markers):
        return True
    return sum(1 for marker in ("liste", "uebersicht", "übersicht", "kalender", "archiv") if marker in lowered) >= 2


def _looks_like_curated_briefing(path: str, title: str, lowered: str) -> bool:
    title_lower = str(title or "").casefold()
    if any(
        marker in path
        for marker in (
            "/community/",
            "/forum/",
            "/thread/",
            "/kino/kinoprogramm",
            "/monat.php",
            "/month/",
            "/calendar",
            "/officeupdates/",
            "/release-notes/",
        )
    ):
        return False
    briefing_markers = (
        "highlights",
        "kinostarts der woche",
        "filmstarts im mai",
        "neuheiten",
        "neuerscheinungen",
        "neue filme",
        "neue spiele",
        "release",
        "releases",
        "trailer",
    )
    haystack = f"{title_lower} {lowered}"
    if not any(marker in haystack for marker in briefing_markers):
        return False
    concrete_markers = (
        '"',
        "„",
        "“",
        " gta ",
        "mario",
        "star wars",
        "resurrection",
        "mandalorian",
        "playstation",
        "xbox",
        "nintendo",
        "switch",
    )
    if any(marker in f" {lowered} " for marker in concrete_markers):
        return True
    title_like_hits = len(re.findall(r"\b[A-ZÄÖÜ][a-zäöüß0-9]+(?:[- ][A-ZÄÖÜ0-9][a-zäöüß0-9]+){1,5}\b", str(title or "")))
    return title_like_hits >= 1 and any(marker in lowered for marker in ("startet", "erscheint", "angekuendigt", "angekündigt"))


def _looks_like_topic_page(path: str, title: str) -> bool:
    title_lower = str(title or "").casefold()
    return any(path.startswith(marker) for marker in ("/thema/", "/themen/", "/topic/", "/topics/", "/category/", "/st/")) or any(
        marker in title_lower for marker in ("aktuelle nachrichten und hintergründe", "aktuelle news zu")
    )


def _looks_like_official_release(host: str, path: str, lowered: str) -> bool:
    official_hosts = ("microsoft.com", "openai.com", "apple.com", "nvidia.com")
    return any(host == marker or host.endswith("." + marker) for marker in official_hosts) and any(
        marker in f"{path} {lowered}" for marker in ("news", "press", "presse", "announces", "launch", "release")
    )


def _looks_like_release_detail(path: str, lowered: str) -> bool:
    return any(marker in lowered for marker in ("trailer", "kinostart", "release", "erscheint", "angekuendigt", "angekündigt")) and (
        bool(re.search(r"/(?:film|filme|news|artikel|nachrichten|kritiken)/", path)) or bool(re.search(r"\d{4,}", path))
    )


def _looks_like_news_article(path: str, title: str, lowered: str) -> bool:
    if not title or len(str(title).strip()) < 12:
        return False
    return bool(re.search(r"/(?:news|artikel|nachrichten|presse|blog|source|entertainment|digital)/", path)) or bool(
        re.search(r"\d{4,}", path)
    ) and any(
        marker in lowered
        for marker in (
            "aktuell",
            "berichtet",
            "branche",
            "kuendigt",
            "kündigt",
            "meldet",
            "neue",
            "neuer",
            "stellt",
            "trend",
            "trends",
        )
    )


def _score_detail_evidence(path: str, lowered: str, *, base: float) -> float:
    score = base
    if re.search(r"\d{4,}", path):
        score += 0.07
    if any(marker in lowered for marker in ("trailer", "ankündigt", "angekuendigt", "erscheint", "startet")):
        score += 0.08
    if any(marker in lowered for marker in ("quelle", "pressemitteilung", "official", "newsroom")):
        score += 0.05
    return round(max(0.0, min(score, 1.0)), 3)
