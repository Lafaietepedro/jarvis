import logging
from pathlib import Path
from typing import Any

from .context import LocalContextProvider
from .memory import MemoryStore
from .nlu import parse_intent
from .permissions import PermissionPolicy
from .risk import enrich_action
from .session import SessionState
from .skills.ide import detect_project_state
from .skills import (
    ComputerSkill,
    AutomationSkill,
    BrowserSkill,
    DevSkill,
    FileSkill,
    IDESkill,
    MediaSkill,
    MemorySkill,
    PrivacySkill,
    ShellSkill,
    SkillResult,
    SystemSkill,
)
from .suggestions import build_suggestions


class JarvisCore:
    def __init__(
        self,
        context_provider: LocalContextProvider | None = None,
        memory_store: MemoryStore | None = None,
        permission_policy: PermissionPolicy | None = None,
        session_state: SessionState | None = None,
    ):
        self.context_provider = context_provider or LocalContextProvider()
        context = self.context_provider.get_context()
        self.memory_store = memory_store or MemoryStore(project_path=context["project"]["path"])
        self.permission_policy = permission_policy or PermissionPolicy()
        self.session_state = session_state or SessionState()
        self.skills = [
            SystemSkill(),
            AutomationSkill(),
            DevSkill(),
            IDESkill(),
            FileSkill(),
            MemorySkill(),
            PrivacySkill(),
            MediaSkill(),
            BrowserSkill(),
            ComputerSkill(),
            ShellSkill(),
        ]

    def execute(self, text: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
        options = options or {}
        self.session_state.set_processing(current_task="command")
        logging.info("Texto recebido: %s", text)
        intent = parse_intent(text)
        logging.info("Intent parsed: %s", intent)

        context = self.context_provider.get_context()
        options = {
            **options,
            "memory_store": self.memory_store,
            "permission_policy": self.permission_policy,
            "session_state": self.session_state,
        }
        if intent.get("intent") == "multi_action":
            result = self._handle_multi_action(intent, context, options)
        else:
            result = self._handle_single_intent(intent, context, options)

        result.action = enrich_action(result.action, intent)
        history = self.memory_store.recent_commands(limit=5)
        project_state = detect_project_state(Path(context["project"]["path"]))
        suggestions = build_suggestions(
            intent,
            context,
            result.action,
            base_suggestions=result.suggestions,
            history=history,
            project_state=project_state,
        )
        response = {
            "text": text,
            "intent": intent,
            "response": result.response,
            "action": result.action,
            "suggestions": suggestions,
            "context": {
                "project": context["project"],
                "privacy": context["privacy"],
            },
            "data": result.data,
            "session": self.session_state.snapshot(),
        }

        skip_memory_record = (
            result.action.get("skill") == "memory"
            and result.action.get("name") in {"clear_history", "delete_memory"}
            and result.action.get("status") == "done"
        )
        if not skip_memory_record:
            self.memory_store.record_command(
                text=text,
                intent=intent,
                action=result.action,
                response=result.response,
                private=options.get("private", False),
            )

        if options.get("source") == "voice":
            self.session_state.set_listening()
        else:
            self.session_state.set_active()
        response["session"] = self.session_state.snapshot()
        return response

    def _handle_single_intent(
        self,
        intent: dict[str, Any],
        context: dict[str, Any],
        options: dict[str, Any],
    ) -> SkillResult:
        skill = self._select_skill(intent)
        if skill is None:
            result = SkillResult(
                response="Ainda não entendi como executar isso. Posso listar arquivos, checar status, abrir apps conhecidos ou preparar comandos de shell.",
                action={"skill": "core", "name": "fallback", "status": "unknown_intent"},
            )
        else:
            result = skill.handle(intent, context, options)
        result.action = enrich_action(result.action, intent)
        return result

    def _handle_multi_action(
        self,
        intent: dict[str, Any],
        context: dict[str, Any],
        options: dict[str, Any],
    ) -> SkillResult:
        steps = intent.get("steps", [])
        step_results = []
        suggestions: list[str] = []
        safe_options = {**options, "confirm_actions": False}
        session_state = options.get("session_state")

        for index, step in enumerate(steps, start=1):
            result = self._handle_single_intent(step, context, safe_options)
            suggestions.extend(result.suggestions)
            step_results.append(
                {
                    "index": index,
                    "intent": step,
                    "response": result.response,
                    "action": result.action,
                    "data": result.data,
                }
            )

        checkpoints = _checkpoints_from_multi_action(step_results)
        if checkpoints and session_state:
            checkpoints = session_state.add_automation_checkpoints("multi_action", checkpoints)
            suggestions.extend(f"confirmar checkpoint {checkpoint['checkpoint_id']}" for checkpoint in checkpoints)

        step_actions = [item["action"] for item in step_results]
        needs_confirmation = len([action for action in step_actions if action.get("status") == "needs_confirmation"])
        blocked = len([action for action in step_actions if action.get("status") == "blocked"])
        done = len([action for action in step_actions if action.get("status") == "done"])
        if needs_confirmation or blocked:
            status = "needs_review"
        else:
            status = "done"

        if status == "done":
            response = f"Executei {done} etapa(s) do pedido composto."
        else:
            response = (
                f"Preparei o pedido composto: {done} etapa(s) concluidas, "
                f"{needs_confirmation} aguardando confirmacao e {blocked} bloqueada(s)."
            )
        if checkpoints:
            response += f" Criei {len(checkpoints)} checkpoint(s) para as etapas sensiveis."

        if needs_confirmation:
            suggestions.append("confirmar a execucao")
        if blocked:
            suggestions.append("revisar permissoes")

        return SkillResult(
            response=response,
            action={
                "skill": "core",
                "name": "multi_action",
                "status": status,
                "steps": len(step_results),
                "done": done,
                "needs_confirmation": needs_confirmation,
                "blocked": blocked,
                "checkpoint_count": len(checkpoints),
                "checkpoint_ids": [checkpoint["checkpoint_id"] for checkpoint in checkpoints],
                "step_actions": step_actions,
            },
            suggestions=suggestions,
            data={"steps": step_results, "checkpoints": checkpoints},
        )

    def _select_skill(self, intent: dict[str, Any]):
        for skill in self.skills:
            if skill.can_handle(intent):
                return skill
        return None


def _checkpoints_from_multi_action(step_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checkpoints = []
    for result in step_results:
        checkpoint = _checkpoint_from_step_result(result)
        if checkpoint:
            checkpoints.append(checkpoint)
    return checkpoints


def _checkpoint_from_step_result(result: dict[str, Any]) -> dict[str, Any] | None:
    action = result.get("action", {})
    status = action.get("status")
    if status not in {"needs_confirmation", "blocked"}:
        return None

    step = result.get("intent", {})
    checkpoint_step = _checkpoint_step_for_action(action, step)
    if checkpoint_step is None:
        return None

    index = result.get("index", 0)
    reason = "confirmation_required" if status == "needs_confirmation" else "permission_required"
    return {
        "index": index,
        "label": f"Etapa {index}: {step.get('text') or action.get('command') or action.get('name')}",
        "status": "checkpoint",
        "reason": reason,
        "source": "multi_action",
        "step": checkpoint_step,
    }


def _checkpoint_step_for_action(action: dict[str, Any], step: dict[str, Any]) -> dict[str, Any] | None:
    if action.get("skill") == "shell" and action.get("name") == "run_command" and action.get("command"):
        return {
            "label": step.get("text") or action["command"],
            "intent": "run_command",
            "command": action["command"],
            "risk": action.get("risk", "medium"),
            "requires_confirmation": True,
            "permission": action.get("permission"),
        }

    if action.get("skill") == "ide" and action.get("name") == "open_project":
        return {
            "label": step.get("text") or "abrir projeto",
            "intent": "open_project",
            "risk": action.get("risk", "medium"),
            "requires_confirmation": action.get("requires_confirmation", False),
            "permission": action.get("permission"),
        }

    return None
