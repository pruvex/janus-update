# AI Studio Bootstrap (Diamond-OS V3.2)

**WICHTIG:** Kopiere fuer jeden Triage-Task nur die `PROJECT_STATE.md` in AI Studio.

## Quick-Start (3 Schritte)

1. **PROJECT_STATE.md kopieren** → AI Studio Gemini Flash
2. **CU-Schaetzung** → Routing-Entscheidung (siehe SECTION 4)
3. **Handover-Template** → Aus `.diamond/system/handover_templates.md`

## Modulare System-Referenzen

| Modul | Pfad | Inhalt |
|-------|------|--------|
| Routing Logic | `.diamond/system/routing_logic.md` | CU-Tabellen, Editor-Entscheidungen |
| Templates | `.diamond/system/handover_templates.md` | Windsurf/Cursor/Pro Templates |
| Loop Defs | `.diamond/system/loop_definitions.md` | 6-Schritte Next-Action-Loop |

## NEXT ACTION LOOP (V3.2)

```
0. THINK (MCP): Max 3-5 Gedanken. Problem-Analyse + Hypothese.
1. IMPL → 2. TEST → 3. LINTER → 4. IMPORTS → 5. DIAMOND-REPORT
```

---

**Version:** 3.2 — Hybrid-Modular  
**Full Docs:** `documentation/00_AI_STUDIO_BOOTSTRAP.md` (Legacy, nur bei Bedarf)
