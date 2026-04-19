import tempfile
import unittest
from pathlib import Path

from app.skills.ide import IDESkill, detect_project_commands, detect_project_state


class IDESkillTest(unittest.TestCase):
    def test_detects_makefile_and_package_scripts(self):
        with tempfile.TemporaryDirectory() as tempdir:
            project_path = Path(tempdir)
            (project_path / "Makefile").write_text(
                ".PHONY: test\n"
                "test:\n\tpython -m unittest\n"
                "start:\n\tuvicorn app.main:app\n",
                encoding="utf-8",
            )
            (project_path / "package.json").write_text(
                '{"scripts":{"dev":"vite","test":"vitest"}}',
                encoding="utf-8",
            )

            commands = detect_project_commands(project_path)
            state = detect_project_state(project_path)

        values = [command["command"] for command in commands]
        self.assertIn("make test", values)
        self.assertIn("make start", values)
        self.assertIn("npm run dev", values)
        self.assertIn("npm run test", values)
        self.assertIn("Makefile", state["markers"])
        self.assertEqual(state["commands"]["count"], 4)
        self.assertTrue(any(file["path"] == "package.json" for file in state["files"]["items"]))

    def test_project_state_skill(self):
        with tempfile.TemporaryDirectory() as tempdir:
            project_path = Path(tempdir)
            (project_path / "README.md").write_text("# Project\n", encoding="utf-8")
            (project_path / "app.py").write_text("print('ok')\n", encoding="utf-8")

            result = IDESkill().handle(
                {"intent": "project_state", "text": "estado do projeto"},
                {"project": {"path": str(project_path)}},
                {},
            )

        self.assertEqual(result.action["name"], "project_state")
        self.assertEqual(result.data["files"]["tracked_count"], 2)


if __name__ == "__main__":
    unittest.main()
