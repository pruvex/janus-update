---
**Task-ID:** M-MEM-04
**Modell:** Kimi K2.5 (Windsurf)
**Audit:** Opus 4.6 (Lead Architect Review 2026-04-06)
**Ref:** `documentation/features/memory_v2.md` Section 4.3

**IST (Codebase-Zustand):**
- `context_manager.py` Zeile 164: `build_final_context()` nimmt `memory_context: str` entgegen — String-Truncation bei Überlänge (Zeile 200: `memory_context[:int(memory_budget * 4)]`). Unpräzise, schneidet Fakten mitten im Satz ab.
- `chat/context_builder.py` Zeile 185: `_get_memory_context(facts)` gruppiert nach Subjekt und baut einen flat String — keine Budget-Awareness, keine Priority-Sortierung.
- `memory_manager.py` Zeile 620: `retrieve_diamond_context()` liefert `str` — 4× `json.loads(m.embedding_json)` Hotspots (Zeilen 654, 687, 699, 717) ohne Caching.
- `chat_orchestrator.py` Zeile 3686: Ruft `self.context_builder._get_memory_context(relevant_facts)` auf und injiziert den String direkt in den LLM-Payload (Zeile 3726).

**SOLL (nach Phase 4):**
- `MemorySlot`-basierte Budget-Selektion ersetzt String-Truncation.
- `TokenBudget` allokiert Tokens nach Ratio: system=10%, memory=30%, history=50%, buffer=1000tk.
- Knapsack-Algorithmus: `continue` statt `break` bei Übergröße — kleinere Slots können noch reinpassen.
- Feature-Flag `MEMORY_V2_ENABLED` für sofortigen Rollback auf alten Code.

**IMPL-LOOP:**
```
[IMPL → TEST → LINTER → IMPORTS → DIAMOND-REPORT]
```

---

# 1. Ziel

Ersetze die String-basierte Context-Injection durch Budget-Aware MemorySlot-Selection. Der LLM bekommt die wichtigsten Fakten zuerst, ohne Token-Verschwendung.

---

# 2. Abhängigkeiten

**REQUIRES (muss existieren):**
- Phase 3: `parse_embedding()` in `embedding_cache.py` ✅ (für `retrieve_diamond_slots()`)
- Phase 3: V2-Felder (priority, memory_type, tags) werden durch Enricher gesetzt ✅

**BLOCKS (wartet auf uns):**
- Phase 5: Unified Tools nutzen Context-System
- Phase 6: Performance-Benchmarks messen diesen Code

---

# 3. Exakte Integrationspunkte (KRITISCH)

### 3.1 NEUE Datei: `backend/services/memory_budget.py`

**ACHTUNG:** `context_manager.py` existiert BEREITS mit `build_final_context()`. Erstelle eine NEUE Datei `memory_budget.py` für die V2-Logik, um den bestehenden Code nicht zu brechen.

```python
# backend/services/memory_budget.py (NEU)
from dataclasses import dataclass
from typing import List, Literal

@dataclass
class MemorySlot:
    text: str
    tokens: int
    tier: Literal["core_always", "core_query", "ephemeral", "stm"]
    priority: float
    memory_id: int
    tags: List[str]

class TokenBudget:
    def __init__(self, max_tokens: int, system_ratio=0.10, memory_ratio=0.30,
                 history_ratio=0.50, response_buffer=1000):
        self.available = max_tokens - response_buffer
        self.system_budget = int(self.available * system_ratio)
        self.memory_budget = int(self.available * memory_ratio)
        self.history_budget = int(self.available * history_ratio)
        self.used_memory = 0

    @property
    def remaining_memory(self) -> int:
        return self.memory_budget - self.used_memory

    def allocate(self, tokens: int) -> bool:
        if self.remaining_memory >= tokens:
            self.used_memory += tokens
            return True
        return False
```

### 3.2 Budget-Mathematik (Referenz für Tests)

Für `max_tokens=8000, response_buffer=1000`:
```
available    = 8000 - 1000 = 7000
system_budget  = 7000 × 0.10 = 700
memory_budget  = 7000 × 0.30 = 2100
history_budget = 7000 × 0.50 = 3500
```

### 3.3 Knapsack: `select_slots_by_budget()`

**KRITISCHER UNTERSCHIED zu Greedy:**
```python
for slot in sorted_slots:
    if budget.remaining_memory < min_slot_tokens:
        break  # Echtes Ende: kein Slot passt mehr
    if budget.allocate(slot.tokens):
        selected.append(slot)
    else:
        skipped.append(slot)
        continue  # <-- KNAPSACK: Überspringt großen Slot, probiert nächsten
```

### 3.4 NEUE Funktion: `retrieve_diamond_slots()` in `memory_manager.py`

**WO:** Neue Funktion NEBEN `retrieve_diamond_context()` (Zeile 620). NICHT ersetzen — beide koexistieren, Feature-Flag entscheidet welche aufgerufen wird.

```python
def retrieve_diamond_slots(db, chat_id, query, ...) -> List[MemorySlot]:
    """V2: Liefert MemorySlots statt String."""
    # Gleiche DB-Queries wie retrieve_diamond_context(),
    # aber gibt MemorySlot-Objekte zurück statt Strings.
    # Nutzt parse_embedding() statt json.loads().
```

### 3.5 Orchestrator-Integration in `chat_orchestrator.py`

**WO:** Zeile 3686 — Feature-Flag-Gate.

```python
# chat_orchestrator.py, Zeile ~3686:
if MEMORY_V2_ENABLED:
    from backend.services.memory_budget import select_slots_by_budget, format_memory_context
    slots = retrieve_diamond_slots(db, chat_id, user_text)
    budget = TokenBudget(max_tokens=model_limit)
    selected = select_slots_by_budget(slots, budget)
    memory_context_string = format_memory_context(selected)
else:
    memory_context_string = self.context_builder._get_memory_context(relevant_facts)
```

### 3.6 Debug-Endpoint in `main.py`

```python
@app.get("/api/debug/memory")
async def debug_memory_system():
    from backend.services.memory_cache import memory_cache
    from backend.services.memory_observability import memory_metrics
    from backend.services.embedding_cache import embedding_cache_stats
    from backend.services.memory_extractor import _extraction_breaker
    return {
        "cache": memory_cache.get_stats(),
        "metrics": memory_metrics.snapshot(),
        "embedding_cache": embedding_cache_stats(),
        "circuit_breaker": _extraction_breaker.get_state(),
    }
```

### 3.7 Feature-Flag

```python
# backend/config.py oder .env:
MEMORY_V2_ENABLED = os.getenv("MEMORY_V2_ENABLED", "true").lower() == "true"
```

---

# 4. Test-Vorgaben

```bash
pytest backend/tests/test_memory_budget.py -v
```

| # | Test | Input | Expected |
|---|------|-------|----------|
| 1 | Budget-Calc | max_tokens=8000, buffer=1000 | system=700, memory=2100, history=3500 |
| 2 | Budget-Calc Small | max_tokens=4000, buffer=1000 | system=300, memory=900, history=1500 |
| 3 | Knapsack Skip-Big | slots=[500tk, 2200tk, 300tk], budget=2100 | selected=[500tk, 300tk], skipped=[2200tk] |
| 4 | Knapsack Full | slots=[100tk×25], budget=2100 | selected=21 slots (2100tk) |
| 5 | Knapsack Empty | slots=[], budget=2100 | selected=[] |
| 6 | Priority Sort | slots=[p=0.5, p=0.9, p=0.7] | order=[0.9, 0.7, 0.5] |
| 7 | Tier Format | slots with core_always + stm | "### CORE IDENTITY" section first |
| 8 | Feature-Flag Off | MEMORY_V2_ENABLED=false | old code path taken |

---

# 5. Audit-Trail

**Status:** ⏳ PENDING (Phase 4/6)
**Opus-Audit:** 2026-04-06 — Bestehende `context_manager.py` identifiziert, neue Datei `memory_budget.py` statt Überschreibung empfohlen.

**WARNUNG:** Die Datei `context_manager.py` wird NICHT modifiziert. Neue Logik geht in `memory_budget.py`. Feature-Flag steuert den Switch im Orchestrator.

**Logging-Prefixe:**
- `[BUDGET]` — Selected X/Y slots, skipped Z (budget: U/M tk)
- `[KNAPSACK]` — Skipping slot (p=P, tk=T), remaining=R tk
- `[CONTEXT V2]` — Built context: N slots, M history, total=T/max tokens
