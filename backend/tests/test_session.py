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

        checkpoint = session.get_automation_checkpoint(1)
        self.assertEqual(checkpoint["step"]["command"], "make test")

        session.remove_automation_checkpoint(1)
        self.assertEqual(session.snapshot()["automation_checkpoints"], [])


if __name__ == "__main__":
    unittest.main()
