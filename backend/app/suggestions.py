from typing import Any

from .proactive import build_proactive_suggestions


def build_suggestions(
    intent: dict[str, Any],
    context: dict[str, Any],
    action: dict[str, Any],
    base_suggestions: list[str] | None = None,
    history: list[dict[str, Any]] | None = None,
    project_state: dict[str, Any] | None = None,
) -> list[str]:
    suggestions = list(base_suggestions or [])
    project = context["project"]
    capabilities = project["capabilities"]

    if action.get("status") == "needs_confirmation":
        suggestions.append("confirmar a execucao")

    if action.get("status") == "blocked" and action.get("reason") == "shell_disabled":
        suggestions.append("ativar execucao de shell somente se confiar no comando")

    suggestions.extend(
        item["command"]
        for item in build_proactive_suggestions(
            context,
            history=history,
            project_state=project_state,
        )
    )

    if intent.get("intent") in {"status", "unknown", "none"}:
        suggestions.append("listar arquivos do projeto")
        suggestions.append("analisar projeto")

    if capabilities["has_makefile"]:
        suggestions.append("rodar make test")
        suggestions.append("comandos do projeto")

    if "README.md" in project.get("markers", []):
        suggestions.append("ler arquivo README.md")

    if capabilities["has_docker_compose"]:
        suggestions.append("subir ambiente com docker compose")

    if capabilities["has_python"]:
        suggestions.append("verificar testes do backend")

    suggestions.append("ver ultimos comandos")
    suggestions.append("pesquisar documentacao do projeto")
    suggestions.append("explicar o que voce pode controlar neste computador")
    return _unique(suggestions)[:5]


def _unique(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
