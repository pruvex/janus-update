# DIAMANT Audit Report V7.0

**Scope:** Forensic Code Audit & Regression Analysis (read-only)

**Status:** Tests are green, but live behavior shows functional regressions.

**Audit date:** 2026-03-07

---

## 0) Executive Summary (gnadenlos ehrlich)

Die Suite ist gruen, aber das System ist **architektonisch ueberangepasst an Tests** und hat in zentralen Flows eine semantische Drift:

1. **Rollen-Semantik im Chat ist inkonsistent** (`model` vs `assistant`) und wird beim Historie-Aufbau falsch rekonstruiert. Das ist ein harter Kandidat fuer Live-Qualitaetsverlust.
2. **Agent-Factory macht Early-Return am Orchestrator vorbei**, wodurch etablierte Guardrails/Context-Pfade umgangen werden.
3. **PDF/Audit-Logik ist im Orchestrator fragmentiert/dupliziert** (mehrere Dateiname-Rekonstruktionen, mehrere Audit-Status-Pfade), was den Fokus auf das richtige Dokument instabil macht.
4. **Viele Errors werden verschluckt oder in weiche Fallbacks gedreht**, statt sichtbar oder strukturiert propagiert.
5. **Test-Suite deckt gerade die regressionskritischen Live-Pfade nicht sauber ab** (mehrere Skip-Tests, gelockerte Assertions, Mock-heavy statt stateful integration).

Kurz: technisch stabil != funktional korrekt.

---

## 1) Forensische Analyse der V6.1-Pflaster

## 1.1 `backend/data/database.py`

### Beobachtung
- Lazy-Exports fuer Legacy (`__getattr__`) geben `Memory`, `Chat`, `Message` aus `models` zurueck.
  - Referenz: `backend/data/database.py:64-70`

### Risiko
- Das ist als Backward-Compat ok, aber es vernebelt die Ownership: `database.Chat` wirkt wie ein echtes Modul-Symbol, ist aber dynamisch.
- In Kombi mit testseitigem Monkeypatching auf `backend.data.database.Message` wird Produktionslogik auf Test-Doubles ausgerichtet.

### Urteil
- **Kein direkter Runtime-Bug allein durch Lazy-Export**, aber ein **Wartbarkeits- und Testillusion-Risiko**.

---

## 1.2 `backend/data/crud.py` (`create_message` & Umgebung)

### Beobachtung
- `create_message` arbeitet mit dynamischem Klassen-Introspektionspfad (`hasattr(sender/role/image_path)`):
  - Referenz: `backend/data/crud.py:79-109`
- Rollenmapping: `sender == "model"` wird auf `role="assistant"` gemappt.
  - Referenz: `backend/data/crud.py:83-85`
- Testfall erzwingt Patch auf `backend.data.database.Message`, nicht auf echte Model-Semantik:
  - Referenz: `backend/tests/test_crud.py:138-167`

### Kritische Nebenwirkung auf echten Chat-Flow
- Der Orchestrator schreibt am Ende mit Sender `"model"`:
  - Referenz: `backend/services/chat_orchestrator.py:2415`
- Daraus wird in DB effektiv `role="assistant"` (durch CRUD-Mapping).
- Beim Historie-Aufbau gilt aber: `assistant` nur wenn `msg.role == "model"`, sonst `user`:
  - Referenz: `backend/services/chat_orchestrator.py:1942-1943`

**Folge:** echte Assistant-Nachrichten mit `role="assistant"` werden als `user` in den naechsten Prompt geschoben.
Das ist eine **harte Kontext-Korruption**.

### Weitere unsaubere Stelle
- `update_contact`: nach `updates.pop("email")` wird `updates['email']` noch im Logger referenziert.
  - Referenz: `backend/data/crud.py:372-375`
- Das ist eine potenzielle `KeyError`-Quelle.

---

## 1.3 `backend/services/chat_orchestrator.py` (Agent-Factory vs Legacy-Pfade)

### Beobachtung
- Agent-Factory wird frueh entschieden und kann mit Early-Return aussteigen:
  - Gate: `backend/services/chat_orchestrator.py:1211-1218`
  - Early return: `backend/services/chat_orchestrator.py:1248-1260`
- Bei Fehler nur Warning + stiller Fallback:
  - Referenz: `backend/services/chat_orchestrator.py:1261-1262`

### Regressionsgefahr
- Dieser Early-Return umgeht grosse Teile des etablierten Standardflows:
  - PDF/Audit-Guidance, Kontextkompression, Tool-Loop-Disziplin, Observer-Statuslogik, weitere post-processing Guards.
- Die Audit-Detektion basiert stark auf prompt-spezifischen Triggern wie `SYSTEM-INSTRUKTION FUR DATEI-UPLOAD`:
  - Referenz: `backend/services/chat_orchestrator.py:1069`
- Follow-up-Formulierungen ohne diesen Marker koennen in Agent-Factory landen und damit den Audit-Kontext verlieren.

### Doppelte/fragmentierte Audit-Pfade
- Dateiname-Rekonstruktion passiert mehrfach:
  - Erste Runde: `1137-1157`
  - Zweite Runde: `1407-1432`
- Audit-Status-Update wird in mehreren Blöcken versucht:
  - Block 1: `2156-2191`
  - Block 2: `2450-2464`
  - Silent observer: `2468-2523`

**Folge:** schwer vorhersagbarer Zustand, hohe Drift-Gefahr zwischen Tests und Live.

---

## 2) Diamond-Score & Schwachstellen-Scan

## 2.1 Diamond-Score (1-10)

| Datei | Score | Urteil |
|---|---:|---|
| `backend/services/chat_orchestrator.py` | **4/10** | Feature-stark, aber ueberladen, viele Sonderpfade, doppelte Logik, hohe kognitive Last |
| `backend/data/crud.py` | **5/10** | Zweckmaessig, aber testgetrieben verbogen (Introspektions-Patchlogik in Kernpfad) |
| `backend/data/database.py` | **7/10** | Stabil, klar, aber Lazy-Export ist mittelfristig ein Struktur-Kompromiss |
| `backend/services/agent_planner.py` | **6/10** | Solide Basis, aber `should_use_agent` Heuristik ist zu simpel fuer kritische Routing-Entscheidungen |
| `backend/tests/routing/test_router.py` | **4/10** | Entschaerfte Assertions sichern gruenen Build, aber wenig echte Routing-Absicherung |

---

## 2.2 Stille Fehler (verschluckte Exceptions / weiche Fallbacks)

### Hohe Relevanz
1. Agent-Delegation-Fehler nur Warning + fallback, Nutzer bekommt Ursache nicht.
   - `backend/services/chat_orchestrator.py:1261-1262`
2. Config-Load mit bare `except` -> `{}`; kaputte Datei wird still geschluckt.
   - `backend/services/chat_orchestrator.py:819-824`
3. Memory-Parsing-Fehler werden im Loop mit `continue` verworfen.
   - `backend/services/chat_orchestrator.py:1032-1033`
4. Historie-Ladefehler nur Warning, danach evtl. Prompt ohne Kontext.
   - `backend/services/chat_orchestrator.py:1944-1945`
5. JSON-Parse bei Tool-Result auf `{}` fallback -> echte Fehlerdetails gehen verloren.
   - `backend/services/chat_orchestrator.py:2063-2067`

### Mittlere Relevanz
6. `init_db()` loggt Fehler, raised aber nicht -> App kann halbdefekt weiterlaufen.
   - `backend/data/database.py:95-112`
7. Kontakt-Update rollbackt still und gibt `None` zurueck ohne Fehlertransport.
   - `backend/data/crud.py:383-389`

---

## 2.3 Context-Leaks (speziell PDF-/Audit-Fokus)

1. **Role-Leak im History Buffer**: `assistant` wird als `user` behandelt.
   - Ursache: CRUD-Rollenmapping + Orchestrator-Historie-Decoder
   - Referenzen: `crud.py:83-85`, `chat_orchestrator.py:1942-1943`
2. **Agent Early-Return Leak**: bestehende Audit-/PDF-Leitplanken werden nicht durchlaufen.
   - Referenz: `chat_orchestrator.py:1248-1260`
3. **Audit-Dateiname mehrfach und unterschiedlich rekonstruiert** -> potenziell falsches Dokument im Folgezug.
   - Referenz: `chat_orchestrator.py:1137-1157`, `1407-1432`
4. **Audit-Status mehrfach in separaten Blöcken gesetzt** -> Race-/Divergenz-Risiko.
   - Referenz: `chat_orchestrator.py:2156-2191`, `2450-2464`, `2468-2523`

---

## 3) Regression-Report: Warum es trotz gruener Tests hakt

## 3.1 Hauptgruende

1. **Tests validieren oft Form statt Verhalten im Endzustand**.
2. **Brittle Assertions wurden durch weichere Response-Checks ersetzt**, wodurch interne Fehlrouten unsichtbar bleiben.
3. **Skip-Tests in regressionskritischen Bereichen** lassen Luecken offen.
4. **Mock-heavy statt stateful/integration**: DB-Rollenfluss und Prompt-History-Semantik werden kaum realistisch getestet.

## 3.2 Konkrete Luecken in der Test-Suite

1. Kein Test, der verifiziert, dass gespeicherte `assistant`-Nachrichten im naechsten Turn als assistant in `chat_history` landen.
   - relevante Code-Stellen: `crud.py:83-85`, `chat_orchestrator.py:1942-1943`
2. Kein integrierter Test fuer Agent-Factory + PDF-Audit-Follow-up (ohne Upload-Marker).
3. Kein Test fuer deterministische Einzigkeit des Audit-Status-Updates (ein Pfad, ein Commit, ein Zustand).
4. Skip-Luecken:
   - `backend/tests/test_orchestrator_logic.py:44-68`
   - `backend/tests/test_main_api.py:50-97`
5. Routing-Test fuer ambiguous intent wurde auf reine Textantwort reduziert.
   - `backend/tests/routing/test_router.py:93-105`

## 3.3 „Unsauere“ Stellen, die gruen gemacht wurden

1. CRUD-Introspektions-Branching (`hasattr` auf Message-Klasse) im Kernpfad statt klarer Schema-Migration.
   - `backend/data/crud.py:90-105`
2. Orchestrator: monolithischer 2500+ Zeilen State-Mix mit mehrfacher Zustandslogik (Audit, Observer, Vision, Agent).
   - `backend/services/chat_orchestrator.py`
3. Mehrere try/except-Fallbacks ohne strukturierte Fehlerklasse oder Incident-ID.
4. Gelockerte Routing-Assertions validieren kaum noch die eigentliche Entscheidungslogik.

---

## 4) Master-Plan zur Reinigung (Phase Q: The Great Cleaning)

## 4.1 Refactoring-Prioritaetenliste (sauberer Code statt mehr Pflaster)

### P0 (sofort, blocker fuer Live-Regression)

1. **Role-Semantik vereinheitlichen (single source of truth)**
   - Entscheiden: intern nur `assistant` oder nur `model`.
   - `crud.create_message`, Historie-Rebuild und alle Writer/Reader auf eine Norm bringen.
   - Erfolgsmetrik: 0 role remap branches, 1 canonical enum.

2. **Agent-Factory Guardrails anheben**
   - Kein Early-Return vor Audit-/Kontext-Pipeline.
   - Agent nur als Subflow innerhalb desselben orchestrierten Lifecycle.
   - Erfolgsmetrik: PDF/Audit-Follow-up reproduzierbar ohne Marker.

3. **Audit-Status/Dateiname zentralisieren**
   - Eine Funktion fuer Dateiname-Aufloesung, eine Funktion fuer Audit-Status-Persistenz.
   - Entfernen doppelter Observer-/Ampel-Updates.
   - Erfolgsmetrik: genau 1 write-path pro Turn.

### P1 (direkt danach)

4. **Structured Error Policy einfuehren**
   - Keine bare excepts in Kernpfaden.
   - Domainenahes Error-Objekt (code, origin, user_visible, retryable).
   - Erfolgsmetrik: jedes swallowed exception pattern entfernt oder begruendet.

5. **Orchestrator entflechten**
   - Aufteilen in:
     - Intake & Mode Detection
     - Context Assembly
     - LLM/Tool Execution Loop
     - Post-Processing/Status Sync
   - Erfolgsmetrik: <800 Zeilen pro Modul, klarer Datenvertrag zwischen Stufen.

6. **CRUD bereinigen**
   - Entferne testgetriebenes Klassen-Introspektionsverhalten aus `create_message`.
   - Migration oder adapter layer explizit, nicht via `hasattr`.

### P2 (Qualitaetsabsicherung)

7. **Testpyramide neu ausrichten auf Live-Regressionen**
   - Stateful Integration-Tests fuer:
     - role roundtrip in history
     - PDF audit multi-turn follow-up
     - agent + audit coexistence
     - audit status consistency

8. **Skipped Tests abbauen mit klaren Owners/Deadlines**
   - `test_orchestrator_logic`, `test_main_api` zuerst.

9. **Regression Gates definieren**
   - Vor Merge: Live-parity smoke (nicht nur unit green), inklusive PDF-turn continuity.

---

## 4.2 Empfohlene Umsetzungsreihenfolge (2 Sprints)

### Sprint Q1
- P0.1 Role-Semantik
- P0.2 Agent-Factory ohne Early-Return
- P0.3 Audit write-path singularisieren
- Neue Integrationstests fuer genau diese 3 Themen

### Sprint Q2
- P1.4 Structured Error Policy
- P1.5 Orchestrator-Modularisierung
- P1.6 CRUD-Hardening
- P2 Regression gates + Skip-Abbau

---

## 4.3 Definition of Done fuer Phase Q

1. Keine Kontext-Rollenkorruption mehr im Prompt-History-Build.
2. PDF/Audit-Follow-up funktioniert robust ohne Spezialprompt-Marker.
3. Audit-Status wird deterministisch an einer Stelle gesetzt.
4. Keine kritischen bare/silent excepts im Kernpfad ohne begruendeten Kommentar.
5. Mindestens 4 neue stateful Integration-Tests decken die bisherigen Live-Regressionen ab.

---

## 5) Abschlussbewertung

Die Regressionen sind **nicht paradox**, sondern konsistent mit dem aktuellen Zustand:
- Testgruen wurde durch Kompatibilitaets- und Assertion-Entschaerfung erreicht,
- waehrend die semantische Konsistenz der Laufzeitpfade (Role, Routing, Audit-State) nicht ausreichend durch echte Integrationsszenarien abgesichert ist.

**Empfehlung:** Phase Q als strukturelle Bereinigung priorisieren, keine weiteren taktischen Pflaster im Orchestrator-Kern.
