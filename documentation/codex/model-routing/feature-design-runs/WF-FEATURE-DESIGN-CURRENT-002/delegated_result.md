FEATURE_DESIGN_REVIEW
Status: PASS
Decision State: DECISION_SUMMARY_READY
Recommended Next Skill: janus-spec-generator
LATEST DECISION SUMMARY
Feature Name: Operator-facing Codex-oder-OR-Wahl in bestehenden Janus-Skills
Primary Goal: In passenden bestehenden Janus-Skills soll am Einstieg sichtbar zwischen lokalem Codex-Pfad und bounded OR-Pfad gewaehlt werden koennen.
User Problem: Der Nutzer will je nach Codex-Kontingent und erwarteten OR-Kosten flexibel entscheiden koennen, welcher Pfad fuer eine konkrete Aufgabe sinnvoller ist.
User Value: Mehr operative Flexibilitaet beim Einsatz von Codex und OR ohne Verlust der lokalen Kontrolle.
Primary Target Surface: bestehende Janus-Skill-Einstiege
Existing or New Surface: bestehend
Existence Confirmation: confirmed by user
User Trigger: Start eines geeigneten Janus-Skills mit bounded OR-Kandidaten
Success Behavior: Der Skill zeigt sichtbar 1 = Codex und 2 = OR inklusive Kosten- und Evidenzhinweis und faellt fail-closed lokal zurueck, wenn kein freigegebener bounded OR-Lane passt.
Failure Behavior: Nicht freigegebene, partielle oder ungesunde OR-Lanes duerfen nicht als normale Wahl erscheinen; in solchen Faellen bleibt nur der lokale Codex-Pfad sichtbar.
User Action Surface: bewusste Auswahl zwischen Codex und OR am Skill-Einstieg
Data / Persistence: nur Telemetrie, Gate-Evidenz und vorhandene Skill- und Routing-Artefakte; keine neue Produktpersistenz
Security / Privacy: keine broad delegated authority, keine Production-Routing-Aktivierung, Codex behaelt finale Validierung und Autoritaet
Edge Cases: fehlende Gate-Daten, fehlende OR-Freigabe, partielle Kandidaten, unvollstaendige Telemetrie, Healthcheck-Fehler
Out of Scope: globale OR-Freigabe, canonical routing-table update, broad delegated repo authority, release actions
Routing Decision: FULL FEATURE PIPELINE
Routing Reason: Das Feature betrifft mehrere bestehende Skill-Einstiege, Sichtbarkeitsregeln, Telemetrie und Governance-Grenzen und ist damit kein kleiner lokaler Backlog-Fix.
Recommended Next Skill: janus-spec-generator
Notes: ['The feature scope is sufficiently decision-locked for a bounded summary draft.', 'Codex remains final owner of the design decision.']
