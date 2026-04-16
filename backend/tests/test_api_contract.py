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
        self.memory = MemoryStore(db_path=str(self.project_path / "memory.sqlite"))
        main.jarvis = JarvisCore(
            LocalContextProvider(workspace=str(self.project_path)),
            memory_store=self.memory,
        )

    def tearDown(self):
        main.jarvis = self.previous_jarvis
        self.tempdir.cleanup()

    def test_presence_contract(self):
        payload = asyncio.run(main.presence())

        self.assertEqual(payload["name"], "JARVIS")
        self.assertIn("status", payload)
        self.assertIn("privacy", payload)
        self.assertIn("project", payload)
        self.assertIn("automation_checkpoints", payload)
        self.assertIn("automation_checkpoint_events", payload)

    def test_checkpoints_contract_empty(self):
        payload = asyncio.run(main.checkpoints())

        self.assertEqual(payload["status"], "empty")
        self.assertEqual(payload["pending_count"], 0)
        self.assertEqual(payload["event_count"], 0)
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


if __name__ == "__main__":
    unittest.main()
