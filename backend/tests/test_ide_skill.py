import tempfile
import unittest
from pathlib import Path

from app.skills.ide import detect_project_commands


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

        values = [command["command"] for command in commands]
        self.assertIn("make test", values)
        self.assertIn("make start", values)
        self.assertIn("npm run dev", values)
        self.assertIn("npm run test", values)


if __name__ == "__main__":
    unittest.main()
