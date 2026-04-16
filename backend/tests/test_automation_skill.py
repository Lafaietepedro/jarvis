import tempfile
import unittest
from pathlib import Path

from app.skills.automation import build_development_routine_plan, build_project_checkup_plan


class AutomationSkillTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.tempdir.name)
        (self.project_path / "Makefile").write_text("test:\n\tpython -m unittest\n", encoding="utf-8")
        self.context = {
            "project": {
                "path": str(self.project_path),
                "name": self.project_path.name,
                "markers": ["Makefile"],
                "capabilities": {"has_makefile": True},
            }
        }

    def tearDown(self):
        self.tempdir.cleanup()

    def test_project_checkup_plan_includes_confirmed_test_step(self):
        plan = build_project_checkup_plan(self.context)

        commands = [step.get("command") for step in plan["steps"]]
        self.assertIn("make test", commands)
        self.assertEqual(plan["execution"], "manual_review_required")
        test_step = next(step for step in plan["steps"] if step.get("command") == "make test")
        self.assertTrue(test_step["requires_confirmation"])

    def test_development_routine_plan_includes_ide_step(self):
        plan = build_development_routine_plan(self.context)

        labels = [step["label"] for step in plan["steps"]]
        self.assertIn("Abrir projeto na IDE", labels)
        self.assertEqual(plan["execution"], "manual_review_required")


if __name__ == "__main__":
    unittest.main()
