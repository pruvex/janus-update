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
