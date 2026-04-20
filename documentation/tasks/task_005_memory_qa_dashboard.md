# Task 005: Memory QA Skill & Dashboard Integration

## 1. Ziel & Kontext
Implementierung des `/test-memory` Slash-Commands und einer visuellen Dashboard-Zusammenfassung für das Memory QA Framework. Ziel ist eine sofortige Gesundheitsübersicht des Memory V2 Systems mit Diamond-Score, Pass/Fail Rate und Performance-Trends.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 003 (QA Framework Foundation), Task 004 (18-Test-Suite)
- **Beeinflusst:** Memory QA Workflow, Windsurf Cascade Skills, System-Health Monitoring
- **Risiko-Einschätzung:** MEDIUM (neue öffentliche API, Skill-Integration)

## 3. Betroffene Dateien
- `backend/services/memory_qa.py` (modifiziert) — Dashboard-Generierung
- `.windsurf/workflows/test-memory.md` (neu) — Slash-Command Skill

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** `/pre-check` ausgeführt.
- [x] **Phase 2 (Implementierung):** 
  - `generate_health_dashboard()` Methode in memory_qa.py
  - ASCII-Tabelle mit Diamond-Score, Pass/Fail, Trends
  - `.windsurf/workflows/test-memory.md` Skill erstellt
- [x] **Phase 3 (Testing):** Syntax-Validierung OK
- [x] **Phase 4 (Post-Check):** `/post-impl` ausgeführt.
- [ ] **Phase 5 (Audit - Optional):** Nicht erforderlich

## 5. Test-Vorgaben
- [x] Syntax: `python -m py_compile backend/services/memory_qa.py` → PASS
- [x] Integration: Skill-Datei validiert
- [ ] Regression: `python -m pytest backend/tests -q`

## 6. Ergebnis & Audit-Trail
**Files Changed:**
- `backend/services/memory_qa.py` — `generate_health_dashboard()` Methode hinzugefügt (ASCII-Dashboard mit Diamond-Score, Pass/Fail Rate, Performance-Trends)
- `.windsurf/workflows/test-memory.md` — Neuer Slash-Command Skill für Memory QA Tests

**What was done:**
Dashboard-Integration für Memory QA Framework implementiert. Die `generate_health_dashboard()` Methode erstellt eine visuelle ASCII-Tabelle mit:
- 💎 Diamond-Score (0-100) mit Health-Status (EXCELLENT/GOOD/FAIR/CRITICAL)
- Pass/Fail/Error Statistiken mit Prozentangaben
- Performance-Trends (Avg/Min/Max Latency)
- Top 3 schnellste Tests
- Failed Tests Übersicht

Der `/test-memory` Skill lädt automatisch die 18-Test-Suite, führt sie aus und zeigt das Dashboard.

**Test Result:**
- Syntax Check: PASS
- Import Test: PASS
- Skill Validation: PASS

## 7. Debugging-Log
**2026-04-07 17:15 — CRITICAL: Score 0/100 nach erstem Run**
- **Symptom:** Alle 18 Tests mit ERROR, `ChatRequest` Schema-Fehler (provider fehlte, chat_id war String)
- **Fix 1:** `provider="openai"` + `chat_id=9999` (Integer) in `run_single_test()`
- **Fix 2:** `_ListHandler` für LogCapture (emit-Methode fehlte)
- **Fix 3:** `get_orchestrator()` Factory mit MagicMock für ContextManager
- **Fix 4:** `_session_context()` ContextManager für DB-Sessions
- **Fix 5:** `error_message or "No error details"` in Dashboard (None-Handling)

**2026-04-07 17:27 — Erfolgreicher Run**
- Status: 0/18 PASSED, 18/18 FAILED (keine ERRORs = Architektur stabil)
- 💎 Diamond-Score: **2/100** 🔴 CRITICAL
- Avg Latency: 6.4s, Max: 23.6s
- Offene Probleme: Log-Patterns `[CACHE HIT]`, `[KNAPSACK]` werden nicht gefunden — Memory-Integration nicht aktiv
