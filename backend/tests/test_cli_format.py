import unittest

from app.cli_format import (
    format_checkpoints,
    format_command_result,
    format_history_export,
    format_diagnostics,
    format_history,
    format_panel,
    format_presence,
    format_privacy,
    format_ui_state,
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
            "automation_checkpoints": [
                {
                    "checkpoint_id": 1,
                    "label": "Rodar testes do projeto",
                    "plan": "project_checkup",
                    "reason": "confirmation_required",
                }
            ],
            "automation_checkpoint_events": [
                {
                    "checkpoint_id": 1,
                    "label": "Rodar testes do projeto",
                    "plan": "project_checkup",
                    "status": "blocked",
                    "reason": "shell_disabled",
                }
            ],
        }
        self.privacy = {
            "data": {
                "permissions": {
                    "cloud_enabled": False,
                    "browser_actions_enabled": False,
                    "desktop_actions_enabled": False,
                    "ide_actions_enabled": False,
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
            "python_modules": {
                "vosk": {"available": False},
                "soundfile": {"available": True},
            },
        }
        self.checkpoints = {
            "status": "pending",
            "pending_count": 1,
            "event_count": 1,
            "summary": {
                "pending": 1,
                "blocked_events": 1,
                "next_step": "Revisar e confirmar checkpoint 1.",
            },
            "checkpoints": [
                {
                    "checkpoint_id": 1,
                    "label": "Rodar testes do projeto",
                    "plan": "project_checkup",
                    "reason": "confirmation_required",
                    "command": "make test",
                    "next_step": "Revisar comando `make test` antes de confirmar.",
                }
            ],
            "events": [
                {
                    "checkpoint_id": 1,
                    "label": "Rodar testes do projeto",
                    "plan": "project_checkup",
                    "status": "blocked",
                    "reason": "shell_disabled",
                    "message": "Rodar testes do projeto foi bloqueado: shell_disabled.",
                }
            ],
        }
        self.ui_state = {
            "schema_version": 1,
            "presence": self.presence,
            "checkpoints": self.checkpoints,
            "history": self.history,
            "privacy": self.privacy["data"],
            "capabilities": {
                "commands": {"count": 2, "items": []},
                "enabled_count": 0,
                "blocked_count": 5,
                "actions": [
                    {
                        "id": "shell.run_command",
                        "label": "Executar comandos de shell",
                        "enabled": False,
                        "env_var": "JARVIS_ENABLE_SHELL",
                    }
                ],
            },
            "actions": [
                {
                    "label": "Confirmar checkpoint 1",
                    "command": "confirmar checkpoint 1",
                    "risk": "medium",
                    "requires_confirmation": True,
                }
            ],
            "next_actions": ["confirmar checkpoint 1", "qual o status"],
        }

    def test_format_presence(self):
        output = format_presence(self.presence)

        self.assertIn("[JARVIS]", output)
        self.assertIn("Project: jarvis", output)
        self.assertIn("Pending checkpoints: 1", output)
        self.assertIn("Checkpoint events: 1", output)

    def test_format_checkpoints(self):
        output = format_checkpoints(self.presence)

        self.assertIn("[CHECKPOINTS]", output)
        self.assertIn("Rodar testes do projeto", output)
        self.assertIn("confirmar checkpoint 1", output)
        self.assertIn("Recent checkpoint events:", output)
        self.assertIn("shell_disabled", output)

    def test_format_empty_checkpoints(self):
        output = format_checkpoints({"automation_checkpoints": []})

        self.assertIn("No pending checkpoints.", output)

    def test_format_dedicated_checkpoints_payload(self):
        output = format_checkpoints(self.checkpoints)

        self.assertIn("Rodar testes do projeto", output)
        self.assertIn("shell_disabled", output)
        self.assertIn("Summary: pending=1", output)
        self.assertIn("Command: make test", output)

    def test_format_privacy(self):
        output = format_privacy(self.privacy)

        self.assertIn("[PRIVACY]", output)
        self.assertIn("Commands recorded: 2", output)
        self.assertIn("Browser actions: False", output)
        self.assertIn("IDE actions: False", output)

    def test_format_history(self):
        output = format_history(self.history)

        self.assertIn("[HISTORY]", output)
        self.assertIn("qual o status", output)

    def test_format_history_export(self):
        output = format_history_export(
            {
                "exported_at": "2026-04-15T00:00:00+00:00",
                "stats": {"path": "/tmp/memory.sqlite"},
                "commands": [{"text": "qual o status"}],
            }
        )

        self.assertIn("[HISTORY EXPORT]", output)
        self.assertIn("Commands exported: 1", output)

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
        self.assertIn("Python modules: 1/2 available", output)
        self.assertIn("vosk", output)

    def test_format_panel(self):
        output = format_panel(self.presence, self.privacy, self.history, self.diagnostics, self.checkpoints)

        self.assertIn("[JARVIS]", output)
        self.assertIn("[CHECKPOINTS]", output)
        self.assertIn("[PRIVACY]", output)
        self.assertIn("[HISTORY]", output)
        self.assertIn("[DIAGNOSTICS]", output)

    def test_format_ui_state(self):
        output = format_ui_state(self.ui_state)

        self.assertIn("[UI STATE]", output)
        self.assertIn("Schema: 1", output)
        self.assertIn("[CAPABILITIES]", output)
        self.assertIn("JARVIS_ENABLE_SHELL", output)
        self.assertIn("[NEXT ACTIONS]", output)
        self.assertIn("Confirmar checkpoint 1 [medium confirm]", output)


if __name__ == "__main__":
    unittest.main()
