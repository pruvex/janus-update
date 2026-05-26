# BACKLOG TASK – BACKLOG-029 – Intent Engine nutzt LLM-Wissen statt system.weather Tool für Wetter-Anfragen (DONE)

## 1. Ziel
Die Intent Engine so korrigieren, dass Wetter-Anfragen das system.weather Tool aufrufen statt LLM-Wissen zu verwenden, um aktuelle Wetterdaten von der API zu erhalten.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-029
- **TestRun:** TEST-RUN-2026-05-12-001-TRUTH-REPORT
- **Beeinflusst:** Intent Engine / Skill Selector / Tool Routing
- **Risiko-Einschätzung:** MEDIUM
- **Abhängigkeit:** BACKLOG-025 (Frontend-Rendering-Fehler) muss zuerst behoben werden für belastbare Verifikation

## 3. Scope
### IN SCOPE
- Intent Engine Konfiguration prüfen: Weather-Intent muss system.weather Tool priorisieren
- Skill Selector Logik prüfen: Warum wird bei Weather-Intent kein Tool-Call ausgeführt?
- LLM-Knowledge Fallback deaktivieren für Weather-Intent (oder nur als echten Fallback wenn Tool nicht verfügbar)
- Validierung dass Wetter-Anfragen system.weather Tool-Call mit korrekten Parametern auslösen

### OUT OF SCOPE
- Frontend-Rendering-Fehler (BACKLOG-025) - dieses Item muss separat behoben werden
- Test-Infrastruktur-Änderungen (dies ist ein Backend-Intent-Routing-Bug)

## 4. Umsetzungsschritte
1. Intent Engine Code analysieren: Wo wird Weather-Intent erkannt und Tool-Call entschieden?
2. Skill Selector Logik prüfen: Warum wird system.weather Tool nicht aufgerufen?
3. LLM-Knowledge Fallback Konfiguration prüfen: Ist Fallback zu aggressiv für Weather-Intent?
4. Fix implementieren: Weather-Intent muss immer system.weather Tool priorisieren
5. Tool-Call-Parameter validieren: Ort und Datum müssen korrekt übergeben werden
6. Test ausführen: TC-001 "Brauche ich morgen in München einen Regenschirm?" mit Tool-Call-Evidence

## 5. Acceptance Criteria
- [ ] Wetter-Anfragen lösen system.weather Tool-Call aus
- [ ] Tool-Call enthält korrekte Parameter (Ort, Datum)
- [ ] LLM-Wissen wird nur als Fallback verwendet wenn Tool nicht verfügbar
- [ ] Test TC-001 (und andere Weather-Tests) bestehen mit Tool-Call-Evidence

## 6. Tests / Validierung
- Reproduktion aus TEST-RUN-2026-05-12-001-TRUTH-REPORT: TC-001 Weather inference
- Tool-Call-Verifikation prüfen: system.weather Tool-Call ist sichtbar
- Tool-Call-Parameter prüfen: Ort und Datum sind korrekt
- Frontend-Rendering-Fehler muss behoben sein (BACKLOG-025) für vollständige Validierung

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für atomaren klaren Intent-Routing-Bugfix

---

## REOPEN CONTEXT
**Status:** DONE
**Completion Date:** 2026-05-13
**Fix Applied:** SkillSelector fallback policy updated to make system.weather mandatory instead of boosted for weather intent (backend/services/skill_selector.py line 163)
**Validation:** Manual Janus test successful, automated tests passed (test_weather_mandates_system_weather)

## DEPENDENCY
**Harte Vorbedingung:** BACKLOG-025 (Frontend Rendering Failure: "win is not defined" JavaScript Error) muss zuerst behoben werden, da Tool-Call-Verifikation durch Frontend-Rendering-Fehler blockiert ist. Ausführung direkt nach BACKLOG-025 empfohlen.
