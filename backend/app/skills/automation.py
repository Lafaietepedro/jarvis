from pathlib import Path
from typing import Any

from ..diagnostics import collect_diagnostics
from .base import BaseSkill, SkillResult
from .ide import detect_project_commands


class AutomationSkill(BaseSkill):
    name = "automation"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") in {
            "automation_plan",
            "project_checkup",
            "execute_automation_plan",
            "execute_project_checkup",
        }

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        if intent.get("intent") == "execute_project_checkup":
            plan = build_project_checkup_plan(context)
            report = execute_plan(plan, context, options)
            return SkillResult(
                response=_execution_response(report),
                action={"skill": self.name, "name": "execute_project_checkup", "status": report["status"]},
                suggestions=_checkpoint_suggestions(report),
                data=report,
            )

        if intent.get("intent") == "execute_automation_plan":
            plan = build_development_routine_plan(context)
            report = execute_plan(plan, context, options)
            return SkillResult(
                response=_execution_response(report),
                action={"skill": self.name, "name": "execute_automation_plan", "status": report["status"]},
                suggestions=_checkpoint_suggestions(report),
                data=report,
            )

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


def execute_plan(plan: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
    results = []
    for index, step in enumerate(plan["steps"], start=1):
        if _requires_checkpoint(step):
            results.append(
                {
                    "index": index,
                    "label": step["label"],
                    "status": "checkpoint",
                    "reason": "confirmation_required" if step.get("requires_confirmation") else "risk_or_permission",
                    "step": step,
                }
            )
            continue

        results.append(_execute_safe_step(index, step, context, options))

    checkpoints = [result for result in results if result["status"] == "checkpoint"]
    return {
        "name": plan["name"],
        "project": plan["project"],
        "status": "blocked" if checkpoints else "done",
        "execution": "checkpointed",
        "executed_steps": [result for result in results if result["status"] == "done"],
        "checkpoints": checkpoints,
        "results": results,
    }


def _requires_checkpoint(step: dict[str, Any]) -> bool:
    if step.get("requires_confirmation"):
        return True
    if step.get("risk") != "low":
        return True
    if step.get("permission"):
        return True
    return False


def _execute_safe_step(index: int, step: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
    intent = step.get("intent")
    if intent == "diagnostics":
        return {
            "index": index,
            "label": step["label"],
            "status": "done",
            "intent": intent,
            "data": collect_diagnostics(context),
        }

    if intent == "project_commands":
        commands = detect_project_commands(Path(context["project"]["path"]))
        return {
            "index": index,
            "label": step["label"],
            "status": "done",
            "intent": intent,
            "data": {"commands": commands},
        }

    if intent == "privacy_panel":
        memory_store = options.get("memory_store")
        session_state = options.get("session_state")
        return {
            "index": index,
            "label": step["label"],
            "status": "done",
            "intent": intent,
            "data": {
                "privacy": context.get("privacy", {}),
                "memory": memory_store.stats() if memory_store else {"enabled": False},
                "session": session_state.snapshot() if session_state else {},
            },
        }

    return {
        "index": index,
        "label": step["label"],
        "status": "checkpoint",
        "reason": "unsupported_safe_step",
        "step": step,
    }


def _execution_response(report: dict[str, Any]) -> str:
    executed = len(report["executed_steps"])
    checkpoints = len(report["checkpoints"])
    if checkpoints:
        return f"Executei {executed} passos seguros e parei em {checkpoints} checkpoints."
    return f"Executei {executed} passos seguros do plano."


def _checkpoint_suggestions(report: dict[str, Any]) -> list[str]:
    suggestions = []
    for checkpoint in report["checkpoints"]:
        step = checkpoint["step"]
        if step.get("command"):
            suggestions.append(f"confirmar {step['command']}")
        else:
            suggestions.append(step["label"])
    return suggestions[:5]


def _first_command(commands: list[dict[str, str]], preferred: tuple[str, ...]) -> str | None:
    values = [command["command"] for command in commands]
    for command in preferred:
        if command in values:
            return command
    return values[0] if values else None
