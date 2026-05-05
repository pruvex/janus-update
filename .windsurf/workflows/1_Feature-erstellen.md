---
description: GPT 5.5 Erstellt einen Sauberen Umsetzungsplan als Taskdatei
---

## Feature Implementation Planning Workflow (JANUS – DIAMANTSTANDARD)

This workflow transforms a Janus Feature Spec into a complete, executable implementation plan.

The output MUST be:
- deterministic
- unambiguous
- executable by weak agents (Gemini Flash, SWE 1.6, Kimi)

If any ambiguity or missing information is detected → STOP and report clearly.

---

## Phase 0: Clarification Gate (MANDATORY FIRST STEP)

0. Before any codebase analysis or implementation planning, inspect the provided Feature Spec for unresolved decisions.

Check for:
- Explicit `OPEN QUESTIONS` sections
- Phrases like `optional later`, `wenn möglich`, `stable`, `secure`, `robust`, `fallback`, `rollback`, `best effort`, `TBD`, `maybe`, `should`, unless they are concretely defined
- Undefined UI behavior
- Undefined retry limits
- Undefined security requirements
- Undefined persistence/state behavior
- Undefined external service behavior
- Any acceptance criterion that is not binary-checkable

Rules:
- ❌ If open questions exist → select only the next highest-impact unresolved decision, then STOP before Phase 1
- ❌ If optional items are not explicitly marked as OUT OF SCOPE → STOP
- ❌ If vague wording changes implementation behavior → STOP
- ❌ Do NOT infer product decisions
- ❌ Do NOT continue to codebase analysis while clarification is unresolved
- ❌ Do NOT present all unresolved questions at once

Decision ordering:
1. Architecture/tooling decisions that affect file/module structure
2. Security/safety decisions
3. State/persistence decisions
4. UI/UX decisions
5. Retry/fallback/error handling decisions
6. Testability and acceptance-criteria decisions

When stopping, return EXACTLY:

---

# DECISION REQUIRED

## Current Blocking Decision
[Ask exactly ONE concrete decision question with affected spec section.]

## Why This Blocks Planning
- [Explain why this decision must be resolved before codebase analysis or task generation.]

## Options

### Option A: [option name]
- **Pros:** [specific advantages]
- **Cons:** [specific disadvantages]
- **Impact:** [files/architecture/testing/user behavior affected]

### Option B: [option name]
- **Pros:** [specific advantages]
- **Cons:** [specific disadvantages]
- **Impact:** [files/architecture/testing/user behavior affected]

### Option C: [option name, only if useful]
- **Pros:** [specific advantages]
- **Cons:** [specific disadvantages]
- **Impact:** [files/architecture/testing/user behavior affected]

## Recommendation
- **Recommended option:** [A/B/C]
- **Reason:** [concrete reasoning based on Janus architecture, risk, implementation effort, and agent determinism]

## Required Answer Format
Answer with one option and, if needed, exact parameters:
- `Decision: Option [A/B/C]`
- `Parameters: [exact values or OUT OF SCOPE markers]`

## Next Step
After this decision is answered, rerun `/Feature-erstellen` to resolve the next blocking decision.

---

If all questions are resolved:
- Replace vague wording with concrete behavior in the derived plan
- Mark all deferred items as explicit `OUT OF SCOPE`
- Continue to Phase 1

---

## Phase 0.5: WHAT_I_LEARNED Lookup Light (LOW-COST)

Purpose: reuse known Janus/Diamond-OS patterns without loading the full knowledge base.

Rules:
- Do not read `WHAT_I_LEARNED.md` fully by default.
- First extract 5-12 targeted lookup keys from the Feature Spec:
  - feature domain
  - likely files/modules
  - integration types
  - external services
  - UI/API/IPC/security/persistence/test keywords
  - known error class if present
- Search `WHAT_I_LEARNED.md` only for those keys/tags.
- Read only directly matching pattern blocks.
- If no relevant match exists, continue without loading the file.
- Apply a learning only if it directly changes planning guardrails, task boundaries, acceptance criteria, or test mapping.
- Do not include generic or weakly related learnings in the generated task file.

Output inside the generated plan:

```markdown
## Relevant Prior Learnings
- **#[PatternName]:** [short actionable rule]
- None found.
```

Example lookup keys:
- Electron/update feature: `AutoUpdate`, `ElectronIPC`, `Playwright`, `RealModuleE2E`, `package-lock`, `manifest`
- Memory feature: `ContextBleed`, `Knapsack`, `similarity threshold`, `memory.read`
- Gemini/tool feature: `GeminiNameSanitization`, `tool_choice`, `function_declarations`

---

## Phase 1: Spec Analysis (GATE)

1. Parse the provided Feature Spec:

Extract:
- Core Idea
- Functional Core
- System Behavior
- Edge Cases
- Constraints
- Integrations

Validate:
- ❌ Missing section → STOP and list missing parts
- ❌ Ambiguous behavior → STOP and request clarification
- ❌ Unclear constraints → STOP

### Spec Validation Layer (HARD GATE)

Before continuing to codebase analysis, validate whether the Feature Spec is implementation-ready.

Check:
- All mandatory sections exist: Feature Name, Core Idea, Functional Core, System Behavior, Edge Cases, Constraints, Integration Context, Test Strategy, Definition of Done
- Every system state has defined entry conditions, exit conditions, and failure behavior
- Every external dependency has defined unavailable/error behavior
- Every persistence/state requirement defines storage location, update trigger, and recovery behavior
- Every UI behavior defines trigger, visible output, user action, and cancellation behavior
- Every retry/fallback rule has exact limits and resulting state
- Every security-sensitive behavior defines concrete validation requirements or is explicitly OUT OF SCOPE
- Every acceptance criterion is binary-checkable
- Every test requirement maps to a concrete observable behavior
- No task-relevant behavior depends on interpretation by the implementing agent

❌ If validation fails:
STOP before Phase 2 and return EXACTLY:

---

# SPEC VALIDATION FAILED

## Missing Required Sections
- [section name] → [why it blocks planning]

## Non-Deterministic Requirements
- `[requirement]` → [why it is not executable] → [required concrete replacement]

## Incomplete Edge Cases
- [edge case] → [missing expected behavior]

## Non-Binary Acceptance Criteria
- `[criterion]` → [why it cannot be verified] → [required measurable condition]

## Required User Decisions
1. [Concrete decision required before planning]

## Next Step
Resolve these items in the Feature Spec, then rerun `/Feature-erstellen`.

---

If validation passes:
- Treat the Feature Spec as planning-ready
- Continue to Phase 2

---

## Phase 2: Codebase Alignment (CRITICAL)

// turbo

2. Analyze the codebase:

Identify:
- Relevant existing modules
- Reusable components
- Conflicting patterns

Determine:
- What will be extended
- What must be refactored
- What must be built from scratch

❌ If architectural conflict detected:
STOP and explain:
- conflict location
- impact
- required resolution

---

## Phase 3: Architecture Definition

3. Define target architecture:

- Feature structure
- Module boundaries
- Data flow:
  UI → Logic → State → API → AI

Rules:
- Follow existing patterns
- Avoid unnecessary abstractions
- Avoid breaking existing features

---

## Phase 4: Implementation Plan (STRICT)

4. Generate step-by-step plan:

Each step MUST include:
- Goal
- EXECUTION TARGET (`Kimi k2.5` or `SWE 1.6`)
- Target Decision Reason
- Files / modules
- Concrete actions
- Expected result

Rules:
- No vague wording
- No interpretation required
- Sequential and executable
- The workflow author MUST assign the execution target for every step.
- The orchestrator, Gemini, or downstream agent MUST NOT choose, infer, or override the execution target.
- If an execution target is missing for any step, the generated task file is INVALID and MUST be fixed before output.

---

## Phase 5: Test Strategy (MANDATORY)

// turbo

5. Generate real test plan:

### Unit Tests
- Concrete functions and logic

### Integration Tests
- Module interactions

### E2E Tests (MANDATORY)
- Real user flows (Playwright)
- NO full mocking

### State Tests
- UI ↔ backend consistency

### AI Tests (if applicable)
- Defined behavior scenarios

MANDATORY:
- At least ONE real E2E flow
- Must validate real system behavior

❌ If not possible:
STOP and explain why

---

## Phase 6: Task Generation (AGENT-OPTIMIZED – CRITICAL)

6. Convert plan into deterministic, agent-executable tasks.

Each task MUST follow EXACT structure:

### TASK T1

**EXECUTION TARGET:**  
`Kimi k2.5` or `SWE 1.6`

**Target Decision Reason:**  
One sentence explaining why this agent is the correct executor for this task.

**Goal (STRICT):**  
Single, clearly defined objective. No combined goals.

**Context:**  
Short explanation of where this fits in the system.

**Input:**  
- Existing files, modules, or data used
- Exact dependencies

**Output (STRICT):**  
- Exact files to create/modify
- Exact behavior after completion

**Implementation Instructions (STEP-BY-STEP):**
1. Do X in file Y
2. Modify function Z
3. Add logic for ...

NO high-level descriptions allowed.

**Files to Modify/Create:**
- /exact/path/file1.ts
- /exact/path/file2.tsx

**Dependencies:**
- Must be completed after: T0
- Required modules/services

**Acceptance Criteria (MANDATORY):**
- [ ] конкретe condition 1
- [ ] конкретe condition 2
- [ ] expected behavior observable

**Test Instructions:**
- Unit: what to test
- Integration: what interaction
- E2E: what user flow

---

### TASK T2
(same structure)

---

### TASK RULES (CRITICAL):

- Tasks MUST be atomic (1 responsibility)
- No hidden assumptions
- No “implement logic” phrasing
- No interpretation required
- Must be executable by weak models
- Every task MUST include exactly one explicit `EXECUTION TARGET`.
- Every task in every task file MUST include the `EXECUTION TARGET` directly under the task heading, not only in a summary table.
- Every task MUST include a short `Target Decision Reason` directly below the `EXECUTION TARGET`.
- Allowed targets are ONLY `Kimi k2.5` and `SWE 1.6`.
- The workflow author MUST decide the target during task generation.
- The orchestrator, Gemini, or downstream agent MUST NOT choose or override the target.
- Use `Kimi k2.5` for deterministic file creation, isolated modules, straightforward refactors, tests with clear expected outputs, and tasks with low architectural ambiguity.
- Use `SWE 1.6` for high-risk integration work, multi-file refactors, Electron/main-process lifecycle work, IPC/security-sensitive work, UI wiring across existing complex files, and tasks requiring broader codebase reasoning.
- If a task cannot be assigned confidently to one of these two targets, STOP and split the task into smaller tasks until the target is obvious.

---

## Phase 6.5: Task Coverage Validation (HARD GATE)

6.5. Validate that the generated tasks fully cover the Feature Spec.

Build a traceability matrix before final output:

```markdown
| Spec Requirement / Edge Case / Constraint | Covered By Task(s) | Coverage Status | Notes |
|---|---|---|---|
| [requirement] | T1, T2 | COVERED | [short reason] |
| [edge case] | OUT OF SCOPE | OUT OF SCOPE | [exact spec marker] |
```

Coverage rules:
- Every functional requirement MUST map to at least one task.
- Every system behavior MUST map to at least one task.
- Every edge case MUST be covered by a task or explicitly marked `OUT OF SCOPE`.
- Every constraint MUST map to task instructions, acceptance criteria, or validation rules.
- Every integration point MUST map to implementation and test tasks.
- Every acceptance criterion MUST map to at least one task and one test instruction.
- No unassigned requirement is allowed.
- No task without explicit `EXECUTION TARGET` and `Target Decision Reason` is allowed.
- No duplicate tasks are allowed unless they cover different concrete responsibilities.
- No contradictory task instructions are allowed.
- No task may implement behavior that is outside the Feature Spec unless it is required by existing architecture compatibility.

❌ If coverage validation fails:
STOP before Phase 6.6 and return EXACTLY:

---

# TASK COVERAGE VALIDATION FAILED

## Missing Coverage
- **Requirement:** [exact requirement]
- **Missing task:** [what task must be added or changed]
- **Why this blocks execution:** [reason]

## Incomplete Edge Cases
- **Edge case:** [exact edge case]
- **Problem:** [not covered / not marked OUT OF SCOPE]
- **Required fix:** [task coverage or OUT OF SCOPE marker]

## Unmapped Acceptance Criteria
- **Criterion:** [exact criterion]
- **Required mapping:** [task + test instruction]

## Duplicate or Contradictory Tasks
- **Tasks:** [Tn/Tm]
- **Conflict:** [exact contradiction or duplication]
- **Required fix:** [merge / split / rewrite]

## Next Step
Fix the task set, then rerun Phase 6.5.

---

If coverage validation passes:
- Mark `Task Coverage: PASS`.
- Continue to Phase 6.6.

---

## Phase 6.6: Final Plan Lock (HARD GATE)

6.6. Freeze the validated task plan before final output.

After this phase starts:
- Do not add new tasks.
- Do not remove tasks.
- Do not change task scope.
- Only formatting fixes are allowed if they do not change meaning.

Determinism checks:
- Every task is atomic and has exactly one responsibility.
- Every task has one explicit `EXECUTION TARGET`.
- Every task has exact files to modify/create or a precise discovery instruction if the file cannot be known before execution.
- Every task has explicit dependencies.
- Every task has binary acceptance criteria.
- Every task has concrete test instructions.
- No task contains phrases like `implement logic`, `handle properly`, `make robust`, `improve`, `optimize`, `support this`, `as needed`, `etc.`, or equivalent vague language.
- No task requires downstream architecture decisions.
- No task depends on unstated assumptions.
- UI or system features MUST include at least one real E2E test task or an explicit deterministic reason why E2E is impossible.
- Execution order must be topologically valid against task dependencies.

Required lock block:

```markdown
## FINAL PLAN LOCK
- **Task Coverage:** PASS
- **Determinism:** PASS
- **Atomicity:** PASS
- **Dependencies:** PASS
- **E2E Coverage:** PASS | NOT APPLICABLE — [reason]
- **Plan Lock:** ACTIVE
```

❌ If final plan lock fails:
STOP before Phase 7 and return EXACTLY:

---

# FINAL PLAN LOCK FAILED

## Non-Deterministic Tasks
- **Task:** [Tn]
- **Problem:** [vague wording / hidden decision / missing file / missing dependency]
- **Required fix:** [exact rewrite required]

## Non-Atomic Tasks
- **Task:** [Tn]
- **Problem:** [multiple responsibilities]
- **Required split:** [new task boundaries]

## Dependency Problems
- **Task:** [Tn]
- **Problem:** [missing / cyclic / implicit dependency]
- **Required fix:** [explicit dependency]

## Missing E2E Coverage
- **Feature area:** [UI/system behavior]
- **Required E2E test:** [concrete user flow]

## Next Step
Fix the plan, then rerun Phase 6.6.

---

If final plan lock passes:
- Emit the `FINAL PLAN LOCK` block in the final output.
- Continue to Phase 7.

---

## Phase 7: Final Output (STRICT MARKDOWN FORMAT)

Return EXACTLY:

---

# FEATURE IMPLEMENTATION PLAN

## A. ARCHITECTURE SUMMARY
- Structure
- Modules
- Data flow

---

## B. IMPLEMENTATION PLAN

### STEP 1
- Goal:
- Files:
- Actions:
- Expected Result:

---

## C. TEST STRATEGY

### UNIT TESTS
- [ ]

### INTEGRATION TESTS
- [ ]

### E2E TESTS (MANDATORY)
- [ ]

### STATE TESTS
- [ ]

### AI TESTS
- [ ]

---

## D. TASKS (ORCHESTRATOR READY)

(Tasks exactly in defined format, including explicit `EXECUTION TARGET` and `Target Decision Reason` for every task)

---

## E. TASK COVERAGE MATRIX

(Traceability matrix from Phase 6.5. Every requirement, edge case, constraint, integration, and acceptance criterion must be mapped or explicitly OUT OF SCOPE.)

---

## F. FINAL PLAN LOCK

- **Task Coverage:** PASS
- **Determinism:** PASS
- **Atomicity:** PASS
- **Dependencies:** PASS
- **E2E Coverage:** PASS | NOT APPLICABLE — [reason]
- **Plan Lock:** ACTIVE

---

## G. EXECUTION ORDER

1. T1
2. T2
3. T3

---

## H. VALIDATION RULES

- All tasks must pass tests
- E2E must pass before completion
- No architecture decisions during execution
- No manual interpretation allowed
- READY FOR TASK EXECUTION may only be emitted if Phase 6.5 and Phase 6.6 both passed

---

## Expected Outcome

- ✅ Deterministic execution
- ✅ Minimal iteration
- ✅ Stable agent behavior
- ✅ READY FOR TASK EXECUTION
- ❌ If unclear → STOP instead of guessing