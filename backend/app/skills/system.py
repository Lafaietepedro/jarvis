import os
import platform
import shutil
from typing import Any

from ..diagnostics import collect_diagnostics
from .base import BaseSkill, SkillResult


class SystemSkill(BaseSkill):
    name = "system"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        return intent.get("intent") in {"status", "system_status", "capabilities", "diagnostics"}

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        if intent.get("intent") == "capabilities":
            return SkillResult(
                response=(
                    "Posso checar status local, listar arquivos do projeto, preparar comandos de shell, "
                    "abrir apps conhecidos e sugerir proximos passos com base no contexto. "
                    "Acoes sensiveis ficam bloqueadas ou pedem confirmacao."
                ),
                action={"skill": self.name, "name": "capabilities", "status": "done"},
                data={"privacy": context["privacy"], "project": context["project"]},
            )

        if intent.get("intent") == "diagnostics":
            diagnostics = collect_diagnostics(context)
            missing = [name for name, item in diagnostics["binaries"].items() if not item["available"]]
            response = "Diagnóstico local pronto."
            if missing:
                response += f" Dependências opcionais ausentes: {', '.join(missing[:5])}."
            return SkillResult(
                response=response,
                action={"skill": self.name, "name": "diagnostics", "status": "done"},
                data=diagnostics,
            )

        disk = shutil.disk_usage(context["project"]["path"])
        load_average = os.getloadavg() if hasattr(os, "getloadavg") else None
        data = {
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
            "load_average": load_average,
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
            },
            "project": context["project"],
            "privacy": context["privacy"],
        }

        return SkillResult(
            response="Estou operacional. O núcleo local está ativo e nenhuma integração externa é necessária.",
            action={"skill": self.name, "name": "status", "status": "done"},
            data=data,
        )
