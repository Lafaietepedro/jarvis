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

    def test_project_status(self):
        intent = parse_intent("analisar projeto")

        self.assertEqual(intent["intent"], "project_status")

    def test_run_tests(self):
        intent = parse_intent("rodar testes")

        self.assertEqual(intent["intent"], "run_tests")

    def test_history(self):
        intent = parse_intent("ultimos comandos")

        self.assertEqual(intent["intent"], "command_history")

    def test_export_history(self):
        intent = parse_intent("exportar historico")

        self.assertEqual(intent["intent"], "export_history")

    def test_clear_history(self):
        intent = parse_intent("limpar historico")

        self.assertEqual(intent["intent"], "clear_history")

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

    def test_unknown(self):
        intent = parse_intent("toque minha playlist")

        self.assertEqual(intent["intent"], "unknown")


if __name__ == "__main__":
    unittest.main()
