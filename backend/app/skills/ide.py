import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ..permissions import PermissionPolicy
from .base import BaseSkill, SkillResult


class IDESkill(BaseSkill):
    name = "ide"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") in {"open_project", "project_commands", "project_state"}

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        project_path = Path(context["project"]["path"])

        if intent.get("intent") == "project_commands":
            commands = detect_project_commands(project_path)
            if not commands:
                return SkillResult(
                    response="Ainda não detectei comandos úteis neste projeto.",
                    action={"skill": self.name, "name": "project_commands", "status": "empty"},
                    data={"commands": []},
                )

            readable = ", ".join(command["command"] for command in commands[:5])
            return SkillResult(
                response=f"Comandos detectados: {readable}.",
                action={"skill": self.name, "name": "project_commands", "status": "done"},
                suggestions=[command["command"] for command in commands[:5]],
                data={"commands": commands},
            )

        if intent.get("intent") == "project_state":
            state = detect_project_state(project_path)
            return SkillResult(
                response=(
                    f"Estado do projeto pronto: {state['files']['tracked_count']} arquivo(s) relevantes, "
                    f"{state['commands']['count']} comando(s) detectado(s)."
                ),
                action={"skill": self.name, "name": "project_state", "status": "done"},
                suggestions=[command["command"] for command in state["commands"]["items"][:5]],
                data=state,
            )

        return self._open_project(project_path, options)

    def _open_project(self, project_path: Path, options: dict[str, Any]) -> SkillResult:
        policy = options.get("permission_policy") or PermissionPolicy()
        decision = policy.evaluate(self.name, "open_project", {"path": str(project_path)}, options)
        if not decision.allowed:
            return SkillResult(
                response="Eu abriria o projeto na IDE, mas ações de IDE estão desativadas por segurança.",
                action={
                    "skill": self.name,
                    "name": "open_project",
                    "status": decision.status,
                    "reason": decision.reason,
                    "path": str(project_path),
                },
                suggestions=["ativar JARVIS_ENABLE_IDE_ACTIONS se quiser permitir abertura da IDE"],
            )

        if shutil.which("code") is None:
            return SkillResult(
                response="Não encontrei `code` neste sistema para abrir o VS Code.",
                action={
                    "skill": self.name,
                    "name": "open_project",
                    "status": "unavailable",
                    "reason": "missing_binary",
                    "binary": "code",
                    "path": str(project_path),
                },
            )

        subprocess.Popen(["code", str(project_path)])
        return SkillResult(
            response="Abrindo projeto no VS Code.",
            action={"skill": self.name, "name": "open_project", "status": "done", "path": str(project_path)},
        )


def detect_project_commands(project_path: Path) -> list[dict[str, str]]:
    commands = []
    commands.extend(_makefile_commands(project_path / "Makefile"))
    commands.extend(_package_json_commands(project_path / "package.json"))
    if (project_path / "docker-compose.yml").exists():
        commands.append({"source": "docker-compose.yml", "name": "up", "command": "docker compose up"})
    if (project_path / "backend" / "tests").exists():
        commands.append({"source": "python", "name": "tests", "command": "python -m unittest discover -s tests"})
    return _unique_commands(commands)


def detect_project_state(project_path: Path) -> dict[str, Any]:
    commands = detect_project_commands(project_path)
    files = _project_files(project_path)
    directories = _project_directories(project_path)
    return {
        "path": str(project_path),
        "name": project_path.name,
        "markers": _project_markers(project_path),
        "directories": directories,
        "files": {
            "tracked_count": len(files),
            "items": files[:20],
        },
        "commands": {
            "count": len(commands),
            "items": commands[:10],
        },
    }


def _makefile_commands(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    targets = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([A-Za-z0-9_.-]+):(?:\s|$)", line)
        if match and not match.group(1).startswith("."):
            target = match.group(1)
            targets.append({"source": "Makefile", "name": target, "command": f"make {target}"})
    return targets


def _package_json_commands(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    scripts = payload.get("scripts") or {}
    return [
        {"source": "package.json", "name": name, "command": f"npm run {name}"}
        for name in sorted(scripts)
    ]


def _unique_commands(commands: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    result = []
    for command in commands:
        value = command["command"]
        if value in seen:
            continue
        seen.add(value)
        result.append(command)
    return result


def _project_markers(project_path: Path) -> list[str]:
    markers = ("README.md", "Makefile", "pyproject.toml", "package.json", "docker-compose.yml", ".git")
    return [marker for marker in markers if (project_path / marker).exists()]


def _project_directories(project_path: Path) -> list[dict[str, Any]]:
    ignored = {".git", ".jarvis", "__pycache__", ".venv", "node_modules"}
    directories = []
    for path in sorted(project_path.iterdir(), key=lambda item: item.name):
        if not path.is_dir() or path.name in ignored:
            continue
        try:
            child_count = len([child for child in path.iterdir() if child.name not in ignored])
        except OSError:
            child_count = 0
        directories.append({"name": path.name, "path": str(path), "child_count": child_count})
    return directories[:12]


def _project_files(project_path: Path) -> list[dict[str, Any]]:
    ignored_dirs = {".git", ".jarvis", "__pycache__", ".venv", "node_modules"}
    interesting_suffixes = {".md", ".py", ".toml", ".json", ".yml", ".yaml", ".txt"}
    files = []
    for path in sorted(project_path.rglob("*"), key=lambda item: str(item.relative_to(project_path))):
        relative = path.relative_to(project_path)
        if any(part in ignored_dirs for part in relative.parts):
            continue
        if not path.is_file():
            continue
        if path.name == "Makefile" or path.suffix in interesting_suffixes:
            files.append(
                {
                    "path": str(relative),
                    "name": path.name,
                    "size_bytes": path.stat().st_size,
                }
            )
        if len(files) >= 50:
            break
    return files
