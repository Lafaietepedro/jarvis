from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillResult:
    response: str
    action: dict[str, Any]
    suggestions: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "response": self.response,
            "action": self.action,
            "suggestions": self.suggestions,
            "data": self.data,
        }


class BaseSkill:
    name = "base"

    def can_handle(self, intent: dict[str, Any]) -> bool:
        raise NotImplementedError

    def handle(self, intent: dict[str, Any], context: dict[str, Any], options: dict[str, Any]) -> SkillResult:
        raise NotImplementedError
