from __future__ import annotations


GOLDEN_PROMPT_SETS: dict[str, tuple[str, ...]] = {
    "smoke": (
        "was gibt es neues zu Microsoft?",
        "was gibt es neues im Kino?",
        "was gibt es neues im Gaming?",
    ),
    "company": (
        "was gibt es neues zu Microsoft?",
        "was gibt es neues zu OpenAI?",
        "aktuelle Nachrichten zu Nvidia?",
        "was gibt es neues zu Apple?",
    ),
    "entertainment": (
        "was gibt es neues im Kino?",
        "was gibt es neues im Gaming?",
        "welche neuen Filmtrailer gibt es?",
        "welche neuen Spiele erscheinen demnaechst?",
    ),
    "sport": (
        "was gibt es neues in der Bundesliga?",
        "was gibt es neues in der NBA?",
        "was gibt es neues in der Formel 1?",
    ),
    "finance_explicit": (
        "hat Nvidia aktuelle Quartalszahlen veroeffentlicht?",
        "wie waren Microsofts letzte Quartalszahlen?",
    ),
}


def prompts_for_set(name: str) -> tuple[str, ...]:
    key = str(name or "smoke").strip().casefold()
    if key == "all":
        prompts: list[str] = []
        seen: set[str] = set()
        for values in GOLDEN_PROMPT_SETS.values():
            for prompt in values:
                if prompt not in seen:
                    prompts.append(prompt)
                    seen.add(prompt)
        return tuple(prompts)
    if key not in GOLDEN_PROMPT_SETS:
        available = ", ".join(sorted((*GOLDEN_PROMPT_SETS.keys(), "all")))
        raise ValueError(f"Unknown prompt set '{name}'. Available: {available}")
    return GOLDEN_PROMPT_SETS[key]
