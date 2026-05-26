---
description: BACKLOG SKILL 2 – Review Priorisierung | Model: GPT-5.5
---

# BACKLOG SKILL 2 – REVIEW PRIORISIERUNG

**Required Model:** GPT-5.5  
**Purpose:** Zeigt offene Backlog-Punkte kostenoptimiert und qualitätsgesichert, bewertet Wichtigkeit, Risiko, Aufwand und Umsetzungsreife und gibt einen Auswahl-Handoff für Backlog Skill 3.  
**Do not use this skill for:** Intake neuer roher Bugs, Implementation, Codeänderungen oder direkte Diamond-Ausführung.

---

## Ziel

Dieser Skill ist das Bewertungs- und Auswahl-Gate für offene Backlog-Items.

Er liest:

```text
documentation/backlog/BACKLOG.md
```

und zeigt dem Nutzer eine klare, priorisierte Liste.

Der Skill ist GPT-5.5-basiert, aber standardmäßig **kostenoptimiert**: Er bewertet nicht jedes Mal den gesamten Backlog neu, sondern nutzt einen Delta-/Cache-first Modus. Tiefe GPT-Bewertung erfolgt nur für neue, geänderte, unklare oder Top-kandidatenrelevante offene Items.

---

## Hard Rules

- Keine Code-Implementation.
- Keine Backlog-Items ohne Nutzerentscheidung in die Umsetzung geben.
- Keine Handoff-Dateien für Skill 1–8 erzeugen; das ist `BACKLOG SKILL 3` im Modus `SELECTED_HANDOFF`.
- Keine Routing-Entscheidung in die Diamond-Pipeline treffen; fehlende `Entry Point` Felder ergänzt `BACKLOG SKILL 3` im Modus `ROUTING_ENRICHMENT`.
- Keine erledigten Items aus `DONE` als offen anzeigen.
- `NEEDS INFO` Items dürfen nicht als umsetzungsbereit markiert werden.
- Bewertungen müssen begründet sein.
- Wenn ein Item kritisch oder riskant ist, klar auf Blocker und Risiko hinweisen.
- Standardmodus ist inkrementell und kostenoptimiert; vollständige Neubewertung ist nur erlaubt, wenn ein Full Review explizit angefordert wird oder die Review-Basis inkonsistent ist.
- Bereits stabil bewertete unveränderte Items dürfen nicht tief neu analysiert werden; sie werden mit ihrer bisherigen Bewertung übernommen und nur gegen neue Top-Kandidaten verglichen.
- GPT-5.5-Analysebudget muss zuerst auf Entscheidungsqualität gehen: neue/geänderte Items, READY-Items mit hoher Wirkung, riskante Items und die finale Next-Best-Auswahl.
- `DONE` Items dürfen nur für Zähl-/Status-Konsistenz geprüft werden, nicht inhaltlich analysiert werden.
- Die Felder `Wichtigkeit`, `Umsetzungsrisiko`, `Aufwand`, `Umsetzungsreife` und `Empfehlung` sind der persistente Bewertungs-Cache.
- Bereits vollständig bewertete offene Items dürfen im DELTA-Modus nicht erneut tief bewertet werden, solange Status, Kurzbeschreibung, Erwartetes/Tatsächliches Verhalten, Akzeptanzkriterien und Fehlende Informationen unverändert wirken.
- Neue oder geänderte Bewertungen müssen direkt in `documentation/backlog/BACKLOG.md` beim jeweiligen Item gespeichert werden.
- Wenn alle offenen Items vollständig bewertet und nicht erkennbar geändert sind, muss der Skill `Deep Reviewed: 0` ausgeben und die vorhandenen Bewertungen nur kompakt übernehmen.

---

## Input

Standardaufruf:

```text
/BACKLOG SKILL 2 – REVIEW PRIORISIERUNG
```

Optional:

```text
Fokus: Bugs | UI | Release | kleine Aufgaben | hohe Priorität | READY only
Modus: DELTA | FULL
Max Deep Review: <n>
```

Default:

```text
Modus: DELTA
Max Deep Review: 5
```

`FULL` ist teuer und nur sinnvoll bei Strategiewechsel, großer Backlog-Umstrukturierung, beschädigter Review-Basis oder explizitem Wunsch nach vollständiger Neubewertung.

---

## Kostenoptimierter Review-Modus

### Default: DELTA Review

Im Standardmodus MUSS der Skill so arbeiten:

1. **Status-Sichtung**
   - Zähle offene Items aus `READY`, `NEEDS INFO` und `BLOCKED`.
   - Ignoriere `DONE` für inhaltliche Bewertung.
   - Erkenne Duplikate, falsch einsortierte Statusblöcke oder Items mit widersprüchlichem Status.

2. **Item-Karten statt Vollanalyse**
   - Arbeite pro offenem Item nur mit kompakten Karten:
     - ID
     - Titel
     - Typ
     - Status
     - Aktualisiert
     - Kurzbeschreibung
     - Betroffener Bereich
     - Fehlende Informationen
     - Akzeptanzkriterien-Kurzcheck
   - Lange Nachweise, alte Chattexte und historische Notizen nur lesen, wenn sie für Risiko/Readiness entscheidend sind.

3. **Deep-Review-Auswahl**
   - Tief bewertet werden maximal `Max Deep Review` Items.
   - Im DELTA-Modus dürfen nur Items tief bewertet werden, wenn mindestens eine Bedingung erfüllt ist:
     - Mindestens eines der Cache-Felder `Wichtigkeit`, `Umsetzungsrisiko`, `Aufwand`, `Umsetzungsreife`, `Empfehlung` fehlt.
     - Status, Kurzbeschreibung, Erwartetes/Tatsächliches Verhalten, Akzeptanzkriterien oder Fehlende Informationen wurden seit der letzten Bewertung erkennbar geändert.
     - Status und Abschnitt widersprechen sich oder die vorhandene Bewertung ist offensichtlich inkonsistent.
     - Der Nutzer fordert `Modus: FULL` oder einen expliziten Fokus, der eine Neubewertung dieses Items nötig macht.
   - Vollständig bewertete und unveränderte Items werden nicht neu analysiert, sondern aus den Cache-Feldern übernommen.
   - Priorität für Deep Review:
     1. Neue oder seit letzter Review geänderte offene Items
     2. `READY` Bugs mit potenziellem Release-/Core-Flow-Impact
     3. Items mit hoher Unsicherheit, widersprüchlichem Status oder unklarer Akzeptanz
     4. Kandidaten für "Nächster sinnvoller Punkt"
   - Unveränderte, eindeutig niedrig priorisierte Items werden nur kompakt übernommen.

4. **Qualitätsvergleich**
   - Nach der Deep-Review-Auswahl MUSS GPT-5.5 die besten Kandidaten gegeneinander vergleichen.
   - Die finale Empfehlung darf nicht nur nach Wichtigkeit gehen, sondern muss Wichtigkeit, Risiko, Aufwand, Reife und Pipeline-Kosten abwägen.

5. **Transparenz**
   - Output MUSS angeben:
     - Review-Modus
     - Anzahl tief bewerteter Items
     - Anzahl übernommener/kompakt geprüfter Items
     - Ob Full Review empfohlen ist
     - Ob Bewertungsfelder in `BACKLOG.md` geschrieben wurden

6. **Persistenzpflicht**
   - Wenn ein Item tief bewertet wird, MUSS der Skill die fünf Cache-Felder direkt unter dem Item in `documentation/backlog/BACKLOG.md` ergänzen oder aktualisieren.
   - Wenn keine Bewertung geändert wurde, MUSS der Skill ausdrücklich melden: `Bewertungs-Cache: unverändert`.
   - Der Skill darf nicht nur Chat-Output erzeugen, wenn neue Bewertungen fehlen; ohne Backlog-Persistenz wäre der DELTA-Cache wirkungslos.

### Full Review Trigger

Führe eine vollständige Neubewertung nur durch, wenn mindestens eine Bedingung zutrifft:

- Nutzer fordert `Modus: FULL`.
- Backlog-Struktur ist inkonsistent genug, dass DELTA keine sichere Empfehlung erlaubt.
- Mehr als 10 offene Items sind neu/geändert.
- Mehrere `CRITICAL`/Release-Blocker konkurrieren.
- Der Nutzer plant eine größere Roadmap-/Release-Entscheidung.
- Letzte Review-Basis ist unbekannt und die aktuelle Auswahl hätte hohes Release-/Security-/Datenverlust-Risiko.

Wenn FULL sinnvoll, aber nicht zwingend ist, nicht automatisch teuer ausführen, sondern klar empfehlen:

```markdown
## Kostenhinweis
- **Empfehlung:** DELTA reicht aus | FULL empfohlen
- **Warum:** <kurze Begründung>
```

---

## Bewertungsdimensionen

Bewerte jedes offene Item nach:

```text
Wichtigkeit: LOW | MEDIUM | HIGH | CRITICAL
Umsetzungsrisiko: LOW | MEDIUM | HIGH
Aufwand: XS | S | M | L | XL
Umsetzungsreife: READY | NEEDS INFO | BLOCKED
Empfehlung: DO NOW | SCHEDULE | NEEDS INFO FIRST | DEFER | DO NOT START
```

### Wichtigkeit

- **CRITICAL:** Blockiert Kernfunktion, Datenverlust, Release-Blocker, Security.
- **HIGH:** Stark sichtbarer Bug oder wichtiger Nutzerflow betroffen.
- **MEDIUM:** Spürbare Verbesserung oder begrenzter Bug.
- **LOW:** Nice-to-have, kosmetisch, geringe Nutzerwirkung.

### Umsetzungsrisiko

- **HIGH:** Persistenz, Migration, Auth/Security, Release, IPC, globale State-Änderung.
- **MEDIUM:** Mehrere Module, API/UI-Kopplung, Testabhängigkeiten.
- **LOW:** Lokale UI-/Text-/kleine Validierungsänderung.

### Aufwand

- **XS:** sehr kleine lokale Änderung.
- **S:** kleiner Task mit klarer Validierung.
- **M:** mehrere Dateien oder Tests.
- **L:** mehrere Subsysteme oder unklare Kantenfälle.
- **XL:** zu groß für direkten Backlog-Handoff; benötigt vollständige Spec.

---

## Sortierung

Zeige offene Items in der ausführlichen Anzeige nach Kategorien gruppiert:

1. `BUG`
2. `CHANGE`
3. `ENHANCEMENT`
4. `IMPROVEMENT`
5. `TECH_DEBT`
6. `UNCLEAR`

Innerhalb jeder Kategorie sortiere:

1. `CRITICAL` und `HIGH` mit `READY`
2. kleine risikoarme `READY` Items
3. wichtige `NEEDS INFO` Items mit konkreten fehlenden Informationen
4. `BLOCKED` Items

Wenn eine Kategorie keine offenen Items enthält, darf sie ausgelassen werden.

Nach der ausführlichen kategorisierten Anzeige MUSS eine kompakte Zusammenfassung folgen, ebenfalls nach Kategorien gruppiert.

Die kompakte Zusammenfassung MUSS je Item enthalten:

- Ampel: `🔴` kritisch/sofort, `🟠` hoch, `🟡` mittel, `🟢` niedrig
- ID und Titel
- Status
- Kurzempfehlung: `DO NOW`, `SCHEDULE`, `NEEDS INFO FIRST`, `DEFER`, `DO NOT START`

Abschließend MUSS eine klare Empfehlung stehen, welches konkrete Backlog-Item als Nächstes angegangen werden sollte.

---

## Output-Format

```markdown
# BACKLOG REVIEW

## Zusammenfassung
- **Review-Modus:** DELTA | FULL
- **Deep Reviewed:** <n>
- **Kompakt geprüft/übernommen:** <n>
- **Full Review empfohlen:** JA | NEIN
- **Open READY:** <n>
- **Needs Info:** <n>
- **Blocked:** <n>
- **Empfohlener nächster Punkt:** BACKLOG-XXX – <Titel>

## Priorisierte offene Punkte nach Kategorien

### BUG

#### 1. BACKLOG-XXX – <Titel>
- **Typ:** BUG | CHANGE | ENHANCEMENT | IMPROVEMENT | TECH_DEBT | UNCLEAR
- **Status:** READY | NEEDS INFO | BLOCKED
- **Wichtigkeit:** LOW | MEDIUM | HIGH | CRITICAL
- **Umsetzungsrisiko:** LOW | MEDIUM | HIGH
- **Aufwand:** XS | S | M | L | XL
- **Umsetzungsreife:** READY | NEEDS INFO | BLOCKED
- **Empfehlung:** DO NOW | SCHEDULE | NEEDS INFO FIRST | DEFER | DO NOT START
- **Begründung:** <kurz und konkret>
- **Fehlt noch:** <falls relevant>

### IMPROVEMENT

#### 2. BACKLOG-XXX – <Titel>
- **Typ:** BUG | CHANGE | ENHANCEMENT | IMPROVEMENT | TECH_DEBT | UNCLEAR
- **Status:** READY | NEEDS INFO | BLOCKED
- **Wichtigkeit:** LOW | MEDIUM | HIGH | CRITICAL
- **Umsetzungsrisiko:** LOW | MEDIUM | HIGH
- **Aufwand:** XS | S | M | L | XL
- **Umsetzungsreife:** READY | NEEDS INFO | BLOCKED
- **Empfehlung:** DO NOW | SCHEDULE | NEEDS INFO FIRST | DEFER | DO NOT START
- **Begründung:** <kurz und konkret>
- **Fehlt noch:** <falls relevant>

## Kompakte Übersicht nach Kategorien

### BUG
- **🔴 BACKLOG-XXX – <Titel>:** Status `<READY|NEEDS INFO|BLOCKED>`, Wichtigkeit `<LOW|MEDIUM|HIGH|CRITICAL>`, Empfehlung `<DO NOW|SCHEDULE|NEEDS INFO FIRST|DEFER|DO NOT START>`

### IMPROVEMENT
- **🟡 BACKLOG-XXX – <Titel>:** Status `<READY|NEEDS INFO|BLOCKED>`, Wichtigkeit `<LOW|MEDIUM|HIGH|CRITICAL>`, Empfehlung `<DO NOW|SCHEDULE|NEEDS INFO FIRST|DEFER|DO NOT START>`

## Empfehlung
- **Nächster sinnvoller Punkt:** BACKLOG-XXX – <Titel>
- **Warum:** <kurze Begründung mit Wichtigkeit, Risiko, Aufwand und Umsetzungsreife>

## Auswahl-Handoff
Wenn du zuerst fehlende Entry Points für das Dashboard ergänzen willst, nutze:

/BACKLOG SKILL 3 – EXECUTION HANDOFF

Mode: ROUTING_ENRICHMENT

Wenn du diesen Punkt direkt in die Umsetzung übergeben willst, nutze:

/BACKLOG SKILL 3 – EXECUTION HANDOFF

Mode: SELECTED_HANDOFF
Backlog Item:
BACKLOG-XXX
```

---

## Nutzerentscheidung

Wenn der Nutzer sagt:

```text
Wir gehen BACKLOG-XXX an.
```

antworte nicht mit Implementation, sondern mit exakt diesem Handoff:

```markdown
# BACKLOG SELECTION READY

## Gewähltes Item
- **ID:** BACKLOG-XXX
- **Titel:** <Titel>

## Nächster Schritt
Nutze:

/BACKLOG SKILL 3 – EXECUTION HANDOFF

Mode: SELECTED_HANDOFF
Backlog Item:
BACKLOG-XXX
```

---

## Blocker Handling

Wenn der Nutzer ein Item mit `NEEDS INFO` oder `BLOCKED` auswählt:

```markdown
# BACKLOG SELECTION BLOCKED

## Item
- **ID:** BACKLOG-XXX
- **Status:** NEEDS INFO | BLOCKED

## Warum nicht bereit
- <konkreter Grund>

## Nächster Schritt
Nutze BACKLOG SKILL 1 mit diesen Zusatzinfos:
- <konkrete Liste>
```
