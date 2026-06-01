# JANUS FEATURE SPEC – DIAMANTSTANDARD v4.4.3

## SPEC REVIEW EXECUTION ROUTING

target_skill: SPEC_REVIEW
execution_mode: SWE_1_6
complexity_score: 44
confidence: MEDIUM
dashboard_hint: CAUTION
reason: Extends the working Janus Mail chat with scoped provider-plus-category search and ambiguity handling without changing the core mail surface.

## FEATURE IDENTITY

- Feature Name: Generische Anbieter-Mail-Suche nach Inhaltstypen
- Source Input: Latest approved decision summary for BACKLOG-100 plus locked user constraint that the existing mail feature already works and must only be optimized
- Depends On: documentation/SPEC/Spec Done/10_janus_mail_module_shell_and_connection_state.md and documentation/SPEC/Spec Done/11_janus_mail_gmail_thread_inbox_and_search.md
- Primary Goal: Let users find mails from one provider for one requested content type directly in the existing mail chat
- User Problem: Users can already use Janus Mail, but still need a fast natural-language way to pull out mails like recipes, receipts, invoices, or order confirmations from a specific sender without manually searching
- User Value: Users get targeted mail retrieval in the current workflow with clear results and without destabilizing the existing mail experience

## USER VALUE

This feature turns an already useful mail flow into a more practical day-to-day retrieval tool.

Instead of browsing or writing broad searches manually, the user can ask for one provider and one content type in plain language and get a direct result list in chat.

The scope stays intentionally narrow so Janus improves the existing mail feature rather than reshaping it.

## TARGET SURFACE

- Primary Target Surface: Existing Janus Mail chat flow
- Existing or New Surface: Existing surface extended with scoped content-type-aware mail search behavior
- User Trigger: User asks in the mail chat for mails from one provider with one requested content type
- Success Behavior: Janus returns a compact result list in chat with provider, subject, date, detected category, and short evidence summary for each hit
- Failure Behavior: Janus asks a focused clarification question when provider or content type is ambiguous, or shows a stable no-results or unavailable response without disrupting mail usage
- Explicit Non-Surfaces: Dedicated mail search page, separate advanced filter UI, mailbox-wide dashboard, multi-provider batch search

## USER ACTION SURFACE

- Action Type: Natural-language retrieval request
- Trigger: User sends one mail-chat request such as "Finde alle Bons von Rewe" or "Zeig mir alle Rezeptmails von Picnic"
- User Input: One provider plus one content type in free text
- Immediate Feedback: Janus either starts a scoped search or asks a concise clarification question
- Result: User receives a directly readable hit list in the existing chat
- Cancel / Undo Behavior: User can refine, restate, or narrow the query in follow-up chat messages without side effects
- Non-Effects: No send, no archive, no delete, no mailbox mutation, no background bulk scan beyond the requested scope

## SYSTEM BEHAVIOR

Janus must interpret the request as a combination of exactly one provider and exactly one content type for the first version of this feature.

The content type must be treated as a user-facing semantic category such as recipe, receipt, invoice, order confirmation, or delivery confirmation rather than as a provider-specific hardcoded rule.

Janus must use the existing mail context and connection state behavior as the foundation and must not replace the current working mail flow with a new interaction model.

If the provider name or requested content type is missing or ambiguous, Janus must ask a targeted clarification question before executing a broad search.

If matching messages are found, Janus must return a compact list in chat that makes it obvious why each result belongs to the requested category.

If no matches are found, Janus must clearly say that no matching mails were found for that provider-and-category combination instead of fabricating weak matches.

This optimization must not degrade existing mail reading, thread browsing, Gmail-backed search, or current consent behavior.

## DATA / PERSISTENCE

- Persistence Required: NO
- Data Created: Keine neue dauerhafte Maildatenhaltung fuer diese Funktion
- Data Updated: Temporaere Such- und Klassifizierungsergebnisse im aktiven Mail-Chat-Kontext
- Data Deleted: Keine
- Source of Truth: Verbundene Maildaten des aktiven Mailkontos plus bestehender Janus Mail-Kontext
- Recovery Behavior: Bei Fehlern oder fehlender Verbindung bleibt der bestehende Mail-Chat nutzbar und zeigt einen lokalen, klaren Fehlerzustand

## CONSTRAINTS

This is an optimization of a working mail feature, not a redesign.

The first version must remain limited to one provider and one content type per request.

No provider-specific special handling may be required for basic success, even if certain providers become useful examples during validation.

The feature must preserve the current mail behavior when the user is not making this kind of targeted request.

Regression risk on the existing mail flow is a primary constraint and must be treated as part of feature correctness.

## SECURITY / PRIVACY

- Sensitive Data Involved: YES
- External Services Involved: YES, existing connected mail provider access is required
- Secrets Required: YES, existing mail auth material is required but never printed
- Privacy Impact: Mail content is searched and lightly categorized for the active user request, so scope control and no-overreach behavior are important
- Security Constraints: No hidden mailbox-wide export, no broad search without clear request intent, no bypass of existing mail consent or connection-state protections

## EDGE CASES

If the user names a provider but no content type, Janus must ask which kind of mail is meant.

If the user names a content type but no provider, Janus must ask which provider should be searched.

If the provider term could refer to multiple sender identities, Janus must clarify before returning results.

If a mail partly matches but the category signal is weak, Janus must prefer not returning it over pretending certainty.

If the mail account is disconnected or consent is unavailable, Janus must report that state cleanly and keep the rest of the mail experience stable.

If no results are found, Janus must return a no-results response that is clearly different from connection failure or ambiguity.

## DEFINITION OF DONE

- [ ] Wenn der Nutzer im bestehenden Mail-Chat einen Anbieter und einen Inhaltstyp nennt, dann zeigt Janus passende Treffer direkt im Chat statt auf eine neue Surface auszuweichen.
- [ ] Wenn Janus Treffer zeigt, dann enthaelt jeder Treffer mindestens Anbieter, Betreff, Datum, erkannte Kategorie und eine kurze Fundstellen-Zusammenfassung.
- [ ] Wenn Anbieter oder Inhaltstyp in der Anfrage nicht eindeutig sind, dann stellt Janus vor der Suche eine gezielte Rueckfrage.
- [ ] Wenn keine passenden Mails existieren, dann zeigt Janus einen klaren No-Results-Zustand statt unpraezise oder erfundene Treffer.
- [ ] Wenn das Feature nicht verwendet wird oder eine Suche fehlschlaegt, dann bleiben bestehende Mail-Funktionen wie Lesen, Thread-Browsing und normaler Mail-Chat unveraendert stabil.

## TEST STRATEGY

- Manual Validation: Anbieter-plus-Kategorie-Anfragen im bestehenden Mail-Chat pruefen, Trefferlisten kontrollieren, Rueckfragen bei Mehrdeutigkeit pruefen, No-Results- und Disconnect-Faelle pruefen
- Automated Validation Candidates:
- Wenn eine Anfrage genau einen Anbieter und einen Inhaltstyp enthaelt, dann wird sie als scoped mail retrieval request erkannt.
- Wenn Anbieter oder Inhaltstyp fehlen oder mehrdeutig sind, dann wird vor der Suche eine Rueckfrage erzeugt.
- Wenn passende Mails gefunden werden, dann ist die Antwortliste kompakt, kategorisiert und nachvollziehbar statt generisch.
- Wenn keine Mails passen, dann rendert Janus einen No-Results-Zustand statt eines allgemeinen Fehlers.
- Wenn andere bestehende Mail-Interaktionen ausgefuehrt werden, dann bleiben deren Antworten und Zustandswechsel unveraendert.
- Regression Areas: Existing mail chat behavior, Gmail-backed search behavior, connection-state handling, consent enforcement
- Failure Case Validation: Ambiguous provider, missing content type, disconnected mail account, weak category evidence, empty result set

## OUT OF SCOPE

Neue Mail-Suchansicht oder separates Search-Panel

Mehrere Anbieter oder mehrere Inhaltstypen in einer einzigen Anfrage

Anbieter-spezifische Sonderregeln als Voraussetzung fuer Kernfunktionalitaet

Mailbox-weite automatische Kategorisierung im Hintergrund

Mail-Mutationen wie Senden, Archivieren, Loeschen oder Labeln

## INTERNAL COMPLEXITY BREAKDOWN

Scope Size: 9
Architectural Risk: 9
State / Persistence Complexity: 6
Cross-System Dependencies: 12
Ambiguity Level: 8
Total Complexity Score: 44
Routing Decision: SWE_1_6
Routing Confidence: MEDIUM
Dashboard Hint: CAUTION

## SPEC REVIEW METADATA

- **Review Status:** APPROVED_WITH_NOTES
- **Complexity Score:** 44
- **Risk:** MEDIUM
- **Recommended Review Model:** 5.4
- **Skill-1 Ready:** YES
- **Split Required:** NO
- **Reviewed At:** 2026-05-31
- **Review Confidence:** HIGH
- **Review Source:** janus-spec-review

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS
- **Completion Date:** 2026-06-01
- **Validation Evidence:**
  - `python -m py_compile backend/services/chat_orchestrator.py backend/main.py backend/services/memory_extractor.py` -> PASS
  - `python -m pytest backend/tests/unit/test_chat_mail_provider_content_type_probe.py backend/tests/test_mail_service.py backend/tests/test_mail_chat_account_guard_store.py -q` -> PASS (39 passed)
  - `node --test frontend/tests/mail-inbox-ui.test.mjs` -> PASS (3 passed)
  - Manual Janus evidence from `AUDIT_PACKAGE.md`: provider/category account-selection flow, recipe detail rendering, multi-index PDF export, and Desktop folder matching present.
