# BACKLOG-113 Task

- **Backlog Item:** BACKLOG-113 - Installierte Skill-Arbeitskopien nutzen den produktiven Dev-Workhorse-Pfad noch nicht als kanonischen OR-Einstieg
- **Status:** READY
- **Erstellt:** 2026-06-22
- **Aktualisiert:** 2026-06-22
- **Follow-up zu:** N/A
- **Kurzbeschreibung:** Die installierten Skill-Arbeitskopien sollen fuer die freigegebenen bounded Dev-/OR-Arbeitsslices konsistent auf den fertigen produktiven Dev-Workhorse-Runner zeigen, statt weiter aeltere Dispatcher-first Einstiege zu beschreiben.
- **Ziel:** Den Alltagseinstieg fuer die installierten `janus-*` Skills so angleichen, dass der kanonische produktive Dev-Workhorse-Pfad als sichtbarer Operator-Einstieg genutzt wird.
- **Scope:** Repo-versionierte Skillquellen und installierte Skill-Arbeitskopien fuer die betroffenen Einstiegspfade, insbesondere `janus-executioner` und `janus-debug`, plus die dazugehoerigen Dev-Workflow-Dokumente. Keine Produktlogik, kein Produktionsrouting, keine kanonische Routing-Tabellen-Aktivierung.
- **Files:**
  - `documentation/codex/skills/janus-executioner/SKILL.md`
  - `documentation/codex/skills/janus-debug/SKILL.md`
  - `C:\Users\pruve\.codex\skills\janus-executioner\SKILL.md`
  - `C:\Users\pruve\.codex\skills\janus-debug\SKILL.md`
  - `documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md`
  - `documentation/ai/CURRENT_STATE.md`
- **Steps:**
  - Den installierten Skill-Kopien einen eindeutigen Verweis auf den kanonischen produktiven Dev-Workhorse-Einstieg geben.
  - Die Alltagssprache in den betroffenen Skill- und Runbook-Texten so angleichen, dass `1 = Codex` und `2 = OR` konsistent am produktiven Runner landen.
  - Sicherstellen, dass die Boundaries fuer fixe Modellzuordnung, Kostenbasis und Codex-owned Abschlussgrenzen erhalten bleiben.
  - Repo-versionierte Skillquellen und installierte Skill-Arbeitskopien inhaltlich gegeneinander abgleichen, ohne Janus-Produktarbeit oder Release-Pfade anzufassen.
- **Akzeptanzkriterien:**
  - Die betroffenen installierten Skill-Arbeitskopien verweisen konsistent auf den produktiven Dev-Workhorse-Runner als kanonischen OR-Einstieg.
  - Die betroffenen Repo-Skillquellen und installierten Kopien stimmen fuer den sichtbaren Everyday-Workflow sprachlich und strukturell ueberein.
  - Der Scope bleibt strikt auf die gebundenen Dev-/OR-Integrationspfade beschraenkt.
  - Keine Produktionsrouting-, Release- oder kanonische Routing-Tabellen-Aktivierung wird durch diesen Slice eingefuehrt.
- **Fehlende Informationen:**
  - Keine
- **Betroffener Bereich:** Codex-Skill-Integration / Dev-Workflow / OR-Workhorse-Einstieg / installierte Skill-Arbeitskopien
- **Nachweise:** `documentation/backlog/BACKLOG.md`; `documentation/ai/CURRENT_STATE.md`; `documentation/codex/CODEX_DEV_ENVIRONMENT_RUNBOOK.md`; `documentation/codex/skills/janus-executioner/SKILL.md`; `documentation/codex/skills/janus-debug/SKILL.md`
- **Notizen:** Das ist bewusst ein kleiner Integrationsslice nach einem fertigen Runner-Block, kein neues Produktfeature.

@[/SKILL 3 - PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-113
Task: documentation/tasks/backlog_BACKLOG-113_installierte_skill_arbeitskopien_nutzen_den_produktiven_dev_workhorse_pfad.md
Backlog Item: BACKLOG-113
