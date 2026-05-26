# Task D10: Logging Pipeline Hardening

## 1. Ziel & Kontext
Logging Pipeline Hardening - Schema-Validierung, Idempotenz und Trace-ID Integration. Erweiterung des Logging-Systems um striktere Schema-Validierung, Trace-ID Tracking und idempotenten Batch-Upload.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** 
  - `backend/services/logging/logger_core.py` (bestehende Async Queue und Batch Worker)
  - `backend/data/schemas_logging.py` (bestehende LogEventCreate Schema)
  - D10 Logging Pipeline Phase 1 (Metadata Injection Pattern)
- **Beeinflusst:**
  - `backend/services/logging/logger_core.py` (Validierungsschicht, UPSERT Support)
  - `backend/data/schemas_logging.py` (trace_id, striktes payload Schema)
  - Alle logging-Aufrufer im System (ToolExecutor, Execution Engine, Chat Orchestrator)
- **Risiko-Einschätzung:** MEDIUM — Schema-Änderungen können Breaking Changes für bestehende Logging-Caller verursachen. Validierungsschicht kann Events bei Schema-Verletzung abweisen (Datenverlust-Risiko).

## 3. Betroffene Dateien
- `backend/data/schemas_logging.py` — trace_id zu LogEvent hinzufügen, striktes Pydantic-Modell für payload definieren
- `backend/services/logging/logger_core.py` — Validierungsschicht vor queue.put(), UPSERT Support für Batch-Uploader

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [x] **Phase 2 (Implementierung):**
  - [x] Erweitere `backend/data/schemas_logging.py`: Füge `trace_id` (UUID oder String) zum LogEvent hinzu
  - [x] Definiere ein striktes Pydantic-Modell für `payload`, das 'input_hash', 'output_summary' und 'error_code' erzwingt
  - [x] Implementiere in `backend/services/logging/logger_core.py` eine Validierungsschicht vor dem `queue.put()`, die Events bei Schema-Verletzung mit einem aussagekräftigen `logger.warning` abweist
  - [x] Bereite den Batch-Uploader in `logger_core.py` auf `UPSERT` vor (Idempotenz via id), falls dies noch nicht geschehen ist
  - [x] Implementiere Queue Overflow Strategy (remove oldest if full)
  - [x] Implementiere Metrics Tracking (successful_uploads, failed_uploads, total_retries)
  - [x] Erstelle system_health Event für periodisches Logging (alle 50 Batches)
  - [x] Verifiziere UPSERT Deduplizierung via id (UUID-Generierung in log_event)
  - [x] Implementiere contextvar für trace_id (set_trace_id, get_trace_id, generate_trace_id)
  - [x] Integriere set_trace_id in chat_orchestrator.py handle_chat_request
  - [x] Logge routing_decision in chat_orchestrator.py
  - [x] Logge fallback_trigger in execution_engine.py
  - [x] Implementiere ensure_logging_schema() in supabase_client.py (Auto-Migration via information_schema.columns)
  - [x] Integriere ensure_logging_schema() in start_worker() (Schema-Check bei jedem Serverstart)
  - [x] Implementiere DLQ-Light: _write_to_dlq() für failed_batches.jsonl bei MAX_RETRIES
- [x] **Phase 3 (Testing):** Syntax Check: `python -m py_compile backend/services/logging/logger_core.py` ✅
- [x] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [x] Regression: `python -m pytest backend/tests -q`
- [x] Targeted: Test Schema-Validierung mit ungültigen payload-Strukturen, Test UPSERT mit doppelten Event-IDs

## 5.1 Post-Implementation-Audit (Phase 2 Completion Check)

### Implementation Verification Checklist
| Check | Status | Notes |
|-------|--------|-------|
| Schema-Erweiterung `trace_id` | ✅ PASS | `LogEventBase` enthält `trace_id: Optional[str]` |
| LogEventPayload Modell | ✅ PASS | Striktes Pydantic-Modell mit `input_hash`, `output_summary`, `error_code` |
| Validierungsschicht | ✅ PASS | `log_event()` validiert Payload vor `queue.put()` mit Warn-Logging |
| UPSERT Idempotenz | ✅ PASS | `upsert()` mit `on_conflict="id"` implementiert |
| Queue Overflow Strategy | ✅ PASS | Drop-Oldest bei Queue voll (maxsize=5000) |
| Metrics Tracking | ✅ PASS | `successful_uploads`, `failed_uploads`, `total_retries` gezählt |
| system_health Event | ✅ PASS | Periodisches Logging alle 50 Batches |
| contextvar Trace-ID | ✅ PASS | `set_trace_id()`, `get_trace_id()`, `generate_trace_id()` implementiert |
| Routing Decision Logging | ✅ PASS | `routing_decision` Event in `chat_orchestrator.py` |
| Fallback Trigger Logging | ✅ PASS | `fallback_trigger` Event in `execution_engine.py` |

### Open Items (Pending Bugfix)
| Item | Status | Owner |
|------|--------|-------|
| Schema-Sync Supabase (DB Migration) | ✅ RESOLVED | ensure_logging_schema() Auto-Migration implementiert |
| DLQ-Light (Dead Letter Queue) | ✅ RESOLVED | failed_batches.jsonl bei MAX_RETRIES implementiert |

### Audit Sign-off
- **Implementiert von:** Kimi K2.5
- **Audit Datum:** 2026-04-25
- **Status:** ✅ COMPLETE (100% Diamant-Standard: Auto-Migration + DLQ-Light)

## 6. Ergebnis & Audit-Trail
**Epic:** D10 — Logging Pipeline Hardening (100% Diamant-Standard)
**Status:** 🥇 SEALED & COMPLETE (2026-04-25)
**Ergebnis:** Logging Pipeline vollständig gehärtet mit Trace-IDs, Overflow-Schutz, Self-Health-Logging, UPSERT-Idempotenz, Auto-Migration-Guard und DLQ-Light.

**Files changed:**
- `backend/data/schemas_logging.py` — trace_id zu LogEventBase hinzugefügt, LogEventPayload Modell erstellt
- `backend/services/logging/logger_core.py` — Validierungsschicht, UPSERT Support, Queue Overflow Strategy, Metrics Tracking, system_health Event, contextvar für trace_id, UUID-Generierung, DLQ-Light (_write_to_dlq)
- `backend/services/logging/supabase_client.py` — ensure_logging_schema() Auto-Migration via information_schema.columns
- `backend/services/chat_orchestrator.py` — set_trace_id Integration, routing_decision Logging
- `backend/services/orchestrator/execution_engine.py` — fallback_trigger Logging (Modell-Upgrades)

**What was done:**
1. Schema-Erweiterung: trace_id Feld für Request-Tracking, striktes LogEventPayload Modell
2. Validierungsschicht: Events mit ungültigem Payload werden abgewiesen mit Warnung
3. UPSERT Support: Batch-Uploader verwendet upsert() mit on_conflict="id" für Idempotenz
4. Queue Overflow Strategy: Ältestes Element wird entfernt wenn Queue voll (5000)
5. Metrics Tracking: successful_uploads, failed_uploads, total_retries werden gezählt
6. system_health Event: Periodisches Logging (alle 50 Batches) mit Queue-Größe und Erfolgsrate
7. Trace-ID Context-Propagation: contextvar mit set_trace_id/get_trace_id/generate_trace_id
8. Routing Decision Logging: routing_decision Event mit gewähltem Modell im Payload
9. Fallback Trigger Logging: fallback_trigger Event bei Modell-Upgrades
10. **Auto-Migration-Guard:** ensure_logging_schema() prüft via information_schema.columns ob trace_id Spalte existiert, führt ALTER TABLE + CREATE INDEX bei Bedarf aus
11. **Schema-Check Integration:** start_worker() ruft ensure_logging_schema() vor Worker-Start auf (bei jedem Serverstart)
12. **DLQ-Light:** _write_to_dlq() schreibt fehlgeschlagene Batches nach 5 Retries in backend/logs/failed_batches.jsonl statt Events ewig in Queue zu halten

**Test result:** Syntax Check: `python -m py_compile backend/services/logging/logger_core.py` ✅ · `python -m py_compile backend/data/schemas_logging.py` ✅ · `python -m py_compile backend/services/logging/supabase_client.py` ✅ · Test-Script `backend/tests/test_logging_final.py` ✅ PASS

## 7. Debugging-Log
**Keine Probleme aufgetreten.** Alle Implementierungen erfolgreich abgeschlossen.
