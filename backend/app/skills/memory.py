from typing import Any

from app.nlu import parse_intent

from .base import BaseSkill, SkillResult
from .files import FileSkill


class MemorySkill(BaseSkill):
    name = "memory"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") in {
            "command_history",
            "export_history",
            "clear_history",
            "delete_memory",
            "memory_audit",
            "revert_file_edit",
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

        if intent.get("intent") == "revert_file_edit":
            source_command = _resolve_revert_source(memory_store, intent)
            if source_command is None:
                return SkillResult(
                    response="Nao encontrei uma edicao auditada para reverter agora.",
                    action={
                        "skill": self.name,
                        "name": "revert_file_edit",
                        "status": "not_found",
                        "reason": "edit_history_not_found",
                    },
                    suggestions=["ultimos comandos", "resumo da memoria"],
                )

            audit = _edit_audit_from_command(source_command)
            revert_command = (audit or {}).get("revert_command")
            if not revert_command:
                return SkillResult(
                    response="Encontrei a edicao, mas ainda nao consigo montar uma reversao segura para esse caso.",
                    action={
                        "skill": self.name,
                        "name": "revert_file_edit",
                        "status": "blocked",
                        "reason": "revert_not_supported",
                        "command_id": source_command.get("id"),
                    },
                    suggestions=["ler arquivo " + (audit or {}).get("path", "")] if (audit or {}).get("path") else [],
                    data={"source_command": source_command, "edit_audit": audit},
                )

            file_result = FileSkill().handle(parse_intent(revert_command), context, options)
            file_result.response = (
                f"Preparei a reversao da edicao registrada no comando {source_command['id']}. "
                f"{file_result.response}"
            )
            file_result.action["revert_source_command_id"] = source_command["id"]
            if audit:
                file_result.action["revert_source_summary"] = audit.get("summary")
            file_result.data = {
                **file_result.data,
                "revert_source_command_id": source_command["id"],
                "revert_source_text": source_command.get("text"),
                "revert_command": revert_command,
                "source_command": source_command,
                "edit_audit": audit,
            }
            return file_result

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


def _resolve_revert_source(memory_store: Any, intent: dict[str, Any]) -> dict[str, Any] | None:
    command_id = intent.get("command_id")
    if command_id:
        command = memory_store.command_by_id(command_id)
        if _edit_audit_from_command(command):
            return command
        return None

    if intent.get("selector") == "latest":
        return memory_store.latest_edit_command()

    return memory_store.latest_edit_command()


def _edit_audit_from_command(command: dict[str, Any] | None) -> dict[str, Any] | None:
    if not command:
        return None
    action = command.get("action", {})
    edit_audit = action.get("edit_audit")
    if isinstance(edit_audit, dict):
        return edit_audit
    delegated = action.get("delegated_action")
    if isinstance(delegated, dict):
        delegated_audit = delegated.get("edit_audit")
        if isinstance(delegated_audit, dict):
            return delegated_audit
    return None
