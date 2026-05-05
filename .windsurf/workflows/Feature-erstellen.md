---
description: Generate deterministic implementation plan and agent-optimized tasks from Feature Spec using codebase analysis
---

## Feature Implementation Planning Workflow (JANUS – DIAMANTSTANDARD)

This workflow transforms a Janus Feature Spec into a complete, executable implementation plan.

The output MUST be:
- deterministic
- unambiguous
- executable by weak agents (Gemini Flash, SWE 1.6, Kimi)

If any ambiguity or missing information is detected → STOP and report clearly.

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
- Files / modules
- Concrete actions
- Expected result

Rules:
- No vague wording
- No interpretation required
- Sequential and executable

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

(Tasks exactly in defined format)

---

## E. EXECUTION ORDER

1. T1
2. T2
3. T3

---

## F. VALIDATION RULES

- All tasks must pass tests
- E2E must pass before completion
- No architecture decisions during execution
- No manual interpretation allowed

---

## Expected Outcome

- ✅ Deterministic execution
- ✅ Minimal iteration
- ✅ Stable agent behavior
- ❌ If unclear → STOP instead of guessing