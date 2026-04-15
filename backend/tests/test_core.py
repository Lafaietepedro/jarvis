import tempfile
import unittest
from pathlib import Path

from app.context import LocalContextProvider
from app.core import JarvisCore
from app.memory import MemoryStore


class JarvisCoreTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.tempdir.name)
        (self.project_path / "README.md").write_text("# Test Project\n", encoding="utf-8")
        (self.project_path / "Makefile").write_text("test:\n\tpython -m unittest\n", encoding="utf-8")
        self.memory = MemoryStore(db_path=str(self.project_path / "memory.sqlite"))
        self.core = JarvisCore(
            LocalContextProvider(workspace=str(self.project_path)),
            memory_store=self.memory,
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def test_status_returns_context_and_suggestions(self):
        result = self.core.execute("qual o status")

        self.assertEqual(result["action"]["status"], "done")
        self.assertEqual(result["context"]["project"]["path"], str(self.project_path))
        self.assertIn("rodar make test", result["suggestions"])

    def test_list_files(self):
        result = self.core.execute("listar arquivos")

        self.assertEqual(result["action"]["skill"], "files")
        self.assertIn("README.md", result["data"]["entries"])

    def test_shell_requires_confirmation_by_default(self):
        result = self.core.execute("rode make test")

        self.assertEqual(result["action"]["status"], "needs_confirmation")
        self.assertIn("confirmar a execucao", result["suggestions"])

    def test_desktop_actions_are_blocked_by_default(self):
        result = self.core.execute("abrir terminal")

        self.assertEqual(result["action"]["skill"], "computer")
        self.assertEqual(result["action"]["status"], "blocked")
        self.assertEqual(result["action"]["reason"], "desktop_actions_disabled")

    def test_project_status_uses_dev_skill(self):
        result = self.core.execute("analisar projeto")

        self.assertEqual(result["action"]["skill"], "dev")
        self.assertIn("rodar make test", result["suggestions"])

    def test_memory_records_non_private_commands(self):
        self.core.execute("qual o status")

        commands = self.memory.recent_commands()

        self.assertEqual(commands[0]["text"], "qual o status")

    def test_memory_skips_private_commands(self):
        self.core.execute("qual o status", options={"private": True})

        self.assertEqual(self.memory.recent_commands(), [])

    def test_history_command_reads_memory(self):
        self.core.execute("qual o status")
        result = self.core.execute("ultimos comandos")

        self.assertEqual(result["action"]["skill"], "memory")
        self.assertTrue(result["data"]["commands"])

    def test_privacy_panel_reports_memory_and_permissions(self):
        result = self.core.execute("painel de privacidade")

        self.assertEqual(result["action"]["skill"], "privacy")
        self.assertIn("memory", result["data"])
        self.assertIn("permissions", result["data"])

    def test_diagnostics_uses_system_skill(self):
        result = self.core.execute("diagnostico")

        self.assertEqual(result["action"]["skill"], "system")
        self.assertEqual(result["action"]["name"], "diagnostics")
        self.assertIn("binaries", result["data"])

    def test_media_actions_are_blocked_by_default(self):
        result = self.core.execute("aumentar volume")

        self.assertEqual(result["action"]["skill"], "media")
        self.assertEqual(result["action"]["status"], "blocked")
        self.assertEqual(result["action"]["reason"], "media_actions_disabled")


if __name__ == "__main__":
    unittest.main()
