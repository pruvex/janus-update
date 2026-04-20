# Task 022: Dual-Window Core (Epic)

## 1. Ziel & Kontext

**Ziel:** Basis-Infrastruktur für zwei gleichwertige Chat-Fenster (Split-Workspace), zentraler Window-State und eindeutige DOM-Suffixe `-A` / `-B`, damit nachfolgende Sprints Logik und Routing fehlerfrei anbinden können.

**Referenzen:** `documentation/Planned Features/1Dual Chat Window System.md`, `documentation/Planned Features/7Dual Window Layout.md`

**Status:** **DONE** (Meilenstein 1 — Infrastruktur & UX-Polish, 2026-04-12)

---

## 2. Impact-Analyse & Abhängigkeiten

- **Basiert auf:** Bestehendes Chat-Markup (`#main-content`), `frontend/js/chat.js`, `chat-manager.js`, `app.js` (View-Wechsel, Draggable).
- **Beeinflusst:** Alle Stellen mit festen Chat-IDs — Umstellung auf suffixed IDs pro Fenster; sekundäres Fenster B erhält gleiche Struktur, Binding folgt in späteren Sprints.
- **Risiko:** Mittel (DOM- und Selektor-Änderungen); Mitigation: primäres Fenster A bleibt Default für bestehende Logik bis Multi-Pane-Routing.

---

## 3. Betroffene Dateien (Sprint 1)

- `frontend/js/window-state.js` — zentraler Store, Fokus-Klassen, `paneId()`-Helfer.
- `frontend/index.html` — `#chat-window-host-A` / `-B`, innere IDs `*-A` / `*-B`.
- `frontend/css/style.css` — Split-Layout, `.window-active`, Docked-Chat-Overrides.
- `frontend/src/styles.css` — globale Selektoren für suffixed IDs (Header/Messages/Toolbar), wo nötig.
- `frontend/js/chat.js`, `chat-manager.js`, `app.js`, `tts.js`, `knowledge-center.js` — Bindung an Fenster **A** (Kompatibilität bis S3+).

---

## 4. Implementation Log

| Datum | Sprint | Kurzbeschreibung |
|-------|--------|------------------|
| 2026-04-12 | **S1** | `window-state.js`: initiales State-Modell (`windows.A/B`, `activeWindowId`), `subscribeWindowState`, Setter, `paneId()` für `-A`/`-B`, DOM-Sync `.window-active` auf `#chat-window-A|B`, `janus:window-state`-Event, Boot nach DOM ready. |
| 2026-04-12 | **S2** | `index.html`: `main-content` als `.dual-chat-workspace`; zwei Hosts `#chat-window-host-A` / `#chat-window-host-B`; vollständige Duplizierung inkl. `chat-window-{A\|B}`, `chat-header-*`, `chat-messages-*`, `chat-input-container-*`, Formular- und Button-IDs mit Suffix; `chat-window--docked` für Split-Layout. |
| 2026-04-12 | **S7** | `style.css`: Layout-Iterationen (linksbündig, Original-Maße 600×700), `display:contents` auf Hosts, Drag/Resize, Fokus-Polish (Opacity/Glow), Reset-Buttons im Header; `src/styles.css`: Attribute-Selektoren `[id^="…-"]` für suffixed IDs. |
| | S3–S6 | *Geplant:* aktives Fenster + `loadChat`/SSE-Ziel, Sidebar-Routing, Metadaten/Titel pro Pane, ggf. Persistenz — noch nicht umgesetzt. |

---

## 5. Sprint-Checkliste (S1–S7)

### Sprint 1 — Central Store

- [x] `frontend/js/window-state.js` mit State-Modell, Subscription, `paneId()`, DOM-Fokus-Klassen
- [x] Script-Einbindung in `index.html` (vor `app.js`)

### Sprint 2 — HTML-Duplizierung

- [x] `#chat-window-host-A` und `#chat-window-host-B` mit konsistenten inneren IDs (`*-A` / `*-B`)
- [x] `data-window="A"|"B"` an Hosts für späteres Binding

### Sprint 3 — Aktives Fenster & Chat-Routing

- [ ] `loadChat` / `sendMessage` / SSE an das jeweils aktive Fenster (`activeWindowId` + `paneId`-Auflösung)
- [ ] `getCurrentChatId` pro Fenster oder Map `windowId → chatId`

### Sprint 4 — Eingabe & Nebenfenster-Verhalten

- [ ] Placeholder/Empty-State für Fenster B bis Chat gewählt
- [ ] Optional: zweites Composer-Verhalten (Fokus, Tastatur)

### Sprint 5 — Sidebar & Indikatoren

- [ ] Chat-Auswahl öffnet im **aktiven** Fenster (laut Dossier)
- [ ] Optional: spätere Indikatoren welcher Chat wo offen ist (nicht Teil Mvp)

### Sprint 6 — Projekt-Ansicht & Edge Cases

- [ ] `switchView` / `project-chat-host`: klare Zuordnung welches Fenster verschoben wird oder beide Docked bleiben
- [ ] Schließen von Fenster B: Fokus zurück auf A (Dossier)

### Sprint 7 — Split-Layout & Active Styling

- [x] CSS: horizontaler Split, visuelle Trennung, `.window-active`
- [x] Draggable nur für nicht-gedockte Fenster (`.chat-window:not(.chat-window--docked)`)

---

## 6. Post-Impl (Meilenstein 1 abgeschlossen)

- **Zentraler State-Store:** `frontend/js/window-state.js` ist aktiv — Modell `windows.A`/`B`, `activeWindowId`, `subscribeWindowState`, Setter, `paneId()` für `-A`/`-B`, DOM-Sync der Klasse **`.window-active`** auf den echten Fenstern `#chat-window-A`/`#chat-window-B`, CustomEvent **`janus:window-state`**, Fokus per `pointerdown` auf dem jeweiligen Chat-Fenster.
- **Layout-Korrektur:** Linksbündiges Andocken im Hauptbereich (`#chat-view`) mit **Original-Größe** (CSS-Variablen `--dual-chat-host-width` / `--dual-chat-host-height`, typisch 600×700px) statt Full-Width-50/50-Split; rechts verbleibender Leerraum; schwebende Fenster mit interact.js (Drag/Resize), Hosts mit `display: contents` ohne „Geister-Rahmen“.
- **Fokus-System:** Inaktive Fenster **`opacity: 0.65`** ohne zusätzlichen Außen-Glow; aktive Fenster **`opacity: 1`**, blauer Rand (**3px**), **`box-shadow: inset 0 0 10px rgba(0, 150, 255, 0.2)`**; Header des aktiven Fensters leicht aufgehellt mit **blau unterlegter** unterer Kante; **`transition`** auf Opacity/Box-Shadow/Header für weichen Wechsel.
- **Reset-Logik:** Buttons **⟲** in jedem Chat-Header (`#chat-window-reset-btn-A`/`B`) — **`resetChatWindowLayout()`** in `app.js` setzt Position, Größe und `data-x`/`data-y` auf die Standardwerte zurück (inkl. Projekt-Host-Fall).

---

## 7. Test-Vorgaben

- [x] Manuell: App startet, Chat in Fenster A sendbar, Fokus-Klick wechselt `.window-active`
- [x] Fenster B: DOM vorhanden; Routing/SSE folgt in S3+
- [ ] Optional: Playwright-Szenarien nach Abschluss Routing

---

## 8. Ergebnis & nächste Schritte

Meilenstein 1 (State, HTML, CSS, Layout, Fokus, Reset) ist **abgeschlossen**. **S3** verbindet bestehende Chat-Logik (`loadChat`, SSE, `sendMessage`) mit `window-state` und den suffixed DOM-Knoten pro aktivem Fenster.
