# JANUS FEATURE SPEC – DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: SPEC_REVIEW
execution_mode: GPT_5_5
complexity_score: 72
confidence: MEDIUM
dashboard_hint: CAUTION
reason: Adds privacy-sensitive AI thread assistance and editable draft replies without permitting autonomous mailbox actions.

## FEATURE IDENTITY

- Feature Name: Janus Mail AI Thread Assist and Draft Replies
- Source Input: Latest approved Janus Mail decision summary from 2026-05-27
- Depends On: documentation/SPEC/11_janus_mail_gmail_thread_inbox_and_search.md and documentation/SPEC/12_janus_mail_manual_actions_and_attachments.md
- Primary Goal: Add thread summary, reply-needed signal, priority guidance, and editable reply drafts inside Janus Mail
- User Problem: Users can read and act on mail, but still spend too much effort understanding thread context and drafting suitable replies
- User Value: Users get practical AI help inside the thread while keeping final editorial and sending control

## USER VALUE

This step adds the first real AI value layer to Janus Mail without turning it into an autonomous agent.

The user can understand a conversation faster, see whether a reply is likely needed, and start from a draft instead of a blank composer.

The feature stays aligned with trust and privacy because AI remains advisory, scoped to the active thread, and never sends or files mail by itself.

## TARGET SURFACE

- Primary Target Surface: Janus Mail thread detail AI panel and draft reply area
- Existing or New Surface: Existing Mail surface extended with in-thread AI assistance
- User Trigger: User opens a thread and views or refreshes AI assistance, or requests an AI draft reply with a selected tone
- Success Behavior: Janus shows a useful thread summary, reply-needed guidance, priority signal, and an editable draft reply inside the active thread
- Failure Behavior: AI assistance degrades gracefully to a visible unavailable or fallback state without breaking mail reading or manual reply
- Explicit Non-Surfaces: Mailbox-wide autonomous triage, hidden AI sending, background account automation

## USER ACTION SURFACE

- Action Type: In-thread AI assistance and draft generation
- Trigger: Open thread, refresh AI help, choose a reply tone, request a draft
- User Input: Tone selection and optional lightweight drafting instruction
- Immediate Feedback: AI panel updates with summary and guidance, and the draft reply appears as editable text
- Result: User receives actionable AI help but still owns the final message and send decision
- Cancel / Undo Behavior: User can ignore AI output, request a new draft, or manually overwrite the draft before send
- Non-Effects: No automatic send, no automatic archive or trash, no forced mailbox-wide AI scan

## SYSTEM BEHAVIOR

AI assistance must stay thread-scoped for this MVP slice rather than running as autonomous whole-mailbox processing.

The AI panel must present a short thread summary, a visible reply-needed signal, and a priority indicator that helps the user decide what matters first.

Draft replies must remain editable before send, and tone selection must shape the draft without making the send action implicit.

If AI output is unavailable, malformed, low-confidence, or stale, Janus must preserve manual mailbox use and show a clear degraded state rather than fabricated certainty.

Janus must not automatically analyze attachments, create tasks, schedule calendar items, or trigger mailbox mutations in this phase.

AI consent contract for this MVP slice is deterministic:

- Global default is OFF for AI Mail Assist.
- While OFF, no thread content is sent to any AI provider.
- User can explicitly enable AI Mail Assist in settings before AI thread assistance is available.
- After global enable, user can still disable AI for a single thread using an in-thread toggle.
- If per-thread AI toggle is OFF, that thread content is not sent to an AI provider.

## DATA / PERSISTENCE

- Persistence Required: YES
- Data Created: Leichtgewichtige AI-Metadaten und bearbeitbare Reply-Drafts fuer aktive Gmail Threads
- Data Updated: Vorhandene AI-Zusammenfassungen, Prioritaetshinweise und Draft-Zustaende koennen fuer dieselbe Konversation erneuert werden
- Data Deleted: Veraltete oder verworfene Draft-Zustaende duerfen ersetzt werden; keine dauerhafte lokale Vollkopie der Mailbox
- Source of Truth: Gmail Thread-Inhalt plus Janus AI-Ausgaben fuer die aktive Konversation
- Recovery Behavior: Wenn AI-Daten fehlen oder unbrauchbar sind, kann die Surface manuell weitergenutzt und AI bei Bedarf erneut angefordert werden

## CONSTRAINTS

AI is advisory only in this phase.

There must be no hidden provider fallback for AI processing and no fake success if the configured provider is unavailable.

AI support must stay limited to summary, reply-needed guidance, priority guidance, and editable draft reply output.

This step must not expand into autonomous task extraction, calendar suggestions, or background whole-mailbox scoring.

If AI consent is not granted under the contract above, the AI panel must render a consent-required state instead of partial or implicit analysis.

## SECURITY / PRIVACY

- Sensitive Data Involved: YES
- External Services Involved: YES, Gmail content plus the configured Janus AI provider
- Secrets Required: YES, existing provider credentials are required but never printed
- Privacy Impact: Thread content may be processed by the configured AI provider, so scope, transparency, and no-fallback behavior are critical
- Security Constraints: No hidden mailbox-wide AI pass, no autonomous action execution, and no leakage of private thread content into unrelated UI or logs

## EDGE CASES

If a thread is too long for the preferred AI path, the user must still receive a controlled degraded experience rather than a broken panel.

If a thread language differs from the requested draft tone or user expectation, Janus must still keep the draft editable and obviously user-owned.

If a new message arrives after an older AI summary was shown, the summary state must not imply it is still current when it is not.

If the AI provider fails or returns unusable output, the user must still be able to read, write, and send mail manually.

If the user does not want AI for a sensitive thread, the manual thread workflow must remain complete without AI dependence.

## DEFINITION OF DONE

- [ ] Wenn der Nutzer einen Thread mit AI-Unterstuetzung oeffnet oder aktualisiert, dann zeigt Janus eine kurze Zusammenfassung, Prioritaet und Reply-Hinweis im Thread-Kontext.
- [ ] Wenn der Nutzer einen Antwortentwurf anfordert, dann erscheint der Entwurf als editierbarer Text und wird nicht automatisch versendet.
- [ ] Wenn der Nutzer einen Ton auswaehlt, dann beeinflusst dieser den Entwurf sichtbar, ohne die finale Kontrolle ueber die Nachricht zu entziehen.
- [ ] Wenn AI-Unterstuetzung scheitert oder unbrauchbar ist, dann bleibt die manuelle Mailnutzung voll benutzbar.
- [ ] Wenn ein Thread sensibel oder aktuell veraendert ist, dann behauptet Janus keine verborgene Vollstaendigkeit oder sichere Automatik.

## TEST STRATEGY

- Manual Validation: AI-Zusammenfassung pruefen, Reply-Hinweis beobachten, Prioritaet sichtbar machen, Draft mit verschiedenen Toenen erzeugen und manuell ueberschreiben
- Automated Validation Candidates:
- Wenn global AI Mail Assist OFF ist, dann rendert der Thread AI panel consent-required und sendet keinen AI analyze request.
- Wenn global AI Mail Assist ON und per-thread toggle ON ist, dann kann AI summary fuer genau diesen Thread erzeugt werden.
- Wenn per-thread toggle OFF ist, dann wird kein AI request fuer diesen Thread ausgefuehrt.
- Wenn AI draft angefordert wird, dann ist das Ergebnis editierbar und triggert keinen send request.
- Wenn AI provider fehlschlaegt, dann bleibt manueller Reply-Flow nutzbar und der Fehlerzustand ist sichtbar.
- Wenn nach Summary neue Threadnachricht eintrifft, dann markiert der AI panel status die Summary als potenziell stale.
- Regression Areas: Thread detail rendering, manual composer ownership, provider error visibility, privacy-safe AI behavior
- Failure Case Validation: AI provider nicht verfuegbar, ungueltige AI-Antwort, neuer Threadstand nach Summary, sensitive Konversation ohne AI-Abhaengigkeit

## OUT OF SCOPE

Autonomous send or filing

Mailbox-wide automatic triage in the background

Task extraction, calendar proposals, or memory-driven proactive follow-ups

Attachment analysis by AI

Multi-provider AI routing or hidden fallback behavior

## INTERNAL COMPLEXITY BREAKDOWN

Scope Size: 13
Architectural Risk: 15
State / Persistence Complexity: 12
Cross-System Dependencies: 14
Ambiguity Level: 18
Total Complexity Score: 72
Routing Decision: GPT_5_5
Routing Confidence: MEDIUM
Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 72
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

