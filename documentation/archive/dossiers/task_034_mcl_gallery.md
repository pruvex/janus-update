# Task 034 — Gallery: MCL-Migration + Max-Modals-Limit + Epic-Polish

## 1. Ziel & Kontext

Migration der Gallery auf MCL-Pfade (Open/Close/Minimize via `modal-api.js`) + Einführung eines globalen Max-Modals-Limit (Soft-Limit 4 gleichzeitige Panels). Dies ist der letzte Task der MCL-Epic und enthält auch übergreifende Polish-Aufgaben.

- **Kategorie:** C8 (Frontend)
- **Modell:** Kimi K2.5 (Windsurf)
- **Voraussetzung:** Task 029 (MCL Core) ABGESCHLOSSEN, Tasks 030-032 empfohlen
- **Risiko:** NIEDRIG (Gallery) + NIEDRIG (Max-Modals-Limit)

## 2. Impact-Analyse & Abhängigkeiten

- **Basiert auf:** Task 029 (`modal-api.js`, `window-state.js`)
- **Beeinflusst:**
  - `frontend/js/gallery.js`: Open/Close/Minimize Pfade (Z.86-106)
  - `frontend/js/dock.js` Z.155-158: `btnGallery.click → dockOpen("gallery")` wird MCL
  - `frontend/js/modal-api.js`: Neues Max-Modals-Limit in `openModal()`
- **Risiko-Einschätzung:** NIEDRIG
  - Gallery nutzt bereits `dockOpen/dockClose/dockMinimize` + `subscribeWindowState`
  - Identisches Migrationsmuster wie Image Studio (Task 031)
  - Gallery ist das kleinste Modul (180 Zeilen, ~25 Zeilen Dock-Kopplung)

## 3. Betroffene Dateien

| Datei | Aktion | Scope |
|---|---|---|
| `frontend/js/gallery.js` | EDIT | Imports (Z.1-7): `openModal`/`closeModal`/`bringToFront` hinzufügen; Sidebar-Button (Z.86-93): → `openModal()`; Minimize (Z.96-99): bleibt `dockMinimize`; Close (Z.102-106): → `closeModal()`; NEU: `mousedown` → `bringToFront()` |
| `frontend/js/dock.js` | EDIT | `btnGallery.click` (Z.155-158): → `openModal({ type: 'gallery' })` |
| `frontend/js/modal-api.js` | EDIT | `openModal()`: Max-Modals-Limit (Soft-Limit 4, ältestes Panel minimieren) |
| `frontend/js/window-state.js` | KEINE ÄNDERUNG | `gallery: dockModuleShape({ exists: true })` existiert bereits |

## 4. Umsetzungsschritte

### Teil A: Gallery MCL-Migration

#### Schritt A1: Imports erweitern in gallery.js

```javascript
// Bestehend:
import { dockClose, dockMinimize, dockOpen, getDockModuleState, subscribeWindowState } from './window-state.js';
// NEU hinzufügen:
import { openModal, closeModal, bringToFront } from './modal-api.js';
```

#### Schritt A2: Sidebar-Button → MCL

```javascript
// VORHER (Z.86-93):
galleryNavBtn.addEventListener('click', () => {
  if (isGalleryPanelVisible()) { dockMinimize('gallery', true); }
  else { dockOpen('gallery'); }
});

// NACHHER:
galleryNavBtn.addEventListener('click', () => {
  if (isGalleryPanelVisible()) { dockMinimize('gallery', true); }
  else { openModal({ type: 'gallery' }); }
});
```

#### Schritt A3: Close → MCL

```javascript
// VORHER (Z.102-106):
closeGalleryBtn.addEventListener('click', () => { dockClose('gallery'); });

// NACHHER:
closeGalleryBtn.addEventListener('click', () => { closeModal('gallery'); });
```

#### Schritt A4: Focus-to-Front

```javascript
// NEU:
galleryWindow?.addEventListener('mousedown', () => { bringToFront('gallery'); });
```

#### Schritt A5: dock.js Button → MCL

```javascript
// VORHER (Z.155-158):
btnGallery?.addEventListener('click', () => { dockOpen('gallery'); });

// NACHHER:
btnGallery?.addEventListener('click', () => { openModal({ type: 'gallery' }); });
```

### Teil B: Max-Modals-Limit (Global Polish)

#### Schritt B1: Soft-Limit in modal-api.js openModal()

```javascript
// frontend/js/modal-api.js — innerhalb openModal(), nach Validierung, vor dockOpen():

const MAX_VISIBLE_MODALS = 4;

function enforceMaxModals(excludeModuleId) {
  const modules = getWindowState()?.dock?.modules || {};
  const visibleModules = Object.entries(modules)
    .filter(([id, m]) => id !== excludeModuleId && m.isOpen && !m.minimized)
    .sort((a, b) => (a[1].zIndex || 0) - (b[1].zIndex || 0));  // niedrigster Z zuerst

  if (visibleModules.length >= MAX_VISIBLE_MODALS) {
    // Ältestes (niedrigster Z-Index) minimieren
    const [oldestId] = visibleModules[0];
    dockMinimize(oldestId, true);
    console.log(`[MCL] Max modals reached (${MAX_VISIBLE_MODALS}), minimized: ${oldestId}`);
  }
}
```

In `openModal()` einfügen:

```javascript
export function openModal(request) {
  // ... bestehende Validierung ...
  enforceMaxModals(moduleId);  // ← NEU: vor dockOpen
  // ... bestehender Code: registerDockModule, dockOpen, applyDockZIndicesFromState ...
}
```

### Teil C: Epic-Polish (Übergreifend)

#### Schritt C1: dock.js Import bereinigen

Nach Tasks 030-034 nutzt `dock.js` `openModal()` statt direkte `dockOpen()`-Calls für Module. Import von `openModal` aus `modal-api.js` hinzufügen, nicht mehr benötigte direkte `dockOpen`-Calls für Module entfernen (Chat-Window-`dockOpen` bleibt).

#### Schritt C2: Console-Log-Audit

Alle MCL-Pfade loggen einheitlich:
- `[MCL] openModal type=<type>` bei Open
- `[MCL] closeModal <moduleId>` bei Close
- `[MCL] bringToFront <moduleId> z=<N>` bei Focus
- `[MCL] Max modals reached, minimized: <moduleId>` bei Limit

## 5. Test-Vorgaben

### Gallery-Migration
- [ ] **T1:** Sidebar-Button öffnet Gallery via `openModal()` (Console: `[MCL] openModal type=gallery`)
- [ ] **T2:** Close-Button schließt via `closeModal('gallery')`
- [ ] **T3:** Minimize-Button → Dock-Taskbar zeigt Gallery als minimiert
- [ ] **T4:** Klick auf Gallery-Panel → `bringToFront()` → Z-Index steigt
- [ ] **T5:** Bilder laden korrekt nach Open
- [ ] **T6:** Bild-Klick funktioniert (öffnet in neuem Tab oder Image Viewer)

### Max-Modals-Limit
- [ ] **T7:** 5. Modal öffnen → ältestes wird automatisch minimiert
- [ ] **T8:** Minimiertes Modal erscheint in Dock-Taskbar und kann wiederhergestellt werden
- [ ] **T9:** Console zeigt `[MCL] Max modals reached` Log

### Regression (Gesamte Epic)
- [ ] **T10:** Knowledge Center: Open/Close/Minimize über MCL
- [ ] **T11:** Image Studio: Open/Close/Minimize über MCL, Bildgenerierung funktioniert
- [ ] **T12:** Image Viewer: Bild-Klick in Chat öffnet Viewer mit Z-Stack
- [ ] **T13:** Alle Module: Focus-to-Front bei Klick auf Panel

## 6. Ergebnis & Audit-Trail

*(wird nach Implementierung ausgefüllt)*

## 7. Debugging-Log

*(wird bei Bedarf ausgefüllt)*
