# UNIVERSAL MODAL SYSTEM — Diamond-Standard Dossier

**Konsolidiert aus**: Modal API Layer.md + Universal Modal System.md + VIDEO MODAL SYSTEM.md
**Basiert auf**: Ist-Analyse des Codebase (Stand 2026-04-13)
**Status**: ENTWURF — Bereit fuer Task-Aufgliederung

---

## 1. Ziel

Ein einziges, konsistentes Window-Management-System fuer alle visuellen Module in Janus.
Skills kommunizieren ueber einen typisierten Contract Layer (MCL) mit der UI — kein Feature spricht direkt mit DOM/React-Komponenten.

---

## 2. Ist-Analyse: Was existiert bereits

### 2.1 Window-State-Infrastruktur (Legacy JS)

| Datei | Funktion | Status |
|---|---|---|
| `frontend/js/window-state.js` | Zentraler State-Store: Dual-Pane (A/B), Dock-Module-Registry, localStorage-Persistence, Event-System (`janus:window-state`) | Produktiv |
| `frontend/js/dock.js` | Taskbar: open/minimize/close fuer knowledge-center, image-studio, gallery; z-index + Geometrie fuer Knowledge-Panel | Produktiv |
| `frontend/js/chat.js` | `appendMessage()` — rendert Skill-Responses als HTML in Chat-Panes; `openImageModal()` fuer Bild-Vollansicht | Produktiv |
| `frontend/js/chat-manager.js` | loadChat/loadChats mit Window-Binding, Sidebar-Sync, Active-Chat-Bar | Produktiv |

### 2.2 Window-Primitives (React)

| Komponente | Funktion | Genutzt von |
|---|---|---|
| `FloatingWindow.tsx` | Drag + Resize + Close, fixed-position Paper, zIndex: 9999 | KnowledgeCenter |
| `FloatingWidget.tsx` | Drag-only (kein Resize), zIndex: 1300 | Nicht referenziert |
| `ImageStudioModal.tsx` | MUI `<Dialog>` (Vollbild, KEIN FloatingWindow) | App.tsx |

### 2.3 Aktuelle Modal-Patterns (4 verschiedene!)

| Feature | Pattern | Problem |
|---|---|---|
| **Knowledge Center** | `FloatingWindow.tsx` + React State in `AppRouter` + Legacy-Bridge `window.openJanusKnowledge` | Doppelte State-Verwaltung (React + dock.js) |
| **Image Studio** | MUI `<Dialog>` in `ImageStudioModal.tsx` + dock.js toggle | Nicht draggable, nicht in Taskbar pinnbar |
| **Gallery** | Rein Legacy-JS + dock.js | Kein React-Pendant |
| **Image Vollansicht** | `window.openImageModal()` in chat.js, einfaches display:block overlay | Kein Window-System, kein Drag/Resize |

### 2.4 Backend-zu-Frontend Response-Flow

```
Skill executes
  -> SkillResponse (JSON)
    -> chat_orchestrator formatiert final text
      -> POST /api/chat Response
        -> Frontend chat.js appendMessage()
          -> marked.parse() + DOM-Manipulation
```

**Kein Mechanismus existiert**, um aus einem Skill-Response direkt ein Modal zu oeffnen.

---

## 3. Architektur-Entscheidungen

### E1: MCL lebt in Legacy-JS (nicht React)

**Begruendung**: Der primaere UI-Runtime-Path laeuft ueber `window-state.js` + `dock.js` + `chat.js`. React-Komponenten sind Islands, die ueber Bridges angebunden werden. Der MCL muss dort leben, wo der State-of-Truth ist — und das ist `window-state.js`.

React-Modals registrieren sich beim MCL via Bridge-Events, genau wie `KnowledgeCenter` es heute schon tut.

### E2: `window-state.js` Dock-Module-Registry = Basis des MCL

Die bestehende `dock.modules`-Registry wird zum MCL erweitert:

```javascript
// Erweiterung des bestehenden dock.modules State
dock: {
  modules: {
    "knowledge-center": {
      exists: true,
      isOpen: false,
      minimized: false,
      // NEU: MCL-Felder
      type: "document",        // Renderer-Typ
      payload: null,            // Aktiver Content
      position: { x: 980, y: 20 },
      size: { w: 900, h: 1270 },
      zIndex: 100,
    },
    "image-studio": { ... },
    "gallery": { ... },
    "video-player": { ... },   // NEU: dynamisch registrierbar
  }
}
```

### E2.1: State-Ownership-Regel (KRITISCH)

**`modal-api.js` (MCL) hat KEINEN eigenen State.**

Alle Lese-/Schreiboperationen laufen ausschliesslich ueber `window-state.js`-Funktionen.
MCL ist eine zustandslose Fassade — er validiert, routet und delegiert, speichert aber nichts selbst.

Verboten:
```javascript
// FALSCH — MCL haelt eigenen State
let activeModals = {};  // ← VERBOTEN in modal-api.js
```

Richtig:
```javascript
// RICHTIG — MCL delegiert an window-state.js
import { getDockModuleState, dockOpen } from './window-state.js';
export function openModal(req) {
  // validate, route, dann:
  dockOpen(modalId);  // window-state.js ist Single Source of Truth
}
```

Damit gibt es **genau ein** State-System, keine Race Conditions, keine Ghost States.

### E3: Kein Greenfield — Migration der 4 bestehenden Patterns

Jedes Feature wird schrittweise auf den MCL-Contract umgestellt, nicht alles auf einmal.

### E4: Backend Modal-Requests via API-Response-Feld

Neues optionales Feld in der Chat-API-Response:

```json
{
  "text": "Hier ist das Video zum Thema...",
  "modal_request": {
    "type": "video",
    "payload": {
      "source": "youtube",
      "url": "https://youtube.com/watch?v=...",
      "title": "Flammkuchen Tutorial"
    },
    "options": {
      "auto_open": true,
      "pinnable": true
    }
  }
}
```

`appendMessage()` in `chat.js` prueft auf `modal_request` und leitet an MCL weiter.

---

## 4. MCL Contract API

### 4.1 Open Modal

```javascript
// frontend/js/modal-api.js
export function openModal(request) {
  // request: { type, payload, options? }
  // Validierung
  if (!SUPPORTED_TYPES.includes(request.type)) {
    console.error(`[MCL] Unsupported modal type: ${request.type}`);
    return null;
  }
  // Renderer-Lookup
  const renderer = RENDERER_MAP[request.type];
  if (!renderer) {
    console.error(`[MCL] No renderer for type: ${request.type}`);
    return null;
  }
  // Dock-Registration + State-Update
  const modalId = generateModalId(request.type);
  registerDockModule(modalId, {
    type: request.type,
    payload: request.payload,
    renderer: renderer,
    ...DEFAULT_OPTIONS,
    ...(request.options || {}),
  });
  dockOpen(modalId);
  return modalId;
}
```

### 4.2 Renderer Map

```javascript
const RENDERER_MAP = {
  "document":      "knowledge-center",   // Bestehend
  "image-studio":  "image-studio",       // Bestehend (Migration von Dialog)
  "gallery":       "gallery",            // Bestehend
  "video":         "video-player",       // NEU
  "image":         "image-viewer",       // NEU (ersetzt openImageModal)
  "pdf":           "pdf-viewer",         // Zukuenftig
  "tool":          "tool-output",        // Zukuenftig
};
```

### 4.3 Close / Minimize / Update

```javascript
export function closeModal(modalId)    { dockClose(modalId); }
export function minimizeModal(modalId) { dockMinimize(modalId, true); }
export function restoreModal(modalId)  { dockMinimize(modalId, false); }

export function updateModalPayload(modalId, payload) {
  // State-Update + Event-Emit fuer Renderer-Refresh
  updateDockModulePayload(modalId, payload);
}
```

### 4.4 Events (Bidirektional)

```javascript
// MCL -> Listener (z.B. Skill-Context-Update)
window.addEventListener("janus:modal-event", (e) => {
  // e.detail: { modalId, event: "closed"|"pinned"|"interacted", context }
});

// Renderer -> MCL (z.B. User schliesst Modal)
emitModalEvent(modalId, "closed", { reason: "user" });
```

---

## 5. Z-Index-Management (Stack-basiert)

```javascript
// frontend/js/modal-api.js
const Z_BASE = 100;       // Dock-Module Basis
const Z_CHAT = 50;        // Chat-Panes
const Z_OVERLAY = 10000;  // Fullscreen-Overlays (Legacy Image Modal)

let zCounter = Z_BASE;

function bringToFront(modalId) {
  zCounter += 1;
  updateDockModuleZIndex(modalId, zCounter);
}

// Focus-to-front: Klick auf Modal -> bringToFront()
```

**Ersetzt**: hardcoded `zIndex: 9999` in FloatingWindow.tsx und `zIndex: 1300` in FloatingWidget.tsx.

---

## 6. Migration-Map

### Phase M1: MCL-Core + Image-Viewer (Niedrigstes Risiko)

**Scope**: `modal-api.js` anlegen, `openImageModal()` in chat.js auf MCL umstellen

| Was | Vorher | Nachher |
|---|---|---|
| `chat.js:openImageModal()` | Direktes `display:block` auf DOM-Element | `openModal({ type: "image", payload: { url } })` |
| Bild-Klick in Chat | `openImageModal(img.src)` | `MCL.openModal(...)` |
| Neues Fenster | Statisches Overlay | FloatingWindow mit Drag/Resize/Close |

**Dateien**: `frontend/js/modal-api.js` (NEU), `frontend/js/chat.js` (Edit), `frontend/js/window-state.js` (Erweiterung)
**Risiko**: Niedrig — nur das Bild-Overlay aendert sich

### Phase M2: Image Studio Migration

**Scope**: `ImageStudioModal.tsx` von MUI Dialog auf FloatingWindow umstellen, MCL-Integration

| Was | Vorher | Nachher |
|---|---|---|
| Image Studio | MUI `<Dialog>` (nicht draggable) | `FloatingWindow` via MCL |
| Oeffnen | `setImageStudioOpen(true)` in React | `MCL.openModal({ type: "image-studio" })` |
| Dock-Integration | dock.js toggle separat | Automatisch via MCL |

**Dateien**: `frontend/src/components/ImageStudioModal.tsx` (Refactor), `frontend/js/dock.js` (Vereinfachung)
**Risiko**: Mittel — React-Bridge muss MCL-Events konsumieren

### Phase M3: Knowledge Center Vereinheitlichung

**Scope**: Doppel-State (React `knowledgeVisible` + dock.js `dockOpen`) zu Single-Source-of-Truth ueber MCL

| Was | Vorher | Nachher |
|---|---|---|
| State | React `useState` + dock.js parallel | Nur MCL (dock-module-state) |
| Oeffnen | `window.openJanusKnowledge()` Bridge | `MCL.openModal({ type: "document", payload: { docId } })` |
| React-Seite | `AppRouter` verwaltet `knowledgeVisible` | React lauscht auf `janus:window-state` Event |

**Dateien**: `frontend/src/App.tsx` (Vereinfachung), `frontend/js/dock.js` (Vereinfachung)
**Risiko**: Mittel — Bridge-Refactor betrifft mehrere Stellen

### Phase M4: Video-Player (Neues Feature)

**Scope**: Neuer Renderer fuer Video-Embeds, Backend-Skill `video_search`, MCL-Integration via `modal_request`

| Komponente | Beschreibung |
|---|---|
| `video-player.js` oder `VideoPlayer.tsx` | YouTube/Vimeo Embed in FloatingWindow |
| Backend `video_search` Skill | YouTube API Query, returns structured payload |
| `chat.js` `appendMessage()` | Erkennt `modal_request` in API-Response, leitet an MCL |
| Chat-Orchestrator | Neues `modal_request`-Feld in Response-Schema |

**Dateien**: Backend + Frontend, mehrere neue Dateien
**Risiko**: Hoch — neues Feature E2E

### Phase M5: Gallery Migration + Dynamic Module Registration

**Scope**: Gallery von rein Legacy auf MCL, dynamische Module (z.B. mehrere Videos gleichzeitig)

---

## 7. Validation Layer

MCL validiert jeden Request:

```javascript
function validateModalRequest(request) {
  const errors = [];
  if (!request.type) errors.push("type required");
  if (!SUPPORTED_TYPES.includes(request.type)) errors.push(`unknown type: ${request.type}`);
  if (!request.payload) errors.push("payload required");
  // Typ-spezifische Validierung
  const validator = TYPE_VALIDATORS[request.type];
  if (validator) {
    const typeErrors = validator(request.payload);
    errors.push(...typeErrors);
  }
  return errors.length === 0 ? { valid: true } : { valid: false, errors };
}
```

---

## 8. Abgrenzung: Was MCL NICHT ist

| MCL ist | MCL ist NICHT |
|---|---|
| Contract zwischen Skills und UI | Ein neues UI-Framework |
| State-Routing + Validation | Rendering-Engine (das bleibt bei FloatingWindow/React) |
| Erweiterung von window-state.js | Ersatz fuer window-state.js |
| Event-basierte Kommunikation | Synchroner Funktionsaufruf aus dem Backend |

---

## 9. Nicht-Funktionale Anforderungen

- **Performance**: Lazy-Load von Renderer-Modulen (Video-Player erst bei erstem Video-Request)
- **Persistenz**: Offene Module + Positionen in localStorage (Erweiterung bestehender Persistence in window-state.js)
- **Accessibility**: Alle Modals mit aria-label, Escape-to-close, Focus-Trap
- **Testbarkeit**: Playwright-Tests fuer open/close/minimize/pin-Zyklen pro Modul

---

## 10. Task-Aufgliederung (Vorschlag)

| Task-ID | Titel | Phase | Abhaengigkeit |
|---|---|---|---|
| `task_029_mcl_core` | MCL-Core: modal-api.js + window-state.js Erweiterung + Z-Index-Stack | M1 | — |
| `task_030_image_viewer_mcl` | Image-Viewer: openImageModal Migration auf MCL | M1 | task_029 |
| `task_031_image_studio_floating` | Image Studio: Dialog -> FloatingWindow + MCL | M2 | task_029 |
| `task_032_knowledge_center_mcl` | Knowledge Center: Single-Source-of-Truth via MCL | M3 | task_029 |
| `task_033_video_player` | Video-Player: Neuer Renderer + Backend-Skill + modal_request | M4 | task_029 |
| `task_034_gallery_mcl` | Gallery: Legacy -> MCL + Dynamic Module Registration | M5 | task_029 |

---

## 11. Offene Entscheidungen

1. **FloatingWindow in Legacy-JS portieren?** Aktuell ist FloatingWindow React. Entweder: (a) alle Modals werden React-Islands, oder (b) ein Legacy-JS FloatingWindow-Equivalent wird gebaut. Empfehlung: (a) — React-Islands via Bridges, wie KnowledgeCenter es vorgemacht hat.

2. **Maximale gleichzeitige Modals?** Vorschlag: Soft-Limit 4, ab dem 5. wird das aelteste minimiert.

3. **Snap-to-Edge?** Nice-to-have fuer spaeter, kein MVP-Requirement.

---

*Dieses Dossier ersetzt die separaten Dokumente "Modal API Layer.md" und "Universal Modal System.md" als verbindliche Architektur-Referenz.*
