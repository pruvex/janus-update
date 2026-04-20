# Task 030 — Image-Viewer: Legacy Overlay → MCL Migration

## 1. Ziel & Kontext

Migration des Bild-Vollansicht-Overlays (`openImageModal` / `closeImageModal` in `chat.js`) auf den MCL-Pfad (`modal-api.js` → `window-state.js`). Nach Abschluss wird die Image-Vollansicht im einheitlichen Z-Stack mit Knowledge Center, Image Studio und Gallery verwaltet.

- **Kategorie:** C8 (Frontend)
- **Modell:** Kimi K2.5 (Windsurf)
- **Voraussetzung:** Task 029 (MCL Core) ABGESCHLOSSEN
- **Risiko:** Niedrig — Scope ist ~60 Zeilen in einer Datei, keine Cross-Module-Abhängigkeiten

## 2. Impact-Analyse & Abhängigkeiten

- **Basiert auf:** Task 029 (`modal-api.js`, `window-state.js` MCL-Erweiterungen)
- **Beeinflusst:** Kein anderes Modul — Image-Viewer ist eigenständig
- **Risiko-Einschätzung:** NIEDRIG
  - `openImageModal` wird nur in `chat.js` aufgerufen (Zeile ~995: img.click in appendMessage)
  - `window.openImageModal` ist als globale Funktion exponiert — Legacy-Wrapper bleibt erhalten
  - Keine React-Komponente beteiligt, rein Legacy-JS

## 3. Betroffene Dateien

| Datei | Aktion | Scope |
|---|---|---|
| `frontend/js/chat.js` | EDIT | `openImageModal()` (Z.31-86) → MCL-Delegation; `closeImageModal()` (Z.88-91) → MCL; Event-Listener (Z.116-130) → MCL; img.click in appendMessage (Z.~995) → MCL |
| `frontend/js/modal-api.js` | KEINE ÄNDERUNG | `RENDERER_MAP.image → "image-viewer"` und `DOCK_HOST_ELEMENT_IDS["image-viewer"] → "image-modal"` existieren bereits |
| `frontend/js/window-state.js` | KEINE ÄNDERUNG | `"image-viewer": dockModuleShape({ exists: true })` existiert bereits |

## 4. Umsetzungsschritte

### Schritt 1: State-Sync-Listener anlegen (NEUER CODE in chat.js)

```javascript
// Neuer Listener — einzige Stelle die #image-modal display steuert
import { getDockModuleState, subscribeWindowState } from './window-state.js';

function syncImageViewerFromDockState() {
  const m = getDockModuleState('image-viewer');
  const visible = !!m?.isOpen && !m?.minimized;
  if (imageModal) {
    imageModal.style.display = visible ? 'block' : 'none';
  }
  // Wenn sichtbar und payload.url vorhanden → Bild laden + skalieren
  if (visible && m?.payload?.url) {
    renderImageInModal(m.payload.url);
  }
  if (!visible && imageModalImg) {
    imageModalImg.src = '';  // Speicher freigeben
  }
}
subscribeWindowState(() => syncImageViewerFromDockState());
```

### Schritt 2: Rendering-Logik extrahieren

Die bestehende Bild-Lade- und Skalierungslogik (tempImage-Preload, proportionale Groeße, 1024×1024-Limit) aus `openImageModal()` in eine neue Funktion `renderImageInModal(url)` extrahieren. Diese Funktion wird NUR vom State-Sync-Listener aufgerufen.

**WICHTIG:** `renderImageInModal()` bleibt in `chat.js` — NICHT in `modal-api.js` verschieben.

### Schritt 3: openImageModal → MCL-Delegation

```javascript
import { openModal } from './modal-api.js';

// Legacy-Compat-Wrapper bleibt als window.openImageModal
window.openImageModal = function(imageUrl) {
  openModal({ type: 'image', payload: { url: imageUrl } });
};
```

### Schritt 4: closeImageModal → MCL-Delegation

```javascript
import { closeModal } from './modal-api.js';

function closeImageModal() {
  closeModal('image-viewer');
}
```

### Schritt 5: Event-Listener anpassen (DOMContentLoaded-Block)

```javascript
// Close-Button → MCL
closeImageModalButton?.addEventListener('click', () => closeImageModal());

// Overlay-Click → MCL (Drag-Guard bleibt)
imageModal?.addEventListener('click', (e) => {
  if (e.target === imageModal && !window.justDragged) {
    closeImageModal();
  }
  window.justDragged = false;
});
```

### Schritt 6: appendMessage img.click → MCL

```javascript
// Zeile ~995 in appendMessage
img.addEventListener("click", (event) => {
  event.stopPropagation();
  openModal({ type: 'image', payload: { url: img.src } });
});
```

## 5. Test-Vorgaben

- [ ] **T1:** Bild-Klick in Chat öffnet Image-Viewer mit korrektem Z-Index (über andere offene Modals)
- [ ] **T2:** Close-Button schließt via `closeModal('image-viewer')`
- [ ] **T3:** Overlay-Click schließt (Drag-Guard respektiert)
- [ ] **T4:** `window.openImageModal(url)` funktioniert weiterhin (Legacy-Compat)
- [ ] **T5:** Bild-Skalierung unverändert (max 1024×1024, proportional, viewport-begrenzt)
- [ ] **T6:** Nach Close: `imageModalImg.src` wird geleert (Memory-Cleanup)
- [ ] **T7:** Kein `display:block/none` auf `#image-modal` außerhalb des State-Sync-Listeners
- [ ] **T8:** Knowledge Center / Image Studio / Gallery unbeeinflusst (Regression-Check)

## 6. Ergebnis & Audit-Trail

*(wird nach Implementierung ausgefüllt)*

## 7. Debugging-Log

*(wird bei Bedarf ausgefüllt)*
