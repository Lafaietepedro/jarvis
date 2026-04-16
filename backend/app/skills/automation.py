from pathlib import Path
from typing import Any

from .base import BaseSkill, SkillResult
from .ide import detect_project_commands


class AutomationSkill(BaseSkill):
    name = "automation"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") in {"automation_plan", "project_checkup"}

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        if intent.get("intent") == "project_checkup":
            plan = build_project_checkup_plan(context)
            return SkillResult(
                response="Montei um plano seguro de check-up do projeto. Nenhuma ação sensível foi executada.",
                action={"skill": self.name, "name": "project_checkup", "status": "planned"},
                suggestions=[step["command"] for step in plan["steps"] if step.get("command")][:5],
                data=plan,
            )

        plan = build_development_routine_plan(context)
        return SkillResult(
            response="Montei uma rotina segura de desenvolvimento. Revise os passos antes de executar qualquer ação.",
            action={"skill": self.name, "name": "automation_plan", "status": "planned"},
            suggestions=[step["label"] for step in plan["steps"][:5]],
            data=plan,
        )


def build_project_checkup_plan(context: dict[str, Any]) -> dict[str, Any]:
    project_path = Path(context["project"]["path"])
    commands = detect_project_commands(project_path)
    test_command = _first_command(commands, ("make test", "npm test", "npm run test", "python -m unittest discover -s tests"))
    steps = [
        {
            "label": "Verificar diagnóstico local",
            "intent": "diagnostics",
            "risk": "low",
            "requires_confirmation": False,
        },
        {
            "label": "Listar comandos detectados do projeto",
            "intent": "project_commands",
            "risk": "low",
            "requires_confirmation": False,
        },
    ]
    if test_command:
        steps.append(
            {
                "label": "Rodar testes do projeto",
                "intent": "run_command",
                "command": test_command,
                "risk": "medium",
                "requires_confirmation": True,
            }
        )
    steps.append(
        {
            "label": "Revisar painel de privacidade",
            "intent": "privacy_panel",
            "risk": "low",
            "requires_confirmation": False,
        }
    )
    return {
        "name": "project_checkup",
        "project": context["project"],
        "steps": steps,
        "execution": "manual_review_required",
    }


def build_development_routine_plan(context: dict[str, Any]) -> dict[str, Any]:
    project_path = Path(context["project"]["path"])
    commands = detect_project_commands(project_path)
    steps = [
        {
            "label": "Abrir projeto na IDE",
            "intent": "open_project",
            "risk": "medium",
            "requires_confirmation": False,
            "permission": "JARVIS_ENABLE_IDE_ACTIONS",
        },
        {
            "label": "Listar comandos do projeto",
            "intent": "project_commands",
            "risk": "low",
            "requires_confirmation": False,
        },
    ]
    if commands:
        steps.append(
            {
                "label": "Escolher comando de desenvolvimento",
                "intent": "project_commands",
                "risk": "low",
                "requires_confirmation": False,
                "options": commands[:5],
            }
        )
    return {
        "name": "development_routine",
        "project": context["project"],
        "steps": steps,
        "execution": "manual_review_required",
    }


def _first_command(commands: list[dict[str, str]], preferred: tuple[str, ...]) -> str | None:
    values = [command["command"] for command in commands]
    for command in preferred:
        if command in values:
            return command
    return values[0] if values else None
