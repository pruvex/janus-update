# BACKLOG-114 Task

- **Backlog Item:** BACKLOG-114 - Installierte Janus-Skill-Arbeitskopien uebernehmen die neuen bestehenden Codex-vs-OR Alltagsgates aus Spec 26 noch nicht nachweisbar
- **Status:** READY
- **Erstellt:** 2026-06-25
- **Aktualisiert:** 2026-06-25
- **Follow-up zu:** BACKLOG-113 - Installierte Skill-Arbeitskopien nutzen den produktiven Dev-Workhorse-Pfad noch nicht als kanonischen OR-Einstieg
- **Kurzbeschreibung:** Die repo-versionierten bestehenden Skill-Gates aus Spec 26 sollen in die installierten `C:\Users\pruve\.codex\skills\janus-*`-Arbeitskopien uebernommen und einmal im echten Workflow so verifiziert werden, dass nur die freigegebenen sichtbaren Lanes `1 = Codex` / `2 = OR` zeigen.
- **Ziel:** Den operator-facing Spec-26-Rollout vom repo-seitigen Wahrheitsstand in die installierten Skill-Arbeitskopien und einen kleinen echten Workflow-Nachweis ueberfuehren.
- **Scope:** Installierte Skill-Arbeitskopien der betroffenen bestehenden Janus-Skills, die zugehoerigen repo-versionierten Skillquellen als Vergleichsbasis und eine gebundene echte Workflow-Verifikation. Keine neue Lane-Freigabe, kein Produktionsrouting, keine Routing-Tabellen-Aktivierung, keine allgemeine Produktlogik.
- **Files:**
  - `documentation/codex/skills/janus-executioner/SKILL.md`
  - `documentation/codex/skills/janus-debug/SKILL.md`
  - `documentation/codex/skills/janus-test-pipeline/SKILL.md`
  - `documentation/codex/skills/janus-quickchange/SKILL.md`
  - `documentation/codex/skills/janus-documentation-update/SKILL.md`
  - `C:\Users\pruve\.codex\skills\janus-executioner\SKILL.md`
  - `C:\Users\pruve\.codex\skills\janus-debug\SKILL.md`
  - `C:\Users\pruve\.codex\skills\janus-test-pipeline\SKILL.md`
  - `C:\Users\pruve\.codex\skills\janus-quickchange\SKILL.md`
  - `C:\Users\pruve\.codex\skills\janus-documentation-update\SKILL.md`
  - `documentation/ai/CURRENT_STATE.md`
- **Steps:**
  - Die repo-versionierten Spec-26-Gates mit den installierten Skill-Arbeitskopien der betroffenen bestehenden Janus-Skills abgleichen.
  - Die installierten Skill-Arbeitskopien so nachziehen, dass sichtbare freigegebene Lanes die normale Wahl `1 = Codex` / `2 = OR` zeigen.
  - Sicherstellen, dass `generator_review` und `execution_write_apply_candidate` in den installierten Skill-Arbeitskopien weiterhin sichtbar lokal bleiben und nicht als normale Alltagswahl erscheinen.
  - Einen kleinen echten Workflow-Nachweis fuer mindestens einen sichtbaren Lane und einen verborgen bleibenden Lane festhalten.
- **Akzeptanzkriterien:**
  - Die betroffenen installierten Skill-Arbeitskopien spiegeln die repo-versionierten bestehenden Spec-26-Gates fuer die sichtbare Alltagswahl konsistent.
  - Sichtbare freigegebene Lanes zeigen im echten Skill-Workflow `1 = Codex` und `2 = OR`.
  - `generator_review` und `execution_write_apply_candidate` bleiben im echten Skill-Workflow sichtbar lokal und erscheinen nicht als normale Alltagswahl.
  - Der Rollout bleibt strikt auf installierte Skill-Arbeitskopien und gebundene Workflow-Verifikation begrenzt, ohne Produktionsrouting oder neue Lane-Freigaben.
- **Fehlende Informationen:**
  - Keine
- **Betroffener Bereich:** Codex-Skill-Integration / installierte Skill-Arbeitskopien / bestehende Janus-Skill-Gates / OR-Alltagsworkflow
- **Nachweise:** `documentation/backlog/BACKLOG.md`; `documentation/SPEC/26_operator_facing_codex_oder_or_wahl_in_bestehenden_janus_skills.md`; `documentation/tasks/TASK-SPEC26.3_execution_result.md`; `documentation/codex/model-routing/or_everyday_lane_inventory_2026-06-24.md`; `documentation/codex/model-routing/or_everyday_operator_registry_summary_2026-06-24.md`
- **Notizen:** Das ist bewusst ein kleiner Rollout-/Verifikationsslice nach einem repo-seitig fertig umgesetzten bestehenden-Skill-Gate-Block, kein neuer OR-Grundlagenbau.

@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-114
Task: documentation/tasks/backlog_BACKLOG-114_installierte_janus_skill_arbeitskopien_uebernehmen_spec26_alltagsgates.md
Backlog Item: BACKLOG-114
