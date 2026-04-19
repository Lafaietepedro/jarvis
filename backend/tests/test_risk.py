import unittest

from app.risk import (
    classify_action,
    classify_capability,
    classify_checkpoint,
    classify_command_text,
    permission_for_reason,
)


class RiskPolicyTest(unittest.TestCase):
    def test_shell_command_requires_confirmation_and_permission(self):
        profile = classify_action({"skill": "shell", "name": "run_command", "command": "make test"})

        self.assertEqual(profile.risk, "medium")
        self.assertTrue(profile.requires_confirmation)
        self.assertEqual(profile.permission, "JARVIS_ENABLE_SHELL")
        self.assertEqual(profile.category, "execution")

    def test_dangerous_shell_command_is_high_risk(self):
        profile = classify_command_text("rodar rm -rf /tmp/example")

        self.assertEqual(profile.risk, "high")
        self.assertTrue(profile.requires_confirmation)
        self.assertEqual(profile.reason, "dangerous_command")

    def test_memory_deletion_is_high_risk(self):
        profile = classify_action({"skill": "memory", "name": "clear_history", "status": "needs_confirmation"})

        self.assertEqual(profile.risk, "high")
        self.assertTrue(profile.requires_confirmation)
        self.assertEqual(profile.reason, "memory_deletion")

    def test_read_file_is_read_only(self):
        profile = classify_action({"skill": "files", "name": "read_file", "status": "done"})

        self.assertEqual(profile.risk, "low")
        self.assertFalse(profile.requires_confirmation)
        self.assertEqual(profile.reason, "read_only")

    def test_file_edit_proposal_is_read_only(self):
        profile = classify_action({"skill": "files", "name": "propose_file_edit", "status": "planned"})

        self.assertEqual(profile.risk, "low")
        self.assertFalse(profile.requires_confirmation)
        self.assertEqual(profile.reason, "read_only")

    def test_checkpoint_inherits_step_permission(self):
        profile = classify_checkpoint(
            {
                "reason": "confirmation_required",
                "intent": "run_command",
                "command": "make test",
                "risk": "medium",
            }
        )

        self.assertEqual(profile.risk, "medium")
        self.assertTrue(profile.requires_confirmation)
        self.assertEqual(profile.permission, "JARVIS_ENABLE_SHELL")
        self.assertEqual(profile.severity, "review")

    def test_blocked_capability_keeps_permission_metadata(self):
        profile = classify_capability("browser.open_url", enabled=False)

        self.assertEqual(profile.risk, "medium")
        self.assertEqual(profile.permission, "JARVIS_ENABLE_BROWSER_ACTIONS")
        self.assertEqual(profile.reason, "permission_required")

    def test_permission_for_reason_maps_disabled_actions(self):
        self.assertEqual(permission_for_reason("media_actions_disabled"), "JARVIS_ENABLE_MEDIA_ACTIONS")
        self.assertIsNone(permission_for_reason("read_only"))

    def test_multi_action_uses_highest_step_risk(self):
        profile = classify_action(
            {
                "skill": "core",
                "name": "multi_action",
                "step_actions": [
                    {"skill": "system", "name": "status", "status": "done"},
                    {"skill": "shell", "name": "run_command", "command": "make test", "status": "needs_confirmation"},
                ],
            }
        )

        self.assertEqual(profile.risk, "medium")
        self.assertTrue(profile.requires_confirmation)
        self.assertEqual(profile.permission, "JARVIS_ENABLE_SHELL")
        self.assertEqual(profile.reason, "multi_action")


if __name__ == "__main__":
    unittest.main()
