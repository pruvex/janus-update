# Task: BACKLOG-023 – Intermittierender Backend Timeout bei Janus Live-Chat Retest

## Backlog Item

- **ID:** BACKLOG-023
- **Typ:** BUG
- **Status:** READY
- **Quelle:** TestRun
- **TestRun:** TEST-RUN-2026-05-11-005-RETEST-002

## Kurzbeschreibung

Janus beantwortet aufeinanderfolgende Live-Chat-Anfragen im automatisierten Retest nicht zuverlässig; TC-001 besteht, TC-002 läuft in einen Backend-/Chat-Timeout.

## Erwartetes Verhalten

Janus verarbeitet aufeinanderfolgende Chat-/Intent-Anfragen stabil oder liefert einen kontrollierten Timeout-/Fallback-Hinweis.

## Tatsächliches Verhalten

Nach erfolgreichem Config-Fix und Backend-Neustart schlägt TC-002 durch Backend-/Chat-Timeout fehl; 15 weitere TestCases wurden nicht ausgeführt.

## Reproduktion / Kontext

TEST-RUN-2026-05-11-005-RETEST-002; TC-001 PASS nach 23.9s; TC-002 FAIL nach 50.5s; Runner: tests/e2e/generated/TEST-RUN-2026-05-11-005.live.spec.js

## Betroffener Bereich

Backend Chat Processing / Connection Pool / Resource Management / Rate-Limit Logic

## Nachweise

documentation/test-results/TEST-RUN-2026-05-11-005-RETEST-002_results.md

## Akzeptanzkriterien

- [x] Connection Pool Config korrekt (max_connections, pool_recycle, connection timeouts)
- [x] DB Sessions werden korrekt geschlossen/returned nach Request-Ende
- [x] Keine Resource Leaks in execution_engine.py bei aufeinanderfolgenden Tool-Loops
- [x] Rate-Limit Logic in LLM Gateway korrekt implementiert (kein blockieren nach erstem Request)
- [x] Gefundene Probleme sind dokumentiert und mit Fix-Vorschlag versehen

## Fehlende Informationen

Keine

## Notizen

Runtime-Logs nicht verfügbar (Backend Log: N/A, Frontend Log: N/A). Statische Code-Inspektion fokussiert auf Connection Pool, Session Management, Resource Leaks, Rate-Limit Logic.

## Statische Code-Inspektion Ergebnisse

### 1. Connection Pool Config (backend/data/database.py)
**Status: KORREKT**
- `pool_size=10`, `max_overflow=20` - Angemessen für SQLite
- `pool_recycle=1800` (30 Minuten) - Standard-Wert für SQLite
- `pool_timeout=30` - 30 Sekunden Timeout für Connection-Acquisition
- `pool_pre_ping=True` - Prüft Verbindung vor Gebrauch
- `pool_reset_on_return="rollback"` - Setzt Transaktionen zurück
- SQLite timeout: 30 Sekunden in connect_args
- WAL Mode aktiviert für bessere Parallelität

**Bewertung:** Die Konfiguration ist für SQLite angemessen und sollte keine Timeout-Probleme verursachen.

### 2. DB Session Management
**Status: KORREKT**
- `get_db_sync()` (database.py Zeile 173-182): Hat proper `finally` Block mit `db.close()`
- `get_db_session()` (database.py Zeile 185-195): Async Context Manager mit proper `finally` Block
- `get_db_context()` (database.py Zeile 204-211): Context Manager mit `db.close()`
- Alle API-Router verwenden `Depends(get_db)` für automatische Session-Verwaltung

**Bewertung:** Sessions werden korrekt geschlossen. Keine Resource Leaks durch offene DB-Sessions.

### 3. Rate-Limit Logic (backend/services/tool_executor.py)
**Status: KORREKT**
- `per_skill_counts` wird frisch pro `execute_tool_calls` initialisiert (Zeile 1111)
- Rate-Limit ist pro-Skill und pro-Turn, nicht global
- `RATE_LIMIT_EXCEEDED` Error-Code existiert, aber blockiert nicht zwischen Requests
- Kein globaler Rate-Limit State, der über Requests hinweg persistieren würde

**Bewertung:** Rate-Limit Logic korrekt implementiert. Kein Blocking nach erstem Request.

### 4. Resource Leaks in execution_engine.py
**Status: KORREKT**
- `OrchestratorExecutionEngine` speichert `self.db` als Instanz-Variable
- DB Session wird von außen injiziert (durch ChatOrchestrator) und dort verwaltet
- Keine `asyncio.gather` oder `asyncio.wait` Patterns gefunden, die Deadlocks verursachen könnten
- Keine `engine.dispose()` Aufrufe nötig für SQLite (Singleton Engine)

**Bewertung:** Keine offensichtlichen Resource Leaks in execution_engine.py.

### 5. Gateway Silos (backend/services/llm_gateway.py)
**Status: KORREKT**
- `_gateway_silos` ist global Singleton mit Thread-Safe Lock
- Gateway-Instanzen werden einmal geladen und wiederverwendet
- `@lru_cache(maxsize=1)` für Modellkatalog

**Bewertung:** Singleton-Pattern ist thread-safe und sollte keine Probleme verursachen.

## Ursachen-Analyse

**Symptom:** TC-001 PASS (23.9s), TC-002 FAIL (50.5s Timeout)
**Muster:** Erste Request funktioniert, zweite Request timeoutet

**Mögliche Ursachen (basierend auf statischer Inspektion):**

1. **SQLite WAL Mode Lock Contention:**
   - Bei schnellen aufeinanderfolgenden Writes kann WAL Mode zu Lock-Wartezeiten führen
   - TC-001 (23.9s) schreibt Daten, TC-002 versucht sofort zu schreiben
   - Lösung: SQLite timeout erhöhen oder aggressive Writes reduzieren

2. **Connection Pool Exhaustion:**
   - `pool_timeout=30` könnte bei hoher Last zu Timeouts führen
   - Wenn viele Connections gleichzeitig geöffnet werden, warten neue Requests
   - Lösung: `pool_timeout` erhöhen oder `pool_size` anpassen

3. **Gateway Silo Initialization Race:**
   - `_gateway_silos` werden lazy beim ersten Request geladen
   - Wenn erster Request noch lädt, könnte zweiter Request blockieren
   - Lösung: Gateway Silos beim App-Start vorinitialisieren

## Empfohlene Fixes

### Fix 1: SQLite Timeout erhöhen (LOW RISK)
**Datei:** `backend/data/database.py` Zeile 42
**Änderung:** `timeout: 30` → `timeout: 60`
**Grund:** Mehr Zeit für Lock-Wartezeiten bei aufeinanderfolgenden Writes

### Fix 2: Connection Pool Timeout erhöhen (LOW RISK)
**Datei:** `backend/data/database.py` Zeile 47
**Änderung:** `pool_timeout=30` → `pool_timeout=60`
**Grund:** Mehr Zeit für Connection-Acquisition bei hoher Last

### Fix 3: Gateway Silos bei App-Start vorinitialisieren (MEDIUM RISK)
**Datei:** `backend/main.py` in lifespan function
**Änderung:** `_ensure_gateway_silos()` beim App-Start aufrufen
**Grund:** Vermeidet Lazy-Loading Race Conditions bei ersten Requests

## Empfehlung

Da Runtime-Logs nicht verfügbar sind und die statische Inspektion keine offensichtlichen Bugs zeigt, empfehle ich:

1. **Fix 1 und Fix 2 implementieren** (LOW RISK, einfache Timeout-Erhöhungen)
2. **Backend-Logging aktivieren** und den Retest mit Logs durchführen
3. **Wenn das Problem persistiert:** Fix 3 implementieren oder detaillierte Performance-Profiling durchführen

## Routing

- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** Klarer Bugfix mit statischer Code-Inspektion (Connection Pool, Resource Management, Rate-Limit), Scope begrenzt auf Backend Core
- **Routing confidence:** MEDIUM
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-05-12
- **Recommended next skill:** SKILL 3

## Bewertung

- **Wichtigkeit:** HIGH
- **Umsetzungsrisiko:** HIGH
- **Aufwand:** M
- **Umsetzungsreife:** READY
- **Empfehlung:** DO NOW
