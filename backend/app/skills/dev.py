from typing import Any

from .base import BaseSkill, SkillResult


class DevSkill(BaseSkill):
    name = "dev"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") in {"project_status", "prepare_project", "run_tests"}

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        capabilities = context["project"]["capabilities"]

        if intent.get("intent") == "run_tests":
            command = self._test_command(capabilities)
            if command is None:
                return SkillResult(
                    response="Ainda não identifiquei um comando de testes para este projeto.",
                    action={"skill": self.name, "name": "run_tests", "status": "not_available"},
                )

            return SkillResult(
                response=f"Posso rodar `{command}`. Preciso da sua confirmação antes de executar.",
                action={
                    "skill": "shell",
                    "name": "run_command",
                    "status": "needs_confirmation",
                    "command": command,
                    "source_skill": self.name,
                },
                suggestions=["confirmar a execucao", "listar arquivos do projeto"],
            )

        if intent.get("intent") == "prepare_project":
            suggestions = self._project_suggestions(capabilities)
            return SkillResult(
                response="Analisei o projeto e preparei os proximos passos provaveis.",
                action={"skill": self.name, "name": "prepare_project", "status": "done"},
                suggestions=suggestions,
                data={"capabilities": capabilities, "markers": context["project"]["markers"]},
            )

        return SkillResult(
            response="Este projeto esta carregado no contexto local. Posso inspecionar arquivos, sugerir comandos e preparar execucoes com confirmacao.",
            action={"skill": self.name, "name": "project_status", "status": "done"},
            suggestions=self._project_suggestions(capabilities),
            data={"capabilities": capabilities, "markers": context["project"]["markers"]},
        )

    def _test_command(self, capabilities: dict[str, bool]) -> str | None:
        if capabilities.get("has_makefile"):
            return "make test"
        if capabilities.get("has_python"):
            return "python -m unittest discover -s tests"
        if capabilities.get("has_node"):
            return "npm test"
        return None

    def _project_suggestions(self, capabilities: dict[str, bool]) -> list[str]:
        suggestions = []
        test_command = self._test_command(capabilities)
        if test_command:
            suggestions.append(f"rodar {test_command}")
        if capabilities.get("has_docker_compose"):
            suggestions.append("subir ambiente com docker compose")
        if capabilities.get("has_python"):
            suggestions.append("verificar testes do backend")
        if capabilities.get("has_node"):
            suggestions.append("verificar scripts do package.json")
        suggestions.append("listar arquivos do projeto")
        return suggestions[:5]
