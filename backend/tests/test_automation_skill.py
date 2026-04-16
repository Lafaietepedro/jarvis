import tempfile
import unittest
from pathlib import Path

from app.skills.automation import build_development_routine_plan, build_project_checkup_plan, execute_plan


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
            },
            "privacy": {
                "local_first": True,
                "cloud_enabled": False,
                "memory_enabled": True,
            },
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

    def test_execute_project_checkup_runs_safe_steps_and_stops_at_checkpoint(self):
        plan = build_project_checkup_plan(self.context)

        report = execute_plan(plan, self.context, {})

        self.assertEqual(report["execution"], "checkpointed")
        self.assertEqual(report["status"], "blocked")
        self.assertGreaterEqual(len(report["executed_steps"]), 2)
        self.assertTrue(report["checkpoints"])
        self.assertEqual(report["checkpoints"][0]["step"]["command"], "make test")

    def test_execute_plan_checkpoints_unsupported_safe_step(self):
        plan = {
            "name": "custom",
            "project": self.context["project"],
            "steps": [
                {
                    "label": "Passo seguro desconhecido",
                    "intent": "unsupported_step",
                    "risk": "low",
                    "requires_confirmation": False,
                }
            ],
        }

        report = execute_plan(plan, self.context, {})

        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["checkpoints"][0]["reason"], "unsupported_safe_step")


if __name__ == "__main__":
    unittest.main()
