# Task 015: Identity Stop-Words Fix — Namenserkennung

## 1. Ziel & Kontext
**Problem:** Der Pre-Pass extrahiert **"Rolf und mag Videospiele"** als kompletten Namen, anstatt nur **"Rolf"**.

**Ziel:** Implementierung von **Stop-Words** ("und", "and") in der Namenserkennung für saubere Trennung.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 014 (Identity Priority Upgrade)
- **Beeinflusst:** Memory Extractor, Identity-Erkennung
- **Risiko-Einschätzung:** P1 — Hohe User-Experience Relevanz

## 3. Betroffene Dateien (Target)
- `backend/services/memory_extractor.py` — Stop-Words Logik für Namenserkennung

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** /pre-check ausführen
- [ ] **Phase 2 (Fix):** Stop-Words ("und", "and") in Namenserkennung implementieren
- [ ] **Phase 3 (Test):** Extraktion von "Rolf und mag Videospiele" → nur "Rolf"
- [ ] **Phase 4 (Post-Impl):** /post-impl

## 5. Test-Vorgaben
- [ ] "Rolf und mag Videospiele" → Extrahiert: "Rolf"
- [ ] "Sarah and likes pizza" → Extrahiert: "Sarah"
- [ ] Stop-Words werden korrekt als Namensgrenze erkannt

## 6. Ergebnis & Audit-Trail
**Implementation:** TBD

## 7. Debugging-Log
**2026-04-07 22:00 — Task Setup**
- Fehler identifiziert: "Rolf und mag Videospiele" als Name
- Ziel: Stop-Words "und"/"and" als Namensgrenze

---

## Phase 2: Implementierungs-Auftrag

**MISSION:** Fixe die Namenserkennung im Pre-Pass durch Stop-Words.

**REQUIREMENTS:**
1. **Stop-Words definieren:**
   - Deutsch: "und"
   - Englisch: "and"
   - Weitere bei Bedarf: ",", ".", "aber", "or", "oder"

2. **Extraktions-Logik:**
   - Name extrahieren bis zum ersten Stop-Word
   - Alles nach Stop-Word gehört NICHT zum Namen
   - Trimmen von Whitespace

3. **Beispiele:**
   ```
   Input:  "Rolf und mag Videospiele"
   Output: "Rolf"
   
   Input:  "Sarah and likes pizza"
   Output: "Sarah"
   
   Input:  "Max, der Bäcker"
   Output: "Max"
   ```

**FILE TO MODIFY:**
- `backend/services/memory_extractor.py` — `_extract_identity_name()` oder äquivalente Funktion

**DELIVERABLE:**
- Saubere Namensextraktion
- Keine "und"/"and" im Namen
