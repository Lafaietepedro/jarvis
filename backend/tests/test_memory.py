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
        self.assertIn("id", commands[0])
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

    def test_export_history(self):
        self.memory.record_command(
            text="qual o status",
            intent={"intent": "status"},
            action={"skill": "system", "status": "done"},
            response="ok",
        )

        exported = self.memory.export_history()

        self.assertEqual(len(exported["commands"]), 1)
        self.assertEqual(exported["commands"][0]["text"], "qual o status")
        self.assertIn("stats", exported)

    def test_preserves_edit_audit_inside_action_history(self):
        self.memory.record_command(
            text="confirmar checkpoint 1",
            intent={"intent": "confirm_checkpoint"},
            action={
                "skill": "automation",
                "name": "confirm_checkpoint",
                "status": "done",
                "edit_audit": {
                    "path": "README.md",
                    "summary": "README.md | linha 1 (alvo 1) | primeira ocorrencia",
                    "revert_command": "preparar edicao arquivo README.md trocar Novo por Antigo",
                },
            },
            response="Checkpoint 1 confirmado.",
        )

        command = self.memory.recent_commands()[0]

        self.assertEqual(command["action"]["edit_audit"]["path"], "README.md")
        self.assertIn("trocar Novo por Antigo", command["action"]["edit_audit"]["revert_command"])

    def test_latest_edit_command_returns_most_recent_audited_edit(self):
        self.memory.record_command(
            text="qual o status",
            intent={"intent": "status"},
            action={"skill": "system", "name": "status", "status": "done"},
            response="ok",
        )
        self.memory.record_command(
            text="confirmar checkpoint 1",
            intent={"intent": "confirm_checkpoint"},
            action={
                "skill": "automation",
                "name": "confirm_checkpoint",
                "status": "done",
                "edit_audit": {"path": "README.md", "summary": "README.md | linha 1"},
            },
            response="ok",
        )

        command = self.memory.latest_edit_command()

        self.assertIsNotNone(command)
        self.assertEqual(command["text"], "confirmar checkpoint 1")
        self.assertEqual(command["action"]["edit_audit"]["path"], "README.md")

    def test_clear_history_returns_deleted_count(self):
        self.memory.record_command(
            text="qual o status",
            intent={"intent": "status"},
            action={"skill": "system", "status": "done"},
            response="ok",
        )

        deleted = self.memory.clear_history()

        self.assertEqual(deleted, 1)
        self.assertEqual(self.memory.recent_commands(), [])

    def test_audit_summary_groups_and_filters_commands(self):
        self.memory.record_command(
            text="qual o status",
            intent={"intent": "status"},
            action={"skill": "system", "name": "status", "status": "done"},
            response="ok",
        )
        self.memory.record_command(
            text="ultimos comandos",
            intent={"intent": "command_history"},
            action={"skill": "memory", "name": "command_history", "status": "done"},
            response="ok",
        )

        audit = self.memory.audit_summary(intent="status")

        self.assertEqual(audit["matching_count"], 1)
        self.assertEqual(audit["filters"]["intent"], "status")
        self.assertEqual(audit["by_intent"][0], {"name": "status", "count": 1})
        self.assertEqual(audit["by_skill"][0], {"name": "system", "count": 1})
        self.assertEqual(audit["sample"][0]["text"], "qual o status")

    def test_audit_summary_filters_by_command_id(self):
        first_id = self.memory.record_command(
            text="qual o status",
            intent={"intent": "status"},
            action={"skill": "system", "name": "status", "status": "done"},
            response="ok",
        )
        self.memory.record_command(
            text="ultimos comandos",
            intent={"intent": "command_history"},
            action={"skill": "memory", "name": "command_history", "status": "done"},
            response="ok",
        )

        audit = self.memory.audit_summary(command_id=first_id)

        self.assertEqual(audit["matching_count"], 1)
        self.assertEqual(audit["filters"]["command_id"], first_id)
        self.assertEqual(audit["sample"][0]["id"], first_id)
        self.assertEqual(audit["sample"][0]["text"], "qual o status")

    def test_deletes_commands_by_id(self):
        self.memory.record_command(
            text="qual o status",
            intent={"intent": "status"},
            action={"skill": "system", "name": "status", "status": "done"},
            response="ok",
        )
        command_id = self.memory.recent_commands()[0]["id"]

        deleted = self.memory.delete_commands(command_ids=[command_id])

        self.assertEqual(deleted["deleted"], 1)
        self.assertEqual(self.memory.recent_commands(), [])

    def test_deletes_commands_by_filter(self):
        self.memory.record_command(
            text="qual o status",
            intent={"intent": "status"},
            action={"skill": "system", "name": "status", "status": "done"},
            response="ok",
        )
        self.memory.record_command(
            text="ultimos comandos",
            intent={"intent": "command_history"},
            action={"skill": "memory", "name": "command_history", "status": "done"},
            response="ok",
        )

        deleted = self.memory.delete_commands(intent="status")

        self.assertEqual(deleted["deleted"], 1)
        self.assertEqual(self.memory.recent_commands()[0]["text"], "ultimos comandos")

    def test_delete_commands_requires_selector(self):
        deleted = self.memory.delete_commands()

        self.assertEqual(deleted["status"], "needs_selector")


if __name__ == "__main__":
    unittest.main()
