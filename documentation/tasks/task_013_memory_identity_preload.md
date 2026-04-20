# Task 013: Memory Inconsistency & Identity Preload — Guaranteed Name Recall

## 1. Ziel & Kontext
**Problem:** User-Name wird nicht konsistent recalled — Inconsistency zwischen erwartetem und tatsächlichem Verhalten.

**Ziel:** Garantierter Recall des User-Namens durch **explizites Laden des Identity-Slots** vor jeder relevanten Operation.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 012 (Pre-Pass & Key-Guard)
- **Beeinflusst:** Memory Manager, Chat Orchestrator, Tool Context
- **Risiko-Einschätzung:** P1 — Hohe User-Experience Relevanz

## 3. Betroffene Dateien (Target)
- `backend/services/memory_manager.py` — Identity-Slot Preload Logik
- `backend/services/chat_orchestrator.py` — Context Injection
- `backend/tools/memory_tools.py` — Name-Recall Verhalten

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** /pre-check ausgeführt
- [x] **Phase 2 (Architektur):** Sonnet (Chat B) — Identity Preload Mechanism designed
- [x] **Phase 3 (Implementierung):** Sonnet (Chat B) — memory_identity.py erstellt
- [x] **Phase 4 (Integration):** IdentitySlot budget-exempt, Log-Signale implementiert
- [x] **Phase 5 (Post-Impl):** /post-impl durch Kimi

## 5. Test-Vorgaben
- [ ] Identity-Slot wird vor jeder Chat-Anfrage geladen
- [ ] Budget-exempt: Slot wird nie aus Kontext gelöscht
- [ ] Fallback-Prompt erscheint nur einmal pro Session wenn Name fehlt
- [ ] [IDENTITY PRELOAD] und [IDENTITY FALLBACK] Logs erscheinen korrekt

## 6. Ergebnis & Audit-Trail
**Architect:** Sonnet (Chat B)
**Implementation:** Sonnet (Chat B) — 2026-04-07

**Key Implementation Details:**
- **Neues Modul:** `memory_identity.py` erstellt
- **Budget-Exempt:** IdentitySlot wird nie aus dem Kontext gelöscht (always protected)
- **Log-Signale:** 
  - `[IDENTITY PRELOAD]` — Wenn Slot erfolgreich geladen
  - `[IDENTITY FALLBACK]` — Wenn Name fehlt und Fallback ausgelöst
- **Session-Tracking:** Fallback-Prompt wird nur einmal pro Session gesendet

**Files Modified:**
- `backend/services/memory_identity.py` — NEW: Identity Preload Modul
- `backend/services/memory_manager.py` — Integration mit Budget-Exemption
- `backend/services/chat_orchestrator.py` — preload_identity_slot() Hook
- `backend/tools/memory_tools.py` — Identity Context Injection

## 7. Debugging-Log
**2026-04-07 21:05 — Task Setup**
- Task 013 erstellt
- Übergabe an Sonnet für Architektur-Design

**2026-04-07 21:30 — Sonnet Implementation Complete**
- `memory_identity.py` Modul erstellt
- IdentitySlot budget-exempt implementiert
- Log-Signale `[IDENTITY PRELOAD]` / `[IDENTITY FALLBACK]` hinzugefügt
- Session-basiertes Fallback (nur einmal pro Session)

**2026-04-07 21:31 — Post-Impl durch Kimi**
- Task-Dokumentation aktualisiert
- Registries aktualisiert

---

## Phase 2: Architektur-Auftrag an Sonnet (Chat B)

**Mission:** Designe den "Identity Preload" Mechanismus für garantierten User-Name Recall.

**Requirements:**
1. **Identity Slot Definition:**
   - Key: `user:physis:heisst:name` oder `user:identity:name`
   - Storage: Memory V2 mit highest priority (0.95)
   - Cache: LRU-Cache Priority Threshold überschreiten

2. **Preload Trigger Points:**
   - Bei jedem neuen Chat-Request
   - Vor jeder Memory-Tool-Invocation
   - Bei Context-Assembly im Orchestrator

3. **Fallback Strategy:**
   - Wenn Identity-Slot leer → polite ask
   - Wenn Name nicht verifiziert → confirmation prompt

4. **Integration Points:**
   - `ChatOrchestrator.handle_chat_request()` — preload_identity_slot()
   - `ToolManager` — inject identity into tool context
   - `memory_read_tool` — guaranteed identity recall

**Deliverable:**
- Architecture decision record
- Interface definitions
- Implementation plan for Phase 3

**Chat B:** @Sonnet — Übernehme Architektur-Design für Task 013
