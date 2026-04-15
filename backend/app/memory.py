import json
import os
import sqlite3
from datetime import datetime, timezone
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

        with sqlite3.connect(self.db_path) as conn:
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

    def recent_commands(self, limit: int = 10) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
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

    def clear_history(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM command_history")

    def stats(self) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM command_history").fetchone()[0]
            latest = conn.execute("SELECT created_at FROM command_history ORDER BY id DESC LIMIT 1").fetchone()

        return {
            "enabled": os.environ.get("JARVIS_DISABLE_MEMORY") != "1",
            "path": str(self.db_path),
            "commands_recorded": total,
            "latest_command_at": latest[0] if latest else None,
        }

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
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

    def _default_db_path(self, project_path: str | None) -> str:
        explicit_path = os.environ.get("JARVIS_MEMORY_PATH")
        if explicit_path:
            return explicit_path

        root = Path(project_path or os.environ.get("JARVIS_WORKSPACE") or Path.cwd())
        return str(root / ".jarvis" / "memory.sqlite")
