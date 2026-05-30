# JANUS FEATURE SPEC – DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: SPEC_REVIEW
execution_mode: SWE_1_6
complexity_score: 34
confidence: HIGH
dashboard_hint: CAUTION
reason: New Janus mail workspace shell with Gmail auth state handling, but no mail data or destructive actions yet.

## FEATURE IDENTITY

- Feature Name: Janus Mail Module Shell and Connection State
- Source Input: Latest approved Janus Mail decision summary from 2026-05-27
- Primary Goal: Introduce a dedicated Janus Mail dock module with a calendar-like two-column shell and clear Gmail connection states
- User Problem: Janus has no dedicated mail workspace, so users cannot enter a mail flow or understand Gmail connection problems inside the product
- User Value: Users get a stable mail entry surface that already feels like Janus and explains what to do when Gmail is unavailable

## USER VALUE

Janus gains a real mail surface instead of scattering mail behavior across chat or tool responses.

The user can open Mail from the Dock, recognize the future workspace shape immediately, and recover from Gmail auth or scope problems without guessing.

This creates a safe first step for the feature because the shell can be tested visually and behaviorally before live mailbox data is introduced.

## TARGET SURFACE

- Primary Target Surface: New Mail dock or modal module inside the existing Janus workspace
- Existing or New Surface: New surface built on the existing Dock and modal pattern
- User Trigger: User opens Mail from the Janus Dock
- User Trigger: User opens Mail from the Janus Dock or from the existing sidebar module list
- Success Behavior: A two-column mail workspace opens with navigation shell and a clear connected or disconnected state
- Failure Behavior: The module stays usable and shows an explicit status or reconnect state instead of a blank or broken panel
- Explicit Non-Surfaces: Chat panel, background automation, standalone browser mail UI

## USER ACTION SURFACE

- Action Type: Dock open, navigation selection, reconnect initiation
- Trigger: Click on the Mail Dock entry, the Mail entry in the sidebar module list, or visible reconnect controls
- User Input: Open Mail, inspect status, choose visible mail navigation areas
- Immediate Feedback: Mail workspace opens immediately and shows connected, missing-auth, missing-scope, or sync-error state
- Result: User understands whether Mail is ready and what the next manual action is
- Cancel / Undo Behavior: User can close or minimize the module without side effects
- Non-Effects: No mailbox data mutation, no message send, no delete, no AI processing

## SYSTEM BEHAVIOR

When the user opens Mail, Janus presents a dedicated workspace that visually aligns with the calendar module and reserves a left area for account and navigation context plus a right area for the active mail content state.

If Gmail is not connected, required scopes are missing, or sync is not currently possible, the mail surface must show a clear state card that explains the problem and the next user-facing recovery action.

The shell must be account-ready, which means it visibly accommodates an account area and an add-account placeholder, but only one Gmail account is active in this first step.

The shell must not pretend that mailbox content is loaded when it is not. Empty placeholders are acceptable only when they are explicit and meaningful.

## DATA / PERSISTENCE

- Persistence Required: NO
- Data Created: Keine neue dauerhafte Maildatenhaltung
- Data Updated: Bestehender Janus window state darf unveraendert genutzt werden
- Data Deleted: Keine
- Source of Truth: Laufender Gmail Verbindungszustand plus bestehender Janus workspace state
- Recovery Behavior: Bei fehlender Verbindung oder fehlerhaftem Auth-Zustand zeigt die Surface einen klaren Wiederherstellungszustand

## CONSTRAINTS

The module must follow the established Janus Dock or modal interaction pattern rather than inventing a separate mail application shell.

The module must be reachable from the same sidebar module list that already opens Image Studio and Calendar.

The first step must remain Gmail-only even though the layout is prepared for future additional accounts.

The module must keep a two-column layout that stays visually close to the calendar feature rather than shifting into a three-column desktop client in this phase.

The shell must not include mailbox content, search results, mail actions, or AI decisions in this step.

The shell must include an explicit "AI Mail Assist" global setting placeholder with default state OFF and explanatory text that no thread content is sent to an AI provider while OFF.

## SECURITY / PRIVACY

- Sensitive Data Involved: YES
- External Services Involved: YES, Gmail connection status is provider-backed
- Secrets Required: YES, existing Google auth material is required but never printed
- Privacy Impact: Mail readiness states can reveal whether a mailbox is connected, so the surface must stay user-local and explicit
- Security Constraints: No secrets in UI text, no auth bypass, no hidden background retries that mask real provider failures

## EDGE CASES

Missing Gmail connection must show a recoverable state instead of a generic empty module.

Missing Gmail scopes must be distinguishable from a generic network or provider error.

A temporary sync failure must not remove the entire mail shell or break Dock behavior.

If the user opens Mail before any account is available, the account-ready placeholder must stay visible and understandable.

If the module is reopened repeatedly, it must return to a stable shell state rather than duplicating views or controls.

## DEFINITION OF DONE

- [ ] Wenn der Nutzer Mail ueber den Dock oeffnet, dann erscheint eine eigene Mail-Surface im Janus Workspace.
- [ ] Wenn der Nutzer Mail ueber den Dock oder die Sidebar-Liste oeffnet, dann erscheint dieselbe Mail-Surface im Janus Workspace.
- [ ] Wenn Gmail korrekt verbunden ist, dann zeigt die Surface einen klaren bereit-Zustand statt einer Fehler- oder Leerseite.
- [ ] Wenn Gmail nicht verbunden ist oder Rechte fehlen, dann zeigt die Surface einen klaren Status mit naechster Nutzeraktion.
- [ ] Wenn der Nutzer Mail schliesst oder minimiert, dann bleibt der restliche Janus Workspace stabil.
- [ ] Wenn noch kein weiterer Provider existiert, dann bleibt die Account-Area sichtbar zukunftsfaehig, aber technisch Gmail-only.

## TEST STRATEGY

- Manual Validation: Mail ueber Dock oeffnen, Statuszustaende pruefen, Shell visuell gegen Kalender-Pattern vergleichen
- Automated Validation Candidates: 
- Wenn Dock-Action "open mail" ausgeloest wird, dann existiert genau eine sichtbare Mail-Surface Instanz.
- Wenn Gmail auth status auf disconnected gesetzt wird, dann rendert die Surface den reconnect state und keine pseudo-inbox.
- Wenn Gmail auth status auf missing_scope gesetzt wird, dann rendert die Surface einen unterscheidbaren permissions state.
- Wenn Mail-Modul geschlossen und erneut geoeffnet wird, dann bleibt der Shell-Status stabil und dupliziert keine Container.
- Regression Areas: Dock integration, modal layering, workspace focus behavior, calendar visual consistency
- Failure Case Validation: Kein Gmail Auth, fehlende Scopes, providerseitiger Fehler, wiederholtes Oeffnen und Schliessen

## OUT OF SCOPE

Threadliste oder Nachrichtendetails

Mailbox-Suche

Antworten, Senden, Archivieren, Trash oder Restore

Anhaenge senden oder speichern

KI-Zusammenfassungen oder Antwortentwuerfe

## INTERNAL COMPLEXITY BREAKDOWN

Scope Size: 8
Architectural Risk: 6
State / Persistence Complexity: 4
Cross-System Dependencies: 10
Ambiguity Level: 6
Total Complexity Score: 34
Routing Decision: SWE_1_6
Routing Confidence: HIGH
Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED
- **Complexity Score:** 34
- **Risk:** MEDIUM
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-05-28
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS WITH FIXES
- **Completed At:** 2026-05-30
- **Implementation Task:** documentation/tasks/task_098_janus_mail_bundle_generated.md
- **Validation Evidence:** py_compile PASS; backend mail/intent/privacy tests PASS; frontend mail modal tests PASS

