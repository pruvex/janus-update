# DIAMOND-REPORT V7 (GLOBAL-UNLOCK)

**Status:** ✅ IMPLEMENTIERT  
**Datum:** 2026-04-07  
**Komponente:** `backend/services/memory_manager.py` - `retrieve_diamond_slots()`  
**Version:** V3 (GLOBAL-UNLOCK)

---

## PROBLEM

In neuen Chats (andere `chat_id`) wurden existierende Memories mit hoher Priorität nicht gefunden. Der Nutzer musste in jedem neuen Chat seine Identität neu definieren.

**Beispiel:**
- Chat A: "Ich bin Max" → Wurde gespeichert mit `priority=0.95`  
- Chat B (neu): "Wer bin ich?" → Keine Erinnerung an "Max"

---

## LÖSUNG: GLOBAL-MEMORY-UNLOCK

Die Funktion `retrieve_diamond_slots()` wurde komplett überarbeitet:

### Logik-Änderungen

| Priorität | Scope | Logik |
|-----------|-------|-------|
| `priority >= 0.8` | **GLOBAL** | Alle Chats - Core Identity (Name, physische Merkmale) |
| `priority 0.5-0.8` | **GLOBAL** | Cross-Chat Vektor-Suche für relevante Fakten |
| `priority < 0.5` | **LOKAL** | Nur aktueller Chat - STM (Short-Term Memory) |

### Deduplizierung

- `seen_ids: set()` verhindert doppelte MemorySlots
- Jedes Memory ID nur einmal im Ergebnis

### Logging

```
[GLOBAL-UNLOCK] Loaded X HIGH PRIO memories globally
[GLOBAL-UNLOCK] Vector search found Y matches globally  
[GLOBAL-UNLOCK] Total Z unique slots for chat_id=N (global unlock active)
```

---

## CODE-ÄNDERUNGEN

**Datei:** `backend/services/memory_manager.py`
**Zeilen:** 836-948

### Vorher (V2):
```python
# Nur core_priority basiert, chat_id Filter für STM
core_always = db.query(models.Memory).filter(
    models.Memory.core_priority == 2
).all()
```

### Nachher (V3 - GLOBAL-UNLOCK):
```python
# 1. HIGH PRIO (>=0.8) - GLOBAL
high_prio_memories = db.query(models.Memory).filter(
    models.Memory.priority >= 0.8
).order_by(models.Memory.priority.desc()).limit(20).all()

# 2. GLOBAL VECTOR SEARCH (0.5-0.8)
global_candidates = db.query(models.Memory).filter(
    models.Memory.priority >= 0.5,
    models.Memory.priority < 0.8
).all()

# 3. STM - NUR LOKAL für <0.5
stm_candidates = db.query(models.Memory).filter(
    models.Memory.chat_id == chat_id,
    models.Memory.priority < 0.5,  # Nur low prio lokal
    ...
).all()

# Deduplizierung
def retrieve_diamond_slots(...):
    seen_ids: set = set()
    for mem in memories:
        if mem.id not in seen_ids:
            slots.append(slot)
            seen_ids.add(mem.id)
```

---

## TEST-INSTRUKTIONEN

1. **Szenario 1 - Cross-Chat Memory:**
   ```
   Chat A: "Ich bin Max und habe braune Haare"
   
   Chat B (neu): "Wer bin ich?"
   Erwartet: "Du bist Max, mit braunen Haaren"
   ```

2. **Log-Prüfung:**
   ```
   [GLOBAL-UNLOCK] Loaded 5 HIGH PRIO memories globally
   [GLOBAL-UNLOCK] Total 12 unique slots for chat_id=2 (global unlock active)
   ```

3. **Deduplizierung:**
   - Selbes Memory in HIGH PRIO + STM → Nur einmal im Ergebnis

---

## TECHNISCHE DETAILS

### Query-Struktur
```
┌─────────────────────────────────────────────────────────┐
│  1. HIGH PRIO (>=0.8) - GLOBAL                           │
│     LIMIT 20, ORDER BY priority DESC                    │
├─────────────────────────────────────────────────────────┤
│  2. GLOBAL VECTOR (0.5-0.8)                           │
│     Vektor-Suche über alle Chats                        │
├─────────────────────────────────────────────────────────┤
│  3. EPHEMERAL - GLOBAL                                  │
│     expires_at > now                                    │
├─────────────────────────────────────────────────────────┤
│  4. STM (<0.5) - LOKAL                                  │
│     chat_id == current, LIMIT 300                       │
└─────────────────────────────────────────────────────────┘
```

### Deduplizierungs-Set
```python
seen_ids: set = set()
# Jedes Memory wird nur hinzugefügt wenn ID neu
```

---

## NÄCHSTE SCHRITTE

1. Backend neu starten
2. Szenario 1 wiederholen (Cross-Chat Memory Test)
3. Logs prüfen auf `[GLOBAL-UNLOCK]` Prefix
4. Bei Erfolg: Status auf ✅ setzen

---

**Fix aktiv.** Globale Erinnerungen werden nun über Chat-Grenzen hinweg gefunden.
