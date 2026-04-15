from typing import Any


def build_greeting(context: dict[str, Any], mode: str = "text", status: str = "active") -> str:
    project_name = context["project"]["name"]
    if status == "paused":
        return f"JARVIS pausado. Contexto local preservado para o projeto {project_name}."
    if status == "processing":
        return f"JARVIS processando. Contexto local carregado para o projeto {project_name}."
    if mode == "voice":
        return f"JARVIS ativo. Estou ouvindo e trabalhando no projeto {project_name}."
    return f"JARVIS ativo. Contexto local carregado para o projeto {project_name}."


def build_presence(
    context: dict[str, Any],
    session: dict[str, Any],
    mode: str = "text",
) -> dict[str, Any]:
    return {
        "status": session["status"],
        "name": "JARVIS",
        "mode": mode,
        "greeting": build_greeting(context, mode=mode, status=session["status"]),
        "voice_listening": session["voice_listening"],
        "uptime_seconds": session["uptime_seconds"],
        "started_at": session["started_at"],
        "last_activity_at": session["last_activity_at"],
        "current_task": session["current_task"],
        "privacy": context["privacy"],
        "project": context["project"],
        "suggestions": [
            "qual o status",
            "listar arquivos",
            "o que voce pode controlar neste computador",
        ],
    }
