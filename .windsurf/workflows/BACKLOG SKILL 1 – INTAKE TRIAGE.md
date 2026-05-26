---
description: BACKLOG SKILL 1 – Intake Triage | Model: SWE 1.6
---

# BACKLOG SKILL 1 – INTAKE TRIAGE

**Required Model:** SWE 1.6  
**Purpose:** Nimmt rohe Bugs, Änderungswünsche, Ergänzungen und Verbesserungen auf, klassifiziert sie und schreibt einen strukturierten Backlog-Eintrag.  
**Do not use this skill for:** Priorisierung, Implementation, Release oder Architekturentscheidungen.

---

## Ziel

Dieser Skill ist der Eingangspunkt für kleine Janus-Themen, die noch keine vollständige Feature-Spec sind.

Er verarbeitet Nutzereingaben wie:

- "Ich habe einen Bug: XY funktioniert nicht."
- "Ich möchte die Chat-Formatierung ändern."
- "Bitte ergänze eine kleine Funktion zu einem bestehenden Feature."
- "Dieses Verhalten ist unklar oder nervig."

Er erzeugt oder aktualisiert ausschließlich Backlog-Einträge in:

```text
documentation/backlog/BACKLOG.md
```

---

## Hard Rules

- Keine Code-Implementation.
- Keine Architekturentscheidungen.
- Keine direkte Übergabe an Skill 1–8 ohne Backlog-Eintrag.
- Keine Priorisierung mehrerer Items; das ist Backlog Skill 2.
- Keine Handoff-Datei für die Diamond-Pipeline; das ist Backlog Skill 3 im Modus `SELECTED_HANDOFF`.
- Fehlende Informationen aktiv und konkret beim Nutzer anfordern.
- Backlog-Einträge müssen artefaktbasiert und später nachvollziehbar sein.
- Wenn die Anfrage mehrere unabhängige Themen enthält, in mehrere Backlog-Items aufteilen oder den Nutzer um Auswahl bitten.
- DONE-Items werden nicht reaktiviert; spätere Probleme, Änderungen oder Regressionen zu erledigten Items werden immer als neues Backlog-Item aufgenommen.

---

## Klassifikation

Klassifiziere jeden Eingang als genau einen Primärtyp:

```text
BUG
CHANGE
ENHANCEMENT
IMPROVEMENT
TECH_DEBT
UNCLEAR
```

Definition:

- **BUG:** Etwas funktioniert nicht wie erwartet oder erzeugt Fehler.
- **CHANGE:** Bestehendes Verhalten soll anders werden.
- **ENHANCEMENT:** Bestehendes Feature soll klein erweitert werden.
- **IMPROVEMENT:** Qualitäts-, UX- oder Stabilitätsverbesserung ohne neues Kernverhalten.
- **TECH_DEBT:** Wartbarkeit, Cleanup, Tests, Struktur.
- **UNCLEAR:** Ziel, erwartetes Verhalten oder Scope fehlen.

---

## Pflichtinformationen pro Typ

### BUG

Erforderlich:

- Erwartetes Verhalten
- Tatsächliches Verhalten
- Reproduktionsschritte
- Betroffener Bereich
- Backend-Log, falls Backend/API betroffen
- Frontend-Konsole, falls UI betroffen
- Screenshot oder Screen Recording, falls visuell sichtbar
- Zeitpunkt/Version, falls relevant

### CHANGE

Erforderlich:

- Aktuelles Verhalten
- Gewünschtes Verhalten
- Betroffene Ansicht/Funktion
- Beispiel oder Screenshot, falls UI betroffen
- Akzeptanzkriterien

### ENHANCEMENT

Erforderlich:

- Bestehendes Feature
- Gewünschte Ergänzung
- Grenzen: was ist ausdrücklich out of scope?
- Akzeptanzkriterien
- Mögliche Nutzerwirkung

### IMPROVEMENT / TECH_DEBT

Erforderlich:

- Warum ist die Änderung sinnvoll?
- Betroffener Bereich
- Risiko, falls bekannt
- Validierbares Ergebnis

---

## Backlog-Datei

Pfad:

```text
documentation/backlog/BACKLOG.md
```

Wenn die Datei fehlt, erstelle sie mit diesen Abschnitten:

```markdown
# Janus Backlog

## NEEDS INFO

## READY

## IN PROGRESS

## DONE

## BLOCKED
```

---

## Backlog-ID-Regel

Neue Items erhalten fortlaufende IDs:

```text
BACKLOG-001
BACKLOG-002
BACKLOG-003
```

Wenn vorhandene IDs existieren, verwende die nächste freie Nummer.

---

## Follow-up-Regel für DONE-Items

Prüfe bei jeder neuen Eingabe, ob das beschriebene Problem, die Änderung oder Ergänzung ein Follow-up zu einem vorhandenen `DONE` Item ist.

Wenn ein Follow-up zu einem `DONE` Item erkannt wird:

- Erstelle trotzdem immer ein neues Backlog-Item mit neuer ID.
- Verschiebe das ursprüngliche `DONE` Item nicht zurück nach `READY` oder `IN PROGRESS`.
- Ergänze im neuen Item einen Verweis:
  - `- **Follow-up zu:** BACKLOG-XXX – <Titel des erledigten Items>`
- Ergänze im ursprünglichen `DONE` Item einen reinen Rückverweis, ohne den Status zu ändern:
  - `- **Follow-ups:**`
  - `  - YYYY-MM-DD – BACKLOG-YYY – <Titel des neuen Follow-up Items>`
- Setze `Aktualisiert` beim ursprünglichen `DONE` Item auf das Datum des Rückverweises.

Wenn die Follow-up-Zuordnung unsicher ist:

- Erstelle das neue Item ohne Rückverweis.
- Vermerke die mögliche Beziehung unter `Notizen`.
- Frage nicht mehrere alte History-Items ab, außer der Nutzer nennt explizit ein konkretes Ursprungsthema.

---

## Status-Regel

Setze genau einen Status:

```text
NEEDS INFO
READY
IN PROGRESS
DONE
BLOCKED
```

- **NEEDS INFO:** Pflichtinformationen fehlen.
- **READY:** Ausreichend beschrieben für Backlog Skill 2 und optionales Routing-Enrichment.
- **IN PROGRESS:** Bereits durch Backlog Skill 3 im Modus `SELECTED_HANDOFF` an die Diamond-Pipeline übergeben.
- **DONE:** Durch Skill 7 abgeschlossen.
- **BLOCKED:** Nicht umsetzbar ohne externe Entscheidung oder Abhängigkeit.

---

## Eintragsformat

Jeder Eintrag muss exakt diese Struktur verwenden:

```markdown
### BACKLOG-XXX – <kurzer Titel>

- **Typ:** BUG | CHANGE | ENHANCEMENT | IMPROVEMENT | TECH_DEBT | UNCLEAR
- **Status:** NEEDS INFO | READY | IN PROGRESS | DONE | BLOCKED
- **Quelle:** User Intake | Screenshot | Log | Audit | Manual Test | Other
- **Erstellt:** YYYY-MM-DD
- **Aktualisiert:** YYYY-MM-DD
- **Kurzbeschreibung:** <1-3 Sätze>
- **Erwartetes Verhalten:** <falls relevant>
- **Tatsächliches Verhalten:** <falls relevant>
- **Reproduktion / Kontext:** <Schritte, Kontext, Beispiel>
- **Betroffener Bereich:** <UI/API/Backend/Frontend/Electron/Doku/Unklar>
- **Nachweise:** <Logs, Screenshots, Konsolenausgabe, Dateien oder "fehlt">
- **Akzeptanzkriterien:**
  - [ ] <prüfbares Kriterium>
- **Fehlende Informationen:**
  - <konkrete Frage oder "Keine">
- **Notizen:** <optional>
```

---

## Output bei fehlenden Informationen

Wenn Informationen fehlen, aktualisiere das Item unter `NEEDS INFO` und gib aus:

```markdown
# BACKLOG ITEM NEEDS INFO

## Item
- **ID:** BACKLOG-XXX
- **Titel:** <Titel>
- **Typ:** <Typ>

## Fehlende Informationen
- **[Info]:** <warum benötigt>

## Bitte liefere als Nächstes
<konkrete Copy-Paste-Anfrage an den Nutzer>
```

---

## Output bei Ready

Wenn der Eintrag ausreichend ist, verschiebe ihn nach `READY` und gib aus:

```markdown
# BACKLOG ITEM READY

## Item
- **ID:** BACKLOG-XXX
- **Titel:** <Titel>
- **Typ:** <Typ>
- **Status:** READY

## Nächster Schritt
Nutze:

/BACKLOG SKILL 2 – REVIEW PRIORISIERUNG
```

---

## Model Switch Rule

Wenn die Eingabe nicht deterministisch klassifizierbar ist oder mehrere gleich plausible Produktinterpretationen existieren:

```text
STOP
MODEL SWITCH REQUIRED: SWE 1.6 → GPT-5.5
```

Gib eine kurze Begründung und die konkrete Klärungsfrage aus.
