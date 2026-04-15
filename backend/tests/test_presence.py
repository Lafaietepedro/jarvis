import unittest

from app.presence import build_greeting, build_presence


class PresenceTest(unittest.TestCase):
    def setUp(self):
        self.context = {
            "project": {
                "name": "jarvis",
                "path": "/tmp/jarvis",
                "markers": ["README.md"],
                "capabilities": {},
            },
            "privacy": {
                "local_first": True,
                "audio_persisted": False,
                "cloud_enabled": False,
                "desktop_actions_enabled": False,
                "shell_enabled": False,
            },
        }
        self.session = {
            "status": "listening",
            "voice_listening": True,
            "started_at": "2026-04-15T00:00:00+00:00",
            "last_activity_at": "2026-04-15T00:00:00+00:00",
            "uptime_seconds": 10,
            "current_task": "voice",
        }

    def test_text_greeting_mentions_active_state_and_project(self):
        greeting = build_greeting(self.context, mode="text")

        self.assertIn("JARVIS ativo", greeting)
        self.assertIn("jarvis", greeting)

    def test_voice_greeting_mentions_listening(self):
        greeting = build_greeting(self.context, mode="voice")

        self.assertIn("JARVIS ativo", greeting)
        self.assertIn("ouvindo", greeting)

    def test_presence_payload_is_auditable(self):
        presence = build_presence(
            self.context,
            session=self.session,
        )

        self.assertEqual(presence["status"], "listening")
        self.assertTrue(presence["voice_listening"])
        self.assertTrue(presence["privacy"]["local_first"])
        self.assertIn("qual o status", presence["suggestions"])

    def test_paused_presence_has_paused_greeting(self):
        self.session["status"] = "paused"
        self.session["voice_listening"] = False

        presence = build_presence(self.context, session=self.session)

        self.assertIn("pausado", presence["greeting"])


if __name__ == "__main__":
    unittest.main()
