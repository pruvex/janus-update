---
id: BUG-SYS-019
title: Memory-Fact Proactivity Guard
status: DONE
priority: P1
category: System/Bug
assignee: Kimi
---

## 1. Problem Statement
Der Orchestrator triggert bei Listen den "Diamond Drill-Down" (Websuche), auch wenn die Liste persönliche Fakten enthält. Dies blockiert die Fakten-Extraktion und führt zu "Native Grounding" Fehlern.

**Beispiel:**
- Nutzer: "Mein Hund heißt Bello. Meine Frau ist Lisa."
- System: Triggert Websuche statt Fakten zu extrahieren → Native Grounding Error

**BUG-SYS-019-V2: Regex Hardening**
- Problem: Anker (^) in Pattern verhindern Match bei Einleitungen wie "Hier sind ein paar Infos..."
- Lösung: Anker entfernt, `search()` statt `match()`, Einleitungs-Muster hinzugefügt

## 2. Root Cause
Die `_should_force_websearch_skill()` Funktion prüft nicht, ob der Nutzer persönliche Fakten teilt. Pattern wie "Mein...", "Ich habe...", "Ich bin..." signalisieren Fact-Telling, nicht Informationsbedarf.

## 3. Lösungsansatz
**BUG-SYS-019: Memory-Fact Proactivity Guard**

1. Implementiere `_is_fact_telling_pattern()` - Erkennt persönliche Fakten
2. Erweitere `_should_force_websearch_skill()` - Prüft Fakten-Pattern VOR Websuche
3. Priorität: Fakten-Erkennung > Websuche (Diamond Drill-Down)

## 4. Umsetzungsschritte
- [x] **Phase 1:** `_is_fact_telling_pattern()` implementieren
- [x] **Phase 2:** `_FACT_TELLING_PATTERNS` definieren
- [x] **Phase 3:** Integration in `_should_force_websearch_skill()`
- [x] **Phase 4:** Syntax-Check
- [x] **Phase 5:** BUG-SYS-019-V2: Regex Hardening
  - [x] Anker (^) aus Pattern entfernt
  - [x] `search()` statt `match()` verwenden
  - [x] Einleitungs-Muster hinzugefügt
- [ ] **Phase 6:** /post-impl

## 5. Implementation Details

### Neue Funktion: `_is_fact_telling_pattern()`
```python
def _is_fact_telling_pattern(user_text: str) -> bool:
    """
    BUG-SYS-019: Erkennt wenn Nutzer persönliche Fakten teilt.
    
    Returns True wenn Pattern wie "Mein/Meine...", "Ich habe...", 
    "Ich bin...", "Ich mag..." erkannt wird.
    
    Bei Fakten-Teilen MUSS Websuche blockiert werden um:
    - Native Grounding Fehler zu vermeiden
    - Memory-Extraktion zu priorisieren
    """
```

### Erkannte Pattern (BUG-SYS-019-V2: ohne ^-Anker!)

#### Kernaussagen (Pattern findet überall in Zeile)
| Pattern | Beispiel |
|---------|----------|
| `(mein|meine)\s+` | "Mein Hund heißt...", "Meine Frau ist..." |
| `(ich\s+habe)\s+` | "Ich habe einen Bruder..." |
| `(ich\s+bin)\s+` | "Ich bin 30 Jahre alt..." |
| `(ich\s+mag)\s+` | "Ich mag Kaffee..." |
| `(ich\s+liebe)\s+` | "Ich liebe Schokolade..." |
| `(ich\s+heiße)\s+` | "Ich heiße Max..." |
| `(mein\s+name\s+ist)\s+` | "Mein Name ist Max..." |
| `(ich\s+arbeite\s+als)\s+` | "Ich arbeite als..." |
| `(ich\s+wohne\s+in)\s+` | "Ich wohne in..." |

#### Einleitungs-Muster (BUG-SYS-019-V2)
| Pattern | Beispiel |
|---------|----------|
| `(hier\s+sind|hier\s+ist|ich\s+erzähle\s+dir|merke\s+dir|infos?\s+über\s+mich|ein\s+paar\s+infos)` | "Hier sind ein paar Infos über mich..." |

### Integration in `_should_force_websearch_skill()`
```python
# ═══════════════════════════════════════════════════════════════════════════
# BUG-SYS-019: PRIORITÄT - Fakten-Erkennung VOR Websuche
# ═══════════════════════════════════════════════════════════════════════════
if _is_fact_telling_pattern(user_text):
    logger.info(
        "[BUG-SYS-019] Blocking web search - fact-telling pattern detected: %r",
        user_text[:60]
    )
    return False  # STRENG UNTERSAGT - Nutzer teilt Fakten, keine Websuche!
# ═══════════════════════════════════════════════════════════════════════════
```

## 6. Test-Vorgaben
- [ ] "Mein Hund heißt Bello" → `return False` (keine Websuche)
- [ ] "Ich habe einen Bruder" → `return False` (keine Websuche)
- [ ] "Ich bin 30 Jahre alt" → `return False` (keine Websuche)
- [ ] Listen mit Fakten: Jede Zeile wird geprüft
- [ ] "Wie ist der Goldpreis?" → `return True` (Websuche erlaubt)

## 7. Ergebnis & Audit-Trail
**Implementation:** Kimi (Windsurf) — 2026-04-08

**Files Modified:**
- `backend/services/chat_orchestrator.py`
  - `_FACT_TELLING_PATTERNS` list (lines ~106-116)
  - `_is_fact_telling_pattern()` function (lines ~119-147)
  - Integration in `_should_force_websearch_skill()` (lines ~155-164)

**Syntax-Check:** ✅ PASSED

## 8. Debugging-Log
**2026-04-08 — Implementation Complete (Kimi)**
- `_is_fact_telling_pattern()` implementiert
- `_FACT_TELLING_PATTERNS` mit 9 Pattern definiert
- Integration in `_should_force_websearch_skill()`
- Logging: `[BUG-SYS-019] Blocking web search - fact-telling pattern detected`
- Syntax-Check: ✅ PASSED

**2026-04-08 — BUG-SYS-019-V2: Regex Hardening (Kimi)**
- Problem: Anker (^) verhindern Match bei Einleitungen
- Lösung: Anker entfernt, jetzt `search()` statt `match()`
- Zusätzlich: Einleitungs-Muster für "Hier sind...", "Ich erzähle dir..."
- Pattern jetzt: 9 Kernaussagen + 1 Einleitungs-Muster
- Syntax-Check: ✅ PASSED
