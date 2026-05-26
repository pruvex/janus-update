# BACKLOG TASK – BACKLOG-020 – Chatfenster-Resize-Problem: Vertikales Resizen blockiert nach Größenänderung

## 1. Ziel
Das Chatfenster lässt sich frei von der unteren rechten Ecke resizen (horizontal + vertikal), ohne dass nach dem ersten Resize-Versuch vertikales Resizen blockiert wird.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-020
- **Beeinflusst:** Frontend / UI / Chat Window / Resize Handler / CSS
- **Risiko-Einschätzung:** MEDIUM

## 3. Scope
### IN SCOPE
- Resize-Handler für Chatfenster reparieren
- CSS-Constraints prüfen und korrigieren
- Vertikales Resizen nach erstem Resize-Versuch wiederherstellen
- Resize über die Ecke ermöglichen
- Reset-Button oben links bleibt funktional
- Feste Initialgröße beim Start erhalten

### OUT OF SCOPE
- Änderung an Chat-Logik oder Backend
- Änderung an anderen UI-Komponenten

## 4. Umsetzungsschritte
1. Frontend-Code für Chatfenster-Resize-Handler lokalisieren (vermutlich in `frontend/js/modules/chat.js` oder ähnlich)
2. Resize-Handler-Logik auf Blockade nach erstem Resize prüfen
3. CSS-Constraints für Chatfenster prüfen (vermutlich in `frontend/css/` oder inline styles)
4. Ursache identifizieren: Resize-Handler oder CSS-Constraints blockieren vertikales Resizen nach erstem Resize-Versuch
5. Fix implementieren: Vertikales Resizen freigeben, keine automatische Größe erzwingen
6. Reset-Button-Logik prüfen und sicherstellen, dass er weiterhin wie erwartet funktioniert
7. Testen: Chatfenster öffnen → Resize von unterer rechter Ecke → vertikales Resizen möglich → Resize über Ecke möglich → Reset-Button funktioniert

## 5. Acceptance Criteria
- [ ] Chatfenster lässt sich frei von der unteren rechten Ecke resizen (horizontal + vertikal)
- [ ] Kein automatischer Sprung auf eine bestimmte Größe beim Resize
- [ ] Resize-Verhalten ist stabil und reproduzierbar
- [ ] Reset-Button oben links funktioniert weiterhin wie erwartet
- [ ] Feste Initialgröße beim Start bleibt erhalten (gewünschtes Verhalten)

## 6. Tests / Validierung
- Manuelles Testen mit beiden Chatfenstern ("Videos über Fische" und "Zweites Fenster")
- Reproduktionsschritte aus Backlog nachvollziehen
- Frontend-Konsole auf Fehlermeldungen prüfen

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für atomaren klaren UI-Bugfix mit deterministischem Scope.
