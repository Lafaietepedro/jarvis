import os
import unittest
from unittest.mock import patch

from app.permissions import PermissionPolicy


class PermissionPolicyTest(unittest.TestCase):
    def setUp(self):
        self.policy = PermissionPolicy()

    def test_shell_requires_confirmation(self):
        decision = self.policy.evaluate("shell", "run_command", {"command": "make test"}, {})

        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_confirmation)
        self.assertEqual(decision.status, "needs_confirmation")

    def test_shell_blocks_dangerous_commands(self):
        decision = self.policy.evaluate(
            "shell",
            "run_command",
            {"command": "rm -rf /tmp/example"},
            {"confirm_actions": True},
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "dangerous_command")

    def test_shell_allows_confirmed_command_when_enabled(self):
        with patch.dict(os.environ, {"JARVIS_ENABLE_SHELL": "1"}):
            decision = self.policy.evaluate(
                "shell",
                "run_command",
                {"command": "make test"},
                {"confirm_actions": True},
            )

        self.assertTrue(decision.allowed)

    def test_desktop_actions_are_disabled_by_default(self):
        decision = self.policy.evaluate("computer", "open_app", {"target": "terminal"}, {})

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "desktop_actions_disabled")

    def test_media_actions_are_disabled_by_default(self):
        decision = self.policy.evaluate("media", "control", {"media_action": "volume_up"}, {})

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "media_actions_disabled")

    def test_media_actions_can_be_enabled(self):
        with patch.dict(os.environ, {"JARVIS_ENABLE_MEDIA_ACTIONS": "1"}):
            decision = self.policy.evaluate("media", "control", {"media_action": "volume_up"}, {})

        self.assertTrue(decision.allowed)

    def test_browser_actions_are_disabled_by_default(self):
        decision = self.policy.evaluate("browser", "search", {"query": "jarvis"}, {})

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "browser_actions_disabled")

    def test_browser_actions_can_be_enabled(self):
        with patch.dict(os.environ, {"JARVIS_ENABLE_BROWSER_ACTIONS": "1"}):
            decision = self.policy.evaluate("browser", "search", {"query": "jarvis"}, {})

        self.assertTrue(decision.allowed)


if __name__ == "__main__":
    unittest.main()
