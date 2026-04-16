import logging
from typing import Any

from .context import LocalContextProvider
from .memory import MemoryStore
from .nlu import parse_intent
from .permissions import PermissionPolicy
from .session import SessionState
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
        skill = self._select_skill(intent)

        if skill is None:
            result = SkillResult(
                response="Ainda não entendi como executar isso. Posso listar arquivos, checar status, abrir apps conhecidos ou preparar comandos de shell.",
                action={"skill": "core", "name": "fallback", "status": "unknown_intent"},
            )
        else:
            result = skill.handle(intent, context, options)

        suggestions = result.suggestions or build_suggestions(intent, context, result.action)
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

        skip_memory_record = result.action.get("skill") == "memory" and result.action.get("name") == "clear_history" and result.action.get("status") == "done"
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

    def _select_skill(self, intent: dict[str, Any]):
        for skill in self.skills:
            if skill.can_handle(intent):
                return skill
        return None
