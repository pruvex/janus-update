# Task 014: Identity Priority Upgrade — Chat-übergreifender Name-Recall

## 1. Ziel & Kontext
**Problem:** Die Identitäts-Priorität ist aktuell nicht auf Maximum gesetzt, was zu Inkonsistenzen beim chatübergreifenden Namens-Recall führt.

**Ziel:** Priorität des Identity-Slots auf **0.95** setzen (Maximum), damit der Name garantiert in jedem Chat-Kontext geladen wird.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 013 (Memory Identity Preload — COMPLETED)
- **Beeinflusst:** Memory Identity, Memory Extractor, Kontext-Auswahl
- **Risiko-Einschätzung:** P1 — Hohe User-Experience Relevanz

## 3. Betroffene Dateien (Target)
- `backend/services/memory_identity.py` — Prioritäts-Konstante auf 0.95 setzen
- `backend/services/memory_extractor.py` — Extraktions-Logik für Identity anpassen

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** /pre-check ausführen
- [ ] **Phase 2 (Implementierung):** Priorität 0.95 in memory_identity.py setzen
- [ ] **Phase 3 (Integration):** memory_extractor.py anpassen
- [ ] **Phase 4 (Post-Impl):** /post-impl

## 5. Test-Vorgaben
- [ ] Identity-Slot hat Priorität 0.95
- [ ] Slot wird in jedem Chat-Kontext geladen
- [ ] Keine Regression bei anderen Memory-Operationen

## 6. Ergebnis & Audit-Trail
**Implementation:** TBD

## 7. Debugging-Log
**2026-04-07 21:40 — Task Setup**
- Task 014 erstellt
- Ziel: Priorität 0.95 für garantierten chatübergreifenden Recall

---

## Phase 2: Implementierungs-Auftrag

**MISSION:** Setze die Identity-Priorität auf 0.95 (Maximum) für chatübergreifenden Name-Recall.

**REQUIREMENTS:**
1. **Konstante in memory_identity.py:**
   - `IDENTITY_PRIORITY = 0.95`
   - Dies ist das Maximum für user_editable=false Memories

2. **Integration in memory_extractor.py:**
   - Identity-Extraktion muss 0.95 Priorität zuweisen
   - Sicherstellen, dass keine niedrigere Priorität überschreibt

3. **Budget-Exemption:**
   - IdentitySlot bleibt budget-exempt (bereits in Task 013)
   - Priorität 0.95 garantiert zusätzlich Erhalt im Knapsack-Selektor

**FILES TO MODIFY:**
- `backend/services/memory_identity.py` — IDENTITY_PRIORITY Konstante
- `backend/services/memory_extractor.py` — Extraktions-Priorität

**DELIVERABLE:**
- Priorität 0.95 aktiv
- Identity wird in jedem Chat-Kontext geladen
