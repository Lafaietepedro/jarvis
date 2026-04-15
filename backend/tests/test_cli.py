import unittest

from app.cli import watch_panel


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
        if path == "/diagnostics":
            return {
                "platform": {"system": "Linux", "release": "test", "python": "3.11"},
                "audio": {"vosk_model_available": False},
                "binaries": {},
            }
        raise AssertionError(f"Unexpected path: {path}")


class CliTest(unittest.TestCase):
    def test_watch_panel_with_iterations_returns_frame(self):
        output = watch_panel(FakeClient(), interval=0, iterations=1)

        self.assertIn("[JARVIS]", output)
        self.assertIn("[DIAGNOSTICS]", output)


if __name__ == "__main__":
    unittest.main()
