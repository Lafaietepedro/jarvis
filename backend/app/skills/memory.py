from typing import Any

from .base import BaseSkill, SkillResult


class MemorySkill(BaseSkill):
    name = "memory"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") == "command_history"

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        memory_store = options.get("memory_store")
        if memory_store is None:
            return SkillResult(
                response="A memoria local ainda nao esta disponivel nesta sessao.",
                action={"skill": self.name, "name": "command_history", "status": "unavailable"},
            )

        commands = memory_store.recent_commands(limit=5)
        if not commands:
            return SkillResult(
                response="Ainda nao tenho comandos recentes registrados.",
                action={"skill": self.name, "name": "command_history", "status": "empty"},
                data={"commands": []},
            )

        readable = ", ".join(command["text"] for command in commands[:3])
        return SkillResult(
            response=f"Ultimos comandos registrados: {readable}.",
            action={"skill": self.name, "name": "command_history", "status": "done"},
            data={"commands": commands},
        )
