# Task: Tages-Panel (Kalender-Widget-Rail) — Diamond-Standard & Release-Pfad

**Status:** Implementiert (Frontend), Release-Verifikation aktiv  
**Stand:** 2026-05-01 (post-impl)

---

## 1. Ziel

Eingebetteter **rechter Rail** am Chat (`#calendar-day-widget-rail`) ohne zweites MCL-Floating-Modal: gleiche Tages-Kennzahlen wie die Kalender-Rechtsrail, „Nächster Termin“, Tagesplan mit „Jetzt“-Marker, Schnellaktionen, KI-Zeile (Delegation in den Vollkalender), zuverlässiges **Schließen (× / Escape)** trotz schwebender Chat-Fenster.

---

## 2. Release-Pfad (Dev vs. Produktion)

| Modus | UI-Quelle | Bemerkung |
|--------|------------|------------|
| **Entwicklung** | Vite: `http://localhost:5173/` | Lädt `frontend/index.html` + ES-Module live. |
| **Produktion (Electron, gepackt)** | HTTP: `http://127.0.0.1:8001/` | FastAPI mountet `frontend/dist` an `/` (`backend/main.py`: `StaticFiles` → `frontend/dist`). |
| **Installer-Inhalt** | `electron-builder` `files` umfasst `frontend/dist/` | `package.json` → `build.files` enthält `frontend/dist/`. |

**Wichtig:** Ohne frischen **`npm run build`** (bzw. `npx vite build`) ist `frontend/dist` veraltet — die installierte App zeigt dann **nicht** den Stand von `frontend/index.html` / `frontend/js/…`.

**Automatische Prüfung:** Nach jedem `vite build` (im `npm run build`) läuft `node scripts/verify-frontend-dist.cjs` und bricht ab, wenn im Bundle keine Tages-Panel-Strings vorkommen (`calendar-day-widget`, `janusCloseDayPanel`, `calendar-day-widget-rail`).

Manuell: `npm run verify:frontend-dist` (erwartet bestehendes `frontend/dist`).

---

## 3. Kerndateien (Referenz)

| Bereich | Pfade |
|--------|--------|
| Markup & Script-Reihenfolge | `frontend/index.html` (Tages-Rail, Module: `calendar-day-widget` vor `calendar-modal` sinnvoll) |
| Panel-Logik | `frontend/js/calendar-day-widget.js` (kein harter Import von `calendar-modal.js`; Lazy-`import()` für Schnellaktionen/KI) |
| Gemeinsame Kennzahlen | `frontend/js/calendar-day-stats.js` |
| Styles | `frontend/css/calendar-day-widget.css` |
| Chat-Bounds (kein Überdecken des Rails) | `frontend/js/app.js` — `getChatWindowBoundsEl` → `#main-content` im Chat |
| Backend statisch | `backend/main.py` — Mount `frontend/dist` |

---

## 4. Post-Impl (abgeschlossene Punkte)

- [x] × / Escape: globale Handler (`attachDayPanelDismissGloballyOnce`), `dayPanelIsOpen()` über `getComputedStyle`, Capture-`pointerdown`/`click`, kein früher Return bei Treffer auf dem Button (Pointer→Click-Lücke).
- [x] `window.janusCloseDayPanel` + HTML-`onclick`-Fallback (ohne problematisches `&&` im Attribut).
- [x] Lazy `import("./calendar-modal.js")` — Panel funktioniert auch wenn das Kalender-Modul beim Eval scheitert.
- [x] `rail[hidden]` CSS mit `display: none !important`.
- [x] E2E: `tests/e2e/calendar-day-widget.spec.js` (×, Escape; gemockte Kalender-API).
- [x] **Release:** `scripts/verify-frontend-dist.cjs` + Anbindung an `npm run build`.

---

## 5. Offen / optional (Backlog)

- Datenparität nur „heute“ vs. Kalender-Suche — gemeinsame Quelle oder UI-Hinweis.
- KI: Kurz-Zusammenfassung im Rail ohne Pflicht „Kalender öffnen“.
- Weitere Quick Actions nur bei echter Flow-Anbindung.

---

## 6. Verwandte Dokumentation

- `documentation/archive/dossiers/UNIVERSAL_MODAL_SYSTEM_DIAMOND_DOSSIER.md` (MCL vs. eingebettetes Rail)
- `documentation/user_guides/janus_calendar_pro_tips.md` (Kalender-Nutzung)
