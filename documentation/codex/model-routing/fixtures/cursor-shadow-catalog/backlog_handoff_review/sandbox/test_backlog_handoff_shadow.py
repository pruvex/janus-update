from __future__ import annotations

from pathlib import Path


def test_shadow_handoff_summary_recommends_precheck_entry() -> None:
    summary_path = Path(__file__).with_name("selected_handoff_shadow.md")
    content = summary_path.read_text(encoding="utf-8")

    assert "Backlog ID: BACKLOG-109" in content
    assert "Empfohlener Einstieg: PRE_IMPLEMENTATION_VERIFICATION" in content
