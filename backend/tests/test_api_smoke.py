import json
import socket
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path

try:
    import uvicorn

    from app import main
    from app.context import LocalContextProvider
    from app.core import JarvisCore
    from app.memory import MemoryStore
except ModuleNotFoundError as exc:
    uvicorn = None
    main = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@unittest.skipIf(main is None or uvicorn is None, f"API smoke dependencies unavailable: {IMPORT_ERROR}")
class ApiSmokeTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.tempdir.name)
        (self.project_path / "README.md").write_text("# API Smoke Test\n", encoding="utf-8")
        (self.project_path / "Makefile").write_text("test:\n\tpython -m unittest\n", encoding="utf-8")
        self.previous_jarvis = main.jarvis
        self.previous_voice_running = main.voice_running
        self.memory = MemoryStore(db_path=str(self.project_path / "memory.sqlite"))
        main.jarvis = JarvisCore(
            LocalContextProvider(workspace=str(self.project_path)),
            memory_store=self.memory,
        )
        main.voice_running = False
        self.server = None
        self.thread = None
        self.base_url = None

    def tearDown(self):
        if self.server:
            self.server.should_exit = True
        if self.thread:
            self.thread.join(timeout=5)
        main.jarvis = self.previous_jarvis
        main.voice_running = self.previous_voice_running
        self.tempdir.cleanup()

    def test_http_smoke_presence_command_history_and_checkpoints(self):
        self._start_server()

        health = self._request("GET", "/health")
        self.assertEqual(health["status"], "ok")

        presence = self._request("GET", "/presence")
        self.assertEqual(presence["name"], "JARVIS")
        self.assertEqual(presence["project"]["path"], str(self.project_path))

        command = self._request("POST", "/command", {"text": "qual o status"})
        self.assertEqual(command["action"]["skill"], "system")
        self.assertEqual(command["action"]["status"], "done")

        history = self._request("GET", "/history")
        self.assertEqual(history["commands"][0]["text"], "qual o status")

        self._request("POST", "/command", {"text": "executar checkup do projeto"})
        checkpoints = self._request("GET", "/checkpoints")
        self.assertEqual(checkpoints["status"], "pending")
        self.assertEqual(checkpoints["pending_count"], 1)

    def test_http_smoke_session_and_checkpoint_events(self):
        self._start_server()

        pause = self._request("POST", "/pause")
        self.assertEqual(pause["status"], "paused")
        presence = self._request("GET", "/presence")
        self.assertEqual(presence["status"], "paused")
        self.assertFalse(presence["voice_listening"])

        resume = self._request("POST", "/resume")
        self.assertEqual(resume["status"], "active")
        presence = self._request("GET", "/presence")
        self.assertEqual(presence["status"], "active")

        self._request("POST", "/command", {"text": "executar checkup do projeto"})
        confirm = self._request(
            "POST",
            "/command",
            {"text": "confirmar checkpoint 1", "confirm_actions": True},
        )
        self.assertEqual(confirm["action"]["name"], "confirm_checkpoint")
        self.assertEqual(confirm["action"]["status"], "blocked")

        checkpoints = self._request("GET", "/checkpoints")
        self.assertEqual(checkpoints["status"], "pending")
        self.assertEqual(checkpoints["pending_count"], 1)
        self.assertEqual(checkpoints["event_count"], 1)
        self.assertEqual(checkpoints["events"][0]["reason"], "shell_disabled")

    def _start_server(self):
        port = _find_free_port()
        self.base_url = f"http://127.0.0.1:{port}"
        config = uvicorn.Config(
            main.app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            lifespan="off",
        )
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        self._wait_until_ready()

    def _wait_until_ready(self):
        deadline = time.time() + 5
        last_error = None
        while time.time() < deadline:
            try:
                self._request("GET", "/health")
                return
            except Exception as exc:
                last_error = exc
                time.sleep(0.05)
        raise AssertionError(f"API server did not become ready: {last_error}")

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        data = json.dumps(payload or {}).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))


def _find_free_port() -> int:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]
    except PermissionError as exc:
        raise unittest.SkipTest(f"Local sockets unavailable in this environment: {exc}") from exc


if __name__ == "__main__":
    unittest.main()
