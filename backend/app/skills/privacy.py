from typing import Any

from .base import BaseSkill, SkillResult


class PrivacySkill(BaseSkill):
    name = "privacy"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") == "privacy_panel"

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        memory_store = options.get("memory_store")
        session_state = options.get("session_state")
        memory = memory_store.stats() if memory_store else {"enabled": False}
        session = session_state.snapshot() if session_state else {}
        permissions = {
            "cloud_enabled": context["privacy"]["cloud_enabled"],
            "browser_actions_enabled": context["privacy"].get("browser_actions_enabled", False),
            "desktop_actions_enabled": context["privacy"]["desktop_actions_enabled"],
            "ide_actions_enabled": context["privacy"].get("ide_actions_enabled", False),
            "shell_enabled": context["privacy"]["shell_enabled"],
            "media_actions_enabled": context["privacy"].get("media_actions_enabled", False),
        }

        return SkillResult(
            response=(
                "Painel de privacidade pronto. Nuvem desligada por padrão, áudio não é persistido, "
                "e ações sensíveis seguem a política de permissões."
            ),
            action={"skill": self.name, "name": "privacy_panel", "status": "done"},
            suggestions=[
                "ver ultimos comandos",
                "pausar o JARVIS",
                "explicar o que voce pode controlar neste computador",
            ],
            data={
                "privacy": context["privacy"],
                "permissions": permissions,
                "memory": memory,
                "session": session,
            },
        )
