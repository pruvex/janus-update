import asyncio
import logging
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
from urllib.parse import urlparse
from urllib.parse import urlencode

import requests
from requests import HTTPError
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from pydantic import BaseModel, Field

from backend.services import llm_gateway

# Imports aus dem Backend
from backend.services.websearch.websearch import execute_websearch_service
from backend.data.schemas_tools import SuggestionMetadata, ToolErrorDetails, ToolResultV1

logger = logging.getLogger("janus_backend")

_GENERIC_DIRECTORY_HOST_TOKENS = {
    "google",
    "duckduckgo",
    "tripadvisor",
    "yelp",
    "opentable",
    "quandoo",
    "lieferando",
    "instagram",
    "facebook",
    "tiktok",
    "youtube",
    "wolt",
    "ubereats",
}

_BLOCKED_BUSINESS_WEBSITE_HOST_MARKERS = (
    "duckduckgo.com",
    "adguard.com",
    "googleadservices.com",
    "doubleclick.net",
    "facebook.com",
    "instagram.com",
    "tripadvisor.",
    "opentable.",
    "quandoo.",
    "lieferando.",
    "ubereats.",
    "wolt.",
    "yelp.",
    "gelbeseiten.",
    "restaurantguru.",
    "expireddomains.",
    "sedo.",
    "parkingcrew.",
    "parklogic.",
    "afternic.",
    "dan.com",
)

OSM_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/cgi/interpreter",
]

# Overpass [timeout:N] + HTTP client cap: fail faster and try next radius/endpoint (partial results OK).
# Kept modest so several endpoint/radius attempts fit inside _OVERPASS_TOTAL_BUDGET_SEC.
_OVERPASS_QUERY_PLANS = (
    {"radius": 2500, "result_multiplier": 4, "timeout_seconds": 8},
    {"radius": 4000, "result_multiplier": 20, "timeout_seconds": 7},
    {"radius": 1200, "result_multiplier": 2, "timeout_seconds": 6},
)
_OVERPASS_HTTP_TIMEOUT_CAP = 10.0
# Max wall-clock for OSM/Overpass phase (Nominatim + Overpass); then prefer web path.
_OVERPASS_TOTAL_BUDGET_SEC = 10.0
# Min remaining seconds reserved for web extraction / enrichment after OSM (find_local_business_tool total 25s).
_LOCAL_BUSINESS_WEB_TAIL_RESERVE_SEC = 12.0
# Max wall-clock for website-discovery phase; paired with tail reserve so total tool stays ≤25s.
_LOCAL_BUSINESS_DISCOVER_WALL_CAP_SEC = 8.0

_SUPPORTED_ROUTING_MODES = {"driving", "walking", "cycling"}
_GOOGLE_MAPS_TRAVEL_MODE = {
    "driving": "driving",
    "walking": "walking",
    "cycling": "bicycling",
}

# --- Pydantic Models für Tool Arguments ---


class CleanGetDistanceArgs(BaseModel):
    origin: str = Field(
        ...,
        description=(
            "Start der Route als **Stadt, Land** oder **PLZ Ort, Land** "
            "(z.B. 'München, Deutschland', '10115 Berlin, DE'). Keine Koordinaten nötig — Geocoding übernimmt das Tool."
        ),
        min_length=3,
        pattern=r".*\S.*",
    )
    destination: str = Field(
        ...,
        description=(
            "Ziel der Route im gleichen Adressformat wie origin "
            "(z.B. 'Hamburg, Deutschland', '80331 München, DE')."
        ),
        min_length=3,
        pattern=r".*\S.*",
    )
    mode: str = Field(
        "driving",
        description="Verkehrsmittel für die Route: `driving` (Auto), `walking` (zu Fuß), `cycling` (Fahrrad).",
        pattern="^(driving|walking|cycling)$",
    )


# --- Helper ---


def _format_duration(seconds: float) -> str:
    """Formatiert Sekunden in Std. und Min."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours} Std. {minutes} Min."
    return f"{minutes} Min."


def _execution_time_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)


def _geo_suggestion_meta(
    *,
    relevance_tags: Optional[List[str]] = None,
    suggest_follow_up: bool = True,
    primary_entity_name: Optional[str] = None,
) -> SuggestionMetadata:
    return SuggestionMetadata(
        relevance_tags=list(relevance_tags or []),
        suggest_follow_up=suggest_follow_up,
        primary_entity_name=primary_entity_name,
    )


def _tool_v1_metadata(started_at: float, suggestion: Optional[SuggestionMetadata] = None) -> Dict[str, Any]:
    meta: Dict[str, Any] = {"execution_time_ms": _execution_time_ms(started_at)}
    if suggestion is not None:
        meta["suggestion"] = suggestion.model_dump(exclude_none=True)
    return meta


def _build_local_business_search_query(query: str, location: str, provider: str) -> str:
    normalized_query = str(query or "").strip()
    normalized_location = str(location or "").strip()
    if str(provider or "").strip().lower() == "ollama":
        return " ".join(part for part in [normalized_query, normalized_location] if part).strip()
    return (
        f"{normalized_query} in {normalized_location} Adresse Telefonnummer Öffnungszeiten "
        f"offizielle Website Speisekarte Menü Reservierung booking"
    ).strip()


def _build_osm_address(tags: Dict[str, Any], fallback_location: str) -> str:
    if not isinstance(tags, dict):
        return fallback_location or "Adresse nicht gefunden"
    street = str(tags.get("addr:street") or "").strip()
    house_number = str(tags.get("addr:housenumber") or "").strip()
    postcode = str(tags.get("addr:postcode") or "").strip()
    city = str(tags.get("addr:city") or tags.get("addr:town") or tags.get("addr:village") or "").strip()
    parts = [" ".join(part for part in [street, house_number] if part).strip(), " ".join(part for part in [postcode, city] if part).strip()]
    address = ", ".join(part for part in parts if part)
    return address or fallback_location or "Adresse nicht gefunden"


def _infer_osm_cuisine_filters(query: str) -> List[str]:
    lowered = str(query or "").strip().casefold()
    if any(token in lowered for token in ["ital", "pizza", "pasta", "trattoria", "osteria", "pizzeria"]):
        return ["italian", "pizza", "pasta", "mediterranean"]
    return []


def _matches_osm_cuisine_or_name(tags: Dict[str, Any], cuisine_filters: List[str], query: str) -> bool:
    if not isinstance(tags, dict):
        return False
    if not cuisine_filters:
        return True
    cuisine_value = str(tags.get("cuisine") or "").casefold()
    if any(token in cuisine_value for token in cuisine_filters):
        return True
    lowered_query = str(query or "").casefold()
    normalized_name = str(tags.get("name") or "").casefold()
    if any(token in lowered_query for token in ["ital", "pizza", "pasta", "trattoria", "osteria", "pizzeria"]):
        name_markers = ("trattoria", "osteria", "ristorante", "pizzeria", "pizza", "forni", "italia", "italiano")
        return any(marker in normalized_name for marker in name_markers)
    return False


def _build_overpass_query(
    latitude: float,
    longitude: float,
    *,
    cuisine_clause: str,
    radius: int,
    result_limit: int,
    timeout_seconds: int,
) -> str:
    return f"""
    [out:json][timeout:{timeout_seconds}];
    (
      node["amenity"="restaurant"]{cuisine_clause}(around:{radius},{latitude},{longitude});
      way["amenity"="restaurant"]{cuisine_clause}(around:{radius},{latitude},{longitude});
      relation["amenity"="restaurant"]{cuisine_clause}(around:{radius},{latitude},{longitude});
    );
    out center tags {result_limit};
    """.strip()


def _fetch_overpass_elements(
    overpass_query_template: str,
    *,
    location: str,
    query: str,
    deadline: Optional[float] = None,
) -> List[Dict[str, Any]]:
    last_error: Optional[Exception] = None
    for plan in _OVERPASS_QUERY_PLANS:
        for endpoint in OSM_ENDPOINTS:
            if deadline is not None and time.perf_counter() >= deadline:
                logger.warning(
                    "LOCAL-BUSINESS-OSM-CAP: Overpass-Frist erreicht (keine Elemente) — Abbruch OSM, bevorzuge Web-Pfad",
                )
                return []
            planned_query = overpass_query_template.format(
                radius=plan["radius"],
                timeout_seconds=plan["timeout_seconds"],
                result_limit=max(1, int(plan["result_multiplier"])),
            )
            try:
                logger.info(
                    "LOCAL-BUSINESS-OSM-TRY: endpoint='%s' radius=%s timeout=%s location='%s'",
                    endpoint,
                    plan["radius"],
                    plan["timeout_seconds"],
                    location,
                )
                response = requests.get(
                    endpoint,
                    params={"data": planned_query},
                    timeout=min(
                        _OVERPASS_HTTP_TIMEOUT_CAP,
                        float(plan["timeout_seconds"]) + 3.0,
                    ),
                    headers={"User-Agent": "Janus-Projekt local-business/1.0"},
                )
                if response.status_code == 504:
                    raise HTTPError("504 Gateway Timeout", response=response)
                response.raise_for_status()
                payload = response.json()
                elements = payload.get("elements") if isinstance(payload, dict) else []
                if isinstance(elements, list) and elements:
                    logger.info(
                        "LOCAL-BUSINESS-OSM-SUCCESS: endpoint='%s' radius=%s timeout=%s elements=%s",
                        endpoint,
                        plan["radius"],
                        plan["timeout_seconds"],
                        len(elements),
                    )
                    return elements
                logger.info(
                    "LOCAL-BUSINESS-OSM-EMPTY: endpoint='%s' radius=%s timeout=%s",
                    endpoint,
                    plan["radius"],
                    plan["timeout_seconds"],
                )
            except requests.exceptions.Timeout as exc:
                last_error = exc
                logger.warning("OSM Server %s timed out, trying next...", endpoint)
                continue
            except HTTPError as exc:
                last_error = exc
                status_code = getattr(getattr(exc, "response", None), "status_code", None)
                if status_code == 504:
                    logger.warning("OSM Server %s timed out, trying next...", endpoint)
                    continue
                logger.warning(
                    "LOCAL-BUSINESS-OSM-RETRY: endpoint='%s' radius=%s timeout=%s query='%s' location='%s' error=%s",
                    endpoint,
                    plan["radius"],
                    plan["timeout_seconds"],
                    query,
                    location,
                    exc,
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "LOCAL-BUSINESS-OSM-RETRY: endpoint='%s' radius=%s timeout=%s query='%s' location='%s' error=%s",
                    endpoint,
                    plan["radius"],
                    plan["timeout_seconds"],
                    query,
                    location,
                    exc,
                )
    if last_error is not None:
        raise last_error
    return []


def _fallback_businesses_from_osm(
    query: str,
    location: str,
    limit: int,
    *,
    osm_phase_deadline: Optional[float] = None,
) -> List[Dict[str, Any]]:
    normalized_query = str(query or "").strip()
    normalized_location = str(location or "").strip()
    normalized_limit = max(1, min(int(limit or 5), 10))
    candidate_limit = max(normalized_limit, min(normalized_limit * 3, 20))
    if not normalized_query or not normalized_location:
        return []
    _osm_deadline = (
        osm_phase_deadline
        if osm_phase_deadline is not None
        else time.perf_counter() + _OVERPASS_TOTAL_BUDGET_SEC
    )
    try:
        if time.perf_counter() >= _osm_deadline:
            logger.info("LOCAL-BUSINESS-OSM: Abbruch vor Geocode (OSM-Frist bereits erreicht)")
            return []
        geolocator = Nominatim(user_agent="Janus-Projekt local-business/1.0")
        _geo_secs = _osm_deadline - time.perf_counter()
        _geo_timeout = min(5.0, max(0.5, _geo_secs - 0.15))
        if _geo_timeout < 0.5:
            logger.info("LOCAL-BUSINESS-OSM: zu wenig Zeit für Nominatim — Abbruch")
            return []
        geo_result = geolocator.geocode(normalized_location, exactly_one=True, timeout=_geo_timeout)
        if geo_result is None:
            logger.info("LOCAL-BUSINESS-OSM: geocode returned no result for location='%s'", normalized_location)
            return []
        latitude = float(getattr(geo_result, "latitude", 0.0) or 0.0)
        longitude = float(getattr(geo_result, "longitude", 0.0) or 0.0)
        if not latitude and not longitude:
            return []

        cuisine_filters = _infer_osm_cuisine_filters(normalized_query)
        cuisine_clause = ""
        if cuisine_filters:
            cuisine_pattern = "|".join(re.escape(value) for value in cuisine_filters)
            cuisine_clause = f'["cuisine"~"(^|;|,|\\s)({cuisine_pattern})(;|,|\\s|$)",i]'

        filtered_query = _build_overpass_query(
            latitude,
            longitude,
            cuisine_clause=cuisine_clause,
            radius="{radius}",
            result_limit="{result_limit}",
            timeout_seconds="{timeout_seconds}",
        )
        elements = _fetch_overpass_elements(
            filtered_query,
            location=normalized_location,
            query=normalized_query,
            deadline=_osm_deadline,
        )
        if not isinstance(elements, list):
            elements = []
        if len(elements) < candidate_limit:
            broad_query = _build_overpass_query(
                latitude,
                longitude,
                cuisine_clause="",
                radius="{radius}",
                result_limit="{result_limit}",
                timeout_seconds="{timeout_seconds}",
            )
            try:
                broad_elements = _fetch_overpass_elements(
                    broad_query,
                    location=normalized_location,
                    query=f"{normalized_query} broad_fallback",
                    deadline=_osm_deadline,
                )
            except Exception as exc:
                logger.warning(
                    "LOCAL-BUSINESS-OSM-BROADEN: broad query failed for query='%s' location='%s' error=%s",
                    normalized_query,
                    normalized_location,
                    exc,
                )
                broad_elements = []
            if isinstance(broad_elements, list) and broad_elements:
                logger.info(
                    "LOCAL-BUSINESS-OSM-BROADEN: location='%s' strict_elements=%s broad_elements=%s",
                    normalized_location,
                    len(elements),
                    len(broad_elements),
                )
                strict_ids = {
                    f"{str(item.get('type') or '')}:{str(item.get('id') or '')}"
                    for item in elements
                    if isinstance(item, dict)
                }
                for item in broad_elements:
                    if not isinstance(item, dict):
                        continue
                    item_key = f"{str(item.get('type') or '')}:{str(item.get('id') or '')}"
                    if item_key in strict_ids:
                        continue
                    tags = item.get("tags") if isinstance(item.get("tags"), dict) else {}
                    if not _matches_osm_cuisine_or_name(tags, cuisine_filters, normalized_query):
                        continue
                    elements.append(item)
                    strict_ids.add(item_key)
                    if len(elements) >= candidate_limit:
                        break

        businesses: List[Dict[str, Any]] = []
        seen_names: set[str] = set()
        for element in elements:
            if not isinstance(element, dict):
                continue
            tags = element.get("tags") if isinstance(element.get("tags"), dict) else {}
            name = str(tags.get("name") or "").strip()
            if not name:
                continue
            normalized_name = name.casefold()
            if normalized_name in seen_names:
                continue
            seen_names.add(normalized_name)
            website = _sanitize_business_website(tags.get("website") or tags.get("contact:website"))
            phone = str(tags.get("phone") or tags.get("contact:phone") or "").strip() or None
            opening_hours = str(tags.get("opening_hours") or "").strip() or None
            cuisine = str(tags.get("cuisine") or "").strip() or None
            business = {
                "name": name[:160],
                "description": None,
                "category": cuisine[:120] if cuisine else None,
                "address": _build_osm_address(tags, normalized_location),
                "opening_hours": opening_hours,
                "phone": phone,
                "email": None,
                "website": website,
                "contact": website or phone,
                "menu_url": None,
                "reservation_url": None,
                "source": "osm_overpass_fallback",
                "query": normalized_query,
                "location": normalized_location,
            }
            if _is_viable_business_entry(business):
                businesses.append(business)
            if len(businesses) >= candidate_limit:
                break
        logger.info(
            "LOCAL-BUSINESS-OSM: location='%s' cuisine_filters=%s businesses=%s candidate_limit=%s",
            normalized_location,
            cuisine_filters,
            len(businesses),
            candidate_limit,
        )
        return businesses
    except Exception as exc:
        logger.warning(
            "LOCAL-BUSINESS-OSM: fallback failed for query='%s' location='%s' error=%s",
            normalized_query,
            normalized_location,
            exc,
        )
        return []


def _country_error(
    started_at: float,
    code: str,
    message: str,
    details: Optional[str] = None,
) -> ToolResultV1:
    err_details: Optional[Dict[str, Any]] = {"detail": details} if details else None
    return ToolResultV1(
        status="error",
        data={},
        error=ToolErrorDetails(code=code, message=message, details=err_details),
        metadata=_tool_v1_metadata(
            started_at,
            _geo_suggestion_meta(relevance_tags=["geo", "country"], suggest_follow_up=False),
        ),
    )


def _local_business_error(
    started_at: float,
    code: str,
    message: str,
    *,
    query: str,
    location: str,
    details: Optional[Dict[str, Any]] = None,
) -> ToolResultV1:
    err_details: Dict[str, Any] = {"query": query, "location": location}
    if details:
        err_details.update(details)
    return ToolResultV1(
        status="error",
        data={},
        error=ToolErrorDetails(code=code, message=message, details=err_details),
        metadata=_tool_v1_metadata(
            started_at,
            _geo_suggestion_meta(relevance_tags=["local_business"], suggest_follow_up=False),
        ),
    )


def _extract_candidate_urls(search_results: Dict[str, Any]) -> List[str]:
    raw_urls = search_results.get("urls")
    if isinstance(raw_urls, list):
        return [str(url).strip() for url in raw_urls if str(url).strip()]
    return []


def _clean_business_field(value: Optional[str]) -> Optional[str]:
    cleaned = str(value or "").strip()
    if not cleaned:
        return None
    lowered = cleaned.lower()
    if lowered in {"keine", "keine angabe", "unbekannt", "nicht gefunden", "-", "n/a", "none"}:
        return None
    return cleaned[:500]


def _derive_business_name_from_url(url: str) -> Optional[str]:
    host = _extract_domain_hint(url)
    if not host:
        return None
    base = host.split(":", 1)[0]
    if "." in base:
        base = base.split(".")[0]
    if not base or base in _GENERIC_DIRECTORY_HOST_TOKENS:
        return None
    cleaned = " ".join(part for part in base.replace("-", " ").replace("_", " ").split() if part)
    if not cleaned:
        return None
    words = [word[:1].upper() + word[1:] for word in cleaned.split()]
    return " ".join(words)[:160]


def _looks_like_placeholder_business(name: Optional[str], address: Optional[str], website: Optional[str]) -> bool:
    normalized_name = " ".join(str(name or "").strip().lower().split())
    normalized_address = " ".join(str(address or "").strip().lower().split())
    normalized_website = str(website or "").strip().lower()
    if not normalized_name:
        return True
    blocked_name_markers = [
        "keine passenden suchergebnisse gefunden",
        "keine passenden treffer gefunden",
        "keine treffer gefunden",
        "keine passenden restaurants gefunden",
        "keine passenden läden gefunden",
        "keine passenden laden gefunden",
        "adresse nicht gefunden",
        "nicht gefunden",
    ]
    if any(marker in normalized_name for marker in blocked_name_markers):
        return True
    if normalized_address == "adresse nicht gefunden" and not normalized_website:
        return True
    return False


def _is_viable_business_entry(business: Dict[str, Any]) -> bool:
    if not isinstance(business, dict):
        return False
    name = str(business.get("name") or "").strip()
    address = str(business.get("address") or "").strip()
    website = str(business.get("website") or "").strip()
    if _looks_like_placeholder_business(name, address, website):
        return False
    return bool(name) and (bool(website) or address.lower() != "adresse nicht gefunden")


def _fallback_businesses_from_candidates(
    urls: List[str],
    query: str,
    location: str,
    limit: int,
) -> List[Dict[str, Any]]:
    normalized_urls = [str(url).strip() for url in (urls or []) if str(url).strip()]
    businesses: List[Dict[str, Any]] = []
    seen_names: set[str] = set()
    for url in normalized_urls:
        name = _derive_business_name_from_url(url)
        if not name:
            continue
        normalized_name = name.casefold()
        if normalized_name in seen_names:
            continue
        seen_names.add(normalized_name)
        menu_url = url if any(token in url.lower() for token in ["menu", "menue", "speisekarte", "karte"]) else None
        reservation_url = url if any(token in url.lower() for token in ["reserv", "booking", "book", "table", "opentable", "quandoo"]) else None
        businesses.append(
            {
                "name": name,
                "description": None,
                "category": None,
                "address": "Adresse nicht gefunden",
                "opening_hours": None,
                "phone": None,
                "email": None,
                "website": url,
                "contact": url,
                "menu_url": menu_url,
                "reservation_url": reservation_url,
                "source": "websearch_url_fallback",
                "query": query,
                "location": location,
            }
        )
        if not _is_viable_business_entry(businesses[-1]):
            businesses.pop()
            continue
        if len(businesses) >= limit:
            break
    return businesses


def _normalize_candidate_business_name(raw_name: Optional[str], query: str, location: str) -> Optional[str]:
    candidate = str(raw_name or "").strip()
    if not candidate:
        return None
    candidate = re.sub(r"\s+", " ", candidate)
    candidate = re.sub(r"^[\-\*•\d\.)\s]+", "", candidate).strip(" -–—:;,.")
    if not candidate:
        return None
    lowered = candidate.casefold()
    blocked_fragments = [
        str(query or "").strip().casefold(),
        str(location or "").strip().casefold(),
        "treffer",
        "suchergebnisse",
        "ergebnisse",
        "restaurants",
        "restaurant",
        "offizielle website",
        "oeffnungszeiten",
        "öffnungszeiten",
        "telefonnummer",
        "reservierung",
        "booking",
        "adresse",
    ]
    if any(fragment and fragment == lowered for fragment in blocked_fragments):
        return None
    if ":" in candidate and lowered.startswith(("treffer:", "suchergebnisse:", "ergebnisse:")):
        candidate = candidate.split(":", 1)[1].strip()
        lowered = candidate.casefold()
    if not candidate:
        return None
    if any(marker in lowered for marker in ["keine treffer", "keine passenden", "nicht gefunden"]):
        return None
    words = [word for word in re.split(r"\s+", candidate) if word]
    if len(words) > 8:
        return None
    if sum(ch.isalpha() for ch in candidate) < 3:
        return None
    return candidate[:160]


def _extract_candidate_name_fragments(line: str, location: str) -> List[str]:
    candidate_line = str(line or "").strip()
    if not candidate_line:
        return []

    fragments: List[str] = []
    if ":" in candidate_line and candidate_line.lower().startswith(("treffer", "suchergebnisse", "ergebnisse")):
        fragments.extend(part.strip() for part in candidate_line.split(":", 1)[1].split(",") if part.strip())
    elif candidate_line.startswith(("-", "*", "•")):
        bullet_body = candidate_line.lstrip("-*• ").strip()
        if bullet_body:
            shortened_fragments: List[str] = []
            for separator in (" - ", " – ", " — ", " | ", " · ", ": "):
                if separator in bullet_body:
                    shortened_fragments.append(bullet_body.split(separator, 1)[0].strip())
            normalized_location = str(location or "").strip()
            if normalized_location:
                location_patterns = [
                    f" in {normalized_location}",
                    f", {normalized_location}",
                    f" - {normalized_location}",
                    f" – {normalized_location}",
                ]
                lowered_body = bullet_body.casefold()
                for pattern in location_patterns:
                    idx = lowered_body.find(pattern.casefold())
                    if idx > 0:
                        shortened_fragments.append(bullet_body[:idx].strip(" -–—|,:;"))
            shortened_fragments = sorted(
                shortened_fragments,
                key=lambda value: (len(str(value or "").split()), len(str(value or ""))),
            )
            fragments.extend(shortened_fragments)
            fragments.append(bullet_body)
    deduped_fragments: List[str] = []
    seen: set[str] = set()
    for fragment in fragments:
        normalized_fragment = str(fragment or "").strip()
        if not normalized_fragment:
            continue
        key = normalized_fragment.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped_fragments.append(normalized_fragment)
    return deduped_fragments


def _fallback_businesses_from_text(
    text: str,
    urls: List[str],
    query: str,
    location: str,
    limit: int,
) -> List[Dict[str, Any]]:
    normalized_text = str(text or "").strip()
    if not normalized_text or _looks_like_no_business_results_text(normalized_text):
        return []
    normalized_urls = [str(url).strip() for url in (urls or []) if str(url).strip()]
    candidate_names: List[str] = []
    for raw_line in normalized_text.splitlines():
        line = str(raw_line or "").strip()
        if not line:
            continue
        fragments = _extract_candidate_name_fragments(line, location)
        allow_multiple_candidates = ":" in line and line.lower().startswith(("treffer", "suchergebnisse", "ergebnisse"))
        for fragment in fragments:
            normalized_name = _normalize_candidate_business_name(fragment, query, location)
            if normalized_name:
                candidate_names.append(normalized_name)
                if not allow_multiple_candidates:
                    break
    businesses: List[Dict[str, Any]] = []
    seen_names: set[str] = set()
    usable_urls = [
        url for url in normalized_urls if (_derive_business_name_from_url(url) is not None or any(token in url.lower() for token in ["menu", "menue", "speisekarte", "reserv", "booking", "book", "table"]))
    ]
    for idx, name in enumerate(candidate_names):
        dedupe_key = name.casefold()
        if dedupe_key in seen_names:
            continue
        seen_names.add(dedupe_key)
        website = usable_urls[idx] if idx < len(usable_urls) else None
        menu_url = website if website and any(token in website.lower() for token in ["menu", "menue", "speisekarte", "karte"]) else None
        reservation_url = website if website and any(token in website.lower() for token in ["reserv", "booking", "book", "table", "opentable", "quandoo"]) else None
        business = {
            "name": name,
            "description": None,
            "category": None,
            "address": location,
            "opening_hours": None,
            "phone": None,
            "email": None,
            "website": website,
            "contact": website,
            "menu_url": menu_url,
            "reservation_url": reservation_url,
            "source": "websearch_snippet_fallback",
            "query": query,
            "location": location,
        }
        if _is_viable_business_entry(business):
            businesses.append(business)
        if len(businesses) >= limit:
            break
    return businesses


def _pick_candidate_url(urls: List[str], *, preferred_tokens: Optional[List[str]] = None) -> Optional[str]:
    normalized_urls = [str(url).strip() for url in (urls or []) if str(url).strip()]
    if not normalized_urls:
        return None
    tokens = [str(token).lower() for token in (preferred_tokens or []) if str(token).strip()]
    if tokens:
        for url in normalized_urls:
            lowered = url.lower()
            if any(token in lowered for token in tokens):
                return url
    return normalized_urls[0]


def _extract_domain_hint(url: Optional[str]) -> Optional[str]:
    parsed = urlparse(str(url or "").strip())
    host = str(parsed.netloc or "").strip().lower()
    if not host:
        return None
    if host.startswith("www."):
        host = host[4:]
    return host or None


def _is_blocked_business_website(url: Optional[str]) -> bool:
    host = _extract_domain_hint(url)
    if not host:
        return False
    return any(marker in host for marker in _BLOCKED_BUSINESS_WEBSITE_HOST_MARKERS)


def _sanitize_business_website(url: Optional[str]) -> Optional[str]:
    normalized = str(url or "").strip()
    if not normalized:
        return None
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    if _is_blocked_business_website(normalized):
        return None
    return normalized


def _is_more_specific_url(candidate: Optional[str], current: Optional[str]) -> bool:
    candidate_value = str(candidate or "").strip()
    current_value = str(current or "").strip()
    if not candidate_value:
        return False
    if not current_value:
        return True
    current_parsed = urlparse(current_value)
    candidate_parsed = urlparse(candidate_value)
    current_path = str(current_parsed.path or "").strip("/")
    candidate_path = str(candidate_parsed.path or "").strip("/")
    if not candidate_path:
        return False
    if not current_path:
        return True
    return len(candidate_path) > len(current_path)


def _extract_opening_hours_from_text(text: str) -> Optional[str]:
    normalized_text = "\n".join(line.strip() for line in str(text or "").splitlines() if line.strip())
    if not normalized_text:
        return None
    patterns = [
        r"((?:Mo|Di|Mi|Do|Fr|Sa|So)(?:\s*[-–—]\s*(?:Mo|Di|Mi|Do|Fr|Sa|So))?\s+\d{1,2}[:.]\d{2}\s*[-–—]\s*\d{1,2}[:.]\d{2})",
        r"((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:\s*[-–—]\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun))?\s+\d{1,2}[:.]\d{2}\s*[-–—]\s*\d{1,2}[:.]\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized_text, flags=re.IGNORECASE)
        if match:
            return match.group(1)[:120]
    return None


def _extract_first_match(pattern: str, text: str) -> Optional[str]:
    match = re.search(pattern, str(text or ""), flags=re.IGNORECASE)
    if not match:
        return None
    return str(match.group(0) or "").strip()[:200]


def _extract_phone_from_text(text: str) -> Optional[str]:
    normalized_text = str(text or "")
    if not normalized_text:
        return None
    candidates = re.findall(r"(?:\+\d{1,3}[\s/\-]?)?(?:\(?\d{2,5}\)?[\s/\-]?){2,6}\d{2,}", normalized_text, flags=re.IGNORECASE)
    for raw_candidate in candidates:
        candidate = str(raw_candidate or "").strip()
        if not candidate:
            continue
        compact = re.sub(r"\s+", " ", candidate)
        digits_only = re.sub(r"\D", "", compact)
        if len(digits_only) < 7:
            continue
        if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", compact):
            continue
        if re.fullmatch(r"\d{1,2}[.-]\d{1,2}[.-]\d{2,4}", compact):
            continue
        return compact[:200]
    return None


def _looks_like_bot_protection_page(text: str, resolved_url: Optional[str] = None) -> bool:
    normalized_text = " ".join(str(text or "").casefold().split())
    normalized_url = str(resolved_url or "").casefold()
    if not normalized_text and not normalized_url:
        return False
    markers = (
        "ddos protection",
        "dDoS protection",
        "checking your browser",
        "verify you are human",
        "please enable javascript and cookies",
        "security check to access",
        "press and hold",
        "cloudflare",
        "attention required",
        "captcha",
        "sorry, you have been blocked",
    )
    return any(marker.casefold() in normalized_text for marker in markers) or "cdn-cgi/challenge" in normalized_url


def _business_quality_score(business: Dict[str, Any]) -> tuple[int, int, int, int, int, str]:
    if not isinstance(business, dict):
        return (0, 0, 0, 0, 0, "")
    website = 1 if _sanitize_business_website(business.get("website")) else 0
    menu = 1 if str(business.get("menu_url") or "").strip() else 0
    reservation = 1 if str(business.get("reservation_url") or "").strip() else 0
    hours = 1 if str(business.get("opening_hours") or "").strip() else 0
    phone = 1 if str(business.get("phone") or "").strip() else 0
    return (website + menu + reservation + hours + phone, website + menu + reservation, website, menu + reservation, hours + phone, str(business.get("name") or "").casefold())


def _choose_best_discovered_website(urls: List[str], business_name: str) -> Optional[str]:
    normalized_name = " ".join(str(business_name or "").casefold().replace("&", " ").replace("-", " ").split())
    name_tokens = [token for token in normalized_name.split() if len(token) >= 3]
    viable_urls = [url for url in (urls or []) if _sanitize_business_website(url)]
    if not viable_urls:
        return None
    for url in viable_urls:
        host = _extract_domain_hint(url) or ""
        lowered = f"{host} {url}".casefold()
        if name_tokens and sum(1 for token in name_tokens if token in lowered) >= max(1, min(2, len(name_tokens))):
            return _sanitize_business_website(url)
    return _sanitize_business_website(_pick_candidate_url(viable_urls))


def _business_name_tokens_for_matching(business_name: str) -> List[str]:
    normalized_name = re.sub(r"[^a-z0-9\s-]", " ", str(business_name or "").casefold())
    raw_tokens = [token for token in normalized_name.replace("-", " ").split() if token]
    if not raw_tokens:
        return []
    kept_tokens: List[str] = []
    for index, token in enumerate(raw_tokens):
        if len(token) >= 2 or (index == 0 and len(raw_tokens) >= 2):
            kept_tokens.append(token)
    return kept_tokens or raw_tokens


def _location_tokens_for_matching(address: str, location: str) -> List[str]:
    combined = " ".join(part for part in [str(address or "").casefold(), str(location or "").casefold()] if part)
    normalized = re.sub(r"[^a-z0-9äöüß\s-]", " ", combined)
    tokens = [token for token in normalized.replace("-", " ").split() if len(token) >= 3]
    stop_tokens = {
        "straße",
        "strasse",
        "allee",
        "platz",
        "restaurant",
        "italienische",
        "italian",
    }
    filtered: List[str] = []
    for token in tokens:
        if token in stop_tokens:
            continue
        if token not in filtered:
            filtered.append(token)
    return filtered


def _build_business_domain_guess_candidates(business_name: str) -> List[str]:
    tokens = _business_name_tokens_for_matching(business_name)
    if not tokens:
        return []
    filtered_tokens = [token for token in tokens if len(token) >= 2]
    if not filtered_tokens:
        filtered_tokens = tokens[:]
    joined = "".join(tokens)
    hyphenated = "-".join(tokens)
    fallback_joined = "".join(filtered_tokens)
    fallback_hyphenated = "-".join(filtered_tokens)
    compact = "".join(token for token in filtered_tokens if token not in {"restaurant", "ristorante", "trattoria", "pizzeria", "osteria"})
    bases: List[str] = []
    for candidate in (joined, hyphenated, fallback_joined, fallback_hyphenated, compact):
        cleaned = str(candidate or "").strip("-")
        if cleaned and cleaned not in bases:
            bases.append(cleaned)
    guessed_urls: List[str] = []
    for base in bases[:4]:
        for prefix in ("https://www.", "https://"):
            for tld in (".de", ".berlin", ".com"):
                guessed = f"{prefix}{base}{tld}/"
                if guessed not in guessed_urls:
                    guessed_urls.append(guessed)
    return guessed_urls


def _score_website_candidate(
    website: Optional[str],
    business_name: str,
    *,
    address: str = "",
    location: str = "",
    menu_url: Optional[str] = None,
    reservation_url: Optional[str] = None,
) -> tuple[int, int, int, int, int, str]:
    normalized_website = _sanitize_business_website(website)
    if not normalized_website:
        return (0, 0, 0, 0, 0, "")
    parsed = urlparse(normalized_website)
    host = str(parsed.netloc or "").casefold()
    matching_tokens = _business_name_tokens_for_matching(business_name)
    token_matches = sum(1 for token in matching_tokens if token in f"{host} {normalized_website}".casefold())
    location_tokens = _location_tokens_for_matching(address, location)
    location_matches = sum(1 for token in location_tokens if token in f"{host} {normalized_website}".casefold())
    https_score = 1 if parsed.scheme == "https" else 0
    tld_score = 2 if host.endswith(".de") else 1 if host.endswith(".berlin") else 0
    detail_score = int(bool(str(menu_url or "").strip())) + int(bool(str(reservation_url or "").strip()))
    host_length_bonus = max(0, 80 - len(host))
    return (token_matches, location_matches, https_score, tld_score, detail_score + host_length_bonus, normalized_website)


def _probe_business_website_guess(url: str, business_name: str, *, address: str = "", location: str = "") -> Optional[Dict[str, Optional[str]]]:
    website = _sanitize_business_website(url)
    if not website:
        return None
    try:
        response = requests.get(
            website,
            timeout=8,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
            },
        )
        response.raise_for_status()
    except Exception:
        return None
    resolved_website = _sanitize_business_website(getattr(response, "url", None)) or website
    if not resolved_website:
        return None
    page_text = "\n".join(
        line.strip() for line in BeautifulSoup(str(response.text or ""), "html.parser").get_text("\n", strip=True).splitlines() if line.strip()
    )
    if _looks_like_bot_protection_page(page_text, getattr(response, "url", None)):
        return None
    business_tokens = _business_name_tokens_for_matching(business_name)
    location_tokens = _location_tokens_for_matching(address, location)
    relevance_haystack = f"{resolved_website} {page_text[:2000]}".casefold()
    if business_tokens and sum(1 for token in business_tokens if token in relevance_haystack) < max(1, min(2, len(business_tokens))):
        return None
    if location_tokens and not any(token in relevance_haystack for token in location_tokens[:4]):
        return None
    soup = BeautifulSoup(str(response.text or ""), "html.parser")
    candidate_urls: List[str] = []
    for link in soup.find_all("a", href=True):
        href = str(link.get("href") or "").strip()
        if not href:
            continue
        absolute_url = _sanitize_business_website(urljoin(resolved_website, href))
        if absolute_url:
            candidate_urls.append(absolute_url)
    return {
        "website": resolved_website,
        "menu_url": _pick_candidate_url(candidate_urls, preferred_tokens=["speisekarte", "menu", "menue", "karte"]),
        "reservation_url": _pick_candidate_url(candidate_urls, preferred_tokens=["reserv", "booking", "book", "table", "opentable", "quandoo"]),
    }


async def _discover_missing_business_websites(
    businesses: List[Dict[str, Any]],
    *,
    query: str,
    location: str,
    provider: str,
    model: str,
    api_key: str,
    max_discoveries: int = 3,
    deadline: Optional[float] = None,
) -> List[Dict[str, Any]]:
    discovered: List[Dict[str, Any]] = []
    discovery_count = 0
    for idx, business in enumerate(businesses):
        if deadline is not None and time.perf_counter() >= deadline:
            logger.info(
                "LOCAL-BUSINESS-WEBSITE-DISCOVERY: Abbruch (Frist) — %d Einträge unverändert übernommen",
                len(businesses) - idx,
            )
            discovered.extend(businesses[idx:])
            break
        current = dict(business) if isinstance(business, dict) else business
        if not isinstance(current, dict):
            discovered.append(current)
            continue
        if discovery_count >= max_discoveries or _sanitize_business_website(current.get("website")):
            discovered.append(current)
            continue
        business_name = str(current.get("name") or "").strip()
        address = str(current.get("address") or "").strip()
        if not business_name:
            discovered.append(current)
            continue
        search_query = " ".join(part for part in [business_name, address, location, query, "offizielle Website", "Speisekarte", "Reservierung"] if part)
        try:
            search_result = await execute_websearch_service(
                query=search_query,
                api_key=api_key,
                provider=provider,
                model=model,
            )
        except Exception as exc:
            logger.info("LOCAL-BUSINESS-WEBSITE-DISCOVERY: search failed for name=%r error=%s", business_name, exc)
            discovered.append(current)
            continue
        if not isinstance(search_result, dict):
            discovered.append(current)
            continue
        candidate_urls = _extract_candidate_urls(search_result)
        website = _choose_best_discovered_website(candidate_urls, business_name)
        if not website:
            if provider == "ollama":
                best_guessed_payload: Optional[Dict[str, Optional[str]]] = None
                best_guessed_score: Optional[tuple[int, int, int, int, int, str]] = None
                for guessed_url in _build_business_domain_guess_candidates(business_name):
                    if deadline is not None and time.perf_counter() >= deadline:
                        logger.info(
                            "LOCAL-BUSINESS-WEBSITE-DISCOVERY: Domain-Try Abbruch (Frist) name=%r",
                            business_name,
                        )
                        break
                    guessed_payload = _probe_business_website_guess(
                        guessed_url,
                        business_name,
                        address=address,
                        location=location,
                    )
                    if not guessed_payload:
                        continue
                    candidate_score = _score_website_candidate(
                        guessed_payload.get("website"),
                        business_name,
                        address=address,
                        location=location,
                        menu_url=guessed_payload.get("menu_url"),
                        reservation_url=guessed_payload.get("reservation_url"),
                    )
                    if best_guessed_score is None or candidate_score > best_guessed_score:
                        best_guessed_payload = guessed_payload
                        best_guessed_score = candidate_score
                if not best_guessed_payload:
                    logger.info("LOCAL-BUSINESS-WEBSITE-DISCOVERY: no website found for name=%r urls=%s", business_name, len(candidate_urls))
                    discovered.append(current)
                    continue
                website = str(best_guessed_payload.get("website") or "").strip()
                current["website"] = website
                if not str(current.get("menu_url") or "").strip() and str(best_guessed_payload.get("menu_url") or "").strip():
                    current["menu_url"] = best_guessed_payload.get("menu_url")
                if not str(current.get("reservation_url") or "").strip() and str(best_guessed_payload.get("reservation_url") or "").strip():
                    current["reservation_url"] = best_guessed_payload.get("reservation_url")
                contact_parts = [part for part in [current.get("phone"), current.get("email"), current.get("website")] if str(part or "").strip()]
                current["contact"] = " | ".join(str(part).strip() for part in contact_parts) if contact_parts else None
                discovery_count += 1
                logger.info(
                    "LOCAL-BUSINESS-WEBSITE-DISCOVERY: guessed website for name=%r website=%r menu=%s reservation=%s",
                    business_name,
                    website,
                    bool(str(current.get("menu_url") or "").strip()),
                    bool(str(current.get("reservation_url") or "").strip()),
                )
                discovered.append(current)
                continue
            logger.info("LOCAL-BUSINESS-WEBSITE-DISCOVERY: no website found for name=%r urls=%s", business_name, len(candidate_urls))
            discovered.append(current)
            continue
        current["website"] = website
        if not str(current.get("menu_url") or "").strip():
            current["menu_url"] = _pick_candidate_url(candidate_urls, preferred_tokens=["speisekarte", "menu", "menue", "karte"])
        if not str(current.get("reservation_url") or "").strip():
            current["reservation_url"] = _pick_candidate_url(candidate_urls, preferred_tokens=["reserv", "booking", "book", "table", "opentable", "quandoo"])
        contact_parts = [part for part in [current.get("phone"), current.get("email"), current.get("website")] if str(part or "").strip()]
        current["contact"] = " | ".join(str(part).strip() for part in contact_parts) if contact_parts else None
        discovery_count += 1
        logger.info(
            "LOCAL-BUSINESS-WEBSITE-DISCOVERY: name=%r website=%r menu=%s reservation=%s",
            business_name,
            website,
            bool(str(current.get("menu_url") or "").strip()),
            bool(str(current.get("reservation_url") or "").strip()),
        )
        discovered.append(current)
    return discovered


def _enrich_business_from_website(business: Dict[str, Any]) -> Dict[str, Any]:
    raw_website = str(business.get("website") or "").strip()
    website = _sanitize_business_website(raw_website)
    if not website:
        logger.info(
            "LOCAL-BUSINESS-WEBSITE: skip website enrichment for name=%r raw_website=%r blocked_or_missing=%s",
            str(business.get("name") or "").strip(),
            raw_website,
            bool(raw_website),
        )
        return business
    try:
        response = requests.get(
            website,
            timeout=12,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
            },
        )
        response.raise_for_status()
    except Exception as exc:
        logger.info("LOCAL-BUSINESS-WEBSITE: fetch failed for website='%s' error=%s", website, exc)
        return business

    soup = BeautifulSoup(str(response.text or ""), "html.parser")
    page_text = "\n".join(line.strip() for line in soup.get_text("\n", strip=True).splitlines() if line.strip())
    resolved_website = _sanitize_business_website(getattr(response, "url", None)) or website
    if _looks_like_bot_protection_page(page_text, getattr(response, "url", None)):
        logger.info(
            "LOCAL-BUSINESS-WEBSITE: protection page detected for name=%r raw_website=%r resolved=%r",
            str(business.get("name") or "").strip(),
            raw_website,
            str(getattr(response, "url", None) or "").strip(),
        )
        merged = dict(business)
        merged["website"] = None
        merged["menu_url"] = None
        merged["reservation_url"] = None
        contact_parts = [part for part in [merged.get("phone"), merged.get("email")] if str(part or "").strip()]
        merged["contact"] = " | ".join(str(part).strip() for part in contact_parts) if contact_parts else None
        return merged
    if _is_blocked_business_website(getattr(response, "url", None)):
        logger.info(
            "LOCAL-BUSINESS-WEBSITE: resolved target blocked for name=%r raw_website=%r resolved=%r",
            str(business.get("name") or "").strip(),
            raw_website,
            str(getattr(response, "url", None) or "").strip(),
        )
        merged = dict(business)
        merged["website"] = None
        merged["menu_url"] = None
        merged["reservation_url"] = None
        contact_parts = [part for part in [merged.get("phone"), merged.get("email")] if str(part or "").strip()]
        merged["contact"] = " | ".join(str(part).strip() for part in contact_parts) if contact_parts else None
        return merged
    candidate_urls: List[str] = []
    for link in soup.select("a[href]"):
        href = str(link.get("href") or "").strip()
        if not href:
            continue
        absolute_url = _sanitize_business_website(urljoin(resolved_website, href))
        if not absolute_url:
            continue
        candidate_urls.append(absolute_url)
        link_text = " ".join(link.get_text(" ", strip=True).split())
        lowered = f"{link_text} {absolute_url}".lower()
        if any(token in lowered for token in ["menu", "menü", "menue", "speisekarte", "karte"]):
            candidate_urls.append(absolute_url)
        if any(token in lowered for token in ["reserv", "booking", "book", "table", "opentable", "quandoo"]):
            candidate_urls.append(absolute_url)

    merged = dict(business)
    merged["website"] = resolved_website
    candidate_menu_url = _pick_candidate_url(
        candidate_urls,
        preferred_tokens=["speisekarte", "menu", "menue", "karte"],
    )
    if _is_more_specific_url(candidate_menu_url, merged.get("menu_url")):
        merged["menu_url"] = candidate_menu_url
    candidate_reservation_url = _pick_candidate_url(
        candidate_urls,
        preferred_tokens=["reserv", "booking", "book", "table", "opentable", "quandoo"],
    )
    if _is_more_specific_url(candidate_reservation_url, merged.get("reservation_url")):
        merged["reservation_url"] = candidate_reservation_url
    if not str(merged.get("phone") or "").strip():
        merged["phone"] = _extract_phone_from_text(page_text)
    if not str(merged.get("email") or "").strip():
        merged["email"] = _extract_first_match(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", page_text)
    if not str(merged.get("opening_hours") or "").strip():
        merged["opening_hours"] = _extract_opening_hours_from_text(page_text)
    contact_parts = [part for part in [merged.get("phone"), merged.get("email"), merged.get("website")] if str(part or "").strip()]
    merged["contact"] = " | ".join(str(part).strip() for part in contact_parts) if contact_parts else None
    logger.info(
        "LOCAL-BUSINESS-WEBSITE: website='%s' resolved='%s' menu=%s reservation=%s phone=%s email=%s hours=%s",
        website,
        resolved_website,
        bool(str(merged.get("menu_url") or "").strip()),
        bool(str(merged.get("reservation_url") or "").strip()),
        bool(str(merged.get("phone") or "").strip()),
        bool(str(merged.get("email") or "").strip()),
        bool(str(merged.get("opening_hours") or "").strip()),
    )
    return merged


def _needs_business_enrichment(business: Dict[str, Any]) -> bool:
    if not isinstance(business, dict):
        return False
    return not all(
        str(business.get(field) or "").strip()
        for field in ("opening_hours", "menu_url", "reservation_url")
    )


def _parse_partial_business_fields(text: str) -> Dict[str, Optional[str]]:
    parsed: Dict[str, Optional[str]] = {
        "opening_hours": None,
        "menu_url": None,
        "reservation_url": None,
    }
    known_labels = {
        "öffnungszeiten": "opening_hours",
        "oeffnungszeiten": "opening_hours",
        "opening hours": "opening_hours",
        "hours": "opening_hours",
        "speisekarte": "menu_url",
        "menu": "menu_url",
        "menü": "menu_url",
        "reservierung": "reservation_url",
        "reservierungslink": "reservation_url",
        "reservation": "reservation_url",
        "booking": "reservation_url",
    }
    for raw_line in str(text or "").splitlines():
        stripped = raw_line.strip().lstrip("-*•1234567890. ").strip()
        if not stripped or ":" not in stripped:
            continue
        label, value = stripped.split(":", 1)
        key = known_labels.get(label.strip().lower())
        if not key:
            continue
        cleaned = _clean_business_field(value)
        if cleaned:
            parsed[key] = cleaned
    return parsed


def _should_count_business_enrichment_attempt(original: Dict[str, Any], enriched: Dict[str, Any]) -> bool:
    if not isinstance(original, dict) or not isinstance(enriched, dict):
        return True
    original_score = _business_quality_score(original)
    enriched_score = _business_quality_score(enriched)
    if enriched_score > original_score:
        return True
    original_website = _sanitize_business_website(original.get("website"))
    enriched_website = _sanitize_business_website(enriched.get("website"))
    if original_website and not enriched_website:
        return False
    if enriched_score == original_score and enriched != original:
        return True
    return enriched_score >= original_score


async def _enrich_business_entry(
    business: Dict[str, Any],
    *,
    query: str,
    location: str,
    provider: str,
    model: str,
    api_key: str,
) -> Dict[str, Any]:
    if not _needs_business_enrichment(business):
        return business

    merged_business = _enrich_business_from_website(business)
    if not _needs_business_enrichment(merged_business):
        return merged_business
    if provider == "ollama" and str(merged_business.get("source") or "").strip() == "osm_overpass_fallback":
        return merged_business

    business_name = str(merged_business.get("name") or "").strip()
    website = str(merged_business.get("website") or "").strip()
    domain_hint = _extract_domain_hint(website)
    target_query_parts = [business_name, location, "Öffnungszeiten", "Speisekarte", "Reservierung"]
    if domain_hint:
        target_query_parts.append(domain_hint)
    enrichment_query = " ".join(part for part in target_query_parts if part)

    try:
        enrichment_search = await execute_websearch_service(
            query=enrichment_query,
            api_key=api_key,
            provider=provider,
            model=model,
        )
    except Exception as exc:
        logger.warning("LOCAL-BUSINESS ENRICH: Websuche fehlgeschlagen für '%s': %s", business_name, exc)
        return merged_business

    if not isinstance(enrichment_search, dict):
        return merged_business

    enrichment_text = str(enrichment_search.get("text", "") or "").strip()
    enrichment_urls = _extract_candidate_urls(enrichment_search)
    if not enrichment_text and not enrichment_urls:
        return merged_business

    excerpt = enrichment_text[:4000]
    enrichment_prompt = f"""
    Analysiere die folgenden Suchergebnisse für den lokalen Eintrag "{business_name}" in "{location}".

    Gib GENAU diese Felder zurück:
    Öffnungszeiten: <kompakt oder 'Nicht gefunden'>
    Speisekarte: <direkter Menü-Link oder 'Nicht gefunden'>
    Reservierung: <direkter Reservierungs-/Booking-Link oder 'Nicht gefunden'>

    REGELN:
    - Nutze bevorzugt die offizielle Domain {domain_hint or 'des Ladens'}.
    - Wenn ein klarer direkter Link erkennbar ist, gib genau diesen Link aus.
    - Wenn nichts belastbar ist, schreibe 'Nicht gefunden'.
    - Keine zusätzlichen Felder, keine Einleitung, keine Nachbemerkung.

    SUCHERGEBNISSE:
    {excerpt}
    """

    try:
        llm_result = await llm_gateway.call_llm(
            provider=provider,
            model_id=model,
            api_key=api_key,
            messages=[{"role": "user", "content": enrichment_prompt}],
            tools=None,
            force_no_tools=True,
        )
    except Exception as exc:
        logger.warning("LOCAL-BUSINESS ENRICH: LLM-Extraktion fehlgeschlagen für '%s': %s", business_name, exc)
        return merged_business

    enriched_fields = _parse_partial_business_fields(str(llm_result.get("text", "") or "").strip())
    if not any(str(enriched_fields.get(field) or "").strip() for field in ("opening_hours", "menu_url", "reservation_url")):
        return merged_business

    merged = dict(merged_business)
    for field in ("opening_hours", "menu_url", "reservation_url"):
        if not str(merged.get(field) or "").strip() and str(enriched_fields.get(field) or "").strip():
            merged[field] = enriched_fields.get(field)
    candidate_menu_url = _pick_candidate_url(
        enrichment_urls,
        preferred_tokens=["speisekarte", "menu", "menue", "karte"],
    )
    if _is_more_specific_url(candidate_menu_url, merged.get("menu_url")):
        merged["menu_url"] = candidate_menu_url
    candidate_reservation_url = _pick_candidate_url(
        enrichment_urls,
        preferred_tokens=["reserv", "booking", "book", "table", "opentable", "quandoo"],
    )
    if _is_more_specific_url(candidate_reservation_url, merged.get("reservation_url")):
        merged["reservation_url"] = candidate_reservation_url
    contact_parts = [part for part in [merged.get("phone"), merged.get("email"), merged.get("website")] if str(part or "").strip()]
    merged["contact"] = " | ".join(str(part).strip() for part in contact_parts) if contact_parts else None
    return merged


async def _selectively_enrich_businesses(
    businesses: List[Dict[str, Any]],
    *,
    query: str,
    location: str,
    provider: str,
    model: str,
    api_key: str,
    max_enriched_items: int = 3,
) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = [business for business in businesses]
    enrichment_candidates: List[tuple[int, Dict[str, Any], int]] = []

    for index, business in enumerate(businesses):
        business_name = str(business.get("name") or "").strip()
        needs_enrichment = _needs_business_enrichment(business)
        if len(enrichment_candidates) < max_enriched_items and needs_enrichment:
            slot = len(enrichment_candidates) + 1
            logger.info(
                "LOCAL-BUSINESS-ENRICHMENT-ITEM: name=%r source=%r website=%r needs_enrichment=%s slot=%s/%s",
                business_name,
                str(business.get("source") or "").strip(),
                str(business.get("website") or "").strip(),
                needs_enrichment,
                slot,
                max_enriched_items,
            )
            enrichment_candidates.append((index, business, slot))
        else:
            logger.info(
                "LOCAL-BUSINESS-ENRICHMENT-SKIP: name=%r source=%r website=%r needs_enrichment=%s reason=%s",
                business_name,
                str(business.get("source") or "").strip(),
                str(business.get("website") or "").strip(),
                needs_enrichment,
                "limit_reached" if needs_enrichment else "already_complete",
            )

    async def _run_enrichment(candidate_index: int, business: Dict[str, Any], slot: int) -> tuple[int, Dict[str, Any]]:
        business_name = str(business.get("name") or "").strip()
        current = await _enrich_business_entry(
            business,
            query=query,
            location=location,
            provider=provider,
            model=model,
            api_key=api_key,
        )
        if not _should_count_business_enrichment_attempt(business, current):
            logger.info(
                "LOCAL-BUSINESS-ENRICHMENT-RETRY-SLOT: name=%r source=%r reason=%s slot=%s/%s",
                business_name,
                str(business.get("source") or "").strip(),
                "quality_regressed_or_blocked_target",
                slot,
                max_enriched_items,
            )
        return candidate_index, current

    if enrichment_candidates:
        enrichment_tasks = [
            _run_enrichment(index, business, slot)
            for index, business, slot in enrichment_candidates
        ]
        enrichment_results = await asyncio.gather(*enrichment_tasks)
        for index, current in enrichment_results:
            enriched[index] = current

    return enriched


def _prioritize_local_business_results(
    businesses: List[Dict[str, Any]],
    *,
    prefer_complete: bool,
) -> List[Dict[str, Any]]:
    if not prefer_complete:
        return businesses
    return sorted(
        businesses,
        key=lambda item: _business_quality_score(item),
        reverse=True,
    )


def _finalize_local_business_results(
    businesses: List[Dict[str, Any]],
    *,
    limit: int,
    provider: str,
    uses_duckduckgo_fallback: bool,
) -> List[Dict[str, Any]]:
    normalized = [item for item in businesses if isinstance(item, dict)]
    if not normalized:
        return []
    ranked = _prioritize_local_business_results(
        normalized,
        prefer_complete=provider == "ollama" and uses_duckduckgo_fallback,
    )
    if provider == "ollama" and uses_duckduckgo_fallback:
        strong = [
            item for item in ranked
            if _sanitize_business_website(item.get("website"))
            or str(item.get("menu_url") or "").strip()
            or str(item.get("reservation_url") or "").strip()
            or (
                str(item.get("opening_hours") or "").strip()
                and str(item.get("phone") or "").strip()
            )
        ]
        weak = [item for item in ranked if item not in strong]
        if len(strong) >= min(limit, 2):
            ranked = strong
        else:
            ranked = strong + weak
    return ranked[:limit]


def _build_business_entry(fields: Dict[str, Optional[str]], urls: List[str], query: str, location: str) -> Optional[Dict[str, Any]]:
    name = _clean_business_field(fields.get("name"))
    if not name:
        return None
    website = _clean_business_field(fields.get("website")) or _pick_candidate_url(urls)
    menu_url = _clean_business_field(fields.get("menu_url")) or _pick_candidate_url(
        urls,
        preferred_tokens=["speisekarte", "menu", "menue", "karte"],
    )
    reservation_url = _clean_business_field(fields.get("reservation_url")) or _pick_candidate_url(
        urls,
        preferred_tokens=["reserv", "booking", "book", "table", "opentable", "quandoo"],
    )
    phone = _clean_business_field(fields.get("phone"))
    email = _clean_business_field(fields.get("email"))
    contact_parts = [part for part in [phone, email, website] if part]
    return {
        "name": name[:160],
        "description": _clean_business_field(fields.get("description")),
        "category": _clean_business_field(fields.get("category")),
        "address": _clean_business_field(fields.get("address")) or "Adresse nicht gefunden",
        "opening_hours": _clean_business_field(fields.get("opening_hours")),
        "phone": phone,
        "email": email,
        "website": website,
        "contact": " | ".join(contact_parts) if contact_parts else None,
        "menu_url": menu_url,
        "reservation_url": reservation_url,
        "source": "websearch_summary",
        "query": query,
        "location": location,
    }


def _looks_like_no_business_results_text(text: str) -> bool:
    normalized = " ".join(str(text or "").strip().lower().split())
    if not normalized:
        return True
    markers = [
        "es wurden keine prägnanten suchergebnisse gefunden",
        "es wurden keine pragnanten suchergebnisse gefunden",
        "keine prägnanten suchergebnisse gefunden",
        "keine pragnanten suchergebnisse gefunden",
        "keine treffer gefunden",
        "keine passenden einträge gefunden",
        "keine passenden eintraege gefunden",
        "keine passenden restaurants gefunden",
        "keine geeigneten suchergebnisse gefunden",
        "ohne belastbare treffer",
        "ohne verlässliche treffer",
        "bitte versuche eine andere suche",
    ]
    return any(marker in normalized for marker in markers)


def _looks_like_ddg_failure_text(text: str) -> bool:
    normalized = " ".join(str(text or "").strip().lower().split())
    if not normalized:
        return False
    markers = [
        "fehler bei der duckduckgo-suche",
        "duckduckgo search failed",
        "connection aborted",
        "connection reseterror",
        "remotehost geschlossen",
        "remote host closed",
        "protocolerror",
        "requests.exceptions.connectionerror",
    ]
    return any(marker in normalized for marker in markers)


def _normalize_business_results(text: str, urls: List[str], query: str, location: str) -> List[Dict[str, Any]]:
    if _looks_like_no_business_results_text(text):
        return []
    normalized: List[Dict[str, Any]] = []
    current: Dict[str, Optional[str]] = {}
    known_labels = {
        "name": "name",
        "beschreibung": "description",
        "description": "description",
        "bekannt für": "description",
        "bekannt fuer": "description",
        "kategorie": "category",
        "category": "category",
        "adresse": "address",
        "address": "address",
        "öffnungszeiten": "opening_hours",
        "oeffnungszeiten": "opening_hours",
        "opening hours": "opening_hours",
        "hours": "opening_hours",
        "kontakt": "contact",
        "telefon": "phone",
        "phone": "phone",
        "e-mail": "email",
        "email": "email",
        "website": "website",
        "webseite": "website",
        "speisekarte": "menu_url",
        "menu": "menu_url",
        "menü": "menu_url",
        "reservierung": "reservation_url",
        "reservierungslink": "reservation_url",
        "reservation": "reservation_url",
        "booking": "reservation_url",
    }
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line:
            business = _build_business_entry(current, urls, query, location)
            if business and _is_viable_business_entry(business):
                normalized.append(business)
            current = {}
            continue
        stripped = line.lstrip("-*•1234567890. ").strip()
        if not stripped:
            continue
        is_bullet_like = line.startswith(("-", "*", "•"))
        if ":" in stripped:
            label, value = stripped.split(":", 1)
            key = known_labels.get(label.strip().lower())
            if key:
                current[key] = value.strip()
                continue
        if is_bullet_like and current.get("name"):
            business = _build_business_entry(current, urls, query, location)
            if business and _is_viable_business_entry(business):
                normalized.append(business)
            current = {}
        if not current.get("name"):
            current["name"] = stripped
        else:
            extra = current.get("contact") or ""
            current["contact"] = f"{extra} | {stripped}".strip(" |")
    business = _build_business_entry(current, urls, query, location)
    if business and _is_viable_business_entry(business):
        normalized.append(business)
    if normalized:
        return normalized
    fallback_url = urls[0] if urls else None
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip().lstrip("-*•1234567890. ").strip()
        if not line:
            continue
        fallback_business = {
            "name": line[:160],
            "description": None,
            "category": None,
            "address": "Adresse nicht gefunden",
            "opening_hours": None,
            "phone": None,
            "email": None,
            "website": fallback_url,
            "contact": fallback_url,
            "menu_url": None,
            "reservation_url": None,
            "source": "websearch_summary",
            "query": query,
            "location": location,
        }
        if _is_viable_business_entry(fallback_business):
            normalized.append(fallback_business)
    return normalized


def _country_ok(started_at: float, data: Dict[str, object]) -> ToolResultV1:
    return ToolResultV1(
        status="ok",
        data={k: v for k, v in data.items()},
        metadata=_tool_v1_metadata(
            started_at,
            _geo_suggestion_meta(relevance_tags=["geo", "country", "reference"]),
        ),
    )


def _local_business_ok_result(
    started_at: float,
    data: Dict[str, Any],
    *,
    message: Optional[str] = None,
) -> ToolResultV1:
    businesses = data.get("businesses")
    n = len(businesses) if isinstance(businesses, list) else 0
    relevance_tags = ["local_business", "poi"] if n > 0 else ["local_business", "search"]
    primary: Optional[str] = None
    if n and isinstance(businesses[0], dict):
        primary = str(businesses[0].get("name") or "").strip() or None
    return ToolResultV1(
        status="ok",
        data=data,
        message=message,
        metadata=_tool_v1_metadata(
            started_at,
            _geo_suggestion_meta(
                relevance_tags=relevance_tags,
                suggest_follow_up=True,
                primary_entity_name=primary,
            ),
        ),
    )


async def _geocode_city_center(geolocator: Nominatim, query: str):
    """Versucht die Stadtmitte anhand der Adresse zu bestimmen."""
    if not query:
        return None

    def _sync_geocode(text: str, with_address: bool):
        return geolocator.geocode(text, exactly_one=True, timeout=20, addressdetails=with_address)

    location = await asyncio.to_thread(_sync_geocode, query, True)
    if not location:
        return None

    address = location.raw.get("address", {}) if isinstance(location.raw, dict) else {}
    city_candidates = [address.get(key) for key in ("city", "town", "village", "municipality", "county")]
    city = next((candidate for candidate in city_candidates if candidate), None)
    state = address.get("state")
    country = address.get("country")

    if city and country:
        canonical_parts = [city]
        if state and state.lower() != city.lower():
            canonical_parts.append(state)
        canonical_parts.append(country)
        canonical_query = ", ".join(canonical_parts)
        canonical_location = await asyncio.to_thread(_sync_geocode, canonical_query, False)
        if canonical_location:
            return canonical_location

    return location


# --- Tools ---


async def get_distance_and_route_tool(
    origin: str, destination: str, mode: str = "driving", **kwargs
) -> ToolResultV1:
    """Berechnet Distanz und Fahrzeit zwischen zwei Orten mittels OSRM. Benötigt keinen API Key."""
    trace_id = kwargs.pop("trace_id", None)
    trace_tag = f"[trace_id={trace_id}]" if trace_id else ""
    started_at = time.perf_counter()

    def _error_response(code: str, message: str) -> ToolResultV1:
        logger.error(f"{trace_tag} {message}")
        return ToolResultV1(
            status="error",
            data={},
            error=ToolErrorDetails(code=code, message=message),
            metadata=_tool_v1_metadata(
                started_at,
                _geo_suggestion_meta(relevance_tags=["geo", "routing"], suggest_follow_up=False),
            ),
        )

    normalized_mode = str(mode or "driving").strip().lower()
    if normalized_mode not in _SUPPORTED_ROUTING_MODES:
        return _error_response(
            "INVALID_MODE",
            "Ungültiger Routing-Modus. Erlaubt sind: driving, walking, cycling.",
        )

    geolocator = Nominatim(user_agent="janus_geo_tool", timeout=20)

    try:
        # 1. Geocoding: Koordinaten finden
        logger.info(f"{trace_tag} Geocoding für Route: {origin} -> {destination}")
        # Nutzung von asyncio.to_thread, um den Main-Loop nicht zu blockieren
        loc_origin = await _geocode_city_center(geolocator, origin)
        loc_dest = await _geocode_city_center(geolocator, destination)

        if not loc_origin or not loc_dest:
            return _error_response(
                "INVALID_COORDINATES",
                f"Konnte einen der Orte nicht finden: '{origin}' oder '{destination}'. Bitte präzisiere die Eingabe.",
            )

        # 2. OSRM API Anfrage (Kostenlos)
        # WICHTIG: OSRM erwartet Format {longitude},{latitude}
        osrm_url = (
            "http://router.project-osrm.org/route/v1/"
            f"{normalized_mode}/{loc_origin.longitude},{loc_origin.latitude};"
            f"{loc_dest.longitude},{loc_dest.latitude}?overview=false"
        )

        response = await asyncio.to_thread(requests.get, osrm_url, timeout=30)

        if response.status_code != 200:
            return _error_response(
                "ROUTING_UNAVAILABLE",
                "Fehler bei der Routenberechnung (OSRM API nicht erreichbar).",
            )

        data = response.json()

        if "routes" not in data or not data["routes"]:
            return _error_response(
                "NO_ROUTE",
                "Keine Route zwischen diesen Orten gefunden.",
            )

        route = data["routes"][0]
        # OSRM gibt Meter zurück -> in km umrechnen
        distance_km = round(route["distance"] / 1000, 1)
        duration_str = _format_duration(route["duration"])

        params = {
            "api": "1",
            "origin": origin,
            "destination": destination,
            "travelmode": _GOOGLE_MAPS_TRAVEL_MODE.get(normalized_mode, "driving"),
        }
        maps_link = f"https://www.google.com/maps/dir/?{urlencode(params)}"

        if "goo.gl" in maps_link:
            maps_link = maps_link.replace("goo.gl", "google.com/maps")

        logger.info(
            f"{trace_tag} Routing result: {distance_km}km in {duration_str}, link={maps_link}"
        )

        return ToolResultV1(
            status="ok",
            data={
                "origin": origin,
                "destination": destination,
                "distance_km": distance_km,
                "duration": duration_str,
                "maps_link": maps_link,
            },
            message=f"{distance_km} km, ca. {duration_str}",
            metadata=_tool_v1_metadata(
                started_at,
                _geo_suggestion_meta(relevance_tags=["geo", "routing", "navigation"]),
            ),
        )

    except Exception as e:
        logger.error(f"{trace_tag} Fehler im Geo-Tool: {e}", exc_info=True)
        return _error_response(
            "ROUTING_UNAVAILABLE",
            (
                "Die Routing-/Geodatenquelle konnte nicht verlaesslich abgerufen werden. "
                "Ich gebe deshalb keine praezise Entfernung oder Route aus."
            ),
        )


async def find_local_business_tool(
    query: str,
    location: str,
    limit: int = 5,
    api_key: str = "",
    provider: str = "openai",
    model: Optional[str] = None,
    **kwargs,
) -> ToolResultV1:
    """
    Sucht nach lokalen Orten, Geschäften oder Dienstleistern.

    Die Suchergebnisse werden an das LLM übergeben, welches eine strukturierte Liste der besten Treffer erzeugt.
    Der gesamte Text wird an die LLM-Pipeline weitergereicht (ohne Tools), daher muss das Modell für die Auswertung selbst verfügbar sein.
    """
    started_at = time.perf_counter()
    normalized_query = str(query or "").strip()
    normalized_location = str(location or "").strip()
    try:
        normalized_limit = int(limit or 5)
    except (ValueError, TypeError):
        return _local_business_error(
            started_at,
            "INVALID_LIMIT",
            "Der Parameter 'limit' muss eine ganze Zahl zwischen 1 und 10 sein.",
            query=normalized_query,
            location=normalized_location,
            details={"limit": limit},
        )

    if not normalized_query:
        return _local_business_error(
            started_at,
            "INVALID_QUERY",
            "Der Parameter 'query' darf nicht leer sein.",
            query=normalized_query,
            location=normalized_location,
        )
    if not normalized_location:
        return _local_business_error(
            started_at,
            "INVALID_LOCATION",
            "Der Parameter 'location' darf nicht leer sein.",
            query=normalized_query,
            location=normalized_location,
        )
    if normalized_limit < 1 or normalized_limit > 10:
        return _local_business_error(
            started_at,
            "INVALID_LIMIT",
            "Der Parameter 'limit' muss zwischen 1 und 10 liegen.",
            query=normalized_query,
            location=normalized_location,
            details={"limit": normalized_limit},
        )

    _FIND_LOCAL_BUSINESS_MAX_SEC = 25.0

    async def _local_business_body() -> ToolResultV1:
        try:
            loc_str = normalized_location

            # OPTIMIERUNG: Suchanfrage auf Daten fokussieren
            search_query = _build_local_business_search_query(normalized_query, loc_str, provider)

            logger.info(f"Lokal-Suche gestartet: '{search_query}'")

            search_results = await execute_websearch_service(
                query=search_query, api_key=api_key, provider=provider, model=model
            )

            if not isinstance(search_results, dict):
                return _local_business_error(
                    started_at,
                    "LOCAL_SEARCH_FAILED",
                    "Die lokale Suche lieferte ein ungültiges Antwortformat.",
                    query=normalized_query,
                    location=normalized_location,
                )

            raw_text = str(search_results.get("text", "") or "").strip()
            candidate_urls = _extract_candidate_urls(search_results)
            search_source = str(search_results.get("source") or "").strip().lower()
            uses_duckduckgo_fallback = provider == "ollama" and search_source == "duckduckgo"
            ddg_result_is_empty_or_useless = uses_duckduckgo_fallback and not raw_text and not candidate_urls
            if uses_duckduckgo_fallback:
                logger.info(
                    "LOCAL-BUSINESS-DDG-INPUT: query='%s' location='%s' text_chars=%s urls=%s preview=%r",
                    normalized_query,
                    normalized_location,
                    len(raw_text),
                    len(candidate_urls),
                    raw_text[:240],
                )
            if not raw_text and not uses_duckduckgo_fallback:
                msg = f"Keine Treffer für '{normalized_query}' in '{normalized_location}' gefunden."
                return _local_business_ok_result(
                    started_at,
                    {
                        "businesses": [],
                        "query": normalized_query,
                        "location": normalized_location,
                        "result_count": 0,
                        "provider": provider,
                        "model": model,
                        "search_query": search_query,
                        "message": msg,
                    },
                    message=msg,
                )

            # Document provider behavior
            if provider == "ollama":
                slice_limit = 2500
            else:
                slice_limit = 7000

            raw_excerpt = raw_text[:slice_limit]

            # OPTIMIERUNG: Strengerer Prompt gegen Google Maps Links
            # WICHTIG: Bei limit=1 explizit nur 1 Ergebnis anfordern!
            result_count = max(1, min(normalized_limit, 10))
            single_result_instruction = "\nABSOLUT WICHTIG: Du musst GENAU EINEN (1) Eintrag zurückgeben. Keinen zweiten. Keine Alternative. Nur der beste Treffer." if result_count == 1 else f"\nErstelle GENAU {result_count} Einträge, wenn genügend Treffer vorhanden sind."

            extraction_prompt = f"""
            Du bist ein Daten-Analyst für lokale Suchergebnisse.

            Analysiere die Suchergebnisse für "{normalized_query}" in "{loc_str}".{single_result_instruction}

            AUSGABEFORMAT PRO EINTRAG:
            Name: <Name>
            Beschreibung: <1 kurzer Satz, wofür der Laden bekannt ist>
            Kategorie: <eine kurze Einordnung wie Budget, Fine Dining, Geheimtipp, Veggi, Familienfreundlich, Modern, Klassisch>
            Adresse: <Straße Hausnummer, soweit auffindbar>
            Öffnungszeiten: <kurz und kompakt, z. B. Mo-So 12:00-22:00 oder 'Nicht gefunden'>
            Telefon: <Telefon oder 'Nicht gefunden'>
            E-Mail: <E-Mail oder 'Nicht gefunden'>
            Website: <offizielle Website oder 'Nicht gefunden'>
            Speisekarte: <direkter Menü-/Speisekarten-Link oder 'Nicht gefunden'>
            Reservierung: <direkter Reservierungs-/Booking-Link oder 'Nicht gefunden'>

            REGELN:
            - Gib nur die besten realistischen Treffer zurück.
            - Nutze bevorzugt die offizielle Website.
            - Priorisiere Quellen, auf denen Öffnungszeiten, Speisekarte oder Reservierung direkt erkennbar sind.
            - Beschreibung maximal ein kurzer Satz.
            - Kategorie knapp und nutzerorientiert.
            - Öffnungszeiten möglichst kompakt zusammenfassen.
            - Speisekarte und Reservierung nur dann als 'Nicht gefunden' markieren, wenn wirklich kein direkter Link erkennbar ist.
            - Wenn eine Restaurantseite einen klaren Menü-/Reservierungslink enthält, gib genau diesen direkten Link aus, nicht nur die Startseite.
            - Keine Fließtext-Erklärung, keine Einleitung, keine Nachbemerkung.
            - Zwischen zwei Einträgen genau eine Leerzeile.

            SUCHERGEBNISSE:
            {raw_excerpt}
            """

            extracted_info = ""
            if uses_duckduckgo_fallback:
                logger.info(
                    "LOCAL-BUSINESS: DDG-Fallback fuer Ollama erkannt, ueberspringe freie Extraktion und nutze deterministische Auswertung. query='%s' location='%s'",
                    normalized_query,
                    normalized_location,
                )
            else:
                try:
                    response = await llm_gateway.call_llm(
                        provider=provider,
                        model_id=model,
                        api_key=api_key,
                        messages=[{"role": "user", "content": extraction_prompt}],
                        tools=None,
                        force_no_tools=True,
                    )
                    extracted_info = str(response.get("text", "") or "").strip()
                except Exception as exc:
                    if provider == "ollama":
                        logger.warning(
                            "LOCAL-BUSINESS: Ollama-Extraktion fehlgeschlagen, nutze URL-Fallback. query='%s' location='%s' error=%s",
                            normalized_query,
                            normalized_location,
                            exc,
                        )
                    else:
                        raise

            businesses = _normalize_business_results(extracted_info, candidate_urls, normalized_query, normalized_location)
            if uses_duckduckgo_fallback:
                logger.info(
                    "LOCAL-BUSINESS-DDG-NORMALIZED: extracted_chars=%s businesses=%s",
                    len(extracted_info),
                    len(businesses),
                )
            if not businesses and provider == "ollama":
                businesses = _fallback_businesses_from_candidates(
                    candidate_urls,
                    normalized_query,
                    normalized_location,
                    normalized_limit,
                )
                if uses_duckduckgo_fallback:
                    logger.info(
                        "LOCAL-BUSINESS-DDG-URL-FALLBACK: businesses=%s urls=%s",
                        len(businesses),
                        len(candidate_urls),
                    )
            if not businesses and provider == "ollama":
                businesses = _fallback_businesses_from_text(
                    raw_text,
                    candidate_urls,
                    normalized_query,
                    normalized_location,
                    normalized_limit,
                )
                if uses_duckduckgo_fallback:
                    logger.info(
                        "LOCAL-BUSINESS-DDG-SNIPPET-FALLBACK: businesses=%s text_chars=%s",
                        len(businesses),
                        len(raw_text),
                    )
            should_try_osm_fallback = uses_duckduckgo_fallback and (
                ddg_result_is_empty_or_useless
                or not raw_text
                or "keine prägnanten ergebnisse" in raw_text.casefold()
                or "keine pragnanten ergebnisse" in raw_text.casefold()
                or _looks_like_ddg_failure_text(raw_text)
            )
            if not businesses and should_try_osm_fallback:
                _elapsed_tool = time.perf_counter() - started_at
                _remaining_tool = _FIND_LOCAL_BUSINESS_MAX_SEC - _elapsed_tool
                if _remaining_tool <= _LOCAL_BUSINESS_WEB_TAIL_RESERVE_SEC:
                    logger.info(
                        "LOCAL-BUSINESS: OSM übersprungen — nur %.1fs bis globalem Limit "
                        "(≥%.0fs für Web-/Nachbearbeitung reserviert)",
                        _remaining_tool,
                        _LOCAL_BUSINESS_WEB_TAIL_RESERVE_SEC,
                    )
                else:
                    _osm_budget = min(
                        _OVERPASS_TOTAL_BUDGET_SEC,
                        _remaining_tool - _LOCAL_BUSINESS_WEB_TAIL_RESERVE_SEC,
                    )
                    if _osm_budget < 0.5:
                        logger.info(
                            "LOCAL-BUSINESS: OSM übersprungen — effektives OSM-Budget %.2fs",
                            _osm_budget,
                        )
                    else:
                        businesses = _fallback_businesses_from_osm(
                            normalized_query,
                            normalized_location,
                            normalized_limit,
                            osm_phase_deadline=time.perf_counter() + _osm_budget,
                        )
                        logger.info(
                            "LOCAL-BUSINESS-DDG-OSM-FALLBACK: businesses=%s osm_budget_sec=%.2f remaining_after_start=%.1fs",
                            len(businesses),
                            _osm_budget,
                            _remaining_tool,
                        )
            if provider == "ollama" and uses_duckduckgo_fallback and businesses:
                _now_disc = time.perf_counter()
                _discovery_deadline = min(
                    _now_disc + _LOCAL_BUSINESS_DISCOVER_WALL_CAP_SEC,
                    started_at + _FIND_LOCAL_BUSINESS_MAX_SEC - _LOCAL_BUSINESS_WEB_TAIL_RESERVE_SEC,
                )
                businesses = await _discover_missing_business_websites(
                    businesses,
                    query=normalized_query,
                    location=normalized_location,
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    max_discoveries=min(normalized_limit, 4),
                    deadline=_discovery_deadline,
                )
            businesses = _prioritize_local_business_results(
                businesses,
                prefer_complete=provider == "ollama" and uses_duckduckgo_fallback,
            )
            osm_businesses = [item for item in businesses if isinstance(item, dict) and str(item.get("source") or "").strip() == "osm_overpass_fallback"]
            enrichable_businesses = [item for item in businesses if isinstance(item, dict) and _needs_business_enrichment(item)]
            website_ready_businesses = [
                item
                for item in businesses
                if isinstance(item, dict) and _sanitize_business_website(item.get("website"))
            ]
            should_enrich_businesses = bool(businesses) and (
                not uses_duckduckgo_fallback
                or any(str(item.get("source") or "").strip() == "osm_overpass_fallback" for item in businesses if isinstance(item, dict))
            )
            logger.info(
                "LOCAL-BUSINESS-ENRICHMENT-GATE: provider=%s uses_ddg_fallback=%s businesses=%s osm_businesses=%s enrichable=%s website_ready=%s should_enrich=%s",
                provider,
                uses_duckduckgo_fallback,
                len(businesses),
                len(osm_businesses),
                len(enrichable_businesses),
                len(website_ready_businesses),
                should_enrich_businesses,
            )
            if should_enrich_businesses:
                if provider == "ollama" and uses_duckduckgo_fallback and osm_businesses:
                    prioritized_businesses = sorted(
                        businesses,
                        key=lambda item: (
                            0 if (isinstance(item, dict) and _sanitize_business_website(item.get("website")) and _needs_business_enrichment(item)) else 1,
                            0 if (isinstance(item, dict) and _sanitize_business_website(item.get("website"))) else 1,
                        ),
                    )
                    if prioritized_businesses != businesses:
                        logger.info(
                            "LOCAL-BUSINESS-ENRICHMENT-PRIORITIZED: first_before=%r first_after=%r",
                            str((businesses[0] or {}).get("name") if businesses and isinstance(businesses[0], dict) else ""),
                            str((prioritized_businesses[0] or {}).get("name") if prioritized_businesses and isinstance(prioritized_businesses[0], dict) else ""),
                        )
                    businesses = prioritized_businesses
                max_enriched_items = 1 if provider == "ollama" else 3
                if provider == "ollama" and uses_duckduckgo_fallback and osm_businesses:
                    website_ready_count = sum(1 for item in businesses if isinstance(item, dict) and _sanitize_business_website(item.get("website")) and _needs_business_enrichment(item))
                    max_enriched_items = max(1, min(normalized_limit, website_ready_count, 4))
                logger.info(
                    "LOCAL-BUSINESS-ENRICHMENT-START: provider=%s max_items=%s businesses=%s",
                    provider,
                    max_enriched_items,
                    len(businesses),
                )
                businesses = await _selectively_enrich_businesses(
                    businesses,
                    query=normalized_query,
                    location=normalized_location,
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    max_enriched_items=max_enriched_items,
                )
                businesses = _finalize_local_business_results(
                    businesses,
                    limit=normalized_limit,
                    provider=provider,
                    uses_duckduckgo_fallback=uses_duckduckgo_fallback,
                )
                logger.info(
                    "LOCAL-BUSINESS-ENRICHMENT-DONE: businesses=%s enriched_candidates=%s",
                    len(businesses),
                    len(enrichable_businesses),
                )
            else:
                businesses = _finalize_local_business_results(
                    businesses,
                    limit=normalized_limit,
                    provider=provider,
                    uses_duckduckgo_fallback=uses_duckduckgo_fallback,
                )
                logger.info(
                    "LOCAL-BUSINESS-ENRICHMENT-SKIP-GATE: provider=%s uses_ddg_fallback=%s businesses=%s",
                    provider,
                    uses_duckduckgo_fallback,
                    len(businesses),
                )

            # FINAL SAFETY NET: Bei limit=1 wirklich nur 1 Ergebnis zurückgeben!
            if normalized_limit == 1 and len(businesses) > 1:
                logger.warning("[SAFETY-NET] limit=1 but %d businesses found! Truncating to 1.", len(businesses))
                businesses = businesses[:1]

            return _local_business_ok_result(
                started_at,
                {
                    "businesses": businesses,
                    "query": normalized_query,
                    "location": normalized_location,
                    "result_count": len(businesses),
                    "provider": provider,
                    "model": model,
                    "search_query": search_query,
                    "search_url": f"https://www.google.com/search?q={search_query.replace(' ', '+')}",
                    "summary": extracted_info,
                    "source_urls": candidate_urls[:normalized_limit],
                },
            )

        except Exception as e:
            logger.error(
                "Fehler in find_local_business_tool (_local_business_body): %s",
                e,
                exc_info=True,
            )
            return _local_business_error(
                started_at,
                "LOCAL_SEARCH_FAILED",
                "Die lokale Suche konnte nicht durchgeführt werden.",
                query=normalized_query,
                location=normalized_location,
                details={"error": str(e), "provider": provider, "model": model},
            )

    try:
        return await asyncio.wait_for(_local_business_body(), timeout=_FIND_LOCAL_BUSINESS_MAX_SEC)
    except asyncio.TimeoutError:
        logger.warning(
            "LOCAL-BUSINESS: Hard-Stop nach %.0fs (vor globalem Tool-Timeout)",
            _FIND_LOCAL_BUSINESS_MAX_SEC,
        )
        return _local_business_error(
            started_at,
            "LOCAL_BUSINESS_TIMEOUT",
            "Die lokale Suche dauerte zu lange und wurde abgebrochen. Bitte erneut versuchen oder die Suche eingrenzen.",
            query=normalized_query,
            location=normalized_location,
            details={"timeout_seconds": _FIND_LOCAL_BUSINESS_MAX_SEC},
        )
    except Exception as e:
        logger.exception(
            "LOCAL-BUSINESS: Unerwarteter Fehler außerhalb von _local_business_body (query=%r location=%r)",
            normalized_query,
            normalized_location,
        )
        return _local_business_error(
            started_at,
            "LOCAL_SEARCH_FAILED",
            f"Die lokale Suche ist fehlgeschlagen: {str(e)}",
            query=normalized_query,
            location=normalized_location,
            details={"error": str(e)},
        )


def get_country_info_tool(country: str, language: str = "de", **kwargs) -> ToolResultV1:
    started_at = time.perf_counter()
    try:
        normalized_country = str(country or "").strip()
        normalized_language = str(language or "de").strip().lower() or "de"

        if not normalized_country:
            return _country_error(
                started_at,
                "INVALID_INPUT",
                "Der Parameter 'country' darf nicht leer sein.",
            )

        fields = "name,translations,capital,population,region,currencies,languages"
        endpoints = [
            f"https://restcountries.com/v3.1/translation/{normalized_country}?fields={fields}",
            f"https://restcountries.com/v3.1/name/{normalized_country}?fields={fields}",
        ]

        response = None
        for endpoint in endpoints:
            candidate = requests.get(endpoint, timeout=8.0)
            if candidate.status_code == 404:
                continue
            response = candidate
            break

        if response is None or response.status_code == 404:
            return _country_error(
                started_at,
                "NOT_FOUND",
                f"Keine Daten für das Land '{normalized_country}' gefunden.",
            )

        if response.status_code >= 400:
            return _country_error(
                started_at,
                "API_ERROR",
                "Die Länder-Datenbank hat einen Fehler gemeldet.",
                f"HTTP {response.status_code}",
            )

        payload = response.json()
        if not isinstance(payload, list) or not payload:
            return _country_error(
                started_at,
                "PARSE_ERROR",
                "Die Länder-Daten konnten nicht gelesen werden.",
                "Unerwartetes API-Format.",
            )

        country_data = payload[0] if isinstance(payload[0], dict) else {}

        translations = country_data.get("translations") if isinstance(country_data.get("translations"), dict) else {}
        default_name = country_data.get("name", {}).get("common", normalized_country)
        if normalized_language.startswith("de"):
            localized_name = translations.get("deu", {}).get("common", default_name)
        elif normalized_language.startswith("en"):
            localized_name = default_name
        else:
            localized_name = default_name

        capital_raw = country_data.get("capital")
        capital = capital_raw[0] if isinstance(capital_raw, list) and capital_raw else "N/A"
        population = country_data.get("population", 0)
        region = country_data.get("region", "N/A")

        currencies_dict = country_data.get("currencies") if isinstance(country_data.get("currencies"), dict) else {}
        currencies = []
        for code, item in currencies_dict.items():
            if isinstance(item, dict):
                curr_name = item.get("name") or "Unbekannte Währung"
            else:
                curr_name = "Unbekannte Währung"
            currencies.append(f"{curr_name} ({code})")
        if not currencies:
            currencies = ["N/A"]

        languages_dict = country_data.get("languages") if isinstance(country_data.get("languages"), dict) else {}
        language_values = [str(value) for value in languages_dict.values() if value]
        if not language_values:
            language_values = ["N/A"]

        return _country_ok(
            started_at,
            {
                "name": localized_name,
                "capital": capital,
                "population": population,
                "region": region,
                "currencies": currencies,
                "languages": language_values,
            },
        )

    except requests.exceptions.RequestException as exc:
        return _country_error(
            started_at,
            "API_ERROR",
            "Die Länder-Datenbank ist derzeit nicht erreichbar.",
            str(exc),
        )
    except Exception as exc:
        logger.error("Unerwarteter Fehler in get_country_info_tool", exc_info=True)
        return _country_error(
            started_at,
            "UNEXPECTED_ERROR",
            "Die Länderdaten konnten nicht verarbeitet werden.",
            str(exc),
        )
