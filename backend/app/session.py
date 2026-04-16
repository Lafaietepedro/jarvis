from datetime import datetime, timezone
from threading import Lock
from typing import Any


class SessionState:
    def __init__(self):
        now = datetime.now(timezone.utc)
        self._lock = Lock()
        self._started_at = now
        self._last_activity_at = now
        self._status = "active"
        self._voice_listening = False
        self._current_task = None
        self._automation_checkpoints: list[dict[str, Any]] = []

    def set_active(self):
        self._update(status="active", voice_listening=False, current_task=None)

    def set_listening(self):
        self._update(status="listening", voice_listening=True, current_task="voice")

    def set_processing(self, current_task: str | None = None):
        self._update(status="processing", current_task=current_task)

    def set_paused(self):
        self._update(status="paused", voice_listening=False, current_task=None)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            now = datetime.now(timezone.utc)
            return {
                "status": self._status,
                "voice_listening": self._voice_listening,
                "started_at": self._started_at.isoformat(),
                "last_activity_at": self._last_activity_at.isoformat(),
                "uptime_seconds": int((now - self._started_at).total_seconds()),
                "current_task": self._current_task,
                "automation_checkpoints": [
                    {
                        "checkpoint_id": checkpoint["checkpoint_id"],
                        "label": checkpoint["label"],
                        "plan": checkpoint["plan"],
                        "reason": checkpoint["reason"],
                    }
                    for checkpoint in self._automation_checkpoints
                ],
            }

    def set_automation_checkpoints(self, plan_name: str, checkpoints: list[dict[str, Any]]):
        with self._lock:
            self._automation_checkpoints = [
                {
                    **checkpoint,
                    "checkpoint_id": index,
                    "plan": plan_name,
                }
                for index, checkpoint in enumerate(checkpoints, start=1)
            ]

    def get_automation_checkpoint(self, checkpoint_id: int | None = None) -> dict[str, Any] | None:
        with self._lock:
            if not self._automation_checkpoints:
                return None
            if checkpoint_id is None:
                return self._automation_checkpoints[0]
            for checkpoint in self._automation_checkpoints:
                if checkpoint["checkpoint_id"] == checkpoint_id:
                    return checkpoint
        return None

    def remove_automation_checkpoint(self, checkpoint_id: int):
        with self._lock:
            self._automation_checkpoints = [
                checkpoint
                for checkpoint in self._automation_checkpoints
                if checkpoint["checkpoint_id"] != checkpoint_id
            ]

    def _update(
        self,
        status: str | None = None,
        voice_listening: bool | None = None,
        current_task: str | None = None,
    ):
        with self._lock:
            self._last_activity_at = datetime.now(timezone.utc)
            if status is not None:
                self._status = status
            if voice_listening is not None:
                self._voice_listening = voice_listening
            self._current_task = current_task
