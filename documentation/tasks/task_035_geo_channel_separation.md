# Task 035: Geo-Channel Separation

## 1. Ziel & Kontext
Geo-Begriffe sollen nicht mehr fälschlich als YouTube-Channel-Hints interpretiert werden, damit Suchanfragen wie "Geschichte von Rom" wieder stadtbezogene Inhalte liefern statt Creator-Handle-Treffer.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 034 (Schema & Naming Lockdown, Provider-Coherence), bestehende Channel-Hint-Extraktion in `video_tools.py`
- **Beeinflusst:** Video-Suchpräzision, Channel-Lock-Heuristik, globale Such-Fallbacks
- **Risiko-Einschätzung:** LOW

## 3. Betroffene Dateien
- `backend/tools/video_tools.py`

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):** GEO_REJECTION_LIST einführen, Channel-Hint gegen Liste prüfen, automatische Query-Extraktion defensiver machen, explizites `channel_name` aus Tool-Call weiterhin priorisieren.
- [ ] **Phase 3 (Testing):** Targeted Syntax-Check + gezielte Szenarien (`"Geschichte von Rom"`, `"Videos von <Kanalname>"`) validieren.
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: `python -m py_compile backend/tools/video_tools.py`

## 6. Ergebnis & Audit-Trail
_Wird automatisch durch /post-impl ausgefüllt._

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
