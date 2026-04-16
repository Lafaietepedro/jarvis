import os
import re
from dataclasses import dataclass


DANGEROUS_COMMAND_PATTERNS = (
    r"\brm\s+-rf\b",
    r"\bsudo\b",
    r"\bmkfs\b",
    r"\bdd\s+",
    r">\s*/dev/",
    r"\bshutdown\b",
    r"\breboot\b",
)


@dataclass
class PermissionDecision:
    allowed: bool
    status: str
    reason: str | None = None
    requires_confirmation: bool = False


class PermissionPolicy:
    def evaluate(self, skill: str, action: str, payload: dict, options: dict) -> PermissionDecision:
        if skill == "shell" and action == "run_command":
            return self._evaluate_shell(payload.get("command") or "", options)

        if skill == "computer" and action == "open_app":
            return self._evaluate_desktop_action()

        if skill == "media" and action == "control":
            return self._evaluate_media_action()

        if skill == "browser" and action in {"open_url", "search"}:
            return self._evaluate_browser_action()

        if skill == "ide" and action == "open_project":
            return self._evaluate_ide_action()

        return PermissionDecision(allowed=True, status="allowed")

    def _evaluate_shell(self, command: str, options: dict) -> PermissionDecision:
        if any(re.search(pattern, command) for pattern in DANGEROUS_COMMAND_PATTERNS):
            return PermissionDecision(allowed=False, status="blocked", reason="dangerous_command")

        if not options.get("confirm_actions"):
            return PermissionDecision(
                allowed=False,
                status="needs_confirmation",
                reason="confirmation_required",
                requires_confirmation=True,
            )

        if os.environ.get("JARVIS_ENABLE_SHELL") != "1":
            return PermissionDecision(allowed=False, status="blocked", reason="shell_disabled")

        return PermissionDecision(allowed=True, status="allowed")

    def _evaluate_desktop_action(self) -> PermissionDecision:
        if os.environ.get("JARVIS_ENABLE_DESKTOP_ACTIONS") != "1":
            return PermissionDecision(allowed=False, status="blocked", reason="desktop_actions_disabled")

        return PermissionDecision(allowed=True, status="allowed")

    def _evaluate_media_action(self) -> PermissionDecision:
        if os.environ.get("JARVIS_ENABLE_MEDIA_ACTIONS") != "1":
            return PermissionDecision(allowed=False, status="blocked", reason="media_actions_disabled")

        return PermissionDecision(allowed=True, status="allowed")

    def _evaluate_browser_action(self) -> PermissionDecision:
        if os.environ.get("JARVIS_ENABLE_BROWSER_ACTIONS") != "1":
            return PermissionDecision(allowed=False, status="blocked", reason="browser_actions_disabled")

        return PermissionDecision(allowed=True, status="allowed")

    def _evaluate_ide_action(self) -> PermissionDecision:
        if os.environ.get("JARVIS_ENABLE_IDE_ACTIONS") != "1":
            return PermissionDecision(allowed=False, status="blocked", reason="ide_actions_disabled")

        return PermissionDecision(allowed=True, status="allowed")
