# 💎 Diamond-Standard Skill-Entwicklung (V3.0 — Immune-System Compatible)

Dieses Dokument ist das verbindliche Gesetz für Janus. Es nutzt das **Zentralisierungsprinzip**: Komplexe Logik findet im `ToolExecutor` statt. Skills sind global, resilient und nahtlos integriert.

**V3.0 Änderungen:**
- Integration des DIAMOND SKILL CONTRACT (D20-D26)
- DIAGNOSE-ENGINE: Unterscheidung zwischen Modell-Fehlern und Skill-Fehlern
- Automatisches Benchmarking durch `/janus-maintenance` (kein manuelles Benchmarking mehr)
- **STRIKTES VERBOT:** Manuelle Änderungen an `model_routing.json` sind verboten

---

## TEIL 1: DIAMOND SKILL CONTRACT (D20-D26)

### 1.1 Output-Format-Kontrakt
Jeder Skill MUSS das folgende Output-Format einhalten:

```python
{
    "status": "success | error",
    "data": {...},  # Bei success: Ergebnis-Daten
    "error": {...}   # Bei error: Fehler-Details
}
```

**Regeln:**
- `status` ist obligatorisch und MUSS entweder "success" oder "error" sein
- Bei `status: "success"`: `data` MUSS enthalten sein, `error` MUSS fehlen
- Bei `status: "error"`: `error` MUSS enthalten sein, `data` KANN fehlen
- Keine gemischten States (z.B. "partial_success" ist verboten)

### 1.2 Global Default Validator
Der `ValidationEngine` in `backend/services/testing/validation.py` erzwingt diesen Kontrakt:
- `ValidationResult` mit `passed`, `validator_type`, `message`, `severity`
- Validatoren: `type_match`, `key_exists`, `contains`, `not_contains`, `regex`, `fuzzy_contains`, `not_crash`
- Multi-Rule-Validierung: Alle Regeln müssen bestehen

### 1.3 DIAGNOSE-ENGINE: Modell vs. Skill Unterscheidung
Das Immunsystem unterscheidet zwischen zwei Fehler-Quellen:

**Modell-Fehler:**
- Symptom: Hohe Latenz, Timeout, 429 Rate Limit, 500 Server Error
- Diagnose: Modell-Problem (z.B. Overload, Outage)
- Lösung: Diamond Routing → Automatischer Modell-Wechsel (D21-D22)

**Skill-Fehler:**
- Symptom: Falsche Daten, Halluzinationen, Logik-Fehler, Format-Breach
- Diagnose: Skill-Problem (z.B. Handler-Code, Validation-Logic)
- Lösung: Skill-Refactoring (manuelle Entwickler-Arbeit)

**Diagnose-Regeln:**
- Pass-Rate < 0.5 + Latenz OK → Skill-Problem (Code-Fix nötig)
- Pass-Rate < 0.5 + Latenz hoch → Modell-Problem (Routing-Wechsel)
- Pass-Rate ≥ 0.5 → System stabil (kein Eingriff nötig)

---

## TEIL 2: Die 8 Ebenen der Unzerstörbarkeit

### Ebene 0: Globaler Kontext & Standort
- **Awareness:** Skills passen sich automatisch an Land, Währung und Sprache des Nutzers an.

### Ebene 1: Funktionale Vision & Idempotenz
- **Nutzen:** Klarer Core-Task. Idempotenz garantiert: Gleicher Input + Ort = Gleicher Output.

### Ebene 2: Technischer Kontrakt (Input/Output)
- **Modelle:** Pydantic Input-Schema UND Output-Schema (zur zentralen Validierung).
- **DIAMOND CONTRACT:** Output MUSS {status, data, error} Format einhalten.

### Ebene 3: Logik, Resilience & Observability
- **Handler:** Liefert nur Rohdaten. Resilience (Timeout/Retry) wird zentral vom Executor gesteuert.

### Ebene 4: Metadaten & Benchmarking
- **Tiering:** `optimal_model_tier` wird durch **automatisches Benchmarking** ermittelt.
- **NEU:** Nutze `/janus-maintenance` Workflow für wöchentliche Kalibrierung (D20-D26).
- **VERBOTEN:** Manuelles Benchmarking mit `benchmark_skill.py`.

### Ebene 5: Sprach-Ebene (Grounding & Seamless UX)
- **Striktes Grounding:** Keine Halluzinationen.
- **No Meta-Talk:** Skills fordern den Nutzer niemals auf, andere Tools zu nutzen. Nötige Präzisierungen erfolgen durch interne Skill-Komposition.

### Ebene 6: Präsentations-Ebene (Renderer)
- **Autorität:** Renderer erzeugt Links/Bilder. Source-Awareness wählt Links passend zu LLM-Zitaten.

### Ebene 7: Benchmarking (Qualitätssicherung)
- **VERALTET:** Manuelles Benchmarking ist verboten.
- **NEU:** Automatisches Benchmarking durch `/janus-maintenance` Workflow.
- **Workflow:** 1) POST `/api/system/run-batch-tests` (Kalibrierung), 2) GET `/api/system/monitoring/summary` (Status)
- **Frequenz:** Wöchentlich zur Sicherung der statistischen Basis für Self-Healing.

### Ebene 8: Agentic Integration (Seamless Orchestration)
- Der Agentic Planner nutzt scharfe Skill-Beschreibungen für proaktive Ketten (z.B. erst Websearch, dann Price-Check).

---

## TEIL 3: IMMUNSYSTEM-REGELN (D20-D26)

### 3.1 STRIKTES VERBOT: Manuelle Routing-Änderungen
**VERBOTEN:** Manuelle Änderungen an `backend/config/model_routing.json`
**GRUND:** Das Immunsystem (D20-D26) verwaltet Routing automatisch basierend auf statistischer Kalibrierung.
**KONSEQUENZ:** Manuelle Eingriffe untergraben die Self-Healing-Mechanismen und können zu inkonsistenten Zuständen führen.

**ZULÄSSIG:**
- Änderungen an Skill-Code (Handler, Validation)
- Änderungen an Test-Blueprints (config/skill_tests/)
- Änderungen an Static Configs (config.json, model_catalog.json, etc.)

**NUR ÜBER IMMUNSYSTEM:**
- Modell-Zuweisungen (Primary, Fallback, Escalation)
- Pass-Rate Updates
- Latency-Updates

### 3.2 Self-Healing Cycle
Wenn ein Skill degradiert ist (pass_rate < 0.5), triggert das Immunsystem automatisch:
1. Diamond Routing Builder (D21) aggregiert historische Daten
2. Self-Heal Cycle (D22) wählt besseres Modell basierend auf Confidence
3. FIFO History Logging (D23) speichert Audit-Trail
4. Auto-Trigger (D24) mit Gates (Cooldown 6h, Lock, Health-Threshold)
5. Monitoring Aggregator (D25) überwacht System-Status

### 3.3 Diagnose-Workflow
Wenn ein Skill Probleme hat:
1. Prüfe `/api/system/monitoring/summary` → Health Snapshot
2. Wenn pass_rate < 0.5:
   - Latenz hoch → Modell-Problem (Routing-Wechsel automatisch)
   - Latenz OK → Skill-Problem (Code-Fix manuell)
3. Wenn pass_rate ≥ 0.5 → System stabil (kein Eingriff nötig)

---

## TEIL 4: Entwicklungs-Workflow (V3.0)

### 4.1 Neuer Skill erstellen
1. Skill-Definition in `backend/tools/` mit DIAMOND CONTRACT Output
2. Test-Blueprint in `config/skill_tests/` erstellen
3. Skill-Registry in `backend/services/registry/` aktualisieren
4. Initialer Test mit `/test-skill` Workflow
5. **NICHT:** Manuelles Benchmarking durchführen
6. **SONDERN:** `/janus-maintenance` Workflow für Kalibrierung nutzen

### 4.2 Skill optimieren
1. Handler-Code verbessern (Logik, Grounding)
2. Test-Blueprint anpassen (Validation Rules)
3. `/janus-maintenance` ausführen für neue Kalibrierung
4. `/api/system/monitoring/summary` prüfen für Status

### 4.3 Skill debuggen
1. `/debug-log` Workflow für Fehleranalyse
2. DIAGNOSE-ENGINE: Modell vs. Skill Unterscheidung
3. Bei Modell-Problem: Immunsystem löst automatisch
4. Bei Skill-Problem: Code-Refactoring nötig

---

## TEIL 5: Referenzen

### 5.1 Architektur-Dokumentation
- `documentation/architecture/JANUS_IMMUNE_SYSTEM.md` — SSOT für Routing-Änderungen (D20-D26)

### 5.2 Workflows
- `/janus-maintenance` — Wöchentliche Kalibrierung und Status-Check
- `/learning-report` — Trend-Analyse (Woche-zu-Woche)
- `/test-skill` — Deterministischer Skill-Test
- `/debug-log` — Fehleranalyse

### 5.3 API Endpoints
- `POST /api/system/run-batch-tests` — Kalibrierung (D20)
- `GET /api/system/monitoring/summary` — Status (D25)
- `POST /api/system/self-heal/auto` — Automatischer Self-Heal Trigger (D24)
- `GET /api/system/learning-report` — Trends (D14)

---

**Diese Version (V3.0) ist ab sofort verbindlich für alle Skill-Entwickler. Manuelles Benchmarking und manuelle Routing-Änderungen sind streng verboten.**
