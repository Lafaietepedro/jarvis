import unittest

from app.cli_format import (
    format_checkpoints,
    format_command_result,
    format_history_export,
    format_history_delete,
    format_memory_audit,
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
                    "id": 1,
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
                    "risk": "medium",
                    "permission": "JARVIS_ENABLE_SHELL",
                    "source_label": "plano de automacao",
                    "checkpoint_detail": "plano de automacao - Rodar testes do projeto - confirmation_required",
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
                    "command": "make test",
                    "source_label": "plano de automacao",
                    "event_detail": "plano de automacao - Rodar testes do projeto - shell_disabled",
                    "message": "Rodar testes do projeto foi bloqueado: shell_disabled.",
                    "next_step": "Ative JARVIS_ENABLE_SHELL=1 apenas se quiser permitir esse tipo de acao.",
                }
            ],
        }
        self.ui_state = {
            "schema_version": 1,
            "presence": self.presence,
            "checkpoints": self.checkpoints,
            "history": self.history,
            "memory_audit": {
                "generated_at": "2026-04-15T00:00:00+00:00",
                "filters": {"limit": 5},
                "matching_count": 1,
                "first_command_at": "2026-04-15T00:00:00+00:00",
                "latest_command_at": "2026-04-15T00:00:00+00:00",
                "by_intent": [{"name": "status", "count": 1}],
                "by_skill": [{"name": "system", "count": 1}],
                "by_action": [{"name": "status", "count": 1}],
                "by_status": [{"name": "done", "count": 1}],
                "sample": [
                    {
                        "id": 1,
                        "text": "qual o status",
                        "action": {"skill": "system", "name": "status", "status": "done"},
                    }
                ],
            },
            "privacy": self.privacy["data"],
            "capabilities": {
                "commands": {"count": 2, "items": []},
                "state": {"files": {"tracked_count": 4}},
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
            "proactive": {
                "suggestions": [
                    {
                        "label": "estado do projeto",
                        "command": "estado do projeto",
                        "reason": "after_status",
                    }
                ]
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
        self.assertIn("Detail: plano de automacao", output)
        self.assertIn("Risk: medium (JARVIS_ENABLE_SHELL)", output)
        self.assertIn("Context: plano de automacao", output)
        self.assertIn("Next: Ative JARVIS_ENABLE_SHELL", output)

    def test_format_checkpoints_shows_file_edit_diff(self):
        output = format_checkpoints(
            {
                "status": "pending",
                "summary": {"pending": 1},
                "checkpoints": [
                    {
                        "checkpoint_id": 2,
                        "label": "Aplicar edicao em README.md",
                        "plan": "file_edit",
                        "reason": "confirmation_required",
                        "source_label": "edicao de arquivo",
                        "path": "README.md",
                        "revert_command": "preparar edicao arquivo README.md trocar bar por foo",
                        "source_command_id": 9,
                        "source_command_text": "preparar edição arquivo README.md trocar foo por bar",
                        "occurrences": 2,
                        "replacement_strategy": "first_occurrence",
                        "edit_preview": {
                            "has_multiple_matches": True,
                            "occurrence_count": 2,
                            "before": {
                                "line_start": 1,
                                "line_end": 2,
                                "focus_start": 1,
                                "focus_end": 1,
                                "text": "   1 | foo\n   2 | keep",
                            },
                            "after": {
                                "line_start": 1,
                                "line_end": 2,
                                "focus_start": 1,
                                "focus_end": 1,
                                "text": "   1 | bar\n   2 | keep",
                            },
                        },
                        "diff": "--- a/README.md\n+++ b/README.md\n-foo\n+bar",
                        "next_step": "Revisar diff e contexto de `README.md`; apenas a primeira de 2 ocorrencias sera editada.",
                    }
                ],
                "events": [],
            }
        )

        self.assertIn("Scope: primeira ocorrencia de 2 encontrada(s)", output)
        self.assertIn("Origin: #9 preparar edição arquivo README.md trocar foo por bar", output)
        self.assertIn("Preview before: linhas 1-2 (alvo 1)", output)
        self.assertIn("Preview after: linhas 1-2 (alvo 1)", output)
        self.assertIn("Diff:", output)
        self.assertIn("--- a/README.md", output)
        self.assertIn("+bar", output)
        self.assertIn("Revert: preparar edicao arquivo README.md trocar bar por foo", output)
        self.assertIn("Context: edicao de arquivo | README.md", output)

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

    def test_format_history_shows_edit_audit_and_revert_hint(self):
        output = format_history(
            {
                "commands": [
                    {
                        "id": 2,
                        "text": "confirmar checkpoint 1",
                        "action": {
                            "skill": "automation",
                            "name": "confirm_checkpoint",
                            "status": "done",
                            "edit_audit": {
                                "path": "README.md",
                                "summary": "README.md | linha 1 (alvo 1) | primeira ocorrencia",
                                "revert_command": "preparar edicao arquivo README.md trocar Projeto Seguro por Test Project",
                            },
                        },
                    }
                ]
            }
        )

        self.assertIn("Edit: README.md | linha 1 (alvo 1) | primeira ocorrencia", output)
        self.assertIn("Revert: preparar edicao arquivo README.md trocar Projeto Seguro por Test Project", output)

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

    def test_format_memory_audit(self):
        output = format_memory_audit(
            {
                "generated_at": "2026-04-15T00:00:00+00:00",
                "filters": {"intent": "status", "limit": 5},
                "matching_count": 1,
                "first_command_at": "2026-04-15T00:00:00+00:00",
                "latest_command_at": "2026-04-15T00:00:00+00:00",
                "by_intent": [{"name": "status", "count": 1}],
                "by_skill": [{"name": "system", "count": 1}],
                "by_action": [{"name": "status", "count": 1}],
                "by_status": [{"name": "done", "count": 1}],
                "sample": [
                    {
                        "id": 1,
                        "text": "qual o status",
                        "action": {"skill": "system", "name": "status", "status": "done"},
                    }
                ],
            }
        )

        self.assertIn("[MEMORY AUDIT]", output)
        self.assertIn("Filters: intent=status", output)
        self.assertIn("By intent: status=1", output)
        self.assertIn("#1", output)
        self.assertIn("qual o status", output)

    def test_format_memory_audit_sample_shows_edit_audit(self):
        output = format_memory_audit(
            {
                "generated_at": "2026-04-15T00:00:00+00:00",
                "filters": {"limit": 5},
                "matching_count": 1,
                "first_command_at": "2026-04-15T00:00:00+00:00",
                "latest_command_at": "2026-04-15T00:00:00+00:00",
                "sample": [
                    {
                        "id": 7,
                        "text": "confirmar checkpoint 1",
                        "action": {
                            "skill": "automation",
                            "name": "confirm_checkpoint",
                            "status": "done",
                            "edit_audit": {
                                "path": "README.md",
                                "summary": "README.md | linha 1 (alvo 1) | primeira ocorrencia",
                            },
                        },
                    }
                ],
            }
        )

        self.assertIn("Edit: README.md | linha 1 (alvo 1) | primeira ocorrencia", output)

    def test_format_history_delete(self):
        output = format_history_delete(
            {
                "status": "done",
                "deleted": 1,
                "selected": 1,
                "command_ids": [1],
            }
        )

        self.assertIn("[HISTORY DELETE]", output)
        self.assertIn("Deleted commands: 1", output)
        self.assertIn("Command ids: 1", output)

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

    def test_format_multi_action_command_result(self):
        output = format_command_result(
            {
                "response": "Preparei o pedido composto.",
                "intent": {"intent": "multi_action"},
                "action": {
                    "skill": "core",
                    "name": "multi_action",
                    "status": "needs_review",
                    "done": 1,
                    "needs_confirmation": 1,
                    "blocked": 0,
                    "checkpoint_ids": [2],
                },
                "suggestions": ["confirmar checkpoint 2"],
            }
        )

        self.assertIn("Steps: done=1 needs_confirmation=1 blocked=0", output)
        self.assertIn("Checkpoints: 2", output)
        self.assertIn("confirmar checkpoint 2", output)

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
        self.assertIn("[MEMORY AUDIT]", output)
        self.assertIn("Matching commands: 1", output)
        self.assertIn("Project files: 4", output)
        self.assertIn("[PROACTIVE]", output)
        self.assertIn("estado do projeto", output)
        self.assertIn("JARVIS_ENABLE_SHELL", output)
        self.assertIn("[NEXT ACTIONS]", output)
        self.assertIn("Confirmar checkpoint 1 [medium confirm]", output)


if __name__ == "__main__":
    unittest.main()
