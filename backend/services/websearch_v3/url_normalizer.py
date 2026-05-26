from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlencode, urlparse, urlunparse


BLOCKED_HOST_SUFFIXES = (
    "google.com",
    "bing.com",
    "duckduckgo.com",
    "vertexaisearch.cloud.google.com",
)

ASSET_EXTENSIONS = (
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".ico",
    ".css",
    ".js",
    ".pdf",
)


def normalize_url(url: str) -> str:
    value = str(url or "").strip()
    if not value:
        return ""
    if value.startswith("//"):
        value = "https:" + value
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""

    host = parsed.netloc.casefold()
    if host.endswith("duckduckgo.com"):
        params = parse_qs(parsed.query)
        redirect = params.get("uddg", [""])[0] or params.get("rut", [""])[0]
        if redirect:
            return normalize_url(unquote(redirect))

    query_pairs = []
    for key, values in parse_qs(parsed.query, keep_blank_values=True).items():
        lowered = key.casefold()
        if lowered.startswith("utm_") or lowered in {"fbclid", "gclid", "igshid", "mc_cid", "mc_eid"}:
            continue
        for item in values:
            query_pairs.append((key, item))
    query = urlencode(query_pairs, doseq=True)
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunparse((parsed.scheme, parsed.netloc, path, "", query, ""))


def host_for_url(url: str) -> str:
    try:
        return urlparse(url).netloc.casefold().removeprefix("www.")
    except Exception:
        return ""


def path_for_url(url: str) -> str:
    try:
        return unquote(urlparse(url).path or "").casefold()
    except Exception:
        return ""


def is_provider_redirect(url: str) -> bool:
    return host_for_url(url) == "vertexaisearch.cloud.google.com"


def is_search_page(url: str) -> bool:
    host = host_for_url(url)
    path = path_for_url(url)
    if host.endswith("google.com") and path.startswith("/search"):
        return True
    if host.endswith("bing.com") and path.startswith("/search"):
        return True
    if host.endswith("duckduckgo.com"):
        return True
    return False


def is_asset_url(url: str) -> bool:
    path = path_for_url(url)
    return path.endswith(ASSET_EXTENSIONS) or "w3.org/2000/svg" in url.casefold()


def is_blocked_url(url: str) -> bool:
    host = host_for_url(url)
    if not host:
        return True
    return is_search_page(url) or is_asset_url(url) or any(host == blocked or host.endswith("." + blocked) for blocked in BLOCKED_HOST_SUFFIXES)
