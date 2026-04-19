import unittest

from app.proactive import build_proactive_suggestions


class ProactiveSuggestionsTest(unittest.TestCase):
    def setUp(self):
        self.context = {
            "project": {
                "name": "jarvis",
                "markers": ["README.md", "Makefile"],
                "capabilities": {
                    "has_makefile": True,
                    "has_docker_compose": False,
                    "has_python": True,
                    "has_node": False,
                },
            }
        }
        self.project_state = {
            "markers": ["README.md", "Makefile"],
            "commands": {
                "items": [
                    {"command": "make test", "source": "Makefile"},
                    {"command": "make start", "source": "Makefile"},
                ]
            },
        }

    def test_suggests_project_snapshot_without_history(self):
        suggestions = build_proactive_suggestions(self.context, project_state=self.project_state)

        commands = [suggestion["command"] for suggestion in suggestions]
        self.assertEqual(commands[0], "estado do projeto")
        self.assertIn("rodar make test", commands)
        self.assertEqual(suggestions[0]["kind"], "proactive")
        test_suggestion = next(suggestion for suggestion in suggestions if suggestion["command"] == "rodar make test")
        self.assertEqual(test_suggestion["risk"], "medium")
        self.assertTrue(test_suggestion["requires_confirmation"])
        self.assertEqual(test_suggestion["permission"], "JARVIS_ENABLE_SHELL")

    def test_uses_recent_status_as_next_intent_signal(self):
        history = [{"intent": {"intent": "status"}, "text": "qual o status"}]

        suggestions = build_proactive_suggestions(self.context, history=history, project_state=self.project_state)

        commands = [suggestion["command"] for suggestion in suggestions]
        self.assertIn("estado do projeto", commands)
        self.assertIn("checkup do projeto", commands)


if __name__ == "__main__":
    unittest.main()
