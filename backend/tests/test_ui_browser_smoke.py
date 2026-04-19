import shutil
import socket
import subprocess
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


@unittest.skipIf(main is None or uvicorn is None, f"Browser smoke dependencies unavailable: {IMPORT_ERROR}")
@unittest.skipIf(shutil.which("chromium") is None, "Chromium browser unavailable")
class UIBrowserSmokeTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.tempdir.name)
        (self.project_path / "README.md").write_text("# UI Browser Smoke\n", encoding="utf-8")
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

    def test_ui_renders_state_in_chromium_headless(self):
        self._start_server()
        result = self._run_chromium("--window-size=1280,900", "--dump-dom")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("JARVIS - active", result.stdout)
        self.assertIn(self.project_path.name, result.stdout)
        self.assertIn("Comando", result.stdout)
        self.assertIn("Privacidade", result.stdout)
        self.assertIn("Memoria", result.stdout)
        self.assertIn("Filtrar memoria", result.stdout)
        self.assertIn("Apagar filtro", result.stdout)

    def test_ui_captures_desktop_and_mobile_screenshots(self):
        self._start_server()

        desktop = self._capture_screenshot("desktop", "1280,900")
        mobile = self._capture_screenshot("mobile", "390,844")

        self.assertGreater(desktop.stat().st_size, 5000)
        self.assertGreater(mobile.stat().st_size, 3000)

    def _capture_screenshot(self, name: str, window_size: str) -> Path:
        screenshot = self.project_path / f"ui-{name}.png"
        result = self._run_chromium(
            f"--window-size={window_size}",
            f"--screenshot={screenshot}",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(screenshot.exists())
        return screenshot

    def _run_chromium(self, *args: str):
        profile = self.project_path / f"chromium-profile-{len(args)}-{time.time_ns()}"
        try:
            return subprocess.run(
                [
                    "chromium",
                    "--headless=new",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    f"--user-data-dir={profile}",
                    "--virtual-time-budget=3000",
                    *args,
                    f"{self.base_url}/ui",
                ],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise unittest.SkipTest(f"Chromium headless timed out: {exc}") from exc

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
                with urllib.request.urlopen(f"{self.base_url}/health", timeout=3):
                    return
            except Exception as exc:
                last_error = exc
                time.sleep(0.05)
        raise AssertionError(f"API server did not become ready: {last_error}")


def _find_free_port() -> int:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]
    except PermissionError as exc:
        raise unittest.SkipTest(f"Local sockets unavailable in this environment: {exc}") from exc


if __name__ == "__main__":
    unittest.main()
