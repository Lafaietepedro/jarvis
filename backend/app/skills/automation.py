from pathlib import Path
from typing import Any

from ..diagnostics import collect_diagnostics
from .base import BaseSkill, SkillResult
from .ide import IDESkill, detect_project_commands
from .shell import ShellSkill


class AutomationSkill(BaseSkill):
    name = "automation"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") in {
            "automation_plan",
            "project_checkup",
            "execute_automation_plan",
            "execute_project_checkup",
            "confirm_checkpoint",
            "pending_checkpoints",
        }

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        if intent.get("intent") == "pending_checkpoints":
            return pending_checkpoints(options)

        if intent.get("intent") == "confirm_checkpoint":
            return confirm_checkpoint(intent, context, options)

        if intent.get("intent") == "execute_project_checkup":
            plan = build_project_checkup_plan(context)
            report = execute_plan(plan, context, options)
            _register_checkpoints(report, options)
            return SkillResult(
                response=_execution_response(report),
                action={"skill": self.name, "name": "execute_project_checkup", "status": report["status"]},
                suggestions=_checkpoint_suggestions(report),
                data=report,
            )

        if intent.get("intent") == "execute_automation_plan":
            plan = build_development_routine_plan(context)
            report = execute_plan(plan, context, options)
            _register_checkpoints(report, options)
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


def confirm_checkpoint(intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
    session_state = options.get("session_state")
    if session_state is None:
        return SkillResult(
            response="Nao encontrei uma sessao ativa com checkpoints pendentes.",
            action={
                "skill": "automation",
                "name": "confirm_checkpoint",
                "status": "empty",
                "reason": "missing_session_state",
            },
        )

    checkpoint = session_state.get_automation_checkpoint(intent.get("checkpoint_id"))
    if checkpoint is None:
        return SkillResult(
            response="Nao ha checkpoints pendentes para confirmar.",
            action={"skill": "automation", "name": "confirm_checkpoint", "status": "empty"},
        )

    result = _execute_confirmed_checkpoint(checkpoint, context, options)
    status = result.action.get("status", "done")
    if status not in {"blocked", "needs_confirmation"}:
        session_state.remove_automation_checkpoint(checkpoint["checkpoint_id"])

    return SkillResult(
        response=f"Checkpoint {checkpoint['checkpoint_id']}: {result.response}",
        action={
            "skill": "automation",
            "name": "confirm_checkpoint",
            "status": status,
            "checkpoint_id": checkpoint["checkpoint_id"],
            "delegated_action": result.action,
        },
        suggestions=result.suggestions,
        data={
            "checkpoint": checkpoint,
            "result": {
                "response": result.response,
                "action": result.action,
                "data": result.data,
            },
        },
    )


def pending_checkpoints(options: dict[str, Any]) -> SkillResult:
    session_state = options.get("session_state")
    checkpoints = []
    if session_state:
        checkpoints = session_state.snapshot().get("automation_checkpoints", [])

    if not checkpoints:
        return SkillResult(
            response="Nao ha checkpoints pendentes no momento.",
            action={"skill": "automation", "name": "pending_checkpoints", "status": "empty"},
            data={"checkpoints": []},
        )

    return SkillResult(
        response=f"Ha {len(checkpoints)} checkpoint(s) pendente(s).",
        action={"skill": "automation", "name": "pending_checkpoints", "status": "done"},
        suggestions=[f"confirmar checkpoint {checkpoint['checkpoint_id']}" for checkpoint in checkpoints[:5]],
        data={"checkpoints": checkpoints},
    )


def _requires_checkpoint(step: dict[str, Any]) -> bool:
    if step.get("requires_confirmation"):
        return True
    if step.get("risk") != "low":
        return True
    if step.get("permission"):
        return True
    return False


def _execute_confirmed_checkpoint(
    checkpoint: dict[str, Any],
    context: dict[str, Any],
    options: dict[str, Any],
) -> SkillResult:
    step = checkpoint["step"]
    step_intent = step.get("intent")
    if step_intent == "run_command":
        command = step.get("command")
        return ShellSkill().handle(
            {"intent": "run_command", "command": command, "text": command},
            context,
            {**options, "confirm_actions": True},
        )

    if step_intent == "open_project":
        return IDESkill().handle({"intent": "open_project", "text": step["label"]}, context, options)

    return SkillResult(
        response="Ainda nao tenho executor seguro para esse tipo de checkpoint.",
        action={
            "skill": "automation",
            "name": "confirm_checkpoint",
            "status": "blocked",
            "reason": "unsupported_checkpoint",
            "checkpoint_intent": step_intent,
        },
    )


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
        checkpoint_id = checkpoint.get("checkpoint_id", checkpoint["index"])
        step = checkpoint["step"]
        if step.get("command"):
            suggestions.append(f"confirmar checkpoint {checkpoint_id}")
        else:
            suggestions.append(f"confirmar checkpoint {checkpoint_id}")
    return suggestions[:5]


def _register_checkpoints(report: dict[str, Any], options: dict[str, Any]):
    checkpoints = [
        {
            **checkpoint,
            "checkpoint_id": index,
            "plan": report["name"],
        }
        for index, checkpoint in enumerate(report["checkpoints"], start=1)
    ]
    report["checkpoints"] = checkpoints
    report["results"] = [
        next(
            (
                checkpoint
                for checkpoint in checkpoints
                if result["status"] == "checkpoint" and checkpoint["index"] == result["index"]
            ),
            result,
        )
        for result in report["results"]
    ]

    session_state = options.get("session_state")
    if session_state:
        session_state.set_automation_checkpoints(report["name"], checkpoints)


def _first_command(commands: list[dict[str, str]], preferred: tuple[str, ...]) -> str | None:
    values = [command["command"] for command in commands]
    for command in preferred:
        if command in values:
            return command
    return values[0] if values else None
