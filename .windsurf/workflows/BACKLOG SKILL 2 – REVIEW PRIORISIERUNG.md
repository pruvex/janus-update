---
description: BACKLOG SKILL 2 – Review Priorisierung | Model: GPT-5.5
---

# BACKLOG SKILL 2 – REVIEW PRIORISIERUNG

**Required Model:** GPT-5.5  
**Purpose:** Zeigt offene Backlog-Punkte strukturiert, bewertet Wichtigkeit, Risiko, Aufwand und Umsetzungsreife und gibt einen Auswahl-Handoff für Backlog Skill 3.  
**Do not use this skill for:** Intake neuer roher Bugs, Implementation, Codeänderungen oder direkte Diamond-Ausführung.

---

## Ziel

Dieser Skill ist das Bewertungs- und Auswahl-Gate für offene Backlog-Items.

Er liest:

```text
documentation/backlog/BACKLOG.md
```

und zeigt dem Nutzer eine klare, priorisierte Liste.

---

## Hard Rules

- Keine Code-Implementation.
- Keine Backlog-Items ohne Nutzerentscheidung in die Umsetzung geben.
- Keine Handoff-Dateien für Skill 1–8 erzeugen; das ist Backlog Skill 3.
- Keine erledigten Items aus `DONE` als offen anzeigen.
- `NEEDS INFO` Items dürfen nicht als umsetzungsbereit markiert werden.
- Bewertungen müssen begründet sein.
- Wenn ein Item kritisch oder riskant ist, klar auf Blocker und Risiko hinweisen.

---

## Input

Standardaufruf:

```text
/BACKLOG SKILL 2 – REVIEW PRIORISIERUNG
```

Optional:

```text
Fokus: Bugs | UI | Release | kleine Aufgaben | hohe Priorität | READY only
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
Wenn du diesen Punkt umsetzen willst, nutze:

/BACKLOG SKILL 3 – EXECUTION HANDOFF

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
