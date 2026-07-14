# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING
target_skill: janus-spec-review
recommended_model: 5.6 Sol
recommended_reasoning: high
new_chat: yes
complexity_score: 69
confidence: HIGH
dashboard_hint: CRITICAL
reason: Sicherheitskritische Konto-Integration über mehrere bestehende Oberflächen mit isolierter Persistenz, Workspace-Grenzen und Providerkontinuität.

## SPEC REVIEW METADATA

- **Review Status:** APPROVED
- **Complexity Score:** 69
- **Risk:** HIGH
- **Recommended Review Model:** 5.6 Sol
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-07-14
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION STATUS

- **Feature Status:** ACTIVE - partial delivery only.
- **Completed Task:** `TASK-CHATGPT-CODEX.1` - official isolated Codex App Server lifecycle boundary; final audit PASS on 2026-07-14.
- **Evidence:** `documentation/tasks/TASK-CHATGPT-CODEX.1_final_audit.md`; `documentation/tasks/TASK-CHATGPT-CODEX.1_AUDIT_PACKAGE.md`.
- **Remaining Tasks:** `TASK-CHATGPT-CODEX.2` through `.4` remain parked and require separate task-breakdown, precheck, execution, validation, and audit gates.
- **Spec Done:** NO - no settings UI, visible provider/model selection, transport, first-send privacy flow, or full account lifecycle is completed by `.1`.

## FEATURE IDENTITY
- Feature Name: ChatGPT-Konto als zusätzlicher Janus-Provider über den offiziellen Codex-Zugang
- Feature ID: CHATGPT-OAUTH-PROVIDER
- Decision Source: LATEST DECISION SUMMARY 2026-07-14
- Primary Goal: ChatGPT-Kontozugang als bewusst getrennte Janus-Nutzungsoption bereitstellen, ohne bestehende API-Key-Provider zu verändern.
- Routing Scope: Full Feature Pipeline

## USER VALUE

Nutzer mit ChatGPT-/Codex-Zugang können Janus ohne zusätzlichen OpenAI-API-Key verwenden. Sie wählen ChatGPT bewusst als Provider und können innerhalb desselben Janus-Chats jederzeit zu oder von einem anderen Provider wechseln. Die sichtbare Modellwahl bleibt auf die mit dem aktiven Konto tatsächlich nutzbaren Codex-Modelle begrenzt.

## TARGET SURFACE
- Primary Surface: Bestehender API-Key-Bereich der Janus-Einstellungen
- Secondary Surface: Bestehendes Provider-/Modell-Dropdown in der Sidebar
- Surface Status: Bestehende Oberflächen werden ergänzt
- Existence Confirmation: confirmed by user and verified in repository
- Provider Label: ChatGPT
- Context Label: Über Codex wird in Einstellungen und Verbindungsstatus sichtbar angezeigt

## USER ACTION SURFACE
- Login Trigger: Mit ChatGPT anmelden in den bestehenden Einstellungen
- Workspace Action: Workspace-Auswahl erfolgt im offiziellen Anmeldevorgang
- Provider Action: ChatGPT wird nach erfolgreicher Anmeldung bewusst im bestehenden Dropdown gewählt
- Model Action: Nutzer wählen ein tatsächlich nutzbares, picker-sichtbares Modell des aktiven Kontos
- Lifecycle Actions: Logout, Account-Wechsel und Erneut versuchen stehen im Verbindungsstatus bereit
- Chat Continuity: Provider- und Modellwechsel bleiben im bestehenden Janus-Chat möglich und erhalten den Chatverlauf

## SYSTEM BEHAVIOR

Janus integriert den offiziell unterstützten Codex-Zugang des ChatGPT-Kontos als zusätzliche Provideroption. Der benötigte lokale Zugang wird durch Janus bereitgestellt und verwaltet; keine vorherige separate Codex-Installation ist nötig.

Nach erfolgreicher Anmeldung zeigt Janus ChatGPT erst dann im Provider-Dropdown an. Der Status zeigt eine verfügbare Konto-Kennung, den aktiven Workspace und den Hinweis Über Codex. Die Modellliste enthält nur Modelle, die der aktive Zugang tatsächlich als picker-sichtbar und nutzbar meldet. Nicht mehr nutzbare Modelle verlangen eine bewusste neue Auswahl; Janus wechselt nie automatisch zu einem Ersatzmodell oder zu einem anderen Provider.

ChatGPT verhält sich innerhalb eines normalen Janus-Chats wie ein bestehender Provider. Es erhält keine eigenständigen Datei-, Shell- oder Codeaktionsrechte. Janus bleibt Eigentümer des Chatverlaufs und der sichtbaren Providerwahl.

Ein abgebrochener oder fehlgeschlagener Login verändert keinen bestehenden Zustand. Bei einer ungültigen Sitzung fordert Janus eine erneute Anmeldung. Wenn der lokale Zugang vorübergehend nicht verfügbar ist, bleibt die Anmeldung erhalten und ChatGPT sichtbar, aber deaktiviert; Janus bietet Erneut versuchen an. Wird ein Kontolimit erreicht, blockiert Janus das Senden und zeigt, sofern verfügbar, den Rücksetzzeitpunkt.

## DATA / PERSISTENCE
- Account Scope: Version 1 unterstützt genau ein aktives Konto
- Workspace Scope: Der im offiziellen Login gewählte Workspace bestimmt die aktive Janus-Verbindung
- Session Ownership: Die offizielle Codex-Grenze besitzt Secrets und deren Refresh
- Janus Persistence: Janus speichert ausschließlich nicht geheime Verbindungsmetadaten, Status- und Auswahlzustand
- Isolation: Die Janus-Anmeldung ist von anderen lokalen Codex- und ChatGPT-Anmeldungen getrennt
- Credential Requirement: Ausschließlich OS-geschützte Credential-Ablage ohne Klartext- oder unsicheren Fallback
- Logout Semantics: Logout oder Account-Wechsel entfernt ausschließlich die Janus-Anmeldung und betrifft keine anderen Codex- oder ChatGPT-Sitzungen
- Chat Retention: Logout entfernt keinen Janus-Chatverlauf

## CONSTRAINTS

Die Funktion verwendet ausschließlich den offiziell unterstützten Codex-Zugang des ChatGPT-Kontos. Sie vermittelt keinen allgemeinen Zugriff auf ChatGPT-Webmodelle oder ChatGPT-Webfunktionen. API-Key-Provider bleiben unabhängig; API-Keys sind kein Fallback für ChatGPT, und ChatGPT ist kein Fallback für API-Key-Provider.

Die Providerauswahl bleibt bewusst. Eine Anmeldung aktiviert ChatGPT nicht automatisch, ein Fehler wechselt keinen Provider, und ein entzogenes oder nicht verfügbares Modell wird nicht ersetzt. Mehrere parallele Janus-Konten sind nicht Teil von Version 1.

## SECURITY / PRIVACY
- Authentication Boundary: Keine reverse-engineerte OAuth-Nutzung und keine unabhängige Janus-Verwaltung von ChatGPT-Secrets
- Credential Storage: Nur OS-geschützte Ablage; kein Klartext, kein exportierbarer Secret-Wert und kein unsicherer Fallback
- Account Isolation: Janus-Logout darf keine fremden lokalen Codex- oder ChatGPT-Sitzungen abmelden
- Workspace Transparency: Aktives Konto und Workspace sind im Verbindungsstatus sichtbar
- Privacy Notice: Vor dem ersten Senden über ChatGPT erscheint einmalig ein Hinweis zur Verarbeitung im aktiven ChatGPT-/Codex-Workspace
- Failure Privacy: Fehler, Logs, Status- und Einstellungen offenbaren keine Zugangsdaten
- Provider Safety: Kein automatischer API-Key-, Modell- oder Provider-Fallback

## EDGE CASES

- Abgebrochener Login lässt alle bisherigen Provider und Einstellungen unverändert.
- Fehlgeschlagener Login zeigt einen retryfähigen Fehler, ohne ChatGPT als nutzbaren Provider hinzuzufügen.
- Ungültige oder nicht erneuerbare Sitzung blockiert ChatGPT-Senden bis zur bewussten erneuten Anmeldung.
- Fehlende sichere Ablage macht ChatGPT nicht nutzbar; es gibt keinen Dateispeicher- oder API-Key-Fallback.
- Vorübergehend nicht startbarer oder aktualisierbarer lokaler Zugang erhält die Anmeldung, deaktiviert ChatGPT sichtbar und bietet Erneut versuchen an.
- Ein während eines Chats entzogenes Modell verlangt eine bewusste Auswahl eines weiterhin nutzbaren Modells.
- Erreichtes Kontolimit blockiert den Sendefall und zeigt, sofern verfügbar, den Rücksetzzeitpunkt.
- Logout bei aktiv ausgewähltem ChatGPT erhält den Chatverlauf und verlangt für eine weitere Nutzung erneute Anmeldung oder eine bewusste Providerwahl.
- Account- oder Workspace-Wechsel entfernt die vorherige Janus-Verbindung, ohne andere lokale Codex- oder ChatGPT-Sitzungen zu beeinflussen.

## DEFINITION OF DONE

- [ ] Wenn ein Nutzer in den Einstellungen Mit ChatGPT anmelden wählt und die Anmeldung erfolgreich abschließt, dann erscheint ChatGPT bewusst auswählbar und der Status zeigt Konto, Workspace sowie Über Codex.
- [ ] Wenn ChatGPT ausgewählt wird, dann werden nur tatsächlich nutzbare, picker-sichtbare Modelle des aktiven Kontos angeboten.
- [ ] Wenn ein Nutzer im bestehenden Chat den Provider zu oder von ChatGPT wechselt, dann bleibt der Janus-Chatverlauf erhalten und kein Providerwechsel erfolgt automatisch.
- [ ] Wenn Login abgebrochen wird oder fehlschlägt, dann bleiben bisherige Provider, Einstellungen und Auswahl unverändert.
- [ ] Wenn die Sitzung ungültig wird, sichere Ablage fehlt oder der lokale Zugang vorübergehend nicht verfügbar ist, dann blockiert Janus ChatGPT sicher und zeigt den festgelegten Wiederanmelde- oder Retryzustand ohne Fallback.
- [ ] Wenn ein Kontolimit erreicht wird, dann blockiert Janus das Senden und zeigt, sofern verfügbar, den Rücksetzzeitpunkt.
- [ ] Wenn ein Nutzer Logout oder Account-Wechsel ausführt, dann wird ausschließlich die Janus-Anmeldung entfernt, Chatverlauf bleibt erhalten und andere lokale Codex- oder ChatGPT-Sitzungen bleiben unbeeinflusst.
- [ ] Wenn ein Nutzer erstmals über ChatGPT sendet, dann erscheint zuvor einmalig der Datenschutzhinweis zum aktiven Workspace.
- [ ] Wenn ein Nutzer ChatGPT verwendet, dann werden keine Zugangsdaten in Klartext, Einstellungen, Exporten, Fehlern oder Logs offengelegt.

## TEST STRATEGY
- Authentication Lifecycle: Erfolg, Abbruch, Fehler, erneute Anmeldung, Logout und Account-Wechsel werden mit sichtbaren Zuständen geprüft
- Workspace and Model Entitlements: Konto, Workspace, picker-sichtbare Modellliste, Modellverlust und bewusste Neuwahl werden geprüft
- Persistence and Isolation: OS-geschützte Ablage, Janus-only Logout, fehlende sichere Ablage und Nichtoffenlegung von Secrets werden geprüft
- Provider Continuity: Bewusste Auswahl, Providerwechsel im bestehenden Chat, Chatverlaufserhalt und fehlender automatischer Fallback werden geprüft
- Availability and Limits: Temporäre Zugangsstörung, Retry, ungültige Sitzung, Kontolimit und Rücksetzzeitpunkt werden geprüft
- Privacy: Einmaliger Datenschutzhinweis und sichtbare Workspace-Transparenz werden geprüft

## OUT OF SCOPE

Allgemeiner ChatGPT-Webzugriff, ChatGPT-Webmodelle oder Webfunktionen außerhalb des offiziell unterstützten Codex-Zugangs, reverse-engineerte OAuth-Nutzung, mehrere parallele Janus-Konten, API-Key-Fallback, automatische Provider- oder Modellwahl, Änderungen an bestehenden API-Key-Providern sowie eigenständige Codex-Datei-, Shell- oder Codeaktionen.

## INTERNAL COMPLEXITY BREAKDOWN

- Scope Size: 13
- Architectural Risk: 17
- State / Persistence Complexity: 15
- Cross-System Dependencies: 17
- Ambiguity Level: 7
- Total Complexity Score: 69
- Routing Decision: 5.6 Sol
- Routing Reasoning: high
- Routing Confidence: HIGH
- Dashboard Hint: CRITICAL
