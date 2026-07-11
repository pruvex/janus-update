# Janus Memory Upgrade — Umsetzungsplan (Hermes-inspiriert)

**Version:** 1.0.0  
**Datum:** 2026-07-07  
**Zielgruppe:** Codex / Cursor / Janus Diamond Pipeline  
**Status:** READY FOR IMPLEMENTATION  
**Epic-ID:** `EPIC-MEM-HERMES-001`

---

## 0. Executive Summary

Dieser Plan beschreibt die **phasenweise** Erweiterung des Janus Memory Systems V2 um drei Hermes-inspirierte Bausteine:

| Phase | Feature | Aufwand | Risiko | Priorität |
|-------|---------|---------|--------|-----------|
| **A** | Hot-Layer-Caps verschärfen | 1–2 Tage | Niedrig | P1 |
| **B** | On-Demand Memory Injection | 1–2 Tage | Niedrig | P1 |
| **C** | Session-Search (FTS5 über Messages) | 1–2 Wochen | Mittel | P0 (größter Nutzen) |
| **D** | Frozen Core + dynamischer Rest | 3–5 Tage | Hoch | P2 (optional) |
| **E** | USER.md Core-Export / Editierbarkeit | 2–3 Tage | Niedrig | P3 |

**Nicht im Scope:** Pluggable External Memory Provider (Mem0/Honcho) — erst bei konkretem Bedarf.

**Grundregel:** Phasen **sequenziell** umsetzen. Keine Phase D vor abgeschlossener Phase C.

---

## 1. Ausgangslage (Ist-Zustand)

### 1.1 Was Janus heute hat

- **Fakten-Gedächtnis:** SQLite `memories` + Embeddings + Float-Priority (0.0–1.0)
- **Retrieval:** `retrieve_diamond_slots()` in `backend/services/memory/retrieval_service.py`
- **Injection:** Pro Turn im `chat_orchestrator.py` (~Zeile 4600), query-basiert
- **Budget:** Knapsack in `backend/services/memory_budget.py`, Feature-Flag `MEMORY_V2_ENABLED`
- **Tools:** `memory_write`, `memory_read`, `memory_update`, `memory_history` in `backend/tools/memory_tools.py`
- **Safety:** Health-Injector, Identity-Hard-Lock, Contact-Scope-Guards, Medical-Override
- **FTS5:** Bereits vorhanden für **Dokumenten-RAG** in `backend/services/rag/fts_store.py` — **nicht** für Chat-Messages

### 1.2 Was fehlt (Gap vs. Hermes)

| Hermes-Layer | Janus-Äquivalent | Status |
|--------------|------------------|--------|
| L1 Hot Layer (`USER.md`/`MEMORY.md`) | Core Memories (priority ≥ 0.95) | ✅ vorhanden, aber unbounded |
| L2 Session Search (FTS5) | — | ❌ fehlt |
| Frozen Snapshot (Prefix-Cache) | Live-Injection pro Turn | ❌ fehlt |
| On-Demand Recall | Teilweise (`_is_generic_memory_suppressed_query`) | ⚠️ unvollständig |

### 1.3 Referenz-Dateien (Source of Truth)

```
backend/services/memory/retrieval_service.py   # retrieve_diamond_slots, Suppression
backend/services/memory_budget.py              # Knapsack, MEMORY_V2_ENABLED
backend/services/chat_orchestrator.py          # Memory-Injection-Pipeline
backend/tools/memory_tools.py                  # Tool-Suite, Sanitizer
backend/services/rag/fts_store.py              # FTS5-Pattern (wiederverwenden)
backend/data/models.py                         # Message, Memory, ContextCompression
backend/services/memory_enricher.py            # Priority-Regeln
backend/services/memory_extractor.py           # Auto-Extraktion
```

---

## 2. Architektur-Zielbild

```text
User Query
    │
    ├─ Intent: external/web/calendar?     → Memory-Skip (Phase B)
    │
    ├─ Intent: episodic/history recall?     → session_search Tool (Phase C)
    │
    └─ Intent: personal/fact recall?
           │
           ├─ Frozen Core Block (Phase D, optional)
           │     priority >= 0.95, session-cached, max N tokens
           │
           └─ Dynamic Slots (bestehend)
                 retrieve_diamond_slots() minus Core
                 query-embedding + knapsack
```

**Schichten nach Umsetzung:**

| Schicht | Mechanismus | Scope | Injection |
|---------|-------------|-------|-----------|
| **Semantic Hot** | Core-Fakten (capped) | Global, cross-chat | Always-on (frozen oder live) |
| **Semantic Query** | Vektor-Retrieval | Global | Pro Turn, query-basiert |
| **Episodic** | FTS5 über `messages` | Cross-session | On-demand via Tool |
| **Procedural** | Skills | — | Unverändert |
| **Task State** | Chat History | Lokal | Unverändert |

---

## 3. Feature-Flags & Rollback

Alle Phasen hinter Env-Flags — Default `false` bis validiert:

```python
# backend/config.py oder backend/services/memory_budget.py

MEMORY_HOT_LAYER_CAP_ENABLED = os.getenv("MEMORY_HOT_LAYER_CAP_ENABLED", "false").lower() == "true"
MEMORY_ON_DEMAND_INJECTION_ENABLED = os.getenv("MEMORY_ON_DEMAND_INJECTION_ENABLED", "false").lower() == "true"
MEMORY_SESSION_SEARCH_ENABLED = os.getenv("MEMORY_SESSION_SEARCH_ENABLED", "false").lower() == "true"
MEMORY_FROZEN_CORE_ENABLED = os.getenv("MEMORY_FROZEN_CORE_ENABLED", "false").lower() == "true"
MEMORY_CORE_EXPORT_ENABLED = os.getenv("MEMORY_CORE_EXPORT_ENABLED", "false").lower() == "true"
```

**Rollback:** Flag auf `false` → alter Codepfad ohne DB-Migration-Rollback.

---

## 4. Phase A — Hot-Layer-Caps (P1)

### 4.1 Ziel

Core-Identity-Fakten (priority ≥ 0.95) hart auf ein Token-Budget begrenzen. Verhindert Akkumulation und unvorhersehbaren Recall.

### 4.2 Akzeptanzkriterien

- [ ] `core_always`-Slots nie > `MAX_CORE_ALWAYS_TOKENS` (aktuell 400, ggf. auf 350 senken)
- [ ] Bei Überlauf: höchste Priority gewinnt, Rest nur via `memory_read` / Session-Search
- [ ] Health/Allergie-Fakten (tags: `health`, `medical`) **nie** aus Core entfernen — Protected Slots
- [ ] Metrik `slots_dropped_core_cap` in `memory_observability.py`
- [ ] Bestehende Tests grün + 3 neue Unit-Tests

### 4.3 Dateien

| Aktion | Datei |
|--------|-------|
| MODIFY | `backend/services/memory/retrieval_service.py` |
| MODIFY | `backend/services/memory_budget.py` |
| MODIFY | `backend/services/memory_observability.py` |
| CREATE | `backend/tests/test_memory_hot_layer_cap.py` |

### 4.4 Implementierungsschritte

1. Konstante `CORE_PROTECTED_TAGS = frozenset({"health", "medical"})` definieren
2. In `retrieve_diamond_slots()`: Core-Always-Slots sammeln → Protected zuerst → Rest nach Priority → Cap anwenden
3. Logging: `[CORE-CAP] dropped={n} protected={m} budget={tk}`
4. Flag `MEMORY_HOT_LAYER_CAP_ENABLED` prüfen; wenn `false` → alter Pfad
5. Tests:
   - 10 Core-Fakten, Budget für 5 → Top-5 + alle Protected
   - Kein Health-Fakt wird gedroppt
   - Flag off → unverändertes Verhalten

### 4.5 Validierung

```bash
python -m pytest backend/tests/test_memory_hot_layer_cap.py -v
python -m pytest backend/tests/test_memory_diamond.py backend/tests/test_memory_regression.py -q
```

### 4.6 Risiko

**Niedrig.** Chirurgische Änderung, schnell revertierbar.

---

## 5. Phase B — On-Demand Memory Injection (P1)

### 5.1 Ziel

`retrieve_diamond_slots()` nicht bei jedem Turn aufrufen, sondern nur bei personal/recall-Intents. Reduziert Kosten und Noise.

### 5.2 Akzeptanzkriterien

- [ ] Queries wie „Wie wird das Wetter?“ → **kein** Memory-Retrieval (0 Slots)
- [ ] „Was mag Oli?“ → Memory-Retrieval aktiv
- [ ] „Wetter in Berlin, wo ich wohne“ → Memory-Retrieval aktiv (Personal-Scope-Hint)
- [ ] Health-Injector bleibt **immer** aktiv (Medical Safety — nicht gated)
- [ ] Flag `MEMORY_ON_DEMAND_INJECTION_ENABLED`

### 5.3 Dateien

| Aktion | Datei |
|--------|-------|
| MODIFY | `backend/services/memory/retrieval_service.py` |
| MODIFY | `backend/services/chat_orchestrator.py` |
| MODIFY | `backend/services/orchestrator/intent_engine.py` (optional, Intent-Signal) |
| CREATE | `backend/tests/test_memory_on_demand_injection.py` |

### 5.4 Implementierungsschritte

1. Funktion `should_inject_memory(query: str, intent: Optional[str]) -> bool` extrahieren
2. Bestehende Heuristiken nutzen:
   - `_is_generic_memory_suppressed_query()` (bereits in retrieval_service.py)
   - `_PERSONAL_SCOPE_HINT_RE`
   - `_EXTERNAL_CONTEXT_QUERY_RE` (invertiert)
3. Im Orchestrator vor `retrieve_diamond_slots()`:
   ```python
   if MEMORY_ON_DEMAND_INJECTION_ENABLED and not should_inject_memory(wf.user_text, wf.intent):
       wf.slots = []  # Health-Injector separat, nicht überschreiben
   else:
       wf.slots = retrieve_diamond_slots(...)
   ```
4. **Wichtig:** `[HEALTH-INJECTOR]` und Calendar-Memory **nicht** hinter dieses Gate hängen
5. Tests für Grenzfälle (Wetter+Wohnort, Kontaktfragen, Smalltalk)

### 5.5 Validierung

```bash
python -m pytest backend/tests/test_memory_on_demand_injection.py -v
python -m pytest backend/tests/test_memory_regression.py -q
```

### 5.6 Risiko

**Niedrig**, solange Health-Injector ausgenommen bleibt.

---

## 6. Phase C — Session-Search (FTS5 über Messages) (P0)

### 6.1 Ziel

Episodisches Gedächtnis: Rohtext-Suche über alle Chat-Messages, on-demand per Tool — analog Hermes L2.

### 6.2 Akzeptanzkriterien

- [ ] FTS5-Index über `messages.content` mit `chat_id`, `role`, `created_at` als UNINDEXED-Metadaten
- [ ] Index-Sync bei jedem Message-Insert (kein separater Batch-Job als einziger Pfad)
- [ ] Backfill-Script für bestehende Messages
- [ ] Tool `session_search` mit Parametern: `query`, `limit`, `chat_id` (optional), `since` (optional)
- [ ] Intent-Routing: Tool nur bei episodischen Queries anbieten
- [ ] Sanitizer: keine Secrets/Passwörter in Ergebnissen (Reuse aus `memory_tools.py`)
- [ ] Ergebnis-Snippets max. 500 Zeichen pro Treffer
- [ ] Flag `MEMORY_SESSION_SEARCH_ENABLED`

### 6.3 Neue Dateien

```
backend/services/memory/session_fts_store.py      # FTS5 Store (Pattern: rag/fts_store.py)
backend/services/memory/session_search_service.py
backend/tools/session_search_tools.py
backend/skills/system/session_search.json
backend/scripts/backfill_session_fts.py
backend/tests/test_session_fts_store.py
backend/tests/test_session_search_tools.py
```

### 6.4 FTS-Schema

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS session_messages USING fts5(
    message_id UNINDEXED,
    chat_id UNINDEXED,
    role UNINDEXED,
    created_at UNINDEXED,
    content,
    tokenize='unicode61 remove_diacritics 2'
);
```

**Separates DB-File:** `{app_data}/session_fts.db` — nicht in `janus.db` mischen (WAL-Konflikte vermeiden).

### 6.5 Sync-Strategie

**Option A (empfohlen): Write-Hook**

In Message-Create-Pfad (CRUD/API) nach erfolgreichem Insert:

```python
if MEMORY_SESSION_SEARCH_ENABLED:
    session_fts_store.index_message(message_id, chat_id, role, content, created_at)
```

**Option B: SQLite Trigger** — nur wenn Messages und FTS in derselben DB (hier nicht empfohlen).

**Backfill:**

```bash
python -m backend.scripts.backfill_session_fts --batch-size 1000 --dry-run
python -m backend.scripts.backfill_session_fts --batch-size 1000
```

### 6.6 Tool-Definition (`session_search.json`)

```json
{
  "id": "session_search",
  "name": "Chat-Verlauf durchsuchen",
  "description": "Durchsucht frühere Gespräche nach Stichwörtern oder Themen. Nutzen für: 'Was haben wir besprochen?', 'Wie hieß die Firma?', Zitate.",
  "parameters": {
    "type": "object",
    "required": ["query"],
    "properties": {
      "query": { "type": "string" },
      "limit": { "type": "integer", "default": 5, "maximum": 20 },
      "chat_id": { "type": "integer", "description": "Optional: nur dieser Chat" },
      "since_days": { "type": "integer", "description": "Optional: nur letzte N Tage" }
    }
  }
}
```

### 6.7 Intent-Routing

Neue Intent-Marker in `intent_engine.py` oder Regex-Set:

```python
_EPISODIC_RECALL_PATTERNS = [
    r"\bwas\s+haben\s+wir\b",
    r"\bwas\s+habe\s+ich\s+(?:dir\s+)?gesagt\b",
    r"\bfrüher\s+(?:mal\s+)?(?:gesagt|besprochen|erwähnt)\b",
    r"\bzitier(?:e|)\s+mir\b",
    r"\bim\s+letzten\s+(?:chat|gespräch)\b",
]
```

Orchestrator: `session_search` zu `valid_tool_names` hinzufügen wenn Intent matcht **oder** Flag global an.

### 6.8 Privacy & Security

| Regel | Umsetzung |
|-------|-----------|
| Secrets filtern | `_SENSITIVE_MEMORY_WRITE_RE` aus memory_tools.py wiederverwenden |
| Assistant-only Messages optional exkludieren | Config `SESSION_SEARCH_ROLES = ["user"]` default |
| Cross-chat Search | Default an, aber UI-Hinweis in Tool-Response |
| PII in Snippets | Truncate + kein Full-Message-Dump |

### 6.9 Abgrenzung zu bestehendem Memory

| Frage-Typ | Tool/Pfad |
|-----------|-----------|
| „Was mag Oli?“ | `memory_read` / `retrieve_diamond_slots` |
| „Was haben wir über Oli besprochen?“ | `session_search` |
| „Merke dir: Oli mag Pizza“ | `memory_write` / Auto-Extractor |

### 6.10 Implementierungsreihenfolge (innerhalb Phase C)

1. `session_fts_store.py` + Unit-Tests
2. Backfill-Script + manuell auf Staging-DB testen
3. Write-Hook in Message-CRUD
4. `session_search_service.py` + Tool
5. Skill-JSON + Tool-Registry
6. Intent-Routing im Orchestrator
7. Integrationstests + 2 manuelle Live-Tests

### 6.11 Validierung

```bash
python -m pytest backend/tests/test_session_fts_store.py backend/tests/test_session_search_tools.py -v
python -m pytest backend/tests/test_memory_regression.py -q
# Manuell:
# 1. Chat mit "Die Firma heißt Acme GmbH" → neuen Chat → "Wie hieß die Firma?"
# 2. Secret "mein Passwort ist geheim123" → session_search darf nicht matchen
```

### 6.12 Risiko

**Mittel.** Größter funktionaler Gewinn, aber Privacy und Index-Drift beachten.

---

## 7. Phase D — Frozen Core + dynamischer Rest (P2, optional)

### 7.1 Ziel

Core-Identity (priority ≥ 0.95) einmal pro Session in den System-Prompt einfrieren. Query-relevante Slots weiterhin dynamisch. Prefix-Cache-freundlich.

### 7.2 Voraussetzung

**Phase C muss live sein** — sonst fehlt Fallback für mid-session Core-Updates.

### 7.3 Akzeptanzkriterien

- [ ] Beim Session-Start (erster Turn pro `chat_id`): Core-Slots laden und cachen
- [ ] Cache-Key: `chat_id` + Session-ID (oder Conversation-Start-Timestamp)
- [ ] `retrieve_diamond_slots()` liefert dynamische Slots **ohne** Core-Always wenn Frozen aktiv
- [ ] Bei `memory_write` mit priority ≥ 0.95: Cache invalidieren **oder** bis nächste Session warten (Config)
- [ ] Config `MEMORY_FROZEN_CORE_REFRESH_ON_WRITE = false` (default, Hermes-Verhalten)
- [ ] Flag `MEMORY_FROZEN_CORE_ENABLED`

### 7.4 Dateien

| Aktion | Datei |
|--------|-------|
| CREATE | `backend/services/memory/frozen_core_cache.py` |
| MODIFY | `backend/services/memory/retrieval_service.py` |
| MODIFY | `backend/services/chat_orchestrator.py` |
| CREATE | `backend/tests/test_frozen_core_cache.py` |

### 7.5 Session-Cache-API

```python
class FrozenCoreCache:
  def get_or_load(db, chat_id) -> List[MemorySlot]: ...
  def invalidate(chat_id) -> None: ...
  def get_stats() -> dict: ...
```

### 7.6 Risiken & Mitigations

| Risiko | Mitigation |
|--------|------------|
| Stale Core nach „Ich bin jetzt vegan“ | Tool-Response zeigt live State; optional `MEMORY_FROZEN_CORE_REFRESH_ON_WRITE=true` |
| Health-Injector Konflikt | Health-Fakten in Frozen Core **inkludieren**, Injector nicht doppeln |
| Regression Identity-Tests | Alle `test_memory_regression.py` + `test_memory_recall_placeholder_regression.py` |

### 7.7 Validierung

```bash
python -m pytest backend/tests/test_frozen_core_cache.py -v
python -m pytest backend/tests/test_memory_regression.py backend/tests/test_memory_recall_placeholder_regression.py -q
```

### 7.8 Risiko

**Hoch** für Recall-Verhalten. Erst nach Phase C, hinter Flag, mit Medical-Regression.

---

## 8. Phase E — USER.md Core-Export (P3)

### 8.1 Ziel

Menschenlesbarer Export der Core-Identity — Transparenz und manuelle Korrektur.

### 8.2 Akzeptanzkriterien

- [ ] API `GET /api/memory/core-profile` → Markdown-Format
- [ ] Optional: `PUT /api/memory/core-profile` → parsed zurück in DB (nur user_editable=true)
- [ ] Export enthält max. `MAX_CORE_ALWAYS_TOKENS` äquivalent
- [ ] Flag `MEMORY_CORE_EXPORT_ENABLED`

### 8.3 Dateien

| Aktion | Datei |
|--------|-------|
| CREATE | `backend/services/memory/core_profile_export.py` |
| MODIFY | `backend/api/routers/memory.py` |
| CREATE | `backend/tests/test_core_profile_export.py` |

### 8.4 Risiko

**Niedrig.** Additiv, kein Einfluss auf Chat-Pipeline wenn Flag off.

---

## 9. Testplan (gesamt)

### 9.1 Regression-Suite (jede Phase)

```bash
python -m pytest backend/tests/test_memory_diamond.py -q
python -m pytest backend/tests/test_memory_regression.py -q
python -m pytest backend/tests/test_memory_tools.py -q
python -m pytest backend/tests/test_memory_retrieval_relevance_priority.py -q
python -m pytest backend/tests/test_memory_recall_placeholder_regression.py -q
```

### 9.2 Medical / Safety (Pflicht bei Phase A, B, D)

```bash
python -m pytest backend/tests/test_memory_extractor_email_pii.py -q
# Manuell: Allergie-Recall mit/ohne Caps und Frozen Core
```

### 9.3 Live-Test-Szenarien

| # | Szenario | Erwartung |
|---|----------|-----------|
| L1 | „Was mag Oli?“ | Fact-Recall korrekt |
| L2 | „Was haben wir letzte Woche über Projekt X gesprochen?“ | session_search Treffer |
| L3 | „Wie wird das Wetter?“ | Kein Memory-Injection (Phase B) |
| L4 | „Wetter wo ich wohne“ | Memory-Injection aktiv |
| L5 | 20 Core-Fakten seeden | Nur Top-N + Health im Core (Phase A) |
| L6 | Mid-session „Ich heiße jetzt Y“ | Mit Frozen: alt bis Session-Ende; mit session_search: neu findbar |

---

## 10. Codex-Ausführungsanweisung

### 10.1 Empfohlener Diamond-Flow pro Phase

```
1. janus-backlog-intake        → Item anlegen (falls nicht vorhanden)
2. janus-preimplementation-check → Scope + Dateien + Tests frozen
3. janus-executioner           → Implementierung (eine Phase pro Run)
4. janus-test-pipeline         → Regression + Live-Evidence
5. janus-final-audit           → PASS vor Flag-Default flip
6. janus-documentation-update  → CURRENT_STATE + WHAT_I_LEARNED
```

### 10.2 Copy-Paste-Startprompt für Codex (Phase C)

```text
Implementiere Phase C aus:
documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md

Scope:
- backend/services/memory/session_fts_store.py (neu)
- backend/tools/session_search_tools.py (neu)
- Write-Hook für Message-Indexierung
- backfill_session_fts.py
- Tests: test_session_fts_store.py, test_session_search_tools.py

Constraints:
- MEMORY_SESSION_SEARCH_ENABLED=false als Default
- Separates DB: session_fts.db
- Sanitizer aus memory_tools.py wiederverwenden
- Health-Injector nicht anfassen
- Keine Änderungen an Frozen Core (Phase D)

Validation:
python -m pytest backend/tests/test_session_fts_store.py backend/tests/test_session_search_tools.py -v
```

### 10.3 Scope-Grenzen (NICHT anfassen)

- `backend/services/rag/*` — separates RAG-System, nur Pattern kopieren
- `memory_extractor.py` — keine Änderung außer explizit in Phase genannt
- Pluggable Provider — out of scope
- Frontend — Phase E optional später

---

## 11. Zeitschätzung & Meilensteine

| Meilenstein | Inhalt | Kalender |
|-------------|--------|----------|
| M1 | Phase A + B merged, Flags off | +3–4 Tage |
| M2 | Phase C MVP, Staging-Backfill | +1–2 Wochen |
| M3 | Phase C Live, Flag on Staging | +2–3 Tage Test |
| M4 | Phase D evaluieren (Go/No-Go) | +1 Woche Beobachtung |
| M5 | Phase E (optional) | +2–3 Tage |

**Gesamt MVP (A+B+C):** ~2–3 Wochen  
**Gesamt inkl. D+E:** ~4–5 Wochen

---

## 12. Go/No-Go für Phase D

Phase D nur starten wenn:

- [ ] Phase C mindestens 1 Woche auf Staging ohne Incidents
- [ ] Recall-Accuracy in Live-Tests ≥ 95% (bestehende Metrik)
- [ ] Medical-Tests weiterhin PASS
- [ ] Prefix-Cache-Ersparnis gemessen (>10% Input-Token-Reduktion in 20+ Turn Sessions)

Wenn No-Go: Frozen Core dauerhaft optional lassen, Phase A+B+C reichen als Zielbild.

---

## 13. Entscheidungslog

| Entscheidung | Gewählt | Alternative verworfen |
|--------------|---------|----------------------|
| FTS5-DB | Separates `session_fts.db` | Trigger in `janus.db` (WAL-Risiko) |
| Session-Search Injection | On-demand Tool | Auto-Inject jeden Turn (zu teuer) |
| Frozen Core Default | `REFRESH_ON_WRITE=false` | Live-Update (teurer, Cache-Bruch) |
| Provider-Plugins | Out of scope | Mem0-Integration |
| Phase-Reihenfolge | A→B→C→D→E | Alles parallel (zu riskant) |

---

**END OF PLAN**
