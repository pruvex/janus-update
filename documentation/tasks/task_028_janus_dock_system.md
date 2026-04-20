# Task 028: Janus Dock System (Feature-Dossier 8)

## Status

**IN PROGRESS** (2026-04-13) — S1/S2/S3 aktiv, **S4 Teilabschluss: Wissensdatenbank-Migration**

## Epic / Ziel

Zentrale **Modul-Taskleiste (Bottom Dock)** innerhalb der App: Nutzer öffnet/schließt **Module** (Image Studio, PDF Viewer, weitere Workspaces) **parallel zu den Chats**, ohne den Chat-Kontext zu verlieren. Architektur-Leitbild: *Chats sind das Denken — Module sind die Werkzeuge.*

**Referenz-Dossier:** `documentation/Planned Features/8Janus Dock.md`

## Meilensteine

| Stufe | Name | Inhalt (Kurz) |
|-------|------|----------------|
| **S1** | **Dock-Infrastruktur** | HTML-Grundgerüst und CSS für eine **fixe Bottom-Bar** unter dem Workspace (Dual-Chat); Icon-Slots, minimale Dock-Styles, Z-Index-Basis (Dock unter Modul-Overlays). |
| **S2** | **Module State Manager** | Erweiterung / Integration in **`frontend/js/window-state.js`** (oder dediziertes Modul): welche Dock-Module sind offen, Fokus, Persistenz (z. B. `localStorage` / Session) — kompatibel zum bestehenden Fenster-/Workspace-Modell. |
| **S3** | **Floating Panel System** | **Draggable Overlay-Container** für Module (Position, optional Snap, z-index über Chat), Minimieren/Schließen, mehrere Module parallel möglich. |
| **S4** | **Modul-Migration** | **Image Studio** und **PDF Viewer** (bestehende UI) **ans Dock anbinden** — Toggle über Dock-Icons öffnet die jeweiligen Floating Panels statt isolierter Einzel-Buttons nur in der Sidebar/Navigation. |

## Nicht-Ziele (laut Dossier-Auszug)

- Vollständiges OS-ähnliches Window-Management außerhalb der Web-App
- Backend-Pflicht für reinen UI-Dock (sofern nicht explizit nachgezogen)

## Betroffene Bereiche (Vorschau)

- `frontend/index.html` — Dock-Container unter Haupt-Workspace
- `frontend/css/style.css` / `frontend/src/styles.css` — Dock + Overlay-Layer
- `frontend/js/window-state.js` — State-Erweiterung `dock` / `openModules`
- Bestehende Module: Image Studio, PDF-Viewer-Pfade (Nav-Buttons → Dock)

## Kurztest (nach Abschluss S1–S4)

- [ ] Dock sichtbar, Icons reagieren, State über Reload (wo definiert) stabil
- [ ] Mindestens zwei Module gleichzeitig öffenbar ohne Chat-Layout-Bruch
- [ ] Image Studio & PDF vom Dock erreichbar wie spezifiziert

## /post-impl (Teilabschluss) — Knowledge-Center-Migration

**Datum:** 2026-04-13  
**Scope:** Wissensdatenbank von Legacy-Modal auf Dock-Panel umgezogen.

- Dock-State für Modul `knowledge-center` in `window-state.js` (open/minimized/close).
- Sidebar-Button „Wissensdatenbank“ öffnet über Dock-API (`dockOpen`) statt direkter Modal-Display-Logik.
- Header-Harmonisierung mit Chat-Header-Prinzip (`[⟲] [_] [×]` rechts), Dark-Theme/Cyan-Akzent.
- Geometry/Reset auf Chat-B-Overlay-Feeling: große Fläche, Start-/Reset-Anchor an Chat-B, Zielhöhe für komplette PDF-Sicht bei 75% weiter erhöht.
- PDF-Preview initial mit `#zoom=75`; Viewer-Bereich nutzt den verfügbaren Vertikalraum (`flex: 1`).

**Hinweis:** Gesamtepic bleibt offen bis Image Studio + PDF Viewer vollständig im Dock-Pattern konsolidiert sind.

## Siehe auch

- `01_CENTRAL_TASK_REGISTRY.md` — **Epics in Entwicklung**
- `documentation/Planned Features/8Janus Dock.md` — Feature-Dossier 8
