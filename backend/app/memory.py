import json
import os
import sqlite3
from contextlib import closing
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
