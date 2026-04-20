# Task 032 — Knowledge Center: Doppel-State eliminieren, MCL als Single Source of Truth

## 1. Ziel & Kontext

Beseitigung der doppelten State-Verwaltung im Knowledge Center. Aktuell existieren zwei parallele Pfade:
1. **Legacy-JS** (`knowledge-center.js`): `dockOpen/dockClose` + eigene `openBridge()` + Custom Event `open-knowledge-center`
2. **React** (`App.tsx`): `knowledgeVisible` useState + `window.openJanusKnowledge` Bridge

Nach Abschluss gibt es genau EINEN Pfad: `openModal({ type: 'document', payload: { docId } })` → MCL → `window-state.js` → Legacy-Listener reagiert.

- **Kategorie:** C8 (Frontend) + G17 (Bridge)
- **Modell:** Kimi K2.5 (Windsurf)
- **Voraussetzung:** Task 029 (MCL Core) ABGESCHLOSSEN, Task 030+031 empfohlen
- **Risiko:** MITTEL — Bridge-Refactor betrifft Legacy-JS + React + Custom Events

## 2. Impact-Analyse & Abhängigkeiten

- **Basiert auf:** Task 029 (`modal-api.js`, `window-state.js`)
- **Beeinflusst:**
  - `frontend/js/knowledge-center.js`: `openBridge()`, `window.openJanusKnowledge`, `open-knowledge-center` Event-Listener
  - `frontend/js/dock.js` Z.136-148: `btnKnowledge.click` dispatcht `open-knowledge-center` Event + `dockOpen()`
  - `frontend/js/chat.js` Z.~293: `window.openJanusKnowledge(uploadResult.document_id)` nach PDF-Upload
  - `frontend/src/App.tsx` Z.139-154: React-Bridge `window.openJanusKnowledge` + `knowledgeVisible` State
  - `frontend/src/components/KnowledgeCenter.tsx`: bekommt `visible` als Prop von App.tsx
- **Risiko-Einschätzung:** MITTEL
  - Drei Caller-Stellen: dock.js Button, chat.js PDF-Upload, React App.tsx Bridge
  - React-State `knowledgeVisible` in App.tsx muss entfernt oder auf MCL-Listener umgestellt werden
  - PDF-Reload-Logik in `knowledge-center.js` (`loadDocs(documentId)`) muss bei `payload`-Änderung getriggert werden

## 3. Betroffene Dateien

| Datei | Aktion | Scope |
|---|---|---|
| `frontend/js/knowledge-center.js` | EDIT | `openBridge()` (Z.246-257) → `openModal({ type: 'document' })`; `window.openJanusKnowledge` (Z.262-264) → MCL-Wrapper; `open-knowledge-center` Listener (Z.266-270) → entfernen oder MCL-Redirect; `closeKnowledgeCenter` (Z.209-216) → `closeModal()`; NEU: Payload-Watcher für docId-Wechsel |
| `frontend/js/dock.js` | EDIT | `btnKnowledge.click` (Z.136-148): Ersatz für `open-knowledge-center` Event → `openModal({ type: 'document' })` |
| `frontend/js/chat.js` | EDIT | PDF-Upload-Success (Z.~293): `window.openJanusKnowledge(docId)` → `openModal({ type: 'document', payload: { docId } })` |
| `frontend/src/App.tsx` | EDIT | `openJanusKnowledge` Bridge (Z.139-154): auf MCL-Event-Listener umstellen oder entfernen; `knowledgeVisible` State entfernen wenn React-KnowledgeCenter nicht mehr genutzt |
| `frontend/js/modal-api.js` | KEINE ÄNDERUNG | `RENDERER_MAP.document → "knowledge-center"` existiert |

## 4. Umsetzungsschritte

### Schritt 1: knowledge-center.js — Open über MCL

```javascript
import { openModal, closeModal, bringToFront } from './modal-api.js';

// VORHER: openBridge → dockOpen + placeWidgetNextToChat + loadDocs
// NACHHER: openBridge → MCL + loadDocs (Rendering bleibt lokal)

const openBridge = async (documentId, options = {}) => {
  const fromTaskbarDock = options.fromTaskbarDock === true;
  const isToggleIntent =
    !fromTaskbarDock && (documentId === null || typeof documentId === 'undefined');

  if (isToggleIntent && currentDockState().isOpen && !currentDockState().minimized) {
    dockMinimize('knowledge-center', true);
    return;
  }

  // MCL öffnet + setzt payload.docId
  openModal({ type: 'document', payload: { docId: documentId } });
  placeWidgetNextToChat();

  if (!docsLoadedOnce || documentId != null) {
    await loadDocs(documentId);
    docsLoadedOnce = true;
  }
};
```

### Schritt 2: Close über MCL

```javascript
// VORHER: dockClose('knowledge-center')
// NACHHER:
const closeKnowledgeCenter = ({ release = false } = {}) => {
  closeModal('knowledge-center');
  if (release) modal.dataset.positioned = 'false';
  if (currentBlobUrl) { URL.revokeObjectURL(currentBlobUrl); currentBlobUrl = null; }
};
```

### Schritt 3: Global Bridges vereinheitlichen

```javascript
// Legacy-Compat: alle Caller landen am selben Punkt
window.openJanusKnowledge = (documentId) => { void openBridge(documentId); };
window.onKnowledgeModalOpen = (documentId) => { void openBridge(documentId); };

// Custom Event → MCL-Redirect (feuert von dock.js)
window.addEventListener('open-knowledge-center', (e) => {
  void openBridge(e?.detail?.documentId, { fromTaskbarDock: e?.detail?.fromTaskbarDock === true });
});
```

### Schritt 4: dock.js Button → MCL

```javascript
// VORHER (Z.136-148): dispatchEvent + dockOpen
// NACHHER:
import { openModal } from './modal-api.js';

btnKnowledge?.addEventListener('click', () => {
  openModal({ type: 'document' });
});
```

### Schritt 5: chat.js PDF-Upload → MCL

```javascript
// VORHER (Z.~293):
if (typeof window.openJanusKnowledge === 'function') {
  window.openJanusKnowledge(uploadResult.document_id);
}

// NACHHER:
import { openModal } from './modal-api.js';
openModal({ type: 'document', payload: { docId: uploadResult.document_id } });
```

### Schritt 6: App.tsx React-Bridge bereinigen

```typescript
// ENTFERNEN: knowledgeVisible useState + openJanusKnowledge Bridge
// React KnowledgeCenter lauscht stattdessen auf window-state:
// Option A: KnowledgeCenter.tsx liest getDockModuleState('knowledge-center') via Bridge
// Option B: KnowledgeCenter.tsx wird nicht mehr gerendert wenn Legacy-JS das Knowledge Center steuert
// ENTSCHEIDUNG: Legacy-JS knowledge-center.js ist das produktive Modul → React-Rendering deaktivieren
```

**ACHTUNG:** Wenn das React-KnowledgeCenter (`KnowledgeCenter.tsx` + `FloatingWindow.tsx`) aktuell NICHT produktiv genutzt wird (Legacy-JS `knowledge-center.js` ist aktiv), dann App.tsx State + Bridge komplett entfernen. Wenn React-Version aktiv ist, muss sie auf MCL-Events hören.

### Schritt 7: Focus-to-Front

```javascript
// NEU in knowledge-center.js:
modal?.addEventListener('mousedown', () => { bringToFront('knowledge-center'); });
```

## 5. Test-Vorgaben

- [ ] **T1:** Dock-Button öffnet Knowledge Center via MCL (Console: `[MCL] openModal type=document`)
- [ ] **T2:** PDF-Upload in Chat öffnet Knowledge Center mit korrektem `docId`
- [ ] **T3:** Close-Button schließt via `closeModal('knowledge-center')`
- [ ] **T4:** Minimize-Button → Dock-Taskbar zeigt Knowledge Center als minimiert
- [ ] **T5:** `window.openJanusKnowledge(docId)` funktioniert weiterhin (Legacy-Compat)
- [ ] **T6:** PDF-Preview lädt korrekt nach Open mit docId
- [ ] **T7:** Dokument-Liste navigierbar, Wechsel zwischen PDFs funktioniert
- [ ] **T8:** Klick auf Panel → `bringToFront()` → Z-Index steigt
- [ ] **T9:** Kein React-State `knowledgeVisible` mehr in App.tsx (oder auf MCL umgestellt)
- [ ] **T10:** Image Studio / Gallery / Image Viewer unbeeinflusst (Regression)

## 6. Ergebnis & Audit-Trail

**Implementiert:** 2026-04-13  
**Agent:** Kimi (Windsurf)  
**Status:** 🟡 IN PROGRESS — Code-Changes deployed, Tests pending

### Durchgeführte Änderungen

| Datei | Zeilen | Änderung |
|-------|--------|----------|
| `frontend/js/knowledge-center.js` | 10 | Import: `openModal`, `closeModal`, `bringToFront` aus `./modal-api.js` |
| `frontend/js/knowledge-center.js` | 197 | `openKnowledgeCenter()`: `dockOpen("knowledge-center")` → `openModal({ type: "document", payload: { docId } })` |
| `frontend/js/knowledge-center.js` | 211 | `closeKnowledgeCenter()`: `dockClose("knowledge-center")` → `closeModal("knowledge-center")` |
| `frontend/js/knowledge-center.js` | 225 | NEU: Focus-to-Front `modal?.addEventListener('mousedown', () => bringToFront('knowledge-center'))` |
| `frontend/js/knowledge-center.js` | 218 | Minimize: bleibt `dockMinimize("knowledge-center", true)` (MCL hat kein minimizeModal) |
| `frontend/js/knowledge-center.js` | 277 | **NEU:** `lastProcessedDocId` State-Tracking für Payload-Sync |
| `frontend/js/knowledge-center.js` | 293-300 | **NEU:** MCL Payload-Sync Loop in `syncKnowledgeFromDockState()` — lädt Dokumente wenn `payload.docId` sich ändert |
| `frontend/js/dock.js` | 139 | Knowledge-Button: `dispatchEvent + dockOpen` → `openModal({ type: "document" })` |
| `frontend/js/chat.js` | 294-310 | PDF-Upload: `window.openJanusKnowledge` → `window.openModal({ type: 'document', payload: { docId } })` mit Fallback |

**Legacy-Compat erhalten:**
- `window.openJanusKnowledge(documentId)` → ruft weiterhin `openBridge()` auf
- `window.onKnowledgeModalOpen(documentId)` → bleibt verfügbar
- `window.addEventListener('open-knowledge-center')` → bleibt für alte Caller aktiv

**React-Bridge (App.tsx):** Nicht verändert — Legacy-JS ist das produktive Modul. React-KnowledgeCenter wird nicht gerendert.

## 7. Debugging-Log

*(wird bei Bedarf ausgefüllt)*
