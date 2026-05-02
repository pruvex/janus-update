# Task 059: Kalender-Spiegel im Memory & proaktiver Termin-Assistent (Diamond)

**Status:** `V1 IMPLEMENTED`  
**Stand:** 2026-05-02  
**Bezug:** Nachgelagert zu TASK-058 (Kalender-Modal / API / Tools); ergänzt das **Assistenten-Verhalten** im Chat.

> **Legende Änderungsherkunft:**
> - `[ORIG]` = aus ursprünglicher Task-059 übernommen
> - `[GPT-TIP]` = aus der ChatGPT-Review integriert (Datei `kalender memory.md`)
> - `[MERGED]` = von mir zusammengeführt / abgewogen / angepasst
> - `[NEW]` = neue Ergänzung auf Basis beider Quellen

---

## 1. Ziel & Problemstellung

### 1.1 Produktziel `[ORIG]`

Janus soll Termine **nicht nur per Live-Tool** (`get_calendar_events`) beantworten können, sondern über einen **dauerhaft aktualisierten, kompakten Kalenderüberblick im Memory-Kontext**, sodass:

- **Schnelle Antworten** auf „Welche Termine habe ich?" möglich sind (weniger Pflicht-Tool-Roundtrips).
- **Proaktive Hinweise** möglich werden, z. B. Nutzer: „Donnerstag fahre ich zu Tante Erna" → Assistent: „Hinweis: Donnerstag hast du um 14:00 ein Meeting — soll ich es verschieben?"

**Quelle der Wahrheit** bleibt der angebundene Kalender (z. B. Google). Memory ist eine **gezielte Spiegelung**, keine Doppelpflege.

### 1.2 Erweitertes Zielbild `[GPT-TIP, MERGED]`

Ein Diamond-Assistent **versteht** Termine, nicht nur deren Zeitfenster:

| Stufe | Beispiel |
|-------|----------|
| **Basis (V1)** | „Du hast um 14:00 einen Termin." |
| **Kontext (V1.1)** | „Du hast um 14:00 ein Meeting — das kollidiert wahrscheinlich mit deiner Fahrt." |
| **Handlung (V2)** | „Soll ich das Meeting auf Freitag verschieben oder absagen?" |

**V1 zielt auf Basis + Kontext; V2 (Handlung) ist Backlog.**

### 1.3 Ist-Stand `[ORIG]`

- Kalenderdaten im Chat-Fluss nur über **Calendar-Tools**; **keine** strukturierte Sync ins Memory.
- Kein proaktiver Abgleich ohne erneuten API-Abruf in derselben Anfrage.

---

## 2. Nicht-Ziele (Scope-Grenze) `[ORIG + MERGED]`

- **Volltext-Spiegelung** jedes Event-Feldes unbegrenzt (Token/Bloat).
- **Garantiertes** proaktives Verhalten in **jedem** Satz (kann stören).
- Ersetzen der **Calendar-API** für Buchungen — Live-Tools bleiben für Mutationen.
- `[NEW]` **Eigenes NLP-Intent-Modul** in V1. Die bestehende LLM-Verarbeitung erkennt Daten/Orte im Prompt bereits; ein dediziertes Intent-Detection-System (classify „travel" vs. „appointment") ist **V2-Backlog**, kein V1-Blocker.
- `[NEW]` **Push-Benachrichtigungen** (10 min vor Termin, Morgenübersicht) — erfordert Frontend-Timer-Architektur (Tray/Notification), **V2-Backlog**.

---

## 3. Phasen-Plan (V1 → V2) `[MERGED: Orig-Phasen + GPT-Upgrades als gestufter Plan]`

### V1 — Snapshot + Enrichment + Kontext-Injection + einfaches Proaktiv

| Phase | Inhalt | Herkunft |
|--------|--------|----------|
| **A – Snapshot-Format + Enrichment** | Pro Event: `id`, `title`, `start`, `end`, `is_all_day`, `location` (trunc. 120 Z.) **+ enrichment**: `event_type`, `importance`, `movable` (siehe §4). | `[ORIG]` Format + `[GPT-TIP]` Semantic Layer |
| **B – Derived Summary** | Neben dem Roh-Snapshot ein kompakter **Derived Block**: `next_event`, `busy_today` (bool), `free_slots_today` (Liste), `day_load_percent`, `event_count_14d`. | `[GPT-TIP]` Memory Split |
| **C – Memory-Integration** | Upsert in `Memory`-Tabelle (`category = "calendar_snapshot"`, `is_core_fact = false`, JSON-Payload). Details siehe §12.1. | `[ORIG]` |
| **D – Schreibpfad / Sync** | Timer-basiert (alle 15–30 min) + bei `calendar-refresh` Event; TTL 20 min. | `[ORIG]` |
| **E – Intelligente Kontext-Injection** | Orchestrator: **nicht** immer kompletter Snapshot, sondern **gefiltert**: heute + morgen Termine vollständig, Rest nur Derived Summary. Max. ~3500 Zeichen. Wenn stale → ehrlich „Stand evtl. älter" oder einmalig Tool nachladen. | `[ORIG]` Injection + `[GPT-TIP]` „Intelligent Injection" |
| **F – Konflikt-Erkennung** | Overlap-Check Snapshot vs. User-Message: Extrahiertes Datum/Zeitfenster prüfen; Konflikte typisiert als `hard` (direkte Überschneidung), `soft` (< 1h Abstand), `load` (> 6 Termine am Tag). | `[GPT-TIP]` Conflict Types |
| **G – Proaktive Regeln (V1)** | Feature-Flag `JANUS_CALENDAR_PROACTIVE_HINTS` (default: off → on nach Tests). Max. **ein** Satz bei `hard`/`soft`-Konflikt. Formulierung: Fakt + optionale Frage, **kein** Moralurteil. | `[ORIG]` Policy + `[GPT-TIP]` Levels |
| **H – Tests** | Unit: Enrichment, Overlap, Derived Block; Integration: Mock-Snapshot + User-Message-Szenarien. | `[ORIG]` |

**Reihenfolge:** A → B → C → D → E → F → G → H (parallel: E+F nach C+D).

### V2-Backlog (nach stabilem V1)

| Thema | Beschreibung | Herkunft |
|-------|-------------|----------|
| **Intent-Detection** | Dediziertes NLP-Modul oder Prompt-Chain: User-Message → strukturierter Intent (`travel`, `meeting`, `leisure`, …) + Zeitfenster-Extraktion → reicherer Overlap. | `[GPT-TIP]` Intent Matching |
| **Handlungs-Vorschläge** | Bei Konflikt nicht nur warnen, sondern „Soll ich verschieben/absagen?" + Tool-Aufruf-Pipeline bei Bestätigung. | `[GPT-TIP]` Proactive Level 3 |
| **Push-Timing** | 10 min vor Termin → Hinweis; morgens → Tagesübersicht; bei Überladung → Warnung. Erfordert Frontend-Timer/Tray. | `[GPT-TIP]` Proactive Timing |
| **LLM-basiertes Scoring** | Importance/Movability nicht nur per Heuristik, sondern LLM-batch-enrichment (z. B. bei erstem Sync eines Events). | `[GPT-TIP]` erweitert |

---

## 4. Semantic Enrichment (Event-Klassifikation) `[GPT-TIP, MERGED]`

Jedes Event im Snapshot erhält **drei abgeleitete Felder** (rein regelbasiert in V1, kein LLM nötig):

### 4.1 `event_type`

| Regel (Titel-/Ort-Heuristik) | Typ |
|-------------------------------|-----|
| Titel enthält: `meeting`, `call`, `standup`, `sync`, `1:1` | `meeting` |
| Titel enthält: `arzt`, `zahnarzt`, `doctor`, `termin bei` | `appointment` |
| Titel enthält: `fokus`, `focus`, `deep work`, `blocker` | `focus` |
| Titel enthält: `geburtstag`, `birthday`, `feier` | `personal` |
| Titel enthält: `reise`, `flug`, `flight`, `fahrt` | `travel` |
| Sonst | `other` |

### 4.2 `importance`

| Regel | Wert |
|-------|------|
| `event_type` in (`appointment`, `travel`) ODER Titel enthält `urgent`, `wichtig`, `deadline` | `high` |
| `event_type` = `meeting` | `medium` |
| Ganztägig ohne Titel-Signal ODER `event_type` in (`focus`, `personal`, `other`) | `low` |

### 4.3 `movable`

| Regel | Wert |
|-------|------|
| `importance` = `high` | `false` |
| Event hat > 2 Teilnehmer (wenn verfügbar) oder ist recurring | `false` |
| Sonst | `true` |

**Speicherung:** Diese drei Felder stehen **im JSON pro Event** neben den Basisdaten.  
**Erweiterung V2:** LLM-Batch-Enrichment für mehrdeutige Titel (z. B. „Thomas" allein → unknown).

---

## 5. Derived Summary Block `[GPT-TIP, MERGED]`

Neben dem Event-Array wird beim Sync ein kompakter **Derived Block** erzeugt und im selben JSON gespeichert:

```json
{
  "v": 1,
  "generated_at": "2026-05-02T08:15:00Z",
  "tz": "Europe/Berlin",
  "derived": {
    "next_event": { "title": "Team Sync", "start": "...", "importance": "medium" },
    "busy_today": true,
    "free_slots_today": ["08:00-09:30", "12:00-13:00"],
    "day_load_percent": 72,
    "event_count_14d": 23,
    "overflow_count": 0
  },
  "events": [ ... ]
}
```

**Vorteil:** Der Orchestrator kann für einfache Fragen („Bin ich heute frei?") **nur den Derived Block** injizieren (~200 Token statt 1500+).

---

## 6. Konflikt-Typen `[GPT-TIP, MERGED]`

| Typ | Definition | Reaktion (V1) |
|-----|-----------|---------------|
| **`hard`** | Event-Zeitraum überlappt mit genanntem Zeitfenster des Nutzers. | Proaktiver Hinweis (wenn Flag on). |
| **`soft`** | Kein direkter Overlap, aber < 60 Min Abstand (Reisezeit, Puffer). | Optional erwähnen, nur bei `importance >= medium`. |
| **`load`** | Tag hat > 6 Termine oder > 6h gebucht, Nutzer plant Zusätzliches. | Optional: „Dein Tag ist ziemlich voll — möchtest du trotzdem?" |

---

## 7. Sync- & Frische-Regeln `[ORIG]`

- Jeder Snapshot trägt **`generated_at`** (UTC) und **`source`** (`google`, …).
- **TTL / Stale-Policy:** Snapshot älter als 20 min → Orchestrator darf einmalig Tool-Abruf nachziehen oder ehrlich „Stand evtl. älter".
- **Löschen / Diff:** Snapshot ist **Full-Replace** (Upsert) — keine inkrementellen Patches in V1; entfallene Events sind automatisch weg.

---

## 8. Privacy & Nutzerkontrolle `[ORIG]`

- Einstellung: **Kalender-Mirror aktiv** (default: an, falls DSGVO-konform mit bestehender Kalender-Einwilligung).
- Keine Speicherung sensibler Freitexte über das definierte Schema hinaus.
- **Teilnehmer-E-Mails** erst ab V2 und nur wenn explizit für `movable`-Heuristik benötigt.

---

## 9. Proaktive Policy `[ORIG + GPT-TIP MERGED]`

### V1 (konservativ, robust)

- **Nur** wenn (a) Snapshot frisch, (b) Nutzer einen **konkreten Tag** nennt oder Reise/Plan andeutet, (c) Konflikt-Typ `hard` oder `soft`.
- **Max. ein** proaktiver Satz. Formulierung: **Fakt** + optionale **kurze Frage**.
- Beispiel: „Übrigens: Donnerstag um 14:00 hast du ein Team-Meeting (Wichtigkeit: mittel). Soll ich dir mehr dazu sagen?"
- **Kein** Moralurteil, **keine** ungefragt ausgelösten Aktionen.

### V2 (Handlung — Backlog)

- Bei `hard`-Konflikt: Vorschlag mit konkreter Aktion → „Soll ich das Meeting auf Freitag verschieben?"
- Nur nach expliziter Nutzer-Bestätigung wird Calendar-Tool aufgerufen.

---

## 10. Akzeptanzkriterien `[ORIG + NEW]`

- [x] Mit aktivem Kalender-Account existiert ein **strukturierter Snapshot** inkl. Enrichment + Derived Block.
- [x] Chat kann „Termine heute" **ohne** sichtbaren Tool-Call beantworten, wenn Snapshot aktuell; sonst **graceful** Fallback.
- [x] `[NEW]` Derived Block allein reicht für: „Bin ich heute frei?", „Wie voll ist mein Tag?".
- [x] Beispiel-Szenario **Donnerstag / Tante Erna**: System erkennt Donnerstag + meldet konkreten kollidierenden Termin **mit Typ und Wichtigkeit**.
- [x] `[NEW]` Enrichment-Felder (`event_type`, `importance`, `movable`) in mindestens 5 Unit-Test-Cases korrekt.
- [x] `[NEW]` Konflikt-Typen (`hard` / `soft` / `load`) in Overlap-Tests korrekt.
- [x] Schalter/Flag: Mirror **aus** → Verhalten wie heute (Tool-basiert), keine falschen Fakten.
- [x] Post-Impl-Doku + Verweis in `PROJECT_STATE.md` / `TECH_PROJECT_INVENTORY.md`.

---

## 11. Risiken `[ORIG + NEW]`

| Risiko | Mitigation |
|--------|-----------|
| **Token-Druck** bei großen Snapshots | Striktes Cap (3500 Z.); Derived Block als Kurzform; intelligente Injection (nur heute+morgen). |
| **Race** (Nutzer ändert Termin, Snapshot alt) | TTL 20 min, optional „Stand von …" in Antwort. |
| **Doppelte Wahrheit** (Memory vs. API) | Memory ist Cache/Spiegel, nie autoritative Quelle für Buchungen. Klarstellen im Prompt. |
| `[NEW]` **Enrichment-Fehler** (falsche Importance) | Heuristik konservativ (Fallback = `other` / `low` / `true`); V2: LLM-basiertes Scoring. |
| `[NEW]` **„Nerviger" Assistent** | Flag default off; max. 1 Satz; kein Moralurteil; Nutzer kann Mirror ganz deaktivieren. |

---

## 12. Referenzen `[ORIG]`

| Bereich | Pfade / Hinweise |
|--------|-------------------|
| Kalender-Tools | `backend/tools/calendar_tools.py` (`get_calendar_events`, …) |
| Calendar Service / API | `backend/services/calendar/calendar_service.py`, `backend/api/routers/calendar.py` |
| Memory / Tools | `backend/services/tool_executor.py`, Memory-Skills/Registry |
| Orchestrierung / Chat | `backend/services/chat_orchestrator.py`, `chat_request_workflow_state.py` |
| Vorgänger Epic Kalender-UI | `documentation/tasks/task_058_calendar_modal_diamond_plan.md` |
| Tages-Panel (nur UI-Bezug) | `documentation/tasks/task_calendar_day_widget_rail_diamond.md` |

---

## 13. Implementation Log

| Datum | Eintrag |
|-------|---------|
| 2026-05-01 | Task-Datei angelegt; Status PLANNED. |
| 2026-05-01 | §12 (alt) ergänzt: Memory-Typ, Fenster, Proaktiv-Flag. |
| 2026-05-02 | **Diamond-Rewrite:** ChatGPT-Review integriert (Enrichment, Conflict Types, Derived Block, Intelligent Injection, V1/V2-Split). Herkunft jeder Änderung mit `[ORIG]`/`[GPT-TIP]`/`[MERGED]`/`[NEW]` markiert. |
| 2026-05-02 | **V1 umgesetzt:** `calendar_memory.py` erstellt (Snapshot, Enrichment, Derived Summary, Staleness, Konfliktlogik), Kalender-Router mit Memory-Upsert + `/api/calendar/sync/memory` verdrahtet, Chat-Orchestrator injiziert gefilterten Snapshot-Kontext und Proaktiv-Hinweise hinter `JANUS_CALENDAR_PROACTIVE_HINTS`. Tests: `backend/tests/test_calendar_memory.py`, bestehende Calendar-Modal-Tests grün. |
| 2026-05-02 | **Post-Impl-Doku abgeschlossen:** Akzeptanzkriterien abgehakt, Betriebsnotizen ergänzt, Status in `PROJECT_STATE.md`, `documentation/TECH_PROJECT_INVENTORY.md` und `documentation/04_PROJECT_INVENTORY_AND_STATUS.md` gespiegelt. |

---

## 14. Checkliste vor Start der Implementierung

- [x] **Abnahme** dieser Task-Datei (V1-Scope klar, V2-Backlog akzeptiert).
- [x] **Speicher-Mechanismus:** `Memory`-Tabelle mit `category = "calendar_snapshot"` (§12.1) oder dedizierte Tabelle.
- [x] **Fenster/Limits:** 14 Tage / max 30 Events / TTL 20 min / 3500-Zeichen-Cap (§12.2).
- [x] **Proaktiv:** Flag `JANUS_CALENDAR_PROACTIVE_HINTS`, default off → on nach Tests (§12.3).
- [x] **Enrichment-Heuristik:** Regelwerk §4 reicht für V1 oder Anpassungen nötig?

---

## 15. Vorgeschlagene Festlegungen (V1-Defaults) `[ORIG, leicht gestrafft]`

### 15.1 Memory-Typ

- **Bestehendes Memory-Modell** (`Memory`-Zeile), `category = "calendar_snapshot"`, `is_core_fact = false`.
- **Ein Eintrag pro Nutzer**, `content` = JSON (Schema-Version `v: 1`, `generated_at`, `tz`, `derived`, `events[]`).
- Alternative (nur bei Ablehnung): eigene Tabelle `user_calendar_mirror`.

### 15.2 Fenster / Größe

| Parameter | Default |
|-----------|---------|
| Zeitfenster | 14 Kalendertage ab heute (Nutzer-TZ) |
| Max. Events | 30 (sortiert nach Start); Rest als `overflow_count` |
| Felder pro Event | `id`, `title`, `start`, `end`, `is_all_day`, `location` (trunc 120 Z.) + Enrichment-Felder |
| Textblock-Cap für LLM | ~3500 Zeichen; bei Überlauf „… und N weitere" |
| TTL | 20 Minuten |

### 15.3 Proaktiv

| Aspekt | Default |
|--------|---------|
| Feature-Flag | `JANUS_CALENDAR_PROACTIVE_HINTS` (Env/Config) |
| Default V1.0 | `off` bis Overlap-Tests grün |
| Wenn `on` | Max. 1 Satz, nur bei `hard`/`soft`-Konflikt, kein Moralurteil |
| Privacy | Nur wenn Kalender-Spiegel aktiv (Einwilligung wie Kalender-Anbindung) |

---

## 16. Post-Implementation Notes (V1)

### 16.1 Implementierte Dateien

- `backend/services/calendar/calendar_memory.py` — Snapshot-Aufbau, Enrichment, Derived Summary, TTL/Staleness, Prompt-Rendering, Konflikt-/Proaktiv-Logik.
- `backend/api/routers/calendar.py` — opportunistischer Snapshot-Upsert bei Event-Loads und Mutationen; manueller Refresh über `/api/calendar/sync/memory`.
- `backend/services/chat_orchestrator.py` — gefilterte Kalender-Kontext-Injection in den bestehenden Memory-Block.
- `backend/services/orchestrator/chat_request_workflow_state.py` — Workflow-Felder für Snapshot-Kontext und Proaktiv-Hinweis.
- `backend/tests/test_calendar_memory.py` — fokussierte Unit-Tests für V1-Verhalten.

### 16.2 Betriebsverhalten

- `JANUS_CALENDAR_MIRROR_ENABLED` steuert den Memory-Spiegel; Default ist `true`.
- `JANUS_CALENDAR_PROACTIVE_HINTS` steuert proaktive Hinweise; Default ist `false`.
- Der Snapshot ist ein Cache, keine Quelle der Wahrheit. Mutationen laufen weiter ausschließlich über Kalender-Tools/API.
- Injektion erfolgt nur bei Kalender-/Planungssignalen und bleibt auf Derived Summary plus heute/morgen begrenzt.

### 16.3 Verifikation

- Befehl: `python -m pytest backend/tests/test_calendar_memory.py backend/tests/test_calendar_modal.py`
- Ergebnis: `26 passed`
- Hinweis: Nach Testende trat nur ein Sentry-Logging-Nachlauf auf; die Tests selbst waren grün.

---

## 17. V2-Backlog (Sammlung) `[GPT-TIP, bewertet]`

| Feature | Aufwand | Wert | Priorität |
|---------|---------|------|-----------|
| Intent-Detection (NLP/Prompt-Chain) | hoch | hoch | P1 nach V1 |
| Handlungs-Vorschläge bei Konflikt | mittel | hoch | P1 |
| LLM-basiertes Event-Scoring | mittel | mittel | P2 |
| Push-Benachrichtigungen (Tray/Timer) | hoch | hoch | P2 (Frontend-Architektur) |
| Morgenübersicht (täglicher Snapshot-Push) | niedrig | mittel | P3 |
