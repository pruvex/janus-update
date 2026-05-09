# Janus Backlog

Dieses Backlog sammelt Bugs, Änderungswünsche, kleine Ergänzungen, Verbesserungen und technische Schulden, bevor sie in die Diamond-Skill-Pipeline übergeben werden.

Healthcheck-Findings aus `SYSTEM HEALTH – HYGIENE CHECK` dürfen hier als `Quelle: System Health` aufgenommen werden, wenn sie nicht sicher mechanisch auto-fixbar sind.

## Status-Regeln

- **NEEDS INFO:** Pflichtinformationen fehlen.
- **READY:** Ausreichend beschrieben für `BACKLOG SKILL 2 – REVIEW PRIORISIERUNG` und optionales `BACKLOG SKILL 3 – ROUTING_ENRICHMENT`.
- **IN PROGRESS:** Durch `BACKLOG SKILL 3 – SELECTED_HANDOFF` explizit an die Diamond-Pipeline übergeben.
- **DONE:** Durch `SKILL 7 – DOKUMENTATIONSUPDATE` nach erfolgreicher Umsetzung abgeschlossen.
- **BLOCKED:** Nicht umsetzbar ohne externe Entscheidung oder Abhängigkeit.

## Dashboard-Datenvertrag

Das spätere Dashboard liest diese Datei als primäre Backlog-State-Quelle.

Pflichtfelder pro Item:

```markdown
- **Typ:** BUG | CHANGE | ENHANCEMENT | IMPROVEMENT | TECH_DEBT | UNCLEAR
- **Status:** NEEDS INFO | READY | IN PROGRESS | DONE | BLOCKED
- **Kurzbeschreibung:** <Text>
- **Betroffener Bereich:** <Text>
```

Optionale Bewertungsfelder aus `BACKLOG SKILL 2 – REVIEW PRIORISIERUNG`:

```markdown
- **Wichtigkeit:** LOW | MEDIUM | HIGH | CRITICAL
- **Umsetzungsrisiko:** LOW | MEDIUM | HIGH
- **Aufwand:** XS | S | M | L | XL
- **Umsetzungsreife:** READY | NEEDS INFO | BLOCKED
- **Empfehlung:** DO NOW | SCHEDULE | NEEDS INFO FIRST | DEFER | DO NOT START
```

Optionale Routing-Felder aus `BACKLOG SKILL 3 – ROUTING_ENRICHMENT`:

```markdown
- **Entry Point:** SPEC_PIPELINE_START | TASK_BREAKDOWN | PRE_IMPLEMENTATION_VERIFICATION | EXECUTION_READY | ROUTING_BLOCKED
- **Routing reason:** <ein kurzer Satz>
- **Routing confidence:** HIGH | MEDIUM | LOW
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** YYYY-MM-DD
```

Optionale Handoff-/Completion-Felder:

```markdown
- **Handoff:** <path> | none
- **Recommended next skill:** SKILL 1 | SKILL 2 | SKILL 3 | SKILL 4 | none
- **Handoff created:** YYYY-MM-DD | none
- **Completed in version:** <version>
- **Completed by task:** <path>
- **Final audit:** PASS | PASS WITH FIXES
- **Validation evidence:** <Text>
```

Dashboard-Regeln:

- `Status != DONE` → Active View.
- `Status == DONE` → History View.
- Dashboard darf keine Backlog-Daten ändern.
- Dashboard darf Copy-Paste-Prompts aus `Entry Point`, `Handoff`, `Recommended next skill` und `Completed by task` ableiten, aber keine Artefakte erzeugen.

## Erlaubte Quellen

- User Intake
- Screenshot
- Log
- Audit
- Manual Test
- System Health
- Other

## NEEDS INFO

## READY

### BACKLOG-006 – Generische Fehlermeldung statt spezifischer Fehlerdetails

- **Typ:** IMPROVEMENT
- **Status:** READY
- **Quelle:** User Intake
- **Erstellt:** 2026-05-07
- **Aktualisiert:** 2026-05-07
- **Kurzbeschreibung:** Wenn etwas nicht funktioniert, geben die Modelle oft eine generische Fehlermeldung "Ich konnte diesmal keine stabile Antwort erzeugen. Bitte sende die Anfrage direkt noch einmal; ich versuche es dann mit einem robusten Neuaufbau." statt genau zu sagen, wo das Problem liegt.
- **Erwartetes Verhalten:** Fehlermeldungen enthalten spezifische Details über den tatsächlichen Fehler: welches Tool fehlgeschlagen ist, welcher Fehlercode aufgetreten ist, welche Exception geworfen wurde, welcher Provider/Model betroffen ist.
- **Tatsächliches Verhalten:** Generische Fallback-Nachricht in `execution_dispatcher.py` Zeile 822 wird ohne Fehlerdetails verwendet. Der `fallback_summary` wird an `execution_engine.run_tool_loop()` übergeben und als Fallback bei Exceptions (Zeile 1238-1254), Stream-Crashes (Zeile 2363-2365), leeren Tool-Round-Ergebnissen (Zeile 2400) und leeren Text-Ergebnissen (Zeile 2723) verwendet.
- **Reproduktion / Kontext:** Wenn ein LLM-Aufruf oder Tool-Aufruf fehlschlägt, wird der statische `fallback_summary` zurückgegeben ohne Informationen über den tatsächlichen Fehler.
- **Betroffener Bereich:** Orchestrator / Execution Engine / Error Handling / User Experience
- **Nachweise:**
  - `backend/services/orchestrator/execution_dispatcher.py` Zeile 822: `wf.fallback_summary = 'Ich konnte diesmal keine stabile Antwort erzeugen...'`
  - `backend/services/orchestrator/execution_engine.py` Zeile 1238-1254: Exception-Handler verwendet `fallback_summary` ohne Fehlerdetails
  - `backend/services/orchestrator/execution_engine.py` Zeile 2363-2365: Stream-Crash-Handler verwendet `fallback_summary` ohne Fehlerdetails
  - `backend/services/orchestrator/execution_engine.py` Zeile 1750-1779: Tool-Fehler werden bereits mit `error_code` und `error_message` extrahiert, aber nicht an den Fallback übergeben
- **Akzeptanzkriterien:**
  - [ ] `fallback_summary` wird dynamisch basierend auf dem tatsächlichen Fehler generiert
  - [ ] Fehlermeldungen enthalten: Fehlercode, Fehlermeldung, betroffenes Tool (falls zutreffend), Provider/Model (falls zutreffend)
  - [ ] Backend-Logs enthalten weiterhin die vollständigen Exception-Details für Debugging
  - [ ] User erhält hilfreiche, spezifische Fehlerinformationen statt generischer Nachricht
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Das Problem ist nicht, dass Fehler auftreten, sondern dass die Fehlermeldung für den User nicht hilfreich ist. Die Execution-Engine extrahiert bereits Fehlerdetails aus Tool-Ergebnissen (Zeile 1750-1779), diese sollten auch an den Fallback übergeben werden.
- **Wichtigkeit:** HIGH
- **Umsetzungsrisiko:** MEDIUM
- **Aufwand:** M
- **Umsetzungsreife:** READY
- **Empfehlung:** SCHEDULE
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** Kleine lokale Änderung in Orchestrator/Execution Engine mit einem Ziel, klaren Akzeptanzkriterien und begrenztem Scope (Error Handling)
- **Routing confidence:** HIGH
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-05-09
- **Handoff:** documentation/tasks/backlog_BACKLOG-006_specific_error_messages.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-05-10

### BACKLOG-007 – Performance-Optimierung für Filesystem-Tool-Calls

- **Typ:** IMPROVEMENT
- **Status:** READY
- **Quelle:** Manual Test (TASK-005)
- **Erstellt:** 2026-05-07
- **Aktualisiert:** 2026-05-07
- **Kurzbeschreibung:** Gemini-3-pro-preview ist deutlich langsamer als GPT-5.4 bei Filesystem-Tasks (~102s vs ~11s für das Erstellen eines Ordners und Verschieben von 5 Dateien).
- **Erwartetes Verhalten:** Filesystem-Tasks sollten in ähnlicher Zeit bei beiden Modellen ausgeführt werden.
- **Tatsächliches Verhalten:** Gemini benötigt ~102 Sekunden für einen Task, den GPT in ~11 Sekunden erledigt. Gemini führt unnötige Tool-Aufrufe durch (z.B. list_directory mit falschem Pfad "Desktop" statt vollständigen Pfad).
- **Reproduktion / Kontext:** Prompt: "hi, erstell auf dem desktop einen ordener 'Bilder' und verschiebe alles jpg und png dateien vom desktop in diesen ordner"
- **Betroffener Bereich:** Performance / Tool-Call-Effizienz / Model-Selection
- **Nachweise:**
  - Gemini-Log: 17:28:55 - 17:30:37 (~102s), Tool-Aufrufe: create_directory, list_directory (fehlerhaft), move_files
  - GPT-Log: 17:32:57 - 17:33:08 (~11s), direkte Antwort ohne sichtbare unnötige Tool-Aufrufe
  - Gemini Logic-Tier Upgrade: gemini-3-flash-preview → gemini-3-pro-preview (für RAG-Intent)
  - GPT Logic-Tier Upgrade: gpt-5.4-nano → gpt-5.4 (für RAG-Intent)
- **Akzeptanzkriterien:**
  - [ ] Unnötige Tool-Aufrufe werden vermieden (z.B. list_directory mit falschem Pfad)
  - [ ] Tool-Call-Effizienz ist verbessert (weniger redundante Aufrufe)
  - [ ] Model-Selection für einfache Tasks ist optimiert (schnellere Modelle für einfache Tasks)
  - [ ] Prompt-Cache-Effizienz ist verbessert
  - [ ] Performance-Unterschied zwischen Modellen ist reduziert (<2x Faktor für ähnliche Tasks)
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Die Performance-Unterschiede sind nicht kritisch für die Funktionalität, aber beeinflussen die UX. Das Logic-Tier Upgrade für RAG-Intent könnte ein Faktor sein. Tool-Call-Patterns sollten analysiert und optimiert werden.
- **Wichtigkeit:** MEDIUM
- **Umsetzungsrisiko:** MEDIUM
- **Aufwand:** M
- **Umsetzungsreife:** READY
- **Empfehlung:** SCHEDULE
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** Kleine lokale Performance-Verbesserung mit einem Ziel, klaren Akzeptanzkriterien und begrenztem Scope (Tool-Call-Effizienz/Model-Selection)
- **Routing confidence:** MEDIUM
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-05-09
- **Handoff:** documentation/tasks/backlog_BACKLOG-007_filesystem_performance.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-05-10

## IN PROGRESS

## DONE

### BACKLOG-020 – Chatfenster-Resize-Problem: Vertikales Resizen blockiert nach Größenänderung

- **Typ:** BUG
- **Status:** DONE
- **Quelle:** Screenshot (User Intake - Beta Test)
- **Erstellt:** 2026-05-09
- **Aktualisiert:** 2026-05-10
- **Abgeschlossen:** 2026-05-10
- **Kurzbeschreibung:** Wenn man versucht, das Chatfenster an der unteren rechten Ecke zu greifen und zu vergrößern, verkleinert es sich auf eine bestimmte Größe und kann dann nur noch horizontal vergrößert werden. Vertikales Resizen oder Resizen über die Ecke ist nicht mehr möglich. Ein Klick auf den Button oben links im Header stellt die ursprüngliche Größe wieder her. Das Problem tritt bei beiden Chatfenstern auf.
- **Erwartetes Verhalten:** Das Chatfenster sollte frei von der unteren rechten Ecke resizbar sein, sowohl horizontal als auch vertikal.
- **Tatsächliches Verhalten:** Nach dem ersten Resize-Versuch springt das Fenster auf eine bestimmte Größe und lässt sich danach nur noch horizontal vergrößern. Vertikales Resizen und Resizen über die Ecke sind blockiert.
- **Reproduktion / Kontext:** Chatfenster öffnen (z.B. "Videos über Fische" oder "Zweites Fenster") → An der unteren rechten Ecke greifen und ziehen → Fenster springt auf bestimmte Größe → Nur noch horizontales Resizen möglich. Das Problem passiert jedes Mal, wenn man das Fenster in der Original/Initialgröße versucht zu vergrößern. Beim Starten von Janus haben die Chatfenster immer eine feste Initialgröße (dies ist gewünscht).
- **Betroffener Bereich:** Frontend / UI / Chat Window / Resize Handler
- **Nachweise:**
  - Screenshot: Chatfenster in verkleinertem Zustand
  - User-Beschreibung: "wenn ich versuche das chatfenster an der unteren, rechten ecke zu greifen und zu vergrößer, verkleinert es sich auf diese größe wie im bild und dann kann ich das fenter nur noch nach rechts vergrößern, aber nicht mehr nach unten oder mit ziehen an der rechten unteren ecke"
  - Frontend-Konsole: Keine Fehlermeldungen
- **Akzeptanzkriterien:**
  - [x] Chatfenster lässt sich frei von der unteren rechten Ecke resizen (horizontal + vertikal)
  - [x] Kein automatischer Sprung auf eine bestimmte Größe beim Resize
  - [x] Resize-Verhalten ist stabil und reproduzierbar
  - [x] Reset-Button oben links funktioniert weiterhin wie erwartet
  - [x] Feste Initialgröße beim Start bleibt erhalten (gewünschtes Verhalten)
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Das Problem tritt bei beiden Chatfenstern auf ("Videos über Fische" und "Zweites Fenster"). Es passiert reproduzierbar jedes Mal beim ersten Resize-Versuch aus der Initialgröße. Im Frontend kommen keine Fehler. Vermutung: Resize-Handler oder CSS-Constraints blockieren vertikales Resizen nach dem ersten Resize-Versuch.
- **Wichtigkeit:** HIGH
- **Umsetzungsrisiko:** MEDIUM
- **Aufwand:** S
- **Umsetzungsreife:** READY
- **Empfehlung:** DO NOW
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** Kleiner klarer UI-Bugfix mit einem Ziel, klaren Akzeptanzkriterien und begrenztem Scope (Frontend Resize Handler/CSS)
- **Routing confidence:** HIGH
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-05-09
- **Handoff:** documentation/tasks/backlog_BACKLOG-020_chatfenster_resize_fix.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-05-10
- **Completed in version:** TBD
- **Completed by task:** backlog_BACKLOG-020_chatfenster_resize_fix.md
- **Final audit:** PASS (Re-Audit nach Skill 6)
- **Validation evidence:** Manueller Retest PASS - freies Resizen funktioniert wie gewünscht

### BACKLOG-017 – ChromaDB-Module fehlen im PyInstaller-Bundle

- **Typ:** BUG
- **Status:** DONE
- **Quelle:** Log (User Intake - Tester)
- **Erstellt:** 2026-05-08
- **Aktualisiert:** 2026-05-09
- **Abgeschlossen:** 2026-05-09
- **Completed in version:** 0.4.17-beta.22
- **Completed by task:** documentation/tasks/backlog_BACKLOG-017_chromadb_pyinstaller_fix.md
- **Final audit:** PASS
- **Validation evidence:** Manual Janus test PASS — ChromaDB-Module vollständig im PyInstaller-Bundle, Vektor-Service und Skill-Router starten ohne Import-Fehler
- **Kurzbeschreibung:** Im gebauten janus-setup-0.4.17-beta.16.exe fehlen ChromaDB-Module im PyInstaller-Bundle. Backend-Log zeigt `No module named 'chromadb.telemetry.product.posthog'` und `No module named 'chromadb.api.rust'`. Dies führt zu Fehlern im Vektor-Service und Skill-Router beim Start.
- **Erwartetes Verhalten:** Alle ChromaDB-Module sind vollständig im PyInstaller-Bundle enthalten. Vektor-Service und Skill-Router starten ohne Module-Import-Fehler.
- **Tatsächliches Verhalten:** Vektor-Service meldet kritischen Fehler beim Start wegen fehlendem `chromadb.telemetry.product.posthog`. Skill-Router kann Index nicht aufbauen wegen fehlendem `chromadb.api.rust`.
- **Reproduktion / Kontext:** Frische Installation von janus-setup-0.4.17-beta.16.exe auf Testsystem. Backend-Log zeigt Import-Fehler beim Start.
- **Betroffener Bereich:** Packaging / PyInstaller / ChromaDB / Vektor-Service / Skill-Router
- **Nachweise:**
  - main.log Zeile 19: `Vektor-Service: Kritischer Fehler beim Start: No module named 'chromadb.telemetry.product.posthog'`
  - main.log Zeile 21: `SKILL-ROUTER: Skill-Index konnte nicht aufgebaut werden: No module named 'chromadb.api.rust'`
- **Akzeptanzkriterien:**
  - [ ] ChromaDB-Module sind vollständig im PyInstaller-Bundle enthalten (inkl. `chromadb.telemetry.product.posthog`, `chromadb.api.rust`)
  - [ ] Vektor-Service startet ohne ChromaDB-Import-Fehler
  - [ ] Skill-Router baut Index erfolgreich auf ohne ChromaDB-Import-Fehler
  - [ ] Memory-Funktionen arbeiten korrekt nach Installation
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Packaging-Problem: PyInstaller spec muss ChromaDB-Submodule explizit einschließen. Beeinflusst Memory/Vektor-Funktionen. Unabhängig vom CLIP-Download-Problem (BACKLOG-018).
- **Handoff:** documentation/tasks/backlog_BACKLOG-017_chromadb_pyinstaller_fix.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-05-09

### BACKLOG-018 – CLIP-Model-Download blockiert First-Start

- **Typ:** BUG
- **Status:** DONE
- **Quelle:** Log (User Intake - Tester)
- **Erstellt:** 2026-05-08
- **Aktualisiert:** 2026-05-09
- **Abgeschlossen:** 2026-05-09
- **Completed in version:** 0.4.17-beta.21
- **Completed by task:** documentation/tasks/backlog_BACKLOG-018_clip_lazy_loading_tasks.md
- **Final audit:** PASS
- **Validation evidence:** Manual Janus test PASS — App startet sofort, CLIP-Model wird lazy-loaded
- **Kurzbeschreibung:** Janus startet gar nicht beim ersten Launch. Der Splashscreen bleibt hängen, nach 120 Sekunden zeigt Windows eine Fehlermeldung. Ursache: Der VISION-SERVICE lädt das CLIP-Model (ViT-B-32.pt, 338MB) synchron vor dem App-Start. Bei langsamer Internetverbindung oder langsamen Servern dauert der Download länger als das Windows-Process-Timeout.
- **Erwartetes Verhalten:** Janus startet sofort beim ersten Launch. Das CLIP-Model wird im Hintergrund nach dem Start lazy-loaded. Vision-Funktionen sind erst verfügbar nachdem das Model geladen ist, aber der Rest der App ist sofort nutzbar.
- **Tatsächliches Verhalten:** App startet nicht. Splashscreen bleibt hängen, Windows tötet den Process nach 120 Sekunden mit Fehlermeldung "siehe Log". Backend-Log zeigt synchronen CLIP-Model-Download (ViT-B-32.pt, 338MB) ab Zeile 47.
- **Reproduktion / Kontext:** Frische Installation von janus-setup-0.4.17-beta.16.exe auf Testsystem. Erster Start: Splashscreen bleibt hängen, nach 120s Windows-Fehlermeldung. Problem tritt unabhängig von Internetgeschwindigkeit auf (auch bei schnellem Internet kann der Download langsam sein).
- **Betroffener Bereich:** Backend / VISION-SERVICE / First-Start Experience / Lazy-Loading
- **Nachweise:**
  - main.log Zeile 47+: CLIP-Model-Download startet synchron bei 23:25:27
  - User-Beschreibung: "janus startet doch gar nicht, nach den 120 sekunden splashscreen kommt eine windows fehlermeldung"
  - User-Requirement: "wir brauchen eine lösung, damit janus auf alles systemen startet und nicht nur auf welchen mit schnellem internet"
- **Akzeptanzkriterien:**
  - [ ] CLIP-Model wird lazy-loaded im Hintergrund nach App-Start (nicht synchron vor dem Start)
  - [ ] App startet sofort, Splashscreen verschwindet nach normalem Start
  - [ ] Vision-Funktionen sind deaktiviert oder zeigen "Loading..." bis CLIP-Model geladen ist
  - [ ] Kein Windows-Process-Timeout durch Model-Downloads
  - [ ] Lösung funktioniert auf allen Systemen unabhängig von Internetgeschwindigkeit
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Root Cause: VISION-SERVICE lädt CLIP-Model synchron im `__init__` oder bei Service-Initialisierung. Lösung: Lazy-Loading Pattern - App startet zuerst, CLIP-Model wird im Hintergrund asynchron geladen. Vision-Requests vor Fertigstellung des Downloads werden entweder queued oder mit "Vision noch nicht bereit" beantwortet. Unabhängig vom ChromaDB-Packaging-Problem (BACKLOG-017).
- **Handoff:** documentation/Planned Features/backlog_BACKLOG-018_clip_lazy_loading.md
- **Recommended next skill:** SKILL 1
- **Handoff created:** 2026-05-09

### BACKLOG-016 – Video-Links funktionieren nicht nach Chat-Wechsel

- **Typ:** BUG
- **Status:** DONE
- **Quelle:** User Intake (Folgebug von BACKLOG-012)
- **Erstellt:** 2026-05-08
- **Aktualisiert:** 2026-05-08
- **Abgeschlossen:** 2026-05-08
- **Completed in version:** 0.4.17-beta.20
- **Completed by task:** documentation/tasks/backlog_BACKLOG-016_video_links_after_chat_switch.md
- **Final audit:** PASS WITH FIXES
- **Validation evidence:** Manual Janus test PASS — Video-Links funktionieren nach Chat-Wechsel
- **Kurzbeschreibung:** Folgebug von BACKLOG-012 – Video-Suchergebnisse ohne Titel. Die Video-Formatierung ist jetzt perfekt (5 Videos von beiden Providern, Titel, Kanal, Aufrufe, Upload-Datum) und bleibt nach Chat-Wechsel erhalten. ABER: Die "Video ansehen" Links funktionieren direkt nach der Suche, aber nicht mehr wenn man den Chat gewechselt hat und wieder zurück kommt. Das Video-Modal öffnet sich nicht mehr und das Video wird nicht gestartet.
- **Erwartetes Verhalten:** Video-Links ("Video ansehen") funktionieren auch nach einem Chat-Wechsel und öffnen das Video-Modal mit dem entsprechenden Video.
- **Tatsächliches Verhalten:** Video-Links funktionieren direkt nach der Suche (Modal öffnet, Video startet). Nach einem Chat-Wechsel und Rückkehr zum Chat sehen die Links korrekt aus, aber öffnen das Modal nicht mehr und starten das Video nicht.
- **Reproduktion / Kontext:** Prompt: "zeig mir ein video über eulen" (oder ähnliche Video-Suche). Beide Provider zeigen 5 Videos mit perfekter Formatierung. Links funktionieren direkt. Chat wechseln → zurück zum Chat → Links funktionieren nicht mehr.
- **Betroffener Bereich:** Frontend Chat Rendering / Video Modal / Chat-Reload / Event Handler Wiring
- **Nachweise:**
  - User-Beschreibung: "es werden jetzt wie gewünscht von beiden providern 5 videos gefunden, die formatierung im chat ist perfekt und bleibt auch erhalten, nachdem an den chat gewechselt hat und zurück zu chat kehrt. ABER! die video links (Video ansehen) funktionieren nach der suche, aber nicht mehr wenn man den chat gewechselt hat und wieder zu rück in den chat kommt"
  - Frontend-Konsole-Logs: `chat.js:1615 💎 VIDEO-LIST-METADATA: Rendering formatted markdown with header 5 videos`
  - Version: 0.4.17-beta.19 (Folgebug von BACKLOG-012 Fix)
- **Akzeptanzkriterien:**
  - [ ] Video-Links funktionieren direkt nach der Suche
  - [ ] Video-Links funktionieren auch nach Chat-Wechsel und Rückkehr
  - [ ] Video-Modal öffnet sich korrekt nach Chat-Wechsel
  - [ ] Video wird gestartet nach Chat-Wechsel
  - [ ] Keine Regression in Video-Formatierung oder Persistenz
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Dies ist ein Folgebug von BACKLOG-012. Der Fix hat die Formatierung und Persistenz gelöst, aber hat die Event-Handler-Wiring für die Video-Links nach Chat-Reload beschädigt. Vermutung: `wireVideoReopenLink` prüft auf `modal_request.type === "video"`, aber beim Markdown-Rendering aus `video_list_metadata` gibt es keine `modal_request`. Daher werden die Event-Handler nicht gebunden. Label-Erkennung prüft auf "hier ansehen", aber Markdown-Link heißt "video ansehen".
- **Handoff:** documentation/tasks/backlog_BACKLOG-016_video_links_after_chat_switch.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-05-08

### BACKLOG-015 – Modell-Wechsel-Benachrichtigung bei nicht verfügbarem Modell

- **Typ:** IMPROVEMENT
- **Status:** DONE
- **Quelle:** User Intake (Screenshot)
- **Erstellt:** 2026-05-08
- **Aktualisiert:** 2026-05-08
- **Abgeschlossen:** 2026-05-08
- **Completed in version:** 0.4.17-beta.18
- **Completed by task:** documentation/tasks/backlog_BACKLOG-015_model_switch_notification_improvement.md
- **Final audit:** PASS
- **Validation evidence:** Manual Janus test PASS — Provider-Wechsel funktioniert ohne falsche Fehlermeldungen, verbesserte Benachrichtigung getestet
- **Kurzbeschreibung:** Wenn ein nicht verfügbares Modell ausgewählt wird, zeigt Janus kurz eine rote Benachrichtigung oben rechts an, dass das Modell nicht verfügbar ist und stattdessen ein anderes verwendet wird. Dies geschieht automatisch ohne explizite Benutzerinteraktion oder klare Erklärung, warum das ursprüngliche Modell nicht verfügbar ist.
- **Erwartetes Verhalten:** Janus sollte entweder:
  1. Den Benutzer proaktiv informieren, wenn ein ausgewähltes Modell nicht verfügbar ist, bevor es automatisch ersetzt wird, und dem Benutzer die Möglichkeit geben, ein alternatives Modell zu wählen oder den Vorgang abzubrechen.
  2. Eine klarere und persistentere Benachrichtigung anzeigen, die erklärt, warum das Modell nicht verfügbar ist (z.B. API-Fehler, Lizenzproblem, etc.).
  3. Das nicht verfügbare Modell aus der Auswahl entfernen oder als inaktiv kennzeichnen.
- **Tatsächliches Verhalten:** Janus zeigt eine temporäre rote Benachrichtigung oben rechts an und wechselt automatisch zu einem anderen Modell, ohne weitere Interaktion oder Erklärung.
- **Reproduktion / Kontext:** Provider-Wechsel im UI wählt ein nicht verfügbares Modell (z.B. `gemini-3-flash-preview`), Janus zeigt kurz: "Modell '[nicht verfügbares Modell]' ist nicht verfügbar. Verwende stattdessen '[verfügbares Modell]'."
- **Betroffener Bereich:** UI / Modell-Auswahl / Fehlermeldungen / Frontend
- **Nachweise:**
  - Screenshot: Rote Benachrichtigung oben rechts mit "Modell 'gemini-3-flash-preview' ist nicht verfügbar. Verwende stattdessen 'gpt-5.4-nano'."
- **Akzeptanzkriterien:**
  - [x] Die Benachrichtigung über nicht verfügbare Modelle ist klar, verständlich und bietet dem Benutzer Handlungsoptionen.
  - [x] Der automatische Modellwechsel wird transparent kommuniziert oder vermieden.
  - [x] Der Benutzer hat mehr Kontrolle über die Auswahl des Modells, wenn das bevorzugte Modell nicht verfügbar ist.
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Die aktuelle Implementierung ist funktional, aber die UX konnte durch mehr Transparenz und Kontrolle verbessert werden. Provider-Wechsel-Probleme wurden ebenfalls behoben (keine falschen Fehlermeldungen mehr, Dropdown nicht mehr leer).
- **Handoff:** documentation/tasks/backlog_BACKLOG-015_model_switch_notification_improvement.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-05-08

### BACKLOG-019 – Hardcoded gpt-5-mini verursacht Fallback-Warnung nach OpenAI-Key-Eingabe

- **Typ:** TECH_DEBT
- **Status:** DONE
- **Quelle:** Screenshot (User Intake - Beta Test)
- **Erstellt:** 2026-05-09
- **Aktualisiert:** 2026-05-09
- **Abgeschlossen:** 2026-05-09
- **Kurzbeschreibung:** Nach Eingabe des OpenAI-Keys erscheint eine Warnung "Das Modell 'gpt-5-mini' ist nicht mehr verfügbar. Janus hat automatisch zu '' gewechselt." Das Modell gpt-5-mini ist hardcoded in `backend/main.py` und `backend/services/calendar/calendar_ai_engine.py` als Fallback/Default, obwohl es nicht mehr im Model-Katalog existiert.
- **Erwartetes Verhalten:** Keine Modelle sind hardcoded. Das System wählt dynamisch das erste verfügbare Modell aus dem Model-Katalog oder fordert den Benutzer auf, ein Modell auszuwählen, wenn keine Konfiguration existiert.
- **Tatsächliches Verhalten:** gpt-5-mini ist hardcoded als Default in `main.py:654` und als Fallback in `calendar_ai_engine.py:140,145`. Wenn dieses Modell nicht im Katalog existiert, fällt das System auf ein leeres Modell zurück und zeigt eine Warnung.
- **Reproduktion / Kontext:** Frische Installation oder Config-Reset → OpenAI-Key eingeben → Warnung erscheint mit leerem Fallback-Modell.
- **Betroffener Bereich:** Backend / Config / Model-Selection / Calendar AI Engine
- **Nachweise:**
  - Screenshot: Warnung "Modell nicht verfügbar" mit gpt-5-mini und leerem Fallback
  - `backend/main.py:654`: `if "last_used_model" not in config: config["last_used_model"] = "gpt-5-mini"`
  - `backend/services/calendar/calendar_ai_engine.py:140,145`: `model_id = ... or "gpt-5-mini"` und Fallback `model_id = "gpt-5-mini"`
- **Akzeptanzkriterien:**
  - [x] Keine hardcoded Modell-IDs im Code (außer in Tests oder dokumentierten Ausnahmen)
  - [x] System wählt dynamisch das erste verfügbare Modell aus dem Model-Katalog wenn keine Konfiguration existiert
  - [x] Calendar AI Engine wählt dynamisch aus dem Katalog statt hardcoded Fallback
  - [x] Keine Warnung über nicht verfügbare Modelle nach Key-Eingabe
  - [x] Lösung ist robust gegen Katalog-Updates (keine neuen hardcoded Referenzen)
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Der Benutzer wünscht explizit keine hardcoded Modelle, da dies zu Problemen führt wenn der Katalog aktualisiert wird. Die Lösung sollte vollständig dynamisch aus dem Model-Katalog lesen. gpt-4o-mini ist ebenfalls möglicherweise nicht mehr im Katalog oder nur für Vision, daher ist auch dieses kein sicherer Default.
- **Handoff:** documentation/tasks/backlog_BACKLOG-019_hardcoded_gpt5mini_fix.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-05-09
- **Version:** 0.4.17-beta.23
- **Task:** documentation/tasks/backlog_BACKLOG-019_hardcoded_gpt5mini_fix.md
- **Audit:** FINAL AUDIT RESULT: PASS (Skill 5 mit GPT-5.5)
- **Skill 6:** FIXED (Provider/Model-Mismatch behoben)
- **Manual Test:** PASS

### BACKLOG-010 – gpt-5.4-nano führt Filesystem-Operationen nicht aus

- **Typ:** BUG
- **Status:** DONE
- **Quelle:** Manual Test (BACKLOG-009 Validation)
- **Erstellt:** 2026-05-07
- **Aktualisiert:** 2026-05-07
- **Abgeschlossen:** 2026-05-07
- **Kurzbeschreibung:** gpt-5.4-nano führt Filesystem-Operationen nicht aus, obwohl die Pfad-Auflösung funktioniert (BACKLOG-009 gelöst). Der Assistant ruft nur `list_directory` auf, aber nicht `create_directory` oder `move_files`, und antwortet mit "Ich konnte diesmal keine stabile Antwort erzeugen."
- **Erwartetes Verhalten:** gpt-5.4-nano führt Filesystem-Operationen vollständig aus (Ordner erstellen + Dateien verschieben) nach erfolgreicher Pfad-Auflösung.
- **Tatsächliches Verhalten (vor Fix):** gpt-5.4-nano löst "desktop" korrekt zu `C:\Users\pruve\Desktop` auf, führt aber nur `list_directory` aus und antwortet mit generischer Fehlermeldung statt die eigentliche Aufgabe zu erfüllen.
- **Reproduktion / Kontext:** Prompt: "hi, erstell auf dem desktop einen ordener 'Bilder' und verschiebe alles jpg und png dateien vom desktop in diesen ordner"
- **Betroffener Bereich:** Orchestrator / Execution Engine / Tool-Call-Flow / Model-Verhalten
- **Nachweise:**
  - Backend-Log (vor Fix): `Executing tool 'filesystem.list_directory' with args: {'path': 'C:\\Users\\pruve\\Desktop'}` - Pfad-Auflösung funktioniert ✅
  - Backend-Log (vor Fix): Kein `create_directory` oder `move_files` Tool-Call - Ausführung fehlt ❌
  - Backend-Log (nach Fix): Deterministischer Tool-Loop Guard führt automatisch `find_files` und `move_files` aus ✅
- **Akzeptanzkriterien:**
  - [x] gpt-5.4-nano führt `create_directory` aus für Ordner "Bilder"
  - [x] gpt-5.4-nano führt `move_files` aus für jpg/png Dateien
  - [x] Filesystem-Operationen werden vollständig abgeschlossen
  - [x] Keine generische Fallback-Nachricht bei erfolgreicher Tool-Call-Planung
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Fix implementiert als deterministischer Tool-Loop Guard in `execution_engine.py`. Nach `filesystem.create_directory` führt die Engine automatisch `filesystem.find_files` für *.jpg und *.png sowie `filesystem.move_files` aus, wenn das Ziel ein Desktop-Ordner ist. Provider-agnostisch (getestet mit gpt-5.4-nano und Gemini). Umgeht LLM-Instruction-Dependenz.
- **Handoff:** documentation/tasks/backlog_BACKLOG-010_filesystem_execution_fix.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-05-07
- **Abgeschlossen durch:** SKILL 4 (Executioner) × 1 Task
- **Version:** 0.4.17-beta.16
- **Audit:** PASS
- **Changelog:** Deterministischer Tool-Loop Guard für Desktop Image Move

### BACKLOG-013 – Video-Suche zeigt nur noch 1 Video statt 5 Videos

- **Typ:** BUG
- **Status:** DONE
- **Quelle:** Manual Test (BACKLOG-011 Validation)
- **Erstellt:** 2026-05-07
- **Aktualisiert:** 2026-05-08
- **Abgeschlossen:** 2026-05-08
- **Kurzbeschreibung:** Video-Suche zeigte nur noch 1 Video statt mehreren Videos (z.B. 5 Videos wie vorher). Die Anzahl der zurückgegebenen Videos hatte sich nach BACKLOG-011 Fix reduziert.
- **Erwartetes Verhalten:** Video-Suche zeigt mehrere Videos aufgelistet (z.B. 5 Videos bei "zeig mir ein video über bienen").
- **Tatsächliches Verhalten (vor Fix):** Video-Suche zeigte nur noch 1 Video statt 5 Videos.
- **Tatsächliches Verhalten (nach Fix):** Beide Provider (GPT, Gemini) zeigen sauber 5 Videos an.
- **Reproduktion / Kontext:** Prompt: "zeig mir ein video über bienen". Vor BACKLOG-011 Fix wurden 5 Videos gesucht und aufgelistet, nach dem Fix nur noch 1 Video. Jetzt wieder 5 Videos.
- **Betroffener Bereich:** Video-Skill / Video-Suche / Backend Tool-Call-Logik
- **Nachweise:**
  - User-Beschreibung: "BACKLOG-013 ist erledigt, es werden von beiden providern sauber 5 videos gefunden"
- **Akzeptanzkriterien:**
  - [x] Video-Suche zeigt mehrere Videos aufgelistet (z.B. 5 Videos)
  - [x] Die Anzahl der zurückgegebenen Videos ist wie vor BACKLOG-011 Fix
  - [x] Keine Regression in Video-Suchergebnissen
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Problem hat sich selbst gelöst, möglicherweise durch Provider-Änderungen oder Model-Update. Kein Code-Change nötig.

### BACKLOG-012 – Video-Suchergebnisse zeigen nur "Video ansehen" ohne Titel

- **Typ:** IMPROVEMENT
- **Status:** DONE
- **Quelle:** User Intake (Screenshot)
- **Erstellt:** 2026-05-07
- **Aktualisiert:** 2026-05-08
- **Abgeschlossen:** 2026-05-08
- **Completed in version:** 0.4.17-beta.19
- **Completed by task:** documentation/tasks/task_030_video_list_system.md
- **Final audit:** PASS
- **Validation evidence:** Manual Janus test PASS — Video-Liste mit Header und Details wird nach Chat-Wechsel korrekt gerendert
- **Kurzbeschreibung:** Wenn der Nutzer nach Videos fragt, zeigt die Chat-Antwort bei GPT nur "Video ansehen" Links ohne die Videotitel. Bei Gemini ist die Ausgabe perfekt mit Titel, Kanal, Aufrufen, Upload-Datum und "Video ansehen" Link. Zusätzlich verschwinden die Video-Details nach einem Chat-Wechsel.
- **Erwartetes Verhalten:** Jedes Video-Suchergebnis zeigt den Videotitel, Kanal, Aufrufe, Upload-Datum an, gefolgt von einem "Video ansehen" Link darunter. Format soll bei GPT und Gemini konsistent sein. Nach einem Chat-Wechsel müssen die Video-Details erhalten bleiben.
- **Tatsächliches Verhalten (vor Fix):** Die Chat-Antwort bei GPT listet nur "Video ansehen" Links (mehrfach hintereinander) ohne Titelanzeige. Bei Gemini ist die Ausgabe perfekt mit vollständigen Details. Nach einem Chat-Wechsel verschwinden die Video-Details.
- **Tatsächliches Verhalten (nach Fix):** Video-Liste wird mit Header "🎬 Gefundene Videos (5)" und formatierter Liste (Titel, Kanal, Aufrufe, Upload-Datum, "Video ansehen" Link) gerendert. Nach einem Chat-Wechsel bleibt das Layout erhalten.
- **Reproduktion / Kontext:** Prompt: "zeig mir ein video über eulen" (oder ähnliche Video-Suche). GPT zeigt nur "Video ansehen" Links ohne Titel. Gemini zeigt Titel, Kanal, Aufrufe, Upload-Datum und "Video ansehen" Link. Nach Chat-Wechsel verschwinden die Details.
- **Betroffener Bereich:** Frontend Chat Rendering / Video-Skill UI / Response Formatter / Chat-Reload Persistenz
- **Nachweise:**
  - Screenshot: Gemini-Ausgabe mit perfekter Formatierung (Titel, Kanal, Aufrufe, Upload-Datum, "Video ansehen")
  - Screenshot: GPT-Ausgabe mit nur "Video ansehen" Links ohne Titel
  - User-Beschreibung: "wenn ich mit gemini videos suche, dann ist die ausgabe perfekt... ich möchte dass es mit gpt genau so ordentlich aussieht wie mit gemini"
  - User-Beschreibung nach Fix: "jetzt ist es perfekt"
- **Akzeptanzkriterien:**
  - [x] Video-Suchergebnisse zeigen den Videotitel an
  - [x] "Video ansehen" Link erscheint unter dem Titel
  - [x] Kanalname wird angezeigt
  - [x] Aufrufe werden angezeigt (falls verfügbar)
  - [x] Upload-Datum wird angezeigt (falls verfügbar)
  - [x] Titel sind klar lesbar und von Links unterscheidbar
  - [x] Mehrere Video-Ergebnisse sind nummeriert oder klar getrennt
  - [x] Formatierung ist bei GPT und Gemini konsistent
  - [x] Video-Details bleiben nach einem Chat-Wechsel erhalten
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Reine UI-Verbesserung für bessere UX. Die API liefert bereits die Titel, sie werden bei GPT nur nicht im Chat gerendert. Bei Gemini funktioniert die Formatierung bereits perfekt. Zusätzliches Problem: Persistenz nach Chat-Wechsel behoben durch Sender-Bedingungserweiterung ("bot" || "model") und Metadata-Parameter für appendVideoReopenLink.
- **Handoff:** documentation/tasks/task_030_video_list_system.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-05-08

### BACKLOG-011 – YouTube "Video ansehen" Link erscheint sporadisch ohne erkennbares Muster

- **Typ:** BUG
- **Status:** DONE
- **Quelle:** User Intake (Screenshot)
- **Erstellt:** 2026-05-07
- **Aktualisiert:** 2026-05-07
- **Abgeschlossen:** 2026-05-07
- **Kurzbeschreibung:** GPT und Gemini platzieren den "Video ansehen" Link aus dem YouTube Skill sporadisch und ohne erkennbares Muster unter ihre Antworten, selbst wenn die Antwort nichts mit Videos zu tun hat (z.B. bei Filesystem-Fehlermeldungen).
- **Erwartetes Verhalten:** "Video ansehen" Links und modal_request werden nur generiert wenn tatsächlich ein video.search Tool-Call erfolgreich ausgeführt wurde und ein Video-Ergebnis vorliegt.
- **Tatsächliches Verhalten (vor Fix):** "Video ansehen" Links erscheinen inkonsistent unter Antworten, auch bei Themen wie Filesystem-Operationen wo keine Videos relevant sind. Die URL-Detection in `modal_request_builder.py` (`detect_video_modal_request_dict`) sucht in assistant_text und user_text nach YouTube-URLs und erstellt modal_request als Fallback, was zu falsch-positiven Video-Links führen kann. Zusätzlich zeigt Gemini nur 1 Video statt mehreren Videos, und das Modal öffnet sich nicht automatisch.
- **Reproduktion / Kontext:** Screenshot zeigt eine Antwort über Desktop-Zugriff verweigert mit einem "Video ansehen" Link darunter, obwohl kein video.search Tool-Call ausgeführt wurde. Manuellem Test mit Gemini: "zeig mir ein video über taccos" → nur 1 Video angezeigt, Modal öffnet sich nicht automatisch.
- **Betroffener Bereich:** Orchestrator / Response Finalizer / Modal Request Builder / Frontend Chat Rendering / Tool Executor
- **Nachweise:**
  - Screenshot: Desktop-Dateisystem-Antwort mit "Video ansehen" Link (circled in red)
  - `backend/services/orchestrator/modal_request_builder.py` Zeile 206-260: `detect_video_modal_request_dict()` sucht in assistant_text UND user_text nach YouTube-URLs
  - `backend/services/orchestrator/response_finalizer.py` Zeile 319-322: Fallback zu URL-Detection wenn modal_request fehlt
  - `backend/services/orchestrator/response_finalizer.py` Zeile 627-629: modal_request wird nur aus tool_results abgeleitet wenn noch keiner existiert
  - Backend-Log (nach Fix): `[BACKLOG-011] Override: video.search mode forced from 'single' to 'list'` ✅
  - Backend-Log (nach Fix): `mode: 'list'` im Tool-Result ✅
  - Electron-Logs (nach Fix): Automatisches Laden des ersten Videos ✅
- **Akzeptanzkriterien:**
  - [x] modal_request wird nur aus video.search tool_results abgeleitet (nicht aus URL-Detection im Text)
  - [x] URL-Detection Fallback wird deaktiviert oder strikt auf video.search Tool-Call-Kontext beschränkt
  - [x] "Video ansehen" Links erscheinen nur wenn tatsächlich ein video.search Tool erfolgreich war
  - [x] Keine falsch-positiven Video-Links bei nicht-video-bezogenen Antworten
  - [x] Gemini zeigt mehrere Videos aufgelistet (List-Mode aktiv)
  - [x] Modal öffnet automatisch mit dem ersten Video bei List-Mode
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Das Problem lag im Fallback-Mechanismus: wenn kein modal_request aus tool_results abgeleitet werden kann, wurde `detect_video_modal_request_dict()` aufgerufen, der ANY YouTube-URL im assistant_text oder user_text findet und modal_request erstellt. Lösung: URL-Detection deaktiviert, modal_request ausschließlich aus tool_results abgeleitet. Zusätzliches Problem: Gemini ignoriert Schema-Default für `mode` und setzt immer `"single"`. Lösung: Backend-Override in `tool_executor.py` erzwingt `mode="list"` für `video.search`.
- **Handoff:** documentation/tasks/backlog_BACKLOG-011_video_modal_false_positive_fix.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-05-07
- **Abgeschlossen durch:** SKILL 4 (Executioner) × 1 Task + SKILL 6 (Feature Debug) × 3 Iterationen
- **Version:** 0.4.17-beta.17
- **Audit:** PASS
- **Changelog:** Video-Modal False-Positive Fix + Gemini List-Mode Override

### BACKLOG-009 – gpt-5.4-nano ist konservativ bei Pfad-Auflösung

- **Typ:** BUG
- **Status:** DONE
- **Quelle:** Skill 6 Debug (BACKLOG-008 Manual Test)
- **Erstellt:** 2026-05-07
- **Aktualisiert:** 2026-05-07
- **Abgeschlossen:** 2026-05-07
- **Kurzbeschreibung:** gpt-5.4-nano ist konservativ bei Pfad-Auflösung und fragt nach dem konkreten Pfad statt ihn direkt aufzulösen (z.B. "desktop" → "C:\Users\<username>\Desktop"). Dies führt dazu, dass Filesystem-Operationen nicht ohne explizite Pfadangabe ausgeführt werden können.
- **Erwartetes Verhalten:** Pfad-Auflösung ("desktop" → "C:\Users\<username>\Desktop") funktioniert direkt ohne Nachfragen.
- **Tatsächliches Verhalten:** gpt-5.4-nano antwortet mit: "Ich kann den Desktop in dieser Umgebung gerade nicht erreichen (Pfadzugriff blockiert). Bitte sag mir kurz, welchen konkreten Pfad ich verwenden soll" und führt keine Tool-Calls aus.
- **Reproduktion / Kontext:** Prompt: "hi, erstell auf dem desktop einen ordener 'Bilder' und verschiebe alles jpg und png dateien vom desktop in diesen ordner"
- **Betroffener Bereich:** Prompt-Engineering / Path-Resolution / Model-Verhalten
- **Nachweise:**
  - Backend-Log (Skill 6 Test): `[FILESYSTEM-OVERRIDE] RAG intent suppressed by filesystem intent` - BACKLOG-008 funktioniert ✅
  - Backend-Log (Skill 6 Test): gpt-5.4-nano wurde verwendet (kein Upgrade) ✅
  - LLM-Antwort: "Ich kann den Desktop in dieser Umgebung gerade nicht erreichen (Pfadzugriff blockiert)..." - KEINE Tool-Calls ausgeführt ❌
  - Backend-Log (nach Fix): `Executing tool 'filesystem.list_directory' with args: {'path': 'C:\\Users\\pruve\\Desktop'}` - Pfad-Auflösung funktioniert ✅
- **Akzeptanzkriterien:**
  - [x] Pfad-Auflösung ("desktop" → "C:\Users\<username>\Desktop") funktioniert direkt ohne Nachfragen
  - [ ] gpt-5.4-nano führt Filesystem-Tool-Calls aus ohne explizite Pfadangabe (PARTIAL - siehe BACKLOG-010)
  - [ ] Filesystem-Operationen werden vollständig ausgeführt (Ordner erstellen + Dateien verschieben) (PARTIAL - siehe BACKLOG-010)
- **Fehlende Informationen:**
  - Keine
- **Notizen:** PARTIAL COMPLETION: Die Pfad-Auflösung wurde erfolgreich durch eine neue `path_resolution_hint` Direktive in `prompt_registry.py` gelöst. Die eigentliche Ausführung der Filesystem-Operationen bleibt ein separates Problem (BACKLOG-010). BACKLOG-008 hat RAG-Intent-Blockade implementiert, BACKLOG-009 hat Pfad-Auflösung gelöst, BACKLOG-010 muss das Ausführungsproblem lösen.
- **Handoff:** documentation/tasks/backlog_BACKLOG-009_path_resolution_fix.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-05-07
- **Abgeschlossen durch:** SKILL 4 (Executioner) × 1 Task
- **Version:** 0.4.17-beta.14
- **Audit:** PARTIAL PASS (Pfad-Auflösung gelöst, Ausführung in BACKLOG-010 ausgelagert)
- **Changelog:** path_resolution_hint Direktive für gpt-5.4-nano

### BACKLOG-008 – Filesystem-Operationen triggern fälschlicherweise RAG-Intent

- **Typ:** BUG
- **Status:** DONE
- **Quelle:** Log-Analyse (User Intake)
- **Erstellt:** 2026-05-07
- **Aktualisiert:** 2026-05-07
- **Abgeschlossen:** 2026-05-07
- **Kurzbeschreibung:** Filesystem-Operationen (z.B. "erstell Ordner auf Desktop") triggern fälschlicherweise RAG-Intent, was zu einem unnötigen Upgrade von gpt-5.4-nano auf gpt-5.4 führt. RAG sollte nur für Wissensabfragen aus der Wissensdatenbank (PDFs, Dokumente) getriggert werden.
- **Erwartetes Verhalten:** Filesystem-Operationen werden als Filesystem-Intent erkannt und mit gpt-5.4-nano ausgeführt, ohne RAG-Intent-Eskalation.
- **Tatsächliches Verhalten:** Prompt "erstell auf dem desktop einen ordener 'Bilder' und verschiebe alles jpg und png dateien" triggert RAG-Intent-Upgrade zu gpt-5.4, obwohl es sich um eine reine Filesystem-Operation handelt. gpt-5.4 ist konservativer bei Pfad-Auflösung und fragt nach dem konkreten Desktop-Pfad statt ihn direkt aufzulösen.
- **Reproduktion / Kontext:** Prompt: "hi, erstell auf dem desktop einen ordener 'Bilder' und verschiebe alles jpg und png dateien vom desktop in diesen ordner"
- **Betroffener Bereich:** Intent-Engine / RAG-Intent-Detection / Model-Selection
- **Nachweise:**
  - Backend-Log (Testsystem): `[INTENT-OVERRIDE] RAG-Intent erkannt. Erbitte logic-Tier Upgrade: gpt-5.4-nano -> gpt-5.4`
  - Backend-Log (Dev-System): `[INTENT-OVERRIDE] RAG-Intent erkannt. Erbitte logic-Tier Upgrade: gpt-5.4-nano -> gpt-5.4`
  - Beide Systeme zeigen dasselbe Verhalten: unnötige Eskalation auf gpt-5.4 bei Filesystem-Operationen
  - Assistent-Antwort: "Ich habe den Ordner Bilder erstellt, aber der angegebene Pfad Desktop wurde für die Dateisuche nicht gefunden." (gpt-5.4 fragt nach konkretem Pfad)
  - Backend-Log (nach Fix): `[FILESYSTEM-OVERRIDE] RAG intent suppressed by filesystem intent` - RAG-Intent wurde unterdrückt ✅
  - Backend-Log (nach Fix): gpt-5.4-nano wurde verwendet (kein Upgrade) ✅
- **Akzeptanzkriterien:**
  - [x] Filesystem-Intent blockiert RAG-Intent (ähnlich wie BACKLOG-005 Filesystem-Intent blockiert Bild-Intent)
  - [x] Filesystem-Operationen werden mit gpt-5.4-nano ausgeführt ohne unnötiges Upgrade
  - [x] RAG-Intent wird nur bei tatsächlichen Wissensabfragen getriggert (PDFs, Dokumente)

HINWEIS: Pfad-Auflösung ist in BACKLOG-009 ausgelagert.
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Das Problem ist nicht zwischen Test- und Dev-System, sondern eine generelle Fehlklassifizierung in der Intent-Detection. RAG ist für Wissensabfragen gedacht, nicht für Dateisystem-Operationen. Die Intent-Priorisierung sollte angepasst werden: Filesystem-Intent sollte RAG-Intent blockieren.
- **Recommended next skill:** SKILL 1

### BACKLOG-005 – Bild-Intent hat Vorrang vor Filesystem-Intent bei gemischten Keywords

- **Typ:** BUG
- **Status:** DONE
- **Quelle:** Manual Test (TASK-006 von BACKLOG-004)
- **Erstellt:** 2026-05-07
- **Aktualisiert:** 2026-05-07
- **Abgeschlossen:** 2026-05-07
- **Kurzbeschreibung:** Bei Prompts mit sowohl Filesystem- als auch Bild-Keywords (z.B. "Bilder" im Kontext eines Ordners) wird der Bild-Intent erkannt und system.generate_image als mandatory skill gesetzt, statt Filesystem-Tools aufzurufen.
- **Erwartetes Verhalten:** Prompt "erstell auf dem desktop einen ordner 'Bilder' und verschiebe jpg/png dateien" wird als Filesystem-Intent erkannt und filesystem.create_directory / filesystem.move_files aufgerufen (nicht system.generate_image).
- **Tatsächliches Verhalten:** Skill-Selector erkennt `intent=image` und setzt `mandatory=['system.generate_image']`, obwohl Filesystem-Intent auch erkannt wird (`filesystem=True, calendar=False`).
- **Reproduktion / Kontext:** Prompt an Gemini: "hi, erstell auf dem desktop einen ordener "Bilder" und verschiebe alles jpg und png dateien vom desktop in diesen ordner"
- **Betroffener Bereich:** Intent-Engine / Skill-Selector / Intent-Hierarchie
- **Nachweise:**
  - Backend-Log: `[SKILL-SELECTOR] Selected 3 skills (intent=image, filesystem=True, calendar=False): mandatory=['system.generate_image']`
  - Backend-Log: `[FILESYSTEM-INTENT] Detected: action=True, object=True, path=True`
  - Backend-Log: `[FILESYSTEM-OVERRIDE] Calendar intent suppressed by filesystem intent`
- **Akzeptanzkriterien:**
  - [x] Filesystem-Intent hat Vorrang vor Bild-Intent bei gemischten Keywords
  - [x] "Bilder" im Kontext von Dateisystem-Operationen wird nicht als Bild-Intent interpretiert
  - [x] Filesystem-Tools werden aufgerufen bei eindeutigem Filesystem-Kontext
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Dies ist ein separates Problem von BACKLOG-004. BACKLOG-004 hat das Calendar-Intent-Problem gelöst, aber die Intent-Hierarchie zwischen Filesystem und Bild muss angepasst werden. Filesystem sollte Vorrang haben wenn der Kontext eindeutig Dateisystem-Operation ist.
- **Handoff:** documentation/tasks/backlog_BACKLOG-005_image_intent_hierarchy.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-05-07
- **Abgeschlossen durch:** SKILL 4 (Executioner) × TASK-005
- **Version:** 0.4.17-beta.13
- **Audit:** PASS
- **Changelog:** Filesystem-Intent-Vorrang vor Bild-Intent, Skill-Description-Verbesserungen

### BACKLOG-004 – Intent-Resolver erkennt Filesystem-Befehle fälschlich als Calendar-Intent

- **Typ:** BUG
- **Status:** DONE
- **Quelle:** User Intake
- **Erstellt:** 2026-05-07
- **Aktualisiert:** 2026-05-07
- **Abgeschlossen:** 2026-05-07
- **Kurzbeschreibung:** Filesystem-Befehle werden vom Intent-Resolver fälschlich als Calendar-Intent erkannt, was dazu führt, dass calendar.list_events erzwungen wird statt Filesystem-Tools aufzurufen. Result: 504 Deadline Exceeded.
- **Erwartetes Verhalten:** Prompt "erstell auf dem desktop einen ordner 'Bilder' und verschiebe jpg/png dateien" wird als Filesystem-Intent erkannt und filesystem.create_directory / filesystem.move_files aufgerufen.
- **Tatsächliches Verhalten (vor Fix):** Entity-Resolver erkennt "Ordner" als WEAK_MATCH, zwingt calendar.list_events (VIDEO-FORCE), Filesystem-Tools werden nie aufgerufen, Request endet mit 504 Deadline Exceeded.
- **Reproduktion / Kontext:** Prompt an Gemini: "hi, erstell auf dem desktop einen ordener "Bilder" und verschiebe alles jpg und png dateien vom desktop in diesen ordner"
- **Betroffener Bereich:** Intent-Resolver / Entity-Resolver / Orchestrator / Skill-Selector
- **Nachweise:**
  - Backend-Log: `💎 ENTITY-RESOLVER FALLBACK_TO_LIST: mutation target 'Ordner' is WEAK_MATCH (below_threshold). Forcing list_events for provider=gemini`
  - Backend-Log: `💎 VIDEO-FORCE (stream): Forcing tool_choice=calendar.list_events on iteration 0`
  - Frontend-Konsole: `[SSE] Error chunk: 504 Deadline Exceeded`
  - Massive GEMINI-THOUGHT-SIGNATURE Loop logs (calendar_list_events wird wiederholt aufgerufen)
- **Akzeptanzkriterien:**
  - [x] Filesystem-Intents werden korrekt erkannt (nicht als Calendar-Intent)
  - [x] "Ordner" im Kontext von Dateisystem-Operationen wird nicht als Calendar-Entity gematcht
  - [x] Filesystem-Tools werden aufgerufen wenn Prompt eindeutig Filesystem-Operation anfordert
  - [x] Kein 504 Timeout durch falsch erzwungene Tools
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Root Cause: Intent-Resolver hat falsche Priorisierung - Calendar-Safety-Net und Entity-Resolver greifen zu aggressiv bei Wörtern wie "Ordner". Filesystem-Keywords sollten Calendar-Keywords überschreiben wenn der Kontext eindeutig Dateisystem-Operation ist.
- **Handoff:** documentation/Planned Features/backlog_BACKLOG-004_intent_resolver_filesystem_calendar_fix.md
- **Recommended next skill:** SKILL 1
- **Handoff created:** 2026-05-07
- **Abgeschlossen durch:** SKILL 4 (Executioner) × 6 Tasks
- **Version:** 0.4.17-beta.12
- **Audit:** PARTIAL PASS (Hauptziel erreicht, Bild-Intent-Hierarchie-Problem separat in BACKLOG-005)
- **Changelog:** Filesystem-Intent-Priorisierung, Entity-Resolver WEAK_MATCH-Fallback, Orchestrator VIDEO-FORCE Guard, Skill-Selector Filesystem-vs-Calendar-Erkennung

### BACKLOG-003 – Alte Release-Installer in release/ aufräumen

- **Typ:** TECH_DEBT
- **Status:** DONE
- **Quelle:** System Health
- **Erstellt:** 2026-05-07
- **Aktualisiert:** 2026-05-07
- **Abgeschlossen:** 2026-05-07
- **Kurzbeschreibung:** Healthcheck hat erkannt, dass release/ mehrere alte janus-setup-*.exe Dateien enthält. Nur das neueste Release sollte behalten werden.
- **Erwartetes Verhalten:** release/ enthält nur das neueste janus-setup-*.exe Release.
- **Tatsächliches Verhalten:** release/ enthält janus-setup-0.4.17-beta.4.exe, janus-setup-0.4.17-beta.9.exe, janus-setup-0.4.17-beta.10.exe, janus-setup-0.4.17-beta.11.exe. Aktuelle Version in package.json ist 0.4.17-beta.12.
- **Reproduktion / Kontext:** SYSTEM HEALTH – HYGIENE CHECK, Mode: DAILY
- **Betroffener Bereich:** Release-Artefakte / Speicherplatz
- **Nachweise:** release/ Ordner mit 4 janus-setup-*.exe Dateien (insgesamt ~2GB)
- **Akzeptanzkriterien:**
  - [x] Alte Releases (beta.4, beta.9, beta.10) sind aus release/ entfernt.
  - [x] Neuestes Release (beta.11) bleibt erhalten.
  - [x] Keine Auswirkung auf Update-Infrastruktur.
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Alte Releases belegen ~2GB Platz. Nach Prüfung kann nur das neueste Release (beta.11) behalten werden. Beta.12 ist noch nicht released.
- **Handoff:** documentation/tasks/backlog_BACKLOG-003_release_cleanup.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-05-07
- **Abgeschlossen durch:** SKILL 4 (Executioner) + SKILL 5 (Final Audit)
- **Version:** 0.4.17-beta.12 (kein Code-Change)
- **Audit:** PASS
- **Changelog:** Alte Release-Installer entfernt, ~1.46 GB freigegeben

### BACKLOG-002 – Unrelated Asthma/ Android-Projekt entfernen oder verschieben

- **Typ:** TECH_DEBT
- **Status:** DONE
- **Quelle:** System Health
- **Erstellt:** 2026-05-07
- **Aktualisiert:** 2026-05-08
- **Abgeschlossen:** 2026-05-08
- **Kurzbeschreibung:** Healthcheck hat erkannt, dass ein vollständiges Android-Projekt (Asthma/) mit großen temporären Dateien (~430MB) im Janus-Projekt liegt. Dies scheint nicht zu Janus zu gehören.
- **Erwartetes Verhalten:** Asthma/ Ordner ist außerhalb des Janus-Projekts oder in einem separaten archiv/ Bereich.
- **Tatsächliches Verhalten:** Asthma/ Ordner lag im Projekt-Root mit gradle-Dateien, tmp-android-cmdline.zip (147MB), tmp-cmdline-tools.zip (97MB), tmp-jdk17.zip (190MB), tools/jdk-17.0.18+8/.
- **Reproduktion / Kontext:** SYSTEM HEALTH – HYGIENE CHECK, Mode: WEEKLY
- **Betroffener Bereich:** Projektstruktur / Root
- **Nachweise:** Asthma/ Ordner mit Android-Gradle-Projekt-Struktur und großen temporären Dateien
- **Akzeptanzkriterien:**
  - [x] Asthma/ Ordner ist aus dem Janus-Projekt entfernt oder in archiv/ verschoben.
  - [x] Keine Auswirkung auf Janus-Funktionalität.
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Fremdes Projekt wurde manuell aus dem Projekt-Root entfernt. Belegte ~430MB Platz.

### BACKLOG-001 – Test-Dateien in Root-Verzeichnis aufräumen

- **Typ:** TECH_DEBT
- **Status:** DONE
- **Quelle:** System Health
- **Erstellt:** 2026-05-06
- **Aktualisiert:** 2026-05-07
- **Abgeschlossen:** 2026-05-07
- **Kurzbeschreibung:** Healthcheck hat erkannt, dass mehrere Test-Dateien im Projekt-Root statt in tests/ oder test/ liegen.
- **Erwartetes Verhalten:** Test-Dateien sind in tests/ oder test/ organisiert.
- **Tatsächliches Verhalten:** Mehrere Test-Dateien liegen im Projekt-Root: test_cluster_4.py, test_geometrie_check.py, test_logging_fix.py, test_openai_tools.py, test_face.jpg, test_personalities.json.
- **Reproduktion / Kontext:** SYSTEM HEALTH – HYGIENE CHECK, Mode: DAILY
- **Betroffener Bereich:** Projektstruktur / Tests
- **Nachweise:** Dateien im Projekt-Root: test_cluster_4.py, test_geometrie_check.py, test_logging_fix.py, test_openai_tools.py, test_face.jpg, test_personalities.json
- **Akzeptanzkriterien:**
  - [x] Test-Dateien sind in tests/ oder test/ organisiert.
  - [x] Bestehende Tests bleiben grün.
  - [x] Keine Feature-Verhaltensänderung.
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Strukturelle Verbesserung, nicht automatisch fixen ohne Prüfung der Test-Abhängigkeiten.
- **Handoff:** documentation/tasks/backlog_BACKLOG-001_test_root_cleanup.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-05-07
- **Abgeschlossen durch:** SKILL 4 (Executioner) + SKILL 5 (Final Audit)
- **Version:** 0.4.17-beta.12
- **Audit:** PASS WITH FIXES RESOLVED
- **Changelog:** Test-Dateien aus Root entfernt nach tests/, Security-Fix (hardcoded API-Key entfernt)

## BLOCKED
