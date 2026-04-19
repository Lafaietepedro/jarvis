import re
from dataclasses import dataclass
from typing import Any

from .permissions import DANGEROUS_COMMAND_PATTERNS


RISK_LEVELS = {"low": 1, "medium": 2, "high": 3}

DISABLED_REASON_PERMISSIONS = {
    "shell_disabled": "JARVIS_ENABLE_SHELL",
    "desktop_actions_disabled": "JARVIS_ENABLE_DESKTOP_ACTIONS",
    "browser_actions_disabled": "JARVIS_ENABLE_BROWSER_ACTIONS",
    "ide_actions_disabled": "JARVIS_ENABLE_IDE_ACTIONS",
    "media_actions_disabled": "JARVIS_ENABLE_MEDIA_ACTIONS",
}

CAPABILITY_ACTIONS = {
    "shell.run_command": {
        "skill": "shell",
        "name": "run_command",
        "risk": "high",
        "requires_confirmation": True,
        "permission": "JARVIS_ENABLE_SHELL",
        "reason": "shell_execution",
        "category": "execution",
        "description": "Executa comandos no sistema local.",
    },
    "ide.open_project": {
        "skill": "ide",
        "name": "open_project",
        "risk": "medium",
        "permission": "JARVIS_ENABLE_IDE_ACTIONS",
        "reason": "app_launch",
        "category": "application",
        "description": "Abre o projeto em uma IDE local.",
    },
    "browser.open_url": {
        "skill": "browser",
        "name": "open_url",
        "risk": "medium",
        "permission": "JARVIS_ENABLE_BROWSER_ACTIONS",
        "reason": "external_app",
        "category": "browser",
        "description": "Abre uma URL ou pesquisa no navegador local.",
    },
    "media.control": {
        "skill": "media",
        "name": "control",
        "risk": "medium",
        "permission": "JARVIS_ENABLE_MEDIA_ACTIONS",
        "reason": "local_state_change",
        "category": "media",
        "description": "Altera volume ou reproducao de midia.",
    },
    "desktop.open_app": {
        "skill": "computer",
        "name": "open_app",
        "risk": "medium",
        "permission": "JARVIS_ENABLE_DESKTOP_ACTIONS",
        "reason": "app_launch",
        "category": "application",
        "description": "Abre aplicativos conhecidos no desktop.",
    },
}


READ_ONLY_ACTIONS = {
    ("system", "status"),
    ("system", "capabilities"),
    ("system", "diagnostics"),
    ("system", "dependency_check"),
    ("system", "install_dependencies"),
    ("files", "pwd"),
    ("files", "list_files"),
    ("ide", "project_commands"),
    ("ide", "project_state"),
    ("memory", "command_history"),
    ("memory", "export_history"),
    ("memory", "memory_audit"),
    ("privacy", "privacy_panel"),
    ("media", "status"),
    ("automation", "automation_plan"),
    ("automation", "project_checkup"),
    ("automation", "pending_checkpoints"),
    ("dev", "project_status"),
    ("dev", "prepare_project"),
    ("core", "fallback"),
}


@dataclass(frozen=True)
class ActionRiskProfile:
    risk: str
    requires_confirmation: bool
    permission: str | None
    reason: str
    category: str
    description: str
    severity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk": self.risk,
            "requires_confirmation": self.requires_confirmation,
            "permission": self.permission,
            "risk_reason": self.reason,
            "risk_category": self.category,
            "risk_description": self.description,
            "severity": self.severity,
        }


def classify_action(action: dict[str, Any] | None, intent: dict[str, Any] | None = None) -> ActionRiskProfile:
    action = action or {}
    skill = action.get("skill")
    name = action.get("name")
    reason = action.get("reason")

    if reason and reason != "confirmation_required":
        reason_profile = _profile_for_reason(reason, action)
        if reason_profile:
            return _with_status_confirmation(reason_profile, action)

    if skill == "shell" and name == "run_command":
        return _shell_profile(action.get("command"))

    if skill == "memory" and name in {"clear_history", "delete_memory"}:
        return _profile(
            "high",
            True,
            None,
            "memory_deletion",
            "memory",
            "Remove dados da memoria local do usuario.",
        )

    if skill == "automation" and name == "confirm_checkpoint":
        delegated = action.get("delegated_action")
        if isinstance(delegated, dict):
            return classify_action(delegated, intent)
        return _profile("medium", True, None, "checkpoint_confirmation", "automation", "Confirma uma acao pendente.")

    if skill == "core" and name == "multi_action":
        step_actions = [item for item in action.get("step_actions", []) if isinstance(item, dict)]
        if step_actions:
            return _aggregate_profiles([classify_action(step_action) for step_action in step_actions])
        return _profile("low", False, None, "multi_action", "automation", "Pedido composto sem acoes sensiveis.")

    if (skill, name) in READ_ONLY_ACTIONS:
        return _profile("low", False, None, "read_only", "read", "Consulta informacoes locais sem alterar o sistema.")

    capability_id = _capability_id_for_action(skill, name)
    if capability_id:
        return classify_capability(capability_id)

    if intent:
        return classify_intent(intent)

    if reason:
        reason_profile = _profile_for_reason(reason, action)
        if reason_profile:
            return _with_status_confirmation(reason_profile, action)

    if action.get("requires_confirmation"):
        return _profile("medium", True, action.get("permission"), "confirmation_required", "review", "Acao requer revisao.")

    return _profile("low", False, action.get("permission"), "unspecified", "general", "Acao sem risco especial conhecido.")


def classify_intent(intent: dict[str, Any] | None) -> ActionRiskProfile:
    intent = intent or {}
    name = intent.get("intent")
    if name == "run_command":
        return _shell_profile(intent.get("command"))
    if name == "open_project":
        return classify_capability("ide.open_project")
    if name in {"open_url", "web_search"}:
        return classify_capability("browser.open_url")
    if name == "open_app":
        return classify_capability("desktop.open_app")
    if name == "media_control" and intent.get("media_action") != "status":
        return classify_capability("media.control")
    if name in {"clear_history", "delete_memory"}:
        return _profile("high", True, None, "memory_deletion", "memory", "Remove dados da memoria local do usuario.")
    if name == "confirm_checkpoint":
        return _profile("medium", True, None, "checkpoint_confirmation", "automation", "Confirma uma acao pendente.")
    return _profile("low", False, None, "read_only", "read", "Consulta ou planejamento sem execucao sensivel.")


def classify_checkpoint(checkpoint: dict[str, Any]) -> ActionRiskProfile:
    reason = checkpoint.get("reason")
    step = checkpoint.get("step") or checkpoint
    step_profile = classify_step(step)
    if reason == "confirmation_required":
        return _profile(
            _max_risk("medium", step_profile.risk),
            True,
            step_profile.permission,
            reason,
            step_profile.category,
            "Acao aguarda confirmacao explicita do usuario.",
        )
    if reason:
        reason_profile = _profile_for_reason(reason, checkpoint)
        if reason_profile:
            return reason_profile
    return step_profile


def classify_step(step: dict[str, Any]) -> ActionRiskProfile:
    intent = step.get("intent")
    if intent == "run_command" or (not intent and step.get("command")):
        return _shell_profile(step.get("command"))
    if intent == "open_project":
        return classify_capability("ide.open_project")
    if intent in {"open_url", "web_search"}:
        return classify_capability("browser.open_url")
    if intent == "media_control":
        return classify_capability("media.control")
    if intent in {"clear_history", "delete_memory"}:
        return _profile("high", True, None, "memory_deletion", "memory", "Remove dados da memoria local do usuario.")

    risk = step.get("risk")
    if risk and risk != "low":
        return _profile(
            _normalize_risk(risk),
            bool(step.get("requires_confirmation")),
            step.get("permission"),
            "step_policy",
            "automation",
            "Passo de automacao marcado como sensivel.",
        )
    return _profile("low", bool(step.get("requires_confirmation")), step.get("permission"), "read_only", "read", "Passo seguro.")


def classify_capability(capability_id: str, enabled: bool | None = None) -> ActionRiskProfile:
    metadata = CAPABILITY_ACTIONS.get(capability_id)
    if not metadata:
        return _profile("low", False, None, "capability", "general", "Capacidade local.")

    reason = metadata["reason"] if enabled is not False else "permission_required"
    return _profile(
        metadata["risk"],
        bool(metadata.get("requires_confirmation", False)),
        metadata.get("permission"),
        reason,
        metadata["category"],
        metadata["description"],
    )


def classify_command_text(command: str) -> ActionRiskProfile:
    normalized = _normalize(command)
    if not normalized:
        return _profile("low", False, None, "empty_command", "general", "Comando vazio.")

    if normalized.startswith(("rodar ", "rode ", "executar ", "execute ", "run ")):
        shell_command = re.sub(r"^(rodar|rode|executar|execute|run)\s+", "", normalized, count=1)
        return _shell_profile(shell_command)

    if normalized.startswith(("abrir site ", "abrir url ", "abrir link ", "pesquisar ", "pesquise ", "buscar ")):
        return classify_capability("browser.open_url")

    if normalized.startswith(("abrir projeto", "abrir vscode", "abrir workspace")):
        return classify_capability("ide.open_project")

    if normalized.startswith(("abrir ", "abra ", "iniciar ", "start ", "open ")):
        return classify_capability("desktop.open_app")

    if any(term in normalized for term in ("aumentar volume", "diminuir volume", "mutar", "silenciar", "proxima musica")):
        return classify_capability("media.control")

    if any(term in normalized for term in ("limpar historico", "apagar historico", "apagar comando", "remover comando")):
        return _profile("high", True, None, "memory_deletion", "memory", "Remove dados da memoria local do usuario.")

    return _profile("low", False, None, "suggested_read", "read", "Sugestao sem execucao sensivel detectada.")


def enrich_action(action: dict[str, Any], intent: dict[str, Any] | None = None) -> dict[str, Any]:
    profile = classify_action(action, intent)
    return apply_profile(action, profile)


def apply_profile(action: dict[str, Any], profile: ActionRiskProfile) -> dict[str, Any]:
    enriched = dict(action)
    enriched["risk"] = profile.risk
    enriched["requires_confirmation"] = profile.requires_confirmation
    enriched["permission"] = profile.permission
    enriched["risk_reason"] = profile.reason
    enriched["risk_category"] = profile.category
    enriched["risk_description"] = profile.description
    return enriched


def permission_for_reason(reason: str | None) -> str | None:
    if reason in DISABLED_REASON_PERMISSIONS:
        return DISABLED_REASON_PERMISSIONS[reason]
    if reason == "permission_required":
        return "explicit_permission"
    return None


def severity_for_event(status: str, reason: str | None) -> str:
    if status == "blocked":
        return "blocked"
    if reason:
        profile = _profile_for_reason(reason, {})
        return profile.severity if profile else "review"
    return "info"


def _profile_for_reason(reason: str, action: dict[str, Any]) -> ActionRiskProfile | None:
    if reason == "dangerous_command":
        return _profile(
            "high",
            True,
            "JARVIS_ENABLE_SHELL",
            reason,
            "execution",
            "Comando com padrao destrutivo ou privilegiado.",
        )
    if reason == "shell_disabled":
        return _profile("high", True, "JARVIS_ENABLE_SHELL", reason, "execution", "Shell local esta desativado.")
    if reason in {"desktop_actions_disabled", "browser_actions_disabled", "ide_actions_disabled", "media_actions_disabled"}:
        return _profile(
            "medium",
            bool(action.get("requires_confirmation", False)),
            permission_for_reason(reason),
            reason,
            "permission",
            "Acao local bloqueada por configuracao de permissao.",
        )
    if reason == "confirmation_required":
        return _profile(
            _normalize_risk(action.get("risk", "medium")),
            True,
            action.get("permission"),
            reason,
            "review",
            "Acao aguarda confirmacao explicita do usuario.",
        )
    if reason in {"permission_required", "risk_or_permission"}:
        return _profile(
            _normalize_risk(action.get("risk", "high")),
            bool(action.get("requires_confirmation", True)),
            permission_for_reason(reason) or action.get("permission"),
            reason,
            "permission",
            "Acao depende de permissao ou revisao antes da execucao.",
        )
    return None


def _shell_profile(command: str | None) -> ActionRiskProfile:
    if _is_dangerous_command(command or ""):
        return _profile(
            "high",
            True,
            "JARVIS_ENABLE_SHELL",
            "dangerous_command",
            "execution",
            "Comando com padrao destrutivo ou privilegiado.",
        )
    return _profile(
        "medium",
        True,
        "JARVIS_ENABLE_SHELL",
        "shell_execution",
        "execution",
        "Executa comando no shell local.",
    )


def _is_dangerous_command(command: str) -> bool:
    return any(re.search(pattern, command) for pattern in DANGEROUS_COMMAND_PATTERNS)


def _capability_id_for_action(skill: str | None, name: str | None) -> str | None:
    if skill == "shell" and name == "run_command":
        return "shell.run_command"
    if skill == "ide" and name == "open_project":
        return "ide.open_project"
    if skill == "browser" and name in {"open_url", "search"}:
        return "browser.open_url"
    if skill == "media" and name == "control":
        return "media.control"
    if skill == "computer" and name == "open_app":
        return "desktop.open_app"
    return None


def _profile(
    risk: str,
    requires_confirmation: bool,
    permission: str | None,
    reason: str,
    category: str,
    description: str,
) -> ActionRiskProfile:
    risk = _normalize_risk(risk)
    return ActionRiskProfile(
        risk=risk,
        requires_confirmation=requires_confirmation,
        permission=permission,
        reason=reason,
        category=category,
        description=description,
        severity=_severity(risk, requires_confirmation, reason),
    )


def _with_status_confirmation(profile: ActionRiskProfile, action: dict[str, Any]) -> ActionRiskProfile:
    if action.get("status") == "needs_confirmation" and not profile.requires_confirmation:
        return _profile(
            profile.risk,
            True,
            profile.permission,
            profile.reason,
            profile.category,
            profile.description,
        )
    return profile


def _aggregate_profiles(profiles: list[ActionRiskProfile]) -> ActionRiskProfile:
    if not profiles:
        return _profile("low", False, None, "multi_action", "automation", "Pedido composto sem acoes sensiveis.")

    highest = profiles[0]
    for profile in profiles[1:]:
        if RISK_LEVELS[profile.risk] > RISK_LEVELS[highest.risk]:
            highest = profile

    permission = next((profile.permission for profile in profiles if profile.permission), None)
    requires_confirmation = any(profile.requires_confirmation for profile in profiles)
    return _profile(
        highest.risk,
        requires_confirmation,
        permission,
        "multi_action",
        "automation",
        "Pedido composto classificado pelo maior risco entre as etapas.",
    )


def _severity(risk: str, requires_confirmation: bool, reason: str) -> str:
    if reason in {"shell_disabled", "dangerous_command", "risk_or_permission", "permission_required"}:
        return "blocked"
    if reason.endswith("_disabled"):
        return "blocked"
    if requires_confirmation or RISK_LEVELS.get(risk, 1) >= RISK_LEVELS["medium"]:
        return "review"
    return "info"


def _normalize_risk(risk: Any) -> str:
    value = str(risk or "low").lower()
    return value if value in RISK_LEVELS else "low"


def _max_risk(first: str, second: str) -> str:
    first = _normalize_risk(first)
    second = _normalize_risk(second)
    return first if RISK_LEVELS[first] >= RISK_LEVELS[second] else second


def _normalize(command: str) -> str:
    return re.sub(r"\s+", " ", command.lower()).strip()
