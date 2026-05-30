# JANUS FEATURE SPEC – DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: SPEC_REVIEW
execution_mode: GPT_5_5
complexity_score: 67
confidence: MEDIUM
dashboard_hint: CAUTION
reason: Adds explicit mail mutations, outgoing reply flow, undo-sensitive actions, and local attachment handling.

## FEATURE IDENTITY

- Feature Name: Janus Mail Manual Actions and Attachments
- Source Input: Latest approved Janus Mail decision summary from 2026-05-27
- Depends On: documentation/SPEC/10_janus_mail_module_shell_and_connection_state.md and documentation/SPEC/11_janus_mail_gmail_thread_inbox_and_search.md
- Primary Goal: Enable user-confirmed mail actions for reply, send, archive, restore, trash, and attachment send or save
- User Problem: Reading mail alone is not enough; users need to act on messages and handle attachments inside Janus
- User Value: Users can complete core Gmail work from Janus while keeping explicit control over every state-changing action

## USER VALUE

This step makes Janus Mail operational rather than observational.

The user can reply, send a new message from the mail context, organize conversations with explicit actions, and move files into or out of email workflows without leaving Janus.

The feature remains safety-first because every mailbox or filesystem action still requires a direct user trigger.

## TARGET SURFACE

- Primary Target Surface: Janus Mail thread detail and composer area
- Existing or New Surface: Existing Mail surface extended with manual action controls
- User Trigger: User clicks reply, send, archive, restore, trash, attach file, or save attachment
- Success Behavior: Requested action completes visibly, the thread state updates, and the user receives confirmation feedback
- Failure Behavior: The action fails locally with clear feedback while the thread view remains stable and understandable
- Explicit Non-Surfaces: Autonomous mail rules, background filing, permanent delete, bulk mailbox operations

## USER ACTION SURFACE

- Action Type: Manual mail mutation and attachment handling
- Trigger: Explicit button or composer action inside Janus Mail
- User Input: Reply text, new message content, action choice, attachment add, attachment save destination
- Immediate Feedback: Visible progress plus confirmation feedback, including undo where the action is reversibly supported in-surface
- Result: Mail is sent or mailbox state changes only after an explicit user action
- Cancel / Undo Behavior: Composer can be abandoned before send, and reversible organization actions can offer immediate undo inside the active surface
- Non-Effects: No auto-send, no background filing, no AI-triggered mutation

## SYSTEM BEHAVIOR

All mailbox-changing actions must be explicitly user-confirmed through direct UI interaction.

For this MVP slice, organization actions cover archive, restore to inbox, and move to trash. Janus must not imply broad custom label management if that is not part of this step.

Outgoing mail must be editable before send. A generated or quoted reply may help the user, but sending itself remains a separate explicit action.

The user must be able to attach a local file while composing and save an incoming attachment locally from the thread view.

When a mutation succeeds, the thread list and active thread detail must reflect the new state without forcing the user to rediscover the conversation manually.

Undo contract for this MVP slice is deterministic:

- Archive: Undo supported via immediate "restore to inbox" action in surface toast window.
- Move to trash: Undo supported via immediate "restore to inbox" action in surface toast window.
- Restore to inbox: No additional undo is promised.
- Send mail: No undo is promised.

If the provider confirms an action but an immediate undo fails, Janus must show explicit undo-failed feedback and the final provider state after refresh.

## DATA / PERSISTENCE

- Persistence Required: YES
- Data Created: Ausgehende Gmail Nachrichten und lokal gespeicherte Anhangsdateien
- Data Updated: Gmail Thread-Zustand und sichtbarer Organisationsstatus fuer die betroffene Konversation
- Data Deleted: Keine dauerhafte Janus-interne Maildatenhaltung; providerseitige Zustandsaenderungen koennen Nachrichten in Trash verschieben
- Source of Truth: Gmail fuer Mailzustand und lokales Dateisystem fuer bewusst gespeicherte Anhaenge
- Recovery Behavior: Bei Aktionsfehlern bleibt die letzte stabile Threadansicht erhalten und zeigt klar, dass die Mutation nicht erfolgreich war

## CONSTRAINTS

This phase must preserve the user-confirmed-actions-only rule without exceptions.

Trash in this MVP means provider-side move to trash, not irreversible permanent deletion.

Attachment handling must be explicit and local; Janus must not silently download, inspect, or redistribute files.

Attachment save safety contract for this MVP slice is deterministic:

- Save destination is always user-selected at action time.
- Filenames are sanitized before write.
- Existing files are never overwritten silently.
- Path traversal segments in attachment filenames are never honored as filesystem paths.

This step must not expand into arbitrary Gmail label management, batch actions, or account-wide cleanup tools.

## SECURITY / PRIVACY

- Sensitive Data Involved: YES
- External Services Involved: YES, Gmail write operations and attachment-related mail transfer
- Secrets Required: YES, existing Google auth material is required but never printed
- Privacy Impact: Message content and attachment filenames are highly sensitive and must remain user-scoped
- Security Constraints: No hidden send, no permanent delete shortcut, no unsafe file path behavior, and no secret or attachment leakage in logs or generic UI

## EDGE CASES

If send fails, the composed message state must stay recoverable enough that the user does not lose confidence in what happened.

If an attachment cannot be added or saved, the rest of the composer or thread view must remain stable.

If a saved filename collides locally, the user-facing behavior must stay explicit rather than silently overwriting unrelated files.

If a reversible mailbox action cannot be undone in the current moment, Janus must not promise undo that it cannot actually perform.

If Gmail rejects an attachment or a mailbox mutation, the user must see the failure as a local action result rather than a silent refresh mismatch.

## DEFINITION OF DONE

- [ ] Wenn der Nutzer eine Antwort verfasst und auf Senden klickt, dann wird die Nachricht nur nach dieser expliziten Aktion versendet.
- [ ] Wenn der Nutzer Archivieren, Restore oder Trash ausloest, dann aktualisiert sich die betroffene Konversation sichtbar und bestaetigt den Zustand.
- [ ] Wenn eine Aktion rueckgaengig gemacht werden kann, dann bietet Janus direktes Undo nur fuer diese real unterstuetzte Situation an.
- [ ] Wenn der Nutzer beim Schreiben einen lokalen Anhang hinzufuegt, dann bleibt der Composer stabil und der Anhang ist fuer den Versand sichtbar.
- [ ] Wenn der Nutzer einen empfangenen Anhang speichert, dann erfolgt dies nur nach expliziter Nutzeraktion und mit nachvollziehbarem Ergebnis.
- [ ] Wenn eine Mail- oder Dateiakion fehlschlaegt, dann bleibt die Mail-Surface benutzbar und zeigt einen klaren lokalen Fehlerzustand.

## TEST STRATEGY

- Manual Validation: Reply senden, Archivieren, Restore, Trash, Anhang hinzufuegen, Anhang speichern, Undo-Verhalten pruefen
- Automated Validation Candidates:
- Wenn Reply-Draft vorhanden ist und send explizit ausgeloest wird, dann erfolgt genau ein send request.
- Wenn archive ausgefuehrt wird, dann zeigt die Surface Undo fuer das definierte Zeitfenster und kann zu inbox restore wechseln.
- Wenn move-to-trash ausgefuehrt wird, dann zeigt die Surface Undo fuer das definierte Zeitfenster und kann zu inbox restore wechseln.
- Wenn restore-to-inbox ausgefuehrt wird, dann wird kein weiteres Undo versprochen.
- Wenn attachment-save mit kollidierendem Dateinamen auftritt, dann wird nicht still ueberschrieben und der Nutzer sieht einen expliziten Konfliktpfad.
- Wenn attachment-filename Traversal-Anteile enthaelt, dann wird nur ein sicherer lokaler Dateiname geschrieben.
- Regression Areas: Thread detail stability, mailbox state refresh, local file handling, Gmail write boundaries
- Failure Case Validation: Sendfehler, abgelehnter Anhang, lokaler Dateifehler, nicht verfuegbares Undo, providerseitig abgelehnte Mutation

## OUT OF SCOPE

Arbitrary custom label management

Permanent delete

Bulk actions across many threads

Attachment preview or attachment AI analysis

Autonomous reply, autonomous filing, or hidden send behavior

## INTERNAL COMPLEXITY BREAKDOWN

Scope Size: 15
Architectural Risk: 14
State / Persistence Complexity: 14
Cross-System Dependencies: 13
Ambiguity Level: 11
Total Complexity Score: 67
Routing Decision: GPT_5_5
Routing Confidence: MEDIUM
Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 67
- **Risk:** HIGH
- **Recommended Review Model:** 5.5
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-05-28
- **Review Confidence:** MEDIUM
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS WITH FIXES
- **Completed At:** 2026-05-30
- **Implementation Task:** documentation/tasks/task_098_janus_mail_bundle_generated.md
- **Validation Evidence:** py_compile PASS; backend mail/intent/privacy tests PASS; frontend mail modal tests PASS

