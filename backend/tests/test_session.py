import unittest

from app.session import SessionState


class SessionStateTest(unittest.TestCase):
    def test_transitions(self):
        session = SessionState()

        session.set_listening()
        self.assertEqual(session.snapshot()["status"], "listening")
        self.assertTrue(session.snapshot()["voice_listening"])

        session.set_processing("command")
        processing = session.snapshot()
        self.assertEqual(processing["status"], "processing")
        self.assertEqual(processing["current_task"], "command")

        session.set_paused()
        paused = session.snapshot()
        self.assertEqual(paused["status"], "paused")
        self.assertFalse(paused["voice_listening"])

    def test_automation_checkpoints_are_stored_and_removed(self):
        session = SessionState()
        session.set_automation_checkpoints(
            "project_checkup",
            [
                {
                    "index": 3,
                    "label": "Rodar testes do projeto",
                    "reason": "confirmation_required",
                    "step": {"intent": "run_command", "command": "make test"},
                }
            ],
        )

        snapshot = session.snapshot()
        self.assertEqual(snapshot["automation_checkpoints"][0]["checkpoint_id"], 1)
        self.assertEqual(snapshot["automation_checkpoints"][0]["plan"], "project_checkup")
        self.assertEqual(snapshot["automation_checkpoints"][0]["command"], "make test")
        self.assertEqual(snapshot["automation_checkpoints"][0]["intent"], "run_command")
        self.assertEqual(snapshot["automation_checkpoints"][0]["index"], 3)

        checkpoint = session.get_automation_checkpoint(1)
        self.assertEqual(checkpoint["step"]["command"], "make test")

        session.remove_automation_checkpoint(1)
        self.assertEqual(session.snapshot()["automation_checkpoints"], [])

    def test_automation_checkpoints_can_be_appended(self):
        session = SessionState()
        session.set_automation_checkpoints(
            "project_checkup",
            [
                {
                    "index": 1,
                    "label": "Rodar testes do projeto",
                    "reason": "confirmation_required",
                    "step": {"intent": "run_command", "command": "make test"},
                }
            ],
        )

        stored = session.add_automation_checkpoints(
            "multi_action",
            [
                {
                    "index": 2,
                    "label": "Etapa 2: abrir projeto",
                    "reason": "permission_required",
                    "source": "multi_action",
                    "step": {"intent": "open_project"},
                }
            ],
        )

        snapshot = session.snapshot()
        self.assertEqual(stored[0]["checkpoint_id"], 2)
        self.assertEqual(len(snapshot["automation_checkpoints"]), 2)
        self.assertEqual(snapshot["automation_checkpoints"][1]["plan"], "multi_action")
        self.assertEqual(snapshot["automation_checkpoints"][1]["source"], "multi_action")

    def test_file_edit_checkpoint_snapshot_exposes_review_metadata(self):
        session = SessionState()
        session.add_automation_checkpoints(
            "file_edit",
            [
                {
                    "index": 1,
                    "label": "Aplicar edicao em README.md",
                    "reason": "confirmation_required",
                    "source": "file_edit",
                    "step": {
                        "intent": "apply_file_edit",
                        "label": "Aplicar edicao em README.md",
                        "path": "README.md",
                        "diff": "--- a/README.md\n+++ b/README.md",
                        "occurrences": 1,
                        "risk": "high",
                        "requires_confirmation": True,
                    },
                }
            ],
        )

        checkpoint = session.snapshot()["automation_checkpoints"][0]

        self.assertEqual(checkpoint["path"], "README.md")
        self.assertEqual(checkpoint["diff"], "--- a/README.md\n+++ b/README.md")
        self.assertEqual(checkpoint["occurrences"], 1)

    def test_automation_checkpoint_events_are_recorded_newest_first(self):
        session = SessionState()

        session.record_automation_checkpoint_event(
            {
                "checkpoint_id": 1,
                "label": "Rodar testes",
                "plan": "project_checkup",
                "status": "blocked",
                "reason": "shell_disabled",
            }
        )

        event = session.snapshot()["automation_checkpoint_events"][0]
        self.assertEqual(event["checkpoint_id"], 1)
        self.assertEqual(event["status"], "blocked")
        self.assertEqual(event["reason"], "shell_disabled")
        self.assertIn("created_at", event)


if __name__ == "__main__":
    unittest.main()
