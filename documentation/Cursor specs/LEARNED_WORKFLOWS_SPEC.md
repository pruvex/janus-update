# Janus Learned Workflows (User-Routinen) — Feature-Spec & Umsetzungsplan

**Version:** 1.0.0  
**Datum:** 2026-07-07  
**Zielgruppe:** Codex / Cursor / Janus Diamond Pipeline  
**Status:** READY FOR IMPLEMENTATION  
**Epic-ID:** `EPIC-WORKFLOW-001`  
**Bezug:** Ergänzt Memory- und Intent-Pläne als **prozedurale Gedächtnisschicht** (Hermes-inspiriert, Janus-native)

---

## 0. Executive Summary

### Vision

Janus erkennt **erfolgreich abgeschlossene Multi-Step-Abläufe** und **bietet proaktiv** an, sie als wiederverwendbare **Routine** zu speichern. Der User muss keine Magic Phrase kennen — Janus fragt nach dem Erfolg:

> *„Soll ich diesen Ablauf als Routine speichern? Beim nächsten Mal reicht z.B. ‚Morgen-Routine‘.“*

**Kernprinzipien:**

| Prinzip | Bedeutung |
|---------|-----------|
| **Janus schlägt vor, User entscheidet** | Nie autonom speichern ohne Zustimmung |
| **Nur Registry-Skills** | Keine freien Shell-Befehle, keine agent-authored Tools |
| **Policy pro Step** | Gleiche Freigaben wie bei Einzelaufrufen |
| **Getrennt von Memory** | Fakten ≠ Abläufe — eigene Tabelle/Store |
| **Progressive Disclosure** | Routine-Index günstig im Prompt, Steps on-demand |

### Nicht im Scope (v1)

- Hermes-Style autonomes `skill_manage create` durch den Agent
- Community Skills Hub / Markdown-SKILL.md ohne Schema
- GEPA/Trace-Optimierung von Routinen
- Automatisches Ausführen von Routinen ohne User-Trigger

### Phasen-Übersicht

| Phase | Feature | Aufwand | Risiko |
|-------|---------|---------|--------|
| **1** | Routine-Store + Datenmodell | 2–3 Tage | Niedrig |
| **2** | Workflow-Detector (Post-Turn) | 3–5 Tage | Mittel |
| **3** | Proaktives Offer + Dialog | 3–4 Tage | Niedrig–Mittel |
| **4** | Routine-Ausführung (Macro-Runner) | 1–1,5 Wochen | Mittel |
| **5** | UI: Routinen verwalten | 1 Woche | Niedrig |

**Gesamt MVP (Phase 1–4):** ~3–4 Wochen  
**Mit UI (Phase 5):** ~4–5 Wochen

**Empfohlene Voraussetzung:** Intent-Upgrade (mindestens Phase 1–2) stabil — sonst werden falsche Abläufe angeboten.

---

## 1. Problem & Motivation

### 1.1 Gap vs. Hermes

Hermes wirbt mit „Aufgaben lernen“ via **procedural memory** (`SKILL.md`). Janus hat:

- ✅ Semantic Memory (Fakten) — Memory V2
- ⏳ Episodic Memory — Session-Search (Memory-Plan Phase C)
- ❌ **Procedural Memory** — fehlt

### 1.2 Warum nicht Hermes 1:1

| Hermes | Janus (dieses Feature) |
|--------|------------------------|
| Agent schreibt Skills autonom | Janus **bietet** Speichern an |
| Markdown, beliebige Prozeduren | JSON-Macro über **CapabilityRegistry** |
| Kein `risk_level` | Policy + `risk_level` pro Step geerbt |
| Curator im Hintergrund | User verwaltet Routinen explizit |

### 1.3 User Value

| Situation | Heute | Mit Learned Workflows |
|-----------|-------|----------------------|
| „Termine + Wetter + Mails“ jeden Morgen | User wiederholt 3 Prompts | „Morgen-Routine“ → 1 Trigger |
| PDF-Sortier-Flow | Jedes Mal neu erklären | Gespeicherte Routine |
| Kontakt vorbereiten | Ad-hoc Tool-Kette | Wiederverwendbarer Macro |

---

## 2. Produktverhalten (UX)

### 2.1 Standard-Flow: Janus bietet an

```text
1. User stellt Multi-Step-Anfrage
2. Janus führt Tool-Loop aus (≥2 verschiedene Skills, Erfolg)
3. Janus antwortet mit Ergebnis
4. Offer-Gate prüft: soll angeboten werden?
5. Janus: „Soll ich diesen Ablauf als Routine speichern? …“
6. User: Ja → Name/Trigger festlegen → gespeichert
         Nein → nichts, Cooldown
         „Nicht mehr fragen“ → Routine-ID auf Denylist
```

### 2.2 Beispiel-Dialog

```
User:  Zeig mir meine Termine heute, das Wetter in München und ungelesene Mails.

Janus: Du hast 3 Termine, es werden 18°C, 2 ungelesene Mails.
       
       Soll ich diesen Ablauf als Routine speichern?
       Beim nächsten Mal reicht z.B. „Morgen-Routine“ oder „Start meinen Tag“.

User:  Ja, nenn es Morgen-Routine.

Janus: Routine „Morgen-Routine“ ist gespeichert. Sag Bescheid, wenn du sie ändern willst.
```

### 2.3 Fallback: User-initiiert

User kann jederzeit sagen:

- „Speicher das als Routine“
- „Merke dir diesen Ablauf“
- „Das soll eine Routine werden“

→ Gleicher Speicher-Flow wie nach „Ja“ auf das Angebot.

### 2.4 Routinen ausführen

```
User:  Morgen-Routine

Janus: [führt gespeicherte Steps aus]
       [kompakte Zusammenfassung aller Step-Ergebnisse]
```

### 2.5 Ablehnung & Cooldown

| User-Antwort | System-Reaktion |
|--------------|-----------------|
| „Ja“ / „Ja, nenn es X“ | Speichern, `user_approved=true` |
| „Nein“ / „Nein danke“ | Kein Speichern, **Session-Cooldown** (kein weiteres Offer diese Session) |
| „Nicht mehr fragen“ / „Später nicht“ | Step-Fingerprint auf **Denylist** |
| Ignorieren | Kein Speichern, Offer nicht wiederholen für denselben Fingerprint |

**Globale User-Präferenz (Settings):**

- `routines_offer_enabled: true` (default)
- `routines_offer_enabled: false` → nie anbieten, nur expliziter User-Request

---

## 3. Wann Janus anbieten darf (Offer-Gate)

### 3.1 Positive Bedingungen (alle müssen erfüllt sein)

| # | Bedingung |
|---|-----------|
| 1 | Turn erfolgreich abgeschlossen (kein Error-Abort, kein Policy-Block mid-flow) |
| 2 | **≥2 verschiedene** `skill_id`s in `wf.kpi_tool_status` / Tool-Trace |
| 3 | Mindestens **1 Step** mit `risk_level` ≥ `medium` ODER **≥3 Steps** gesamt |
| 4 | Kein reiner Recall-Turn (`personal_recall` ohne Tools) |
| 5 | Kein Greeting/Smalltalk/Help-Only |
| 6 | `routines_offer_enabled` = true |
| 7 | Step-Fingerprint nicht auf Denylist |
| 8 | Kein Session-Cooldown aktiv |
| 9 | Ähnliche Routine existiert nicht bereits (Jaccard Steps ≥ 0.85 → skip) |

### 3.2 Negative Bedingungen (nie anbieten)

| Situation | Grund |
|-----------|-------|
| Medical/Health-Turn | Falsche Automatisierung riskant |
| Policy-Consent-Dialog | UX-Kontext passt nicht |
| Einzel-Tool-Turn | Zu trivial |
| Fehlgeschlagener Tool-Loop | Nichts Worth Learning |
| Ambiguity-Klärungs-Turn | Kein echter Ablauf |
| `memory_write` allein | Das ist Memory, nicht Workflow |

### 3.3 Offer-Text-Regeln

- Kurz, **ein** Angebot pro erfolgreichem Multi-Step-Turn
- Vorschlag für Trigger-Name aus Step-Kontext ableiten (optional, nicht erzwingen)
- Kein Offer in derselben Antwort wie Medical-Warnungen

---

## 4. Architektur

### 4.1 Schichten-Modell (Janus Gedächtnis)

```text
Semantic   → Memory V2 (Fakten über User/Welt)
Episodic   → Session-Search (was wurde gesagt)
Procedural → Learned Workflows (dieses Feature) — WIE etwas erledigt wird
Task State → Chat History (ephemeral)
```

### 4.2 Komponenten

```
┌─────────────────────────────────────────────────────────────────┐
│                     CHAT ORCHESTRATOR                            │
│  execution_engine tool loop → response_finalizer                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  workflow_detector.py                                            │
│  - extrahiert Step-Trace aus wf.kpi_tool_status                  │
│  - baut StepFingerprint (skill_ids, arg_keys, order)             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  workflow_offer_service.py                                       │
│  - Offer-Gate (Abschnitt 3)                                      │
│  - Cooldown / Denylist                                           │
│  - generiert Offer-Text                                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ User: Ja
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  routine_store.py (CRUD)                                         │
│  - SQLite user_routines                                          │
│  - Validierung gegen CapabilityRegistry                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Trigger: "Morgen-Routine"
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  routine_runner.py                                               │
│  - führt Steps sequenziell aus                                   │
│  - Policy pro Step                                               │
│  - aggregiert Ergebnis                                           │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Integration mit bestehenden Systemen

| System | Integration |
|--------|-------------|
| `CapabilityRegistry` | Nur `skill_id`s aus Registry erlaubt |
| `SkillSelector` | Intent `routine_execute` → Runner |
| `IntentEngine` | Neuer Intent: `detect_routine_trigger` |
| `execution_engine` | Runner nutzt bestehenden Tool-Executor |
| Policy-System | Pro Step `grant_permission` wie heute |
| Memory V2 | `{{user.city}}` etc. in Args via Placeholder-Resolver |

---

## 5. Datenmodell

### 5.1 Tabelle `user_routines`

```sql
CREATE TABLE user_routines (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,           -- FK users, oder local profile id
    name            VARCHAR(100) NOT NULL,      -- "Morgen-Routine"
    description     TEXT,                       -- optional, menschenlesbar
    trigger_phrases JSON NOT NULL DEFAULT '[]', -- ["morgen-routine", "start meinen tag"]
    steps_json      JSON NOT NULL,              -- siehe 5.2
    step_fingerprint VARCHAR(64) NOT NULL,      -- SHA256 normalisierte Step-IDs
    source_chat_id  INTEGER,                    -- wo gelernt
    source_turn_id  INTEGER,                    -- optional
    user_approved   BOOLEAN NOT NULL DEFAULT 0,
    offer_state     VARCHAR(20) DEFAULT 'saved', -- saved | declined | denied_forever
    run_count       INTEGER DEFAULT 0,
    last_run_at     DATETIME,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_routines_user ON user_routines(user_id);
CREATE UNIQUE INDEX idx_routines_fingerprint ON user_routines(user_id, step_fingerprint);
```

### 5.2 Step-Schema (`steps_json`)

```json
{
  "version": 1,
  "steps": [
    {
      "order": 1,
      "skill_id": "calendar.list_events",
      "args": {
        "range": "today"
      },
      "arg_bindings": {}
    },
    {
      "order": 2,
      "skill_id": "system.weather",
      "args": {
        "city": "{{user.city}}"
      },
      "arg_bindings": {
        "city": "memory:wohnort"
      }
    },
    {
      "order": 3,
      "skill_id": "communication.list_emails",
      "args": {
        "unread_only": true
      },
      "arg_bindings": {}
    }
  ]
}
```

**Regeln:**

- `skill_id` muss in `CapabilityRegistry._available_skills` existieren
- `args` nur JSON-primitive + erlaubte Placeholders
- Keine rohen User-Strings mit PII in `args` — Bindings über `arg_bindings`
- `risk_level` wird zur Laufzeit vom Skill-JSON gelesen, nicht gespeichert

### 5.3 Step-Fingerprint

```python
def build_step_fingerprint(steps: List[RoutineStep]) -> str:
    """
    Normalisiert: sortierte skill_ids + arg_keys (nicht Werte).
    Beispiel: calendar.list_events:range|communication.list_emails:unread_only|system.weather:city
    """
```

Zweck: Duplikat-Erkennung, Denylist, „ähnliche Routine existiert“.

### 5.4 Tabelle `user_routine_offer_log` (Cooldown)

```sql
CREATE TABLE user_routine_offer_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    step_fingerprint VARCHAR(64) NOT NULL,
    offer_state     VARCHAR(20) NOT NULL,  -- offered | accepted | declined | denied_forever
    chat_id         INTEGER,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. Feature-Flags

```python
# backend/config.py oder backend/services/workflow/routine_config.py

ROUTINES_ENABLED = os.getenv("ROUTINES_ENABLED", "false").lower() == "true"
ROUTINES_PROACTIVE_OFFER_ENABLED = os.getenv("ROUTINES_PROACTIVE_OFFER_ENABLED", "false").lower() == "true"
ROUTINES_EXECUTION_ENABLED = os.getenv("ROUTINES_EXECUTION_ENABLED", "false").lower() == "true"
ROUTINES_MIN_STEPS = int(os.getenv("ROUTINES_MIN_STEPS", "2"))
ROUTINES_OFFER_COOLDOWN_PER_SESSION = os.getenv("ROUTINES_OFFER_COOLDOWN_PER_SESSION", "true").lower() == "true"
```

**Rollback:** Alle Flags `false` → kein Offer, kein Runner, DB bleibt unberührt.

---

## 7. Phasen-Detail

### Phase 1 — Routine-Store + Datenmodell (2–3 Tage)

**Dateien:**

```
backend/data/models.py                    # UserRoutine, UserRoutineOfferLog
backend/data/database.py                # Migration
backend/services/workflow/routine_store.py
backend/services/workflow/routine_schema.py   # Pydantic
backend/tests/test_routine_store.py
```

**Akzeptanzkriterien:**

- [ ] CRUD: create, read, update, delete, list_by_user
- [ ] Fingerprint-Dedup: zweiter Create mit gleichem Fingerprint → Merge oder Reject
- [ ] Registry-Validation: unbekannte `skill_id` → HTTP 400 / Tool-Error
- [ ] Tests: 10 Unit-Tests

---

### Phase 2 — Workflow-Detector (3–5 Tage)

**Dateien:**

```
backend/services/workflow/workflow_detector.py
backend/services/workflow/step_trace_extractor.py
backend/tests/test_workflow_detector.py
```

**Input:** `wf.kpi_tool_status`, Tool-Call-Log aus Execution-Engine

**Output:**

```python
@dataclass
class DetectedWorkflow:
    steps: List[RoutineStep]
    fingerprint: str
    skill_count: int
    is_offer_candidate: bool
    reject_reason: Optional[str]
```

**Akzeptanzkriterien:**

- [ ] Extrahiert korrekte Step-Reihenfolge aus Multi-Tool-Turn
- [ ] Ignoriert fehlgeschlagene Steps
- [ ] `is_offer_candidate` korreliert mit Offer-Gate (Abschnitt 3)
- [ ] Tests mit Fixtures aus echten KPI-Traces

---

### Phase 3 — Proaktives Offer + Dialog (3–4 Tage)

**Dateien:**

```
backend/services/workflow/workflow_offer_service.py
backend/services/orchestrator/intent_engine.py   # detect_routine_save_confirm, detect_routine_trigger
backend/services/orchestrator/response_finalizer.py  # Offer anhängen
backend/tests/test_workflow_offer_service.py
backend/tests/test_routine_intent_patterns.py
```

**Intent-Patterns (neu):**

```python
# Bestätigung nach Offer
_ROUTINE_SAVE_CONFIRM_RE = re.compile(
    r"\b(?:ja|ok|okay|gerne|speicher|speichern|mach das|klar)\b", re.I)

# Expliziter User-Request
_ROUTINE_SAVE_REQUEST_RE = re.compile(
    r"\b(?:speicher.*(?:routine|ablauf)|merk.*(?:ablauf|routine)|als routine)\b", re.I)

# Ausführung
_ROUTINE_TRIGGER_RE = ...  # Match gegen trigger_phrases in DB
```

**Akzeptanzkriterien:**

- [ ] Nach Multi-Step-Erfolg: Offer-Text in Antwort (wenn Gate passt)
- [ ] „Ja“ → Routine gespeichert mit User-gewähltem Namen
- [ ] „Nein“ → kein Speichern, Session-Cooldown
- [ ] „Nicht mehr fragen“ → Fingerprint auf Denylist
- [ ] `ROUTINES_PROACTIVE_OFFER_ENABLED=false` → kein Offer, expliziter Request funktioniert
- [ ] Max. 1 Offer pro Session (wenn Cooldown an)

---

### Phase 4 — Routine-Ausführung (1–1,5 Wochen)

**Dateien:**

```
backend/services/workflow/routine_runner.py
backend/services/workflow/placeholder_resolver.py   # {{user.city}} aus Memory
backend/services/orchestrator/intent_engine.py    # detect_routine_trigger
backend/tests/test_routine_runner.py
backend/tests/test_routine_placeholder_resolver.py
```

**Runner-Verhalten:**

1. Trigger matcht `trigger_phrases` (fuzzy, normalisiert)
2. Steps sequenziell über bestehenden `tool_executor`
3. Policy-Gate pro Step — bei Block: abbrechen + erklären
4. Ergebnisse aggregieren → eine Antwort
5. `run_count++`, `last_run_at` update

**Akzeptanzkriterien:**

- [ ] „Morgen-Routine“ führt alle Steps aus
- [ ] Placeholder `{{user.city}}` aus Memory aufgelöst
- [ ] Policy-Block bei Step 2 → Step 3 nicht ausgeführt, User informiert
- [ ] Unbekannte Routine → „Keine Routine gefunden“
- [ ] Integrationstest: Save → Execute Roundtrip

---

### Phase 5 — UI Routinen verwalten (1 Woche, optional MVP+)

**Scope:**

- Liste gespeicherter Routinen
- Umbenennen, Trigger bearbeiten, löschen
- Toggle „Routine-Vorschläge“ (`routines_offer_enabled`)
- Kein Step-Editor in v1 (nur löschen + neu speichern)

**Dateien:** Frontend-Modal + `GET/PUT/DELETE /api/routines`

---

## 8. API-Endpunkte

```
GET    /api/routines              # Liste User-Routinen
GET    /api/routines/{id}         # Detail
POST   /api/routines              # Manuell erstellen (optional)
PUT    /api/routines/{id}         # Name/Trigger ändern
DELETE /api/routines/{id}         # Löschen
POST   /api/routines/{id}/run     # Manuell ausführen (Debug)
GET    /api/routines/settings     # offer_enabled etc.
PUT    /api/routines/settings     # Präferenzen
```

---

## 9. Sicherheit & Privacy

| Risiko | Mitigation |
|--------|------------|
| Routine führt gefährliche Skills aus | Nur Registry-Skills; `risk_level` high → Policy wie heute |
| PII in gespeicherten Args | `arg_bindings` statt Rohwerte; Sanitizer beim Speichern |
| Routine mit veralteten Permissions | Re-Check Policy bei **jeder** Ausführung |
| Zu aggressive Offers | Offer-Gate + Cooldown + Settings-Toggle |
| Cross-User-Leak | `user_id` strikt in allen Queries |
| Medical-Workflows automatisiert | Medical-Turns vom Offer ausgeschlossen |

---

## 10. Testplan

### 10.1 Unit & Integration

```bash
python -m pytest backend/tests/test_routine_store.py -v
python -m pytest backend/tests/test_workflow_detector.py -v
python -m pytest backend/tests/test_workflow_offer_service.py -v
python -m pytest backend/tests/test_routine_runner.py -v
python -m pytest backend/tests/test_routine_placeholder_resolver.py -v
```

### 10.2 Live-Szenarien

| # | Szenario | Erwartung |
|---|----------|-----------|
| L1 | Termine + Wetter + Mails → Erfolg | Offer erscheint |
| L2 | User: „Ja, Morgen-Routine“ | Gespeichert, Trigger funktioniert |
| L3 | „Morgen-Routine“ (neuer Tag) | 3 Steps ausgeführt, Summary |
| L4 | „Nein“ auf Offer | Nicht gespeichert, kein 2. Offer diese Session |
| L5 | „Wie heißt mein Hund?“ | Kein Offer |
| L6 | Policy-Block bei Mail-Step | Runner stoppt, erklärt |
| L7 | „Speicher das als Routine“ (explizit) | Speichern ohne vorheriges Offer |
| L8 | Gleicher Ablauf 2× | 2. Mal kein Offer (Fingerprint-Dedup) |

---

## 11. Aufwand & Risiko — Gesamt

| Phase | Aufwand | Risiko | Abhängigkeit |
|-------|---------|--------|--------------|
| 1 Store | 2–3 Tage | Niedrig | — |
| 2 Detector | 3–5 Tage | Mittel | KPI-Trace zuverlässig |
| 3 Offer | 3–4 Tage | Niedrig–Mittel | Phase 2 |
| 4 Runner | 1–1,5 Wochen | Mittel | Phase 1, Policy-System |
| 5 UI | 1 Woche | Niedrig | Phase 4 |
| **MVP 1–4** | **~3–4 Wochen** | **Mittel** | Intent stabil empfohlen |

**Größtes Risiko:** Falsche Offers bei instabilem Intent-Routing → Intent-Plan Phase 1–2 zuerst oder parallel starten.

---

## 12. Codex-Startprompt

```text
Implementiere Phase 1 + Phase 2 aus:
documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md

Scope Phase 1:
- user_routines + user_routine_offer_log Tabellen
- backend/services/workflow/routine_store.py
- backend/services/workflow/routine_schema.py
- backend/tests/test_routine_store.py

Scope Phase 2:
- backend/services/workflow/workflow_detector.py
- backend/services/workflow/step_trace_extractor.py
- backend/tests/test_workflow_detector.py

Constraints:
- ROUTINES_ENABLED=false als Default
- Nur skill_ids aus CapabilityRegistry erlaubt
- Kein Offer-UI, kein Runner in diesem Slice
- Keine Änderung an Memory V2 oder IntentEngine (außer Imports vorbereiten)

Validation:
python -m pytest backend/tests/test_routine_store.py backend/tests/test_workflow_detector.py -v
```

---

## 13. Entscheidungslog

| Entscheidung | Gewählt | Verworfen |
|--------------|---------|-----------|
| Wer initiiert Speichern? | **Janus bietet an** | Nur User-Magic-Phrase |
| Zustimmung | Explizit „Ja“ | Autonomes Speichern |
| Format | JSON-Macro | Hermes SKILL.md |
| Skill-Quelle | CapabilityRegistry only | Freie Shell-Befehle |
| Args mit PII | Placeholder + bindings | Rohwerte speichern |
| Duplikate | Fingerprint-Dedup | Unbegrenzt speichern |

---

## 14. Spätere Erweiterungen (v2+)

- Vorschlag nach 3× gleichem Muster ohne vorheriges Offer
- Routine teilen/exportieren
- Step-Editor in UI
- Bedingte Steps („nur wenn Termine > 0“)
- Routine aus Session-Search rekonstruieren (braucht Memory-Plan Phase C)

---

**END OF SPEC**
