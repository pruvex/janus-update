from __future__ import annotations

from gate_prompt_apply_shadow import build_write_apply_shadow_lines


def test_build_write_apply_shadow_lines_includes_accepted_source_summary_line() -> None:
    lines = build_write_apply_shadow_lines(
        choice_2_label="Cursor",
        selected_model="composer-2.5",
        estimated_cost=0.0025,
    )

    assert lines[0] == "1 = Codex"
    assert lines[1] == "2 = Cursor"
    assert "Empfohlenes Worker-Modell: composer-2.5" in lines
    assert "Accepted source summary: apply the validated prompt delta exactly once." in lines
    assert lines[-1].startswith("Voraussichtliche Worker-Kosten ")
