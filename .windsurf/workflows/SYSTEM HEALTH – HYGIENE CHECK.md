---
description: SYSTEM HEALTH – Hygiene Check | Model: SWE 1.6 | Escalation: GPT-5.5 if required | Modes: DAILY/WEEKLY/MONTHLY
---

# SYSTEM HEALTH – HYGIENE CHECK

**Required Model:** SWE 1.6  
**Escalation Model:** GPT-5.5  
**Modes:** DAILY | WEEKLY | MONTHLY  
**Purpose:** Prüft Ordnung, Struktur und technische Hygiene der Codebase, führt nur sichere mechanische Fixes nach Freigabe aus und schreibt größere Findings ins Backlog.  
**Do not use this skill for:** Feature-Implementation, große Refactors, Architekturumbauten, Release, Version-Bump oder kreative Produktverbesserungen.

---

## Zweck

Dieser Skill beantwortet:

```text
Ist mein System noch sauber, strukturiert und gesund?
```

Er kümmert sich um:

- Ordnung
- Struktur
- technische Qualität
- Hygiene-Findings
- sichere mechanische Korrekturen
- Backlog-Einträge für größere oder riskante Themen

Er ist kein Feature-, Bugfix-, Release- oder Refactor-Ausführungsskill.

---

## Mode Selection Gate

Wenn der Nutzer einen Modus nennt oder eindeutig andeutet, normalisiere ihn ohne Rückfrage:

- `1`, `DAILY`, `dayly`, `daily`, `kurz`, `schnell`, `start`, `tagescheck` -> `DAILY`
- `2`, `WEEKLY`, `weekly`, `woechentlich`, `wöchentlich`, `weekly check`, `montag` -> `WEEKLY`
- `3`, `MONTHLY`, `monthly`, `monatlich`, `monatscheck`, `1. des monats` -> `MONTHLY`

Wenn der Nutzer nur allgemein "Healthcheck", "Hygiene Check", "schau ob alles sauber ist" oder ähnlich sagt und keinen Zeitraum nennt, nutze `DAILY` als Default und schreibe im Report:

```text
Modus automatisch gewählt: DAILY (kurzer Hygiene-Check, weil kein Zeitraum genannt wurde).
```

Wenn der Nutzer nach dem passenden Modus fragt oder mehrere Modi gleichzeitig andeutet, stoppe und frage:

```markdown
# SYSTEM HEALTH MODE REQUIRED

Welchen Healthcheck möchtest du ausführen?

1) DAILY – Start-of-Day Hygiene Check, täglich zu Arbeitsbeginn
2) WEEKLY – Weekly Structure Check, empfohlen montags
3) MONTHLY – Monthly Architecture Hygiene Check, empfohlen am 1. des Monats

Antworte mit: 1, 2, 3, DAILY, WEEKLY oder MONTHLY.
```

Keine Prüfung ausführen, wenn der Modus nach diesen Regeln weiterhin unklar ist.

Akzeptierte Eingaben:

```text
1 | DAILY | dayly | daily | kurz | schnell | start | tagescheck
2 | WEEKLY | weekly | woechentlich | wöchentlich | weekly check | montag
3 | MONTHLY | monthly | monatlich | monatscheck
```

Normalisiere `dayly` zu `DAILY`.

---

## Modi

### 1) DAILY – Start-of-Day Hygiene Check

Zweck:
- sauberer Start in den Arbeitstag
- schnelle Hygiene-Prüfung
- keine tiefen Architekturentscheidungen

Prüfe:
- Workflow-Ordner enthält nur echte Slash-Skills.
- `documentation/backlog/BACKLOG.md` existiert und hat die Standardabschnitte.
- Offene `IN PROGRESS` Backlog-Items sind sichtbar.
- Offensichtliche temporäre, leere oder falsch abgelegte Dateien sind erkennbar.
- Es gibt keine offensichtlichen doppelten Runbook-/Workflow-Artefakte.
- Es gibt keine klar kaputten Hygiene-Artefakte, die den Tagesstart stören.

Auto-Fix-Policy:
- Nur sichere, mechanische, lokale und reversible Fixes vorschlagen.
- Auto-Fixes nur nach expliziter Nutzerfreigabe ausführen.
- Ohne Freigabe nur reporten.
- Keine Backlog-Items schreiben. DAILY darf Backlog-Kandidaten nur vorschlagen und auf WEEKLY/MONTHLY verweisen.

Output-Policy:
- DAILY nutzt standardmäßig `Compact Output`.
- Wenn Auto-Fix-Kandidaten, Backlog-Kandidaten oder Eskalationen gefunden werden, muss DAILY zusätzlich die passenden Gate-/Freigabe-Sektionen aus dem Vollformat ausgeben.
- Wenn keine Findings gefunden werden, reicht der kompakte Report mit Ampel, Empfehlung und Scan-Abdeckung.

### 2) WEEKLY – Weekly Structure Check

Zweck:
- wöchentliche Strukturprüfung
- technische Schulden und Refactor-Kandidaten erkennen
- größere Findings ins Backlog schreiben

Prüfe zusätzlich zu DAILY:
- große Dateien und ungewöhnliches Wachstum
- Ordnerdrift oder falsch abgelegte Dateien
- verwaiste Doku-/Task-/Runbook-Artefakte
- Test-/Doku-Konsistenz auf offensichtlicher Ebene
- wiederkehrende Hygiene-Probleme
- Backlog-Gesundheit: viele `NEEDS INFO`, alte `IN PROGRESS`, blockierte Items

Auto-Fix-Policy:
- Kleine sichere Fixes nur nach Freigabe.
- Riskante oder größere Themen immer ins Backlog.

Performance-Budget:
- Weekly darf gründlicher als DAILY sein, muss aber interaktiv bleiben.
- Zielzeit: ca. 1-3 Minuten.
- Wenn ein Scan zu lange dauert, Ergebnis zusammenfassen und mit Fallback weitermachen.
- Keine vollständige Tiefenanalyse jeder Datei durchführen.
- Große Trefferlisten auf Top-N begrenzen.

### 3) MONTHLY – Monthly Architecture Hygiene Check

Zweck:
- tiefer Architektur- und Wartbarkeitscheck
- langfristige Risiken erkennen
- größere Verbesserungen in das Backlog überführen

Prüfe zusätzlich zu WEEKLY:
- Modulgrenzen und Verantwortlichkeiten
- zentrale Services mit zu vielen Verantwortlichkeiten
- potenzielle Architekturdrift
- riskante Kopplungen
- große Refactor-Kandidaten
- langfristige Wartbarkeitsrisiken

Auto-Fix-Policy:
- Keine großen Auto-Fixes.
- Architektur- oder Refactor-Findings ins Backlog oder, bei Unklarheit, Eskalation zu GPT-5.5.

Performance-Budget:
- Monthly darf länger dauern als WEEKLY, soll aber ebenfalls bounded bleiben.
- Zielzeit: ca. 3-8 Minuten.
- Architektur-Findings stichprobenartig und risikoorientiert prüfen, nicht jede Datei vollständig lesen.

---

## Scan Performance & Robustness Rules

Alle Modi müssen Scans begrenzen und robuste Fallbacks verwenden.

### Encoding / PowerShell Hinweis

Diese Workflow-Datei ist UTF-8. Wenn PowerShell Umlaute oder Gedankenstriche als Mojibake anzeigt (`PrÃ¼ft`, `GRÃœN`, `â€“`), ist das ein Anzeige-/Encoding-Problem des Lesebefehls, kein inhaltlicher Skill-Fehler.

- Bevorzuge beim Lesen in PowerShell: `Get-Content -Encoding UTF8`.
- Keine Massen-Rewrites nur zur Encoding-Kosmetik durchführen.
- Wenn ein echter Encoding-Fix nötig ist, nur die betroffene Datei gezielt und nach Snapshot/Freigabe umkodieren.

### Excludes für Datei-Scans

Bei rekursiven Scans standardmäßig ausschließen:

```text
.git/
node_modules/
backend/venv/
venv/
.pytest_cache/
.ruff_cache/
playwright-report/
test-results/
__pycache__/
dist/
build/
.vercel/
```

### Top-N-Regel

- Große Dateien: maximal Top 20 anzeigen.
- Root-Hygiene-Findings: maximal Top 20 anzeigen.
- Doku-/Task-Drift: maximal Top 20 auffällige Artefakte anzeigen.
- Bei mehr Treffern: Anzahl nennen und repräsentative Beispiele geben.

### PowerShell Robustness

Wenn PowerShell genutzt wird:

- Keine komplexen Einzeiler verwenden, wenn Quoting mit `$_` riskant ist.
- Bevorzuge einfache, robuste Befehle oder Python-Fallbacks.
- Wenn ein Befehl mit Quoting-/Parserfehler fehlschlägt, nicht wiederholt denselben Befehl ausführen.
- Stattdessen Fallback verwenden und den Fehler im Report kurz erwähnen.

Robuster Fallback für große Dateien:

```text
python -c "from pathlib import Path; ex={'.git','node_modules','venv','.pytest_cache','.ruff_cache','playwright-report','test-results','__pycache__','dist','build','.vercel'}; root=Path('.'); files=[]; [files.append((p.stat().st_size,str(p))) for p in root.rglob('*') if p.is_file() and not any(part in ex for part in p.parts) and p.stat().st_size>500*1024]; print('\\n'.join(f'{s}\\t{p}' for s,p in sorted(files, reverse=True)[:20]))"
```

### Timebox-Regel

- Wenn ein einzelner Scan länger als ca. 60 Sekunden dauert, abbrechen oder Ergebnis als unvollständig markieren.
- Nie mehrfach denselben fehlerhaften Scan wiederholen.
- Bei unvollständigem Scan:
  - kein BLOCKED ausgeben, außer Pflichtartefakte fehlen
  - im Report unter `Hinweise zur Scan-Abdeckung` nennen
  - konservativ keine riskanten Auto-Fixes vorschlagen

### Auto-Fix nach unvollständigem Scan

Wenn relevante Scans unvollständig waren:

- Keine nicht-trivialen Auto-Fixes empfehlen.
- Nur leere Dateien/Ordner oder eindeutig temporäre Dateien mit `Risk: LOW` anbieten.
- Bei unklaren Artefakten Backlog oder Ignore statt Auto-Fix wählen.

---

## Hard Rules

- Keine großen Refactors selbst machen.
- Keine Architektur umbauen.
- Keine Features anfassen.
- Keine Bugfix-Implementation durchführen.
- Keine kreativen Verbesserungen vornehmen.
- Keine riskanten Deletes.
- Keine Dependency-Upgrades.
- Kein Release.
- Keine Änderungen an produktivem Verhalten.
- Keine Änderungen an User-Arbeit ohne explizite Freigabe.
- Keine spekulativen Backlog-Einträge ohne konkreten Finding-Grund.
- Keine stillen Backlog-Mutationen während einer Auto-Fix-Freigabephase.
- Bei Unsicherheit stoppen und GPT-5.5-Eskalation ausgeben.
- Der Abschlussbericht muss vollständig auf Deutsch sein, außer technischen Dateipfaden, Skill-Namen, Status-Tokens und Modellnamen.
- Der Abschlussbericht muss immer eine eindeutige operative Empfehlung enthalten.
- Weiche Empfehlungen wie "if desired", "bei Bedarf" oder "optional" dürfen nicht die Hauptempfehlung sein; optionale Punkte gehören in "Optionale Folgeaktion".

---

## Systemhealth Ampel & Handlungsempfehlung

Der Healthcheck muss am Ende eine klare Ampelbewertung mit Prozentwert ausgeben:

```text
Systemhealth: <0-100>% – GRÜN | GELB | ROT
```

Bewertung:

- **GRÜN (90-100%):** Keine Blocker, keine Escalations, keine Backlog-Pflicht, höchstens ignorierte oder rein optionale Hygiene-Hinweise.
- **GELB (70-89%):** System ist nutzbar, aber es gibt nicht-blockierende Hygiene-Findings, Auto-Fix-Kandidaten oder kleinere Strukturdrift.
- **ROT (0-69%):** Blocker, Escalations, riskante Inkonsistenzen, fehlende Kernartefakte oder Findings, die aktuelles Arbeiten stoppen sollten.

Deterministische Richtwerte:

- Startwert: 100%.
- Pro nicht-blockierendem Auto-Fix-Kandidaten: -5 bis -10 Punkte.
- Pro Backlog-Item: -10 bis -15 Punkte.
- Pro Escalation: -25 Punkte.
- Sobald mindestens ein Auto-Fix-Kandidat vorhanden ist, ist `GRÜN` nur erlaubt, wenn keine sonstigen Hygiene-Findings, keine Backlog-Änderung und keine uncommitted changes vorliegen; sonst maximal `GELB` und maximal `89%`.
- Sobald ein Backlog-Item erstellt oder aktualisiert wurde, ist die Bewertung maximal `GELB` und maximal `89%`, außer das Item ist rein dokumentarisch und kein Struktur-/Wartungsfinding.
- Sobald `Workspace-Status: uncommitted changes vorhanden` zusammen mit Auto-Fix-Kandidaten vorkommt, ist die Bewertung maximal `GELB` und maximal `89%`.
- Bei blockierendem Finding: maximal 69%.
- Bei unlesbaren Pflichtartefakten: maximal 69%.
- Wenn die Pflichtsektion `## Auto-Fix-Gate-Prüfung` bei vorhandenen Auto-Fix-Kandidaten fehlt, ist die Auto-Fix-Freigabe `BLOCKED – Report inkonsistent`, die Bewertung maximal `GELB` und der Score maximal `89%`.
- Wenn Backlog-Änderungen im Report nicht eindeutig als geschrieben oder nur vorgeschlagen gekennzeichnet sind, ist die Bewertung maximal `GELB` und der Score maximal `89%`.
- Bei reinen Ignore-Findings ohne Risiko: kein Abzug.

Die Prozentzahl ist eine operative Orientierung, keine exakte Qualitätsmetrik.

### Empfohlene Aktion

Der Report muss genau eine Hauptempfehlung ausgeben:

```text
Empfohlene Aktion: WEITERMACHEN | WEITERMACHEN MIT VORSICHT | JETZT FIXEN | BLOCKIERT | ESKALIEREN
```

Regeln:

- **WEITERMACHEN:** Systemhealth GRÜN, keine freigabepflichtigen Auto-Fixes, keine Blocker.
- **WEITERMACHEN MIT VORSICHT:** Systemhealth GELB, keine Blocker; Auto-Fixes sind nicht zwingend für aktuelle Arbeit.
- **JETZT FIXEN:** Safe Auto-Fix ist niedrig riskant und blockiert real den aktuellen Arbeitsfluss.
- **BLOCKIERT:** Systemhealth ROT durch Blocker; keine Feature-/Release-Arbeit fortsetzen.
- **ESKALIEREN:** Bewertung ist nicht deterministisch oder betrifft riskante zentrale Systemstruktur.

Wenn es optionale Aufräumarbeiten gibt, müssen sie separat stehen:

```text
Optionale Folgeaktion:
- <konkreter Cleanup oder "Keine">
```

### Auto-Fix-Freigabe am Ende

Wenn mindestens ein Auto-Fix-Kandidat gefunden wurde, muss der Report am Ende eine direkte Nutzerfrage enthalten.

Der Healthcheck darf Auto-Fixes nicht ausführen, bevor der Nutzer explizit zustimmt.

Begriffsdefinition:

- **Auto-Fix-Kandidaten** sind Maßnahmen, z. B. "Leere Log-Dateien entfernen".
- **Betroffene Artefakte** sind konkrete Dateien oder Ordner, z. B. `backend_stdout.log` und `backend_stderr.log`.
- Eine Maßnahme kann mehrere Artefakte betreffen.
- Der Report muss beide Zahlen getrennt nennen.
- Die Zahl `Betroffene Auto-Fix-Artefakte` muss konkrete Dateien und konkrete Ordner zählen.
- Wenn ein Ordner als eigenständige Lösch-/Verschiebe-Aktion ausgeführt wird und enthaltene Dateien zusätzlich explizit gelistet werden, zählt der Ordner zusätzlich zu den enthaltenen Dateien.
- Wenn ein Ordner als eigenständige Lösch-/Verschiebe-Aktion ausgeführt wird und die enthaltenen Dateien nicht einzeln gelistet werden, zählt nur der Ordner.
- Wenn ein Ordner nur als Container genannt wird und nicht selbst gelöscht/verschoben wird, zählt nur der konkrete Inhalt.
- Bei Sammelaktionen muss die Artefaktzahl aus der Summe der explizit gelisteten Dateien/Ordner berechnet werden.

Risiko-Schärfung:

- Leere Dateien, leere Ordner und eindeutig timestamped temporäre Backup-Artefakte dürfen `Risk: LOW` sein.
- Nicht-leere Dateien dürfen nur dann `Risk: LOW` sein, wenn sie eindeutig generiert, temporär und nicht referenziert sind.
- Nicht-leere Debug-, Report-, Script-, Test- oder Dokumentationsdateien sind mindestens `Risk: LOW-MEDIUM`, auch wenn sie nur verschoben und nicht gelöscht werden.
- `LOW-MEDIUM` Kandidaten dürfen nicht unter "alle sicheren Auto-Fix-Kandidaten" pauschal ausgeführt werden; sie müssen über `AUSWAHL` oder eine separate explizite Einzel-Freigabe bestätigt werden.
- Python-, PowerShell-, Batch-, JavaScript- oder andere ausführbare Skripte dürfen niemals pauschal als `Risk: LOW` gelöscht oder verschoben werden, außer sie sind leer.
- Bilddateien, PDFs, Datenbanken, Markdown-Dokumente, Reports und nicht-leere JSON-Dateien dürfen niemals pauschal als `Risk: LOW` gelöscht werden, außer sie sind eindeutig generiert und entbehrlich belegt.
- Nicht-leere `*.json` im Projekt-Root sind mindestens `Risk: LOW-MEDIUM`, außer sie sind eindeutig reine, timestamped oder disposable Tool-Ausgaben und werden nicht von Tests, Config oder Dokumentation referenziert.
- Nicht-leere `*.png`, `*.jpg`, `*.jpeg`, `*.webp` im Projekt-Root sind mindestens `Risk: LOW-MEDIUM`, außer sie sind eindeutig generierte Screenshots/Artefakte mit belegt entbehrlichem Zweck.
- Root-`*.exe` ist mindestens `Risk: LOW-MEDIUM`, außer eindeutig belegt ist, dass es ein veraltetes Release-Artefakt ist, eine neuere Kopie im offiziellen Release-Ordner existiert, es nicht referenziert wird und die Zielaktion bevorzugt Verschieben/Archivieren statt Löschen ist.
- Wenn ein Finding mögliche Credentials, Tokens, API Keys, Secrets, private URLs oder hardcoded Zugangsdaten erwähnt, darf es nicht als Auto-Fix-Kandidat ausgeführt werden.
- Mögliche Credential-/Secret-Findings sind mindestens `BACKLOG ITEM` mit `Risk: MEDIUM` oder bei unklarem Schaden `ESCALATION REQUIRED`.
- Wenn `Workspace-Status: unbekannt` ist und nicht-leere Dateien betroffen sind, darf keine Empfehlung `NEIN – Auto-Fix ohne Snapshot` ausgegeben werden.
- Bei unbekanntem Workspace-Status und nicht-trivialen Änderungen muss die Empfehlung `JA – zuerst Safety-Snapshot` oder `ABBRECHEN` lauten.
- Rollback via Git darf nur als sicher bezeichnet werden, wenn geprüft wurde, dass die betroffenen Artefakte Git-getrackt sind.

### Auto-Fix Eligibility Hard Gate

Ein Finding darf nur dann unter `Auto-Fix-Kandidaten` stehen, wenn alle folgenden Punkte erfüllt sind:

- konkrete Artefakte sind bekannt
- Artefakte sind lokal begrenzt
- kein produktives Verhalten wird geändert
- kein Build-, Runtime-, Test- oder Dokumentationsvertrag ist erkennbar betroffen
- keine Credentials oder Secrets werden erwähnt
- Risiko ist deterministisch bewertbar
- bei Löschung nicht-leerer Dateien ist belegt, dass sie generiert oder entbehrlich sind

Wenn ein Punkt nicht erfüllt ist:

- nicht als Auto-Fix-Kandidat klassifizieren
- stattdessen `BACKLOG ITEM`, `IGNORE` oder `ESCALATION REQUIRED` wählen

Zusätzliche harte Klassifizierungsregeln:

- Nicht-leere Skripte (`*.py`, `*.ps1`, `*.bat`, `*.js`, `*.cjs`, `*.mjs`) → niemals pauschaler Auto-Fix; mindestens `LOW-MEDIUM` und nur per `AUSWAHL`, sonst Backlog. Dies gilt für Löschen, Verschieben und Archivieren.
- Utility-Skripte im Root (`*.py` mit Tool-/Debug-/Export-Funktion) → standardmäßig `BACKLOG ITEM` oder `AUSWAHL` mit `Risk: LOW-MEDIUM`; niemals `Risk: LOW`, auch wenn nur nach `tools/` oder `scripts/` verschoben wird.
- Dateien mit möglichen Secrets/Credentials → kein Auto-Fix; `BACKLOG ITEM` oder `ESCALATION REQUIRED`.
- Nicht-leere Bilder (`*.png`, `*.jpg`, `*.jpeg`, `*.webp`) → kein pauschaler Auto-Fix; ignorieren oder Backlog, wenn Strukturdrift relevant ist.
- Nicht-leere Root-JSON-Dateien (`*.json`) → kein pauschaler Auto-Fix; höchstens `AUSWAHL` mit `Risk: LOW-MEDIUM`, sonst Backlog/Ignore.
- Root-Release-Artefakte (`*.exe`, Installer, Setup-Dateien) → kein Löschen als pauschaler Auto-Fix; höchstens `AUSWAHL` mit `Risk: LOW-MEDIUM` und bevorzugt Verschieben nach `release/` oder Backlog.
- Datenbanken (`*.db`, `*.sqlite`) → niemals Auto-Fix.
- Aktive Config-Dateien und config-nahe Backups → nur verschieben/löschen, wenn eindeutig altes Backup und Zielpfad/Replacement klar ist.

### Auto-Fix Scope Budget

Der Healthcheck darf Auto-Fix nur für kleine, mechanische Hygiene-Maßnahmen anbieten.

Pauschal sichere Auto-Fix-Vorschläge sind auf folgende Grenzen beschränkt:

- maximal 3 Auto-Fix-Maßnahmen
- maximal 10 betroffene Artefakte
- ausschließlich `Risk: LOW`
- ausschließlich leere Ordner, leere Dateien oder eindeutig temporäre/generated Artefakte ohne Nutzdatenwert

Wenn mehr als 3 Maßnahmen oder mehr als 10 Artefakte betroffen sind:

- kein pauschales `JA`
- `Pauschales JA erlaubt: NEIN`
- Empfehlung: `AUSWAHL verwenden` oder `Backlog/Task für Root-Cleanup erstellen`
- der Report muss die Kandidaten in Gruppen aufteilen: `Sofort per AUSWAHL möglich`, `Backlog/Task`, `Ignorieren`

Wenn ein Cleanup unterschiedliche Artefaktklassen mischt (`.vtt`, `.m4a`, `.log`, `.json`, `.py`, `.png`, `.exe`, Ordner):

- nicht als ein großer Auto-Fix-Block behandeln
- riskante Klassen aus Auto-Fix herauslösen
- nur eindeutig temporäre LOW-Artefakte dürfen in `Sofort per AUSWAHL möglich` bleiben

### Auto-Fix Execution Gating

Der Freigabe-Block muss zwischen pauschal sicheren und selektiv freizugebenden Maßnahmen unterscheiden.

Pauschales `JA – alle sicheren Auto-Fix-Kandidaten jetzt ausführen` ist nur erlaubt, wenn:

- alle gelisteten Kandidaten `Risk: LOW` sind
- keine nicht-leeren Skripte betroffen sind
- keine nicht-leeren Doku-/Report-/Bild-/Daten-/Config-Dateien betroffen sind
- Workspace-Status `sauber` oder ausreichend geprüft ist
- Rollback entweder nicht nötig oder konkret möglich ist

Pauschales `JA` ist verboten, wenn:

- `Workspace-Status: unbekannt` ist und irgendeine nicht-leere Datei gelöscht oder verschoben werden soll.
- `Workspace-Status: unbekannt` ist und die Auto-Fixes nicht ausschließlich leere Dateien oder leere Ordner betreffen.
- `Workspace-Status: unbekannt` ist und Audio-, Subtitle-, Log-, Report-, Daten-, Bild-, Config- oder Dokumentationsdateien betroffen sind, auch wenn sie als temporär eingeschätzt werden.
- mehr als 3 Maßnahmen oder mehr als 10 Artefakte betroffen sind.
- irgendein Kandidat `*.py`, nicht-leere `*.json`, Root-`*.png` oder Root-`*.exe` betrifft.

In diesen Fällen muss `Pauschales JA erlaubt: NEIN` gesetzt werden. Erlaubte Optionen sind dann nur `NEIN` und `AUSWAHL`, oder zuerst eine Safety-Snapshot-Frage.

Wenn mindestens ein Kandidat `Risk: LOW-MEDIUM` oder höher ist:

- keine Option `JA – alle sicheren Auto-Fix-Kandidaten jetzt ausführen` anbieten
- stattdessen `AUSWAHL` oder Einzel-Freigabe erzwingen
- `LOW` Kandidaten dürfen separat vorgeschlagen werden
- `LOW-MEDIUM` Kandidaten müssen einzeln mit Grund und Risiko bestätigt werden

Pflichtformulierung bei gemischten Risiken:

```text
Pauschale Ausführung ist nicht verfügbar, weil mindestens ein Kandidat LOW-MEDIUM oder höher ist.
Bitte nutze AUSWAHL und bestätige riskantere Kandidaten einzeln.
```

Wenn `Workspace-Status: unbekannt` und nicht-leere Artefakte betroffen sind:

- keine Empfehlung `NEIN – Auto-Fix ohne Snapshot`
- keine Empfehlung `NEIN – nur triviale LOW-Fixes ohne Snapshot`
- keine pauschale Ausführung
- `Pauschales JA erlaubt: NEIN`
- Empfehlung muss `JA – zuerst Safety-Snapshot`, `AUSWAHL verwenden` oder `ABBRECHEN` sein
- wenn nur einzelne LOW-Dateien eindeutig temporär sind, darf `AUSWAHL verwenden` empfohlen werden

### Pre-Output Consistency Gate

Vor Ausgabe des finalen Reports muss der Healthcheck seine Auto-Fix-Sektion selbst prüfen.

Der Report darf keine Auto-Fix-Freigabe anbieten, wenn eine der folgenden Prüfungen fehlschlägt:

- Summary-Zahl `Auto-fix candidates` entspricht nicht der Anzahl der im Freigabe-Block gelisteten Maßnahmen.
- Summary-Zahl `Betroffene Auto-Fix-Artefakte` entspricht nicht der Summe der explizit gelisteten Artefakte im Freigabe-Block.
- Ein Kandidat enthält nicht-leere Skripte und ist trotzdem `Risk: LOW`.
- Ein Kandidat enthält nicht-leere JSON-, Log-, Report-, Doku-, Bild-, Daten- oder Config-Dateien und ist ohne Entbehrlichkeitsbeleg `Risk: LOW`.
- Ein Kandidat erwähnt mögliche Credentials/Secrets und steht trotzdem unter Auto-Fix.
- `Workspace-Status: unbekannt` und nicht-leere Artefakte sind betroffen, aber Empfehlung ist `NEIN`.
- Eine pauschale `JA`-Option wird angeboten, obwohl mindestens ein Kandidat nach Dateityp oder Risiko `LOW-MEDIUM` oder höher sein müsste.
- Mehr als 3 Auto-Fix-Maßnahmen oder mehr als 10 Artefakte werden als freigabefähiger Auto-Fix-Block präsentiert.
- Ein Root-`*.py`, nicht-leeres Root-`*.json`, Root-`*.png` oder Root-`*.exe` ist als `Risk: LOW` klassifiziert.
- Ein nicht-leeres Skript wird als Auto-Fix-Kandidat geführt, ohne `Risk: LOW-MEDIUM` und ohne `AUSWAHL`/Einzelfreigabe zu erzwingen.
- Ein Root-Installer/`*.exe` wird gelöscht statt verschoben/archiviert, ohne belegten Ersatz im offiziellen Release-Ordner und ohne Einzelfreigabe.
- Der Sicherheits-Checkpoint vor Auto-Fix fehlt, obwohl Auto-Fix-Kandidaten vorhanden sind.
- Die Auto-Fix-Frage erscheint vor dem Sicherheits-Checkpoint.
- Die Pflichtsektion `## Auto-Fix-Gate-Prüfung` fehlt, obwohl Auto-Fix-Kandidaten vorhanden sind.
- Die Pflichtsektion `## Auto-Fix-Gate-Prüfung` steht nach der Auto-Fix-Frage oder nach der Freigabeaufforderung.
- `## Auto-Fix-Gate-Prüfung` nennt `Status: PASS`, aber die Kandidaten-/Artefaktzahlen, Risikoangaben oder erlaubten Optionen widersprechen dem Freigabeblock.
- Backlog-Items werden als erstellt/aktualisiert dargestellt, aber `## Backlog-Änderungen` fehlt oder sagt nicht eindeutig, ob `documentation/backlog/BACKLOG.md` tatsächlich geändert wurde.
- `## Backlog-Änderungen` steht nach `## Auto-Fix-Gate-Prüfung`, `## Sicherheits-Checkpoint vor Auto-Fix`, `## Freigabe erforderlich` oder der Auto-Fix-Frage.
- `Workspace-Status: unbekannt` und nicht-leere Dateien sind betroffen, aber `Pauschales JA erlaubt: JA`.
- `Workspace-Status: unbekannt` und nicht-leere Dateien sind betroffen, aber die Optionen enthalten eine pauschale `JA`-Ausführung.
- `Workspace-Status: unbekannt` und nicht-leere Dateien sind betroffen, aber die Sicherheits-Empfehlung lautet `NEIN – nur triviale LOW-Fixes ohne Snapshot`.
- Ein Backlog-Finding zu nicht-leeren Skripten oder unklarem Skriptordner wird als `GRÜN`/`irgendwann` bewertet.

Wenn eine Prüfung fehlschlägt:

- Report trotzdem ausgeben
- Auto-Fix-Freigabe auf `BLOCKED – Report inkonsistent` setzen
- keine Frage `Möchtest du diese Auto-Fixes jetzt ausführen?` stellen
- unter `Hinweise zur Report-Konsistenz` alle fehlerhaften Punkte nennen
- konservative Empfehlung ausgeben: `AUSWAHL nach manueller Prüfung` oder `zuerst Safety-Snapshot`
- Systemhealth maximal `GELB` setzen, auch wenn die Hygiene-Findings sonst `GRÜN` ergeben würden.
- Score maximal `89%` setzen.

Pflichtformat bei blockierter Auto-Fix-Freigabe:

```text
## Hinweise zur Report-Konsistenz
- <konkreter Konflikt, z. B. "Summary nennt 3 Artefakte, Freigabe-Block listet 11.">
- <konkreter Konflikt, z. B. "Nicht-leere Python-Skripte wurden als LOW klassifiziert.">

## Freigabe erforderlich
Status: BLOCKED – Report inkonsistent
Warum: Auto-Fix darf bei widersprüchlichen Zahlen oder falscher Risikoklasse nicht angeboten werden.
Empfehlung: AUSWAHL nach manueller Prüfung oder zuerst Safety-Snapshot.
```

Risk-Revalidation-Regel:

- Direkt vor Ausgabe müssen alle Auto-Fix-Kandidaten erneut gegen `Risiko-Schärfung`, `Auto-Fix Eligibility Hard Gate` und `Auto-Fix Execution Gating` geprüft werden.
- Diese zweite Prüfung überstimmt frühere Einschätzungen.
- Bei Konflikt immer die höhere Risikoklasse wählen.
- Wenn die zweite Prüfung einen Auto-Fix-Kandidaten hochstuft, muss der Freigabe-Block neu berechnet werden: Kandidatenzahl, Artefaktzahl, JA/AUSWAHL-Optionen, Score und Snapshot-Empfehlung.
- Wenn die zweite Prüfung mehr als 3 Maßnahmen, mehr als 10 Artefakte oder gemischte Dateiklassen erkennt, muss sie den Auto-Fix-Block reduzieren oder auf `BLOCKED – Scope zu groß für Auto-Fix` setzen.
- Kandidaten, die `*.py`, nicht-leere Root-`*.json`, Root-`*.png`, Root-`*.exe`, unbekannte Ordner oder persönliche Doku-/PDF-Ordner betreffen, müssen aus pauschalem Auto-Fix herausgelöst werden.

Pflichtausgabe der zweiten Prüfung:

```text
## Auto-Fix-Gate-Prüfung
- **Status:** PASS | BLOCKED
- **Geprüfte Kandidaten:** <n>
- **Hochgestufte Kandidaten:** <Liste oder "Keine">
- **Pauschales JA erlaubt:** JA | NEIN
- **Grund:** <kurze Begründung>
```

Diese Sektion ist bei vorhandenen Auto-Fix-Kandidaten immer verpflichtend und muss vor `## Sicherheits-Checkpoint vor Auto-Fix`, `## Freigabe erforderlich` und `## Auto-Fix-Entscheidung` stehen.

Wenn `Workspace-Status: unbekannt` und nicht-leere Dateien betroffen sind, muss diese Sektion ausgeben:

```text
- **Pauschales JA erlaubt:** NEIN
- **Grund:** Workspace-Status unbekannt und nicht-leere Dateien betroffen; nur AUSWAHL oder Safety-Snapshot erlaubt.
```

Wenn die Sektion nicht erzeugt werden kann:

- `Status: BLOCKED` annehmen
- keine Auto-Fix-Frage stellen
- unter `Hinweise zur Report-Konsistenz` nennen: `Auto-Fix-Gate-Prüfung fehlt`
- Systemhealth maximal `GELB` und Score maximal `89%`

Wenn `Status: BLOCKED` oder `Pauschales JA erlaubt: NEIN` ist:

- keine pauschale `JA`-Option anzeigen
- nur `NEIN` und `AUSWAHL` anzeigen
- wenn der Sicherheits-Checkpoint ebenfalls fehlt oder falsch ist, gar keine Auto-Fix-Entscheidung anzeigen

Harte Beispiele, die immer gelten:

- `debug_thinking/` mit `A.py`, `B.py`, `C.py`, `D.py` → `Risk: LOW-MEDIUM`, weil nicht-leere Python-Skripte betroffen sind.
- `*.py` Dateien im Root oder Unterordnern → niemals pauschal `LOW`, außer Datei ist leer.
- `*.log` im Root → nur `LOW`, wenn generiert, entbehrlich und nicht Teil einer permanenten Log-/Debug-Infrastruktur.
- `*.json` im Root → mindestens `LOW-MEDIUM`, wenn nicht eindeutig reine disposable Tool-Ausgabe.
- `*.png` im Root → mindestens `LOW-MEDIUM`, wenn Zweck nicht eindeutig generiert/entbehrlich ist.
- `*.exe` im Root → nur `LOW-MEDIUM` per `AUSWAHL`, wenn als veraltetes Build-Artefakt belegt und Ziel-/Archivpfad klar ist; sonst Backlog oder Eskalation.
- Bei `Workspace-Status: unbekannt` und nicht-leeren Artefakten → Empfehlung niemals `NEIN – nur triviale LOW-Fixes ohne Snapshot`.
- Ein Backlog-Item zu einem Ordner mit nicht-leeren Skripten und unklarem Zweck → mindestens `Backlog-Wichtigkeit: GELB`, `Empfohlener Zeitpunkt: nach aktuellem Feature`, `Risiko wenn ignoriert: mittel-niedrig`.

### Backlog Mutation Safety Gate

Wenn der Healthcheck `documentation/backlog/BACKLOG.md` erstellt, ergänzt oder aktualisiert, gilt:

- Die Änderung muss im Report unter `Dateien geändert` genannt werden.
- `Backlog items created/updated` muss exakt zur tatsächlichen Änderung passen.
- Ein neues Backlog-Item mit `Status: READY` muss im Abschnitt `## READY` stehen.
- Ein neues Backlog-Item mit `Status: NEEDS INFO` muss im Abschnitt `## NEEDS INFO` stehen.
- Ein neues Backlog-Item mit `Status: BLOCKED` muss im Abschnitt `## BLOCKED` stehen.
- Der Abschnitt `## IN PROGRESS` darf nur Items enthalten, die wirklich an die Diamond-Pipeline übergeben wurden.
- Es dürfen keine bestehenden `BACKLOG-XXX` IDs überschrieben werden.
- Neue IDs müssen fortlaufend zur höchsten bestehenden ID vergeben werden.
- Wenn ein ähnliches Item existiert, aktualisieren statt duplizieren.

Backlog-Änderungen sind keine Auto-Fixes, aber trotzdem Workspace-Änderungen.

Jeder Report muss eindeutig zwischen tatsächlicher Backlog-Mutation und bloßem Vorschlag unterscheiden.

`## Backlog-Änderungen` muss im Report vor `## Auto-Fix-Gate-Prüfung`, `## Sicherheits-Checkpoint vor Auto-Fix`, `## Freigabe erforderlich` und jeder Auto-Fix-Frage stehen.

Wenn `## Backlog-Änderungen` erst nach der Auto-Fix-Frage erscheint:

- Report als inkonsistent markieren
- Auto-Fix-Freigabe auf `BLOCKED – Report inkonsistent` setzen
- keine Auto-Fix-Frage stellen
- unter `Hinweise zur Report-Konsistenz` nennen: `Backlog-Änderungen stehen nach der Auto-Fix-Frage`

Pflichtformat auch ohne Backlog-Schreibzugriff:

```text
## Backlog-Änderungen
- **Status:** JA | NEIN
- **Datei geändert:** documentation/backlog/BACKLOG.md | Keine
- **Items erstellt/aktualisiert:** <Liste oder "Keine">
- **Hinweis:** <"Änderung wurde bereits vorgenommen" oder "Eintrag ist nur vorgeschlagen und wurde nicht geschrieben">
```

Wenn Backlog geschrieben wurde:

- Der Abschlussstatus darf nicht `Dateien geändert: Keine` sagen.
- Die Auto-Fix-Frage muss klarstellen, dass der Backlog bereits geändert wurde und die Frage nur die verbleibenden Auto-Fixes betrifft.
- Wenn Backlog-Schreibzugriff fehlschlägt oder die Status/Abschnitt-Zuordnung inkonsistent ist, muss der Report unter `Hinweise zur Report-Konsistenz` warnen.

Pflichtformat bei Backlog-Änderung:

```text
## Backlog-Änderungen
- **Status:** JA
- **Datei geändert:** documentation/backlog/BACKLOG.md
- **Items erstellt/aktualisiert:** <Liste>
- **Hinweis:** Diese Änderung wurde bereits vorgenommen; die folgende Auto-Fix-Freigabe betrifft nur Datei-/Ordner-Fixes.
```

### Pre-Auto-Fix Safety Snapshot Gate

Bevor freigegebene Auto-Fixes ausgeführt werden, muss der Healthcheck einen Sicherheits-Checkpoint prüfen.

Der Sicherheits-Checkpoint ist Pflicht, sobald mindestens ein Auto-Fix-Kandidat im Report steht.

Der Sicherheits-Checkpoint muss im Report vor der Auto-Fix-Frage stehen.

Wenn der Sicherheits-Checkpoint nicht erstellt werden kann:

- keine Auto-Fix-Frage stellen
- Freigabe auf `BLOCKED – Sicherheits-Checkpoint fehlt` setzen
- Systemhealth maximal `GELB` und Score maximal `89%`
- klare nächste Aktion nennen: Workspace-Status prüfen oder Safety-Snapshot erstellen

Ziel:

- Nutzerarbeit schützen
- Rollback ermöglichen
- keine unrelated Workspace-Änderungen versehentlich committen

Regeln:

- Der Healthcheck darf **keinen automatischen Git-Commit ohne explizite Nutzerfreigabe** erstellen.
- Wenn der Workspace bereits viele unrelated Änderungen enthält, darf kein pauschaler Commit erstellt werden.
- Vor destruktiven Aktionen muss mindestens ein Rollback-Plan ausgegeben werden.
- Wenn Git verfügbar ist, muss vor Ausführung empfohlen werden, entweder:
  - einen gezielten `/save` auszuführen, oder
  - nur die Healthcheck-Auto-Fix-Änderungen nach der Ausführung separat zu speichern.
- Wenn der Nutzer ausdrücklich einen Commit/Snapshot möchte, muss der Healthcheck zuerst die konkret zu sichernden Dateien/Ordner nennen und Freigabe einholen.

Pflichtblock vor Auto-Fix-Ausführung:

```text
## Sicherheits-Checkpoint vor Auto-Fix

- **Workspace-Status:** sauber | uncommitted changes vorhanden | unbekannt
- **Commit/Snapshot automatisch erstellt:** NEIN
- **Warum:** Auto-Fix darf keine unrelated Änderungen ungeprüft committen.
- **Rollback-Plan:** <konkret, z. B. "verschobene Dateien aus archiv/ zurückschieben"; "gelöschte leere Dateien/Ordner haben keinen Inhalt">
- **Empfehlung:** <JA – zuerst Safety-Snapshot | NEIN – nur triviale LOW-Fixes ohne Snapshot | AUSWAHL verwenden | ABBRECHEN>
- **Empfehlungsgrund:** <klare kurze Begründung>
```

Rollback-Belegpflicht:

- `Aus Git wiederherstellen` darf nur als Rollback-Plan genannt werden, wenn für jedes betroffene Artefakt geprüft wurde, dass es Git-getrackt ist.
- Für untracked oder unbekannt getrackte Artefakte muss der Rollback-Plan entweder `Snapshot erstellen`, `Verschieben statt Löschen` oder `AUSWAHL nach Einzelprüfung` lauten.
- Bei großen oder nicht-leeren untracked Artefakten darf der Rollback nicht als trivial bezeichnet werden.

Wenn ein sicherer Snapshot sinnvoll ist, aber nicht automatisch erstellt werden darf, frage:

```text
Möchtest du vor dem Auto-Fix einen gezielten Safety-Snapshot erstellen?

Empfehlung: <JA | NEIN | ABBRECHEN>
Warum: <klare kurze Begründung>

Optionen:
1) JA – zuerst gezielten Snapshot/Save vorbereiten
2) NEIN – keinen Snapshot erstellen; danach nur AUSWAHL nach Einzelprüfung
3) ABBRECHEN – keine Auto-Fixes ausführen
```

Empfehlungslogik:

- Empfiehl **JA**, wenn:
  - nicht-leere Dateien verschoben/gelöscht werden sollen
  - `LOW-MEDIUM` Kandidaten ausgewählt wurden
  - der Workspace uncommitted changes enthält und die Auto-Fixes mehrere Artefakte betreffen
  - der Workspace-Status unbekannt ist und die Aktion nicht ausschließlich leere Dateien/Ordner betrifft
  - Rollback nicht trivial ist
- Empfiehl **NEIN**, wenn:
  - ausschließlich leere Dateien/Ordner gelöscht werden
  - ausschließlich eindeutig temporäre timestamped Dateien gelöscht werden
  - keine nicht-leeren Dateien betroffen sind
  - der Rollback-Plan trivial ist oder kein Nutzdatenverlust möglich ist
- Empfiehl **NEIN** niemals, wenn `Workspace-Status: unbekannt` ist und nicht-leere Dateien gelöscht oder verschoben werden sollen.
- Empfiehl **NEIN – nur triviale LOW-Fixes ohne Snapshot** nur, wenn ausschließlich leere Dateien/Ordner oder eindeutig entbehrliche leere/timestamped Artefakte betroffen sind.
- Nicht-leere Audio-, Subtitle- und Log-Dateien dürfen bei unbekanntem Workspace-Status zwar `Risk: LOW` bleiben, aber nicht pauschal per `JA` ausgeführt werden; nutze `AUSWAHL verwenden` oder `JA – zuerst Safety-Snapshot`.
- Wenn `JA – zuerst Safety-Snapshot` empfohlen wird, darf die Snapshot-Option `NEIN` nicht direkt zur Auto-Fix-Ausführung führen; sie führt nur zurück zu `AUSWAHL nach Einzelprüfung` oder `ABBRECHEN`.
- Empfiehl **ABBRECHEN**, wenn:
  - Workspace-Status unbekannt ist und die Aktion nicht rein trivial ist
  - zentrale Dateien, Datenbanken, aktive Configs, Scripts oder Dokumentation betroffen sind
  - Risiko nicht sicher bestimmbar ist

Die Empfehlung muss eine Hauptempfehlung sein. Optionen bleiben auswählbar, aber der Nutzer muss klar sehen, was Janus empfiehlt.

Pflichtformat:

```text
## Auto-Fix-Gate-Prüfung
- **Status:** PASS | BLOCKED
- **Geprüfte Kandidaten:** <n>
- **Hochgestufte Kandidaten:** <Liste oder "Keine">
- **Pauschales JA erlaubt:** JA | NEIN
- **Grund:** <kurze Begründung>

## Sicherheits-Checkpoint vor Auto-Fix
- **Workspace-Status:** sauber | uncommitted changes vorhanden | unbekannt
- **Commit/Snapshot automatisch erstellt:** NEIN
- **Warum:** Auto-Fix darf keine unrelated Änderungen ungeprüft committen.
- **Rollback-Plan:** <konkreter Rollback-Plan>
- **Empfehlung:** <JA – zuerst Safety-Snapshot | NEIN – nur triviale LOW-Fixes ohne Snapshot | AUSWAHL verwenden | ABBRECHEN>
- **Empfehlungsgrund:** <klare kurze Begründung>

## Freigabe erforderlich

Es wurden <n> sichere Auto-Fix-Kandidaten gefunden.
Betroffene Artefakte: <m> Dateien/Ordner.

Diese Maßnahmen würden bei Zustimmung ausgeführt:

1) <Titel des Auto-Fix-Kandidaten>
   - Was passiert: <konkrete Datei-/Ordneraktion>
   - Betroffene Artefakte: <konkrete Liste>
   - Warum sicher: <kurze Begründung>
   - Risiko: LOW

2) <Titel des Auto-Fix-Kandidaten>
   - Was passiert: <konkrete Datei-/Ordneraktion>
   - Betroffene Artefakte: <konkrete Liste>
   - Warum sicher: <kurze Begründung>
   - Risiko: LOW

Möchtest du diese Auto-Fixes jetzt ausführen?

Optionen:
1) JA – alle pauschal freigegebenen LOW-Kandidaten jetzt ausführen, nur wenn `Pauschales JA erlaubt: JA` und Auto-Fix Execution Gating erfüllt ist
2) NEIN – nichts ausführen, nur Report behalten
3) AUSWAHL – ich wähle einzelne Kandidaten aus

Bitte antworte mit: JA, NEIN oder AUSWAHL.
```

Wenn `Pauschales JA erlaubt: NEIN` ist, muss der Optionenblock stattdessen lauten:

```text
Optionen:
1) NEIN – nichts ausführen, nur Report behalten
2) AUSWAHL – ich wähle einzelne Kandidaten aus

Bitte antworte mit: NEIN oder AUSWAHL.
```

Wenn `AUSWAHL` gewählt wird, muss der Healthcheck die Kandidaten nummeriert auflisten und auf die konkrete Auswahl warten.

Wenn `NEIN` gewählt wird:

- Keine Dateien ändern.
- Abschlussstatus bleibt report-only.

Wenn `JA` gewählt wird:

- `JA` darf nur akzeptiert werden, wenn `Pauschales JA erlaubt: JA` im Abschnitt `## Auto-Fix-Gate-Prüfung` steht.
- Nur Kandidaten ausführen, die im Report als `Risk: LOW` und `Requires approval: YES` markiert wurden.
- Keine `LOW-MEDIUM`, `MEDIUM` oder unklaren Kandidaten pauschal ausführen.
- Keine Backlog-Items automatisch implementieren.
- Keine ignorierten Findings anfassen.
- Danach einen kurzen Fix-Report mit Anzahl der ausgeführten Maßnahmen, Anzahl der betroffenen Artefakte und geänderten/gelöschten Dateien/Ordner ausgeben.

Pflichtformat für den Fix-Report nach Freigabe:

```text
## Fix-Report

- **Ausgeführte Auto-Fix-Maßnahmen:** <n>
- **Betroffene Artefakte:** <m>
- **Gelöschte Artefakte:** <n>
- **Verschobene Artefakte:** <n>

## Ausgeführte Maßnahmen
1) <Maßnahme>
   - Artefakte: <Liste>
   - Ergebnis: gelöscht | verschoben | übersprungen

## Abschlussstatus nach Auto-Fix
- **Dateien/Ordner geändert:** <m>
- **Was wurde gemacht:** <kurz>
- **Ergebnis:** <neuer Systemhealth-Score + Ampel + Bedeutung>
```

### Backlog-Einträge transparent bewerten

Wenn ein Finding ins Backlog geschrieben oder dort aktualisiert wurde, muss der Report genau erklären:

- welcher Backlog-Eintrag erstellt oder aktualisiert wurde
- warum er ins Backlog gehört
- welche konkrete Datei / Struktur / Beobachtung der Auslöser war
- wie wichtig die Bearbeitung ist
- wann der Nutzer ihn sinnvoll angehen sollte

Pflicht-Ampel für Backlog-Wichtigkeit:

```text
Backlog-Wichtigkeit: ROT | GELB | GRÜN
```

Bewertung:

- **ROT:** Sofort erledigen. Das Finding blockiert aktuelle Arbeit, Release-Fähigkeit, zentrale Workflows oder kann kurzfristig Folgefehler auslösen.
- **GELB:** Zeitnah erledigen, typischerweise nach dem aktuellen Feature oder vor dem nächsten größeren Release/Arbeitsblock. Nicht akut blockierend, aber relevante Struktur- oder Wartungsdrift.
- **GRÜN:** Irgendwann erledigen. Niedrige Priorität, rein kosmetisch oder langfristige Hygiene ohne akutes Risiko.

Mindestbewertung:

- Backlog-Items zu nicht-leeren Skripten, unbekanntem Skriptzweck, ausführbaren Dateien oder unklaren Debug-/Analyseordnern sind mindestens `GELB`.
- `GRÜN` ist nur erlaubt, wenn keine ausführbaren oder nicht-leeren Arbeitsartefakte betroffen sind und das Finding eindeutig kosmetisch ist.

Der Report muss für jeden Backlog-Eintrag eine konkrete Empfehlung enthalten:

```text
## Backlog-Bewertung
- **BACKLOG-XXX:** <Titel>
  - **Wichtigkeit:** ROT | GELB | GRÜN
  - **Empfohlener Zeitpunkt:** sofort | nach aktuellem Feature | vor nächstem Release | irgendwann
  - **Warum wichtig:** <kurze Begründung>
  - **Risiko wenn ignoriert:** <konkretes Risiko oder "gering">
```

---

## Finding Decision Engine

Jedes Finding muss genau eine Entscheidung erhalten:

```text
A) AUTO-FIX CANDIDATE
B) BACKLOG ITEM
C) IGNORE
D) ESCALATION REQUIRED
```

### A) AUTO-FIX CANDIDATE

Nur wenn alles zutrifft:

- sicher
- mechanisch
- lokal
- reversibel
- kein Feature-Verhalten betroffen
- keine Architekturentscheidung nötig
- geringe Nebenwirkungswahrscheinlichkeit

Beispiele:
- eindeutig temporäre Datei entfernen
- leere versehentliche Datei entfernen
- eindeutig falsch abgelegtes Runbook aus `workflows` in `runbooks` verschieben
- einfache Dateinamensnormalisierung ohne Import-/Pfadfolgen

Auto-Fix-Ausführung:
- Vor Ausführung eine explizite Freigabe einholen.
- Wenn keine Freigabe vorliegt, nur als Kandidat reporten.

### B) BACKLOG ITEM

Wenn das Finding größer, riskant oder nicht rein mechanisch ist.

Beispiele:
- große Datei sollte aufgeteilt werden
- Modul hat gemischte Verantwortlichkeiten
- Architekturgrenze ist unsauber
- technische Schuld mit realem Wartungsrisiko
- wiederkehrendes Hygiene-Problem

Schreibe oder aktualisiere einen Eintrag in:

```text
documentation/backlog/BACKLOG.md
```

Backlog-Typen:

```text
TECH_DEBT
IMPROVEMENT
ENHANCEMENT
BUG
```

Standardquelle:

```text
Quelle: System Health
```

Standardstatus:

```text
READY
```

Nutze `NEEDS INFO`, wenn konkrete Zusatzinformationen nötig sind.

### C) IGNORE

Ignoriere Findings, wenn:

- kein echter Mehrwert entsteht
- Datei bewusst so liegt
- Datei generiert oder extern ist
- Kosten größer als Nutzen sind
- kein Risiko besteht

Ignorierte Findings im Report kurz begründen.

### D) ESCALATION REQUIRED

Nutze diese Entscheidung, wenn SWE 1.6 das Finding nicht sicher bewerten kann.

---

## Escalation Rule

Wenn während des Checks eines der folgenden Probleme auftritt:

- Architekturproblem ist nicht eindeutig bewertbar
- Auto-Fix vs. Backlog ist unklar
- Finding betrifft zentrale Systemstruktur
- mehrere plausible Strukturinterpretationen existieren
- Risiko ist hoch und Auswirkungen sind nicht sicher abgrenzbar
- Monthly Check findet systemweite Architekturdrift
- Orchestrator-, Routing-, Persistence-, Security- oder Release-Struktur ist betroffen und die richtige Entscheidung ist nicht deterministisch

Dann:

```text
STOP
SYSTEM HEALTH ESCALATION REQUIRED
```

Nicht weiter raten, nicht kreativ entscheiden, keine riskanten Änderungen ausführen.

Output:

```markdown
# SYSTEM HEALTH ESCALATION REQUIRED

## Reason
- <konkreter Grund>

## Problem
- <Finding / Bereich / Datei>

## Why SWE 1.6 stopped
- <warum nicht deterministisch entscheidbar>

## Required Action
Bitte wechsle auf GPT-5.5 und führe diesen Skill erneut aus:

/SYSTEM HEALTH – HYGIENE CHECK

Mode: DAILY | WEEKLY | MONTHLY

## Compact Handover
- **Mode:** <mode>
- **Finding:** <finding>
- **Relevant files:** <paths>
- **Options:** <Auto-Fix | Backlog | Ignore | unclear>
- **Risk:** <LOW | MEDIUM | HIGH>
```

---

## Backlog Item Format

Wenn ein Health Finding ins Backlog gehört, nutze das bestehende Format aus `documentation/backlog/BACKLOG.md`.

Backlog-Schreibregel nach Modus:

- `DAILY`: keine Backlog-Datei ändern; nur `Backlog-Kandidat` reporten und als empfohlene Folgeaktion `WEEKLY` oder gezielten Backlog-Skill nennen.
- `WEEKLY`: konkrete, nicht spekulative Struktur-/Hygiene-Findings dürfen ins Backlog geschrieben oder aktualisiert werden.
- `MONTHLY`: Architektur-/Refactor-Findings dürfen ins Backlog geschrieben werden, sofern keine GPT-5.5-Eskalation erforderlich ist.

Beispiel:

```markdown
### BACKLOG-XXX – Refactor large orchestration service

- **Typ:** TECH_DEBT
- **Status:** READY
- **Quelle:** System Health
- **Erstellt:** YYYY-MM-DD
- **Aktualisiert:** YYYY-MM-DD
- **Kurzbeschreibung:** Healthcheck hat erkannt, dass die Datei sehr groß ist und gemischte Verantwortlichkeiten enthält.
- **Erwartetes Verhalten:** Verantwortlichkeiten sind klar getrennt und wartbar.
- **Tatsächliches Verhalten:** Eine zentrale Datei bündelt mehrere Verantwortlichkeiten.
- **Reproduktion / Kontext:** SYSTEM HEALTH – HYGIENE CHECK, Mode: WEEKLY
- **Betroffener Bereich:** Backend / Struktur
- **Nachweise:** <konkrete Datei / Messwert / Finding>
- **Akzeptanzkriterien:**
  - [ ] Verantwortlichkeiten sind nachvollziehbar getrennt.
  - [ ] Bestehende Tests bleiben grün.
  - [ ] Keine Feature-Verhaltensänderung ohne separate Spezifikation.
- **Fehlende Informationen:**
  - Keine
- **Notizen:** Größerer Refactor-Kandidat, nicht automatisch fixen.
```

Wenn ein ähnliches Backlog-Item bereits existiert, aktualisiere es statt ein Duplikat zu erstellen.

---

## Recommended Checks

### Struktur / Workflows

- `.windsurf/workflows` enthält nur echte Slash-Skills.
- Master-Runbooks liegen außerhalb, z. B. `.windsurf/runbooks`.
- Skill-Dateien haben sichtbare Modellangabe in der Description.
- Keine alten Legacy-Duplikate, die im Slash-Menü stören.

### Backlog

- `documentation/backlog/BACKLOG.md` existiert.
- Standardabschnitte existieren:
  - `NEEDS INFO`
  - `READY`
  - `IN PROGRESS`
  - `DONE`
  - `BLOCKED`
- Backlog-Items haben eindeutige `BACKLOG-XXX` IDs.
- Keine offensichtlichen Duplikate.

### Codebase Hygiene

- sehr große Dateien identifizieren
- falsch abgelegte Dateien identifizieren
- temporäre oder offensichtliche Junk-Dateien identifizieren
- verwaiste Doku-/Task-Artefakte identifizieren
- riskante Strukturdrift identifizieren

### Safety

- Keine destruktiven Änderungen ohne Freigabe.
- Keine externen Publish-/Release-Aktionen.
- Keine Dependency- oder Versionierungsaktionen.

---

## Output Format

### Compact Output für DAILY

DAILY darf dieses kompakte Format verwenden, solange keine Auto-Fix-Kandidaten, Backlog-Kandidaten oder Eskalationen vorliegen.

Wenn DAILY Findings enthält, bleibt der Kopf kompakt, aber die betroffenen Pflichtsektionen aus dem Vollformat müssen ergänzt werden:

- `## Auto-Fix-Kandidaten` plus Gate/Sicherheits-Checkpoint/Freigabe, wenn Auto-Fix-Kandidaten vorhanden sind.
- `## Backlog-Kandidaten`, wenn ein Finding größer als DAILY ist. DAILY schreibt diese Kandidaten nicht selbst ins Backlog.
- `## Eskalationen`, wenn eine Bewertung nicht deterministisch möglich ist.

```markdown
# SYSTEM HEALTH REPORT

## Modus
- DAILY
- **Modus automatisch gewählt:** JA | NEIN

## Systemhealth
- **Score:** <0-100>%
- **Ampel:** GRÜN | GELB | ROT
- **Statussatz:** <ein klarer Satz, ob das System heute nutzbar ist>

## Kurzbefund
- **Findings:** <n>
- **Auto-Fix-Kandidaten:** <n>
- **Backlog-Kandidaten:** <n>
- **Eskalationen:** <n>
- **Scan-Abdeckung:** vollständig | teilweise, mit kurzer Begründung

## Klare Empfehlung
- **Empfohlene Aktion:** WEITERMACHEN | WEITERMACHEN MIT VORSICHT | JETZT FIXEN | BLOCKIERT | ESKALIEREN
- **Jetzt tun:** <ein konkreter nächster Schritt>

## Optionale Folgeaktion
- <konkreter optionaler Cleanup oder "Keine">
```

### Vollformat für WEEKLY, MONTHLY und DAILY mit Findings

```markdown
# SYSTEM HEALTH REPORT

## Modus
- DAILY | WEEKLY | MONTHLY

## Systemhealth
- **Score:** <0-100>%
- **Ampel:** GRÜN | GELB | ROT
- **Statussatz:** <ein klarer Satz, ob das System heute nutzbar ist>

## Zusammenfassung
- **Findings:** <n>
- **Auto-fix candidates:** <n>
- **Betroffene Auto-Fix-Artefakte:** <m>
- **Backlog items created/updated:** <n>
- **Ignored findings:** <n>
- **Escalations:** <n>

## Klare Empfehlung
- **Empfohlene Aktion:** WEITERMACHEN | WEITERMACHEN MIT VORSICHT | JETZT FIXEN | BLOCKIERT | ESKALIEREN
- **Warum:** <kurze Begründung>
- **Jetzt tun:** <ein konkreter nächster Schritt>
- **Nicht jetzt tun:** <konkrete Abgrenzung, falls relevant>

## Auto-Fix-Kandidaten
- **[Finding]:** <safe fix proposal>
  - **Risk:** LOW
  - **Requires approval:** YES

## Im Backlog ergänzt / aktualisiert
- **BACKLOG-XXX:** <title>
  - **Type:** TECH_DEBT | IMPROVEMENT | ENHANCEMENT | BUG
  - **Reason:** <reason>

## Backlog-Änderungen
- **Status:** JA | NEIN
- **Datei geändert:** documentation/backlog/BACKLOG.md | Keine
- **Items erstellt/aktualisiert:** <Liste oder "Keine">
- **Hinweis:** <"Änderung wurde bereits vorgenommen" oder "Eintrag ist nur vorgeschlagen und wurde nicht geschrieben">

## Backlog-Bewertung
- **BACKLOG-XXX:** <title>
  - **Wichtigkeit:** ROT | GELB | GRÜN
  - **Empfohlener Zeitpunkt:** sofort | nach aktuellem Feature | vor nächstem Release | irgendwann
  - **Warum wichtig:** <kurze Begründung>
  - **Risiko wenn ignoriert:** <konkretes Risiko oder "gering">

## Ignoriert
- **[Finding]:** <reason>

## Eskalationen
- **[Finding]:** <reason or none>

## Optionale Folgeaktion
- <konkreter optionaler Cleanup oder "Keine">

## Auto-Fix-Gate-Prüfung
- **Status:** PASS | BLOCKED
- **Geprüfte Kandidaten:** <n>
- **Hochgestufte Kandidaten:** <Liste oder "Keine">
- **Pauschales JA erlaubt:** JA | NEIN
- **Grund:** <kurze Begründung>

## Sicherheits-Checkpoint vor Auto-Fix
- **Workspace-Status:** sauber | uncommitted changes vorhanden | unbekannt
- **Commit/Snapshot automatisch erstellt:** NEIN
- **Warum:** <kurze Begründung>
- **Rollback-Plan:** <konkreter Plan>
- **Empfehlung:** JA – zuerst Safety-Snapshot | NEIN – nur triviale LOW-Fixes ohne Snapshot | AUSWAHL verwenden | ABBRECHEN
- **Empfehlungsgrund:** <klare kurze Begründung>

## Freigabe erforderlich
- **Auto-Fix-Kandidaten:** <n>
- **Betroffene Artefakte:** <m>
- **Diese Maßnahmen würden bei Zustimmung ausgeführt:**
  1. **<Titel>:**
     - **Was passiert:** <konkrete Datei-/Ordneraktion>
     - **Betroffene Artefakte:** <konkrete Liste>
     - **Warum sicher:** <kurze Begründung>
     - **Risiko:** LOW
  2. **<Titel>:**
     - **Was passiert:** <konkrete Datei-/Ordneraktion>
     - **Betroffene Artefakte:** <konkrete Liste>
     - **Warum sicher:** <kurze Begründung>
     - **Risiko:** LOW

## Auto-Fix-Entscheidung
- **Frage:** Möchtest du diese Auto-Fixes jetzt ausführen?
- **Optionen:**
  1. JA – alle pauschal freigegebenen LOW-Kandidaten jetzt ausführen, nur wenn `Pauschales JA erlaubt: JA` und Auto-Fix Execution Gating erfüllt ist
  2. NEIN – nichts ausführen, nur Report behalten
  3. AUSWAHL – einzelne Kandidaten auswählen
- **Antwortformat:** JA | NEIN | AUSWAHL, oder nur NEIN | AUSWAHL wenn `Pauschales JA erlaubt: NEIN`

## Abschlussstatus
- **Dateien geändert:** <Liste oder "Keine">
- **Was wurde gemacht:** <kurz>
- **Ergebnis:** <GRÜN/GELB/ROT + klare operative Bedeutung>
```

---

## Final Safety Check

Before completing:

1. Ensure no feature behavior was changed.
2. Ensure no large refactor was performed.
3. Ensure no release/version action was performed.
4. Ensure any Backlog updates use valid `BACKLOG-XXX` IDs.
5. Ensure any auto-fix was either only proposed or explicitly approved.
6. Ensure unclear findings stopped with `SYSTEM HEALTH ESCALATION REQUIRED`.
