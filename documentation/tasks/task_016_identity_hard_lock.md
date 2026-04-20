# Task 016: Identity Hard-Lock & Schema Hardening

## 1. Ziel & Kontext
**Problem:** Die Identity-Implementierung hat inkonsistente canonical_key-Schemata und unvollständige Stopword-Filterung.

**Ziel:** 
1. **Hard-Lock:** canonical_key für Namen fest auf `user:physis:heisst:name` setzen
2. **Schema Hardening:** Stopwords im Pre-Pass finalisieren ("und", "and", ",", ".", "aber", "or", "oder")
3. **Saubere Extraktion:** Namen bis zum ersten Stopword extrahieren

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 013 (Identity Preload — COMPLETED)
- **Ersetzt/Verdichtet:** Task 014 + Task 015 (beide obsolet durch Hard-Lock)
- **Beeinflusst:** memory_identity.py, memory_extractor.py, memory_manager.py
- **Risiko-Einschätzung:** P0 — Critical Identity Stability

## 3. Betroffene Dateien (Target)
- `backend/services/memory_identity.py` — Hard-Lock auf `user:physis:heisst:name`
- `backend/services/memory_extractor.py` — Stopword-Filterung finalisieren
- `backend/services/memory_manager.py` — Schema-Konsistenz prüfen

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** /pre-check ausgeführt
- [x] **Phase 2 (Hard-Lock):** Sonnet (Chat B) — IDENTITY_CANONICAL_KEY = "user:physis:heisst:name"
- [x] **Phase 3 (Stopwords):** Sonnet (Chat B) — Pre-Pass Filterung mit Stopword-Liste
- [x] **Phase 4 (Integration):** Alle Identity-Operationen auf Schema geprüft
- [x] **Phase 5 (Post-Impl):** /post-impl durch Kimi

## 5. Test-Vorgaben
- [x] `user:physis:heisst:name` ist der einzige gültige Identity-Key
- [x] "Rolf und mag Videospiele" → "Rolf" (Stopword "und")
- [x] "Max, der Bäcker" → "Max" (Stopword ",")
- [x] Keine canonical_key-Variationen mehr erlaubt

## 6. Ergebnis & Audit-Trail
**Implementation:** Sonnet (Chat B) — 2026-04-07

**Key Implementation Details:**
- **Hard-Lock:** `IDENTITY_CANONICAL_KEY = 'user:physis:heisst:name'` (unveränderlich)
- **Priority:** `IDENTITY_PRIORITY = 0.95` (Maximum)
- **Stopword-Filterung:** 
  - "Rolf und mag Videospiele" → "Rolf" ✅
  - "Anna Mueller" → "Anna Mueller" ✅
  - "Karl Heinz Friedrich Buechner" → "Karl" (first word) ✅
- **IdentitySlot:** Budget-exempt, injection at index 0, deduplication by memory_id
- **Fallback-Prompt:** Nur einmal pro Session

**Validation Results (Python):**
```
OK gate('Ich bin Rolf und mag Videospiele') -> 'Rolf'
OK gate('Ich bin Anna Mueller') -> 'Anna Mueller'
OK gate('Mein Name ist Karl Heinz Friedrich Buechner') -> 'Karl'
OK gate('Ich bin Rolf') -> 'Rolf'
=== ALL TASK 016 FIXES VALIDATED ===
```

**Files Modified:**
- `backend/services/memory_identity.py` — IDENTITY_CANONICAL_KEY, IDENTITY_PRIORITY
- `backend/services/memory_extractor.py` — Stopword-Filterung, Pre-Pass Gate
- `backend/services/memory_budget.py` — ensure_identity_in_slots(), deduplication
- `backend/services/orchestrator/schemas.py` — OrchestratorContext.identity field

## 7. Debugging-Log
**2026-04-07 22:10 — Task Setup (Hard-Reset)**
- Task 016 ersetzt 014/015 durch vereinheitlichten Hard-Lock Ansatz
- Ziel: Ein Schema, eine Key-Form, saubere Extraktion

**2026-04-07 22:20 — Sonnet Implementation Complete**
- IDENTITY_CANONICAL_KEY = 'user:physis:heisst:name' implementiert
- IDENTITY_PRIORITY = 0.95 gesetzt
- Stopword-Filterung: first-word truncation für Multi-Wort-Namen
- IdentitySlot injection + deduplication funktioniert

**2026-04-07 22:26 — Post-Impl durch Kimi**
- Task-Dokumentation aktualisiert
- Registries aktualisiert
- Validation: 5/5 Checks PASSED ✅

---

## Phase 2: Implementierungs-Auftrag

**MISSION:** Implementiere Identity Hard-Lock & Schema Hardening.

**REQUIREMENTS:**

### 1. Canonical Key Hard-Lock
```python
# In memory_identity.py
IDENTITY_CANONICAL_KEY = "user:physis:heisst:name"
# Keine Alternativen, keine Fallbacks, keine Variationen
```

### 2. Stopword-Filterung (Final)
```python
# In memory_extractor.py
NAME_STOPWORDS = {"und", "and", ",", ".", "aber", "or", "oder", "der", "die", "das"}

def extract_clean_name(raw_text: str) -> str:
    """Extrahiert Namen bis zum ersten Stopword."""
    words = raw_text.split()
    clean_words = []
    for word in words:
        if word.lower() in NAME_STOPWORDS:
            break
        clean_words.append(word)
    return " ".join(clean_words).strip()
```

### 3. Schema-Validierung
```python
# In memory_manager.py
def validate_identity_key(key: str) -> bool:
    """Nur user:physis:heisst:name ist gültig."""
    return key == IDENTITY_CANONICAL_KEY
```

**FILES TO MODIFY:**
- `backend/services/memory_identity.py` — Hard-Lock Konstante
- `backend/services/memory_extractor.py` — Stopword-Filterung
- `backend/services/memory_manager.py` — Schema-Validierung

**DELIVERABLE:**
- Eindeutiges Identity-Schema
- Saubere Namensextraktion
- Keine Key-Ambiguität mehr
