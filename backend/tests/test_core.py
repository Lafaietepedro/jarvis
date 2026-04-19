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

    def test_export_history_command(self):
        self.core.execute("qual o status")
        result = self.core.execute("exportar historico")

        self.assertEqual(result["action"]["skill"], "memory")
        self.assertEqual(result["action"]["name"], "export_history")
        self.assertTrue(result["data"]["commands"])

    def test_clear_history_requires_confirmation(self):
        self.core.execute("qual o status")
        result = self.core.execute("limpar historico")

        self.assertEqual(result["action"]["status"], "needs_confirmation")
        self.assertTrue(self.memory.recent_commands())

    def test_clear_history_confirmed(self):
        self.core.execute("qual o status")
        result = self.core.execute("limpar historico", options={"confirm_actions": True})

        self.assertEqual(result["action"]["status"], "done")
        self.assertEqual(self.memory.recent_commands(), [])

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

    def test_dependency_check_uses_system_skill(self):
        result = self.core.execute("validar dependencias opcionais")

        self.assertEqual(result["action"]["skill"], "system")
        self.assertEqual(result["action"]["name"], "dependency_check")
        self.assertIn("dependencies", result["data"])

    def test_install_dependencies_is_planned_not_executed(self):
        result = self.core.execute("instalar dependencias opcionais")

        self.assertEqual(result["action"]["skill"], "system")
        self.assertEqual(result["action"]["name"], "install_dependencies")
        self.assertEqual(result["action"]["status"], "planned")
        self.assertIn("dependencies", result["data"])

    def test_media_actions_are_blocked_by_default(self):
        result = self.core.execute("aumentar volume")

        self.assertEqual(result["action"]["skill"], "media")
        self.assertEqual(result["action"]["status"], "blocked")
        self.assertEqual(result["action"]["reason"], "media_actions_disabled")

    def test_browser_search_is_blocked_by_default(self):
        result = self.core.execute("pesquisar por fastapi")

        self.assertEqual(result["action"]["skill"], "browser")
        self.assertEqual(result["action"]["name"], "search")
        self.assertEqual(result["action"]["status"], "blocked")
        self.assertEqual(result["action"]["reason"], "browser_actions_disabled")

    def test_browser_open_url_is_blocked_by_default(self):
        result = self.core.execute("abrir site example.com")

        self.assertEqual(result["action"]["skill"], "browser")
        self.assertEqual(result["action"]["name"], "open_url")
        self.assertEqual(result["action"]["status"], "blocked")
        self.assertEqual(result["action"]["url"], "https://example.com")

    def test_project_commands_uses_ide_skill(self):
        result = self.core.execute("comandos do projeto")

        self.assertEqual(result["action"]["skill"], "ide")
        self.assertEqual(result["action"]["name"], "project_commands")
        self.assertIn("commands", result["data"])

    def test_project_state_uses_ide_skill(self):
        result = self.core.execute("estado do projeto")

        self.assertEqual(result["action"]["skill"], "ide")
        self.assertEqual(result["action"]["name"], "project_state")
        self.assertIn("files", result["data"])

    def test_open_project_is_blocked_by_default(self):
        result = self.core.execute("abrir projeto")

        self.assertEqual(result["action"]["skill"], "ide")
        self.assertEqual(result["action"]["name"], "open_project")
        self.assertEqual(result["action"]["status"], "blocked")
        self.assertEqual(result["action"]["reason"], "ide_actions_disabled")

    def test_project_checkup_builds_automation_plan(self):
        result = self.core.execute("checkup do projeto")

        self.assertEqual(result["action"]["skill"], "automation")
        self.assertEqual(result["action"]["status"], "planned")
        self.assertEqual(result["data"]["execution"], "manual_review_required")

    def test_execute_project_checkup_runs_safe_steps_and_reports_checkpoint(self):
        result = self.core.execute("executar checkup do projeto")

        self.assertEqual(result["action"]["skill"], "automation")
        self.assertEqual(result["action"]["name"], "execute_project_checkup")
        self.assertEqual(result["action"]["status"], "blocked")
        self.assertEqual(result["data"]["execution"], "checkpointed")
        self.assertTrue(result["data"]["executed_steps"])
        self.assertTrue(result["data"]["checkpoints"])
        self.assertEqual(result["session"]["automation_checkpoints"][0]["checkpoint_id"], 1)

    def test_development_routine_builds_automation_plan(self):
        result = self.core.execute("rotina de desenvolvimento")

        self.assertEqual(result["action"]["skill"], "automation")
        self.assertEqual(result["action"]["name"], "automation_plan")
        self.assertTrue(result["data"]["steps"])

    def test_execute_development_routine_reports_ide_checkpoint(self):
        result = self.core.execute("executar rotina de desenvolvimento")

        self.assertEqual(result["action"]["skill"], "automation")
        self.assertEqual(result["action"]["name"], "execute_automation_plan")
        self.assertEqual(result["action"]["status"], "blocked")
        self.assertEqual(result["data"]["checkpoints"][0]["step"]["intent"], "open_project")

    def test_confirm_checkpoint_uses_pending_automation_checkpoint(self):
        self.core.execute("executar checkup do projeto")

        result = self.core.execute("confirmar checkpoint 1")

        self.assertEqual(result["action"]["skill"], "automation")
        self.assertEqual(result["action"]["name"], "confirm_checkpoint")
        self.assertEqual(result["action"]["status"], "blocked")
        self.assertEqual(result["action"]["delegated_action"]["reason"], "shell_disabled")
        self.assertEqual(result["session"]["automation_checkpoints"][0]["checkpoint_id"], 1)
        self.assertEqual(result["session"]["automation_checkpoint_events"][0]["status"], "blocked")

    def test_pending_checkpoints_reports_session_state(self):
        self.core.execute("executar checkup do projeto")
        self.core.execute("confirmar checkpoint 1")

        result = self.core.execute("checkpoints pendentes")

        self.assertEqual(result["action"]["skill"], "automation")
        self.assertEqual(result["action"]["name"], "pending_checkpoints")
        self.assertEqual(result["action"]["status"], "done")
        self.assertEqual(result["data"]["checkpoints"][0]["checkpoint_id"], 1)
        self.assertEqual(result["data"]["events"][0]["reason"], "shell_disabled")


if __name__ == "__main__":
    unittest.main()
