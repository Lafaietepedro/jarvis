from pathlib import Path
from typing import Any

from .base import BaseSkill, SkillResult


class FileSkill(BaseSkill):
    name = "files"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") in {"list_files", "where_am_i"}

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        project_path = Path(context["project"]["path"])

        if intent.get("intent") == "where_am_i":
            return SkillResult(
                response=f"Estou trabalhando em {project_path}.",
                action={"skill": self.name, "name": "pwd", "status": "done", "path": str(project_path)},
                data={"path": str(project_path)},
            )

        entries = sorted(project_path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
        visible_entries = [entry.name + ("/" if entry.is_dir() else "") for entry in entries if not entry.name.startswith(".")]
        preview = visible_entries[:20]
        suffix = "" if len(visible_entries) <= 20 else f" e mais {len(visible_entries) - 20}"
        readable = ", ".join(preview) if preview else "nenhum arquivo visivel"

        return SkillResult(
            response=f"Encontrei {readable}{suffix}.",
            action={"skill": self.name, "name": "list_files", "status": "done", "path": str(project_path)},
            data={"path": str(project_path), "entries": preview, "total": len(visible_entries)},
        )
