# BACKLOG TASK – BACKLOG-006 – Generische Fehlermeldung statt spezifischer Fehlerdetails

## 1. Ziel
Fehlermeldungen enthalten spezifische Details über den tatsächlichen Fehler: welches Tool fehlgeschlagen ist, welcher Fehlercode aufgetreten ist, welche Exception geworfen wurde, welcher Provider/Model betroffen ist.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-006
- **Beeinflusst:** Backend / Orchestrator / Execution Engine / Error Handling / User Experience
- **Risiko-Einschätzung:** MEDIUM

## 3. Scope
### IN SCOPE
- `fallback_summary` dynamisch basierend auf tatsächlichem Fehler generieren
- Fehlerdetails (Fehlercode, Fehlermeldung, betroffenes Tool, Provider/Model) an Fallback übergeben
- Backend-Logs behalten vollständige Exception-Details für Debugging
- User erhält hilfreiche, spezifische Fehlerinformationen statt generischer Nachricht

### OUT OF SCOPE
- Änderung an Tool-Logik oder Provider-Integration
- Änderung an Frontend-Error-Handling

## 4. Umsetzungsschritte
1. `backend/services/orchestrator/execution_dispatcher.py` Zeile 822 prüfen: `fallback_summary` ist statisch
2. `backend/services/orchestrator/execution_engine.py` Exception-Handler prüfen (Zeile 1238-1254)
3. `backend/services/orchestrator/execution_engine.py` Stream-Crash-Handler prüfen (Zeile 2363-2365)
4. `backend/services/orchestrator/execution_engine.py` leere Tool-Round-Ergebnisse prüfen (Zeile 2400)
5. `backend/services/orchestrator/execution_engine.py` leere Text-Ergebnisse prüfen (Zeile 2723)
6. Tool-Fehler-Extraktion prüfen (Zeile 1750-1779): extrahiert bereits `error_code` und `error_message`
7. Dynamischen `fallback_summary` implementieren: Fehlerdetails aus Tool-Ergebnissen oder Exceptions extrahieren und in Fallback einbauen
8. Alle Fallback-Verwendungen (Exception, Stream-Crash, leere Tool-Round, leeres Text-Ergebnis) mit dynamischem Fallback aktualisieren
9. Backend-Logs sicherstellen: vollständige Exception-Details werden weiterhin geloggt
10. Testen: Verschiedene Fehlerfälle auslösen und prüfen, ob spezifische Fehlermeldungen angezeigt werden

## 5. Acceptance Criteria
- [ ] `fallback_summary` wird dynamisch basierend auf dem tatsächlichen Fehler generiert
- [ ] Fehlermeldungen enthalten: Fehlercode, Fehlermeldung, betroffenes Tool (falls zutreffend), Provider/Model (falls zutreffend)
- [ ] Backend-Logs enthalten weiterhin die vollständigen Exception-Details für Debugging
- [ ] User erhält hilfreiche, spezifische Fehlerinformationen statt generischer Nachricht

## 6. Tests / Validierung
- Manuelles Testen mit verschiedenen Fehlerfällen (Tool-Fehler, Provider-Fehler, Exception)
- Backend-Logs auf vollständige Exception-Details prüfen
- Frontend auf angezeigte Fehlermeldungen prüfen

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für atomare Änderung in Orchestrator/Execution Engine mit deterministischem Scope (Error Handling).
