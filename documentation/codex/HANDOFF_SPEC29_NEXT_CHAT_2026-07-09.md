# NEW CHAT HANDOFF - SPEC 29

## Recommended Gate

MODEL SWITCH GATE
- Skill: `janus-spec-review`
- Empfohlenes Modell: `5.4`
- Empfohlene Intelligenz: `high`
- Neuer Chat: `ja`
- Kontextstrategie: `frischer Chat mit nur den unten genannten gebundenen Artefakten und diesem Handoff`
- Grund: `Die Feature-Spec fuer Spec 29 existiert bereits im Repo. Der naechste saubere Pipeline-Schritt ist daher Spec-Review, nicht noch einmal Spec-Generator. Ein neuer Chat reduziert Drift und haelt die Produkt-, Routing- und Cursor-Evidence-Vorgaben kompakt.`

## Copy-Paste Prompt For New Chat

```text
MODEL SWITCH GATE
- Skill: janus-spec-review
- Empfohlenes Modell: 5.4
- Empfohlene Intelligenz: high
- Neuer Chat: ja
- Kontextstrategie: nur gebundene Artefakte laden
- Grund: Spec 29 ist bereits generiert; bitte nicht neu generieren, sondern reviewen und fuer die naechste Pipeline-Stufe absichern.

Bitte uebernimm ab hier im Janus-Repo den naechsten Schritt fuer:

Feature: Stilles Routinenlernen mit Kandidatenphase

Wichtiger Status:
- `BACKLOG-121` ist abgeschlossen, final auditiert, dokumentiert und nach `backup/develop` gepusht.
- Die gemeinsame Delegation-Policy wurde dabei bewusst gehaertet:
  - bounded externe Cursor-Alternativen duerfen in opt-in-Lanes auch bei negativer ROI sichtbar bleiben
  - Codex bleibt dabei weiterhin die empfohlene Standardwahl
  - ROI ist nicht mehr die primaere Produktbegruendung fuer Sichtbarkeit; alternative Arbeitskapazitaet und operatives Weiterarbeiten sind vorrangig

Wichtige operative Arbeitsregel fuer diese Rollout-Phase:
- Wir wollen absichtlich so oft wie sinnvoll moeglich echte produktive Arbeit ueber Cursor laufen lassen, vor allem ueber Cursor Composer und wo passend Cursor API.
- Ziel ist nicht nur Umsetzung, sondern echte Evidence-Sammlung fuer:
  - Routing-Nuetzlichkeit
  - ROI / Tokenersparnis
  - Sichtbarkeit der Optionen im Gate
  - Timeout-Verhalten
  - Qualitaet der gelieferten Patches
  - Review-/Validation-Aufwand
  - spaeteres Hardening der Cursor-Workhorse-Route
- Cursor-first pruefen, wenn der Slice bounded ist.
- Echte Cursor-Arbeit bevorzugen, wenn die Lane sichtbar und sinnvoll ist.
- Wenn Cursor fuer einen Slice nicht sichtbar, nicht sinnvoll oder nicht ROI-positiv ist, soll das als Evidence festgehalten werden, statt stillschweigend ignoriert zu werden.
- Wichtiges Produkt-Update aus BACKLOG-121:
  - Es geht nicht primaer darum, zwingend Tokens zu sparen.
  - Alternativkapazitaet zaehlt explizit mit.
  - Wenn Codex-Kontingent knapp ist, kann sichtbare Cursor-Arbeit trotzdem wertvoll sein, auch wenn die reine ROI-Rechnung knapp negativ waere.
- Codex bleibt trotzdem Review-, Validierungs- und Acceptance-Owner.

Repo-Wahrheit fuer Spec 29:
- Feature-Spec existiert bereits:
  - `documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md`
- Task-Artifact existiert bereits:
  - `documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md`

Bitte daher:
1. die bestehende Spec 29 reviewen statt neu zu generieren
2. pruefen, ob die Spec die stille Kandidatenphase, automatische Promotion beim zweiten passenden Erfolg, passive Chat-Transparenz, Settings-Verwaltung, 30-Tage-Verfall und Risk-/Sensitive-Guards klar und fail-closed genug beschreibt
3. speziell pruefen, ob die Task-Slices spaeter bounded und wo sinnvoll Cursor-first ausfuehrbar bleiben
4. falls die Spec review-ready ist, den naechsten sauberen Schritt fuer `janus-spec-to-task` freigeben

Gebundene Artefakte zuerst:
- `documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md`
- `documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md`
- `documentation/ai/CURRENT_STATE.md`
- optional fuer Delegation-/Evidence-Kontext:
  - `documentation/tasks/backlog_BACKLOG-121_final_audit.md`
  - `documentation/codex/HANDOFF_SPEC29_NEXT_CHAT_2026-07-09.md`

Wichtige Produktentscheidung in einem Satz:
Janus soll wiederkehrende erfolgreiche Mehrschritt-Ablaufe still lernen, zunaechst nur als unsichtbaren Kandidaten vormerken und erst nach einem echten zweiten passenden erfolgreichen Fall automatisch in eine sichtbare gespeicherte Routine umwandeln, ohne vorherige Save-Frage im Chat.
```

## Bound Artifacts

- `documentation/SPEC/29_stilles_routinenlernen_mit_kandidatenphase.md`
- `documentation/tasks/TASK-SPEC29_stilles_routinenlernen_mit_kandidatenphase.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/tasks/backlog_BACKLOG-121_final_audit.md`

## Routing Notes

- Do not send the next chat back into `janus-spec-generator` unless the existing Spec 29 is judged structurally invalid or materially out of sync with the locked decision summary.
- Default next skill is `janus-spec-review`.
- If review passes cleanly, next expected downstream step is `janus-spec-to-task`.

## Cursor / OR Evidence Notes

- `BACKLOG-121` changed the interpretation of negative ROI for visible bounded Cursor alternatives.
- Visible Cursor options may remain available for alternative capacity even when raw token-savings are slightly negative.
- Codex remains recommendation and acceptance owner; visibility and recommendation are now treated as separate policy dimensions.
- Future bounded implementation slices for this feature should therefore be checked explicitly for real Cursor execution suitability rather than hidden automatically behind ROI-only reasoning.
