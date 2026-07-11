from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


class JanusExecutionerSkillSurfaceTests(unittest.TestCase):
    def test_executioner_skill_mentions_four_choice_gate(self) -> None:
        skill_path = REPO_ROOT / "documentation" / "codex" / "skills" / "janus-executioner" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        self.assertIn("- `1 = Codex`", content)
        self.assertIn("- `2 = OpenRouter`", content)
        self.assertIn("- `3 = Cursor Composer`", content)
        self.assertIn("- `4 = Cursor API`", content)
        self.assertIn("For `TASK-EX-002` / `execution_write_apply_candidate`, option `2` is now the sealed deterministic local apply worker", content)


if __name__ == "__main__":
    unittest.main()
