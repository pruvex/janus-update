import json
import logging
import math
import os
import re
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import aiohttp
import keyring
from dotenv import load_dotenv

from backend.data.schemas import VideoResult, VideoSearchInput, VideoSearchOutput
from backend.data.schemas_tools import ToolErrorDetails, ToolResultV1
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger("janus_backend")

_YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
_YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
_YOUTUBE_CHANNELS_URL = "https://www.googleapis.com/youtube/v3/channels"
_YOUTUBE_PLAYLIST_ITEMS_URL = "https://www.googleapis.com/youtube/v3/playlistItems"
# Smart latest: raw search window (API cap 50; we filter in Python).
_SMART_LATEST_NET_MAX_RESULTS = 20
# Channel name resolution: enough candidates for fuzzy pick (log top 3).
_CHANNEL_SEARCH_MAX_RESULTS = 20
# UNIVERSAL CHANNEL LOCK: Keine harte Liste mehr - jeder Kanalname wird dynamisch erkannt
_VIDEO_CACHE_TTL_SECONDS = 3600
_LATEST_CACHE_TTL_SECONDS = 120
_VIDEO_CACHE_LOCK = threading.Lock()
_VIDEO_CACHE: Dict[str, Dict[str, Any]] = {}

_CHANNEL_ID_CACHE_TTL_SECONDS = 7 * 24 * 3600
_CHANNEL_ID_CACHE_LOCK = threading.Lock()
_CHANNEL_ID_MEMORY_CACHE: Dict[str, Dict[str, Any]] = {}


def clear_video_search_cache() -> None:
    """One-shot flush (e.g. on app startup) so stale ranked results cannot linger."""
    with _VIDEO_CACHE_LOCK:
        _VIDEO_CACHE.clear()
    with _CHANNEL_ID_CACHE_LOCK:
        _CHANNEL_ID_MEMORY_CACHE.clear()
    logger.info("💎 VIDEO-CACHE: cleared on startup (one-shot)")


def _channel_id_cache_file_path() -> Path:
    base = Path(get_app_data_dir())
    base.mkdir(parents=True, exist_ok=True)
    return base / "youtube_channel_id_cache.json"


def _read_channel_id_disk_cache() -> Dict[str, Any]:
    path = _channel_id_cache_file_path()
    if not path.is_file():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _write_channel_id_disk_cache(entries: Dict[str, Any]) -> None:
    path = _channel_id_cache_file_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"entries": entries}, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.warning("Channel-ID disk cache write failed: %s", exc)


def _channel_id_cache_key(channel_name: str) -> str:
    return _normalize_text_for_match(channel_name)


def _channel_cache_get_resolved_id(key: str) -> Tuple[Optional[str], str]:
    """Return (channel_id or None, 'hit'|'miss')."""
    if not key:
        return None, "miss"
    now = time.time()
    with _CHANNEL_ID_CACHE_LOCK:
        ent = _CHANNEL_ID_MEMORY_CACHE.get(key)
        if isinstance(ent, dict):
            cid = str(ent.get("channel_id") or "").strip()
            if cid and float(ent.get("expires_at", 0.0)) > now:
                return cid, "hit"
    disk = _read_channel_id_disk_cache()
    raw_entries = disk.get("entries")
    entries: Dict[str, Any] = raw_entries if isinstance(raw_entries, dict) else {}
    e = entries.get(key)
    if isinstance(e, dict):
        cid = str(e.get("channel_id") or "").strip()
        ex = float(e.get("expires_at", 0.0))
        if cid and ex > now:
            with _CHANNEL_ID_CACHE_LOCK:
                _CHANNEL_ID_MEMORY_CACHE[key] = {"channel_id": cid, "expires_at": ex}
            return cid, "hit"
    return None, "miss"


def _pick_best_channel_id_from_search_items(items: List[Dict[str, Any]], channel_hint: str) -> str:
    """Pick official channel among search results (avoid fan re-upload channels); fuzzy prefix/contains.
    
    UNIVERSAL CHANNEL LOCK: Dynamischer Score +5000 bei Übereinstimmung mit extrahiertem Hint.
    """
    hint_n = _normalize_text_for_match(channel_hint)
    best_id = ""
    best_score = -1.0
    
    for it in items:
        if not isinstance(it, dict):
            continue
        ch_id = str(((it.get("id") or {}).get("channelId")) or "").strip()
        sn = it.get("snippet") if isinstance(it.get("snippet"), dict) else {}
        title = str(sn.get("title") or "").strip()
        if not ch_id or not title:
            continue
        title_n = _normalize_text_for_match(title)
        
        # UNIVERSAL LOCK: Base score aus Fuzzy-Matching
        sc = _channel_match_score(title, hint_n)
        
        # Level 1: Exakter Match = SOFORTIGER GEWINNER
        if hint_n and hint_n == title_n:
            logger.info("💎 CHANNEL-EXACT-MATCH: '%s' == '%s' (ID: %s)", title, channel_hint, ch_id)
            return ch_id
        
        # Level 2: Teil-String Match = +5000 Punkte (dominiert alle anderen)
        if hint_n and (hint_n in title_n or title_n in hint_n):
            sc += 5000.0
            logger.debug("💎 CHANNEL-PARTIAL-MATCH: '%s' contains '%s' (+5000)", title, hint_n)
        
        # Level 3: Prefix Match = +100 Punkte
        if hint_n and (title_n.startswith(hint_n) or hint_n.startswith(title_n)):
            sc += 100.0
            
        # Level 4: Token-Overlap = +10 pro Treffer
        hint_tokens = set(hint_n.split())
        title_tokens = set(title_n.split())
        overlap = len(hint_tokens & title_tokens)
        sc += 10.0 * overlap
        
        if sc > best_score:
            best_score = sc
            best_id = ch_id
            
    # Mindest-Score für Akzeptanz: 100 (verhindert falsche Matches)
    if best_score >= 100:
        logger.info("💎 CHANNEL-SELECTED: Score=%.0f for ID=%s", best_score, best_id)
        return best_id
    
    return ""


def _channel_cache_store(key: str, channel_id: str) -> None:
    expires_at = time.time() + _CHANNEL_ID_CACHE_TTL_SECONDS
    with _CHANNEL_ID_CACHE_LOCK:
        _CHANNEL_ID_MEMORY_CACHE[key] = {"channel_id": channel_id, "expires_at": expires_at}
    disk = _read_channel_id_disk_cache()
    raw_entries = disk.get("entries")
    entries: Dict[str, Any] = dict(raw_entries) if isinstance(raw_entries, dict) else {}
    now = time.time()
    entries[key] = {"channel_id": channel_id, "expires_at": expires_at}
    # drop expired
    pruned: Dict[str, Any] = {}
    for k, v in entries.items():
        if not isinstance(v, dict):
            continue
        if float(v.get("expires_at", 0.0)) > now:
            pruned[k] = v
    _write_channel_id_disk_cache(pruned)


async def _resolve_channel_by_handle(
    session: aiohttp.ClientSession,
    api_key: str,
    handle: str,
) -> str:
    """Try channels.list?forHandle=@handle (deterministic, zero ambiguity)."""
    clean = str(handle or "").strip().lstrip("@")
    if not clean:
        return ""
    for attempt in (f"@{clean}", clean):
        params: Dict[str, Any] = {
            "key": api_key,
            "part": "id,snippet",
            "forHandle": attempt,
        }
        _log_diamond_api_call(_YOUTUBE_CHANNELS_URL, params)
        try:
            data = await _youtube_get(session, _YOUTUBE_CHANNELS_URL, params)
        except Exception as exc:
            logger.debug("💎 HANDLE-RESOLVE: forHandle='%s' failed: %s", attempt, exc)
            continue
        items = data.get("items") if isinstance(data.get("items"), list) else []
        if items and isinstance(items[0], dict):
            ch_id = str(items[0].get("id") or "").strip()
            if ch_id:
                sn = items[0].get("snippet") if isinstance(items[0].get("snippet"), dict) else {}
                logger.info("💎 HANDLE-RESOLVED: '%s' -> ID: %s title='%s'", attempt, ch_id, str(sn.get("title") or ""))
                return ch_id
    return ""


async def _resolve_channel_id(
    session: aiohttp.ClientSession,
    api_key: str,
    channel_name: str,
    safe_search: str,
) -> Tuple[str, str]:
    """
    Resolve a human channel name via search.list(type=channel) + Python best-match.
    Cached 7d (RAM + disk).
    """
    label = str(channel_name or "").strip()
    key = _channel_id_cache_key(label)
    cached, src = _channel_cache_get_resolved_id(key)
    if cached:
        logger.info("💎 CHANNEL-RESOLVED: '%s' -> ID: %s (Cache: %s)", label, cached, src)
        logger.info("💎 CHANNEL-LOCK: Resolved '%s' to ID: %s", label, cached)
        return cached, src
    # Phase 1: Deterministic handle lookup (channels.list?forHandle)
    handle_id = await _resolve_channel_by_handle(session, api_key, label)
    if handle_id:
        _channel_cache_store(key, handle_id)
        logger.info("💎 CHANNEL-RESOLVED: '%s' -> ID: %s (Cache: miss, via handle)", label, handle_id)
        logger.info("💎 CHANNEL-LOCK: Resolved '%s' to ID: %s", label, handle_id)
        return handle_id, "miss"
    # Phase 2: Fuzzy search fallback
    params: Dict[str, Any] = {
        "key": api_key,
        "part": "snippet",
        "q": label,
        "type": "channel",
        "maxResults": _CHANNEL_SEARCH_MAX_RESULTS,
        "safeSearch": safe_search,
    }
    _log_diamond_api_call(_YOUTUBE_SEARCH_URL, params)
    data = await _youtube_get(session, _YOUTUBE_SEARCH_URL, params)
    items = data.get("items") if isinstance(data.get("items"), list) else []
    if not items:
        logger.info("💎 CHANNEL-RESOLVED: '%s' -> ID: (none) (Cache: miss)", label)
        return "", "miss"
    for i, it in enumerate(items[:3]):
        if not isinstance(it, dict):
            continue
        sn = it.get("snippet") if isinstance(it.get("snippet"), dict) else {}
        t = str(sn.get("title") or "").strip()
        ch = str(((it.get("id") or {}).get("channelId")) or "").strip()
        logger.info("💎 CHANNEL-HIT [%s]: title='%s' id=%s", i + 1, t, ch or "?")
    ch_id = _pick_best_channel_id_from_search_items(items, label)
    if not ch_id:
        logger.info("💎 CHANNEL-RESOLVED: '%s' -> ID: (none) (Cache: miss)", label)
        return "", "miss"
    _channel_cache_store(key, ch_id)
    logger.info("💎 CHANNEL-RESOLVED: '%s' -> ID: %s (Cache: miss)", label, ch_id)
    logger.info("💎 CHANNEL-LOCK: Resolved '%s' to ID: %s", label, ch_id)
    return ch_id, "miss"


def _get_youtube_api_key() -> str:
    # Priority 1: Local config in AppData (not in Git, for beta testers)
    app_data = Path(get_app_data_dir())
    local_config = app_data / "local_config.json"
    if local_config.is_file():
        try:
            with open(local_config, "r", encoding="utf-8") as f:
                config = json.load(f)
            local_key = str(config.get("youtube_api_key") or "").strip()
            if local_key:
                logger.info("VIDEO-SEARCH: Using YOUTUBE_API_KEY from local_config.json.")
                return local_key
        except Exception as exc:
            logger.debug("VIDEO-SEARCH: Failed to read local_config.json: %s", exc)
    
    # Priority 2: Environment variable (.env)
    # Try multiple paths for .env (dev vs PyInstaller)
    env_paths = [
        Path(__file__).resolve().parents[2] / ".env",  # Dev environment
        Path(sys._MEIPASS) / ".env" if getattr(sys, 'frozen', False) else None,  # PyInstaller
        Path.cwd() / ".env",  # Current working directory
    ]
    for env_path in env_paths:
        if env_path and env_path.is_file():
            load_dotenv(dotenv_path=env_path, override=False)
            break
    env_key = str(os.getenv("YOUTUBE_API_KEY") or "").strip()
    if env_key:
        logger.info("VIDEO-SEARCH: Using YOUTUBE_API_KEY from environment.")
        return env_key
    
    # Priority 3: Keyring
    for candidate in ("youtube", "youtube_api", "google", "google_api"):
        key = str(keyring.get_password("Janus-Projekt", candidate) or "").strip()
        if key:
            logger.info("VIDEO-SEARCH: Using YouTube API key from keyring namespace '%s'.", candidate)
            return key
    
    return ""


def set_youtube_api_key(api_key: str) -> bool:
    """
    Speichert den YouTube-API-Key sicher in der lokalen Konfiguration (AppData).
    Diese Datei wird nicht im Git versioniert und ist für Beta-Tester gedacht.
    
    Args:
        api_key: Der YouTube-API-Key
        
    Returns:
        True bei Erfolg, False bei Fehler
    """
    app_data = Path(get_app_data_dir())
    app_data.mkdir(parents=True, exist_ok=True)
    local_config = app_data / "local_config.json"
    
    try:
        # Existierende Konfiguration laden oder neue erstellen
        if local_config.is_file():
            with open(local_config, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}
        
        # Key speichern
        config["youtube_api_key"] = api_key.strip()
        
        # Konfiguration schreiben
        with open(local_config, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info("VIDEO-SEARCH: YouTube API key saved to local_config.json.")
        return True
    except Exception as exc:
        logger.error("VIDEO-SEARCH: Failed to save YouTube API key to local_config.json: %s", exc)
        return False


def _normalize_query(query: str, *, suppress_tutorial_suffix: bool = False) -> str:
    q = " ".join(str(query or "").strip().split())
    low = q.lower()
    if "youtube" in low:
        q = q.replace("YouTube", "").replace("youtube", "").strip()
    if "video" in low:
        q = q.replace("Video", "").replace("video", "").strip()
    if not q:
        return str(query or "").strip()
    if suppress_tutorial_suffix:
        return q
    if not any(tok in q.lower() for tok in ("tutorial", "anleitung", "rezept", "how to", "guide")):
        q = f"{q} tutorial"
    return q


def _token_overlap_score(query: str, title: str, channel: str) -> float:
    q_tokens = {tok for tok in query.lower().split() if len(tok) > 2}
    if not q_tokens:
        return 0.0
    target = f"{title} {channel}".lower()
    hits = sum(1 for tok in q_tokens if tok in target)
    return min(1.0, hits / max(1, len(q_tokens)))


def _channel_quality_score(channel_title: str, subscriber_count: int) -> float:
    base = 0.25 if any(marker in channel_title.lower() for marker in ("official", "tv", "kitchen", "academy")) else 0.0
    subs = min(1.0, math.log10(max(1, subscriber_count)) / 7.0)
    return min(1.0, base + subs)


def _normalize_text_for_match(value: str) -> str:
    txt = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()
    return " ".join(txt.split())


GEO_REJECTION_LIST = {
    "rom",
    "paris",
    "berlin",
    "wien",
    "tokio",
    "tokyo",
    "london",
    "madrid",
    "barcelona",
    "mailand",
    "venedig",
    "prag",
    "athen",
    "istanbul",
    "new york",
}


def _is_geo_rejected_hint(hint: str) -> bool:
    norm = _normalize_text_for_match(hint)
    if not norm:
        return False
    return norm in GEO_REJECTION_LIST


def _extract_channel_hint(query: str) -> str:
    """
    Universelle Kanal-Intent-Erkennung.
    Erkennt Muster wie: 'von NAME', 'vom Kanal NAME', 'auf NAME', 'Kanal NAME',
    'neuestes Video NAME', 'Video von NAME', etc.
    """
    q = str(query or "").strip()
    
    # Erweiterte Patterns für universelle Kanal-Erkennung
    patterns = (
        # Standard: "von Zumikito", "from MrBeast"
        r"(?:\bvon\b|\bfrom\b)\s+([A-Za-z0-9][A-Za-z0-9 ._\-&]{1,64})",
        # Explizit: "vom Kanal", "from channel"
        r"(?:\bvom\skanal\b|\bfrom\schannel\b)\s+([A-Za-z0-9][A-Za-z0-9 ._\-&]{1,64})",
        # Auf dem Kanal: "auf Zumikito"
        r"\bauf\b\s+([A-Za-z0-9][A-Za-z0-9 ._\-&]{1,64})",
        # Explizite Kanal-Nennung: "Kanal Zumikito", "channel MrBeast"
        r"(?:^|\s)(?:kanal|channel)\s+([A-Za-z0-9][A-Za-z0-9 ._\-&]{1,64})",
        # Video-Kontext: "neuestes Video Zumikito", "latest video MrBeast"
        r"(?:video|videos)\s+(?:von|from|by)\s+([A-Za-z0-9][A-Za-z0-9 ._\-&]{1,64})",
        # Direkt nach Adjektiv: "neuestes von Zumikito"
        r"(?:neueste[ns]?|latest|newest|aktuellste)\s+(?:video|von|from)?\s+([A-Za-z0-9][A-Za-z0-9 ._\-&]{1,64})",
    )
    
    for pat in patterns:
        m = re.search(pat, q, re.IGNORECASE)
        if not m:
            continue
        hint = m.group(1).strip(" .,:;!?-")
        # Stop-Wörter entfernen
        hint = re.split(r"\b(video|videos|kanal|channel|latest|neueste|newest|von|from|auf|on)\b", hint, flags=re.IGNORECASE)[0]
        hint = hint.strip()
        
        # Validierung: Muss wie ein Kanalname aussehen
        if _is_likely_channel_name(hint):
            norm = _normalize_text_for_match(hint)
            if norm and len(norm) >= 2:
                logger.info("💎 UNIVERSAL-CHANNEL-HINT: Extrahiert '%s' aus Query", norm)
                return norm
    
    return ""


def _is_likely_channel_name(text: str) -> bool:
    """Prüft ob ein Text ein valider Kanalname sein könnte (keine Satzzeichen, min. 2 Zeichen)."""
    if not text or len(text) < 2:
        return False
    # Keine Satzzeichen am Ende (außer erlaubte wie & - _)
    if re.search(r'[.!?,:;]$', text):
        return False
    # Mindestens ein Buchstabe
    if not re.search(r'[a-zA-Z]', text):
        return False
    return True


def _clean_channel_hint_for_resolution(hint: str) -> str:
    """NUCLEAR STRIP: Entferne ALLE Kontext-Wörter vom Kanal-Hint."""
    if not hint:
        return ""
    # Liste der zu entfernenden Wörter
    garbage_words = [
        'neueste', 'neuesten', 'neuestes', 'neuester', 'neuesten',
        'latest', 'newest', 'most recent',
        'aktuellste', 'aktuellster', 'aktuellsten',
        'letzte', 'letzter', 'letztes', 'letzten',
        'video', 'videos',
        'von', 'vom', 'kanal', 'channel', 'auf', 'from', 'by'
    ]
    cleaned = str(hint).lower()
    for word in garbage_words:
        cleaned = re.sub(rf'\b{re.escape(word)}\b', '', cleaned, flags=re.IGNORECASE)
    # Mehrfache Leerzeichen entfernen und trimmen
    cleaned = ' '.join(cleaned.split())
    return cleaned.strip()


def _query_has_channel_intent(query: str) -> bool:
    q = str(query or "").lower()
    if any(marker in q for marker in (" von ", " vom kanal ", " from ", " from channel ", " auf ")):
        return True
    if re.search(r"(?:^|\s)(?:kanal|channel)\s+[a-z0-9]", q, re.IGNORECASE):
        return True
    return False


def _query_wants_recency(raw_query: str) -> bool:
    """True if the user asks for the newest / latest / most recent video."""
    q = f" {str(raw_query or '').strip().lower()} "
    markers = (
        " neueste ",
        " neuesten ",
        " neues ",
        " aktuellste ",
        " aktuellster ",
        " aktuellsten ",
        " letzte ",
        " letzter ",
        " letztes ",
        " letzten ",
        " latest ",
        " newest ",
        " most recent ",
    )
    return any(m in q for m in markers)


def _refine_search_query(base_query: str, channel_hint: str) -> str:
    q = " ".join(str(base_query or "").split()).strip()
    if not channel_hint:
        return q
    return f"\"{channel_hint}\" official {q}".strip()


def _channel_match_score(channel_title: str, channel_hint: str) -> float:
    if not channel_hint:
        return 0.0
    channel_norm = _normalize_text_for_match(channel_title)
    if not channel_norm:
        return 0.0
    if channel_norm == channel_hint:
        return 1.0
    if channel_norm.startswith(channel_hint) or channel_hint.startswith(channel_norm):
        return 0.98
    if channel_hint in channel_norm or channel_norm in channel_hint:
        return 0.95
    hint_tokens = {t for t in channel_hint.split() if len(t) > 1}
    if not hint_tokens:
        return 0.0
    hit_count = sum(1 for t in hint_tokens if t in channel_norm)
    if hit_count <= 0:
        return 0.0
    return min(0.9, hit_count / max(1, len(hint_tokens)))


def _recency_score(published_at: Optional[str]) -> float:
    s = str(published_at or "").strip()
    if not s:
        return 0.0
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        days_old = max(0.0, (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 86400.0)
        # 0 days => 1.0, 60+ days => ~0.0
        return max(0.0, 1.0 - (days_old / 60.0))
    except Exception:
        return 0.0


def _rank_video(
    *,
    query: str,
    channel_hint: str,
    title: str,
    channel_title: str,
    published_at: Optional[str],
    views: int,
    subscriber_count: int,
    wants_recency: bool,
) -> float:
    relevance = _token_overlap_score(query, title, channel_title)  # 0..1 (primary)
    views_score = min(1.0, math.log10(max(1, views)) / 8.0)  # 0..1
    channel_score = _channel_quality_score(channel_title, subscriber_count)  # 0..1
    channel_match = _channel_match_score(channel_title, channel_hint)  # 0..1
    channel_norm = _normalize_text_for_match(channel_title)
    query_norm = _normalize_text_for_match(query)
    query_tokens = set(query_norm.split())
    exact_channel_match = bool(channel_hint) and channel_norm == channel_hint
    global_exact_token_match = (not channel_hint) and bool(channel_norm) and channel_norm in query_tokens
    recency = _recency_score(published_at) if wants_recency else 0.0
    # Loyalty-over-playability: semantic/channel relevance dominates score by design.
    return (
        (1000.0 if (exact_channel_match or global_exact_token_match) else 0.0)  # radical channel authority
        +
        (8.0 * relevance)
        + (7.0 * channel_match)  # hard boost if query names a channel
        + (0.6 * recency)
        + (0.3 * channel_score)
        + (0.1 * views_score)
    )


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(str(value))
    except Exception:
        return default


def _video_cache_key(
    *, query: str, safe_search: bool, max_results: int, min_views: int, order: str
) -> str:
    normalized_query = str(query or "").strip().lower()
    ord_key = str(order or "relevance").strip().lower()
    return f"{normalized_query}|safe={int(bool(safe_search))}|max={int(max_results)}|min={int(min_views)}|order={ord_key}"


def _get_cached_video_result(cache_key: str) -> Optional[ToolResultV1]:
    now = time.time()
    with _VIDEO_CACHE_LOCK:
        entry = _VIDEO_CACHE.get(cache_key)
        if not entry:
            return None
        if float(entry.get("expires_at", 0.0)) <= now:
            _VIDEO_CACHE.pop(cache_key, None)
            return None
        data = entry.get("data")
        metadata = entry.get("metadata")
    if not isinstance(data, dict):
        return None
    return ToolResultV1(status="ok", data=data, metadata=metadata if isinstance(metadata, dict) else {})


def _store_cached_video_result(cache_key: str, result: ToolResultV1, *, ttl: int = _VIDEO_CACHE_TTL_SECONDS) -> None:
    expires_at = time.time() + ttl
    with _VIDEO_CACHE_LOCK:
        _VIDEO_CACHE[cache_key] = {
            "expires_at": expires_at,
            "data": dict(result.data or {}),
            "metadata": dict(result.metadata or {}),
        }


def _log_diamond_api_call(url: str, params: Dict[str, Any]) -> None:
    """Log request URL with query string; API key redacted (diamond audit)."""
    redacted = {str(k): ("***" if str(k) == "key" else v) for k, v in sorted(params.items())}
    qs = urlencode(redacted, doseq=True)
    logger.info("💎 API-CALL: %s?%s", url, qs)


async def _youtube_get(session: aiohttp.ClientSession, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
        payload = await response.json(content_type=None)
        if response.status >= 400:
            raise RuntimeError(f"YouTube API error {response.status}: {payload}")
        if not isinstance(payload, dict):
            raise RuntimeError("YouTube API returned non-dict payload")
        return payload


async def _channels_uploads_playlist_id(
    session: aiohttp.ClientSession, api_key: str, channel_id: str
) -> str:
    """Return relatedPlaylists.uploads for the channel (chronological upload order)."""
    data = await _youtube_get(
        session,
        _YOUTUBE_CHANNELS_URL,
        {"key": api_key, "part": "contentDetails", "id": channel_id},
    )
    items = data.get("items") if isinstance(data.get("items"), list) else []
    if not items or not isinstance(items[0], dict):
        return ""
    cd = items[0].get("contentDetails") if isinstance(items[0].get("contentDetails"), dict) else {}
    rp = cd.get("relatedPlaylists") if isinstance(cd.get("relatedPlaylists"), dict) else {}
    return str(rp.get("uploads") or "").strip()


async def _playlist_items_get_videos(
    session: aiohttp.ClientSession, api_key: str, uploads_playlist_id: str, max_results: int = 5
) -> List[str]:
    """
    FEED-AUTHORITY: Hole die neuesten N Videos aus der Upload-Playlist.
    Die Playlist ist PHYSIKALISCH chronologisch sortiert (neuestes zuerst).
    """
    data = await _youtube_get(
        session,
        _YOUTUBE_PLAYLIST_ITEMS_URL,
        {
            "key": api_key,
            "part": "snippet,contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": max_results,
        },
    )
    items = data.get("items") if isinstance(data.get("items"), list) else []
    video_ids: List[str] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        # Versuche videoId aus contentDetails zu holen
        cd = it.get("contentDetails") if isinstance(it.get("contentDetails"), dict) else {}
        vid = str(cd.get("videoId") or "").strip()
        if len(vid) == 11:
            video_ids.append(vid)
            continue
        # Fallback: resourceId aus snippet
        sn = it.get("snippet") if isinstance(it.get("snippet"), dict) else {}
        rid = sn.get("resourceId") if isinstance(sn.get("resourceId"), dict) else {}
        vid = str(rid.get("videoId") or "").strip()
        if len(vid) == 11:
            video_ids.append(vid)
    return video_ids


def _parse_youtube_published_at(ts: str) -> datetime:
    """Parse snippet publishedAt for authoritative sorting (UTC)."""
    s = str(ts or "").strip()
    if not s:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.fromtimestamp(0, tz=timezone.utc)


def _format_published_date_human(iso_date: Optional[str]) -> Optional[str]:
    """Format ISO-8601 publishedAt to human-readable DD.MM.YYYY."""
    s = str(iso_date or "").strip()
    if not s:
        return None
    try:
        dt = _parse_youtube_published_at(s)
        if dt.timestamp() <= 0:
            return None
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return None


def _build_video_markdown_output(videos: list) -> str:
    """
    Baut eine LLM-lesbare, UI-freundliche Video-Liste.
    KEIN Autoplay. Nur Übersicht.
    """
    if not videos:
        return "Keine Videos gefunden."

    lines = []
    lines.append(f"### 🎬 Gefundene Videos ({len(videos)})\n")

    for i, v_data in enumerate(videos, start=1):
        # Adapt to handle both Pydantic models and dicts
        title = v_data.get('title', 'Unbekannter Titel').strip()
        channel = v_data.get('channel', 'Unbekannt')
        url = v_data.get('watch_url', '')
        views = v_data.get('views', None)
        published = v_data.get('published_date_human', '')

        meta_parts = []
        if channel:
            meta_parts.append(channel)
        if views is not None:
            meta_parts.append(f"{views:,} Aufrufe".replace(",", "."))
        if published:
            meta_parts.append(f"(Hochgeladen am {published})")

        meta = " • ".join(meta_parts)

        lines.append(f"**{i}. {title}**")
        if meta:
            lines.append(f"_{meta}_")
        if url:
            lines.append(f"[Video ansehen]({url})")

        lines.append("") # Leerzeile für spacing

    return "\n".join(lines)


def _to_rfc3339(date_str: str) -> str:
    """Konvertiert YYYY-MM-DD zu RFC 3339 für YouTube API."""
    s = str(date_str or "").strip()
    if "T" not in s:
        s = f"{s}T00:00:00Z"
    return s


def _parse_iso8601_duration_seconds(raw: Optional[str]) -> Optional[int]:
    """YouTube contentDetails.duration, e.g. PT4M54S, PT45S, PT1H2M3S."""
    s = str(raw or "").strip()
    if not s.startswith("PT"):
        return None
    m = re.match(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$", s)
    if not m:
        return None
    h, mn, sec = m.group(1), m.group(2), m.group(3)
    total = int(h or 0) * 3600 + int(mn or 0) * 60 + int(sec or 0)
    return total if total > 0 or (h or mn or sec) else None


def _video_duration_seconds_from_item(item: Dict[str, Any]) -> Optional[int]:
    cd = item.get("contentDetails") if isinstance(item.get("contentDetails"), dict) else {}
    return _parse_iso8601_duration_seconds(str(cd.get("duration") or ""))


def _snippet_live_broadcast_content(item: Dict[str, Any]) -> str:
    sn = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
    return str(sn.get("liveBroadcastContent") or "none").strip().lower()


def _apply_smart_filters(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Drop obvious Shorts-by-title; annotate live / premiere (upcoming) on each item.
    Mutates copies via shallow copy + _smart_meta sidecar.
    """
    out: List[Dict[str, Any]] = []
    for raw in videos:
        if not isinstance(raw, dict):
            continue
        sn = raw.get("snippet") if isinstance(raw.get("snippet"), dict) else {}
        title = str(sn.get("title") or "")
        if "#shorts" in title.lower():
            continue
        item = dict(raw)
        lbc = _snippet_live_broadcast_content(raw)
        item["_smart_meta"] = {
            "is_live": lbc == "live",
            "is_premiere_or_upcoming": lbc == "upcoming",
        }
        out.append(item)
    return out


def _duration_label_for_log(item: Dict[str, Any], duration_sec: Optional[int]) -> str:
    sm = item.get("_smart_meta") if isinstance(item.get("_smart_meta"), dict) else {}
    if sm.get("is_live"):
        return "live"
    if sm.get("is_premiere_or_upcoming"):
        return "upcoming"
    if duration_sec is None:
        return "unknown"
    m, s = divmod(int(duration_sec), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def _diamond_smart_score(
    *,
    published_at: str,
    duration_sec: Optional[int],
    has_non_short_alternative: bool,
    smart_meta: Optional[Dict[str, Any]] = None,
) -> float:
    """Diamond score: timestamp base + quality bonus/malus (see SMART LATEST VIDEO dossier)."""
    pub_dt = _parse_youtube_published_at(published_at)
    now = datetime.now(timezone.utc)
    now_ts = now.timestamp()
    pt = pub_dt.timestamp()
    # Scheduled premieres can have publishedAt in the future — do not beat real uploads.
    if pt > now_ts:
        pt = now_ts - 365 * 86400
    timestamp_weight = pt
    score = timestamp_weight
    d = duration_sec
    if d is not None and 120 <= d <= 1200:
        score += 10.0
    if d is not None and d < 60 and has_non_short_alternative:
        score -= 50.0
    sm = smart_meta if isinstance(smart_meta, dict) else {}
    if sm.get("is_premiere_or_upcoming") or sm.get("is_live"):
        score -= 200.0
    return score


async def _search_list_in_channel_by_date(
    session: aiohttp.ClientSession,
    api_key: str,
    *,
    channel_id: str,
    safe_search: str,
) -> List[str]:
    """search.list: full channel chronological net; ``q`` empty string (audit), not keyword-restricted."""
    params: Dict[str, Any] = {
        "key": api_key,
        "part": "snippet",
        "channelId": channel_id,
        "type": "video",
        "order": "date",
        "maxResults": _SMART_LATEST_NET_MAX_RESULTS,
        "q": "",
        "safeSearch": safe_search,
    }
    _log_diamond_api_call(_YOUTUBE_SEARCH_URL, params)
    search_data = await _youtube_get(session, _YOUTUBE_SEARCH_URL, params)
    items = search_data.get("items") if isinstance(search_data.get("items"), list) else []
    video_ids: List[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        vid = str(((item.get("id") or {}).get("videoId")) or "").strip()
        if len(vid) == 11:
            video_ids.append(vid)
    return video_ids


async def _fetch_video_resources_content_details(
    session: aiohttp.ClientSession,
    api_key: str,
    video_ids: List[str],
) -> List[Dict[str, Any]]:
    """videos.list with contentDetails for duration-aware scoring."""
    if not video_ids:
        return []
    det = await _youtube_get(
        session,
        _YOUTUBE_VIDEOS_URL,
        {
            "key": api_key,
            "part": "snippet,statistics,status,contentDetails",
            "id": ",".join(video_ids),
        },
    )
    return det.get("items") if isinstance(det.get("items"), list) else []


async def _smart_latest_from_channel_net(
    session: aiohttp.ClientSession,
    api_key: str,
    *,
    channel_id: str,
    safe_search: str,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Unchained API net (no videoDuration), top N by order=date, then Python filters + Diamond score.
    Returns the winning videos.list item (full dict) or None.
    """
    params: Dict[str, Any] = {
        "key": api_key,
        "part": "snippet",
        "channelId": channel_id,
        "type": "video",
        "order": "date",
        "maxResults": _SMART_LATEST_NET_MAX_RESULTS,
        "q": "",
        "safeSearch": safe_search,
    }
    assert params["maxResults"] == _SMART_LATEST_NET_MAX_RESULTS
    logger.info(
        "💎 LATEST-VIDEO: order='date' channelId=%s net=%s q='' (chronological channel net)",
        channel_id,
        _SMART_LATEST_NET_MAX_RESULTS,
    )
    _log_diamond_api_call(_YOUTUBE_SEARCH_URL, params)
    search_data = await _youtube_get(session, _YOUTUBE_SEARCH_URL, params)
    items = search_data.get("items") if isinstance(search_data.get("items"), list) else []
    video_ids: List[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        vid = str(((item.get("id") or {}).get("videoId")) or "").strip()
        if len(vid) == 11:
            video_ids.append(vid)
    if not video_ids:
        return None, {"reason": "empty_search"}

    details = await _fetch_video_resources_content_details(session, api_key, video_ids)
    public_details: List[Dict[str, Any]] = []
    for item in details:
        if not isinstance(item, dict):
            continue
        st = item.get("status") if isinstance(item.get("status"), dict) else {}
        if str(st.get("privacyStatus") or "").lower() != "public":
            continue
        public_details.append(item)

    if not public_details:
        return None, {"reason": "no_public"}

    filtered = _apply_smart_filters(public_details)
    if not filtered:
        logger.warning("💎 SMART-LATEST: filters removed all candidates; fallback to unfiltered public list")
        filtered = list(public_details)

    durations: List[Optional[int]] = []
    for it in filtered:
        durations.append(_video_duration_seconds_from_item(it))
    has_non_short_alternative = any((d is not None and d >= 60) for d in durations)

    scored: List[Tuple[float, Dict[str, Any], Optional[int]]] = []
    for item, dsec in zip(filtered, durations):
        sn = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
        pub = str(sn.get("publishedAt") or "")
        score = _diamond_smart_score(
            published_at=pub,
            duration_sec=dsec,
            has_non_short_alternative=has_non_short_alternative,
            smart_meta=item.get("_smart_meta") if isinstance(item.get("_smart_meta"), dict) else None,
        )
        scored.append((score, item, dsec))

    scored.sort(key=lambda t: t[0], reverse=True)
    for score, item, dsec in scored:
        sn = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
        title = str(sn.get("title") or "")
        logger.info(
            "💎 SMART-SCORE: Title='%s', Score=%f (Duration: %s)",
            title,
            score,
            _duration_label_for_log(item, dsec),
        )

    if not scored:
        return None, {"reason": "no_scored"}

    win_score, winner, win_dur = scored[0]
    wsn = winner.get("snippet") if isinstance(winner.get("snippet"), dict) else {}
    logger.info(
        "💎 FINAL SELECTION: '%s' (Published: %s) Diamond=%f",
        str(wsn.get("title") or ""),
        str(wsn.get("publishedAt") or ""),
        win_score,
    )
    meta = {
        "diamond_score": win_score,
        "duration_seconds": win_dur,
        "pipeline": "smart_latest",
    }
    return winner, meta


async def _video_list_pipeline(
    session: aiohttp.ClientSession,
    api_key: str,
    payload: VideoSearchInput,
    selected_channel_id: str,
    channel_hint: str,
    wants_chrono: bool,
    safe_search: str,
    started_at: datetime,
) -> ToolResultV1:
    """
    List-Mode: Liefert N Videos als Liste.

    Strategie:
    1. Channel + keine Filter → playlistItems (günstig, 1 Quota-Unit)
    2. Channel + topic/date Filter → search.list mit channelId (100 Quota-Units)
    3. Kein Channel → search.list global (100 Quota-Units)
    """
    max_results = min(payload.max_results, 15)  # Hard-Cap
    has_topic = bool(payload.topic_query and str(payload.topic_query).strip())
    has_date = bool(payload.published_after or payload.published_before)

    video_ids: List[str] = []

    if selected_channel_id and not has_topic and not has_date:
        # GÜNSTIGSTER PFAD: Upload-Playlist (Absolute Feed Authority für Listen)
        uploads_pl_id = await _channels_uploads_playlist_id(session, api_key, selected_channel_id)
        if uploads_pl_id:
            video_ids = await _playlist_items_get_videos(session, api_key, uploads_pl_id, max_results=max_results)
            logger.info("💎 LIST-MODE: Feed-Authority path, got %d videos from uploads playlist", len(video_ids))

    if not video_ids:
        # SEARCH API (teurer, aber Filter-fähig)
        search_params: Dict[str, Any] = {
            "key": api_key,
            "part": "snippet",
            "type": "video",
            "maxResults": max_results,
            "safeSearch": safe_search,
            "order": "date" if wants_chrono else "relevance",
        }
        if selected_channel_id:
            search_params["channelId"] = selected_channel_id
        if has_topic:
            search_params["q"] = str(payload.topic_query).strip()
        elif str(payload.query or "").strip():
            search_params["q"] = str(payload.query).strip()
        if payload.published_after:
            search_params["publishedAfter"] = _to_rfc3339(payload.published_after)
        if payload.published_before:
            search_params["publishedBefore"] = _to_rfc3339(payload.published_before)

        _log_diamond_api_call(_YOUTUBE_SEARCH_URL, search_params)
        search_data = await _youtube_get(session, _YOUTUBE_SEARCH_URL, search_params)
        items = search_data.get("items") if isinstance(search_data.get("items"), list) else []
        video_ids = [
            str(((it.get("id") or {}).get("videoId")) or "").strip()
            for it in items if isinstance(it, dict)
        ]
        video_ids = [vid for vid in video_ids if len(vid) == 11]
        logger.info("💎 LIST-MODE: Search API path, got %d video IDs", len(video_ids))

    if not video_ids:
        raise RuntimeError("NO_VIDEO_RESULTS")

    # Details abrufen
    details = await _youtube_get(session, _YOUTUBE_VIDEOS_URL, {
        "key": api_key,
        "part": "snippet,statistics,status",
        "id": ",".join(video_ids),
    })
    detail_items = details.get("items") if isinstance(details.get("items"), list) else []

    # VideoResult-Objekte bauen
    results: List[VideoResult] = []
    for item in detail_items:
        if not isinstance(item, dict):
            continue
        status = item.get("status") if isinstance(item.get("status"), dict) else {}
        if str(status.get("privacyStatus") or "").lower() != "public":
            continue
        # v0.4.16-beta.7: Drop non-embeddable videos. YouTube reports these via
        # status.embeddable=false. Embedding them leads to Error 101/150/153 in
        # the iframe player. Filtering upstream keeps the UI clean.
        if not bool(status.get("embeddable")):
            logger.debug("VIDEO-SEARCH: skipping non-embeddable video id=%s", item.get("id"))
            continue
        snippet = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
        stats = item.get("statistics") if isinstance(item.get("statistics"), dict) else {}
        vid = str(item.get("id") or "").strip()
        title = str(snippet.get("title") or "").strip()
        if len(vid) != 11 or not title:
            continue
        results.append(VideoResult(
            video_id=vid,
            title=title,
            channel=str(snippet.get("channelTitle") or "").strip(),
            views=_safe_int(stats.get("viewCount"), 0),
            thumbnail=str(
                ((snippet.get("thumbnails") or {}).get("high") or {}).get("url")
                or ((snippet.get("thumbnails") or {}).get("medium") or {}).get("url")
                or ""
            ).strip(),
            watch_url=f"https://www.youtube.com/watch?v={vid}",
            embed_url=f"https://www.youtube.com/embed/{vid}?rel=0",
            is_embeddable=bool(status.get("embeddable")),
            published_date_human=_format_published_date_human(str(snippet.get("publishedAt") or "")),
        ))

    if not results:
        raise RuntimeError("NO_VIDEO_RESULTS")

    output = VideoSearchOutput(
        videos=results,
        count=len(results),
        mode=str(payload.mode or "single"),
        query=str(payload.query or "").strip(),
        retrieved_at=started_at.isoformat(),
    )
    return ToolResultV1(
        status="ok",
        data=output.model_dump(),
        message=_build_video_markdown_output([v.model_dump() for v in results]),
        is_final_response=True,
        metadata={
            "source": "youtube_data_api_v3",
            "pipeline": "video_list",
            "mode": str(payload.mode or "single"),
            "max_results_requested": payload.max_results,
            "actual_count": len(results),
            "has_topic_filter": has_topic,
            "has_date_filter": has_date,
            "channel_id": selected_channel_id or None,
        },
    )


async def video_search_tool(args: VideoSearchInput) -> ToolResultV1:
    started_at = datetime.now(timezone.utc)
    try:
        payload = VideoSearchInput.model_validate(args)
        api_key = _get_youtube_api_key()
        if not api_key:
            raise RuntimeError("YOUTUBE_API_KEY_MISSING")

        raw_query = str(payload.query or "").strip()

        # ── OLLAMA SAFETY: Mode-Validierung und Plural-Heuristik ────────────
        raw_mode = str(getattr(payload, 'mode', 'single')).strip().lower()
        if raw_mode not in ('single', 'list'):
            raw_mode = 'single'
        # Heuristic override für schwache Modelle: Plural-Erkennung
        if raw_mode == 'single':
            q_lower = raw_query.lower()
            plural_signals = re.search(r'\b(?:letzten|letzte)\s+\d+\s+video', q_lower)
            multi_signals = any(tok in q_lower for tok in ('alle videos', 'mehrere videos', 'videos von', 'video liste'))
            if plural_signals or multi_signals:
                logger.info("💎 OLLAMA-SAFETY: mode='single' overridden to 'list' by plural heuristic")
                raw_mode = 'list'
        is_list_mode = (raw_mode == 'list')
        # ───────────────────────────────────────────────────────────────────

        # ABSOLUTE FEED AUTHORITY: Explicit channel_name from LLM takes precedence
        explicit_channel = str(payload.channel_name or "").strip() if payload.channel_name else ""
        extracted_hint = ""
        if not explicit_channel and _query_has_channel_intent(raw_query):
            candidate_hint = _extract_channel_hint(raw_query)
            if candidate_hint and _is_geo_rejected_hint(candidate_hint):
                logger.info(
                    "💎 GEO-GUARD: rejected auto-extracted channel hint '%s' -> forcing global search",
                    candidate_hint,
                )
            else:
                extracted_hint = candidate_hint
        channel_resolve_name = explicit_channel or extracted_hint.strip()
        # Channel-Intent = wenn wir einen validen Kanalnamen haben (explicit oder extrahiert)
        channel_intent = bool(channel_resolve_name)
        channel_hint = channel_resolve_name
        if explicit_channel:
            logger.info("💎 EXPLICIT-CHANNEL: LLM lieferte channel_name='%s'", explicit_channel)
        wants_recency_keywords = _query_wants_recency(raw_query)
        wants_chrono = bool(payload.wants_latest) or wants_recency_keywords
        search_order = "date" if wants_chrono else "relevance"
        # NUCLEAR FIX: Tutorial-Suffix immer unterdrücken bei wants_latest (nicht nur bei channel_intent)
        query = _normalize_query(raw_query, suppress_tutorial_suffix=bool(channel_intent or payload.wants_latest))
        if channel_intent:
            api_query = query
        else:
            api_query = _refine_search_query(query, extracted_hint or "")
        selected_channel_id = ""
        channel_cache_src = ""
        safe_search = "strict" if payload.safe_search else "none"
        used_uploads_playlist = False
        smart_latest_meta: Dict[str, Any] = {}

        # ── LIST MODE BRANCH ────────────────────────────────────────────────
        if is_list_mode:
            async with aiohttp.ClientSession() as session:
                # Channel-Resolution für List-Mode
                if channel_intent and channel_hint:
                    clean_hint = _clean_channel_hint_for_resolution(channel_hint)
                    if clean_hint and clean_hint != channel_hint:
                        logger.info("💎 HINT-STRIP: '%s' -> '%s'", channel_hint, clean_hint)
                        channel_hint = clean_hint
                    selected_channel_id, channel_cache_src = await _resolve_channel_id(
                        session, api_key, channel_hint, safe_search
                    )

                result = await _video_list_pipeline(
                    session=session,
                    api_key=api_key,
                    payload=payload,
                    selected_channel_id=selected_channel_id,
                    channel_hint=channel_hint,
                    wants_chrono=wants_chrono,
                    safe_search=safe_search,
                    started_at=started_at,
                )
                # Add Markdown output for LLM JSON-blindness fix
                if result.status == "ok" and isinstance(result.data, dict):
                    videos = result.data.get("videos", [])
                    markdown_output = _build_video_markdown_output(videos)
                    result.message = markdown_output
                return result
        # ── SINGLE MODE (bestehend, unverändert) ────────────────────────────

        async with aiohttp.ClientSession() as session:
            if channel_intent and channel_hint:
                # NUCLEAR STRIP: Bereinige den Hint von Kontext-Wörtern
                clean_hint = _clean_channel_hint_for_resolution(channel_hint)
                if clean_hint and clean_hint != channel_hint:
                    logger.info("💎 HINT-STRIP: '%s' -> '%s'", channel_hint, clean_hint)
                    channel_hint = clean_hint
                
                logger.info("💎 MODE: CHANNEL_LOCK for '%s'", channel_hint)
                selected_channel_id, channel_cache_src = await _resolve_channel_id(
                    session, api_key, channel_hint, safe_search
                )
            else:
                logger.info("💎 MODE: GLOBAL_SEARCH")

            if channel_intent and not selected_channel_id:
                logger.info("💎 MODE: GLOBAL_SEARCH (channel resolve failed)")

            if selected_channel_id:
                strat = "ch_latest" if wants_chrono else "ch_topic"
            else:
                strat = "search"
            cache_key = _video_cache_key(
                query=f"{api_query}|cid={selected_channel_id}|strat={strat}",
                safe_search=payload.safe_search,
                max_results=payload.max_results,
                min_views=payload.min_views,
                order=search_order,
            )
            # CACHE-CONTROL: Bei wants_latest Cache ignorieren (max 120s TTL bei Store)
            if not wants_chrono:
                cached_result = _get_cached_video_result(cache_key)
                if cached_result is not None:
                    logger.info(
                        "💎 [VIDEO-CACHE] Hit for: '%s'",
                        f"{api_query}|cid={selected_channel_id}|order={search_order}|strat={strat}",
                    )
                    return cached_result
            else:
                logger.info("💎 CACHE-BYPASS: wants_latest=true, skipping cache lookup")

            detail_items: List[Dict[str, Any]] = []

            async def _fetch_details_for_ids(vids: List[str]) -> List[Dict[str, Any]]:
                if not vids:
                    return []
                det = await _youtube_get(
                    session,
                    _YOUTUBE_VIDEOS_URL,
                    {
                        "key": api_key,
                        "part": "snippet,statistics,status",
                        "id": ",".join(vids),
                    },
                )
                return det.get("items") if isinstance(det.get("items"), list) else []

            # ── ABSOLUTE FEED AUTHORITY ──────────────────────────────────
            # When wants_latest + channel resolved: grab index-0 from uploads
            # playlist and return IMMEDIATELY (no ranking, no scoring).
            # This is the ONLY reliable way to beat YouTube search bias.
            # ──────────────────────────────────────────────────────────────
            feed_authority_result: Optional[ToolResultV1] = None

            if selected_channel_id and wants_chrono:
                logger.info(
                    "💎 ABSOLUTE-FEED-AUTHORITY: Channel '%s' (ID: %s) + wants_latest=true",
                    channel_hint,
                    selected_channel_id,
                )
                used_uploads_playlist = True
                uploads_pl_id = await _channels_uploads_playlist_id(
                    session, api_key, selected_channel_id
                )
                if uploads_pl_id:
                    # Index 0 = physikalisch neuestes Video
                    playlist_video_ids = await _playlist_items_get_videos(
                        session, api_key, uploads_pl_id, max_results=3
                    )
                    if playlist_video_ids:
                        logger.info(
                            "💎 FEED-AUTHORITY: %d Videos aus Upload-Playlist (Top-3)",
                            len(playlist_video_ids),
                        )
                        feed_details = await _fetch_details_for_ids(playlist_video_ids)
                        # Pick first public, non-upcoming, non-short video
                        for fd_item in feed_details:
                            if not isinstance(fd_item, dict):
                                continue
                            fd_status = fd_item.get("status") if isinstance(fd_item.get("status"), dict) else {}
                            if str(fd_status.get("privacyStatus") or "").lower() != "public":
                                continue
                            fd_sn = fd_item.get("snippet") if isinstance(fd_item.get("snippet"), dict) else {}
                            fd_title = str(fd_sn.get("title") or "").strip()
                            if "#shorts" in fd_title.lower():
                                continue
                            fd_lbc = str(fd_sn.get("liveBroadcastContent") or "none").lower()
                            if fd_lbc == "upcoming":
                                continue
                            fd_vid = str(fd_item.get("id") or "").strip()
                            if len(fd_vid) != 11 or not fd_title:
                                continue
                            fd_stats = fd_item.get("statistics") if isinstance(fd_item.get("statistics"), dict) else {}
                            fd_views = _safe_int(fd_stats.get("viewCount"), 0)
                            fd_thumb = str(
                                ((fd_sn.get("thumbnails") or {}).get("high") or {}).get("url")
                                or ((fd_sn.get("thumbnails") or {}).get("medium") or {}).get("url")
                                or ((fd_sn.get("thumbnails") or {}).get("default") or {}).get("url")
                                or ""
                            ).strip()
                            fd_channel = str(fd_sn.get("channelTitle") or "").strip()
                            fd_pub = str(fd_sn.get("publishedAt") or "").strip()
                            fd_embeddable = bool(fd_status.get("embeddable"))
                            logger.info(
                                "💎 ABSOLUTE-FEED-AUTHORITY WINNER: '%s' by '%s' (Published: %s, ID: %s)",
                                fd_title, fd_channel, fd_pub, fd_vid,
                            )
                            best_video = VideoResult(
                                video_id=fd_vid,
                                title=fd_title,
                                channel=fd_channel,
                                views=fd_views,
                                thumbnail=fd_thumb,
                                watch_url=f"https://www.youtube.com/watch?v={fd_vid}",
                                embed_url=f"https://www.youtube.com/embed/{fd_vid}?rel=0",
                                is_embeddable=fd_embeddable,
                                published_date_human=_format_published_date_human(fd_pub),
                            )
                            output = VideoSearchOutput(
                                selected_video=best_video,
                                query=query,
                                retrieved_at=started_at.isoformat(),
                            )
                            output_dict = output.model_dump()
                            videos_list = [output_dict.get("selected_video", {})]
                            markdown_output = _build_video_markdown_output(videos_list)
                            feed_authority_result = ToolResultV1(
                                status="ok",
                                data={
                                    "videos": videos_list,
                                    "count": len(videos_list),
                                    "mode": "list",
                                    "query": query,
                                    "retrieved_at": started_at.isoformat(),
                                },
                                message=markdown_output,
                                is_final_response=True,
                                metadata={
                                    "source": "youtube_data_api_v3",
                                    "pipeline": "absolute_feed_authority",
                                    "search_order": "uploads_playlist_index_0",
                                    "selected_published_at": fd_pub,
                                    "uploads_playlist_resolver": True,
                                    "channel_resolver_cache": channel_cache_src,
                                    "wants_latest": True,
                                    "wants_chrono_effective": True,
                                },
                            )
                            _store_cached_video_result(cache_key, feed_authority_result, ttl=_LATEST_CACHE_TTL_SECONDS)
                            break
                    else:
                        logger.warning("💎 FEED-AUTHORITY: Keine Videos in Upload-Playlist")
                else:
                    logger.warning("💎 FEED-AUTHORITY: Keine Upload-Playlist für Kanal %s", selected_channel_id)

            # Early return if feed authority succeeded
            if feed_authority_result is not None:
                return feed_authority_result

            # ── STANDARD CHANNEL PATH (non-latest or feed-authority fallback) ─
            if selected_channel_id:
                logger.info(
                    "💎 FEED-STANDARD: Nutze Upload-Playlist für '%s' (ID: %s)",
                    channel_hint,
                    selected_channel_id
                )
                used_uploads_playlist = True
                uploads_pl_id = await _channels_uploads_playlist_id(
                    session, api_key, selected_channel_id
                )
                if uploads_pl_id:
                    playlist_video_ids = await _playlist_items_get_videos(
                        session, api_key, uploads_pl_id, max_results=5
                    )
                    if playlist_video_ids:
                        logger.info(
                            "💎 FEED-STANDARD: %d Videos aus Upload-Playlist geladen",
                            len(playlist_video_ids)
                        )
                        detail_items = await _fetch_details_for_ids(playlist_video_ids)
                    else:
                        logger.warning("💎 FEED-STANDARD: Keine Videos in Upload-Playlist")
                else:
                    logger.warning("💎 FEED-STANDARD: Keine Upload-Playlist für Kanal %s", selected_channel_id)
                
                # Fallback nur wenn Playlist völlig leer
                if not detail_items:
                    logger.info("💎 FEED-STANDARD-FALLBACK: Versuche Search-API (nur bei leerer Playlist)")
                    video_ids_ch = await _search_list_in_channel_by_date(
                        session,
                        api_key,
                        channel_id=selected_channel_id,
                        safe_search=safe_search,
                    )
                    detail_items = await _fetch_details_for_ids(video_ids_ch)
                
                if not detail_items:
                    logger.warning(
                        "💎 FEED-STANDARD: Keine Videos für Kanal %s gefunden",
                        selected_channel_id,
                    )

            # GLOBAL SEARCH: Nur wenn KEIN Kanal erkannt wurde
            if not selected_channel_id and not detail_items:
                logger.info("💎 MODE: GLOBAL_SEARCH (kein Kanal erkannt)")
                logger.info("💎 SEARCH_ORDER: %s", search_order)
                
                global_params: Dict[str, Any] = {
                    "key": api_key,
                    "part": "snippet",
                    "type": "video",
                    "maxResults": payload.max_results,
                    "safeSearch": safe_search,
                    "order": "date" if wants_chrono else "relevance",
                    "q": api_query if str(api_query or "").strip() else raw_query,
                }
                _log_diamond_api_call(_YOUTUBE_SEARCH_URL, global_params)
                search_data = await _youtube_get(session, _YOUTUBE_SEARCH_URL, global_params)
                items = search_data.get("items") if isinstance(search_data.get("items"), list) else []
                video_ids = [
                    str(((item.get("id") or {}).get("videoId")) or "").strip()
                    for item in items
                    if isinstance(item, dict)
                ]
                video_ids = [vid for vid in video_ids if len(vid) == 11]
                if not video_ids:
                    raise RuntimeError("NO_VIDEO_RESULTS")

                details = await _youtube_get(
                    session,
                    _YOUTUBE_VIDEOS_URL,
                    {
                        "key": api_key,
                        "part": "snippet,statistics,status",
                        "id": ",".join(video_ids),
                    },
                )
                detail_items = details.get("items") if isinstance(details.get("items"), list) else []

        relax_min_views = used_uploads_playlist or (bool(selected_channel_id) and wants_chrono)

        best: Optional[VideoResult] = None
        best_score = -1.0
        best_published_at = ""
        ranking_log: List[Dict[str, Any]] = []
        for item in detail_items:
            if not isinstance(item, dict):
                continue
            status = item.get("status") if isinstance(item.get("status"), dict) else {}
            if str(status.get("privacyStatus") or "").lower() != "public":
                continue

            snippet = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
            stats = item.get("statistics") if isinstance(item.get("statistics"), dict) else {}

            video_id = str(item.get("id") or "").strip()
            title = str(snippet.get("title") or "").strip()
            channel = str(snippet.get("channelTitle") or "").strip()
            thumbnail = str(
                ((snippet.get("thumbnails") or {}).get("high") or {}).get("url")
                or ((snippet.get("thumbnails") or {}).get("medium") or {}).get("url")
                or ((snippet.get("thumbnails") or {}).get("default") or {}).get("url")
                or ""
            ).strip()
            views = _safe_int(stats.get("viewCount"), 0)
            subscribers = 0
            is_embeddable = bool(status.get("embeddable"))
            published_at = str(snippet.get("publishedAt") or "").strip()

            if not relax_min_views and views < payload.min_views:
                continue
            if len(video_id) != 11 or not title:
                continue
            # v0.4.16-beta.7: Skip non-embeddable videos (status.embeddable=false)
            # to avoid Error 101/150/153 in the iframe player.
            if not is_embeddable:
                logger.debug("VIDEO-SEARCH (single): skipping non-embeddable id=%s", video_id)
                continue

            score = _rank_video(
                query=query,
                channel_hint=channel_hint,
                title=title,
                channel_title=channel,
                published_at=published_at,
                views=views,
                subscriber_count=subscribers,
                wants_recency=wants_chrono,
            )
            logger.debug(
                "VIDEO-SEARCH ranking: id=%s relevance=%.3f channel_match=%.3f views=%d embeddable=%s score=%.3f",
                video_id,
                _token_overlap_score(query, title, channel),
                _channel_match_score(channel, channel_hint),
                views,
                is_embeddable,
                score,
            )
            ranking_log.append({"channel": channel, "title": title, "score": score, "published_at": published_at})
            if score > best_score:
                best_score = score
                best_published_at = published_at
                best = VideoResult(
                    video_id=video_id,
                    title=title,
                    channel=channel,
                    views=views,
                    thumbnail=thumbnail,
                    watch_url=f"https://www.youtube.com/watch?v={video_id}",
                    embed_url=f"https://www.youtube.com/embed/{video_id}?rel=0",
                    is_embeddable=is_embeddable,
                    published_date_human=_format_published_date_human(published_at),
                )

        for row in sorted(ranking_log, key=lambda r: float(r.get("score", 0.0)), reverse=True)[:3]:
            logger.info(
                "💎 RANKING: Kanal='%s', Titel='%s', publishedAt='%s', Score=%f",
                str(row.get("channel") or ""),
                str(row.get("title") or ""),
                str(row.get("published_at") or ""),
                float(row.get("score") or 0.0),
            )

        if best:
            logger.info("💎 SELECTED: publishedAt='%s'", best_published_at)

        if not best:
            raise RuntimeError("NO_VIDEO_FOUND")

        output = VideoSearchOutput(
            selected_video=best,
            query=query,
            retrieved_at=started_at.isoformat(),
        )
        output_dict = output.model_dump()
        videos_list = [output_dict.get("selected_video", {})]
        markdown_output = _build_video_markdown_output(videos_list)
        result = ToolResultV1(
            status="ok",
            data={
                "videos": videos_list,
                "count": len(videos_list),
                "mode": "list",
                "query": query,
                "retrieved_at": started_at.isoformat(),
            },
            message=markdown_output,
            is_final_response=True,
            metadata={
                "source": "youtube_data_api_v3",
                "score": round(best_score, 4),
                "search_order": search_order,
                "selected_published_at": best_published_at,
                "uploads_playlist_resolver": used_uploads_playlist,
                "channel_resolver_cache": channel_cache_src,
                "wants_latest": bool(payload.wants_latest),
                "wants_chrono_effective": wants_chrono,
                "smart_latest": smart_latest_meta if smart_latest_meta else None,
            },
        )
        effective_ttl = _LATEST_CACHE_TTL_SECONDS if wants_chrono else _VIDEO_CACHE_TTL_SECONDS
        _store_cached_video_result(cache_key, result, ttl=effective_ttl)
        return result
    except Exception as exc:
        logger.error("VIDEO-SEARCH failed: %s", exc, exc_info=True)
        return ToolResultV1(
            status="error",
            data={},
            error=ToolErrorDetails(code="VIDEO_SEARCH_FAILED", message=str(exc)),
        )
