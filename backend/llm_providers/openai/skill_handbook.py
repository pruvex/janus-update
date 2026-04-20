from __future__ import annotations

from typing import Optional

from backend.services.prompting.core.model import SkillDirective


_SKILL_DIRECTIVES = {
    "system.websearch": SkillDirective(
        skill_id="system.websearch",
        instruction_set={
            "nano": "STRICT_TRUTH: Trust snippets. Extract prices, release dates, names and rankings exactly. Ignore filler text. Keep only relevant entities. Cite sources tersely. For release or ranking lists, keep the list flat and attach one fitting source link per item when present in the material. FINAL ANSWER ONLY: Never repeat instructions, XML tags, rules, templates or internal reasoning.",
            "mini": "STRICT_TRUTH: Trust snippets. Extract exact prices, dates, names and ranked items completely. Resolve minor wording noise, but do not invent facts. Cite precisely. For release or ranking lists, keep the list flat and attach one fitting source link per item when present in the material. FINAL ANSWER ONLY: Do not repeat instructions or internal rules.",
            "standard": "Reason about conflicting sources carefully. Prefer official or market-relevant sources, preserve completeness, and cite precisely.",
        },
    ),
    "system.create_pdf": SkillDirective(
        skill_id="system.create_pdf",
        instruction_set={
            "nano": "ULTRA_SIMPLE_MD: No parentheses in headers. Keep structure parser-safe.",
            "mini": "Use stable markdown with short sections and deterministic headings.",
            "standard": "Use professional layout. Group logical sections clearly.",
        },
    ),
}


def get_skill_directive(skill_id: str) -> Optional[SkillDirective]:
    return _SKILL_DIRECTIVES.get(str(skill_id or "").strip())
