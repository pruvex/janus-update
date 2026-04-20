# Task 029 — MCL Core (modal-api & window-state)

## 1. Klassifizierung & Ressourcen
- **Kategorie:** C8 (Frontend) / Architektur
- **Modell:** Claude 4.5 Sonnet (Cursor)
- **Ort:** Cursor

## 2. IST / SOLL
- **IST:** `modal-api.js` mit `RENDERER_MAP`, `openModal` / `closeModal` / `bringToFront`, Z-Stack ab 100; `window-state` mit MCL-Feldern (`type`, `payload`, `zIndex`, `position`, `size`) und `registerDockModule` / `updateDockModuleZIndex`.
- **SOLL:** Stateless MCL-Fassade bleibt Single-Source über `dock.modules`; keine parallelen Modal-Maps im Frontend.

## 3. Nächster Schritt
- **NEXT:** Task 030: `openImageModal` und sichtbare Hosts an MCL anbinden; Panel-Klicks → `bringToFront`.

## 4. Akzeptanz
- [x] `frontend/js/modal-api.js` mit `RENDERER_MAP` und Z-Stack-Sync auf Dock-Hosts.
- [x] `window-state.js` erweitert um MCL-Metadaten und Register-/Z-Index-APIs.
