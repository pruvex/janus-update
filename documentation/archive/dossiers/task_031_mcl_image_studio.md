# Task 031 — Image Studio: Z-Stack-Integration + MCL Open/Close

## 1. Ziel & Kontext

Integration des Image Studio in den MCL Z-Stack. Das Image Studio bleibt als Legacy-JS-Modul mit seinem bestehenden DOM-Host (`#image-studio-modal`). Die Migration betrifft NUR die Open/Close/Minimize-Pfade und das Z-Index-Management — die gesamte Business-Logik (1300+ Zeilen: Pricing, Generierung, Export, Inpainting, Presets, Quality Gates) bleibt unberührt.

- **Kategorie:** C8 (Frontend)
- **Modell:** Kimi K2.5 (Windsurf)
- **Voraussetzung:** Task 029 (MCL Core) ABGESCHLOSSEN, Task 030 (Image Viewer) empfohlen
- **Risiko:** NIEDRIG — nur ~20 von 3400 Zeilen betroffen (0.6%)

**ACHTUNG: Das Image Studio wird NICHT auf FloatingWindow/React umgestellt. Es bleibt ein Legacy-JS-Panel. Nur die Dock-Interaktion wird auf MCL-Pfade vereinheitlicht.**

## 2. Impact-Analyse & Abhängigkeiten

- **Basiert auf:** Task 029 (`modal-api.js`, `window-state.js` MCL-Erweiterungen)
- **Beeinflusst:**
  - `dock.js` Zeile 150-153: `btnImageStudio.click → dockOpen("image-studio")` — wird zu MCL-Call
  - `dock.js` Zeile 108-116: `applyHostVisibility` für Image Studio — bleibt, aber Z-Index kommt jetzt aus MCL
- **Risiko-Einschätzung:** NIEDRIG
  - Image Studio nutzt bereits `dockOpen/dockClose/dockMinimize` + `subscribeWindowState` korrekt
  - Die Migration ist im Wesentlichen: bestehende `dockOpen('image-studio')` durch `openModal({ type: 'image-studio' })` ersetzen
  - Alle 6 Sub-Module (`api.js`, `export.js`, `inpainting.js`, `presets.js`, `state.js`, `utils.js`) haben KEINE Dock-Abhängigkeiten

## 3. Betroffene Dateien

| Datei | Aktion | Scope |
|---|---|---|
| `frontend/js/image-studio.js` | EDIT | Imports (Z.1-8): `openModal`/`closeModal` ergänzen; Open-Button (Z.866-877): → `openModal()`; Close-Button (Z.883-886): → `closeModal()`; Minimize (Z.879-881): → `dockMinimize()` bleibt (MCL hat kein minimizeModal); Overlay-Click (Z.889-893): → `closeModal()` |
| `frontend/js/dock.js` | EDIT | `btnImageStudio.click` (Z.150-153): → `openModal({ type: 'image-studio' })` |
| `frontend/js/image-studio.js` | EDIT | `syncImageStudioFromDockState()` (Z.92-105): Z-Index aus MCL-State lesen (optional — wird bereits durch `applyDockZIndicesFromState` in modal-api.js global gesynct) |
| `frontend/js/modal-api.js` | KEINE ÄNDERUNG | `RENDERER_MAP["image-studio"] → "image-studio"` existiert; `DOCK_HOST_ELEMENT_IDS["image-studio"] → "image-studio-modal"` existiert |
| `frontend/js/modules/image-studio/*.js` | KEINE ÄNDERUNG | 6 Module (877 Zeilen) ohne Dock-Abhängigkeit |
| `frontend/css/image-studio.css` | KEINE ÄNDERUNG | 1202 Zeilen unberührt |

## 4. Umsetzungsschritte

### Schritt 1: Import erweitern in image-studio.js

```javascript
// Bestehend:
import { dockClose, dockMinimize, dockOpen, getDockModuleState, subscribeWindowState } from './window-state.js';
// NEU hinzufügen:
import { openModal, closeModal, bringToFront } from './modal-api.js';
```

### Schritt 2: Open-Button → MCL

```javascript
// VORHER (Z.866-877):
openBtn.addEventListener('click', () => {
  dockOpen('image-studio');
  if (!appState.pricingData) loadPricingData();
  loadAllLocalImages();
});

// NACHHER:
openBtn.addEventListener('click', () => {
  openModal({ type: 'image-studio' });
  if (!appState.pricingData) loadPricingData();
  loadAllLocalImages();
});
```

### Schritt 3: Close-Button + Overlay → MCL

```javascript
// Close-Button (Z.883-886):
closeBtn.addEventListener('click', () => { closeModal('image-studio'); });

// Overlay-Click (Z.889-893):
window.addEventListener('click', (event) => {
  if (event.target === modal) { closeModal('image-studio'); }
});
```

### Schritt 4: Minimize bleibt auf dockMinimize

```javascript
// KEINE ÄNDERUNG — MCL hat bewusst kein minimizeModal()
// dockMinimize wird direkt auf window-state.js aufgerufen (erlaubt)
minimizeBtn?.addEventListener('click', () => { dockMinimize('image-studio', true); });
```

### Schritt 5: Focus-to-Front bei Klick auf Panel

```javascript
// NEU: Klick auf das Image-Studio-Panel bringt es in den Vordergrund
modal?.addEventListener('mousedown', () => { bringToFront('image-studio'); });
```

### Schritt 6: dock.js Button anpassen

```javascript
// VORHER (dock.js Z.150-153):
btnImageStudio?.addEventListener("click", () => { dockOpen("image-studio"); });

// NACHHER:
import { openModal } from './modal-api.js';
btnImageStudio?.addEventListener("click", () => { openModal({ type: "image-studio" }); });
```

## 5. Test-Vorgaben

- [ ] **T1:** Sidebar-Button öffnet Image Studio via `openModal()` (Console: `[MCL] openModal` Log)
- [ ] **T2:** Close-Button schließt via `closeModal('image-studio')`
- [ ] **T3:** Minimize-Button minimiert (Dock-Taskbar zeigt Image Studio als minimiert)
- [ ] **T4:** Klick auf Panel → `bringToFront()` → Z-Index steigt über andere offene Modals
- [ ] **T5:** Pricing-Daten laden korrekt nach Open
- [ ] **T6:** Bildgenerierung funktioniert unverändert (End-to-End)
- [ ] **T7:** Export-Modal (JPEG-Optionen) funktioniert unverändert
- [ ] **T8:** Inpainting-Modus funktioniert unverändert
- [ ] **T9:** Presets laden und anwenden korrekt
- [ ] **T10:** Knowledge Center / Gallery / Image Viewer unbeeinflusst (Regression)

## 6. Ergebnis & Audit-Trail

**Implementiert:** 2026-04-13  
**Agent:** Kimi (Windsurf)  
**Status:** ✅ **DONE** — Code-Changes deployed

### Durchgeführte Änderungen

| Datei | Zeilen | Änderung |
|-------|--------|----------|
| `frontend/js/image-studio.js` | 9 | Import: `openModal`, `closeModal`, `bringToFront` aus `./modal-api.js` |
| `frontend/js/image-studio.js` | 869 | Open-Button: `dockOpen('image-studio')` → `openModal({ type: 'image-studio' })` |
| `frontend/js/image-studio.js` | 886 | Close-Button: `dockClose('image-studio')` → `closeModal('image-studio')` |
| `frontend/js/image-studio.js` | 892 | Overlay-Click: `dockClose('image-studio')` → `closeModal('image-studio')` |
| `frontend/js/image-studio.js` | 897 | NEU: Focus-to-Front `modal?.addEventListener('mousedown', () => bringToFront('image-studio'))` |
| `frontend/js/image-studio.js` | 881 | Minimize: bleibt `dockMinimize('image-studio', true)` (MCL hat kein minimizeModal) |
| `frontend/js/dock.js` | 12 | Import: `openModal` aus `./modal-api.js` |
| `frontend/js/dock.js` | 153 | Sidebar-Button: `dockOpen("image-studio")` → `openModal({ type: "image-studio" })` |

**Business-Logik unberührt:** Alle 6 Sub-Module (`api.js`, `export.js`, `inpainting.js`, `presets.js`, `state.js`, `utils.js`) haben keine Dock-Abhängigkeiten und wurden nicht geändert.

## 7. Debugging-Log

*(wird bei Bedarf ausgefüllt)*
