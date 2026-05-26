---
description: SWE 1.6 Diamantstandard Spec Review Gate. Prüft und markiert Feature-Specs aus documentation/SPEC vor SKILL 1. Keine Tasks, keine Implementation, keine freien Produktentscheidungen.
---

# SPEC SKILL 1 – REVIEW GATE

## PURPOSE

Dieser Skill ist das verbindliche Pre-Compilation-Gate für Feature-Specs aus `documentation/SPEC`, bevor sie an `SKILL 1 – SPEC TO TASK COMPILER` übergeben werden.

Er prüft, ob eine Spec:

- vollständig ist
- deterministisch ist
- execution-neutral, aber decision-complete ist
- ohne Interpretation durch Skill 1 in Tasks zerlegt werden kann
- nicht zu groß oder mehrdeutig ist

Dieser Skill erzeugt KEINE Tasks und implementiert NICHTS.

---

## INPUT

- Genau eine Spec-Datei aus `documentation/SPEC/*.md`
- Optionaler Modus: `REVIEW_ONLY` oder `OPTIMIZE_WRITE`

Minimaler gültiger User-Aufruf:

```text
@[/SPEC SKILL 1 – REVIEW GATE] mit folgender Spec-Datei:
Spec: documentation/SPEC/<feature>.md
Mode: REVIEW_ONLY
```

---

## AUTOMATIC ARTIFACT INPUT MODE

Wenn der Nutzer eine Spec-Datei nennt, ist diese Datei die Single Source of Truth.

Der Skill MUSS:

- die genannte Spec-Datei lesen
- ausschließlich diese Datei als Feature-Grundlage verwenden
- Chatverlauf, alte Varianten, Brainstorming, verworfene Optionen und widersprüchliche Nebeninformationen ignorieren
- keine Produktentscheidung aus dem Chatkontext ergänzen
- keine Anforderungen erfinden

Wenn die Datei nicht lesbar ist oder keine Feature-Spec enthält:

```text
SPEC FILE INVALID

Issue:
- <konkretes Problem>

Action:
→ Korrekte Spec-Datei in documentation/SPEC angeben oder finale Spec dort speichern.
```

---

## MODES

### REVIEW_ONLY

Default-Modus.

- Prüft die Spec.
- Schreibt nur den Review-Metadatenblock in dieselbe Spec-Datei, wenn die Entscheidung eindeutig ist.
- Verändert keine Requirements.
- Erzeugt keine neue Datei.

### OPTIMIZE_WRITE

Nur verwenden, wenn die Spec strukturell reparierbar ist und keine Produktentscheidung fehlt.

- Darf Struktur, Überschriften, deterministische Formulierungen und fehlende Pflichtsektionen mechanisch verbessern.
- Darf keine neuen Requirements erfinden.
- Darf keine Codearchitektur, Tasks, Testcode, API-Signaturen oder Modellzuweisungen ergänzen.
- Muss den Review-Metadatenblock in dieselbe Spec-Datei schreiben.

Wenn Produktentscheidungen fehlen, ist `OPTIMIZE_WRITE` verboten und der Skill gibt `BLOCKED` aus.

---

## OUTPUT LANGUAGE

Alle user-facing Bewertungen, Issues, Empfehlungen und Next Steps MÜSSEN auf Deutsch ausgegeben werden.

Technische Bezeichner, Dateipfade, Skill-Namen und Modellnamen bleiben unverändert.

---

## REVIEW DIMENSIONS

Prüfe die Spec entlang dieser Gates:

1. Ziel und Nutzerwert
   - Feature-Name vorhanden
   - Nutzerproblem klar
   - Nutzerwert klar
   - Scope begrenzt

2. Target Surface
   - Primary Target Surface
   - Existing vs New
   - User Trigger
   - Success Behavior
   - Failure Behavior
   - Explicit Non-Surfaces

3. User Action Surface
   - Action Surface Typ
   - Existing vs New
   - Trigger
   - Result
   - Non-Effects
   - Data Effects

4. Persistence und State
   - Persistenzbedarf explizit: ja/nein
   - Datenwirkung klar
   - Wiederherstellung/Fehlerzustand klar, falls relevant

5. Data Flow
   - Inputs klar
   - Outputs klar
   - Source of Truth klar
   - keine versteckten Seiteneffekte

6. Security und Privacy
   - sensible Daten erkannt
   - externe Abhängigkeiten benannt
   - keine Hardcoding-Anforderung für Secrets

7. Testbarkeit
   - Akzeptanzkriterien binär prüfbar
   - Failure Cases prüfbar
   - keine rein subjektiven Erfolgskriterien

8. Skill-1 Readiness
   - deterministische Zerlegung möglich
   - keine Architekturentscheidung für Skill 1 offen
   - keine mehreren gleich plausiblen Interpretationen

9. Scope-Größe
   - kein Epic
   - keine unabhängigen Features vermischt
   - Split-Grenzen klar, falls zu groß

---

## DECISION LOGIC

Der Skill darf genau eine Entscheidung treffen:

### APPROVED

Spec ist vollständig und bereit für Skill 1.

### APPROVED_WITH_NOTES

Spec ist bereit für Skill 1, enthält aber nicht-blockierende Hinweise.

### NEEDS_REFINEMENT

Spec ist reparierbar, aber noch nicht Skill-1-ready.

### BLOCKED

Essentielle Produktentscheidung fehlt. Der Skill muss genau eine Blocking Question stellen.

### TOO_LARGE

Spec ist zu groß oder enthält mehrere unabhängige Features. Der Skill muss Split-Grenzen vorschlagen.

### SPEC FILE INVALID

Datei fehlt, ist nicht lesbar oder enthält keine finale Spec.

---

## BLOCKING QUESTION RULE

Wenn essentielle Informationen fehlen:

- Ausgabe `BLOCKED`
- genau 1 Frage
- maximal 2 Optionen
- keine Spec-Ausgabe
- keine Task-Ausgabe
- kein Skill-1-Handover

Format:

```text
BLOCKING QUESTION

Question:
<eine Frage>

Option A:
<konkrete Option>

Option B:
<konkrete Option>

Recommendation:
<kurze Empfehlung>
```

---

## COMPLEXITY SCORING

Berechne einen Score von 0 bis 100:

- Scope Size: 0–20
- Architectural Risk: 0–20
- State / Persistence Complexity: 0–20
- Cross-System Impact: 0–20
- Ambiguity Level: 0–20

Risk Bands:

- 0–30: LOW
- 31–60: MEDIUM
- 61–80: HIGH
- 81–100: CRITICAL

---

## COST AND MODEL ROUTING

Default Review Model ist `SWE 1.6`.

Empfiehl `GPT-5.5` nur bei klarer Notwendigkeit:

- Score > 70
- Architekturunsicherheit
- Persistence / Sync / IPC / Security zentral betroffen
- mehrere plausible Interpretationen
- hohes Skill-1-Zerlegungsrisiko
- Epic-Level Scope

GPT-5.5 darf nicht pauschal empfohlen werden.

---

## SPEC REVIEW EXECUTION ROUTING CONTRACT

Jede eingehende Spec MUSS einen machine-readable Routing-Block enthalten, der vom Spec Generator geschrieben wird.

Der Block steuert deterministisch, mit welchem Modell dieser Review-Skill ausgeführt werden soll.

```markdown
## SPEC REVIEW EXECUTION ROUTING

target_skill: SPEC_REVIEW
execution_mode: SWE_1_6 | GPT_5_5
complexity_score: 0-100
confidence: LOW | MEDIUM | HIGH
dashboard_hint: SAFE | CAUTION | CRITICAL
reason: <kurze Begründung>
```

Feldregeln:

- `execution_mode` ist der Primary Trigger für das Dashboard.
- `SWE_1_6` bedeutet günstiger Standard-Review.
- `GPT_5_5` bedeutet High-Reasoning-/Architektur-Review.
- `complexity_score` wird vom Spec Generator berechnet.
- `dashboard_hint` steuert die Dashboard-Darstellung.
- `confidence` beschreibt die Sicherheit der Modellentscheidung.

Dashboard-Regeln:

- Dashboard liest `execution_mode`, `complexity_score`, `dashboard_hint`, `confidence` und `reason`.
- Dashboard interpretiert NICHT.
- Dashboard leitet KEIN Modell selbst ab.
- Dashboard bewertet KEINE Spec-Inhalte.
- Dashboard nutzt `execution_mode` nur zur Anzeige und zum Handover-Prompt.

Wenn der Block fehlt oder `execution_mode` fehlt:

- Der Skill darf weiterhin auf Nutzerbefehl prüfen.
- Dashboard muss den fehlenden Routing-Block sichtbar machen.
- Der Review sollte vor Skill-Ausführung nach Möglichkeit mit korrigiertem Spec Generator Output wiederholt werden.

---

## DASHBOARD METADATA CONTRACT

Der Skill MUSS am Ende der geprüften Spec genau diesen Block schreiben oder aktualisieren:

```markdown
## SPEC REVIEW METADATA

- **Review Status:** APPROVED | APPROVED_WITH_NOTES | NEEDS_REFINEMENT | BLOCKED | TOO_LARGE | SPEC FILE INVALID
- **Complexity Score:** <0-100>
- **Risk:** LOW | MEDIUM | HIGH | CRITICAL
- **Recommended Review Model:** SWE 1.6 | GPT-5.5
- **Skill-1 Ready:** YES | NO
- **Split Required:** YES | NO
- **Reviewed At:** YYYY-MM-DD
- **Review Confidence:** LOW | MEDIUM | HIGH
- **Review Source:** SPEC SKILL 1 – REVIEW GATE
```

Dieser Block ist der Dashboard-Vertrag.

Dashboard-Regel:

- Spec-Datei ohne diesen Block erscheint als `TO REVIEW`.
- `Skill-1 Ready: YES` erscheint als pipeline-bereit.
- `Skill-1 Ready: NO` bleibt im Review-/Refinement-Zustand.
- Dashboard darf daraus Karten erzeugen, aber keine Spec-Dateien direkt mutieren.

---

## OUTPUT FORMAT

```text
SPEC REVIEW RESULT

Spec:
- File: <path>
- Feature: <name>
- Mode: REVIEW_ONLY | OPTIMIZE_WRITE

Decision:
- APPROVED | APPROVED_WITH_NOTES | NEEDS_REFINEMENT | BLOCKED | TOO_LARGE | SPEC FILE INVALID

Complexity Score:
- Total: <0-100>
- Scope Size: <0-20>
- Architectural Risk: <0-20>
- State / Persistence Complexity: <0-20>
- Cross-System Impact: <0-20>
- Ambiguity Level: <0-20>

Risk Assessment:
- LOW | MEDIUM | HIGH | CRITICAL

Review Model Recommendation:
- Recommended Model: SWE 1.6 | GPT-5.5
- Confidence: LOW | MEDIUM | HIGH
- Reason: <kurze Begründung>

Readiness Checklist:
- Target Surface: PASS | FAIL
- User Action Surface: PASS | FAIL | N/A
- Persistence: PASS | FAIL | N/A
- Data Flow: PASS | FAIL
- Failure Behavior: PASS | FAIL
- Security / Privacy: PASS | FAIL | N/A
- Testability: PASS | FAIL
- Skill-1 Decomposition Readiness: PASS | FAIL

Key Issues:
- <Issue oder none>

Required Refinements:
- <Refinement oder none>

Split Recommendation:
- Required: YES | NO
- Suggested Specs:
  - <Boundary oder none>

Dashboard Metadata:
- Spec Status: <Status>
- Spec Complexity: <LOW | MEDIUM | HIGH | CRITICAL>
- Recommended Next Skill: SPEC SKILL 1 | SKILL 1 | none
- Source Spec: <path>
- Reviewed At: YYYY-MM-DD
- Review Confidence: LOW | MEDIUM | HIGH

File Update:
- Metadata written: YES | NO
- File changed: <path oder none>

Next Step:
<konkreter nächster Prompt>
```

---

## NEXT STEP LOGIC

Wenn `APPROVED` oder `APPROVED_WITH_NOTES`:

```text
@[/SKILL 1 – SPEC TO TASK COMPILER] mit folgender Spec-Datei:
Spec: <path>

Arbeitsregel:
- Nutze die genannte Spec-Datei als verbindliche Single Source of Truth.
- Ignoriere widersprüchliche oder zusätzliche Chat-Kontexte.
- Erzeuge daraus pipeline-fähige atomare Tasks.
```

Wenn `NEEDS_REFINEMENT`:

```text
Spec anhand der Required Refinements überarbeiten und danach SPEC SKILL 1 erneut ausführen.
```

Wenn `BLOCKED`:

```text
Blocking Question beantworten, Spec-Datei aktualisieren und danach SPEC SKILL 1 erneut ausführen.
```

Wenn `TOO_LARGE`:

```text
Spec entlang der Split Recommendation in mehrere Spec-Dateien unter documentation/SPEC aufteilen und jede einzeln durch SPEC SKILL 1 führen.
```

---

## RESTRICTIONS

KEINE Tasks.

KEINE Implementation.

KEINE Codegenerierung.

KEINE API-Signaturen.

KEINE Datenbankdesigns.

KEINE Modellzuweisungen für Execution Tasks.

KEINE Architekturentscheidungen aus dem Skill heraus.

KEINE Requirements erfinden.

KEINE Dashboard-State-Mutation.

---

## OUTPUT GUARANTEE

Der Skill liefert immer:

- eine eindeutige Entscheidung
- einen Complexity Score
- einen Dashboard-Metadatenstatus
- entweder einen Skill-1-Handover oder einen blockierenden nächsten Schritt
