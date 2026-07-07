from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


class SkillSurfaceOperatorMappingsTests(unittest.TestCase):
    def test_documentation_draft_shared_gate_maps_openrouter_to_option_three(self) -> None:
        skill_path = REPO_ROOT / "documentation" / "codex" / "skills" / "janus-documentation-update" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        self.assertIn("- `1 = Codex`", content)
        self.assertIn("- `2 = Cursor`", content)
        self.assertIn("- `3 = OpenRouter`", content)
        self.assertIn(
            "- if the user chooses `3`, `or`, `opr`, or `openrouter`, the shared delegate currently plans the bounded documentation-draft helper path and hands off to the existing dispatcher/runtime pair",
            content,
        )

    def test_backlog_handoff_tri_modal_gate_maps_openrouter_to_option_three(self) -> None:
        skill_path = REPO_ROOT / "documentation" / "codex" / "skills" / "janus-backlog-handoff" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        self.assertIn(
            "- if the user chooses `3`, `or`, `openrouter`, or `opr`, invoke the same runner with `--operator-choice delegated --input-package-json <bounded package>`",
            content,
        )
        self.assertNotIn(
            "- if the user chooses `2`, `or`, `openrouter`, or `opr`, invoke the same runner with `--operator-choice delegated --input-package-json <bounded package>`",
            content,
        )

    def test_feature_design_shared_gate_keeps_cursor_unimplemented_and_or_on_option_three(self) -> None:
        skill_path = REPO_ROOT / "documentation" / "codex" / "skills" / "janus-feature-design" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        self.assertIn(
            "- if the user chooses `2`, `cursor`, or `Cursor`, do not imply a live Cursor feature-design path unless a later migration artifact explicitly adds one",
            content,
        )
        self.assertIn(
            "- if the user chooses `3`, `or`, `opr`, or `openrouter`, the shared delegate currently plans the bounded feature-design helper path and hands off to the existing runner",
            content,
        )

    def test_precheck_shared_gate_keeps_cursor_unimplemented_and_or_on_option_three(self) -> None:
        skill_path = REPO_ROOT / "documentation" / "codex" / "skills" / "janus-preimplementation-check" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        self.assertIn(
            "- if the user chooses `2`, `cursor`, or `Cursor`, do not imply a live Cursor precheck path unless a later migration artifact explicitly adds one",
            content,
        )
        self.assertIn(
            "- if the user chooses `3`, `or`, `opr`, or `openrouter`, the shared delegate currently plans the bounded precheck helper path and hands off to the existing runner",
            content,
        )

    def test_quickchange_exception_keeps_option_two_hidden(self) -> None:
        skill_path = REPO_ROOT / "documentation" / "codex" / "skills" / "janus-quickchange" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        self.assertIn(
            "The visible gate for this lane is currently `1 = Codex` / `3 = OpenRouter`; there is not yet a validated Cursor quickchange backend here, so option `2` stays unavailable for this specific slice.",
            content,
        )
        self.assertIn(
            "- if the user chooses `3`, `or`, `opr`, or `openrouter`, the shared delegate currently plans the bounded dispatcher path and hands off to the existing helper chain",
            content,
        )


if __name__ == "__main__":
    unittest.main()
