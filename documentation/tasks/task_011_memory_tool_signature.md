# Task 011: Memory Tool Signature-Mismatch — Critical Fix

## 1. Ziel & Kontext
Der Executor meldet: `TypeError: memory_read_tool() missing 1 required positional argument: 'params'`

Die Memory-Tools wurden mit falscher Signatur definiert und können vom ToolExecutor nicht aufgerufen werden.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 010 (Naming-Mismatch Fix)
- **Beeinflusst:** ToolExecutor, Memory Tools Live-Operation
- **Risiko-Einschätzung:** CRITICAL — Tools komplett nicht funktionsfähig

## 3. Betroffene Dateien
- `backend/tools/memory_tools.py` — Alle 4 Tool-Signaturen geändert

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Analyse):** TypeError wegen falscher Parameter-Reihenfolge
- [x] **Phase 2 (Fix):** Signaturen auf `(db: Session, **kwargs)` umgestellt
- [x] **Phase 3 (Post-Impl):** Dokumentation

## 5. Test-Vorgaben
- [ ] Backend-Startup ohne TypeError
- [ ] ToolExecutor kann Tools aufrufen
- [ ] Parameter werden korrekt aus kwargs extrahiert

## 6. Ergebnis & Audit-Trail
**Problem:**
```python
# ALT (FALSCH):
def memory_read_tool(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    
# NEU (KORREKT):
def memory_read_tool(db: Session, **kwargs) -> Dict[str, Any]:
    params = {k: v for k, v in kwargs.items() if v is not None}
```

**Changes:**
- `memory_write_tool(db: Session, **kwargs)` — chat_id aus kwargs.pop() mit Default 9999
- `memory_read_tool(db: Session, **kwargs)` — params aus kwargs
- `memory_update_tool(db: Session, **kwargs)` — params aus kwargs
- `memory_history_tool(db: Session, **kwargs)` — params aus kwargs

**Key Implementation Detail:**
- `chat_id` wird speziell behandelt: `kwargs.pop("chat_id", 9999)`
- Alle anderen Parameter: `params = {k: v for k, v in kwargs.items() if v is not None}`

## 7. Debugging-Log
**2026-04-07 19:50 — Analysis**
- TypeError: missing 1 required positional argument: 'params'
- ToolExecutor injiziert `db` als ersten Parameter
- Alte Signatur: `(params, db)` → passt nicht zu Executor-Aufruf

**2026-04-07 19:55 — Fix Deployed**
- Alle 4 Tools auf `(db: Session, **kwargs)` umgestellt
- Flexible Parameter-Extraktion via kwargs.get() und kwargs.pop()
- TypeError sollte jetzt behoben sein
