import difflib
from pathlib import Path
from typing import Any

from .base import BaseSkill, SkillResult


MAX_TEXT_BYTES = 20_000
MAX_PREVIEW_CHARS = 2_000
IGNORED_DIRS = {".git", ".jarvis", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules", ".venv", "venv"}


class FileSkill(BaseSkill):
    name = "files"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") in {"list_files", "where_am_i", "find_file", "read_file", "propose_file_edit"}

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        project_path = Path(context["project"]["path"])

        if intent.get("intent") == "where_am_i":
            return SkillResult(
                response=f"Estou trabalhando em {project_path}.",
                action={"skill": self.name, "name": "pwd", "status": "done", "path": str(project_path)},
                data={"path": str(project_path)},
            )

        if intent.get("intent") == "find_file":
            return _find_file(project_path, intent.get("target") or "")

        if intent.get("intent") == "read_file":
            return _read_file(project_path, intent.get("target") or "")

        if intent.get("intent") == "propose_file_edit":
            return _propose_file_edit(
                project_path,
                intent.get("target") or "",
                intent.get("old_text") or "",
                intent.get("new_text") or "",
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


def _find_file(project_path: Path, target: str) -> SkillResult:
    query = target.strip()
    if not query:
        return SkillResult(
            response="Qual arquivo voce quer localizar?",
            action={"skill": "files", "name": "find_file", "status": "needs_target"},
        )

    matches = _find_matches(project_path, query)
    if not matches:
        return SkillResult(
            response=f"Nao encontrei arquivos com `{query}` neste workspace.",
            action={"skill": "files", "name": "find_file", "status": "empty", "target": query},
            data={"matches": [], "target": query},
        )

    readable = ", ".join(match["path"] for match in matches[:5])
    return SkillResult(
        response=f"Encontrei {len(matches)} arquivo(s): {readable}.",
        action={"skill": "files", "name": "find_file", "status": "done", "target": query},
        suggestions=[f"ler arquivo {matches[0]['path']}"],
        data={"matches": matches[:20], "target": query, "total": len(matches)},
    )


def _read_file(project_path: Path, target: str) -> SkillResult:
    query = target.strip()
    if not query:
        return SkillResult(
            response="Qual arquivo voce quer que eu leia?",
            action={"skill": "files", "name": "read_file", "status": "needs_target"},
        )

    path = _resolve_project_file(project_path, query)
    if path is None or not path.exists() or not path.is_file():
        matches = _find_matches(project_path, query)
        suggestions = [f"ler arquivo {match['path']}" for match in matches[:3]]
        return SkillResult(
            response=f"Nao encontrei um arquivo legivel chamado `{query}` neste workspace.",
            action={"skill": "files", "name": "read_file", "status": "not_found", "target": query},
            suggestions=suggestions,
            data={"matches": matches[:10], "target": query},
        )

    if path.stat().st_size > MAX_TEXT_BYTES:
        return SkillResult(
            response=f"`{_relative_path(project_path, path)}` e grande demais para leitura direta agora.",
            action={
                "skill": "files",
                "name": "read_file",
                "status": "blocked",
                "reason": "file_too_large",
                "path": _relative_path(project_path, path),
            },
        )

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return SkillResult(
            response=f"`{_relative_path(project_path, path)}` nao parece ser texto UTF-8.",
            action={
                "skill": "files",
                "name": "read_file",
                "status": "blocked",
                "reason": "binary_or_unsupported_encoding",
                "path": _relative_path(project_path, path),
            },
        )

    summary = _summarize_text(content)
    relative = _relative_path(project_path, path)
    return SkillResult(
        response=f"Li `{relative}`. {summary}",
        action={"skill": "files", "name": "read_file", "status": "done", "path": relative},
        data={
            "path": relative,
            "size_bytes": path.stat().st_size,
            "line_count": len(content.splitlines()),
            "preview": content[:MAX_PREVIEW_CHARS],
            "truncated": len(content) > MAX_PREVIEW_CHARS,
            "summary": summary,
        },
        )


def _propose_file_edit(project_path: Path, target: str, old_text: str, new_text: str) -> SkillResult:
    query = target.strip()
    if not query or not old_text:
        return SkillResult(
            response="Para preparar uma edicao, diga o arquivo e o texto a substituir.",
            action={"skill": "files", "name": "propose_file_edit", "status": "needs_details"},
        )

    path = _resolve_project_file(project_path, query)
    if path is None or not path.exists() or not path.is_file():
        matches = _find_matches(project_path, query)
        return SkillResult(
            response=f"Nao encontrei um arquivo legivel chamado `{query}` para preparar edicao.",
            action={"skill": "files", "name": "propose_file_edit", "status": "not_found", "target": query},
            suggestions=[f"encontrar arquivo {query}"],
            data={"matches": matches[:10], "target": query},
        )

    blocked = _read_text_for_edit(project_path, path)
    if isinstance(blocked, SkillResult):
        return blocked
    content = blocked
    occurrences = content.count(old_text)
    relative = _relative_path(project_path, path)
    if occurrences == 0:
        return SkillResult(
            response=f"Nao encontrei o trecho solicitado em `{relative}`. Nenhuma edicao foi preparada.",
            action={
                "skill": "files",
                "name": "propose_file_edit",
                "status": "not_found",
                "reason": "old_text_not_found",
                "path": relative,
            },
            suggestions=[f"ler arquivo {relative}"],
        )

    updated = content.replace(old_text, new_text, 1)
    diff = _unified_diff(relative, content, updated)
    return SkillResult(
        response=f"Preparei uma proposta de edicao para `{relative}`. Nada foi gravado.",
        action={
            "skill": "files",
            "name": "propose_file_edit",
            "status": "planned",
            "path": relative,
            "occurrences": occurrences,
        },
        suggestions=[f"ler arquivo {relative}"],
        data={
            "path": relative,
            "old_text": old_text,
            "new_text": new_text,
            "occurrences": occurrences,
            "diff": diff,
            "writes_file": False,
        },
    )


def _read_text_for_edit(project_path: Path, path: Path) -> str | SkillResult:
    relative = _relative_path(project_path, path)
    if path.stat().st_size > MAX_TEXT_BYTES:
        return SkillResult(
            response=f"`{relative}` e grande demais para preparar edicao direta agora.",
            action={
                "skill": "files",
                "name": "propose_file_edit",
                "status": "blocked",
                "reason": "file_too_large",
                "path": relative,
            },
        )

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return SkillResult(
            response=f"`{relative}` nao parece ser texto UTF-8.",
            action={
                "skill": "files",
                "name": "propose_file_edit",
                "status": "blocked",
                "reason": "binary_or_unsupported_encoding",
                "path": relative,
            },
        )


def _resolve_project_file(project_path: Path, target: str) -> Path | None:
    root = project_path.resolve()
    candidate = (root / target).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if candidate.exists():
        return candidate

    matches = _find_matches(project_path, target)
    if matches:
        return (root / matches[0]["path"]).resolve()
    return candidate


def _find_matches(project_path: Path, query: str) -> list[dict[str, Any]]:
    normalized = query.lower().strip()
    matches = []
    for path in _iter_project_files(project_path):
        relative = _relative_path(project_path, path)
        name = path.name.lower()
        relative_lower = relative.lower()
        if normalized in name or normalized in relative_lower:
            matches.append({"path": relative, "name": path.name, "size_bytes": path.stat().st_size})
    return sorted(matches, key=lambda item: (len(item["path"]), item["path"].lower()))


def _iter_project_files(project_path: Path):
    for path in project_path.rglob("*"):
        if any(part.startswith(".") or part in IGNORED_DIRS for part in path.relative_to(project_path).parts[:-1]):
            continue
        if path.name.startswith(".") or path.name in IGNORED_DIRS:
            continue
        if path.is_file():
            yield path


def _relative_path(project_path: Path, path: Path) -> str:
    return str(path.resolve().relative_to(project_path.resolve()))


def _summarize_text(content: str) -> str:
    lines = content.splitlines()
    non_empty = [line.strip() for line in lines if line.strip()]
    if not non_empty:
        return "O arquivo esta vazio."

    heading = next((line for line in non_empty if line.startswith("#")), None)
    first = heading or non_empty[0]
    if len(first) > 160:
        first = first[:157] + "..."
    return f"Resumo: {len(lines)} linha(s). Primeiro trecho relevante: {first}"


def _unified_diff(relative_path: str, before: str, after: str) -> str:
    diff = difflib.unified_diff(
        before.splitlines(),
        after.splitlines(),
        fromfile=f"a/{relative_path}",
        tofile=f"b/{relative_path}",
        lineterm="",
    )
    return "\n".join(diff)
