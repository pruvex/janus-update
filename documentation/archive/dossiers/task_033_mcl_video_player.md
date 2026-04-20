# Task 033 — Video-Player: Neues Feature (Backend modal_request + Frontend Renderer)

## 1. Ziel & Kontext

Erstes Feature das den vollen MCL-Pfad von Backend bis UI nutzt: Der Chat-Orchestrator liefert ein `modal_request`-Feld in der API-Response, das Frontend erkennt es in `appendMessage()` und öffnet via MCL ein Video-Player-Modal.

Dies ist das einzige Feature in der MCL-Epic das **neuen Code** schreibt (alle anderen migrieren bestehenden Code).

- **Kategorie:** C7 (Backend) + C8 (Frontend)
- **Modell:** Claude 4.5 Sonnet (Cursor) für Backend, Kimi K2.5 (Windsurf) für Frontend
- **Voraussetzung:** Task 029 (MCL Core) ABGESCHLOSSEN
- **Risiko:** HOCH — neues Feature End-to-End, Backend-Schema-Erweiterung + neuer Frontend-Host

## 2. Impact-Analyse & Abhängigkeiten

- **Basiert auf:** Task 029 (`modal-api.js` mit `RENDERER_MAP.video → "video-player"`, `DOCK_HOST_ELEMENT_IDS["video-player"] → "video-player-modal"`)
- **Beeinflusst:**
  - `backend/services/chat_orchestrator.py`: Neues `modal_request`-Feld in Response
  - `frontend/js/chat.js` `appendMessage()`: Muss `modal_request` aus API-Response erkennen
  - `frontend/index.html`: Neuer DOM-Host `#video-player-modal`
  - `frontend/js/window-state.js`: `"video-player"` existiert bereits mit `exists: false` — wird dynamisch registriert
- **Risiko-Einschätzung:** HOCH
  - Backend-API-Response-Schema wird erweitert (Abwärtskompatibel: optionales Feld)
  - Neuer Frontend-Renderer + DOM-Host
  - YouTube-Embed-Security (sandbox, allow-scripts)
  - Kein existierender Code zum Migrieren — alles neu

## 3. Betroffene Dateien

### Backend (NEU)

| Datei | Aktion | Scope |
|---|---|---|
| `backend/services/chat_orchestrator.py` | EDIT | `handle_chat_request()` Response-Dict: optionales `modal_request` Feld hinzufügen |
| `backend/data/schemas.py` | EDIT | Neues `ModalRequest` Pydantic-Schema (optional in ChatResponse) |

### Frontend (NEU + EDIT)

| Datei | Aktion | Scope |
|---|---|---|
| `frontend/js/chat.js` | EDIT | `appendMessage()`: nach Render prüfen ob `data.modal_request` existiert → `openModal()` |
| `frontend/index.html` | EDIT | Neuer DOM-Host: `<div id="video-player-modal" class="dock-panel">...</div>` |
| `frontend/js/video-player.js` | NEU | State-Sync-Listener + YouTube/Vimeo Embed-Renderer |
| `frontend/css/style.css` oder eigene CSS | EDIT | Styling für Video-Player-Panel |
| `frontend/js/modal-api.js` | KEINE ÄNDERUNG | Mapping existiert bereits |

## 4. Umsetzungsschritte

### Phase A: Backend — modal_request Schema

#### Schritt A1: Pydantic-Schema

```python
# backend/data/schemas.py
class ModalRequest(BaseModel):
    type: str                    # "video", "image", "document", etc.
    payload: dict                # type-spezifisch
    options: dict | None = None  # auto_open, pinnable, etc.

# In ChatResponse (oder äquivalent):
class ChatResponse(BaseModel):
    text: str
    modal_request: ModalRequest | None = None  # Optional — abwärtskompatibel
```

#### Schritt A2: Orchestrator — modal_request bei Video-Intent

```python
# backend/services/chat_orchestrator.py
# Wenn ein Skill ein Video-Ergebnis liefert:
response["modal_request"] = {
    "type": "video",
    "payload": {
        "url": video_url,
        "title": video_title,
        "source": "youtube",  # oder "vimeo"
    },
    "options": { "auto_open": True }
}
```

**ACHTUNG:** In Phase 1 muss kein vollständiger `video_search` Skill existieren. Es reicht ein manueller Trigger oder ein Test-Endpoint der eine Response mit `modal_request` liefert.

### Phase B: Frontend — appendMessage Hook

#### Schritt B1: modal_request Erkennung in appendMessage

```javascript
// frontend/js/chat.js — am Ende von appendMessage(), nach dem DOM-Append:
if (data?.modal_request && typeof data.modal_request === 'object') {
  const mr = data.modal_request;
  if (mr.type && mr.payload) {
    // Verzögerter MCL-Call damit Chat-Message erst sichtbar ist
    requestAnimationFrame(() => {
      openModal({ type: mr.type, payload: mr.payload, options: mr.options });
    });
  }
}
```

### Phase C: Frontend — Video-Player Host + Renderer

#### Schritt C1: DOM-Host in index.html

```html
<!-- Video-Player Panel (MCL-managed) -->
<div id="video-player-modal" class="dock-panel dock-panel--video" style="display:none;">
  <div class="dock-panel-header">
    <span class="dock-panel-title">Video Player</span>
    <div class="dock-panel-controls">
      <button id="video-player-minimize-btn" class="dock-panel-btn" title="Minimieren">−</button>
      <button id="close-video-player-btn" class="dock-panel-btn" title="Schließen">×</button>
    </div>
  </div>
  <div id="video-player-content" class="dock-panel-body">
    <!-- Embed wird dynamisch gesetzt -->
  </div>
</div>
```

#### Schritt C2: video-player.js (NEUES MODUL)

```javascript
import { getDockModuleState, subscribeWindowState, dockMinimize } from './window-state.js';
import { closeModal, bringToFront } from './modal-api.js';

document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('video-player-modal');
  const content = document.getElementById('video-player-content');
  const closeBtn = document.getElementById('close-video-player-btn');
  const minimizeBtn = document.getElementById('video-player-minimize-btn');
  if (!modal || !content) return;

  let currentUrl = null;

  function syncVideoPlayerFromDockState() {
    const m = getDockModuleState('video-player');
    const visible = !!m?.isOpen && !m?.minimized;
    modal.style.display = visible ? 'flex' : 'none';

    // Payload-Wechsel → neues Video laden
    const url = m?.payload?.url;
    if (visible && url && url !== currentUrl) {
      currentUrl = url;
      renderVideoEmbed(url, m.payload);
    }
    if (!visible && currentUrl) {
      content.innerHTML = '';  // Embed entfernen → stoppt Wiedergabe
      currentUrl = null;
    }
  }

  function renderVideoEmbed(url, payload) {
    const title = payload?.title || 'Video';
    const embedUrl = toEmbedUrl(url);
    if (!embedUrl) {
      content.innerHTML = `<p style="color:#f88;">URL nicht einbettbar: ${url}</p>`;
      return;
    }
    content.innerHTML = `
      <iframe src="${embedUrl}" title="${title}"
        style="width:100%;height:100%;border:none;"
        sandbox="allow-scripts allow-same-origin allow-popups"
        allowfullscreen></iframe>`;

    // Panel-Titel aktualisieren
    const titleEl = modal.querySelector('.dock-panel-title');
    if (titleEl) titleEl.textContent = title;
  }

  function toEmbedUrl(url) {
    // YouTube
    const ytMatch = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]+)/);
    if (ytMatch) return `https://www.youtube-nocookie.com/embed/${ytMatch[1]}`;
    // Vimeo
    const vimeoMatch = url.match(/vimeo\.com\/(\d+)/);
    if (vimeoMatch) return `https://player.vimeo.com/video/${vimeoMatch[1]}`;
    return null;  // Unbekannte Plattform
  }

  closeBtn?.addEventListener('click', () => closeModal('video-player'));
  minimizeBtn?.addEventListener('click', () => dockMinimize('video-player', true));
  modal?.addEventListener('mousedown', () => bringToFront('video-player'));

  subscribeWindowState(() => syncVideoPlayerFromDockState());
  syncVideoPlayerFromDockState();
});
```

## 5. Test-Vorgaben

- [ ] **T1:** Backend-Response mit `modal_request` Feld wird korrekt serialisiert (Unit-Test)
- [ ] **T2:** `appendMessage()` erkennt `modal_request` und ruft `openModal()` auf
- [ ] **T3:** YouTube-URL wird korrekt zu Embed-URL konvertiert
- [ ] **T4:** Vimeo-URL wird korrekt konvertiert
- [ ] **T5:** Unbekannte URL → Fehlermeldung im Panel (kein Crash)
- [ ] **T6:** Close-Button → `closeModal('video-player')` → Embed wird entfernt (stoppt Wiedergabe)
- [ ] **T7:** Minimize → Taskbar zeigt Video-Player als minimiert
- [ ] **T8:** Z-Index korrekt (Video über Chat, unter neuerem Modal)
- [ ] **T9:** Bestehende Module (Knowledge, Image Studio, Gallery, Image Viewer) unbeeinflusst
- [ ] **T10:** `modal_request` fehlt in Response → kein Fehler, normaler Chat-Flow

## 6. Ergebnis & Audit-Trail

- **Status:** DONE (End-to-End stabilisiert, inkl. Persistenz- und UX-Fixes)
- **Geänderte Dateien (Auszug):**
  - `backend/services/orchestrator/execution_engine.py` — `modal_request` wird aus erfolgreichen `video.search` Tool-Resultaten robust abgeleitet (provider-agnostisch).
  - `backend/data/schemas.py`, `backend/data/crud.py`, `backend/services/orchestrator/status_sync.py` — `modal_request` in Message-Schema und Persistenzpfad aufgenommen.
  - `frontend/js/chat.js` — Reopen-Link-Mechanik (`Video ansehen`), Stream-Nachinjektion, Link-Interception (YouTube/Vimeo), Fallbacks (`lastVideoModalRequest`/Cache/`data-video-url`).
  - `frontend/js/chat-manager.js` — historische Messages laden `modal_request` mit, inkl. Fallback-Pfade.
  - `frontend/js/modal-api.js` — idempotentes `openModal` fuer `video-player` (bestehendes Modal aktualisieren + `bringToFront()` statt Flackern).
  - `frontend/js/video-player.js`, `frontend/js/knowledge-center.js` — Positionierung auf Top-Left von `chat-window-B`, stabile Payload-Anwendung ohne unnoetige Reloads.
  - `frontend/src/styles.css` — Host `pointer-events: none`, Content `pointer-events: auto` fuer nicht blockierende Chat-Interaktion.
  - `backend/tools/video_tools.py` — 1h In-Memory-Cache fuer identische Requests (Quota-Schutz).
  - `backend/services/orchestrator/prompt_registry.py`, `backend/skills/system/video_search.json` — strikte Synthesis-Regeln (kein JSON-Dump, kompakter Nutzertext).
- **Was umgesetzt wurde:** Task 033 wurde von einem initialen MCL-Feature zu einem vollstaendig robusten Video-Workflow erweitert: Tool-Ausfuehrung, modal_request-Generierung, Persistenz, Streaming-Kompatibilitaet, Reopen-Link-UX und Modal-Lifecycle sind nun konsistent ueber GPT/Gemini, Chat-Wechsel und App-Neustarts.
- **Verifikation:**
  - Manuelle End-to-End-Pruefungen in der App (GPT + Gemini) laut Session-Verlauf: PASS.
  - Lint-Checks fuer zuletzt geaenderte Frontend-Dateien (`video-player.js`, `knowledge-center.js`): PASS.
  - Voller `pytest backend/tests -q`: in diesem Tasklauf nicht erneut ausgefuehrt.

## 7. Debugging-Log

- **Issue:** Gemini lieferte teilweise kein oeffnendes Video-Modal.
  - **Fix:** `modal_request` serverseitig deterministisch aus Tool-Resultaten erzeugt.
- **Issue:** Reopen-Link fehlte oder verschwand bei Stream/Chat-Wechsel/Reload.
  - **Fix:** Multi-Layer-Fallback in `chat.js` + Persistenz ueber Message-Metadata und `localStorage`.
- **Issue:** Offenes Video-Modal blockierte Chat-Interaktion.
  - **Fix:** `pointer-events` am Host deaktiviert, nur Content interaktiv.
- **Issue:** Klicks im Chat stoppten Video-Wiedergabe.
  - **Fix:** `iframe.src` nur bei URL-Aenderung neu setzen.
- **Issue:** Modal-Position driftete von gewuenschter Referenz (`chat-window-B`) ab.
  - **Fix:** beide Module (`video-player`, `knowledge-center`) auf direkte Top-Left-Anchor-Berechnung zurueckgestellt.
