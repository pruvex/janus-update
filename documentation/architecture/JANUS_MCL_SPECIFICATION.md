# JANUS MCL SPECIFICATION — Final Sealed Document

**Version:** 1.0.0  
**Status:** 🥇 **SEALED & COMPLETE**  
**Date:** 2026-04-14  
**Epic:** Universal Modal System (Task 029-034)  

---

## 1. System Definition

### 1.1 Purpose

Das **Modal Contract Layer (MCL)** ist die zentrale Architekturkomponente für alle visuellen Ausgaben in Janus. Es definiert den einzigen validen Pfad, über den Skills und Backend-Logik mit der UI kommunizieren.

> 💎 **Core Value:** *Kein Feature spricht direkt mit der UI — alles geht durch einen klaren, stabilen Contract Layer.*

### 1.2 Position im System Stack

```
[ Skills / AI Logic / Backend ]
           ↓
   💎 MCL (Modal Contract Layer)
           ↓
[ Universal Modal System — UI Runtime ]
           ↓
[ Renderers (Video / Image / PDF / Tools) ]
           ↓
[ UI Output — DOM / React ]
```

---

## 2. Core Principles

### 2.1 Stateless Architecture

- **MCL hat KEINEN eigenen State** — Single Source of Truth ist `window-state.js`
- Alle State-Änderungen laufen über `registerDockModule()` / `updateDockModuleState()`
- Keine parallelen Modal-Maps im Frontend erlaubt

### 2.2 Strict Contract Enforcement

- Nur validierte `modal_request` Objekte werden verarbeitet
- Kein direkter UI-Zugriff aus Skills
- Bidirektionale State-Synchronisation via Event-System

### 2.3 Separation of Concerns

| Layer | Responsibility |
|-------|---------------|
| Skills | Entscheidung & Daten |
| MCL | Übersetzung & Routing |
| Modal System | Rendering & Window Behavior |

---

## 3. Modal Contract API

### 3.1 Backend → Frontend: `modal_request` Schema

```json
{
  "modal_request": {
    "type": "video | image | document | gallery | image-studio",
    "payload": {
      // Type-spezifische Daten
    },
    "options": {
      "auto_open": true,
      "pinnable": true,
      "draggable": true,
      "resizable": true
    }
  }
}
```

**Integration in Chat-Response:**
- `backend/data/schemas.py`: `ModalRequest` Pydantic-Schema
- `backend/services/orchestrator/execution_engine.py`: Generiert `modal_request` aus Tool-Results
- `frontend/js/chat.js`: `appendMessage()` erkennt `modal_request` und ruft `openModal()`

### 3.2 Frontend API: `modal-api.js`

```javascript
// Open Modal
openModal({
  type: 'video',                    // Renderer-Typ
  payload: { videoId, title, url }, // Content-Daten
  options: { auto_open: true }      // Verhaltens-Flags
});

// Close / Minimize / Focus
closeModal(modalId);           // Schließt Modal, entfernt Embed
minimizeModal(modalId);        // Minimiert zu Taskbar
bringToFront(modalId);         // Hebt Z-Index an (Z-Stack)

// Event System
subscribeWindowState(callback);  // State-Änderungen abonnieren
emitModalEvent(modalId, event, context);  // Events publizieren
```

### 3.3 Renderer Mapping

```javascript
const RENDERER_MAP = {
  "document":      "knowledge-center",   // PDF/Text-Dokumente
  "image-studio":  "image-studio",       // Bildgenerierung
  "gallery":       "gallery",            // Bildergalerie
  "video":         "video-player",       // YouTube/Vimeo Embed
  "image":         "image-viewer",       // Bild-Vollansicht
};

const DOCK_HOST_ELEMENT_IDS = {
  "knowledge-center": "knowledge-center-panel",
  "image-studio":     "image-studio-modal",
  "gallery":          "gallery-window",
  "video-player":     "video-player-modal",
  "image-viewer":     "image-modal",
};
```

---

## 4. Z-Index Management (Z-Stack)

### 4.1 Layer Architecture

| Layer | Z-Base | Purpose |
|-------|--------|---------|
| Chat Panes | 50 | Standard-Chat-Fenster |
| Dock Modules | 100 | Alle MCL-verwalteten Modals |
| Fullscreen Overlays | 10000 | Legacy Image Overlay (veraltet) |

### 4.2 Z-Stack Logic

```javascript
const Z_BASE = 100;
let zCounter = Z_BASE;

function bringToFront(modalId) {
  zCounter += 1;
  updateDockModuleZIndex(modalId, zCounter);
}
```

- Klick auf Panel → `bringToFront()` → Z-Index steigt
- Focus-to-Front bei jedem `mousedown` Event
- Keine hartkodierten `zIndex: 9999` mehr

---

## 5. FIFO-Guard: Max-Modals-Limit

### 5.1 Soft-Limit 4

```javascript
const MAX_VISIBLE_MODALS = 4;

function enforceMaxModals(excludeModuleId) {
  const modules = getWindowState()?.dock?.modules || {};
  const visibleModules = Object.entries(modules)
    .filter(([id, m]) => id !== excludeModuleId && m.isOpen && !m.minimized)
    .sort((a, b) => (a[1].zIndex || 0) - (b[1].zIndex || 0));

  if (visibleModules.length >= MAX_VISIBLE_MODALS) {
    const [oldestId] = visibleModules[0];  // Niedrigster Z-Index = ältestes
    dockMinimize(oldestId, true);
    console.log(`[MCL] Max modals reached (${MAX_VISIBLE_MODALS}), minimized: ${oldestId}`);
  }
}
```

- 5. Modal öffnen → ältestes wird automatisch minimiert
- Minimierte Module erscheinen in Taskbar

---

## 6. Escape-Key Handling

- Globaler `keydown` Listener auf `document`
- `Escape` → Schließt oberstes Modal (höchster Z-Index)
- Kaskadiert durch offene Modals falls mehrere sichtbar

---

## 7. Video Search Integration

### 7.1 Backend: Video Search Skill

**API Contract:**
- Input: `{ query: string, max_results: int, min_views: int }`
- Output: `{ selected_video: { video_id, title, channel, views, thumbnail, embed_url } }`

**Cache-Mechanismus:**
```python
# backend/tools/video_tools.py
VIDEO_CACHE_TTL = 3600  # 1 Stunde
_cache = {}  # In-Memory Cache für identische Queries
```

**Log-Signale:**
- `💎 [VIDEO-CACHE] Hit for: <query>` — Cache-Treffer
- `VIDEO-SEARCH: Using YOUTUBE_API_KEY from environment.` — API-Key OK
- `💎 TOOL CALL ATTEMPT: video.search with args {...}` — Skill-Invocation
- `💎 TOOL CALL RESULT: {"status": "ok", ...}` — Erfolgreiche Ausführung

### 7.2 Frontend: Video Player Renderer

**Features:**
- YouTube/Vimeo Embed via `iframe`
- Sandbox: `allow-scripts allow-same-origin allow-popups`
- Autoplay nur bei `auto_open: true`
- Close entfernt Embed → stoppt Wiedergabe

**Reopen-Mechanismus:**
- Persistenz über `localStorage` (`lastVideoModalRequest`)
- Chat-Message-Metadata speichert `video_url`
- Fallback: `data-video-url` Attribut an Chat-Message

### 7.3 Feed Authority via PlaylistItems API

**Problem:** `youtube.search.list` liefert Relevanz-basierte Ergebnisse, nicht deterministisch chronologische. Selbst mit `order=date` kann die API alte "relevante" Inhalte bevorzugen.

**Lösung:** Absolute Feed Authority über `playlistItems.list`:

```python
# 1. Channel → Uploads-Playlist ID
channels.list(id=channelId, part='contentDetails')
→ relatedPlaylists.uploads

# 2. Uploads-Playlist → Chronologische Videos
playlistItems.list(playlistId=uploadsId, part='snippet', maxResults=3)
→ Index 0 = physikalisch neuestes Video
```

**Trigger-Bedingungen:**
- `wants_latest=true` (Nano-Modelle: MUSS-FELD)
- `channel_name` explizit gesetzt (keine Regex-Extraktion)

**Cache-Control:**
- Bei `wants_latest`: Cache-Bypass beim Lookup
- TTL bei Store: 120 Sekunden (`_LATEST_CACHE_TTL_SECONDS`)
- Standard-Suche: 3600 Sekunden (`_VIDEO_CACHE_TTL_SECONDS`)

**Log-Signale:**
- `💎 ABSOLUTE-FEED-AUTHORITY: Channel '<name>' + wants_latest=true`
- `💎 FEED-AUTHORITY: 3 Videos aus Upload-Playlist (Top-3)`
- `💎 ABSOLUTE-FEED-AUTHORITY WINNER: '<title>' by '<channel>'`
- `💎 CACHE-BYPASS: wants_latest=true, skipping cache lookup`

**Ergebnis:** Deterministisch das physisch neueste Video — keine Relevanz-Algorithmen, keine Such-Bias.

---

## 8. Migration Summary (Task 029-034)

### Task 029 — MCL Core
- `modal-api.js` mit `RENDERER_MAP`, `openModal` / `closeModal` / `bringToFront`
- Z-Stack ab Basis 100
- `window-state.js` Erweiterung: MCL-Felder (`type`, `payload`, `zIndex`, `position`, `size`)

### Task 030 — Image Viewer Migration
- `openImageModal()` Legacy-Overlay → MCL
- Bild-Klick in Chat öffnet einheitlichen Image-Viewer
- State-Sync-Listener für `display: block/none`

### Task 031 — Image Studio Z-Stack
- Open/Close/Minimize auf MCL-Pfade
- Focus-to-Front via `mousedown`
- 1300+ Zeilen Business-Logik unberührt

### Task 032 — Knowledge Center Single-Source-of-Truth
- Doppel-State (React + Legacy-JS) eliminiert
- `openBridge()` → `openModal({type: 'document'})`
- Payload-Watcher für `docId`-Wechsel

### Task 033 — Video Player E2E
- `modal_request` Schema Backend→Frontend
- `video-player.js` Renderer mit YouTube/Vimeo Support
- Persistenz, Reopen-Links, Stream-Kompatibilität

### Task 034 — Gallery + Max-Modals
- Gallery MCL-Migration
- FIFO-Guard: Soft-Limit 4 Modals
- Epic-Polish: Console-Log-Audit

---

## 9. Safety & Stability Rules

### 9.1 VERBOTEN in MCL

```javascript
// ❌ FALSCH — MCL hält eigenen State
let activeModals = {};  // VERBOTEN in modal-api.js

// ❌ FALSCH — Direkter DOM-Zugriff
modal.style.display = 'block';  // Außerhalb von State-Sync-Listenern

// ❌ FALSCH — Skills sprechen UI direkt
skill → DOM-Manipulation  // Immer: Skill → MCL → UI
```

### 9.2 ERLAUBT in MCL

```javascript
// ✅ RICHTIG — MCL delegiert an window-state.js
import { getDockModuleState, dockOpen } from './window-state.js';
export function openModal(req) {
  // Validierung, dann:
  dockOpen(modalId);  // window-state.js ist Single Source of Truth
}

// ✅ RICHTIG — State-Sync-Listener (einzige Stelle für DOM-Änderungen)
subscribeWindowState(() => {
  const m = getDockModuleState('video-player');
  modal.style.display = m?.isOpen ? 'flex' : 'none';
});
```

---

## 10. Reference Files

### Core Implementation
- `frontend/js/modal-api.js` — MCL Contract Layer
- `frontend/js/window-state.js` — Single Source of Truth
- `frontend/js/dock.js` — Taskbar-Integration

### Renderers
- `frontend/js/video-player.js` — YouTube/Vimeo Embed
- `frontend/js/knowledge-center.js` — PDF/Text-Dokumente
- `frontend/js/image-studio.js` — Bildgenerierung
- `frontend/js/gallery.js` — Bildergalerie
- `frontend/js/chat.js` — Image-Viewer + `appendMessage()` Hook

### Backend
- `backend/tools/video_tools.py` — Video Search Skill + Cache
- `backend/services/orchestrator/execution_engine.py` — `modal_request` Generierung
- `backend/data/schemas.py` — `ModalRequest` Pydantic-Schema

---

## 11. Archiv-Referenz

Die ursprünglichen separaten Dokumente wurden konsolidiert:

| Original Document | Archived At |
|-------------------|-------------|
| `Universal Modal System.md` | `documentation/archive/dossiers/` |
| `UNIVERSAL_MODAL_SYSTEM_DIAMOND_DOSSIER.md` | `documentation/archive/dossiers/` |
| `Video Search Skill.md` | `documentation/archive/dossiers/` |
| `Modal API Layer.md` | `documentation/archive/dossiers/` |
| `task_029_mcl_core.md` | `documentation/archive/dossiers/` |
| `task_030_mcl_image_viewer.md` | `documentation/archive/dossiers/` |
| `task_031_mcl_image_studio.md` | `documentation/archive/dossiers/` |
| `task_032_mcl_knowledge_center.md` | `documentation/archive/dossiers/` |
| `task_033_mcl_video_player.md` | `documentation/archive/dossiers/` |
| `task_034_mcl_gallery.md` | `documentation/archive/dossiers/` |

---

## 12. Post-Implementation Logs

### Task 033 — Video Player Integration (SEALED)
- **Status:**  **COMPLETE**  
- **Date:** 2026-04-14  
- **Key Achievement:** Video Skill generiert `modal_request` mit YouTube/Vimeo-Embed  
- **Pattern Applied:** Backend-Source-of-Truth + UI Fallback Chain  
- **Files:** `backend/tools/video_tools.py`, `frontend/js/video-player.js`  
- **Verification:** "Neuestes Video von Zumikito" öffnet deterministisch Modal  

### Task 034 — Gallery Integration (SEALED)
- **Status:**  **COMPLETE**  
- **Date:** 2026-04-14  
- **Key Achievement:** Bildergalerie als Modal-Renderer mit Dock-Integration  
- **Pattern Applied:** Stateless MCL + Event-System  
- **Files:** `frontend/js/gallery.js`, `frontend/js/modal-api.js`  
- **Verification:** Gallery-Button in Sidebar öffnet Modal, Minimize geht zu Dock  

### Task 035 — Video Search Feed Authority (NUCLEAR REPAIR)
- **Status:**  **COMPLETE**  
- **Date:** 2026-04-15  
- **Key Achievement:** Feed-Authority Pattern statt Search-API für Kanal-Videos  
- **Pattern Applied:** Authoritative Playlist-Retrieval over Keyword-Search  
- **Changes:**
  - `_clean_channel_hint_for_resolution()` — Entfernt Müll-Wörter vor Resolution  
  - `_playlist_items_get_videos()` — Playlist-API für chronologische Videos  
  - `video_search_tool()` — Upload-Playlist als PRIMARY Strategy  
- **Files:** `backend/tools/video_tools.py` (Lines 334-352, 538-572, 913-960)  
- **Verification:**  
  - "neuestes video von Ninjon" →  FEED-AUTHORITY Log  
  - "Wie backe ich Pizza" →  MODE: GLOBAL_SEARCH  

---

*„Ein System. Viele Inhalte. Keine Duplikate.“* — Diamond Standard Sealed
