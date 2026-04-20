# Task 010: Memory Tool Naming-Mismatch — Critical Fix

## 1. Ziel & Kontext
Gemini versucht `memory.memory_read` aufzurufen, aber das Backend kennt dieses Tool nicht.

**Root Cause:** Naming-Mismatch zwischen Skill-JSONs und Tool-Registrierung.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 009 (Tool Registration Fix)
- **Beeinflusst:** LLM Tool-Calling, Gemini Integration
- **Risiko-Einschätzung:** CRITICAL — Memory Tools nicht nutzbar im Live-System

## 3. Betroffene Dateien
- `backend/skills/system/memory_*.json` — "skill" Feld hinzugefügt
- `backend/tool_registry.py` — Tool-Namen auf memory.write/read/update/history geändert

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Analyse):** JSONs haben kein "skill" Feld, Tools haben falsche Namen
- [x] **Phase 2 (Fix JSONs):** "skill": "memory.write" etc. hinzugefügt
- [x] **Phase 3 (Fix Registry):** name="memory.write" etc. statt "memory_write"
- [x] **Phase 4 (Post-Impl):** Dokumentation

## 5. Test-Vorgaben
- [ ] Backend-Startup ohne WARNINGs
- [ ] Gemini kann memory.read/write/update/history aufrufen
- [ ] Tool-Names in _skill_mapping sind korrekt

## 6. Ergebnis & Audit-Trail
**Problem-Chain:**
```
Gemini ruft: memory.memory_read
            ↓
JSON hatte: Kein "skill" Feld → Mapping war leer/broken
            ↓
Tool Registry: name="memory_read" (underscore)
            ↓
Skill System: Erwartet "memory.read" (dot-notation)
```

**Fix:**
1. JSONs: `"skill": "memory.write"`, `"skill": "memory.read"`, etc.
2. Registry: `name="memory.write"`, `name="memory.read"`, etc.

**Files Changed:**
- `backend/skills/system/memory_write.json` — Added: `"skill": "memory.write"`
- `backend/skills/system/memory_read.json` — Added: `"skill": "memory.read"`
- `backend/skills/system/memory_update.json` — Added: `"skill": "memory.update"`
- `backend/skills/system/memory_history.json` — Added: `"skill": "memory.history"`
- `backend/tool_registry.py:396-419` — Tool names: `memory_write` → `memory.write`, etc.

## 7. Debugging-Log
**2026-04-07 19:35 — Analysis**
- Vergleich mit `websearch.json`: hat `"skill": "system.websearch"`
- Memory-JSONs: Kein "skill" Feld → Mapping konnte nicht korrekt gebaut werden
- Tool Registry: Nutzte `name="memory_write"` statt `name="memory.write"`

**2026-04-07 19:38 — Fix Deployed**
- Alle 4 JSONs aktualisiert mit "skill" Feld
- Tool Registry Names auf dot-notation geändert
- Jetzt aligned mit Skill-System Erwartung
