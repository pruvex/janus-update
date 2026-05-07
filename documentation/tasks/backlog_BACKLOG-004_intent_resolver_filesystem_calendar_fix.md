# TASK FILE – BACKLOG-004

## Feature
BACKLOG-004 – Intent-Resolver erkennt Filesystem-Befehle fälschlich als Calendar-Intent

---

## TASK-001 – Intent-Resolver Filesystem-Keyword-Priorisierung implementieren ✅ COMPLETED

### Ziel
Intent-Resolver muss Filesystem-Keywords (desktop, ordner, dateien, verschiebe, erstellen) höher priorisieren als Calendar-Keywords (ordner, events) wenn der Kontext eindeutig Dateisystem-Operationen anfordert.

### Beschreibung
Der Intent-Resolver erkennt derzeit Filesystem-Befehle fälschlich als Calendar-Intent, weil Calendar-Keywords wie "ordner" Vorrang haben. Dies muss korrigiert werden durch Kontext-basierte Priorisierung.

### 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-004
- **Beeinflusst:** backend/services/intent/ (Intent-Resolver Module)
- **Risiko-Einschätzung:** MEDIUM

### Files
- `backend/services/intent/` (Intent-Resolver Module)
- `tests/` (Unit-Tests für Intent-Resolver)

### Steps
1. Aktuelle Intent-Resolver-Logik analysieren und verstehen wie Keywords priorisiert werden ✅
2. Kontext-Erkennung implementieren: Wenn Prompt Filesystem-spezifische Keywords enthält (desktop, verschiebe, erstellen, dateien), dann Filesystem-Intent höher gewichten als Calendar-Intent ✅
3. Keyword-Gewichtung anpassen: Filesystem-Keywords erhalten höhere Priorität als Calendar-Keywords bei gemischten Prompts ✅
4. Logging hinzufügen: Logge Intent-Entscheidung mit Grund für Debugging ✅
5. Unit-Tests schreiben für Filesystem-Prompt, Calendar-Prompt (Regression) und gemischte Prompts ✅

### Acceptance Criteria
- [x] Prompt "erstell auf dem desktop einen ordner 'Bilder' und verschiebe jpg/png dateien" wird als Filesystem-Intent erkannt (nicht Calendar-Intent)
- [x] Backend-Log zeigt Intent-Entscheidung mit Begründung
- [x] Unit-Tests existieren und laufen erfolgreich
- [x] Keine Regression bei reinen Calendar-Prompts

### Tests
- Unit-Test für Intent-Resolver mit Filesystem-Prompt ✅
- Unit-Test für Intent-Resolver mit Calendar-Prompt (Regressionstest) ✅
- Unit-Test für gemischte Prompts ✅

### Model
- **Assigned Model:** SWE 1.6
- **Reason:** Intent-Resolver-Änderung mit komplexer Logik und Regression-Risiko

### Implementation Details
- **Geänderte Dateien:**
  - `backend/services/orchestrator/intent_engine.py`:
    - FILESYSTEM_ACTION_MARKERS, FILESYSTEM_OBJECT_MARKERS, FILESYSTEM_PATH_MARKERS hinzugefügt
    - detect_filesystem_intent() Methode implementiert
    - detect_calendar_intent() mit Filesystem-Veto erweitert
    - Logging für FILESYSTEM-OVERRIDE und FILESYSTEM-INTENT hinzugefügt
  - `backend/tests/unit/test_intent_filesystem_priority.py`:
    - 17 Unit-Tests für Filesystem-Intent-Priorisierung
    - Tests für Filesystem-Detection, Calendar-Veto, Regression, gemischte Prompts

- **Testergebnisse:** 17/17 Tests bestanden

---

## TASK-002 – Entity-Resolver WEAK_MATCH-Fallback korrigieren ✅ COMPLETED

### Ziel
Entity-Resolver darf keine WEAK_MATCH Calendar-Entities erzwingen wenn Filesystem-Tools verfügbar sind und der Prompt Filesystem-Operationen anfordert.

### Beschreibung
Entity-Resolver erkennt "Ordner" als WEAK_MATCH und erzwingt calendar.list_events (VIDEO-FORCE) auch wenn Filesystem-Tools verfügbar sind. Dies muss durch Kontext-Prüfung verhindert werden.

### 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-004
- **Beeinflusst:** backend/services/orchestrator/entity_resolver.py
- **Risiko-Einschätzung:** MEDIUM

### Files
- `backend/services/intent/entity_resolver.py` (oder entsprechende Datei)
- `backend/services/intent/` (verwandte Module)

### Steps
1. Aktuelle Entity-Resolver-Logik analysieren und verstehen wie WEAK_MATCH und VIDEO-FORCE ausgelöst werden ✅
2. Kontext-Prüfung implementieren: Wenn Intent-Resolver Filesystem-Intent erkannt hat, dann WEAK_MATCH Calendar-Entities nicht erzwingen ✅
3. Fallback-Logik anpassen: Bei Filesystem-Intents Filesystem-Tools bevorzugen statt Calendar-List-Events ✅
4. Logging anpassen: ENTITY-RESOLVER FALLBACK_TO_LIST nur loggen wenn tatsächlich notwendig ✅

### Acceptance Criteria
- [x] "Ordner" im Kontext von Dateisystem-Operationen wird nicht als Calendar-Entity gematcht
- [x] Backend-Log zeigt kein ENTITY-RESOLVER FALLBACK_TO_LIST bei Filesystem-Intents
- [x] Keine Regression bei Calendar-Intents mit echten WEAK_MATCH Calendar-Entities

### Tests
- Unit-Test für Entity-Resolver mit Filesystem-Intent und "Ordner"-Keyword ✅
- Unit-Test für Entity-Resolver mit Calendar-Intent und WEAK_MATCH (Regressionstest) ✅

### Model
- **Assigned Model:** SWE 1.6
- **Reason:** Multi-file Entity-Resolver-Änderung mit komplexer Fallback-Logik und Regression-Risiko

### Implementation Details
- **Geänderte Dateien:**
  - `backend/services/orchestrator/entity_resolver.py`:
    - `is_filesystem_intent` Parameter zur `resolve()` Methode hinzugefügt
    - WEAK_MATCH Logik angepasst: Bei Filesystem-Intent wird `CLARIFY_USER` statt `FALLBACK_TO_LIST` zurückgegeben
    - Leerer Snapshot Logik angepasst: Bei Filesystem-Intent wird `CLARIFY_USER` statt `FALLBACK_TO_LIST` zurückgegeben
    - Logging für Filesystem-Intent Veto hinzugefügt
  - `backend/tests/unit/test_entity_resolver_filesystem_veto.py`:
    - 8 Unit-Tests für Entity-Resolver Filesystem-Intent Veto
    - Tests für WEAK_MATCH Veto, Regression, RESOLVED-Matches, leere Snapshots

- **Testergebnisse:** 8/8 Tests bestanden

---

## TASK-003 – Orchestrator VIDEO-FORCE bei Filesystem-Intents verhindern ✅ COMPLETED

### Ziel
VIDEO-FORCE darf nicht bei Filesystem-Intents angewendet werden.

### Beschreibung
Orchestrator wendet VIDEO-FORCE an und erzwingt tool_choice=calendar.list_events auch bei Filesystem-Intents. Dies muss durch Intent-basierte Guard verhindert werden.

### 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-004
- **Beeinflusst:** backend/services/orchestrator/orchestrator.py
- **Risiko-Einschätzung:** MEDIUM

### Files
- `backend/services/orchestrator/orchestrator.py` (oder entsprechende Datei)
- `backend/services/orchestrator/` (verwandte Module)

### Steps
1. Aktuelle Orchestrator-Logik analysieren und verstehen wie VIDEO-FORCE ausgelöst wird ✅
2. Intent-basierte Guard implementieren: VIDEO-FORCE nur anwenden wenn Intent Calendar ist, nicht bei Filesystem-Intent ✅
3. Tool-Choice-Logik anpassen: Bei Filesystem-Intents Filesystem-Tools bevorzugen ✅
4. Logging anpassen: VIDEO-FORCE nur loggen wenn tatsächlich angewendet ✅

### Acceptance Criteria
- [x] VIDEO-FORCE wird nicht bei Filesystem-Intents angewendet
- [x] Backend-Log zeigt kein VIDEO-FORCE bei Filesystem-Intents
- [x] Keine Regression bei Calendar-Intents die VIDEO-FORCE benötigen

### Tests
- Unit-Test für Orchestrator mit Filesystem-Intent ✅
- Unit-Test für Orchestrator mit Calendar-Intent (Regressionstest) ✅

### Model
- **Assigned Model:** SWE 1.6
- **Reason:** Orchestrator-Änderung mit komplexer Tool-Choice-Logik und Regression-Risiko

### Implementation Details
- **Geänderte Dateien:**
  - `backend/services/orchestrator/intent_engine.py`:
    - `is_filesystem_intent` zur IntentDetectionResult-Klasse hinzugefügt
    - Filesystem-Intent-Erkennung zur detect_intents Methode hinzugefügt
  - `backend/services/orchestrator/execution_dispatcher.py`:
    - `_is_filesystem_intent` Variable hinzugefügt
    - Guard implementiert: VIDEO-FORCE wird übersprungen bei Filesystem-Intent
    - Logging für VIDEO-FORCE SKIP hinzugefügt
  - `backend/services/chat_orchestrator.py`:
    - `is_filesystem_intent` zum Workflow hinzugefügt (aus Intent-Ergebnis)
  - `backend/tests/unit/test_video_force_filesystem_veto.py`:
    - 10 Unit-Tests für VIDEO-FORCE Filesystem-Intent Veto
    - Tests für Filesystem-Intent-Detection, Calendar-Regression, gemischte Prompts

- **Testergebnisse:** 10/10 Tests bestanden

---

## TASK-004 – Skill-Selector Filesystem-vs-Calendar-Erkennung validieren ✅ COMPLETED

### Ziel
Skill-Selector korrekt erkennt Filesystem vs Calendar-Intents und wählt entsprechende Tools.

### Beschreibung
Skill-Selector muss sicherstellen, dass bei Filesystem-Intents Filesystem-Tools ausgewählt werden und bei Calendar-Intents Calendar-Tools. Validierung der Intent-zu-Tool-Mapping.

### 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-004
- **Beeinflusst:** backend/services/skill_selector.py
- **Risiko-Einschätzung:** LOW

### Files
- `backend/services/skill_selector.py` (oder entsprechende Datei)
- `backend/services/skill/` (verwandte Module)

### Steps
1. Aktuelle Skill-Selector-Logik analysieren und verstehen wie Intent zu Tool-Mapping funktioniert ✅
2. Intent-zu-Tool-Mapping validieren: Filesystem-Intent → Filesystem-Tools, Calendar-Intent → Calendar-Tools ✅
3. Mapping anpassen falls notwendig für konsistentes Verhalten ✅
4. Logging hinzufügen: Logge gewählte Tools basierend auf Intent ✅

### Acceptance Criteria
- [x] Filesystem-Intents wählen Filesystem-Tools (filesystem.create_directory, filesystem.move_files)
- [x] Calendar-Intents wählen Calendar-Tools (calendar.list_events)
- [x] Keine Regression bei bestehenden Intent-zu-Tool-Mappings

### Tests
- Unit-Test für Skill-Selector mit Filesystem-Intent ✅
- Unit-Test für Skill-Selector mit Calendar-Intent ✅
- Integrationstest für kompletten Intent-zu-Tool-Flow ✅

### Model
- **Assigned Model:** SWE 1.6
- **Reason:** Skill-Selector-Änderung mit Intent-zu-Tool-Mapping und Regression-Risiko

### Implementation Details
- **Geänderte Dateien:**
  - `backend/services/skill_selector.py`:
    - Filesystem-Intent-Handling zur _intent_policy Methode hinzugefügt
    - Logging für gewählte Tools basierend auf Intent hinzugefügt
    - Filesystem-Intent wird erkannt und Calendar-Tools werden nicht erzwungen
  - `backend/tests/unit/test_skill_selector_filesystem_calendar.py`:
    - 9 Unit-Tests für Skill-Selector Filesystem-vs-Calendar-Erkennung
    - Tests für Filesystem-Intent-Erkennung, Calendar-Regression, Logging, Edge Cases

- **Testergebnisse:** 9/9 Tests bestanden

---

## TASK-005 – Integrationstest für Filesystem-Intent-Flow schreiben

### Ziel
Integrationstest validiert den kompletten Flow von Prompt über Intent-Resolver zu Tool-Aufruf für Filesystem-Operationen.

### Beschreibung
Integrationstest simuliert den Reproduktions-Prompt und validiert dass Filesystem-Tools korrekt aufgerufen werden ohne 504 Timeout.

### Files
- `tests/integration/test_intent_resolver_filesystem.py` (neu)
- `tests/integration/` (verwandte Test-Dateien)

### Steps
1. Integrationstest-Datei erstellen für Filesystem-Intent-Flow
2. Testfall implementieren: Prompt "erstell auf dem desktop einen ordner 'Bilder' und verschiebe jpg/png dateien"
3. Validierungen implementieren: Intent ist Filesystem, Entity-Resolver erzwingt keine Calendar-Entities, VIDEO-FORCE nicht angewendet, Filesystem-Tools aufgerufen
4. Test ausführen und grün machen

### Acceptance Criteria
- [ ] Integrationstest existiert und läuft erfolgreich
- [ ] Test validiert kompletten Flow von Prompt zu Tool-Aufruf
- [ ] Kein 504 Timeout im Test

### Tests
- Integrationstest selbst ist der Test

### Model
- **Assigned Model:** SWE 1.6
- **Reason:** Integrationstest mit mehreren Modulen und komplexem Flow

---

## TASK-006 – Manueller End-to-End Test mit Reproduktions-Prompt

### Ziel
Manueller Test mit dem originalen Reproduktions-Prompt validiert dass der Bug behoben ist.

### Beschreibung
Manueller Test in Janus mit dem exakten Reproduktions-Prompt aus der Spec validiert dass Filesystem-Tools aufgerufen werden und kein 504 Timeout auftritt.

### Files
- Keine Code-Änderungen, nur manueller Test

### Steps
1. Janus starten mit aktualisiertem Code
2. Prompt eingeben: "hi, erstell auf dem desktop einen ordener "Bilder" und verschiebe alles jpg und png dateien vom desktop in diesen ordner"
3. Backend-Logs prüfen: Kein ENTITY-RESOLVER FALLBACK_TO_LIST, kein VIDEO-FORCE, Filesystem-Tools aufgerufen
4. Frontend-Konsole prüfen: Kein 504 Deadline Exceeded, erfolgreiche Response
5. Ergebnis dokumentieren

### Acceptance Criteria
- [ ] Filesystem-Intents werden korrekt erkannt (nicht als Calendar-Intent)
- [ ] "Ordner" im Kontext von Dateisystem-Operationen wird nicht als Calendar-Entity gematcht
- [ ] Filesystem-Tools werden aufgerufen wenn Prompt eindeutig Filesystem-Operation anfordert
- [ ] Kein 504 Timeout durch falsch erzwungene Tools

### Tests
- Manueller End-to-End Test

### Model
- **Assigned Model:** Kimi k2.5
- **Reason:** Deterministischer manueller Test ohne Code-Änderungen, nur Validierung und Dokumentation

---

## AUSFÜHRUNGSKETTE
Reihenfolge: Sequenziell (TASK-001 → TASK-002 → TASK-003 → TASK-004 → TASK-005 → TASK-006)

## ZUGEWIESENE MODELLE
- SWE 1.6: TASK-001, TASK-002, TASK-003, TASK-004, TASK-005
- Kimi k2.5: TASK-006

## MODELL-BEDEUTUNG
Diese Zuweisungen sind Task-Ausführungsmodelle für spätere einzelne Skill-3-/Skill-4-Läufe. Sie sind NICHT das Modell für Skill 2.
