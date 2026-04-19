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
        self.assertIn("estado do projeto", result["suggestions"])
        self.assertIn("rodar make test", result["suggestions"])

    def test_list_files(self):
        result = self.core.execute("listar arquivos")

        self.assertEqual(result["action"]["skill"], "files")
        self.assertIn("README.md", result["data"]["entries"])

    def test_find_file(self):
        result = self.core.execute("encontrar arquivo README.md")

        self.assertEqual(result["action"]["skill"], "files")
        self.assertEqual(result["action"]["name"], "find_file")
        self.assertEqual(result["action"]["status"], "done")
        self.assertEqual(result["data"]["matches"][0]["path"], "README.md")
        self.assertIn("ler arquivo README.md", result["suggestions"])

    def test_read_file(self):
        result = self.core.execute("ler arquivo README.md")

        self.assertEqual(result["action"]["skill"], "files")
        self.assertEqual(result["action"]["name"], "read_file")
        self.assertEqual(result["action"]["status"], "done")
        self.assertEqual(result["action"]["risk"], "low")
        self.assertFalse(result["action"]["requires_confirmation"])
        self.assertEqual(result["data"]["path"], "README.md")
        self.assertIn("# Test Project", result["data"]["preview"])

    def test_read_file_blocks_path_traversal(self):
        result = self.core.execute("ler arquivo ../README.md")

        self.assertEqual(result["action"]["skill"], "files")
        self.assertEqual(result["action"]["name"], "read_file")
        self.assertEqual(result["action"]["status"], "not_found")

    def test_propose_file_edit_does_not_write(self):
        result = self.core.execute("preparar edição arquivo README.md trocar Test Project por Projeto Seguro")

        self.assertEqual(result["action"]["skill"], "files")
        self.assertEqual(result["action"]["name"], "propose_file_edit")
        self.assertEqual(result["action"]["status"], "planned")
        self.assertEqual(result["action"]["risk"], "low")
        self.assertEqual(result["action"]["checkpoint_count"], 1)
        self.assertEqual(result["action"]["checkpoint_ids"], [1])
        self.assertFalse(result["data"]["writes_file"])
        self.assertIn("-# Test Project", result["data"]["diff"])
        self.assertIn("+# Projeto Seguro", result["data"]["diff"])
        self.assertEqual(result["data"]["checkpoints"][0]["source"], "file_edit")
        self.assertEqual(result["session"]["automation_checkpoints"][0]["plan"], "file_edit")
        self.assertEqual(result["session"]["automation_checkpoints"][0]["path"], "README.md")
        self.assertIn("+# Projeto Seguro", result["session"]["automation_checkpoints"][0]["diff"])
        self.assertIn("# Test Project", (self.project_path / "README.md").read_text(encoding="utf-8"))
        self.assertIn("confirmar checkpoint 1", result["suggestions"])

    def test_propose_file_edit_requires_existing_text(self):
        result = self.core.execute("preparar edição arquivo README.md trocar Ausente por Novo")

        self.assertEqual(result["action"]["name"], "propose_file_edit")
        self.assertEqual(result["action"]["status"], "not_found")
        self.assertEqual(result["action"]["reason"], "old_text_not_found")

    def test_confirm_file_edit_checkpoint_applies_change(self):
        self.core.execute("preparar edição arquivo README.md trocar Test Project por Projeto Seguro")

        result = self.core.execute("confirmar checkpoint 1")

        self.assertEqual(result["action"]["skill"], "automation")
        self.assertEqual(result["action"]["name"], "confirm_checkpoint")
        self.assertEqual(result["action"]["status"], "done")
        self.assertEqual(result["action"]["delegated_action"]["name"], "apply_file_edit")
        self.assertEqual(result["action"]["delegated_action"]["risk"], "high")
        self.assertIn("# Projeto Seguro", (self.project_path / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(result["session"]["automation_checkpoints"], [])
        event = result["session"]["automation_checkpoint_events"][0]
        self.assertEqual(event["source"], "file_edit")
        self.assertEqual(event["intent"], "apply_file_edit")
        self.assertEqual(event["path"], "README.md")
        self.assertIn("+# Projeto Seguro", event["diff"])

    def test_shell_requires_confirmation_by_default(self):
        result = self.core.execute("rode make test")

        self.assertEqual(result["action"]["status"], "needs_confirmation")
        self.assertEqual(result["action"]["risk"], "medium")
        self.assertTrue(result["action"]["requires_confirmation"])
        self.assertEqual(result["action"]["permission"], "JARVIS_ENABLE_SHELL")
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

    def test_memory_audit_command_reads_summary(self):
        self.core.execute("qual o status")
        result = self.core.execute("resumo da memoria")

        self.assertEqual(result["action"]["skill"], "memory")
        self.assertEqual(result["action"]["name"], "memory_audit")
        self.assertGreaterEqual(result["data"]["audit"]["matching_count"], 1)

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
        self.assertEqual(result["action"]["risk"], "high")
        self.assertEqual(result["action"]["risk_reason"], "memory_deletion")
        self.assertTrue(self.memory.recent_commands())

    def test_clear_history_confirmed(self):
        self.core.execute("qual o status")
        result = self.core.execute("limpar historico", options={"confirm_actions": True})

        self.assertEqual(result["action"]["status"], "done")
        self.assertEqual(self.memory.recent_commands(), [])

    def test_delete_memory_requires_confirmation(self):
        self.core.execute("qual o status")
        command_id = self.memory.recent_commands()[0]["id"]

        result = self.core.execute(f"apagar comando {command_id}")

        self.assertEqual(result["action"]["name"], "delete_memory")
        self.assertEqual(result["action"]["status"], "needs_confirmation")
        self.assertTrue(self.memory.recent_commands())

    def test_delete_memory_confirmed(self):
        self.core.execute("qual o status")
        command_id = self.memory.recent_commands()[0]["id"]

        result = self.core.execute(f"apagar comando {command_id}", options={"confirm_actions": True})

        self.assertEqual(result["action"]["name"], "delete_memory")
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

    def test_multi_action_runs_safe_steps(self):
        result = self.core.execute("qual o status e listar arquivos")

        self.assertEqual(result["intent"]["intent"], "multi_action")
        self.assertEqual(result["action"]["skill"], "core")
        self.assertEqual(result["action"]["name"], "multi_action")
        self.assertEqual(result["action"]["status"], "done")
        self.assertEqual(result["action"]["done"], 2)
        self.assertEqual(result["action"]["risk"], "low")
        self.assertEqual(len(result["data"]["steps"]), 2)
        self.assertEqual(result["data"]["steps"][0]["action"]["name"], "status")
        self.assertEqual(result["data"]["steps"][1]["action"]["name"], "list_files")

    def test_multi_action_prepares_sensitive_steps_without_execution(self):
        result = self.core.execute("estado do projeto e rodar testes", options={"confirm_actions": True})

        self.assertEqual(result["intent"]["intent"], "multi_action")
        self.assertEqual(result["action"]["status"], "needs_review")
        self.assertEqual(result["action"]["done"], 1)
        self.assertEqual(result["action"]["needs_confirmation"], 1)
        self.assertEqual(result["action"]["checkpoint_count"], 1)
        self.assertEqual(result["action"]["checkpoint_ids"], [1])
        self.assertEqual(result["action"]["risk"], "medium")
        self.assertTrue(result["action"]["requires_confirmation"])
        self.assertEqual(result["action"]["permission"], "JARVIS_ENABLE_SHELL")
        test_step = result["data"]["steps"][1]
        self.assertEqual(test_step["action"]["status"], "needs_confirmation")
        self.assertEqual(result["data"]["checkpoints"][0]["step"]["command"], "make test")
        self.assertEqual(result["session"]["automation_checkpoints"][0]["plan"], "multi_action")
        self.assertEqual(result["session"]["automation_checkpoints"][0]["command"], "make test")
        self.assertIn("confirmar a execucao", result["suggestions"])
        self.assertIn("confirmar checkpoint 1", result["suggestions"])

    def test_multi_action_checkpoint_can_be_confirmed(self):
        self.core.execute("estado do projeto e rodar testes")

        result = self.core.execute("confirmar checkpoint 1")

        self.assertEqual(result["action"]["skill"], "automation")
        self.assertEqual(result["action"]["name"], "confirm_checkpoint")
        self.assertEqual(result["action"]["status"], "blocked")
        self.assertEqual(result["action"]["delegated_action"]["reason"], "shell_disabled")
        self.assertEqual(result["session"]["automation_checkpoints"][0]["checkpoint_id"], 1)
        event = result["session"]["automation_checkpoint_events"][0]
        self.assertEqual(event["source"], "multi_action")
        self.assertEqual(event["step_index"], 2)
        self.assertEqual(event["command"], "make test")

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
