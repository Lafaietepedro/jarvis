import subprocess
from typing import Any

from .base import BaseSkill, SkillResult
from ..permissions import PermissionPolicy


class ShellSkill(BaseSkill):
    name = "shell"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") == "run_command"

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        command = (intent.get("command") or "").strip()
        if not command:
            return SkillResult(
                response="Qual comando voce quer que eu rode?",
                action={"skill": self.name, "name": "run_command", "status": "needs_command"},
            )

        policy = options.get("permission_policy") or PermissionPolicy()
        decision = policy.evaluate(self.name, "run_command", {"command": command}, options)

        if decision.reason == "dangerous_command":
            return SkillResult(
                response="Esse comando parece destrutivo. Vou precisar de uma confirmação explícita e uma política mais forte antes de executar.",
                action={
                    "skill": self.name,
                    "name": "run_command",
                    "status": decision.status,
                    "reason": decision.reason,
                    "command": command,
                },
            )

        if decision.requires_confirmation:
            return SkillResult(
                response=f"Posso rodar `{command}`, mas preciso da sua confirmação.",
                action={
                    "skill": self.name,
                    "name": "run_command",
                    "status": decision.status,
                    "reason": decision.reason,
                    "command": command,
                },
            )

        if not decision.allowed:
            return SkillResult(
                response=f"Comando confirmado, mas execução de shell está desativada. Eu rodaria `{command}`.",
                action={
                    "skill": self.name,
                    "name": "run_command",
                    "status": decision.status,
                    "reason": decision.reason,
                    "command": command,
                },
            )

        completed = subprocess.run(
            command,
            cwd=context["project"]["path"],
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = (completed.stdout or completed.stderr or "").strip()
        preview = output[:1200]

        return SkillResult(
            response=f"Comando finalizado com codigo {completed.returncode}.",
            action={
                "skill": self.name,
                "name": "run_command",
                "status": "done" if completed.returncode == 0 else "failed",
                "command": command,
                "returncode": completed.returncode,
            },
            data={"output": preview, "truncated": len(output) > len(preview)},
        )
