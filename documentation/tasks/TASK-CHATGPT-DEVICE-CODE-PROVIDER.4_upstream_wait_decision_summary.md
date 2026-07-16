# LATEST DECISION SUMMARY - TASK-CHATGPT-DEVICE-CODE-PROVIDER.4

Feature Name: ChatGPT über offiziellen Codex-Device-Code - Upstream-Warteentscheidung

Primary Goal: Die Janus-only Tool- und Sicherheitsgrenze unverändert erhalten, bis der offizielle Codex App Server einen nachweisbaren Modus bereitstellt, der ausschließlich Janus-Client-Tools zulässt.

User Problem: Der aktuell gebundene offizielle Runtime-Stand fügt mindestens das Codex-native Tool `update_plan` zwingend hinzu und kann deshalb die freigegebene Janus-only Grenze nicht erfüllen.

User Value: Keine stille Abschwächung der Sicherheits- und Kontrollgrenze und keine neue Eigenverantwortung für eine gepatchte Codex-Runtime.

Primary Target Surface: Bestehende ChatGPT-Provider-Integration in Janus.

Existing or New Surface: Bestehende, noch nicht produktiv aktivierte Provider-Integration.

Existence Confirmation: im Repository und durch die gebundenen Task-/Spec-Artefakte verifiziert.

User Trigger: Kein neuer Benutzer-Trigger; die Integration bleibt bis zum Nachweis offizieller Runtime-Unterstützung nicht verfügbar.

Success Behavior: Sobald ein offizieller Runtime-Stand einen nachweisbaren Dynamic-Tools-only- oder vollständigen Core-Tool-Allowlist-Modus bietet, darf Task `.4` gegen genau diesen Stand neu geprüft werden. Erst ein grüner Precheck darf Implementierung freigeben.

Failure Behavior: Solange die Fähigkeit fehlt, abweicht oder nicht eindeutig nachweisbar ist, bleibt Task `.4` `BLOCKED`, ChatGPT bleibt vollständig nicht nutzbar und es gibt keinen reduzierten Text-, Tool- oder Provider-Fallback.

User Action Surface: Keine neue Aktion. Bestehende Auswahl, Entwürfe und andere Provider bleiben unbeeinflusst; ChatGPT darf nicht als funktionsfähiger Produktionsprovider dargestellt werden.

Data / Persistence: Keine neuen Daten, Credentials, Threads oder Bestätigungen werden erzeugt, geändert oder gelöscht.

Security / Privacy: Die Janus-only Tool-Autorität, Redaction, explizite Datenschutzbestätigung, API-Key-Nichtbeeinflussung und Produktions-default-deny bleiben unverändert. Eine Janus-gepatchte Codex-Runtime wird nicht verfolgt.

Edge Cases: Ein bloßes Versionsupdate, experimentelles Feld, Promptverbot, Read-only-Sandbox, Approval-Ablehnung oder Eventfilterung genügt nicht. Erforderlich ist erneut account-freie, ausführbare Evidenz, dass vor Modelldispatch keine Codex-native Aktionsoberfläche angeboten wird.

Out of Scope: Gepatchte oder geforkte Codex-Runtime; Abschwächung der Janus-only Anforderung; Zulassung von `update_plan`; Text-only-Degradierung; automatische Wiederholung; Provider-Fallback; Konto-, Git-, Sync-, Build-, Release- oder Produktionsaktion.

Routing Decision: FULL FEATURE PIPELINE

Routing Reason: Die bestehende Integration bleibt hochriskant und sicherheitsrelevant; die Warteentscheidung muss als Amendierung der aktiven Spec gebunden und erneut reviewed werden, bevor ein späterer Precheck zulässig ist.

Recommended Next Skill: `janus-spec-generator`

Decision Status: LOCKED

Locked Choice: A - auf offiziellen Upstream-Support warten und Task `.4` sicher `BLOCKED` lassen.
