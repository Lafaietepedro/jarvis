import argparse
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.cli import (
    chat_loop,
    format_chat_session_history,
    handle_chat_action,
    parse_chat_line,
    run,
    watch_panel,
    write_json_file,
)


class FakeClient:
    posted_payloads = []
    get_paths = []

    def get(self, path, params=None):
        self.get_paths.append(path)
        if path == "/presence":
            return {
                "status": "active",
                "voice_listening": False,
                "uptime_seconds": 1,
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
        if path == "/checkpoints":
            return {
                "status": "pending",
                "pending_count": 1,
                "event_count": 1,
                "checkpoints": [
                    {
                        "checkpoint_id": 1,
                        "label": "Rodar testes do projeto",
                        "plan": "project_checkup",
                        "reason": "confirmation_required",
                    }
                ],
                "events": [
                    {
                        "checkpoint_id": 1,
                        "label": "Rodar testes do projeto",
                        "plan": "project_checkup",
                        "status": "blocked",
                        "reason": "shell_disabled",
                    }
                ],
            }
        if path == "/ui/state":
            return {
                "schema_version": 1,
                "presence": {
                    "status": "active",
                    "voice_listening": False,
                    "uptime_seconds": 1,
                    "greeting": "JARVIS ativo.",
                    "project": {"name": "jarvis", "path": "/tmp/jarvis"},
                    "privacy": {"cloud_enabled": False, "memory_enabled": True},
                    "automation_checkpoints": [],
                    "automation_checkpoint_events": [],
                },
                "checkpoints": {
                    "status": "pending",
                    "pending_count": 1,
                    "event_count": 0,
                    "checkpoints": [
                        {
                            "checkpoint_id": 1,
                            "label": "Rodar testes do projeto",
                            "plan": "project_checkup",
                            "reason": "confirmation_required",
                        }
                    ],
                    "events": [],
                },
                "history": {"limit": 5, "commands": []},
                "privacy": {
                    "permissions": {"cloud_enabled": False, "shell_enabled": False},
                    "memory": {"enabled": True, "commands_recorded": 0, "path": "/tmp/memory.sqlite"},
                    "session": {"status": "active"},
                },
                "next_actions": ["confirmar checkpoint 1", "qual o status"],
            }
        if path == "/privacy":
            return {
                "data": {
                    "permissions": {},
                    "memory": {"enabled": True, "commands_recorded": 0, "path": "/tmp/memory.sqlite"},
                    "session": {"status": "active"},
                }
            }
        if path == "/history":
            return {"commands": []}
        if path == "/history/export":
            return {
                "exported_at": "2026-04-15T00:00:00+00:00",
                "stats": {"path": "/tmp/memory.sqlite"},
                "commands": [],
            }
        if path == "/diagnostics":
            return {
                "platform": {"system": "Linux", "release": "test", "python": "3.11"},
                "audio": {"vosk_model_available": False},
                "binaries": {},
            }
        raise AssertionError(f"Unexpected path: {path}")

    def post(self, path, payload=None):
        if path == "/command":
            self.posted_payloads.append(payload)
            text = (payload or {}).get("text", "")
            if text.startswith("confirmar checkpoint"):
                return {
                    "response": "Checkpoint 1 confirmado.",
                    "intent": {"intent": "confirm_checkpoint"},
                    "action": {"skill": "automation", "name": "confirm_checkpoint", "status": "blocked"},
                    "suggestions": [],
                }
            if text == "validar dependencias opcionais":
                return {
                    "response": "Dependências opcionais verificadas.",
                    "intent": {"intent": "dependency_check"},
                    "action": {"skill": "system", "name": "dependency_check", "status": "done"},
                    "suggestions": ["instalar dependencias opcionais"],
                }
            if text == "instalar dependencias opcionais":
                return {
                    "response": "Preparei os comandos de instalacao das dependencias opcionais.",
                    "intent": {"intent": "install_dependencies"},
                    "action": {"skill": "system", "name": "install_dependencies", "status": "planned"},
                    "suggestions": ["sudo apt install playerctl"],
                }
            return {
                "response": "Estou operacional.",
                "intent": {"intent": "status"},
                "action": {"skill": "system", "name": "status", "status": "done"},
                "suggestions": [],
            }
        if path in {"/pause", "/resume", "/start", "/stop"}:
            return {"status": path.lstrip("/")}
        if path == "/history/clear":
            return {"status": "done", "deleted": 1 if payload and payload.get("confirm") else 0}
        raise AssertionError(f"Unexpected path: {path}")


class CliTest(unittest.TestCase):
    def setUp(self):
        FakeClient.posted_payloads = []
        FakeClient.get_paths = []

    def test_watch_panel_with_iterations_returns_frame(self):
        output = watch_panel(FakeClient(), interval=0, iterations=1)

        self.assertIn("[JARVIS]", output)
        self.assertIn("[DIAGNOSTICS]", output)

    def test_parse_chat_line_command(self):
        action, payload = parse_chat_line("/privacy")

        self.assertEqual(action, "privacy")
        self.assertEqual(payload, {})

    def test_parse_chat_line_shortcut_command(self):
        action, payload = parse_chat_line("/p")

        self.assertEqual(action, "panel")
        self.assertEqual(payload, {})

    def test_parse_chat_line_dependencies_shortcut(self):
        action, payload = parse_chat_line("/deps")

        self.assertEqual(action, "dependencies")
        self.assertEqual(payload, {})

    def test_parse_chat_line_shortcut_confirm_checkpoint(self):
        action, payload = parse_chat_line("/cc 2")

        self.assertEqual(action, "confirm-checkpoint")
        self.assertEqual(payload["checkpoint_id"], 2)

    def test_parse_chat_line_shortcut_confirm(self):
        action, payload = parse_chat_line("/c rode make test")

        self.assertEqual(action, "ask")
        self.assertTrue(payload["confirm_actions"])
        self.assertEqual(payload["text"], "rode make test")

    def test_parse_chat_line_session_history(self):
        action, payload = parse_chat_line("/s")

        self.assertEqual(action, "session-history")
        self.assertEqual(payload, {})

    def test_parse_chat_line_private(self):
        action, payload = parse_chat_line("/private qual o status")

        self.assertEqual(action, "ask")
        self.assertTrue(payload["private"])
        self.assertEqual(payload["text"], "qual o status")

    def test_parse_chat_line_export_history(self):
        action, payload = parse_chat_line("/export-history")

        self.assertEqual(action, "export-history")
        self.assertEqual(payload, {})

    def test_parse_chat_line_checkpoints(self):
        action, payload = parse_chat_line("/checkpoints")

        self.assertEqual(action, "checkpoints")
        self.assertEqual(payload, {})

    def test_parse_chat_line_ui_state_shortcut(self):
        action, payload = parse_chat_line("/ui")

        self.assertEqual(action, "ui-state")
        self.assertEqual(payload, {})

    def test_parse_chat_line_confirm_checkpoint(self):
        action, payload = parse_chat_line("/confirm-checkpoint 1")

        self.assertEqual(action, "confirm-checkpoint")
        self.assertEqual(payload["checkpoint_id"], 1)

    def test_parse_chat_line_invalid_confirm_checkpoint(self):
        action, payload = parse_chat_line("/confirm-checkpoint um")

        self.assertEqual(action, "invalid")
        self.assertIn("Use /confirm-checkpoint", payload["message"])

    def test_handle_chat_action_ask(self):
        output = handle_chat_action(FakeClient(), "ask", {"text": "qual o status"})

        self.assertIn("[COMMAND]", output)
        self.assertIn("Estou operacional.", output)

    def test_handle_chat_action_export_history(self):
        output = handle_chat_action(FakeClient(), "export-history", {})

        self.assertIn("[HISTORY EXPORT]", output)

    def test_handle_chat_action_checkpoints(self):
        client = FakeClient()
        output = handle_chat_action(client, "checkpoints", {})

        self.assertIn("[CHECKPOINTS]", output)
        self.assertIn("Rodar testes do projeto", output)
        self.assertIn("/checkpoints", FakeClient.get_paths)

    def test_handle_chat_action_ui_state(self):
        output = handle_chat_action(FakeClient(), "ui-state", {})

        self.assertIn("[UI STATE]", output)
        self.assertIn("[NEXT ACTIONS]", output)
        self.assertIn("confirmar checkpoint 1", output)
        self.assertIn("/ui/state", FakeClient.get_paths)

    def test_handle_chat_action_dependencies(self):
        output = handle_chat_action(FakeClient(), "dependencies", {})

        self.assertIn("[COMMAND]", output)
        self.assertIn("Dependências opcionais verificadas.", output)
        self.assertEqual(FakeClient.posted_payloads[0]["text"], "validar dependencias opcionais")
        self.assertTrue(FakeClient.posted_payloads[0]["private"])

    def test_handle_chat_action_install_dependencies(self):
        output = handle_chat_action(FakeClient(), "install-dependencies", {})

        self.assertIn("[COMMAND]", output)
        self.assertIn("sudo apt install playerctl", output)
        self.assertEqual(FakeClient.posted_payloads[0]["text"], "instalar dependencias opcionais")
        self.assertTrue(FakeClient.posted_payloads[0]["private"])

    def test_watch_panel_fetches_dedicated_checkpoints_endpoint(self):
        output = watch_panel(FakeClient(), interval=0, iterations=1)

        self.assertIn("[CHECKPOINTS]", output)
        self.assertIn("/checkpoints", FakeClient.get_paths)

    def test_handle_chat_action_confirm_checkpoint(self):
        output = handle_chat_action(FakeClient(), "confirm-checkpoint", {"checkpoint_id": 1})

        self.assertIn("[COMMAND]", output)
        self.assertEqual(FakeClient.posted_payloads[0]["text"], "confirmar checkpoint 1")
        self.assertTrue(FakeClient.posted_payloads[0]["confirm_actions"])

    def test_handle_chat_action_invalid(self):
        output = handle_chat_action(FakeClient(), "invalid", {"message": "Use /confirm-checkpoint <id>."})

        self.assertEqual(output, "Use /confirm-checkpoint <id>.")

    def test_handle_chat_action_session_history(self):
        output = handle_chat_action(
            FakeClient(),
            "session-history",
            {},
            session_history=[{"input": "qual o status", "action": "ask"}],
        )

        self.assertIn("[CHAT SESSION]", output)
        self.assertIn("qual o status -> ask", output)

    def test_format_empty_chat_session_history(self):
        output = format_chat_session_history([])

        self.assertIn("No messages in this session yet.", output)

    def test_run_confirm_checkpoint(self):
        args = argparse.Namespace(
            url="http://test",
            command="confirm-checkpoint",
            checkpoint_id=1,
            private=True,
            speak=False,
        )

        with patch("app.cli.JarvisHttpClient", return_value=FakeClient()):
            output = run(args)

        self.assertIn("[COMMAND]", output)
        self.assertEqual(FakeClient.posted_payloads[0]["text"], "confirmar checkpoint 1")
        self.assertTrue(FakeClient.posted_payloads[0]["private"])

    def test_run_dependencies(self):
        args = argparse.Namespace(url="http://test", command="dependencies")

        with patch("app.cli.JarvisHttpClient", return_value=FakeClient()):
            output = run(args)

        self.assertIn("[COMMAND]", output)
        self.assertEqual(FakeClient.posted_payloads[0]["text"], "validar dependencias opcionais")

    def test_run_ui_state(self):
        args = argparse.Namespace(url="http://test", command="ui-state", history_limit=5)

        with patch("app.cli.JarvisHttpClient", return_value=FakeClient()):
            output = run(args)

        self.assertIn("[UI STATE]", output)
        self.assertIn("Schema: 1", output)
        self.assertIn("/ui/state", FakeClient.get_paths)

    def test_run_desktop_launcher_prints_entry(self):
        args = argparse.Namespace(
            url="http://test",
            command="desktop-launcher",
            ui_url=None,
            output=None,
        )

        output = run(args)

        self.assertIn("[Desktop Entry]", output)
        self.assertIn("Exec=xdg-open http://test/ui", output)

    def test_run_desktop_launcher_writes_entry(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "jarvis.desktop"
            args = argparse.Namespace(
                url="http://test",
                command="desktop-launcher",
                ui_url="http://custom/ui",
                output=str(path),
            )

            output = run(args)

            self.assertIn("Desktop launcher written", output)
            self.assertIn("Exec=xdg-open http://custom/ui", path.read_text(encoding="utf-8"))

    def test_handle_chat_action_clear_history(self):
        output = handle_chat_action(FakeClient(), "clear-history", {})

        self.assertIn('"status": "done"', output)

    def test_write_json_file(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "history.json"

            write_json_file(str(path), {"ok": True})

            self.assertIn('"ok": true', path.read_text(encoding="utf-8"))

    def test_chat_loop_exits(self):
        inputs = iter(["/exit"])
        outputs = []

        result = chat_loop(FakeClient(), input_func=lambda _: next(inputs), output_func=outputs.append)

        self.assertEqual(result, "Chat closed.")
        self.assertTrue(outputs[0].startswith("JARVIS chat active"))

    def test_chat_loop_tracks_session_history(self):
        inputs = iter(["qual o status", "/s", "/exit"])
        outputs = []

        result = chat_loop(FakeClient(), input_func=lambda _: next(inputs), output_func=outputs.append)

        self.assertEqual(result, "Chat closed.")
        self.assertTrue(any("[CHAT SESSION]" in output for output in outputs))
        self.assertTrue(any("qual o status -> ask" in output for output in outputs))


if __name__ == "__main__":
    unittest.main()
