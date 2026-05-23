from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping
from urllib.parse import unquote, urlparse

from backend.services.websearch.query_bias import normalize_source_url


class LinkIntent(str, Enum):
    NEWS = "news"
    RELEASE = "release"
    RANKING = "ranking"
    API_DOCS = "api_docs"
    GENERAL = "general"


@dataclass(frozen=True)
class SourceQualityScore:
    score: int
    acceptable: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)
    url: str = ""
    host: str = ""


_LOW_VALUE_DOMAINS = (
    "youtube.",
    "youtu.be",
    "reddit.",
    "tiktok.",
    "facebook.",
    "instagram.",
    "pinterest.",
    "glbgpt.",
    "digen.",
    "cryptobriefing.",
    "dentro.de/ai/news",
    "nevercodealone.",
)

_PAYWALL_DOMAINS = (
    "welt.de",
    "thepioneer.de",
    "pioneer.de",
    "handelsblatt.com",
    "handelsblatt.de",
    "faz.net",
)

_GERMAN_SOURCE_HINTS = (
    ".de",
    ".at",
    ".ch",
    "de.",
    "heise",
    "golem",
    "spiegel",
    "zeit",
    "tagesschau",
    "deutschlandfunk",
    "computerwoche",
    "t3n",
    "basicthinking",
    "netzwelt",
    "winfuture",
    "chip",
    "sueddeutsche",
    "n-tv",
    "ntv",
    "gamepro",
    "gamestar",
    "gameswirtschaft",
    "musikexpress",
    "tonspion",
    "visions",
    "rockhard",
)

_HIGH_QUALITY_NEWS_HOSTS = {
    "openai.com": 16,
    "tagesschau.de": 18,
    "deutschlandfunk.de": 18,
    "spiegel.de": 14,
    "zeit.de": 14,
    "heise.de": 16,
    "golem.de": 16,
    "t3n.de": 13,
    "computerwoche.de": 13,
    "basicthinking.de": 12,
    "netzwelt.de": 10,
    "n-tv.de": 12,
    "ntv.de": 12,
}

_HIGH_QUALITY_RELEASE_HOSTS = {
    "nintendo.com": 14,
    "nintendo.de": 18,
    "gamepro.de": 16,
    "gamestar.de": 16,
    "gameswirtschaft.de": 15,
    "musikexpress.de": 15,
    "tonspion.de": 13,
    "visions.de": 13,
    "rockhard.de": 13,
}

_GENERIC_NEWS_PATHS = {
    "",
    "news",
    "ai/news",
    "ki/news",
    "aktuelles",
    "nachrichten",
    "technology/news",
    "tech/news",
}

_STOPWORDS = {
    "quelle",
    "openai",
    "news",
    "aktuell",
    "aktuelle",
    "meldung",
    "meldungen",
    "mai",
    "juni",
    "seit",
    "wurde",
    "werden",
    "eine",
    "einer",
    "einen",
    "das",
    "der",
    "die",
    "und",
    "fuer",
    "fur",
    "mit",
    "zum",
    "zur",
    "den",
    "dem",
}

_BROAD_LABELS = {
    "openai",
    "google",
    "microsoft",
    "meta",
    "apple",
    "amazon",
    "nvidia",
    "tesla",
}

_PROVIDER_REDIRECT_HOSTS = {
    "vertexaisearch.cloud.google.com",
}


def source_url(source: Mapping[str, Any] | str) -> str:
    if isinstance(source, str):
        return normalize_source_url(source)
    return normalize_source_url(
        str(source.get("url") or source.get("uri") or source.get("source_url") or "").strip()
    )


def source_host_path(source: Mapping[str, Any] | str) -> tuple[str, str]:
    url = source_url(source)
    if not url:
        return "", ""
    try:
        parsed = urlparse(url)
    except Exception:
        return "", ""
    return parsed.netloc.casefold().removeprefix("www."), unquote(parsed.path).casefold()


def source_haystack(source: Mapping[str, Any] | str) -> str:
    if isinstance(source, str):
        url = source_url(source)
        host, path = source_host_path(source)
        return f"{url} {host} {path}"
    url = source_url(source)
    haystack = " ".join(
        str(source.get(key) or "")
        for key in (
            "title",
            "name",
            "source",
            "domain",
            "snippet",
            "description",
            "text",
            "url",
            "uri",
            "source_url",
            "news_target_title",
            "news_target_label",
        )
    )
    host, path = source_host_path(source)
    return f"{haystack} {url} {host} {path}"


def tokenize_quality_text(value: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9][a-z0-9._-]{2,}", str(value or "").casefold())
    return [token for token in tokens if token not in _STOPWORDS and not token.isdigit() and len(token) > 2]


def normalize_label_for_match(value: str) -> str:
    normalized = re.sub(r"\s+", " ", str(value or "")).strip().casefold()
    normalized = re.sub(r"^www\.", "", normalized)
    normalized = re.sub(r"\.(com|de|net|org|co\.uk|tv)$", "", normalized)
    return normalized


def is_generic_news_landing_page(source: Mapping[str, Any] | str) -> bool:
    host, path = source_host_path(source)
    if not host:
        return False
    clean_path = path.strip("/")
    if clean_path in _GENERIC_NEWS_PATHS:
        return True
    return bool(clean_path.endswith("/news") and clean_path.count("/") <= 2)


def is_documentation_page_for_news(source: Mapping[str, Any] | str) -> bool:
    host, path = source_host_path(source)
    if not host:
        return False
    if host == "platform.openai.com" and path.startswith("/docs"):
        return True
    if host.endswith("openai.com") and path.startswith(("/docs", "/api", "/reference")):
        return True
    if host == "help.openai.com" and not any(marker in path for marker in ("release", "releasenotes", "announcements")):
        return True
    return False


def is_paywalled_source(source: Mapping[str, Any] | str) -> bool:
    haystack = source_haystack(source).casefold()
    return any(marker in haystack for marker in _PAYWALL_DOMAINS)


def is_low_value_source(source: Mapping[str, Any] | str, intent: LinkIntent | str = LinkIntent.GENERAL) -> bool:
    link_intent = LinkIntent(intent)
    haystack = source_haystack(source).casefold()
    if any(marker in haystack for marker in _LOW_VALUE_DOMAINS):
        return True
    if link_intent == LinkIntent.NEWS:
        return is_paywalled_source(source) or is_generic_news_landing_page(source) or is_documentation_page_for_news(source)
    return False


def has_german_or_official_signal(source: Mapping[str, Any] | str, label: str = "") -> bool:
    haystack = source_haystack(source).casefold()
    label_norm = normalize_label_for_match(label)
    if label_norm and label_norm in normalize_label_for_match(haystack):
        return True
    return any(marker in haystack for marker in _GERMAN_SOURCE_HINTS)


def score_source_for_intent(
    source: Mapping[str, Any] | str,
    *,
    intent: LinkIntent | str = LinkIntent.GENERAL,
    title: str = "",
    summary: str = "",
    label: str = "",
    target_index: int | str | None = None,
    min_score: int | None = None,
) -> SourceQualityScore:
    link_intent = LinkIntent(intent)
    url = source_url(source)
    host, path = source_host_path(source)
    if not url:
        return SourceQualityScore(-999, False, ("missing_url",), url="", host=host)

    haystack = source_haystack(source).casefold()
    haystack_norm = normalize_label_for_match(haystack)
    label_norm = normalize_label_for_match(label)
    score = 0
    reasons: list[str] = []

    if isinstance(source, Mapping) and target_index is not None and str(source.get("news_target_index") or "") == str(target_index):
        score += 100
        reasons.append("resolved_target")

    if has_german_or_official_signal(source, label):
        score += 14
        reasons.append("german_or_official")

    if label_norm and label_norm in haystack_norm:
        if label_norm in _BROAD_LABELS:
            score += 6
            reasons.append("broad_label_match")
        else:
            score += 20
            reasons.append("label_match")

    tokens = tokenize_quality_text(f"{title} {summary}")[:10]
    token_matches = sum(1 for token in tokens if token in haystack)
    score += token_matches * 5
    if token_matches:
        reasons.append(f"token_match:{token_matches}")

    if link_intent == LinkIntent.NEWS:
        is_provider_redirect = host in _PROVIDER_REDIRECT_HOSTS
        host_bonus = _HIGH_QUALITY_NEWS_HOSTS.get(host, 0)
        if not host_bonus:
            host_bonus = max((bonus for domain, bonus in _HIGH_QUALITY_NEWS_HOSTS.items() if host.endswith("." + domain)), default=0)
        score += host_bonus
        if host_bonus:
            reasons.append("trusted_news_host")
        if is_provider_redirect:
            reasons.append("provider_redirect")
        elif path and path.strip("/") and not is_generic_news_landing_page(source):
            score += 6
            reasons.append("detail_path")
        if is_documentation_page_for_news(source):
            score -= 120
            reasons.append("docs_not_news")
        if is_generic_news_landing_page(source):
            score -= 90
            reasons.append("generic_news_landing")
        if is_paywalled_source(source):
            score -= 55
            reasons.append("paywall")

    elif link_intent == LinkIntent.RELEASE:
        host_bonus = _HIGH_QUALITY_RELEASE_HOSTS.get(host, 0)
        score += host_bonus
        if host_bonus:
            reasons.append("trusted_release_host")

    elif link_intent == LinkIntent.API_DOCS:
        if (host == "platform.openai.com" and path.startswith("/docs")) or (
            host.endswith("openai.com") and path.startswith(("/docs", "/api", "/reference"))
        ):
            score += 80
            reasons.append("official_docs")

    if any(marker in haystack for marker in _LOW_VALUE_DOMAINS):
        score -= 80
        reasons.append("low_value_domain")

    threshold = min_score
    if threshold is None:
        threshold = {
            LinkIntent.NEWS: 24,
            LinkIntent.RELEASE: 18,
            LinkIntent.RANKING: 16,
            LinkIntent.API_DOCS: 30,
            LinkIntent.GENERAL: 1,
        }[link_intent]
    acceptable = score >= threshold and not is_low_value_source(source, link_intent)
    if link_intent == LinkIntent.NEWS and "resolved_target" not in reasons:
        min_token_matches = 3 if "provider_redirect" in reasons else 2
        strong_label = "label_match" in reasons and label_norm not in _BROAD_LABELS
        if token_matches < min_token_matches and not strong_label:
            acceptable = False
            reasons.append("weak_item_binding")
    return SourceQualityScore(score, acceptable, tuple(reasons), url=url, host=host)


def select_best_source_for_item(
    sources: list[Mapping[str, Any]],
    *,
    intent: LinkIntent | str,
    title: str,
    summary: str = "",
    label: str = "",
    target_index: int | str | None = None,
    min_score: int | None = None,
) -> tuple[str, SourceQualityScore]:
    best_url = ""
    best_quality = SourceQualityScore(-999, False, ("no_candidates",))
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        quality = score_source_for_intent(
            source,
            intent=intent,
            title=title,
            summary=summary,
            label=label,
            target_index=target_index,
            min_score=min_score,
        )
        if quality.score > best_quality.score:
            best_quality = quality
            best_url = quality.url
    if not best_quality.acceptable:
        return "", best_quality
    return best_url, best_quality
