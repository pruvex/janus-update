from __future__ import annotations

from gate_prompt_shadow import build_shadow_operator_prompt_lines


def test_build_shadow_operator_prompt_lines_includes_session_budget_line() -> None:
    lines = build_shadow_operator_prompt_lines(
        choice_2_label="Cursor",
        selected_model="composer-2.5",
        estimated_cost=0.0025,
    )

    assert lines[0] == "1 = Codex"
    assert lines[1] == "2 = Cursor"
    assert "Empfohlenes Worker-Modell: composer-2.5" in lines
    assert any(line.startswith("Session-Budget:") for line in lines)
