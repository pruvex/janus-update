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
- [x] `fallback_summary` wird dynamisch basierend auf dem tatsächlichen Fehler generiert
- [x] Fehlermeldungen enthalten: Fehlercode, Fehlermeldung, betroffenes Tool (falls zutreffend), Provider/Model (falls zutreffend)
- [x] Backend-Logs enthalten weiterhin die vollständigen Exception-Details für Debugging
- [x] User erhält hilfreiche, spezifische Fehlerinformationen statt generischer Nachricht

## 6. Tests / Validierung
- [x] Manuelles Testen mit verschiedenen Fehlerfällen (Tool-Fehler, Provider-Fehler, Exception)
- [x] Backend-Logs auf vollständige Exception-Details prüfen
- [x] Frontend auf angezeigte Fehlermeldungen prüfen

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für atomare Änderung in Orchestrator/Execution Engine mit deterministischem Scope (Error Handling).

## 8. Implementierungsdetails

### Geänderte Dateien
1. **backend/services/orchestrator/execution_engine.py**
   - `_build_dynamic_fallback_summary()` Helper-Funktion hinzugefügt (Zeilen ~1836-1875)
   - `run_tool_loop()` mit dynamischem Fallback aktualisiert (Zeilen ~2248-2274)
   - `run_tool_loop_stream()` mit dynamischem Fallback aktualisiert (Zeilen ~2895-2945, ~3020-3085)
   - Tool-Fehler-Tracking mit `_last_tool_error` Variable
   - Provider/Model Extraktion aus `gateway_kwargs`
   - Exception-Handler mit `exc_info=True` für vollständige Backend-Logs

2. **backend/services/orchestrator/execution_dispatcher.py**
   - Import von `_build_dynamic_fallback_summary` (Zeilen ~23-24)
   - Initiale `fallback_summary` Zuweisung mit dynamischem Helper (Zeilen ~833-840)

### Test-Ergebnisse
- **GPT (gpt-5.4):** Zeigt spezifische Fehlerdetails (Tool-Name, Fehlercode, Fehlermeldung) ✅
- **Gemini (gemini-3-pro-preview):** Zeigt jetzt auch spezifische Fehlerdetails nach Fix ✅
- **Python Compile Check:** Bestanden ✅

### Test-Prompt
```
Lies die Datei C:\this\path\does\not\exist\test123.txt
```

### Backend-Log-Prüfung
Backend-Logs enthalten weiterhin vollständige Exception-Details mit `exc_info=True` in allen Exception-Handlern.

---

## 9. SKILL 6 FINAL AUDIT HANDOVER

### Spec/Task Reference
- **Backlog Item:** BACKLOG-006 – Generische Fehlermeldung statt spezifischer Fehlerdetails
- **Task File:** documentation/tasks/backlog_BACKLOG-006_specific_error_messages.md
- **Backlog Source:** documentation/backlog/BACKLOG.md

### Implementation Summary
**Target Task:** ALL COMPLETED ✅

**Geänderte Dateien:**
1. `backend/services/orchestrator/execution_engine.py`
   - `_build_dynamic_fallback_summary()` Helper-Funktion hinzugefügt
   - `run_tool_loop()` mit dynamischem Fallback aktualisiert
   - `run_tool_loop_stream()` mit dynamischem Fallback aktualisiert
   - Tool-Fehler-Tracking mit `_last_tool_error` Variable
   - Provider/Model Extraktion aus `gateway_kwargs`
   - Exception-Handler mit `exc_info=True` für vollständige Backend-Logs

2. `backend/services/orchestrator/execution_dispatcher.py`
   - Import von `_build_dynamic_fallback_summary`
   - Initiale `fallback_summary` Zuweisung mit dynamischem Helper

### Acceptance Criteria Status
- [x] `fallback_summary` wird dynamisch basierend auf dem tatsächlichen Fehler generiert
- [x] Fehlermeldungen enthalten: Fehlercode, Fehlermeldung, betroffenes Tool (falls zutreffend), Provider/Model (falls zutreffend)
- [x] Backend-Logs enthalten weiterhin die vollständigen Exception-Details für Debugging
- [x] User erhält hilfreiche, spezifische Fehlerinformationen statt generischer Nachricht

### Test Results
**Overall Test Results:** PASS ✅

**Manual Janus Test:**
- **Test Prompt:** `Lies die Datei C:\this\path\does\not\exist\test123.txt`
- **GPT (gpt-5.4):** Zeigt spezifische Fehlerdetails (Tool-Name, Fehlercode, Fehlermeldung) ✅
- **Gemini (gemini-3-pro-preview):** Zeigt jetzt auch spezifische Fehlerdetails nach Fix ✅
- **Python Compile Check:** Bestanden ✅

**Backend-Log Verification:**
- Backend-Logs enthalten weiterhin vollständige Exception-Details mit `exc_info=True` in allen Exception-Handlern ✅

### Changed Files
1. `backend/services/orchestrator/execution_engine.py` (Lines modified: 1836-1875, 2248-2274, 2895-2945, 3020-3085)
2. `backend/services/orchestrator/execution_dispatcher.py` (Lines modified: 23-24, 833-840)

### Known Risks
- Keine bekannten Risiken
- Änderungen sind lokal begrenzt auf Error Handling im Orchestrator
- Keine Auswirkungen auf andere Systemkomponenten

### Recommended Audit Model
- **Risk Level:** MEDIUM
- **Recommended Model:** SWE 1.6
- **Reason:** MEDIUM Risk mit lokal begrenztem Scope (Error Handling im Orchestrator). Keine Auswirkungen auf kritische Systemkomponenten.
- **Alternative:** GPT-5.5 (wenn höhere Sicherheit gewünscht oder bei Unsicherheit)

### Next Step
```
@[/SKILL 6 – DIAMANTSTANDARD FINAL AUDIT]
```

**Audit Model Gate:** SWE 1.6 (MEDIUM Risk)

---

## 10. SKILL 7 IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-05-11
- **Completed By:** SKILL 6 – DIAMANTSTANDARD FINAL AUDIT
- **Validation Evidence:** Skill 6 Audit PASS. Manual Janus Test PASS (GPT + Gemini). Python compile check bestanden. Alle Acceptance Criteria erfüllt.
- **Version Bump:** 0.4.17-beta.27 → 0.4.17-beta.28
- **Skill 7 Completed At:** 2026-05-11
