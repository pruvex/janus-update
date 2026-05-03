# Task 066: Memory Context Bleed Prevention (Threshold Tuning)

## 1. Ziel & Kontext
**Ziel:** Erhöhung des Minimum-Score-Thresholds für den Knapsack-Algorithmus im Memory-Retrieval von 0.50 auf 0.65-0.70, um zu verhindern, dass unzusammenhängende alte Tests in den Kontext gelangen und kleine Modelle wie Gemini Flash verwirren.

**Kontext:** Die aktuelle Strategie mit Threshold 0.50 spült zu viele irrelevante Kontext-Fragmente in die Konversation. Dies führt dazu, dass Gemini Flash (und andere kleine Modelle) von veralteten, nicht-relevanten Test-Einträgen abgelenkt werden und die Qualität der Antworten sinkt.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Memory-Retrieval-System (Knapsack-Algorithmus), Task 057 (Context Awareness System)
- **Beeinflusst:** 
  - Memory retrieval scoring (`memory_retrieval.py` oder `memory_manager.py`)
  - Chat-Kontext-Konstruktion (`chat_orchestrator.py`)
  - Alle LLM-Interaktionen, die auf Memory angewiesen sind
  - → Modified by task_066: Threshold-Tuning für Kontext-Relevanz
- **Risiko-Einschätzung:** MEDIUM – Höherer Threshold könnte theoretisch relevante Kontexte ausschließen, erfordert sorgfältiges Testing

## 3. Betroffene Dateien
- `backend/services/memory/memory_retrieval.py` (oder `memory_manager.py`) – Knapsack-Threshold-Parameter
- `backend/services/chat_orchestrator.py` – Kontext-Konstruktion
- Optional: `backend/services/context/context_compressor.py` – Falls Threshold mit Compression interagiert

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
  - Lokalisieren der Threshold-Definition (vermutlich `MIN_SIMILARITY` oder ähnlich)
  - Analyse aktueller Score-Verteilung in Test-Queries
- [ ] **Phase 2 (Implementierung):**
  - Threshold von 0.50 auf 0.65 erhöhen (konservativer Start)
  - Logging hinzufügen: Anzahl der vor/nach dem Filter zurückgelieferten Items
  - Optional: Threshold konfigurierbar machen (Env-Var oder Config)
- [ ] **Phase 3 (Testing):**
  - Memory-QA-Tests laufen lassen
  - Manuelle Tests mit bekannten "verwirrenden" Queries
  - Prüfung: Werden relevante Kontexte noch gefunden?
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q` 
- [ ] Targeted: `python -m pytest backend/tests/test_memory*.py -v`
- [ ] Manuelle Validierung: Queries mit bekannten "Bleed"-Problemen testen

## 6. Ergebnis & Audit-Trail
_Wird automatisch durch /post-impl ausgefüllt._

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
