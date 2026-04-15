import shutil
import subprocess
from typing import Any

from .base import BaseSkill, SkillResult
from ..permissions import PermissionPolicy


VOLUME_STEP = "5%"


class MediaSkill(BaseSkill):
    name = "media"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") == "media_control"

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        media_action = intent.get("media_action")
        if media_action == "status":
            return self._status()

        command = self._command_for(media_action)
        if command is None:
            return SkillResult(
                response="Ainda não sei qual ação de mídia executar.",
                action={"skill": self.name, "name": "control", "status": "needs_action"},
            )

        policy = options.get("permission_policy") or PermissionPolicy()
        decision = policy.evaluate(self.name, "control", {"media_action": media_action}, options)
        if not decision.allowed:
            return SkillResult(
                response="Eu alteraria a mídia ou o volume, mas ações de mídia estão desativadas por segurança.",
                action={
                    "skill": self.name,
                    "name": "control",
                    "status": decision.status,
                    "reason": decision.reason,
                    "media_action": media_action,
                },
                suggestions=["ativar JARVIS_ENABLE_MEDIA_ACTIONS se quiser permitir controle de mídia"],
            )

        missing = self._missing_binary(command)
        if missing:
            return SkillResult(
                response=f"Não encontrei `{missing}` neste sistema para controlar mídia.",
                action={
                    "skill": self.name,
                    "name": "control",
                    "status": "unavailable",
                    "reason": "missing_binary",
                    "binary": missing,
                    "media_action": media_action,
                },
            )

        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=5)
        status = "done" if completed.returncode == 0 else "failed"
        return SkillResult(
            response=self._response_for(media_action, status),
            action={
                "skill": self.name,
                "name": "control",
                "status": status,
                "media_action": media_action,
                "returncode": completed.returncode,
            },
            data={"stderr": completed.stderr.strip()[:500]},
        )

    def _status(self) -> SkillResult:
        data = {
            "volume": self._run_query(["pactl", "get-sink-volume", "@DEFAULT_SINK@"]),
            "mute": self._run_query(["pactl", "get-sink-mute", "@DEFAULT_SINK@"]),
            "player": self._run_query(["playerctl", "status"]),
        }
        available = any(item["available"] for item in data.values())
        response = "Status de mídia consultado." if available else "Não encontrei controles de mídia disponíveis neste sistema."
        return SkillResult(
            response=response,
            action={"skill": self.name, "name": "status", "status": "done" if available else "unavailable"},
            data=data,
        )

    def _run_query(self, command: list[str]) -> dict[str, Any]:
        binary = command[0]
        if shutil.which(binary) is None:
            return {"available": False, "reason": "missing_binary", "binary": binary}
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=5)
        return {
            "available": completed.returncode == 0,
            "returncode": completed.returncode,
            "output": completed.stdout.strip()[:500],
            "error": completed.stderr.strip()[:500],
        }

    def _command_for(self, media_action: str | None) -> list[str] | None:
        commands = {
            "volume_up": ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"+{VOLUME_STEP}"],
            "volume_down": ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"-{VOLUME_STEP}"],
            "mute": ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"],
            "unmute": ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"],
            "play_pause": ["playerctl", "play-pause"],
            "play": ["playerctl", "play"],
            "pause": ["playerctl", "pause"],
            "next": ["playerctl", "next"],
            "previous": ["playerctl", "previous"],
        }
        return commands.get(media_action or "")

    def _missing_binary(self, command: list[str]) -> str | None:
        binary = command[0]
        return binary if shutil.which(binary) is None else None

    def _response_for(self, media_action: str | None, status: str) -> str:
        if status != "done":
            return "Não consegui executar a ação de mídia."
        responses = {
            "volume_up": "Aumentei o volume.",
            "volume_down": "Diminuí o volume.",
            "mute": "Áudio silenciado.",
            "unmute": "Áudio reativado.",
            "play_pause": "Alternando reprodução.",
            "play": "Reprodução iniciada.",
            "pause": "Reprodução pausada.",
            "next": "Avançando faixa.",
            "previous": "Voltando faixa.",
        }
        return responses.get(media_action or "", "Ação de mídia executada.")
