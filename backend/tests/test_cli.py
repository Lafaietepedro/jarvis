import unittest
import tempfile
from pathlib import Path

from app.cli import chat_loop, handle_chat_action, parse_chat_line, watch_panel, write_json_file


class FakeClient:
    def get(self, path, params=None):
        if path == "/presence":
            return {
                "status": "active",
                "voice_listening": False,
                "uptime_seconds": 1,
                "greeting": "JARVIS ativo.",
                "project": {"name": "jarvis", "path": "/tmp/jarvis"},
                "privacy": {"cloud_enabled": False, "memory_enabled": True},
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
    def test_watch_panel_with_iterations_returns_frame(self):
        output = watch_panel(FakeClient(), interval=0, iterations=1)

        self.assertIn("[JARVIS]", output)
        self.assertIn("[DIAGNOSTICS]", output)

    def test_parse_chat_line_command(self):
        action, payload = parse_chat_line("/privacy")

        self.assertEqual(action, "privacy")
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

    def test_handle_chat_action_ask(self):
        output = handle_chat_action(FakeClient(), "ask", {"text": "qual o status"})

        self.assertIn("[COMMAND]", output)
        self.assertIn("Estou operacional.", output)

    def test_handle_chat_action_export_history(self):
        output = handle_chat_action(FakeClient(), "export-history", {})

        self.assertIn("[HISTORY EXPORT]", output)

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


if __name__ == "__main__":
    unittest.main()
