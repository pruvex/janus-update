# Task 009: Memory Tool Mapping — Critical Fix

## 1. Ziel & Kontext
Kritisches Live-System Problem: Das Backend meldet beim Startup:
```
WARNING: SKILL-SYSTEM: Kein Mapping für Tool 'memory_write'.
```

Die Memory-Tools (memory_write, memory_read, memory_update, memory_history) sind zwar implementiert, aber das Mapping fehlt im Live-System.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 008 (Cognitive Bridge, 83/100 Diamond-Score)
- **Beeinflusst:** ToolManager._load_skill_catalog(), LLM Tool-Calling, Live-System
- **Risiko-Einschätzung:** CRITICAL — Memory V2 Features nicht nutzbar ohne Tool-Mapping

## 3. Betroffene Dateien
- `backend/skills/memory/` — FALSCHE DUPLIKATE gelöscht
- `backend/skills/system/memory_*.json` — Korrekte Skill-Definitionen (bereits vorhanden!)
- `backend/main.py` — Tool-Registration hinzugefügt

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** Analyse der Skill-Loading-Logik
- [x] **Phase 2 (Analyse):**
  - [x] Gefunden: `backend/skills/memory/*.json` sind falsche Duplikate
  - [x] Gefunden: Korrekte JSONs sind bereits in `backend/skills/system/`
  - [x] **KRITISCH:** `register_all_tools()` wurde nie in `main.py` aufgerufen!
- [x] **Phase 3 (Fix):**
  - [x] Falsche Duplikate in `backend/skills/memory/` gelöscht
  - [x] Tool-Registration in `backend/main.py` lifespan hinzugefügt
- [x] **Phase 4 (Post-Impl):** Dokumentation aktualisiert

## 5. Test-Vorgaben
- [ ] Backend-Startup ohne "Kein Mapping für Tool 'memory_X'" WARNINGs
- [ ] `/test-memory` Suite weiterhin 83/100
- [ ] LLM kann memory_write/read/update/history Tools aufrufen

## 6. Ergebnis & Audit-Trail
**Root Cause Analysis:**
```
Problem:  WARNING: SKILL-SYSTEM: Kein Mapping für Tool 'memory_write'
          ↑
Ursache:  register_all_tools() wurde NIE in main.py aufgerufen!
          ↑
Fix:      Tool-Registration in lifespan() hinzugefügt
```

**Files Changed:**
- `backend/main.py:314-320` — Tool-Registration hinzugefügt
- `backend/skills/memory/*.json` — Falsche Duplikate gelöscht

**What was done:**
1. Analysiert: Tool-JSONs existieren korrekt in `backend/skills/system/`
2. Gefunden: Falsche Duplikate in `backend/skills/memory/` — gelöscht
3. **KRITISCH GEFUNDEN:** `register_all_tools()` nie aufgerufen
4. Fix: Tool-Registration in `main.py` lifespan() hinzugefügt

## 7. Debugging-Log
**2026-04-07 19:25 — Root Cause Analysis**
- Duplikate in `backend/skills/memory/` entdeckt und gelöscht
- Korrekte JSONs bereits in `backend/skills/system/`
- **CRITICAL FINDING:** Keine Tool-Registration in main.py

**2026-04-07 19:30 — Fix Deployed**
- `backend/main.py` Zeile 314-320: Tool-Registration hinzugefügt
- Log-Meldung: "All tools registered successfully (including memory_write, memory_read, memory_update, memory_history)."

