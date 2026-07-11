from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


class SkillSurfaceOperatorMappingsTests(unittest.TestCase):
    def test_documentation_draft_shared_gate_maps_or_to_two_and_cursor_api_to_four(self) -> None:
        skill_path = REPO_ROOT / "documentation" / "codex" / "skills" / "janus-documentation-update" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        self.assertIn("- `1 = Codex`", content)
        self.assertIn("- `2 = OpenRouter`", content)
        self.assertIn("- `4 = Cursor API`", content)
        self.assertIn(
            "- if the user chooses `2`, `or`, `opr`, or `openrouter`, the shared delegate currently plans the bounded documentation-draft helper path and hands off to the existing dispatcher/runtime pair",
            content,
        )
        self.assertIn(
            "- if the user chooses `4`, `cursor-api`, `cursor_api`, or `api`, the shared delegate plans the bounded Cursor API review path and keeps Codex as final owner",
            content,
        )

    def test_backlog_handoff_shared_gate_maps_openrouter_to_two(self) -> None:
        skill_path = REPO_ROOT / "documentation" / "codex" / "skills" / "janus-backlog-handoff" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        self.assertIn(
            "- if the user chooses `2`, `or`, `openrouter`, or `opr`, invoke the same runner with `--operator-choice delegated --input-package-json <bounded package>`",
            content,
        )
        self.assertIn(
            "- if the user chooses `4`, `cursor-api`, `cursor_api`, or `api`, invoke the shared delegate and keep the task bounded to the same review package",
            content,
        )

    def test_feature_design_shared_gate_keeps_or_on_two_and_api_on_four(self) -> None:
        skill_path = REPO_ROOT / "documentation" / "codex" / "skills" / "janus-feature-design" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        self.assertIn(
            "- if the user chooses `2`, `or`, `opr`, or `openrouter`, the shared delegate currently plans the bounded feature-design helper path and hands off to the existing runner",
            content,
        )
        self.assertIn(
            "- if the user chooses `4`, `cursor-api`, `cursor_api`, or `api`, do not imply a live Cursor feature-design path unless a later migration artifact explicitly adds one",
            content,
        )

    def test_precheck_shared_gate_keeps_or_on_two_and_api_on_four(self) -> None:
        skill_path = REPO_ROOT / "documentation" / "codex" / "skills" / "janus-preimplementation-check" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        self.assertIn(
            "- if the user chooses `2`, `or`, `opr`, or `openrouter`, the shared delegate currently plans the bounded precheck helper path and hands off to the existing runner",
            content,
        )
        self.assertIn(
            "- if the user chooses `4`, `cursor-api`, `cursor_api`, or `api`, do not imply a live Cursor precheck path unless a later migration artifact explicitly adds one",
            content,
        )

    def test_quickchange_exception_keeps_option_three_hidden(self) -> None:
        skill_path = REPO_ROOT / "documentation" / "codex" / "skills" / "janus-quickchange" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        self.assertIn(
            "The visible gate for this lane is currently `1 = Codex` / `2 = OpenRouter` / `4 = Cursor API`; there is not yet a validated Cursor Composer quickchange backend here, so option `3` stays unavailable for this specific slice.",
            content,
        )
        self.assertIn(
            "- if the user chooses `2`, `or`, `opr`, or `openrouter`, the shared delegate currently plans the bounded dispatcher path and hands off to the existing helper chain",
            content,
        )
        self.assertIn(
            "- if the user chooses `4`, `cursor-api`, `cursor_api`, or `api`, the shared delegate currently plans the bounded Cursor API review path",
            content,
        )


if __name__ == "__main__":
    unittest.main()
