FEATURE_DESIGN_REVIEW
Status: PASS
Decision State: DECISION_SUMMARY_READY
Recommended Next Skill: janus-spec-generator
LATEST DECISION SUMMARY
Feature Name: Operator-facing Codex-oder-OR-Wahl in bestehenden Janus-Skills
Primary Goal: In passenden bestehenden Janus-Skills soll am Einstieg sichtbar zwischen lokalem Codex-Pfad und bounded OR-Pfad gewaehlt werden koennen.
User Problem: Der Nutzer will je nach Codex-Kontingent und erwarteten OR-Kosten flexibel entscheiden koennen, welcher Pfad fuer eine konkrete Aufgabe sinnvoller ist.
User Value: Flexibilitaet bei der Auswahl zwischen Codex und OR zur Optimierung von Kontingentnutzung und Kosten
Primary Target Surface: bestehende Janus-Skill-Einstiege
Existing or New Surface: bestehend
Existence Confirmation: confirmed by user
User Trigger: Start eines geeigneten Janus-Skills mit bounded OR-Kandidaten
Success Behavior: Der Skill zeigt sichtbar 1 = Codex und 2 = OR inklusive Kosten-/Evidenzhinweis und faellt fail-closed lokal zurueck, wenn kein freigegebener bounded OR-Lane passt.
Failure Behavior: Nicht freigegebene, partielle oder ungesunde OR-Lanes duerfen nicht als normale Wahl erscheinen; in solchen Faellen bleibt nur der lokale Codex-Pfad sichtbar.
User Action Surface: bewusste Auswahl zwischen Codex und OR am Skill-Einstieg
Data / Persistence: nur Telemetrie, Gate-Evidenz und vorhandene Skill-/Routing-Artefakte; keine neue Produktpersistenz
Security / Privacy: keine broad delegated authority, keine Production-Routing-Aktivierung, Codex behaelt finale Validierung und Autoritaet
Edge Cases: fehlende Gate-Daten, fehlende OR-Freigabe, partielle Kandidaten, unvollstaendige Telemetrie, Healthcheck-Fehler
Out of Scope: globale OR-Freigabe, canonical routing-table update, broad delegated repo authority, release actions
Routing Decision: FULL FEATURE PIPELINE
Routing Reason: Feature is fully scoped and aligned with existing Janus skill architecture with clear local fallback
Recommended Next Skill: janus-spec-generator
Notes: ['User wants flexible Codex vs OR routing choice', 'Feature applies to existing Janus skills', 'Local Codex remains default/fail-closed', 'OR routing is bounded and gated']
