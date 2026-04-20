import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple


_LOCAL_BUSINESS_KEYWORDS = [
    "restaurants",
    "restaurant",
    "apotheke",
    "supermarkt",
    "baumarkt",
    "kino",
    "museum",
    "café",
    "cafe",
    "bar",
    "hotel",
    "arzt",
    "zahnarzt",
    "pizzeria",
    "bäckerei",
    "baeckerei",
    "laden",
    "geschäft",
    "geschaeft",
    "shop",
]

_GERMAN_MONTH_NAMES = {
    1: "Januar",
    2: "Februar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember",
}

_MONTH_NAME_PATTERN = (
    r"Januar|Februar|März|Maerz|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember|"
    r"January|February|March|April|May|June|July|August|September|October|November|December"
)

_RELATIVE_TOKEN_REGEX = {
    "month": r"\b(?:nächsten monat|naechsten monat|kommenden monat|next month|diesen monat|diesem monat|this month|current month)\b",
    "week": r"\b(?:nächste woche|naechste woche|kommende woche|next week)\b",
    "year": r"\b(?:dieses jahr|in diesem jahr|current year|this year)\b",
    "quarter": r"\b(?:nächstes quartal|naechstes quartal|kommendes quartal|kommenden quartal|next quarter)\b",
}

_WEBSEARCH_PRICE_MARKERS = (
    "preis",
    "preise",
    "straßenpreis",
    "straßenpreise",
    "strassenpreis",
    "strassenpreise",
    "straßenpreise",
    "gold",
    "goldpreis",
    "feinunze",
    "kosten",
    "kostet",
    "kurs",
    "kurse",
    "spotpreis",
    "wert",
    "price",
    "street price",
    "street prices",
    "cost",
)

_WEBSEARCH_TOP_LIST_MARKERS = (
    "top 3",
    "top3",
    "top drei",
    "highlight",
    "highlights",
    "beste",
    "besten",
    "beliebteste",
    "beliebtesten",
    "beliebte",
    "popular",
    "populär",
    "populaer",
    "ranking",
    "rangliste",
    "empfehl",
    "most anticipated",
)

_WEBSEARCH_SWITCH_2_LAUNCH_MARKERS = (
    "wann wurde die switch 2",
    "switch 2 veröffentlicht",
    "switch 2 veroeffentlicht",
    "switch 2 release",
    "switch 2 launch",
    "konsole veröffentlicht",
    "konsole veroeffentlicht",
)


def sanitize_tool_arguments(
    tool_name: str,
    tool_args: Dict[str, Any],
    *,
    provider: str,
    original_user_text: Optional[str] = None,
) -> Dict[str, Any]:
    normalized_tool_name = str(tool_name or "").strip().lower()
    sanitized = dict(tool_args or {})
    if not normalized_tool_name:
        return sanitized
    user_text = str(original_user_text or "").strip()
    if normalized_tool_name == "system.websearch" and user_text:
        return _sanitize_websearch_tool_args(sanitized, user_text=user_text)
    if str(provider or "").strip().lower() != "ollama":
        return sanitized
    if not user_text:
        return sanitized
    if normalized_tool_name == "system.local_business":
        return _sanitize_local_business_tool_args(sanitized, user_text=user_text)
    return sanitized


def _sanitize_websearch_tool_args(tool_args: Dict[str, Any], *, user_text: str) -> Dict[str, Any]:
    sanitized = dict(tool_args or {})
    current_query = str(sanitized.get("query") or "").strip()
    if not current_query:
        sanitized["query"] = user_text
        return sanitized
    if _should_restore_websearch_query_from_user_text(current_query, user_text):
        current_query = user_text
    time_reference = _resolve_relative_time_reference(user_text)
    if time_reference:
        current_query = _replace_query_time_reference(current_query, reference=time_reference)
    canonical_query = _canonicalize_websearch_query(current_query, user_text=user_text)
    if canonical_query:
        current_query = canonical_query
    sanitized["query"] = current_query
    return sanitized


def _should_restore_websearch_query_from_user_text(current_query: str, user_text: str) -> bool:
    normalized_user = str(user_text or "").strip()
    normalized_query = str(current_query or "").strip()
    if not normalized_user:
        return False
    if _resolve_relative_time_reference(normalized_user):
        return True
    lowered_user = normalized_user.lower()
    lowered_query = normalized_query.lower()
    if any(marker in lowered_user for marker in _WEBSEARCH_PRICE_MARKERS):
        return True
    if any(marker in lowered_user for marker in _WEBSEARCH_TOP_LIST_MARKERS) and not any(
        marker in lowered_query for marker in _WEBSEARCH_TOP_LIST_MARKERS
    ):
        return True
    if any(token in lowered_query for token in (" usd", " dollar", " troy ounce", "current ")) and not any(
        token in lowered_user for token in ("usd", "dollar", "troy ounce", "current")
    ):
        return True
    return False


def _canonicalize_websearch_query(query: str, *, user_text: str) -> str:
    normalized_query = re.sub(r"\s+", " ", str(query or "").strip())
    normalized_user = re.sub(r"\s+", " ", str(user_text or "").strip())
    if not normalized_query:
        return normalized_query
    lowered_user = normalized_user.lower()
    lowered_query = normalized_query.lower()
    if _is_switch_2_price_query(lowered_user) or _is_switch_2_price_query(lowered_query):
        return _build_switch_2_price_query(normalized_query, user_text=normalized_user)
    if _is_switch_2_game_release_query(lowered_user) or _is_switch_2_game_release_query(lowered_query):
        return _build_switch_2_release_query(normalized_query, user_text=normalized_user)
    return normalized_query


def _is_switch_2_price_query(text: str) -> bool:
    lowered = str(text or "").strip().lower()
    if not lowered:
        return False
    has_switch_2 = "switch 2" in lowered or "nintendo switch 2" in lowered
    has_price_intent = any(token in lowered for token in ("preis", "preise", "kosten", "kostet", "uvp", "price", "cost"))
    has_games_focus = any(token in lowered for token in ("spiele", "games", "game"))
    return has_switch_2 and has_price_intent and not has_games_focus


def _is_switch_2_game_release_query(text: str) -> bool:
    lowered = str(text or "").strip().lower()
    if not lowered:
        return False
    has_switch_2 = "switch 2" in lowered or "nintendo switch 2" in lowered
    has_games = any(token in lowered for token in ("spiele", "games", "game"))
    has_release = any(
        token in lowered
        for token in ("erscheinen", "erschein", "release", "launch", "upcoming", "kommende", "pipeline")
    )
    return has_switch_2 and has_games and has_release


def _build_switch_2_price_query(query: str, *, user_text: str) -> str:
    normalized_query = re.sub(r"\s+", " ", str(query or "").strip())
    lowered_user = str(user_text or "").strip().lower()
    parts = ["Nintendo Switch 2", "Preis"]
    if any(token in lowered_user for token in ("aktuell", "aktuelle", "heute", "derzeit", "current", "latest")):
        parts.append("aktuell")
    if any(token in lowered_user for token in ("deutschland", "germany", "deutsch")):
        parts.append("Deutschland")
    parts.append("Euro")
    if any(token in lowered_user for token in ("uvp", "offiziell", "offizielle", "msrp", "listenpreis")):
        parts.append("UVP")
    elif any(token in normalized_query.lower() for token in ("uvp", "msrp", "listenpreis")):
        parts.append("UVP")
    return " ".join(part for part in parts if part).strip()


def _build_switch_2_release_query(query: str, *, user_text: str) -> str:
    normalized_query = re.sub(r"\s+", " ", str(query or "").strip())
    lowered_user = str(user_text or "").strip().lower()
    lowered_query = normalized_query.lower()
    time_fragment = _extract_time_fragment_for_switch_2_release_query(normalized_query)
    parts = ["Nintendo Switch 2", "upcoming games", "release"]
    if time_fragment:
        parts.append(time_fragment)
    if any(token in lowered_user for token in ("deutschland", "germany", "deutsch")):
        parts.append("Deutschland")
    if any(token in lowered_user or token in lowered_query for token in ("preis", "preise", "kosten", "kostet", "uvp", "price", "cost")):
        parts.append("Preis")
    if any(token in lowered_user or token in lowered_query for token in ("uvp", "msrp", "listenpreis", "offiziell", "offizielle")):
        parts.append("UVP")
    if any(token in lowered_user or token in lowered_query for token in ("straßenpreis", "straßenpreise", "strassenpreis", "strassenpreise", "street price", "street prices")):
        parts.append("Straßenpreise")
    if any(token in lowered_user or token in lowered_query for token in _WEBSEARCH_TOP_LIST_MARKERS):
        parts.append("Top 3")
        parts.append("Highlights")
        parts.append("beliebteste Spiele")
    if any(token in lowered_user or token in lowered_query for token in _WEBSEARCH_SWITCH_2_LAUNCH_MARKERS):
        parts.append("Konsole")
        parts.append("Launch Deutschland")
    return " ".join(part for part in parts if part).strip()


def _extract_time_fragment_for_switch_2_release_query(query: str) -> str:
    normalized_query = re.sub(r"\s+", " ", str(query or "").strip())
    if not normalized_query:
        return ""
    month_match = re.search(rf"\b(?:{_MONTH_NAME_PATTERN})\s+\d{{4}}\b", normalized_query, flags=re.IGNORECASE)
    if month_match:
        return str(month_match.group(0) or "").strip()
    week_match = re.search(r"\b(?:kw|kalenderwoche)\s*\d{1,2}\s+20\d{2}\b", normalized_query, flags=re.IGNORECASE)
    if week_match:
        return str(week_match.group(0) or "").strip()
    quarter_match = re.search(r"\bQ[1-4]\s+20\d{2}\b", normalized_query, flags=re.IGNORECASE)
    if quarter_match:
        return str(quarter_match.group(0) or "").strip().upper()
    year_match = re.search(r"\b20\d{2}\b", normalized_query)
    if year_match:
        return str(year_match.group(0) or "").strip()
    return ""


def _resolve_relative_time_reference(user_text: str) -> Optional[Tuple[str, str]]:
    lowered = re.sub(r"\s+", " ", str(user_text or "").strip().lower())
    if not lowered:
        return None
    now = datetime.utcnow()
    if any(token in lowered for token in ("nächste woche", "naechste woche", "kommende woche", "next week")):
        target = now + timedelta(weeks=1)
        iso_year, iso_week, _ = target.isocalendar()
        return ("week", f"Kalenderwoche {iso_week:02d} {iso_year}")
    if any(token in lowered for token in ("nächstes quartal", "naechstes quartal", "kommendes quartal", "kommenden quartal", "next quarter")):
        current_quarter = ((now.month - 1) // 3) + 1
        target_quarter = current_quarter + 1
        target_year = now.year
        if target_quarter == 5:
            target_quarter = 1
            target_year += 1
        return ("quarter", f"Q{target_quarter} {target_year}")
    if any(token in lowered for token in ("dieses jahr", "in diesem jahr", "current year", "this year")):
        return ("year", str(now.year))
    if any(token in lowered for token in ("nächsten monat", "naechsten monat", "kommenden monat", "next month")):
        target_month = now.month + 1
        target_year = now.year
        if target_month == 13:
            target_month = 1
            target_year += 1
        return ("month", f"{_GERMAN_MONTH_NAMES[target_month]} {target_year}")
    if any(token in lowered for token in ("diesen monat", "diesem monat", "current month", "this month")):
        return ("month", f"{_GERMAN_MONTH_NAMES[now.month]} {now.year}")
    return None


def _replace_query_time_reference(query: str, *, reference: Tuple[str, str]) -> str:
    sanitized_query = re.sub(r"\s+", " ", str(query or "").strip())
    if not sanitized_query:
        return reference[1]
    kind, reference_text = reference
    token_pattern = _RELATIVE_TOKEN_REGEX.get(kind)
    if token_pattern:
        sanitized_query = re.sub(token_pattern, reference_text, sanitized_query, flags=re.IGNORECASE)
    if reference_text.casefold() in sanitized_query.casefold():
        return sanitized_query
    if kind == "month":
        month_year_pattern = re.compile(rf"\b(?:{_MONTH_NAME_PATTERN})\s+\d{{4}}\b", flags=re.IGNORECASE)
        if month_year_pattern.search(sanitized_query):
            return month_year_pattern.sub(reference_text, sanitized_query, count=1)
        year_match = re.search(r"\b20\d{2}\b", sanitized_query)
        if year_match:
            return re.sub(r"\b20\d{2}\b", reference_text.split(" ", 1)[1], sanitized_query, count=1)
    elif kind == "week":
        kw_pattern = re.compile(r"\b(?:kw|kalenderwoche)\s*\d{1,2}\s+20\d{2}\b", flags=re.IGNORECASE)
        if kw_pattern.search(sanitized_query):
            return kw_pattern.sub(reference_text, sanitized_query, count=1)
    elif kind == "year":
        year_pattern = re.compile(r"\b20\d{2}\b")
        if year_pattern.search(sanitized_query):
            return year_pattern.sub(reference_text, sanitized_query, count=1)
    elif kind == "quarter":
        quarter_pattern = re.compile(r"\b(?:q[1-4]|quartal\s+[1-4])\s*20\d{2}\b", flags=re.IGNORECASE)
        if quarter_pattern.search(sanitized_query):
            return quarter_pattern.sub(reference_text, sanitized_query, count=1)
    return f"{sanitized_query} {reference_text}".strip()


def _sanitize_local_business_tool_args(tool_args: Dict[str, Any], *, user_text: str) -> Dict[str, Any]:
    sanitized = dict(tool_args or {})
    current_query = str(sanitized.get("query") or "").strip()
    current_location = str(sanitized.get("location") or "").strip()
    extracted_query = _extract_local_business_query_from_text(user_text)
    extracted_location = _extract_local_business_location_from_text(user_text)

    query_is_suspicious = bool(current_query) and current_query.casefold() not in user_text.casefold()
    location_is_suspicious = bool(current_location) and current_location.casefold() not in user_text.casefold()

    if extracted_query and (not current_query or query_is_suspicious):
        sanitized["query"] = extracted_query
    if extracted_location and (not current_location or location_is_suspicious):
        sanitized["location"] = extracted_location
    return sanitized


def _extract_local_business_location_from_text(text: str) -> Optional[str]:
    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    if not normalized:
        return None
    match = re.search(r"\b(?:in|im|am|an der|an den)\s+([^\n,.!?]+)", normalized, flags=re.IGNORECASE)
    if not match:
        return None
    location = str(match.group(1) or "").strip(" .,!?:;")
    location = re.sub(
        r"^(?:bitte|genau|exakt|nur|mal|doch|die|den|dem|das|einen|eine|einer|gute|guten|guter|besten|bestes|bestenfalls)\s+",
        "",
        location,
        flags=re.IGNORECASE,
    ).strip()
    return location[:160] if location else None


def _extract_local_business_query_from_text(text: str) -> Optional[str]:
    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    if not normalized:
        return None
    keyword_pattern = "|".join(re.escape(keyword) for keyword in _LOCAL_BUSINESS_KEYWORDS)
    match = re.search(
        r"((?:[A-Za-zÄÖÜäöüß][\wÄÖÜäöüß-]*\s+){0,3}(?:" + keyword_pattern + r"))",
        normalized,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    query = str(match.group(1) or "").strip(" .,!?:;")
    query = re.sub(
        r"^(?:finde(?:\s+mir)?|suche(?:\s+mir)?|zeig(?:e)?\s+mir|empfiehl(?:\s+mir)?|nenn(?:e)?\s+mir|bitte|genau|exakt|nur|mal)\s+",
        "",
        query,
        flags=re.IGNORECASE,
    )
    query = re.sub(
        r"^(?:\d+|vier|drei|zwei|fünf|fuenf|sechs|sieben|acht|neun|zehn)\s+",
        "",
        query,
        flags=re.IGNORECASE,
    )
    query = re.sub(
        r"^(?:gute|guten|guter|besten|bestes|hochbewertete|hoch bewertete|top)\s+",
        "",
        query,
        flags=re.IGNORECASE,
    )
    query = query.strip()
    return query[:160] if query else None
