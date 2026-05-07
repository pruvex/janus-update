# Janus Backlog

Dieses Backlog sammelt Bugs, Änderungswünsche, kleine Ergänzungen, Verbesserungen und technische Schulden, bevor sie in die Diamond-Skill-Pipeline übergeben werden.

Healthcheck-Findings aus `SYSTEM HEALTH – HYGIENE CHECK` dürfen hier als `Quelle: System Health` aufgenommen werden, wenn sie nicht sicher mechanisch auto-fixbar sind.

## Status-Regeln

- **NEEDS INFO:** Pflichtinformationen fehlen.
- **READY:** Ausreichend beschrieben für `BACKLOG SKILL 2 – REVIEW PRIORISIERUNG`.
- **IN PROGRESS:** Durch `BACKLOG SKILL 3 – EXECUTION HANDOFF` an die Diamond-Pipeline übergeben.
- **DONE:** Durch `SKILL 7 – DOKUMENTATIONSUPDATE` nach erfolgreicher Umsetzung abgeschlossen.
- **BLOCKED:** Nicht umsetzbar ohne externe Entscheidung oder Abhängigkeit.

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
- **Recommended next skill:** SKILL 1

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
- **Recommended next skill:** SKILL 1

### BACKLOG-005 – Bild-Intent hat Vorrang vor Filesystem-Intent bei gemischten Keywords

- **Typ:** BUG
- **Status:** IN PROGRESS
- **Quelle:** Manual Test (TASK-006 von BACKLOG-004)
- **Erstellt:** 2026-05-07
- **Aktualisiert:** 2026-05-07
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
  - [ ] Filesystem-Intent hat Vorrang vor Bild-Intent bei gemischten Keywords
  - [ ] "Bilder" im Kontext von Dateisystem-Operationen wird nicht als Bild-Intent interpretiert
  - [ ] Filesystem-Tools werden aufgerufen bei eindeutigem Filesystem-Kontext
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Dies ist ein separates Problem von BACKLOG-004. BACKLOG-004 hat das Calendar-Intent-Problem gelöst, aber die Intent-Hierarchie zwischen Filesystem und Bild muss angepasst werden. Filesystem sollte Vorrang haben wenn der Kontext eindeutig Dateisystem-Operation ist.
- **Handoff:** documentation/tasks/backlog_BACKLOG-005_image_intent_hierarchy.md
- **Recommended next skill:** SKILL 3
- **Handoff created:** 2026-05-07

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

## IN PROGRESS

## DONE

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

## READY

### BACKLOG-002 – Unrelated Asthma/ Android-Projekt entfernen oder verschieben

- **Typ:** TECH_DEBT
- **Status:** READY
- **Quelle:** System Health
- **Erstellt:** 2026-05-07
- **Aktualisiert:** 2026-05-07
- **Kurzbeschreibung:** Healthcheck hat erkannt, dass ein vollständiges Android-Projekt (Asthma/) mit großen temporären Dateien (~430MB) im Janus-Projekt liegt. Dies scheint nicht zu Janus zu gehören.
- **Erwartetes Verhalten:** Asthma/ Ordner ist außerhalb des Janus-Projekts oder in einem separaten archiv/ Bereich.
- **Tatsächliches Verhalten:** Asthma/ Ordner liegt im Projekt-Root mit gradle-Dateien, tmp-android-cmdline.zip (147MB), tmp-cmdline-tools.zip (97MB), tmp-jdk17.zip (190MB), tools/jdk-17.0.18+8/.
- **Reproduktion / Kontext:** SYSTEM HEALTH – HYGIENE CHECK, Mode: WEEKLY
- **Betroffener Bereich:** Projektstruktur / Root
- **Nachweise:** Asthma/ Ordner mit Android-Gradle-Projekt-Struktur und großen temporären Dateien
- **Akzeptanzkriterien:**
  - [ ] Asthma/ Ordner ist aus dem Janus-Projekt entfernt oder in archiv/ verschoben.
  - [ ] Keine Auswirkung auf Janus-Funktionalität.
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Fremdes Projekt belegt ~430MB Platz. Sollte mit Nutzer geklärt werden ob benötigt oder gelöscht werden kann.

## DONE

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
