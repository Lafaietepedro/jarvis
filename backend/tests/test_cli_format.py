import unittest

from app.cli_format import (
    format_command_result,
    format_diagnostics,
    format_history,
    format_panel,
    format_presence,
    format_privacy,
)


class CliFormatTest(unittest.TestCase):
    def setUp(self):
        self.presence = {
            "status": "active",
            "voice_listening": False,
            "uptime_seconds": 12,
            "greeting": "JARVIS ativo.",
            "project": {"name": "jarvis", "path": "/tmp/jarvis"},
            "privacy": {"cloud_enabled": False, "memory_enabled": True},
        }
        self.privacy = {
            "data": {
                "permissions": {
                    "cloud_enabled": False,
                    "desktop_actions_enabled": False,
                    "shell_enabled": False,
                    "media_actions_enabled": False,
                },
                "memory": {
                    "enabled": True,
                    "commands_recorded": 2,
                    "path": "/tmp/jarvis/.jarvis/memory.sqlite",
                },
                "session": {"status": "active"},
            }
        }
        self.history = {
            "commands": [
                {
                    "text": "qual o status",
                    "action": {"skill": "system", "name": "status", "status": "done"},
                }
            ]
        }
        self.diagnostics = {
            "platform": {"system": "Linux", "release": "test", "python": "3.11"},
            "audio": {"vosk_model_available": False},
            "binaries": {
                "pactl": {"available": False},
                "playerctl": {"available": True},
            },
        }

    def test_format_presence(self):
        output = format_presence(self.presence)

        self.assertIn("[JARVIS]", output)
        self.assertIn("Project: jarvis", output)

    def test_format_privacy(self):
        output = format_privacy(self.privacy)

        self.assertIn("[PRIVACY]", output)
        self.assertIn("Commands recorded: 2", output)

    def test_format_history(self):
        output = format_history(self.history)

        self.assertIn("[HISTORY]", output)
        self.assertIn("qual o status", output)

    def test_format_empty_history(self):
        output = format_history({"commands": []})

        self.assertIn("No commands recorded yet.", output)

    def test_format_command_result(self):
        output = format_command_result(
            {
                "response": "Estou operacional.",
                "intent": {"intent": "status"},
                "action": {"skill": "system", "name": "status", "status": "done"},
                "suggestions": ["listar arquivos"],
            }
        )

        self.assertIn("[COMMAND]", output)
        self.assertIn("listar arquivos", output)

    def test_format_diagnostics(self):
        output = format_diagnostics(self.diagnostics)

        self.assertIn("[DIAGNOSTICS]", output)
        self.assertIn("pactl", output)

    def test_format_panel(self):
        output = format_panel(self.presence, self.privacy, self.history, self.diagnostics)

        self.assertIn("[JARVIS]", output)
        self.assertIn("[PRIVACY]", output)
        self.assertIn("[HISTORY]", output)
        self.assertIn("[DIAGNOSTICS]", output)


if __name__ == "__main__":
    unittest.main()
