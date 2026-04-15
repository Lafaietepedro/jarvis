import subprocess
from typing import Any

from .base import BaseSkill, SkillResult
from ..permissions import PermissionPolicy


APP_ALIASES = {
    "arquivos": "xdg-open",
    "browser": "xdg-open",
    "chrome": "google-chrome",
    "codigo": "code",
    "code": "code",
    "firefox": "firefox",
    "navegador": "xdg-open",
    "terminal": "x-terminal-emulator",
    "vscode": "code",
}


class ComputerSkill(BaseSkill):
    name = "computer"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") == "open_app"

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        target = intent.get("target")
        command = APP_ALIASES.get(target or "")

        if not target or not command:
            return SkillResult(
                response="Ainda não sei qual aplicativo abrir.",
                action={"skill": self.name, "name": "open_app", "status": "needs_target"},
            )

        policy = options.get("permission_policy") or PermissionPolicy()
        decision = policy.evaluate(self.name, "open_app", {"target": target, "command": command}, options)
        if not decision.allowed:
            return SkillResult(
                response=f"Eu abriria {target}, mas ações de desktop estão desativadas por segurança.",
                action={
                    "skill": self.name,
                    "name": "open_app",
                    "status": decision.status,
                    "reason": decision.reason,
                    "target": target,
                    "command": command,
                },
            )

        try:
            args = [command]
            if command == "xdg-open":
                args.append(context["project"]["path"])
            subprocess.Popen(args)
        except Exception as exc:
            return SkillResult(
                response=f"Não consegui abrir {target}.",
                action={
                    "skill": self.name,
                    "name": "open_app",
                    "status": "failed",
                    "target": target,
                    "error": str(exc),
                },
            )

        return SkillResult(
            response=f"Abri {target}.",
            action={"skill": self.name, "name": "open_app", "status": "done", "target": target},
        )
