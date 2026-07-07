from __future__ import annotations


def build_shadow_operator_prompt_lines(
    *,
    choice_2_label: str = "Cursor",
    selected_model: str = "",
    estimated_cost: float = 0.0,
    session_cap_usd: float = 0.15,
) -> list[str]:
    _ = session_cap_usd
    lines = [
        "1 = Codex",
        f"2 = {choice_2_label}",
        "Cursor is the bounded external worker option for this shadow lane.",
    ]
    if selected_model.strip():
        lines.append(f"Empfohlenes Worker-Modell: {selected_model}")
    lines.append(f"Voraussichtliche Worker-Kosten {estimated_cost:.6f}")
    return lines
