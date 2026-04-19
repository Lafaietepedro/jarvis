import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any


class MemoryStore:
    def __init__(self, db_path: str | None = None, project_path: str | None = None):
        self.db_path = Path(db_path or self._default_db_path(project_path))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def record_command(
        self,
        text: str,
        intent: dict[str, Any],
        action: dict[str, Any],
        response: str,
        private: bool = False,
    ):
        if private or os.environ.get("JARVIS_DISABLE_MEMORY") == "1":
            return

        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                """
                INSERT INTO command_history
                    (created_at, text, intent, action, response)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    text,
                    json.dumps(intent, ensure_ascii=True),
                    json.dumps(action, ensure_ascii=True),
                    response,
                ),
            )
            conn.commit()

    def recent_commands(self, limit: int = 10) -> list[dict[str, Any]]:
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT created_at, text, intent, action, response
                FROM command_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "created_at": row["created_at"],
                "text": row["text"],
                "intent": json.loads(row["intent"]),
                "action": json.loads(row["action"]),
                "response": row["response"],
            }
            for row in rows
        ]

    def export_history(self, limit: int | None = None) -> dict[str, Any]:
        query = """
            SELECT created_at, text, intent, action, response
            FROM command_history
            ORDER BY id ASC
        """
        params = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)

        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        commands = [
            {
                "created_at": row["created_at"],
                "text": row["text"],
                "intent": json.loads(row["intent"]),
                "action": json.loads(row["action"]),
                "response": row["response"],
            }
            for row in rows
        ]

        return {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "stats": self.stats(),
            "commands": commands,
        }

    def audit_summary(
        self,
        intent: str | None = None,
        skill: str | None = None,
        action: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        commands = self._filtered_commands(
            intent=intent,
            skill=skill,
            action=action,
            since=since,
            until=until,
        )
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "filters": {
                "intent": intent,
                "skill": skill,
                "action": action,
                "since": since,
                "until": until,
                "limit": limit,
            },
            "stats": self.stats(),
            "matching_count": len(commands),
            "first_command_at": commands[-1]["created_at"] if commands else None,
            "latest_command_at": commands[0]["created_at"] if commands else None,
            "by_intent": _count_by(commands, lambda command: command.get("intent", {}).get("intent", "unknown")),
            "by_skill": _count_by(commands, lambda command: command.get("action", {}).get("skill", "unknown")),
            "by_action": _count_by(commands, lambda command: command.get("action", {}).get("name", "unknown")),
            "by_status": _count_by(commands, lambda command: command.get("action", {}).get("status", "unknown")),
            "sample": commands[:limit],
        }

    def clear_history(self) -> int:
        with closing(sqlite3.connect(self.db_path)) as conn:
            total = conn.execute("SELECT COUNT(*) FROM command_history").fetchone()[0]
            conn.execute("DELETE FROM command_history")
            conn.commit()
        return total

    def stats(self) -> dict[str, Any]:
        with closing(sqlite3.connect(self.db_path)) as conn:
            total = conn.execute("SELECT COUNT(*) FROM command_history").fetchone()[0]
            latest = conn.execute("SELECT created_at FROM command_history ORDER BY id DESC LIMIT 1").fetchone()

        return {
            "enabled": os.environ.get("JARVIS_DISABLE_MEMORY") != "1",
            "path": str(self.db_path),
            "commands_recorded": total,
            "latest_command_at": latest[0] if latest else None,
        }

    def _init_db(self):
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS command_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    text TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    action TEXT NOT NULL,
                    response TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _default_db_path(self, project_path: str | None) -> str:
        explicit_path = os.environ.get("JARVIS_MEMORY_PATH")
        if explicit_path:
            return explicit_path

        root = Path(project_path or os.environ.get("JARVIS_WORKSPACE") or Path.cwd())
        return str(root / ".jarvis" / "memory.sqlite")

    def _filtered_commands(
        self,
        intent: str | None = None,
        skill: str | None = None,
        action: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict[str, Any]]:
        since_at = _parse_datetime_filter(since, end_of_day=False)
        until_at = _parse_datetime_filter(until, end_of_day=True)
        commands = self.export_history()["commands"]
        filtered = []
        for command in reversed(commands):
            created_at = _parse_datetime_filter(command["created_at"], end_of_day=False)
            if since_at and created_at and created_at < since_at:
                continue
            if until_at and created_at and created_at > until_at:
                continue
            if intent and command.get("intent", {}).get("intent") != intent:
                continue
            if skill and command.get("action", {}).get("skill") != skill:
                continue
            if action and command.get("action", {}).get("name") != action:
                continue
            filtered.append(command)
        return filtered


def _count_by(commands: list[dict[str, Any]], key_func) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for command in commands:
        key = key_func(command) or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return [
        {"name": name, "count": count}
        for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _parse_datetime_filter(value: str | None, end_of_day: bool) -> datetime | None:
    if not value:
        return None
    try:
        if len(value) == 10:
            parsed_date = datetime.fromisoformat(value).date()
            parsed_time = time.max if end_of_day else time.min
            return datetime.combine(parsed_date, parsed_time, tzinfo=timezone.utc)
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
