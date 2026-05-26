# TASK-071: Capability Empty-State Guidance Implementation

## Ziel
Erweitern des Empty-State in `help_skill.py` gemäß Spec "Capability Empty-State Chat Response Guidance" - ausführlichere, nutzerzentrierte Erklärung wenn keine Capability-Daten verfügbar sind.

## Beschreibung
Das Feature definiert das Chat-Verhalten von Janus, wenn Nutzer nach Fähigkeiten fragen aber keine Capability-Daten verfügbar sind. Statt einer kurzen technischen Meldung soll ein klarer, erklärender Empty-State im Chat ausgegeben werden, der:
- den Zustand verständlich macht
- mögliche Ursachen neutral einordnet
- beruhigende Hinweise zur Temporarität gibt
- Empfehlung zur erneuten Anfrage ausspricht

Die Änderung ist rein textbasiert im Chat-Kontext und verändert keine Daten oder Systemlogik.

## Files
- `backend/services/help_skill.py` (_handle_capability_overview Methode, Zeile 107-168)

## Impact-Analyse
- **Basiert auf:** Spec "Capability Empty-State Chat Response Guidance" (documentation/Planned Features/Capability Empty-State Guidance View.md)
- **Beeinflusst:** backend/services/help_skill.py (nur Text-Änderung, keine Logik-Änderung)
- **Risiko-Einschätzung:** LOW (Text-Änderung ohne Architekturentscheidungen, bestehende Logik bleibt unverändert)

## Steps

### Step 1: Empty-State Text gemäß Spec ersetzen
In `backend/services/help_skill.py`, Methode `_handle_capability_overview` (aktuell Zeile 122-129):

Aktuellen Fallback-Text durch ausführlichen Empty-State gemäß Spec Section 4 (Failure/Empty Surface Behavior) ersetzen:

**Aktuell:**
```python
if not capabilities:
    return HelpOutput(
        answer="Ich kann meine Fähigkeiten aktuell nicht zuverlässig anzeigen. Bitte versuche es später erneut.",
        suggestions=[],
        actions=[],
        source_category="capability_overview",
        fallback_used=True
    )
```

**Neu (gemäß Spec):**
```python
if not capabilities:
    empty_state_text = (
        "Aktuell kann ich meine Fähigkeiten leider nicht anzeigen. "
        "Dies liegt daran, dass die Capability-Daten entweder nicht geladen, "
        "nicht initialisiert oder nicht verfügbar sind. "
        "Dieser Zustand kann temporär sein – bitte versuche deine Anfrage später erneut."
    )
    return HelpOutput(
        answer=empty_state_text,
        suggestions=[],
        actions=[],
        source_category="capability_overview",
        fallback_used=True
    )
```

Der neue Text enthält alle Required Elements aus Spec Section 4:
- Klare Aussage, dass aktuell keine Fähigkeiten angezeigt werden können
- Neutrale Erklärung möglicher Ursachen (nicht geladen, nicht initialisiert, keine Daten verfügbar)
- Beruhigender Hinweis, dass der Zustand temporär sein kann
- Empfehlung, die Anfrage später erneut zu stellen

## Acceptance Criteria
- [ ] Empty-State wird im Chat ausgegeben wenn `capabilities` leer ist
- [ ] Empty-State enthält klare Aussage dass aktuell keine Fähigkeiten angezeigt werden können
- [ ] Empty-State enthält neutrale Erklärung möglicher Ursachen (nicht geladen, nicht initialisiert, keine Daten verfügbar)
- [ ] Empty-State enthält beruhigenden Hinweis dass der Zustand temporär sein kann
- [ ] Empty-State enthält Empfehlung die Anfrage später erneut zu stellen
- [ ] Keine UI-Komponenten oder Controls werden erzeugt
- [ ] Keine Datenveränderung oder Persistenz erfolgt
- [ ] Bestehende Capability-Antworten mit Daten bleiben unverändert

## Tests
- Unit Test: `_handle_capability_overview` mit leerer capabilities-Liste → Empty-State-Text enthält alle 4 Required Elements aus Spec Section 4
- Unit Test: `_handle_capability_overview` mit gefüllter capabilities-Liste → normale Capability-Übersicht wird ausgegeben (Non-Regression)
- Integration Test: Chat-Anfrage "Was kannst du?" ohne Capability-Daten → Empty-State wird im Chat angezeigt
- Code-Review: Keine UI-Komponenten, Buttons oder Persistenz-Änderungen in help_skill.py

## Model: SWE 1.6
**Reason:** Single-File Text-Erweiterung in bestehendem Python-Modul, deterministische Änderung ohne Architekturentscheidungen.

## Risiken
- Gering: Text-Änderung ohne Logik-Änderung, bestehende Tests sollten weiterhin passen
- Rückfall-Szenario: Wenn neuer Text zu lang ist, kann er bei Bedarf gekürzt werden

## Dependencies
- Keine
