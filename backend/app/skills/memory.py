from typing import Any

from .base import BaseSkill, SkillResult


class MemorySkill(BaseSkill):
    name = "memory"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") in {
            "command_history",
            "export_history",
            "clear_history",
            "delete_memory",
            "memory_audit",
        }

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

        if intent.get("intent") == "memory_audit":
            audit = memory_store.audit_summary()
            return SkillResult(
                response=f"Auditoria local pronta: {audit['matching_count']} comando(s) encontrados.",
                action={"skill": self.name, "name": "memory_audit", "status": "done"},
                suggestions=["exportar historico", "limpar historico"],
                data={"audit": audit},
            )

        if intent.get("intent") == "delete_memory":
            command_id = intent.get("command_id")
            if not command_id:
                return SkillResult(
                    response="Diga qual id de comando devo esquecer, por exemplo: apagar comando 3.",
                    action={
                        "skill": self.name,
                        "name": "delete_memory",
                        "status": "needs_selector",
                        "reason": "missing_command_id",
                    },
                    suggestions=["resumo da memoria", "ultimos comandos"],
                )
            if not options.get("confirm_actions"):
                return SkillResult(
                    response=f"Posso apagar o comando {command_id} da memoria local, mas preciso de confirmacao explicita.",
                    action={
                        "skill": self.name,
                        "name": "delete_memory",
                        "status": "needs_confirmation",
                        "reason": "confirmation_required",
                        "command_id": command_id,
                    },
                    suggestions=[f"confirmar apagar comando {command_id}", "resumo da memoria"],
                )

            deleted = memory_store.delete_commands(command_ids=[command_id])
            return SkillResult(
                response=f"Memoria local atualizada. Removi {deleted['deleted']} comando(s).",
                action={
                    "skill": self.name,
                    "name": "delete_memory",
                    "status": "done",
                    "deleted": deleted["deleted"],
                },
                suggestions=["resumo da memoria"],
                data={"deleted": deleted},
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
