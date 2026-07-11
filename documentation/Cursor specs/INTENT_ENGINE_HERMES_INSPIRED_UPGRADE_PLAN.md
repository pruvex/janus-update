# Janus Intent Engine Upgrade — Umsetzungsplan (Hermes-inspiriert)

**Version:** 1.0.0  
**Datum:** 2026-07-07  
**Zielgruppe:** Codex / Cursor / Janus Diamond Pipeline  
**Status:** READY FOR IMPLEMENTATION  
**Epic-ID:** `EPIC-INTENT-HERMES-001`  
**Bezug:** Ergänzt `MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md` (Memory-Layer), adressiert separat das Routing-Problem.

---

## 0. Executive Summary

### Problem

Die Janus `IntentEngine` (~1.980 Zeilen, 25+ Boolean-Flags) erkennt bei **sprachlicher Variation** oft falsch. Symptome:

- Kontaktfakten landen in News/Websearch statt Memory/Contact-Pfad (BACKLOG-108, 119)
- Pet-/Owner-Sätze werden falsch als Kontakt-Subject klassifiziert (BACKLOG-108, 116)
- Verb-Synonyme (`besitzt` vs. `hat`) fehlen → falscher Pfad (BACKLOG-110)
- Ambiguity-Block erzwingt Klärungsfragen statt korrekter Tool-Nutzung
- Jede neue Formulierung = neuer Regex-Patch

### Zielbild (Hermes-inspiriert, Janus-spezifisch)

**Nicht** Hermes-Level-Vereinfachung (das würde Domänen-Routing zerstören), sondern:

1. **Schichten statt 25 paralleler Flags**
2. **Auxiliary Classifier** (billiges LLM) für Action + Subject
3. **Regex-Freeze** — keine neuen Keyword-Listen mehr
4. **Negative Routing** — LLM darf entscheiden, wo Regex unsicher ist
5. **Confidence-Routing** statt hartem Ambiguity-Block

### Phasen-Übersicht

| Phase | Feature | Aufwand | Risiko | Erwarteter Accuracy-Gewinn* |
|-------|---------|---------|--------|----------------------------|
| **0** | Intent-Benchmark-Suite | 2–3 Tage | Niedrig | Messbarkeit (Baseline) |
| **1** | Action/Subject Classifier (Auxiliary) | 1,5–2 Wochen | Mittel | **+12–18 pp** Contact/Pet/Recall |
| **2** | Confidence-Routing (Ambiguity sanft) | 3–5 Tage | Mittel | **−30–50%** Fehl-Klärungsfragen |
| **3** | Regex-Freeze + Deprecation-Pfad | 2–3 Tage | Niedrig | Wartungskosten ↓ |
| **4** | Entity-First Routing (Pet/Contact/Owner) | 1–1,5 Wochen | Mittel | **+8–12 pp** Contact/Pet |
| **5** | `/skipdetect` Operator-Bypass | 1 Tag | Niedrig | UX bei Fehlern ↑ |

\* *pp = Prozentpunkte auf der jeweiligen Intent-Teilmenge, nicht global über alle Turns. Siehe Abschnitt 12.*

**Gesamt MVP (Phase 0–2):** ~3 Wochen  
**Gesamt inkl. 4–5:** ~5–6 Wochen

---

## 1. Ist-Zustand

### 1.1 Architektur heute

```
User Text
  → IntentEngine.detect_all_intents()     # 25+ boolesche Flags parallel
  → Veto-Kette (Calendar/Shopping/FS/Geo/Weather/News/Wikipedia)
  → detect_ambiguity_in_query()           # kann Tools komplett blockieren
  → execution_dispatcher / tool_selector  # Skill- und Tool-Routing
  → LLM
```

**Kern-Dateien:**

| Datei | Rolle |
|-------|-------|
| `backend/services/orchestrator/intent_engine.py` | Haupt-Engine, ~1.980 Zeilen |
| `backend/utils/intent_classifier.py` | Parallel-Heuristiken + `classify_intent_with_llm` (3 Klassen) |
| `backend/services/orchestrator/execution_dispatcher.py` | Ambiguity-Block, Model-Tier-Override |
| `backend/services/chat/tool_selector.py` | Skill-Auswahl nach Intent |
| `backend/services/orchestrator/entity_resolver.py` | Entity-Auflösung (teilweise) |

### 1.2 Was gut funktioniert (behalten!)

- Calendar vs. Shopping Veto-Hierarchie
- Calendar-Snapshot-Boost (`calendar_user_text_overlap_snapshot`)
- Personal-Recall → Websearch-Block (Precedence Guard)
- Fact-Telling → Memory/Contact-Pflichtpfad (wenn erkannt)
- Policy-Consent exakte Matches (`1/2/3`)
- Help-Intents mit Scope-Guard
- Video-Channel-Lock

### 1.3 Was systematisch scheitert

| Fehlerklasse | Beispiel | Ursache |
|--------------|----------|---------|
| **Verb-Varianz** | „besitzt einen Hund“ | Regex kennt nur „hat“ |
| **Subject-Verwechslung** | „Olis Hund Tasso ist …“ | Action+Subject in einem Pattern |
| **Recall vs. Web** | „Was weißt du über Chris?“ | `personal_recall` Regex zu eng |
| **News-FP** | Kontaktfakt mit Eigennamen | `news_on` schlägt Fact-Telling |
| **Ambiguity-Overblock** | Kurze Kontaktantworten | `disable_tools=True` |
| **Doppel-System** | Greeting in 2 Modulen | `intent_engine` + `intent_classifier` |

### 1.4 Hermes-Vergleich (Kurz)

| | Janus | Hermes |
|---|-------|--------|
| Intent-Tiefe | 25+ Domänen-Flags | ~4 Model-Routing-Klassen |
| Mechanismus | Regex-Wachstum | Negative Routing → LLM |
| Fehlerkosten | Hoch (falscher Skill) | Niedrig (falsches Modell) |
| LLM-Classifier | Minimal (3 Klassen, selten) | Geplant als Standard |
| Wartung | Jede Phrase = Patch | Wenig Code |

**Lesson:** Janus braucht Domänen-Routing, aber **nicht** als endlose Regex-Liste.

---

## 2. Soll-Architektur

```text
User Text + letzte 2 Turns + light context (calendar_snapshot yes/no)
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│ LAYER 1: SAFETY (deterministisch, immer)                  │
│  - Policy consent, Medical, PII, Personal-Recall-Web-Block│
└───────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│ LAYER 2: AUXILIARY CLASSIFIER (Nano/Flash, ~1 Call/Turn)  │
│  Output: { action, subject, confidence }                  │
│  action:  recall | tell_fact | mutate | create | search  │
│           | general | clarify                             │
│  subject: self | contact | pet | calendar | none          │
└───────────────────────────────────────────────────────────┘
        │
        ├─ confidence >= 0.80 → Routing aus Classifier
        ├─ 0.55–0.79        → Classifier + Regex-Vote (Merge)
        └─ < 0.55           → Regex-Fallback + LLM entscheidet Tools
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│ LAYER 3: DOMAIN VETO (bestehend, nur bei Konflikt)        │
│  Calendar/Shopping/FS/Geo/Weather — unverändert           │
└───────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│ LAYER 4: ENTITY RESOLVER (Pet → Owner → Contact)          │
│  Nur wenn subject in {contact, pet}                       │
└───────────────────────────────────────────────────────────┘
        │
        ▼
   Tool Selector / Dispatcher / LLM
```

### 2.1 Action/Subject statt 25 Flags

**Mapping (intern):**

| Classifier `action` | Ersetzt / konsolidiert |
|---------------------|------------------------|
| `recall` | `is_personal_recall`, Teile von `is_self_referential` |
| `tell_fact` | `is_fact_telling` |
| `mutate` | `is_calendar_mutation` |
| `create` | `is_calendar_creation` |
| `search` | `is_web_search`, `is_wikipedia`, `is_news` (mit Veto) |
| `general` | Smalltalk, Opinion, Greeting |
| `clarify` | Niedrige Confidence — Rückfrage |

| Classifier `subject` | Ersetzt |
|----------------------|---------|
| `contact` | Kontakt-Name-Extraktion in Regex |
| `pet` | Pet-led Patterns (`_FACT_TELLING_PATTERNS` Pet-Zweig) |
| `self` | `SELF_REF_REGEX`, „ich/mein“-Pfade |
| `calendar` | Kalender-Objekt erkannt |
| `none` | Kein spezifisches Subject |

**Wichtig:** Bestehende `IntentDetectionResult`-Felder bleiben als **kompatibilitäts-Schicht** (deprecated), werden aus Classifier + Veto befüllt.

---

## 3. Feature-Flags & Rollback

```python
# backend/config.py oder backend/services/orchestrator/intent_config.py

INTENT_BENCHMARK_MODE = os.getenv("INTENT_BENCHMARK_MODE", "false").lower() == "true"
INTENT_AUX_CLASSIFIER_ENABLED = os.getenv("INTENT_AUX_CLASSIFIER_ENABLED", "false").lower() == "true"
INTENT_CONFIDENCE_ROUTING_ENABLED = os.getenv("INTENT_CONFIDENCE_ROUTING_ENABLED", "false").lower() == "true"
INTENT_REGEX_FREEZE = os.getenv("INTENT_REGEX_FREEZE", "false").lower() == "true"
INTENT_ENTITY_FIRST_ENABLED = os.getenv("INTENT_ENTITY_FIRST_ENABLED", "false").lower() == "true"
INTENT_SKIP_DETECT_ENABLED = os.getenv("INTENT_SKIP_DETECT_ENABLED", "true").lower() == "true"
```

**Rollback:** Alle Flags `false` → exakt alter `detect_all_intents()`-Pfad.

---

## 4. Phase 0 — Intent-Benchmark-Suite (Pflicht vor allem anderen)

### 4.1 Ziel

Messbare Baseline — ohne Benchmark sind Accuracy-Prozentangaben Spekulation.

### 4.2 Aufwand / Risiko

| | Wert |
|---|------|
| Aufwand | **2–3 Tage** |
| Risiko | **Niedrig** |

### 4.3 Dateien

```
backend/tests/fixtures/intent_benchmark_cases.jsonl
backend/tests/test_intent_benchmark.py
backend/scripts/run_intent_benchmark.py
documentation/test-runs/INTENT_BENCHMARK_BASELINE.md
```

### 4.4 Benchmark-Format (JSONL)

```json
{
  "id": "INT-108-001",
  "user_text": "olis hund tasso ist ein podenco",
  "context": {"calendar_snapshot": false},
  "expected": {
    "action": "tell_fact",
    "subject": "pet",
    "is_fact_telling": true,
    "is_ambiguous": false,
    "must_not_route": ["news", "websearch"]
  },
  "source": "BACKLOG-108"
}
```

### 4.5 Mindest-Korpus (Start: 80–120 Cases)

| Cluster | Anzahl | Quelle |
|---------|--------|--------|
| Contact fact-telling | 20 | BACKLOG-108, 110, 120 |
| Contact recall | 15 | BACKLOG-119 |
| Pet-owner bridge | 15 | BACKLOG-108, 116 |
| Calendar vs shopping | 15 | Bestehende Tests |
| Ambiguity false-positive | 10 | Live-Debug |
| Greeting/smalltalk | 10 | `intent_classifier` |
| Geo/weather veto | 10 | BACKLOG-036 |
| Regression (bestehend grün) | 15 | `test_calendar_routing_fix.py` |

### 4.6 Akzeptanzkriterien

- [ ] `python -m backend.scripts.run_intent_benchmark` gibt Report: accuracy pro Cluster + gesamt
- [ ] Baseline dokumentiert in `INTENT_BENCHMARK_BASELINE.md`
- [ ] CI-fähig (kein LLM-Call in Phase-0-Tests — nur Regex-Pfad)

---

## 5. Phase 1 — Auxiliary Action/Subject Classifier (Kernstück)

### 5.1 Ziel

Ein billiger LLM-Call pro Turn ersetzt Regex-Wachstum für die Fehlerklassen Contact/Pet/Recall/Fact.

### 5.2 Aufwand / Risiko

| | Wert |
|---|------|
| Aufwand | **1,5–2 Wochen** |
| Risiko | **Mittel** |
| Kosten/Turn | ~50–150 Input-Tokens, ~20 Output-Tokens (Nano/Flash) |

### 5.3 Neue Dateien

```
backend/services/orchestrator/intent_aux_classifier.py
backend/services/orchestrator/intent_config.py
backend/data/schemas_intent.py                    # Pydantic: ActionSubjectResult
backend/tests/test_intent_aux_classifier.py
backend/tests/test_intent_action_subject_mapping.py
```

### 5.4 Classifier-Contract

```python
@dataclass
class ActionSubjectResult:
    action: Literal["recall", "tell_fact", "mutate", "create", "search", "general", "clarify"]
    subject: Literal["self", "contact", "pet", "calendar", "none"]
    confidence: float  # 0.0–1.0
    evidence: str      # max 80 chars, für Logs
    source: Literal["aux_llm", "regex_fallback", "merged"]
```

### 5.5 System-Prompt (Kern)

```text
Klassifiziere die Nutzeräußerung für einen deutschen Personal Assistant.

Antworte NUR als JSON:
{"action":"...","subject":"...","confidence":0.0-1.0,"evidence":"..."}

action:
- recall: Nutzer fragt nach gespeichertem Wissen über Person/Tier/Sich
- tell_fact: Nutzer teilt neuen Fakt mit (keine Frage)
- mutate: bestehenden Kalendertermin ändern/verschieben/löschen
- create: neuen Termin anlegen
- search: externe/aktuelle Infos (Wetter, News, Wikipedia, Web)
- general: Smalltalk, Meinung, Identitätsfrage an Assistenten
- clarify: echte Mehrdeutigkeit, keine sichere Zuordnung

subject:
- self, contact, pet, calendar, none

Regeln:
- "Was weißt du über X" → recall + contact
- "Olis Hund Tasso ist ein Podenco" → tell_fact + pet (NICHT contact)
- "Chris mag Pizza" → tell_fact + contact
- Eigennamen allein ≠ search
```

### 5.6 Integration in `detect_all_intents()`

```python
def detect_all_intents(self, user_text, *, calendar_snapshot=None):
    # LAYER 1: Safety (unverändert)
    safety = self._evaluate_safety_layer(user_text)

    # LAYER 2: Auxiliary (neu, wenn Flag)
    aux = None
    if INTENT_AUX_CLASSIFIER_ENABLED:
        aux = await intent_aux_classifier.classify(user_text, calendar_snapshot=calendar_snapshot)

    # LAYER 3: Legacy Regex (weiterhin, als Fallback/Vote)
    legacy = self._detect_all_intents_legacy(user_text, calendar_snapshot=calendar_snapshot)

    # Merge
    return self._merge_intent_results(legacy, aux, safety)
```

**Merge-Regeln:**

| Situation | Entscheidung |
|-----------|--------------|
| `aux.confidence >= 0.80` | Aux gewinnt für action/subject |
| `aux.confidence 0.55–0.79` | Aux action, subject aus Entity Resolver |
| `aux.confidence < 0.55` | Legacy Regex |
| Safety-Veto aktiv | Safety überschreibt immer |
| Aux vs. Legacy Konflikt | Log + niedrigere Confidence → `clarify` |

### 5.7 Modellwahl

| Provider | Modell | Begründung |
|----------|--------|------------|
| OpenAI | `gpt-5.4-nano` | Bereits in `classify_intent_with_llm` |
| Gemini | `gemini-3-flash-preview` | Schnell, günstig |
| Offline | Regex only | Flag off |

**Circuit-Breaker:** Wie `memory_extractor` — 3 Fehler → 120s Open, Regex-Fallback.

### 5.8 Akzeptanzkriterien

- [ ] Benchmark Contact/Pet/Recall: **+12–18 pp** vs. Phase-0-Baseline
- [ ] Keine Regression: `test_calendar_routing_fix.py` (35 Tests) grün
- [ ] Latenz P95 Classifier < 400ms
- [ ] Flag off → identisches Verhalten

### 5.9 Risiken

| Risiko | Mitigation |
|--------|------------|
| LLM halluziniert action | Confidence-Threshold + Legacy-Fallback |
| Latenz | Async, parallel zu Embedding-Prep wo möglich |
| Kosten | Nano only, max 20 Output-Tokens |
| Provider-Ausfall | Circuit-Breaker → Regex |

---

## 6. Phase 2 — Confidence-Routing statt Ambiguity-Hard-Block

### 6.1 Ziel

`disable_tools=True` nur bei echter Mehrdeutigkeit — nicht bei niedriger Regex-Confidence.

### 6.2 Aufwand / Risiko

| | Wert |
|---|------|
| Aufwand | **3–5 Tage** |
| Risiko | **Mittel** |

### 6.3 Verhalten heute vs. neu

| Confidence | Heute | Neu |
|------------|-------|-----|
| ≥ 0.80 | Tools aktiv (wenn nicht ambiguous) | Tools **erzwingen** |
| 0.55–0.79 | Oft `disable_tools` | Tools **anbieten**, LLM wählt |
| < 0.55 | `disable_tools` + Klärungsfrage | Klärungsfrage **oder** general chat |

### 6.4 Dateien

| Aktion | Datei |
|--------|-------|
| MODIFY | `backend/services/orchestrator/execution_dispatcher.py` |
| MODIFY | `backend/services/orchestrator/intent_engine.py` (`detect_ambiguity_in_query`) |
| CREATE | `backend/tests/test_intent_confidence_routing.py` |

### 6.5 Akzeptanzkriterien

- [ ] Benchmark-Cluster „Ambiguity FP“: **−30–50%** Fehl-Blocks
- [ ] Contact/Pet-Facts mit confidence ≥ 0.80: **nie** `disable_tools`
- [ ] Medical/Policy-Pfade unverändert

---

## 7. Phase 3 — Regex-Freeze & Deprecation

### 7.1 Ziel

Stoppt Regex-Wachstum. Neue Formulierungen → Classifier, nicht neue Patterns.

### 7.2 Aufwand / Risiko

| | Wert |
|---|------|
| Aufwand | **2–3 Tage** |
| Risiko | **Niedrig** (prozessual) |

### 7.3 Maßnahmen

- [ ] `INTENT_REGEX_FREEZE=true` → CI warnt bei neuen `_FACT_TELLING_PATTERNS`
- [ ] Comment-Header in `intent_engine.py`: „NO NEW PATTERNS — use aux classifier“
- [ ] Bestehende Patterns: eingefroren, nur Bugfixes mit Benchmark-Case
- [ ] `intent_classifier.is_web_search_intent` → deprecate, durch Classifier `search` ersetzen

---

## 8. Phase 4 — Entity-First Routing (Pet → Owner → Contact)

### 8.1 Ziel

Subject-Auflösung **nach** Action-Klassifikation, nicht in Regex vermischen.

### 8.2 Aufwand / Risiko

| | Wert |
|---|------|
| Aufwand | **1–1,5 Wochen** |
| Risiko | **Mittel** |

### 8.3 Pipeline

```text
action=tell_fact, subject=pet
  → entity_resolver.resolve_pet_owner("tasso")
  → contact_manager.get_contact("oli")
  → memory_write + contact_writeback
```

### 8.4 Dateien

| Aktion | Datei |
|--------|-------|
| MODIFY | `backend/services/orchestrator/entity_resolver.py` |
| MODIFY | `backend/services/contact_manager.py` |
| CREATE | `backend/services/orchestrator/intent_entity_bridge.py` |
| CREATE | `backend/tests/test_intent_entity_bridge.py` |

### 8.5 Akzeptanzkriterien

- [ ] Benchmark Pet-Owner-Cluster: **+8–12 pp**
- [ ] BACKLOG-108/116/119 Live-Szenarien grün
- [ ] Kein Doppel-Write (pet line + owner line) — bestehende Normalisierung bleibt

---

## 9. Phase 5 — Operator-Bypass `/skipdetect`

### 9.1 Ziel

User kann fehlklassifizierten Turn umgehen (Hermes-ARC-Pattern).

### 9.2 Aufwand / Risiko

| | Wert |
|---|------|
| Aufwand | **1 Tag** |
| Risiko | **Niedrig** |

### 9.3 Verhalten

- User schreibt `/skipdetect` oder Prefix `!` am Turn-Start
- Nächster Turn: `INTENT_AUX_CLASSIFIER_ENABLED` skip, reines LLM + alle Tools
- Logging: `[INTENT-BYPASS] user requested skipdetect`

---

## 10. Was NICHT anfassen

| Bereich | Grund |
|---------|-------|
| Calendar/Shopping Veto-Logik | Funktioniert, nur einbinden |
| Precedence Guard (Personal → no Websearch) | Safety-kritisch |
| Health-Injector | Medical |
| `gateway/run.py`-Style Command-Routing | Janus hat UI/API, nicht CLI |
| Komplette Entfernung von `IntentDetectionResult` | Breaking Change — nur deprecaten |

---

## 11. Testplan (gesamt)

### 11.1 Jede Phase

```bash
python -m backend.scripts.run_intent_benchmark --report
python -m pytest backend/tests/test_calendar_routing_fix.py -q
python -m pytest backend/tests/test_tool_selector_contact_routing.py -q
python -m pytest backend/tests/unit/test_intent_engine.py -q
python -m pytest backend/tests/test_memory_regression.py -q
```

### 11.2 Live-Retest-Szenarien (Pflicht vor Flag-Flip)

| # | Input | Erwartung |
|---|-------|-----------|
| L1 | „olis hund tasso ist ein podenco“ | tell_fact, pet, contact writeback |
| L2 | „was weißt du über chris gier?“ | recall, contact, kein websearch |
| L3 | „tasso frisst gerne thunfisch“ | tell_fact, pet, owner=oli |
| L4 | „wie wird das wetter in münchen?“ | search, kein calendar-boost |
| L5 | „termin morgen 14 uhr zahnarzt“ | create, calendar |
| L6 | „besitzt einen hund namens bello“ | tell_fact (Verb-Varianz) |
| L7 | „wer ist nathan?“ (Kontakt existiert) | recall, nicht wikipedia |

---

## 12. Accuracy-Einschätzung (ehrlich)

### 12.1 Methodik

Ohne Phase-0-Benchmark sind alle Zahlen **Schätzungen** aus:

- BACKLOG-Historie (108, 110, 116, 119, 120 = Intent/Routing-Bugs)
- 35 Tests in `test_calendar_routing_fix.py` (viele Patch-getriebene Edge Cases)
- Live-Debug-Muster in `SKILL_USAGE_LOG.md`

**Nach Phase 0** werden die Prozentangaben durch echte Messung ersetzt.

### 12.2 Geschätzte Baseline heute (vor Upgrade)

| Intent-Cluster | Anteil der User-Turns* | Geschätzte Accuracy** |
|----------------|------------------------|----------------------|
| Greeting/Smalltalk | ~15% | **~95%** |
| Calendar/Shopping (strukturiert) | ~15% | **~85%** |
| Contact/Pet Fact-Telling | ~20% | **~65–75%** |
| Contact/Personal Recall | ~15% | **~70–80%** |
| Web/Weather/Geo | ~15% | **~80–85%** |
| Ambiguity-Entscheidung | ~10% | **~60–70%** (viele FP) |
| Rest (General/Help/Video) | ~10% | **~85%** |

\* *Anteile grob geschätzt für einen Personal-Assistant mit aktivem Kontakt-/Memory-Use.*  
\** *„Accuracy“ = korrekter Primary-Action-Pfad (richtiger Skill/Tool/Block).*

**Gewichtete Gesamt-Accuracy (geschätzt): ~78–83%** über alle Turns.

### 12.3 Erwartete Accuracy nach Phasen

| Nach Phase | Contact/Pet/Recall | Ambiguity FP | Gesamt (gewichtet) |
|------------|-------------------|--------------|-------------------|
| **0** (Baseline messen) | messen | messen | messen |
| **1** (Aux Classifier) | **~85–92%** (+12–18 pp) | unverändert | **~84–88%** (+5–7 pp) |
| **2** (Confidence-Routing) | leicht besser | **−30–50% FP** | **~86–90%** (+2–3 pp) |
| **4** (Entity-First) | **~90–95%** (+5–8 pp) | — | **~88–92%** (+2–3 pp) |

### 12.4 Interpretation für den Product Owner

| Formulierung | Realistische Erwartung |
|--------------|------------------------|
| „Janus wird 20% genauer“ | **Ja, grob** — auf gesamt-gewichteter Primary-Route (~78% → ~88–92% nach MVP) |
| „Kein Kontakt-Bug mehr“ | **Nein** — Edge Cases bleiben, aber **deutlich seltener** |
| „Keine Regex-Patches mehr“ | **Ja, nach Phase 3 Freeze** — neue Sprache geht in Classifier |
| „Kosten steigen“ | **Leicht** — ~1 Nano-Call/Turn (~0.0001–0.0003 USD) |
| „Latenz steigt“ | **+200–400ms P95** — parallelisierbar |

### 12.5 Was der Upgrade **nicht** löst

- LLM-Antwortqualität (nur Routing)
- Memory-Recall-Qualität (siehe Memory-Plan)
- Modell-Halluzinationen nach korrektem Routing
- Komplett neue Domänen ohne Benchmark-Cases

---

## 13. Aufwand & Risiko — Gesamtbild

| Szenario | Kalender | Risiko | Accuracy-Gewinn |
|----------|----------|--------|-----------------|
| **MVP (0+1+2)** | ~3 Wochen | **Mittel** | **+7–10 pp gesamt**, Contact/Pet **+12–18 pp** |
| **Voll (0–5)** | ~5–6 Wochen | **Mittel-Hoch** | **+10–14 pp gesamt**, Contact/Pet **+20–25 pp** |
| **Nur Regex-Patches (Status quo)** | laufend | **Niedrig pro Patch, hoch kumulativ** | **+1–2 pp pro Bug**, Wartungsexplosion |

### Risiko-Matrix

| Risiko | Schwere | Wahrscheinlichkeit | Mitigation |
|--------|---------|-------------------|------------|
| Classifier-FP bei search/recall | Hoch | Mittel | Safety-Layer + Benchmark |
| Latenz-Regression | Mittel | Mittel | Async, Circuit-Breaker |
| Legacy-Merge-Bugs | Hoch | Mittel | Kompatibilitäts-Schicht, Flag off |
| Kosten | Niedrig | Hoch | Nano only, Session-Caching später |
| Team gewöhnt sich an Regex-Patches | Mittel | Hoch | Phase 3 Freeze + CI-Warnung |

### Empfohlene Reihenfolge

```
Phase 0 (messen) → Phase 1 (Classifier) → Phase 2 (Confidence) → Live-Staging 1 Woche
  → Go/No-Go → Phase 4 (Entity) → Phase 3 (Freeze) → Phase 5 (Bypass)
```

**Phase 1 nicht ohne Phase 0** — sonst keine ehrliche Vorher/Nachher-Messung.

---

## 14. Codex-Startprompt

```text
Implementiere Phase 0 + Phase 1 aus:
documentation/Cursor specs/INTENT_ENGINE_HERMES_INSPIRED_UPGRADE_PLAN.md

Scope Phase 0:
- backend/tests/fixtures/intent_benchmark_cases.jsonl (min. 80 Cases aus BACKLOG-108/110/116/119/120 + test_calendar_routing_fix)
- backend/scripts/run_intent_benchmark.py
- backend/tests/test_intent_benchmark.py
- documentation/test-runs/INTENT_BENCHMARK_BASELINE.md

Scope Phase 1:
- backend/services/orchestrator/intent_aux_classifier.py
- backend/services/orchestrator/intent_config.py
- Integration in detect_all_intents() hinter INTENT_AUX_CLASSIFIER_ENABLED=false
- backend/tests/test_intent_aux_classifier.py

Constraints:
- IntentDetectionResult API nicht brechen
- Safety/Veto-Layer unverändert
- Health-Injector / Precedence Guard nicht anfassen
- Circuit-Breaker bei Classifier-Ausfall
- Keine neuen Regex-Patterns in _FACT_TELLING_PATTERNS

Validation:
python -m backend.scripts.run_intent_benchmark --report
python -m pytest backend/tests/test_intent_aux_classifier.py backend/tests/test_calendar_routing_fix.py -q
```

---

## 15. Go/No-Go nach MVP (Phase 0–2)

| Kriterium | Schwelle |
|-----------|----------|
| Benchmark gesamt | ≥ +7 pp vs. Baseline |
| Contact/Pet/Recall Cluster | ≥ +12 pp |
| Ambiguity FP | ≥ −30% |
| `test_calendar_routing_fix.py` | 100% grün |
| Live-Retest L1–L7 | 7/7 PASS |
| P95 Latenz | < +500ms vs. heute |

**No-Go:** Flag `INTENT_AUX_CLASSIFIER_ENABLED` dauerhaft off, Regex-Pfad bleibt Primary, Classifier nur Logging.

---

**END OF PLAN**
