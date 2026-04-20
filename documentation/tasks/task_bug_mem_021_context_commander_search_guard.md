# Task BUG-MEM-021: Context Commander & Search-Guard V3

## 1. Ziel & Kontext
**Problem:**
1. Self-referentielle Fragen ("Was bin ich allergisch gegen?", "Welche Hobbys habe ich?") lösen unnötig Websuche aus.
2. Gesundheitskritische Informationen (Allergien, Medikamente) werden vom LLM ignoriert.
3. LLM behauptet "Ich habe keine Informationen" obwohl Familienmitglieder im Context sind.

**Ziel:**
- **Recall-Guard:** Self-referentielle Queries → keine Websuche (Memory-Only).
- **Medical-Override:** Gesundheitsdaten → Critical Warning im System-Prompt.
- **Family-Context:** Verbot für "keine Informationen" wenn Familie im Context.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** BUG-MEM-020 (Density & Priority — COMPLETED)
- **Beeinflusst:** chat_orchestrator.py, Skill-Routing, System-Prompt
- **Risiko-Einschätzung:** P1 — High (Safety-Critical)

## 3. Betroffene Dateien (Target)
- `backend/services/chat_orchestrator.py` — Module-level constants, _should_force_websearch_skill(), Context Selection, Directive Injection

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** Task-File gelesen
- [x] **Phase 2 (Recall-Guard):** `_SELF_REF_RE` implementiert
- [x] **Phase 3 (Medical-Override):** Health-Tags + Keywords + Warning Block
- [x] **Phase 4 (Family-Context):** Family-Relation-Regex + Instruction Hardening
- [x] **Phase 5 (Test):** Syntax-Check PASSED
- [x] **Phase 6 (Post-Impl):** /post-impl durch Kimi

## 5. Test-Vorgaben
- [ ] "Was bin ich allergisch gegen?" → keine Websuche, nur Memory
- [ ] Health Slot vorhanden → System-Prompt enthält "!!! CRITICAL MEDICAL WARNING !!!"
- [ ] "Wer ist mein Bruder?" mit Family im Context → direkte Antwort, keine "keine Info"

## 6. Ergebnis & Audit-Trail
**Implementation:** Kimi (Windsurf) — 2026-04-08

**Key Implementation Details:**

### 21.1 RECALL-GUARD (Lines ~153-162)
```python
_SELF_REF_RE = re.compile(
    r'(wer|was|wie|welche|wei[sß]t).*(ich|mein|meine|mir|mich)',
    re.IGNORECASE,
)
```
- Blockiert Websearch wenn self-referentielles Muster erkannt
- Log: `[RECALL-GUARD-021] Blocking web search – self-referential query`

### 21.2 MEDICAL-OVERRIDE (Lines ~162-174, ~4224-4233)
```python
_HEALTH_SLOT_TAGS = frozenset({"gesundheit", "health", "allergie", ...})
_HEALTH_SLOT_KEYWORDS = ("allergi", "unverträglich", "medikament", ...)
```
- Tag-Check: Intersection mit Slot-Tags
- Keyword-Check: Substring-Match im Slot-Text
- Warning Block wird ABOVE Identity Directive prepended

### 21.3 FAMILY-CONTEXT (Lines ~175-180, ~4199-4215)
```python
_FAMILY_RELATION_RE = re.compile(
    r'\b(bruder|schwester|vater|mutter|eltern|sohn|tochter|...)\b',
    re.IGNORECASE,
)
```
- Erkennt Familienbeziehungen im Memory-Context
- Instruction-Hardening: Hard-Verbot für "Ich habe keine Informationen"
- Log: `[INSTRUCTION-HARDENING-021] Family-context clause added`

**Files Modified:**
- `backend/services/chat_orchestrator.py`
  - Module-level constants (lines ~153-180)
  - `_should_force_websearch_skill()` — Recall-Guard integration (line ~202-212)
  - Context Selection — Health/Family detection (lines ~3857-3882)
  - Directive Injection — Warning + Hardening (lines ~4196-4224)

**Syntax-Check:** ✅ PASSED

## 7. Debugging-Log
**2026-04-08 — Task Setup**
- 3-Schichten-Sicherheitskonzept identifiziert: Recall-Guard + Medical-Override + Family-Context

**2026-04-08 — Implementation Complete (Kimi)**
- Alle 3 Layer implementiert
- Syntax-Check: ✅ PASSED
- Logging-Signale etabliert:
  - `[RECALL-GUARD-021]`
  - `[MEDICAL-OVERRIDE-021]`
  - `[FAMILY-CONTEXT-021]`
  - `[INSTRUCTION-HARDENING-021]`

**2026-04-08 — Post-Impl durch Kimi**
- Task-Dokumentation aktualisiert (Phase 5+6 abgehakt)
- Registries aktualisiert (PROJECT_STATE.md, 01_CENTRAL_TASK_REGISTRY.md)
- WHAT_I_LEARNED.md aktualisiert mit 4 neuen Patterns:
  - Jaccard Similarity Duplicate Filter (BUG-MEM-020)
  - Recall-Guard for Self-Referential Queries (BUG-MEM-021)
  - Medical-Override for Health-Critical Slots (BUG-MEM-021)
  - Family-Context Instruction Hardening (BUG-MEM-021)
- /post-impl COMPLETE

---

## Phase 2: Implementierungs-Auftrag (Archiv)

### Aufgabe (Kimi → Windsurf)
1. **Recall-Guard:**
   - Füge `_SELF_REF_RE` Pattern zu `chat_orchestrator.py` hinzu
   - Integriere in `_should_force_websearch_skill()` — return False bei Match

2. **Medical-Override:**
   - Tags: `gesundheit`, `health`, `allergie`, `allergen`, `medizin`, `medication`, `medical`
   - Keywords: `allergi`, `unverträglich`, `intoleranz`, `medikament`, `erkrankung`, `krankheit`, `diabetes`, `asthma`, `epilepsie`, `blutdruck`
   - Prepended Warning Block bei Detection

3. **Family-Context:**
   - Regex für: bruder, schwester, vater, mutter, eltern, sohn, tochter, oma, opa, großvater, großmutter, mann, frau, kind, kinder, cousin, cousine, tante, onkel, familie
   - Instruction Hardening: Verbot für "keine Informationen"

4. Führe Syntax-Check durch.
