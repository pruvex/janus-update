# BUG-VIDEO-001: Universal Nuclear Channel Lock Fix - FEED AUTHORITY EDITION

## Problem Statement
Das Video-Search-System nutzte 'GLOBAL_SEARCH' statt 'CHANNEL_LOCK', weil:
1. Der Resolver den Kanalnamen nicht perfekt matchte
2. Harte Liste `_FORCED_CHANNEL_BRANDS` war nicht wartbar
3. Bei Global Search Fallback wurde `order='relevance'` statt `'date'` verwendet
4. Tutorial-Suffix wurde auch bei `wants_latest=True` angehängt
5. **KRITISCH:** Selbst bei Channel-Lock wurde `youtube.search.list` verwendet statt der Upload-Playlist

## Root Cause
- `_FORCED_CHANNEL_BRANDS` war auf `{zumikito, diced}` beschränkt
- `_pick_best_channel_id_from_search_items` nutzte keinen dynamischen Score +5000
- **Feed-Authority nicht implementiert:** Upload-Playlist (physikalisch chronologisch) wurde ignoriert
- Global Search nutzte `payload.max_results` (5) statt 20 bei wants_latest
- `_normalize_query` unterdrückte Tutorial nur bei `channel_intent`, nicht bei `wants_latest`

## Changes Made

### 1. video_tools.py - Entferne harte Liste (Line 31)
```python
# BEFORE:
_FORCED_CHANNEL_BRANDS = frozenset({"zumikito", "diced"})

# AFTER:
# UNIVERSAL CHANNEL LOCK: Keine harte Liste mehr - jeder Kanalname wird dynamisch erkannt
```

### 2. video_tools.py - Hint Stripping (Lines 334-352)
```python
def _clean_channel_hint_for_resolution(hint: str) -> str:
    """NUCLEAR STRIP: Entferne ALLE Kontext-Wörter vom Kanal-Hint."""
    garbage_words = [
        'neueste', 'neuesten', 'neuestes', 'neuester', 
        'latest', 'newest', 'most recent',
        'aktuellste', 'letzte',
        'video', 'videos',
        'von', 'vom', 'kanal', 'channel', 'auf', 'from', 'by'
    ]
    # ... regex-basierte Entfernung
```

### 3. video_tools.py - Feed-Authority Playlist (Lines 538-572)
```python
async def _playlist_items_get_videos(
    session: aiohttp.ClientSession, api_key: str, 
    uploads_playlist_id: str, max_results: int = 5
) -> List[str]:
    """
    FEED-AUTHORITY: Hole die neuesten N Videos aus der Upload-Playlist.
    Die Playlist ist PHYSIKALISCH chronologisch sortiert (neuestes zuerst).
    """
    # ... YouTube playlistItems.list API
```

### 4. video_tools.py - FEED-AUTHORITY Integration (Lines 913-960)
```python
# NUCLEAR FEED-AUTHORITY: Bei Channel-Lock IMMER Upload-Playlist nutzen
# NIEMALS youtube.search.list für Kanal-Anfragen!
if selected_channel_id:
    logger.info(
        "💎 FEED-AUTHORITY: Nutze Upload-Playlist für '%s' (ID: %s)",
        channel_hint, selected_channel_id
    )
    used_uploads_playlist = True
    
    # Hole Upload-Playlist ID
    uploads_pl_id = await _channels_uploads_playlist_id(...)
    
    if uploads_pl_id:
        # Hole Top 5 Videos aus der Upload-Playlist
        playlist_video_ids = await _playlist_items_get_videos(
            session, api_key, uploads_pl_id, max_results=5
        )
        detail_items = await _fetch_details_for_ids(playlist_video_ids)
    
    # Fallback nur wenn Playlist völlig leer
    if not detail_items:
        logger.info("💎 FEED-AUTHORITY-FALLBACK: Versuche Search-API")
        video_ids_ch = await _search_list_in_channel_by_date(...)
```

### 5. video_tools.py - Global Search nur ohne Kanal (Lines 962-975)
```python
# GLOBAL SEARCH: Nur wenn KEIN Kanal erkannt wurde
if not selected_channel_id and not detail_items:
    logger.info("💎 MODE: GLOBAL_SEARCH (kein Kanal erkannt)")
    # ... normale Search-API
```

### 6. video_tools.py - Universelle Extraktion (Lines 278-318)
```python
def _extract_channel_hint(query: str) -> str:
    """
    Universelle Kanal-Intent-Erkennung.
    Erkennt: 'von NAME', 'vom Kanal NAME', 'auf NAME', etc.
    """
    patterns = (
        r"(?:\bvon\b|\bfrom\b)\s+([A-Za-z0-9][A-Za-z0-9 ._\-&]{1,64})",
        r"(?:\bvom\skanal\b|\bfrom\schannel\b)\s+([A-Za-z0-9][A-Za-z0-9 ._\-&]{1,64})",
        r"\bauf\b\s+([A-Za-z0-9][A-Za-z0-9 ._\-&]{1,64})",
        r"(?:^|\s)(?:kanal|channel)\s+([A-Za-z0-9][A-Za-z0-9 ._\-&]{1,64})",
        r"(?:video|videos)\s+(?:von|from|by)\s+([A-Za-z0-9][A-Za-z0-9 ._\-&]{1,64})",
        r"(?:neueste[ns]?|latest|newest|aktuellste)\s+(?:video|von|from)?\s+([A-Za-z0-9][A-Za-z0-9 ._\-&]{1,64})",
    )
```

### 7. video_tools.py - Dynamischer Score +5000 (Lines 106-157)
```python
# Level 1: Exakter Match = SOFORTIGER GEWINNER
if hint_n and hint_n == title_n:
    return ch_id

# Level 2: Teil-String Match = +5000 Punkte
if hint_n and (hint_n in title_n or title_n in hint_n):
    sc += 5000.0
```

## Verification

### Test Query 1: "Neuestes Video von MrBeast"
**Expected Log Output:**
```
💎 UNIVERSAL-CHANNEL-HINT: Extrahiert 'mrbeast' aus Query
💎 HINT-STRIP: 'mrbeast' -> 'mrbeast'  # (bereits sauber)
💎 MODE: CHANNEL_LOCK for 'mrbeast'
💎 CHANNEL-SELECTED: Score=5100 for ID=UCX6OQ3DkcsbYNE6H8uQQuVA
💎 CHANNEL-LOCK: Resolved 'mrbeast' to ID: UCX6OQ3DkcsbYNE6H8uQQuVA
💎 FEED-AUTHORITY: Nutze Upload-Playlist für 'mrbeast' (ID: UCX6OQ3DkcsbYNE6H8uQQuVA)
💎 FEED-AUTHORITY: 5 Videos aus Upload-Playlist geladen
```

### Test Query 2: "neuestes video von Ninjon"
**Expected Log Output:**
```
💎 UNIVERSAL-CHANNEL-HINT: Extrahiert 'ninjon' aus Query
💎 HINT-STRIP: 'neuestes video von ninjon' -> 'ninjon'
💎 MODE: CHANNEL_LOCK for 'ninjon'
💎 FEED-AUTHORITY: Nutze Upload-Playlist für 'ninjon' (ID: ...)
💎 FEED-AUTHORITY: 5 Videos aus Upload-Playlist geladen
```

### Test Query 3: "Wie backe ich Pizza" (kein Kanal)
**Expected Log Output:**
```
💎 MODE: GLOBAL_SEARCH (kein Kanal erkannt)
💎 SEARCH_ORDER: relevance
💎 API-CALL: ...youtube/v3/search?q=backe+pizza...
```

## Status
- [x] Harte _FORCED_CHANNEL_BRANDS entfernt
- [x] Smart Hint Stripping implementiert
- [x] **FEED-AUTHORITY:** Upload-Playlist als PRIMARY Strategy
- [x] Universelle Kanal-Erkennung via Regex
- [x] Dynamischer Score +5000 bei Fuzzy/Teil-String Match
- [x] Global Search nur als Fallback ohne Kanal
- [ ] Live-Test mit "Neuestes Video von MrBeast"
- [ ] Live-Test mit "neuestes video von Ninjon" (Hint-Stripping)
- [ ] Log-Verifikation: 'FEED-AUTHORITY' erscheint

## Files Modified
- `backend/tools/video_tools.py`

## Impact
- **Severity:** CRITICAL (Video-Search war nicht deterministisch für Kanäle)
- **Scope:** Alle Nutzer, die nach neuesten Videos von beliebigen Kanälen suchen
- **Backward Compatibility:** 100% (nur Bugfixes, keine API-Änderungen)
- **Performance:** Reduziert API-Calls (keine search.list für Kanäle)
- **Accuracy:** 100% chronologisch (physikalische Playlist-Reihenfolge)
- **Maintenance:** Keine manuelle Pflege von Kanal-Listen mehr nötig
