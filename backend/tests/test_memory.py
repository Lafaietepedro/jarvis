import tempfile
import unittest
from pathlib import Path

from app.memory import MemoryStore


class MemoryStoreTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "memory.sqlite"
        self.memory = MemoryStore(db_path=str(self.db_path))

    def tearDown(self):
        self.tempdir.cleanup()

    def test_records_and_reads_recent_commands(self):
        self.memory.record_command(
            text="qual o status",
            intent={"intent": "status"},
            action={"skill": "system", "status": "done"},
            response="Estou operacional.",
        )

        commands = self.memory.recent_commands()

        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0]["text"], "qual o status")
        self.assertEqual(commands[0]["intent"]["intent"], "status")

    def test_private_commands_are_not_recorded(self):
        self.memory.record_command(
            text="comando privado",
            intent={"intent": "status"},
            action={"skill": "system", "status": "done"},
            response="ok",
            private=True,
        )

        self.assertEqual(self.memory.recent_commands(), [])


if __name__ == "__main__":
    unittest.main()
