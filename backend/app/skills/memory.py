from typing import Any

from .base import BaseSkill, SkillResult


class MemorySkill(BaseSkill):
    name = "memory"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") in {"command_history", "export_history", "clear_history"}

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        memory_store = options.get("memory_store")
        if memory_store is None:
            return SkillResult(
                response="A memoria local ainda nao esta disponivel nesta sessao.",
                action={"skill": self.name, "name": "command_history", "status": "unavailable"},
            )

        if intent.get("intent") == "export_history":
            exported = memory_store.export_history()
            return SkillResult(
                response=f"Histórico exportado com {len(exported['commands'])} comandos.",
                action={"skill": self.name, "name": "export_history", "status": "done"},
                data=exported,
            )

        if intent.get("intent") == "clear_history":
            if not options.get("confirm_actions"):
                return SkillResult(
                    response="Posso limpar o histórico local, mas preciso de confirmação explícita.",
                    action={
                        "skill": self.name,
                        "name": "clear_history",
                        "status": "needs_confirmation",
                        "reason": "confirmation_required",
                    },
                    suggestions=["confirmar limpeza do historico", "exportar historico antes de limpar"],
                )

            deleted = memory_store.clear_history()
            return SkillResult(
                response=f"Histórico local limpo. Removi {deleted} comandos.",
                action={"skill": self.name, "name": "clear_history", "status": "done", "deleted": deleted},
                suggestions=["painel de privacidade"],
                data={"deleted": deleted},
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
