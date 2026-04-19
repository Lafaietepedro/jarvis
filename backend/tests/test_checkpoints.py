import unittest

from app.checkpoints import build_checkpoint_state


class CheckpointsTest(unittest.TestCase):
    def test_build_checkpoint_state(self):
        state = build_checkpoint_state(
            {
                "automation_checkpoints": [
                    {
                        "checkpoint_id": 1,
                        "label": "Rodar testes",
                        "plan": "project_checkup",
                        "reason": "confirmation_required",
                    }
                ],
                "automation_checkpoint_events": [
                    {
                        "checkpoint_id": 1,
                        "label": "Rodar testes",
                        "status": "blocked",
                    }
                ],
            }
        )

        self.assertEqual(state["status"], "pending")
        self.assertEqual(state["pending_count"], 1)
        self.assertEqual(state["event_count"], 1)
        self.assertEqual(state["checkpoints"][0]["checkpoint_id"], 1)
        self.assertEqual(state["checkpoints"][0]["severity"], "review")
        self.assertEqual(state["checkpoints"][0]["risk"], "medium")
        self.assertTrue(state["checkpoints"][0]["requires_confirmation"])
        self.assertEqual(state["summary"]["pending"], 1)
        self.assertEqual(state["summary"]["blocked_events"], 1)
        self.assertIn("Rodar testes", state["events"][0]["message"])

    def test_empty_checkpoint_state(self):
        state = build_checkpoint_state({})

        self.assertEqual(state["status"], "empty")
        self.assertEqual(state["pending_count"], 0)
        self.assertEqual(state["event_count"], 0)
        self.assertEqual(state["checkpoints"], [])
        self.assertEqual(state["events"], [])
        self.assertEqual(state["summary"]["next_step"], "Nenhuma acao pendente.")

    def test_multi_action_checkpoint_exposes_step_detail(self):
        state = build_checkpoint_state(
            {
                "automation_checkpoints": [
                    {
                        "checkpoint_id": 1,
                        "index": 2,
                        "label": "Etapa 2: rodar testes",
                        "plan": "multi_action",
                        "source": "multi_action",
                        "reason": "confirmation_required",
                        "intent": "run_command",
                        "command": "make test",
                        "step_label": "rodar testes",
                        "risk": "medium",
                        "permission": "JARVIS_ENABLE_SHELL",
                    }
                ],
                "automation_checkpoint_events": [],
            }
        )

        checkpoint = state["checkpoints"][0]
        self.assertEqual(checkpoint["source_label"], "pedido composto")
        self.assertEqual(checkpoint["step_index"], 2)
        self.assertEqual(checkpoint["step_label"], "rodar testes")
        self.assertIn("pedido composto", checkpoint["checkpoint_detail"])
        self.assertIn("etapa 2", checkpoint["checkpoint_detail"])


if __name__ == "__main__":
    unittest.main()
