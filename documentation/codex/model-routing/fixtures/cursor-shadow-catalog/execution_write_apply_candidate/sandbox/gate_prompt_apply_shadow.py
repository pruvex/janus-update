from __future__ import annotations


def build_write_apply_shadow_lines(
    *,
    choice_2_label: str = "Cursor",
    selected_model: str = "",
    estimated_cost: float = 0.0,
) -> list[str]:
    lines = [
        "1 = Codex",
        f"2 = {choice_2_label}",
        "Cursor may apply an accepted bounded delta in this shadow lane.",
    ]
    if selected_model.strip():
        lines.append(f"Empfohlenes Worker-Modell: {selected_model}")
    lines.append("Accepted source summary: apply the validated prompt delta exactly once.")
    lines.append(f"Voraussichtliche Worker-Kosten {estimated_cost:.6f}")
    return lines
