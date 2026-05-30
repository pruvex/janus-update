# JANUS FEATURE SPEC – DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: SPEC_REVIEW
execution_mode: SWE_1_6
complexity_score: 48
confidence: MEDIUM
dashboard_hint: CAUTION
reason: Introduces live Gmail thread-first inbox reading and Gmail-backed search without yet allowing destructive mail changes.

## FEATURE IDENTITY

- Feature Name: Janus Mail Gmail Thread Inbox and Search
- Source Input: Latest approved Janus Mail decision summary from 2026-05-27
- Primary Goal: Show Gmail mail as thread-first inbox content with searchable, readable thread detail inside Janus Mail
- User Problem: Even with a Mail shell, users still need a real inbox view to inspect conversations and find messages quickly
- User Value: Users can read and search their Gmail conversations in Janus without leaving the product

## USER VALUE

This step turns the shell into a useful mailbox surface by loading Gmail conversations and making them readable in a thread-first way.

The user can scan a list of conversations, search with familiar Gmail semantics, and open a thread detail view without yet risking message mutations.

Because the phase is read-focused, it gives us an early integration checkpoint before reply, delete, or AI behavior is introduced.

## TARGET SURFACE

- Primary Target Surface: Janus Mail module content area for thread list and thread detail
- Existing or New Surface: Existing Mail surface extended with live Gmail content
- User Trigger: User opens Mail while connected and optionally enters a Gmail search query
- Success Behavior: Thread list appears, search returns matching Gmail threads, and selecting a thread shows readable chronological messages
- Failure Behavior: Search or load failures stay localized to the mail content state with explicit user feedback
- Explicit Non-Surfaces: Chat-driven mailbox browsing, offline inbox, local search index

## USER ACTION SURFACE

- Action Type: Browse, select thread, search
- Trigger: Open Mail, click a visible thread, submit or clear a search query
- User Input: Search text and thread selection
- Immediate Feedback: Matching thread list updates and selected thread detail becomes visible
- Result: User can inspect Gmail conversations in Janus
- Cancel / Undo Behavior: User can clear search or select a different thread without side effects
- Non-Effects: No send, no delete, no archive, no AI draft generation

## SYSTEM BEHAVIOR

The inbox must be thread-first, which means the list represents Gmail conversations rather than individual loose messages.

Search must use Gmail-backed query behavior for this MVP instead of creating a separate Janus-local search system.

Selecting a thread must show its messages in chronological reading order with enough message context to understand the conversation flow.

If a message body cannot be rendered in its preferred representation, Janus must still show a readable fallback rather than failing the whole thread view.

Empty inbox and no-result states must be distinct so the user can tell whether there is nothing to read or whether the current search simply found nothing.

## DATA / PERSISTENCE

- Persistence Required: NO
- Data Created: Keine neue dauerhafte Mailhistorie in Janus
- Data Updated: Laufende Gmail Thread- und Suchergebnisse im Arbeitsspeicher
- Data Deleted: Keine
- Source of Truth: Gmail Threads und Gmail Search Ergebnisse fuer den aktiven Gmail Account
- Recovery Behavior: Bei Lade- oder Suchfehlern bleibt die letzte stabile Mail-Surface erhalten und zeigt einen lokalen Fehlerzustand

## CONSTRAINTS

Gmail thread identity is authoritative in this phase; Janus must not invent its own independent thread grouping model.

Search must remain Gmail-backed, not Janus-index-backed.

This phase remains read-only even though attachment presence may be visible inside a thread.

The surface must stay Gmail-only and must not imply full multi-account behavior yet.

## SECURITY / PRIVACY

- Sensitive Data Involved: YES
- External Services Involved: YES, Gmail message content and search are provider-backed
- Secrets Required: YES, existing Google auth material is required but never printed
- Privacy Impact: Message content becomes visible in-product and must remain scoped to the active user session
- Security Constraints: No cross-provider fallback, no hidden mail export, and no leaking full message content into unrelated UI areas

## EDGE CASES

An empty inbox must show a meaningful no-mail state.

A search with zero matches must show a no-results state that is different from an empty inbox.

Very long threads must remain readable without collapsing the entire module.

If a Gmail thread loads partially or contains malformed content, Janus must still present a usable thread detail state.

If the selected thread disappears because the search changes, the detail area must return to a stable neutral state.

## DEFINITION OF DONE

- [ ] Wenn Gmail verbunden ist, dann zeigt Janus Mail eine Threadliste statt einer leeren Shell.
- [ ] Wenn der Nutzer eine Suchanfrage ausfuehrt, dann aktualisiert sich die Threadliste mit Gmail-basierten Ergebnissen.
- [ ] Wenn der Nutzer einen Thread auswaehlt, dann zeigt Janus die enthaltenen Nachrichten in lesbarer chronologischer Reihenfolge.
- [ ] Wenn keine Threads oder keine Suchtreffer vorhanden sind, dann zeigt Janus unterschiedliche und verstaendliche Leerzustaende.
- [ ] Wenn ein Lade- oder Suchfehler auftritt, dann bleibt die Mail-Surface stabil und zeigt einen lokalen Fehlerzustand statt eines Workspace-Bruchs.

## TEST STRATEGY

- Manual Validation: Threadliste laden, Suche pruefen, Threaddetail mit mehreren Nachrichten kontrollieren, Leer- und Fehlerzustaende pruefen
- Automated Validation Candidates:
- Wenn Gmail thread payload mit N Threads geliefert wird, dann rendert die Liste N Thread-Eintraege.
- Wenn eine gueltige Gmail-Query eingegeben wird, dann wird exakt diese Query an den Gmail-backed search path weitergegeben.
- Wenn ein Thread ausgewaehlt wird, dann rendert das Detail Nachrichten in chronologischer Reihenfolge.
- Wenn Suchergebnis leer ist, dann rendert no-results und nicht no-inbox.
- Wenn Threaddetail-Render fehlschlaegt, dann bleibt Liste bedienbar und der Fehlerzustand ist lokal im Detailbereich.
- Regression Areas: Mail shell layout, Gmail connectivity state, content rendering fallback, workspace navigation
- Failure Case Validation: Leere Inbox, keine Suchtreffer, fehlerhafte Nachrichtendarstellung, unterbrochene Suche

## OUT OF SCOPE

Antworten oder neue Nachrichten senden

Archivieren, Restore, Trash oder sonstige Mailmutation

Anhaenge lokal speichern oder versenden

Eigener Janus Suchindex

KI-Zusammenfassungen, Prioritaet oder Antwortentwuerfe

## INTERNAL COMPLEXITY BREAKDOWN

Scope Size: 12
Architectural Risk: 10
State / Persistence Complexity: 6
Cross-System Dependencies: 14
Ambiguity Level: 6
Total Complexity Score: 48
Routing Decision: SWE_1_6
Routing Confidence: MEDIUM
Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED
- **Complexity Score:** 48
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

