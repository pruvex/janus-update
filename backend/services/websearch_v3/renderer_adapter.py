from __future__ import annotations

from .models import SingleVerifiedNewsResult, SupportedFact


NO_SOURCE_TEXT = "Ich habe aktuell keine ausreichend belastbare Quelle gefunden."


def render_supported_fact(fact: SupportedFact) -> str:
    source = fact.source
    return (
        "Kurzlage: Es liegt aktuell eine belegte Meldung vor.\n\n"
        f"1. {fact.topic_label}: {fact.title}\n"
        f"{fact.summary}\n"
        f"Quelle: {source.source_label}. [Link]({source.canonical_url})\n\n"
        "Einordnung:\n"
        "Diese Kurzlage basiert auf einer verifizierten Webquelle."
    )


def render_supported_facts(facts: tuple[SupportedFact, ...]) -> str:
    if not facts:
        return NO_SOURCE_TEXT
    if len(facts) == 1:
        return render_supported_fact(facts[0])

    count_text = "zwei" if len(facts) == 2 else str(len(facts))
    lines = [f"Kurzlage: Es liegen aktuell {count_text} belegte Meldungen vor.", ""]
    for index, fact in enumerate(facts[:4], start=1):
        source = fact.source
        lines.extend(
            [
                f"{index}. {fact.topic_label}: {fact.title}",
                fact.summary,
                f"Quelle: {source.source_label}. [Link]({source.canonical_url})",
                "",
            ]
        )
    lines.extend(
        [
            "Einordnung:",
            "Diese Kurzlage basiert auf verifizierten Webquellen.",
        ]
    )
    return "\n".join(lines).strip()


def render_single_verified_news(result: SingleVerifiedNewsResult) -> str:
    facts = result.facts or ((result.fact,) if result.fact else tuple())
    if not facts:
        return NO_SOURCE_TEXT
    return render_supported_facts(facts)
