import unittest

from app.diagnostics import build_optional_dependency_report


class DiagnosticsTest(unittest.TestCase):
    def test_optional_dependency_report_marks_ready(self):
        report = build_optional_dependency_report(
            {
                "audio": {"vosk_model_available": True},
                "binaries": {"pactl": {"available": True}},
                "python_modules": {"vosk": {"available": True}},
            }
        )

        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["install_hints"], [])

    def test_optional_dependency_report_builds_install_hints(self):
        report = build_optional_dependency_report(
            {
                "audio": {"vosk_model_available": False},
                "binaries": {"pactl": {"available": False}},
                "python_modules": {"vosk": {"available": False}},
            }
        )

        self.assertEqual(report["status"], "missing_optional")
        self.assertIn("pactl", report["missing"]["binaries"])
        self.assertIn("vosk", report["missing"]["python_modules"])
        commands = [hint["command"] for hint in report["install_hints"]]
        self.assertTrue(any("sudo apt install" in command for command in commands))
        self.assertTrue(any("pip install -r requirements.txt" in command for command in commands))
        self.assertTrue(any("VOSK_MODEL_PATH" in command for command in commands))


if __name__ == "__main__":
    unittest.main()
