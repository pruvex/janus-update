# BACKLOG TASK – BACKLOG-008 – Filesystem-Intent blockiert RAG-Intent

## 1. Ziel
Filesystem-Intent soll RAG-Intent blockieren, um unnötige Logic-Tier-Upgrades bei reinen Dateisystem-Operationen zu verhindern.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-008
- **Beeinflusst:** Intent-Engine / RAG-Intent-Detection / Model-Selection
- **Risiko-Einschätzung:** MEDIUM (Intent-Priorisierung beeinflusst Kernverhalten)

## 3. Scope
### IN SCOPE
- Intent-Priorisierung anpassen: Filesystem-Intent blockiert RAG-Intent
- RAG-Intent-Detection präzisieren: nur bei Wissensabfragen (PDFs, Dokumente)
- Log-Output `[INTENT-OVERRIDE] RAG-Intent erkannt` wird nicht mehr bei Filesystem-Operationen getriggert

### OUT OF SCOPE
- Allgemeine RAG-System-Optimierung
- Pfad-Auflösungslogik (separates UX-Problem)
- Model-Selection für andere Intent-Typen

## 4. Umsetzungsschritte
1. Analyse der aktuellen Intent-Priorisierungslogik in der Intent-Engine (ähnlich wie BACKLOG-005 für Filesystem-vs-Bild) und Identifizierung der Stelle, an der RAG-Intent erkannt wird und Logic-Tier-Upgrades auslöst
2. Implementierung einer Filesystem-Intent-Blockade für RAG-Intent (Pattern wie BACKLOG-005: Filesystem-Override-Logik in der Intent-Engine)
3. Validierung durch Test dass RAG-Intent weiterhin bei echten Wissensabfragen getriggert wird

## 5. Acceptance Criteria
- [ ] Filesystem-Intent blockiert RAG-Intent (kein unnötiges Logic-Tier-Upgrade)
- [ ] Filesystem-Operationen werden mit gpt-5.4-nano ausgeführt
- [ ] RAG-Intent wird nur bei tatsächlichen Wissensabfragen getriggert (PDFs, Dokumente)
- [ ] Log zeigt `[INTENT-OVERRIDE] RAG-Intent erkannt` nicht mehr bei reinen Filesystem-Prompts

## 6. Tests / Validierung
- Test mit Filesystem-Prompt ohne RAG-Keywords: "erstell auf dem desktop einen ordner 'Bilder'" → prüfe dass kein Upgrade gpt-5.4-nano → gpt-5.4 erfolgt
- Log-Check auf Model-Selection bei Filesystem-Operationen
- Test mit explizitem Dokumenten-Request: "suche im PDF nach X" → prüfe dass RAG-Intent weiterhin getriggert wird
- Manuellem Test mit Desktop-Ordner-Operation zur Validierung der Pfad-Auflösung

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Intent-Engine-Integration mit MEDIUM-Risiko, erfordert Verständnis der Intent-Priorisierungsarchitektur und mehrerer betroffener Module
