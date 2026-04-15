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


if __name__ == "__main__":
    unittest.main()
