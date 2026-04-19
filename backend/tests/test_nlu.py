import unittest

from app.nlu import parse_intent


class ParseIntentTest(unittest.TestCase):
    def test_turn_on_light_with_area(self):
        intent = parse_intent("JARVIS, acenda a luz da sala por favor")

        self.assertEqual(intent["intent"], "turn_on")
        self.assertEqual(intent["device"], "light")
        self.assertEqual(intent["domain"], "light")
        self.assertEqual(intent["area"], "sala")

    def test_turn_off_light_with_accented_area(self):
        intent = parse_intent("Apague a lâmpada da cozinha agora")

        self.assertEqual(intent["intent"], "turn_off")
        self.assertEqual(intent["device"], "light")
        self.assertEqual(intent["area"], "cozinha")

    def test_desligar_is_not_confused_with_ligar(self):
        intent = parse_intent("desligar a luz da sala")

        self.assertEqual(intent["intent"], "turn_off")
        self.assertEqual(intent["device"], "light")
        self.assertEqual(intent["area"], "sala")

    def test_infer_light_for_acender_room(self):
        intent = parse_intent("acenda o escritorio")

        self.assertEqual(intent["intent"], "turn_on")
        self.assertEqual(intent["device"], "light")
        self.assertEqual(intent["area"], "escritorio")

    def test_status(self):
        intent = parse_intent("qual o status")

        self.assertEqual(intent["intent"], "status")

    def test_open_app(self):
        intent = parse_intent("abrir terminal")

        self.assertEqual(intent["intent"], "open_app")
        self.assertEqual(intent["target"], "terminal")

    def test_run_command(self):
        intent = parse_intent("rode make test")

        self.assertEqual(intent["intent"], "run_command")
        self.assertEqual(intent["command"], "make test")

    def test_list_files(self):
        intent = parse_intent("listar arquivos")

        self.assertEqual(intent["intent"], "list_files")

    def test_capabilities(self):
        intent = parse_intent("o que voce pode controlar neste computador")

        self.assertEqual(intent["intent"], "capabilities")

    def test_diagnostics(self):
        intent = parse_intent("diagnostico")

        self.assertEqual(intent["intent"], "diagnostics")

    def test_dependency_check(self):
        intent = parse_intent("validar dependencias opcionais")

        self.assertEqual(intent["intent"], "dependency_check")

    def test_install_dependencies(self):
        intent = parse_intent("instalar dependencias opcionais")

        self.assertEqual(intent["intent"], "install_dependencies")

    def test_project_status(self):
        intent = parse_intent("analisar projeto")

        self.assertEqual(intent["intent"], "project_status")

    def test_project_checkup(self):
        intent = parse_intent("checkup do projeto")

        self.assertEqual(intent["intent"], "project_checkup")

    def test_execute_project_checkup(self):
        intent = parse_intent("executar checkup do projeto")

        self.assertEqual(intent["intent"], "execute_project_checkup")

    def test_automation_plan(self):
        intent = parse_intent("rotina de desenvolvimento")

        self.assertEqual(intent["intent"], "automation_plan")

    def test_execute_automation_plan(self):
        intent = parse_intent("executar rotina de desenvolvimento")

        self.assertEqual(intent["intent"], "execute_automation_plan")

    def test_run_tests(self):
        intent = parse_intent("rodar testes")

        self.assertEqual(intent["intent"], "run_tests")

    def test_open_project(self):
        intent = parse_intent("abrir projeto no vscode")

        self.assertEqual(intent["intent"], "open_project")

    def test_project_commands(self):
        intent = parse_intent("comandos do projeto")

        self.assertEqual(intent["intent"], "project_commands")

    def test_project_state(self):
        intent = parse_intent("estado do projeto")

        self.assertEqual(intent["intent"], "project_state")

    def test_history(self):
        intent = parse_intent("ultimos comandos")

        self.assertEqual(intent["intent"], "command_history")

    def test_memory_audit(self):
        intent = parse_intent("resumo da memoria")

        self.assertEqual(intent["intent"], "memory_audit")

    def test_delete_memory(self):
        intent = parse_intent("apagar comando 3")

        self.assertEqual(intent["intent"], "delete_memory")
        self.assertEqual(intent["command_id"], 3)

    def test_export_history(self):
        intent = parse_intent("exportar historico")

        self.assertEqual(intent["intent"], "export_history")

    def test_clear_history(self):
        intent = parse_intent("limpar historico")

        self.assertEqual(intent["intent"], "clear_history")

    def test_confirm_checkpoint(self):
        intent = parse_intent("confirmar checkpoint 2")

        self.assertEqual(intent["intent"], "confirm_checkpoint")
        self.assertEqual(intent["checkpoint_id"], 2)

    def test_pending_checkpoints(self):
        intent = parse_intent("checkpoints pendentes")

        self.assertEqual(intent["intent"], "pending_checkpoints")

    def test_privacy_panel(self):
        intent = parse_intent("painel de privacidade")

        self.assertEqual(intent["intent"], "privacy_panel")

    def test_media_volume_up(self):
        intent = parse_intent("aumentar volume")

        self.assertEqual(intent["intent"], "media_control")
        self.assertEqual(intent["media_action"], "volume_up")

    def test_media_status(self):
        intent = parse_intent("status do audio")

        self.assertEqual(intent["intent"], "media_control")
        self.assertEqual(intent["media_action"], "status")

    def test_web_search(self):
        intent = parse_intent("pesquisar por python fastapi")

        self.assertEqual(intent["intent"], "web_search")
        self.assertEqual(intent["query"], "python fastapi")

    def test_open_url(self):
        intent = parse_intent("abrir site example.com")

        self.assertEqual(intent["intent"], "open_url")
        self.assertEqual(intent["url"], "example.com")

    def test_multi_action_with_safe_steps(self):
        intent = parse_intent("qual o status e listar arquivos")

        self.assertEqual(intent["intent"], "multi_action")
        self.assertEqual(intent["step_count"], 2)
        self.assertEqual(intent["steps"][0]["intent"], "status")
        self.assertEqual(intent["steps"][1]["intent"], "list_files")

    def test_multi_action_keeps_sensitive_step_as_step(self):
        intent = parse_intent("estado do projeto e rodar testes")

        self.assertEqual(intent["intent"], "multi_action")
        self.assertEqual([step["intent"] for step in intent["steps"]], ["project_state", "run_tests"])

    def test_single_search_query_with_connector_does_not_become_multi_action(self):
        intent = parse_intent("pesquisar python e fastapi")

        self.assertEqual(intent["intent"], "web_search")
        self.assertEqual(intent["query"], "python e fastapi")

    def test_unknown(self):
        intent = parse_intent("toque minha playlist")

        self.assertEqual(intent["intent"], "unknown")


if __name__ == "__main__":
    unittest.main()
