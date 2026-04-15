import shutil
import subprocess
from typing import Any
from urllib.parse import quote_plus, urlparse

from ..permissions import PermissionPolicy
from .base import BaseSkill, SkillResult


class BrowserSkill(BaseSkill):
    name = "browser"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") in {"open_url", "web_search"}

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        if intent.get("intent") == "open_url":
            url = _normalize_url(intent.get("url") or "")
            if not url:
                return SkillResult(
                    response="Qual URL voce quer abrir?",
                    action={"skill": self.name, "name": "open_url", "status": "needs_url"},
                )
            return self._open_target(url, "open_url", options)

        query = (intent.get("query") or "").strip()
        if not query:
            return SkillResult(
                response="O que voce quer pesquisar?",
                action={"skill": self.name, "name": "search", "status": "needs_query"},
            )
        search_url = f"https://duckduckgo.com/?q={quote_plus(query)}"
        return self._open_target(search_url, "search", options, query=query)

    def _open_target(self, url: str, action: str, options: dict[str, Any], query: str | None = None) -> SkillResult:
        policy = options.get("permission_policy") or PermissionPolicy()
        decision = policy.evaluate(self.name, action, {"url": url, "query": query}, options)
        if not decision.allowed:
            return SkillResult(
                response="Eu abriria o navegador, mas ações de navegador estão desativadas por segurança.",
                action={
                    "skill": self.name,
                    "name": action,
                    "status": decision.status,
                    "reason": decision.reason,
                    "url": url,
                    "query": query,
                },
                suggestions=["ativar JARVIS_ENABLE_BROWSER_ACTIONS se quiser permitir abertura de navegador"],
            )

        if shutil.which("xdg-open") is None:
            return SkillResult(
                response="Não encontrei `xdg-open` neste sistema para abrir o navegador.",
                action={
                    "skill": self.name,
                    "name": action,
                    "status": "unavailable",
                    "reason": "missing_binary",
                    "binary": "xdg-open",
                    "url": url,
                    "query": query,
                },
            )

        completed = subprocess.run(["xdg-open", url], check=False, capture_output=True, text=True, timeout=5)
        status = "done" if completed.returncode == 0 else "failed"
        response = "Abrindo navegador." if action == "open_url" else f"Pesquisando por {query}."
        if status != "done":
            response = "Não consegui abrir o navegador."

        return SkillResult(
            response=response,
            action={
                "skill": self.name,
                "name": action,
                "status": status,
                "url": url,
                "query": query,
                "returncode": completed.returncode,
            },
            data={"stderr": completed.stderr.strip()[:500]},
        )


def _normalize_url(raw_url: str) -> str | None:
    value = raw_url.strip()
    if not value:
        return None

    parsed = urlparse(value)
    if not parsed.scheme:
        value = f"https://{value}"
        parsed = urlparse(value)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return value
