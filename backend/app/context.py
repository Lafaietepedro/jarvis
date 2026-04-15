import os
from pathlib import Path
from typing import Any


PROJECT_MARKERS = (
    "README.md",
    "Makefile",
    "pyproject.toml",
    "package.json",
    "docker-compose.yml",
    ".git",
)


class LocalContextProvider:
    def __init__(self, workspace: str | None = None):
        self.workspace = workspace or os.environ.get("JARVIS_WORKSPACE")

    def get_context(self) -> dict[str, Any]:
        project_path = self._detect_project_path()
        markers = [marker for marker in PROJECT_MARKERS if (project_path / marker).exists()]
        capabilities = {
            "has_makefile": "Makefile" in markers,
            "has_docker_compose": "docker-compose.yml" in markers,
            "has_python": (project_path / "pyproject.toml").exists() or (project_path / "backend").exists(),
            "has_node": "package.json" in markers,
        }

        return {
            "project": {
                "path": str(project_path),
                "name": project_path.name,
                "markers": markers,
                "capabilities": capabilities,
            },
            "privacy": {
                "local_first": True,
                "audio_persisted": False,
                "cloud_enabled": os.environ.get("JARVIS_ENABLE_CLOUD") == "1",
                "desktop_actions_enabled": os.environ.get("JARVIS_ENABLE_DESKTOP_ACTIONS") == "1",
                "browser_actions_enabled": os.environ.get("JARVIS_ENABLE_BROWSER_ACTIONS") == "1",
                "shell_enabled": os.environ.get("JARVIS_ENABLE_SHELL") == "1",
                "media_actions_enabled": os.environ.get("JARVIS_ENABLE_MEDIA_ACTIONS") == "1",
                "memory_enabled": os.environ.get("JARVIS_DISABLE_MEMORY") != "1",
            },
        }

    def _detect_project_path(self) -> Path:
        if self.workspace:
            return Path(self.workspace).expanduser().resolve()

        current = Path.cwd().resolve()
        for path in (current, *current.parents):
            if any((path / marker).exists() for marker in PROJECT_MARKERS):
                return path
        return current
