# TASK FILE - TASK-SPEC15

TASK-SPEC15
- Source Spec: documentation/SPEC/15_semi_automatisches_adressbuch_mit_memory_kopplung.md
- Backlog Item: N/A
- Feature: Semi-automatisches Adressbuch mit Memory-Kopplung
- Generated At: 2026-06-06

## Generated Tasks

### TASK-SPEC15.1 Extend the contact schema, persistence contract, and settings surface for rich contact cards
- Ziel:
  Create the storage and UI foundation for contact cards that can distinguish private people from organizations, store richer contact knowledge, and expose proposal-related state without replacing the existing address book surface.
- Scope:
  Extend the existing contact model, CRUD/API contract, and settings address-book UI only as far as needed to represent contact type, richer card fields, and controlled management metadata required by the reviewed spec. Do not implement proposal orchestration, web-enrichment decisions, or Memory write coupling in this task.
- Files:
  - backend/data/models.py
  - backend/data/database.py
  - backend/data/contact_schemas.py
  - backend/data/crud.py
  - backend/api/routers/contacts.py
  - frontend/index.html
  - frontend/js/settings.js
  - frontend/css/settings.css
  - backend/tests/test_contact_manager.py
  - backend/tests/integration/test_error_resilience.py
- Steps:
  1. Extend the `Contact` persistence shape so cards can distinguish private person versus organization and hold richer contact knowledge plus proposal-management metadata required by later tasks.
  2. Add migration-safe SQLite drift handling in the existing lightweight schema-migration path so already populated local databases do not require a reset.
  3. Update contact schemas and CRUD/API responses so the richer card contract is available without breaking the current address-book create, edit, list, and delete flow.
  4. Expand the settings-side address-book UI so users can view and edit the richer card structure on the existing surface while preserving the current address-book entry point and modal workflow.
- Acceptance Criteria:
  - The address-book contract can distinguish private contacts from organizations.
  - Contact cards can store objective contact fields plus richer structured contact knowledge without relying on free-form notes only.
  - Existing local databases remain readable after the schema extension without manual reset.
  - Existing address-book create, edit, list, and delete behavior remains intact after the schema/API extension.
  - The settings address-book surface stays the single management surface for overview and detail cards.
- Tests:
  - `python -m pytest backend/tests/test_contact_manager.py -q`
  - `python -m pytest backend/tests/integration/test_error_resilience.py -q`
  - Add or update CRUD/API regression coverage for the richer contact-card contract and migration-safe default handling.
  - `node --check frontend/js/settings.js`
- Model: 5.4
- Reason:
  Shared persistence plus existing-surface UI work with migration and compatibility risk, but still a normal Janus implementation task.

### TASK-SPEC15.2 Implement direct-context contact proposals, duplicate handling, and rejection suppression
- Ziel:
  Turn contact extraction from direct user context into a confirmation-first proposal flow that creates or updates private contacts only after the user approves and that remembers rejected suggestions.
- Scope:
  Rework the existing contact-detection path for chat, calendar, and adjacent direct-context entry points so new private contacts become proposals instead of silent writes, and so likely duplicates become merge or update suggestions instead of automatic second cards.
- Files:
  - backend/services/contact_manager.py
  - backend/tools/contact_tools.py
  - backend/tools/calendar_tools.py
  - backend/services/chat_orchestrator.py
  - backend/data/crud.py
  - backend/data/models.py
  - backend/tests/test_contact_manager.py
  - backend/tests/test_calendar_tools.py
- Steps:
  1. Audit the current extraction path and remove silent private-contact creation behavior where the reviewed spec now requires a confirmation-first proposal.
  2. Introduce deterministic candidate states for new contact proposal, existing-contact update proposal, and merge suggestion.
  3. Add duplicate and near-match checks so likely existing contacts route to merge or augmentation suggestions instead of automatic second cards.
  4. Persist user rejection or suppression outcomes so the same proposal does not immediately resurface without materially new evidence.
- Acceptance Criteria:
  - New private contacts detected from direct context are surfaced as confirmable proposals before creation.
  - Potential duplicates do not create automatic second contact cards.
  - Rejected proposals are remembered and do not continuously reappear without new evidence.
  - Existing direct-context contact extraction continues to work only within the confirmation and privacy rules from the spec.
- Tests:
  - `python -m pytest backend/tests/test_contact_manager.py -q`
  - `python -m pytest backend/tests/test_calendar_tools.py -q`
  - Add or update regression coverage for proposal creation, duplicate routing, and suppression behavior.
- Model: 5.4
- Reason:
  This is the main orchestration task across existing contact and direct-context flows, but it remains within one reviewed product behavior.

### TASK-SPEC15.3 Add public-organization enrichment and ambiguity-safe contact updates
- Ziel:
  Keep public enrichment useful for organizations and other public entries while enforcing the spec's privacy boundary that private contacts are never web-enriched and ambiguous results never auto-apply.
- Scope:
  Refactor the existing incomplete-contact enrichment path so only public/organization entries may use internet enrichment, ambiguous hits require user choice, and conflicting public data becomes a proposal rather than a silent overwrite.
- Files:
  - backend/services/contact_manager.py
  - backend/data/crud.py
  - backend/api/routers/contacts.py
  - backend/tests/test_contact_manager.py
- Steps:
  1. Tighten the existing enrichment gate around public entries and organizations so private contacts are excluded from internet enrichment.
  2. Convert ambiguous public hits into explicit selection-required outcomes rather than implicit enrichment failure or auto-pick behavior.
  3. Route conflicting public fields such as phone, email, address, or website into a proposal state until the user confirms the change.
  4. Preserve useful enrichment for clearly identified organizations with incomplete objective contact data.
- Acceptance Criteria:
  - Private contacts are never enriched from web results.
  - Ambiguous public matches require an explicit user selection before adoption.
  - Conflicting public data does not silently overwrite existing contact-card values.
  - Clear organization entries can still receive objective public-data proposals for missing fields.
- Tests:
  - `python -m pytest backend/tests/test_contact_manager.py -q`
  - Add or update enrichment regression coverage for private-contact blocking, ambiguity gating, and conflict-as-proposal behavior.
- Model: 5.4
- Reason:
  Existing enrichment logic already exists, but this task hardens it around the reviewed privacy and ambiguity contract.

### TASK-SPEC15.4 Connect confirmed contact knowledge with Memory and Memory-backed contact updates
- Ziel:
  Make confirmed contact knowledge and confirmed Memory knowledge mutually usable without turning unconfirmed or sensitive data into a silent shared system state.
- Scope:
  Wire only the confirmed contact and memory paths required by the spec so approved contact facts can become usable memory and confirmed memory facts can become contact-update suggestions under the same sensitivity rules.
- Files:
  - backend/services/contact_manager.py
  - backend/data/crud.py
  - backend/tools/memory_tools.py
  - backend/services/memory_extractor.py
  - backend/tests/test_memory_tools.py
  - backend/tests/test_memory_write_update_conflict_handling.py
  - backend/tests/test_contact_manager.py
- Steps:
  1. Define the confirmed-only handoff points between contact updates and memory writes so only approved contact knowledge can become reusable memory.
  2. Add the reverse path so confirmed relevant memory can generate contact update suggestions instead of silent contact mutation.
  3. Enforce the spec's sensitivity rules for preferences, dislikes, health-adjacent facts, relationship details, and similar personal data.
  4. Preserve traceability between confirmed contact facts, memory facts, and rejected update attempts.
- Acceptance Criteria:
  - Confirmed contact knowledge can be reused by Memory without silently importing unconfirmed facts.
  - Confirmed relevant Memory knowledge can surface as contact-update suggestions without directly mutating contact cards.
  - Sensitive personal information still requires explicit confirmation before persistence.
  - Conflict handling between Memory and contact updates remains explicit and reviewable.
- Tests:
  - `python -m pytest backend/tests/test_memory_tools.py -q`
  - `python -m pytest backend/tests/test_memory_write_update_conflict_handling.py -q`
  - `python -m pytest backend/tests/test_contact_manager.py -q`
- Model: 5.4
- Reason:
  Cross-system state linkage with privacy-sensitive write paths needs careful execution, but the reviewed spec already fixed the product rules.

### TASK-SPEC15.5 Add focused regression coverage for address-book proposals, enrichment, and Memory coupling
- Ziel:
  Lock in the reviewed address-book behavior so future changes do not quietly reintroduce silent private-contact writes, repeated nuisance proposals, unsafe enrichment, or unguarded Memory coupling.
- Scope:
  Extend only the smallest useful backend and existing surface checks that can verify the reviewed contact-intelligence contract without inventing a separate test product.
- Files:
  - backend/tests/test_contact_manager.py
  - backend/tests/test_calendar_tools.py
  - backend/tests/test_memory_tools.py
  - backend/tests/test_memory_write_update_conflict_handling.py
  - frontend/js/settings.js
- Steps:
  1. Add regression coverage for confirmation-first private-contact proposals and duplicate/merge suggestion routing.
  2. Add regression coverage for suppression memory so rejected proposals do not immediately reappear.
  3. Add regression coverage for public-organization enrichment boundaries and ambiguity handling.
  4. Add regression coverage for confirmed-only Memory coupling and sensitive-data confirmation gates.
- Acceptance Criteria:
  - Automated checks fail if private direct-context contacts are silently created again.
  - Automated checks fail if ambiguous public enrichment can auto-apply.
  - Automated checks fail if rejected suggestions immediately resurface without new evidence.
  - Automated checks fail if Memory coupling bypasses confirmation or sensitive-data gating.
- Tests:
  - `python -m pytest backend/tests/test_contact_manager.py -q`
  - `python -m pytest backend/tests/test_calendar_tools.py -q`
  - `python -m pytest backend/tests/test_memory_tools.py -q`
  - `python -m pytest backend/tests/test_memory_write_update_conflict_handling.py -q`
  - `node --check frontend/js/settings.js`
- Model: 5.4
- Reason:
  Pure regression-hardening task on concrete existing evidence surfaces, intended to keep later iterations honest.

## Task Breakdown Release

- Target Task: TASK-SPEC15.1
- Target Subtask: N/A
- Breakdown Decision: TASK DESIGN COMPLETE
- Readiness: READY FOR SINGLE TASK PRECHECK
- Execution Model: 5.4
- Breakdown Focus:
  Establish the richer contact-card and persistence contract first, because proposal flow, public enrichment, and Memory coupling all depend on that shared contact shape.
