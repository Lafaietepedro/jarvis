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
            }

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
