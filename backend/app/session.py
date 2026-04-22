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
        self._automation_checkpoint_events: list[dict[str, Any]] = []

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
                    self._checkpoint_snapshot(checkpoint)
                    for checkpoint in self._automation_checkpoints
                ],
                "automation_checkpoint_events": list(self._automation_checkpoint_events),
            }

    def _checkpoint_snapshot(self, checkpoint: dict[str, Any]) -> dict[str, Any]:
        step = checkpoint.get("step", {})
        snapshot = {
            "checkpoint_id": checkpoint["checkpoint_id"],
            "index": checkpoint.get("index"),
            "label": checkpoint["label"],
            "plan": checkpoint["plan"],
            "source": checkpoint.get("source"),
            "reason": checkpoint["reason"],
            "intent": step.get("intent"),
            "command": step.get("command"),
            "step_label": step.get("label"),
            "risk": step.get("risk"),
            "permission": step.get("permission"),
        }
        for key in ("path", "diff", "occurrences", "edit_preview", "replacement_strategy"):
            if step.get(key) is not None:
                snapshot[key] = step[key]
        return snapshot

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

    def add_automation_checkpoints(self, plan_name: str, checkpoints: list[dict[str, Any]]) -> list[dict[str, Any]]:
        with self._lock:
            next_id = max(
                [checkpoint["checkpoint_id"] for checkpoint in self._automation_checkpoints],
                default=0,
            ) + 1
            stored = [
                {
                    **checkpoint,
                    "checkpoint_id": index,
                    "plan": plan_name,
                }
                for index, checkpoint in enumerate(checkpoints, start=next_id)
            ]
            self._automation_checkpoints.extend(stored)
            return list(stored)

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

    def record_automation_checkpoint_event(self, event: dict[str, Any]):
        with self._lock:
            self._automation_checkpoint_events.insert(
                0,
                {
                    **event,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            self._automation_checkpoint_events = self._automation_checkpoint_events[:10]

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
