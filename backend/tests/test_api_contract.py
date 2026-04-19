import asyncio
import tempfile
import unittest
from pathlib import Path

try:
    from app import main
    from app.context import LocalContextProvider
    from app.core import JarvisCore
    from app.memory import MemoryStore
except ModuleNotFoundError as exc:
    main = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@unittest.skipIf(main is None, f"API dependencies unavailable: {IMPORT_ERROR}")
class ApiContractTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.tempdir.name)
        (self.project_path / "README.md").write_text("# API Contract Test\n", encoding="utf-8")
        (self.project_path / "Makefile").write_text("test:\n\tpython -m unittest\n", encoding="utf-8")
        self.previous_jarvis = main.jarvis
        self.previous_voice_running = main.voice_running
        self.memory = MemoryStore(db_path=str(self.project_path / "memory.sqlite"))
        main.jarvis = JarvisCore(
            LocalContextProvider(workspace=str(self.project_path)),
            memory_store=self.memory,
        )
        main.voice_running = False

    def tearDown(self):
        main.jarvis = self.previous_jarvis
        main.voice_running = self.previous_voice_running
        self.tempdir.cleanup()

    def test_presence_contract(self):
        payload = asyncio.run(main.presence())

        self.assertEqual(payload["name"], "JARVIS")
        self.assertIn("status", payload)
        self.assertIn("privacy", payload)
        self.assertIn("project", payload)
        self.assertIn("automation_checkpoints", payload)
        self.assertIn("automation_checkpoint_events", payload)

    def test_context_contract(self):
        payload = asyncio.run(main.context())

        self.assertEqual(payload["project"]["path"], str(self.project_path))
        self.assertEqual(payload["project"]["name"], self.project_path.name)
        self.assertIn("README.md", payload["project"]["markers"])
        self.assertIn("Makefile", payload["project"]["markers"])
        self.assertTrue(payload["project"]["capabilities"]["has_makefile"])
        self.assertFalse(payload["project"]["capabilities"]["has_node"])
        self.assertTrue(payload["privacy"]["local_first"])
        self.assertFalse(payload["privacy"]["cloud_enabled"])
        self.assertFalse(payload["privacy"]["shell_enabled"])
        self.assertTrue(payload["privacy"]["memory_enabled"])

    def test_history_contract(self):
        command = main.CommandRequest(text="qual o status")
        asyncio.run(main.command(command))

        payload = asyncio.run(main.history(limit=5))

        self.assertIn("commands", payload)
        self.assertEqual(len(payload["commands"]), 1)
        history_entry = payload["commands"][0]
        self.assertIn("created_at", history_entry)
        self.assertEqual(history_entry["text"], "qual o status")
        self.assertEqual(history_entry["intent"]["intent"], "status")
        self.assertEqual(history_entry["action"]["status"], "done")
        self.assertIn("response", history_entry)

    def test_history_audit_contract(self):
        command = main.CommandRequest(text="qual o status")
        asyncio.run(main.command(command))

        payload = asyncio.run(main.audit_history(intent="status", limit=3))

        self.assertEqual(payload["filters"]["intent"], "status")
        self.assertEqual(payload["matching_count"], 1)
        self.assertEqual(payload["by_intent"][0]["name"], "status")
        self.assertEqual(payload["sample"][0]["text"], "qual o status")

    def test_pause_and_resume_contract(self):
        paused = asyncio.run(main.pause())

        self.assertEqual(paused["status"], "paused")
        presence = asyncio.run(main.presence())
        self.assertEqual(presence["status"], "paused")
        self.assertFalse(presence["voice_listening"])

        resumed = asyncio.run(main.resume())

        self.assertEqual(resumed["status"], "active")
        presence = asyncio.run(main.presence())
        self.assertEqual(presence["status"], "active")
        self.assertFalse(presence["voice_listening"])

    def test_checkpoints_contract_empty(self):
        payload = asyncio.run(main.checkpoints())

        self.assertEqual(payload["status"], "empty")
        self.assertEqual(payload["pending_count"], 0)
        self.assertEqual(payload["event_count"], 0)
        self.assertEqual(payload["summary"]["pending"], 0)
        self.assertEqual(payload["checkpoints"], [])
        self.assertEqual(payload["events"], [])

    def test_command_and_checkpoints_contract(self):
        command = main.CommandRequest(text="executar checkup do projeto")
        result = asyncio.run(main.command(command))

        self.assertEqual(result["action"]["skill"], "automation")
        self.assertEqual(result["action"]["name"], "execute_project_checkup")

        checkpoints = asyncio.run(main.checkpoints())
        self.assertEqual(checkpoints["status"], "pending")
        self.assertEqual(checkpoints["pending_count"], 1)
        self.assertEqual(checkpoints["checkpoints"][0]["checkpoint_id"], 1)

        confirm = main.CommandRequest(text="confirmar checkpoint 1", confirm_actions=True)
        confirmed = asyncio.run(main.command(confirm))

        self.assertEqual(confirmed["action"]["name"], "confirm_checkpoint")
        checkpoints = asyncio.run(main.checkpoints())
        self.assertEqual(checkpoints["event_count"], 1)
        self.assertEqual(checkpoints["events"][0]["reason"], "shell_disabled")
        self.assertEqual(checkpoints["summary"]["blocked_events"], 1)
        self.assertIn("JARVIS_ENABLE_SHELL", checkpoints["events"][0]["next_step"])

    def test_ui_state_contract(self):
        command = main.CommandRequest(text="qual o status")
        asyncio.run(main.command(command))

        payload = asyncio.run(main.ui_state(history_limit=3))

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["presence"]["name"], "JARVIS")
        self.assertEqual(payload["checkpoints"]["status"], "empty")
        self.assertEqual(payload["history"]["limit"], 3)
        self.assertEqual(payload["history"]["commands"][0]["text"], "qual o status")
        self.assertFalse(payload["privacy"]["permissions"]["cloud_enabled"])
        self.assertIn("capabilities", payload)
        self.assertIn("actions", payload["capabilities"])
        self.assertIn("proactive", payload)
        self.assertTrue(payload["proactive"]["suggestions"])
        self.assertEqual(payload["actions"][0]["risk"], "low")
        self.assertFalse(payload["actions"][0]["requires_confirmation"])
        self.assertIn("next_actions", payload)

    def test_ui_frontend_contract(self):
        page = asyncio.run(main.ui())
        script = asyncio.run(main.ui_asset("app.js"))
        manifest = asyncio.run(main.ui_asset("manifest.webmanifest"))
        missing = asyncio.run(main.ui_asset("../main.py"))

        self.assertIn(b"id=\"command-form\"", page.body)
        self.assertIn(b"/ui/state", script.body)
        self.assertIn(b"JARVIS Local", manifest.body)
        self.assertEqual(script.media_type, "text/javascript")
        self.assertEqual(manifest.media_type, "application/manifest+json")
        self.assertEqual(missing.status_code, 404)


if __name__ == "__main__":
    unittest.main()
