import tempfile
import unittest
from pathlib import Path

from app.context import LocalContextProvider
from app.memory import MemoryStore
from app.session import SessionState
from app.ui_state import build_ui_state


class UIStateTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.tempdir.name)
        (self.project_path / "README.md").write_text("# UI State Test\n", encoding="utf-8")
        (self.project_path / "Makefile").write_text("test:\n\tpython -m unittest\n", encoding="utf-8")
        self.context = LocalContextProvider(workspace=str(self.project_path)).get_context()
        self.memory = MemoryStore(db_path=str(self.project_path / "memory.sqlite"))

    def tearDown(self):
        self.tempdir.cleanup()

    def test_build_ui_state_groups_desktop_contract(self):
        session = SessionState()
        session.set_automation_checkpoints(
            "project_checkup",
            [
                {
                    "index": 1,
                    "label": "Rodar testes",
                    "reason": "confirmation_required",
                    "step": {"command": "make test"},
                }
            ],
        )
        self.memory.record_command(
            text="qual o status",
            intent={"intent": "status"},
            action={"skill": "system", "status": "done"},
            response="Tudo operacional.",
        )

        state = build_ui_state(
            self.context,
            session=session.snapshot(),
            memory_store=self.memory,
            history_limit=3,
        )

        self.assertEqual(state["schema_version"], 1)
        self.assertEqual(state["presence"]["name"], "JARVIS")
        self.assertEqual(state["checkpoints"]["pending_count"], 1)
        self.assertEqual(state["history"]["limit"], 3)
        self.assertEqual(state["history"]["commands"][0]["text"], "qual o status")
        self.assertEqual(state["memory_audit"]["matching_count"], 1)
        self.assertEqual(state["memory_audit"]["by_intent"][0]["name"], "status")
        self.assertFalse(state["privacy"]["permissions"]["shell_enabled"])
        self.assertEqual(state["privacy"]["memory"]["commands_recorded"], 1)
        self.assertEqual(state["next_actions"][0], "confirmar checkpoint 1")
        self.assertEqual(state["actions"][0]["command"], "confirmar checkpoint 1")
        self.assertEqual(state["actions"][0]["risk"], "medium")
        self.assertTrue(state["actions"][0]["requires_confirmation"])
        self.assertEqual(state["actions"][0]["permission"], "JARVIS_ENABLE_SHELL")
        self.assertEqual(state["actions"][0]["risk_category"], "execution")
        self.assertEqual(state["actions"][1]["kind"], "proactive")
        test_action = next(action for action in state["actions"] if action["command"] == "rodar make test")
        self.assertEqual(test_action["risk"], "medium")
        self.assertTrue(test_action["requires_confirmation"])
        self.assertIn("estado do projeto", state["next_actions"])
        self.assertTrue(state["proactive"]["suggestions"])
        self.assertEqual(state["capabilities"]["commands"]["count"], 1)
        self.assertGreaterEqual(state["capabilities"]["state"]["files"]["tracked_count"], 2)
        self.assertEqual(state["capabilities"]["blocked_count"], 5)
        self.assertEqual(state["capabilities"]["actions"][0]["env_var"], "JARVIS_ENABLE_SHELL")
        self.assertEqual(state["capabilities"]["actions"][0]["risk"], "high")
        self.assertEqual(state["capabilities"]["actions"][0]["risk_reason"], "permission_required")

    def test_build_ui_state_without_memory_store(self):
        session = SessionState().snapshot()

        state = build_ui_state(self.context, session=session, memory_store=None)

        self.assertEqual(state["history"]["commands"], [])
        self.assertEqual(state["memory_audit"]["matching_count"], 0)
        self.assertFalse(state["memory_audit"]["stats"]["enabled"])
        self.assertFalse(state["privacy"]["memory"]["enabled"])
        self.assertEqual(state["actions"][0]["risk"], "low")
        self.assertEqual(state["proactive"]["suggestions"][0]["command"], "estado do projeto")
        self.assertIn("capabilities", state)

    def test_build_ui_state_exposes_composite_checkpoint_detail(self):
        session = SessionState()
        session.add_automation_checkpoints(
            "multi_action",
            [
                {
                    "index": 2,
                    "label": "Etapa 2: rodar testes",
                    "reason": "confirmation_required",
                    "source": "multi_action",
                    "step": {
                        "label": "rodar testes",
                        "intent": "run_command",
                        "command": "make test",
                        "risk": "medium",
                        "requires_confirmation": True,
                        "permission": "JARVIS_ENABLE_SHELL",
                    },
                }
            ],
        )

        state = build_ui_state(self.context, session=session.snapshot(), memory_store=self.memory)

        checkpoint = state["checkpoints"]["checkpoints"][0]
        self.assertEqual(checkpoint["source_label"], "pedido composto")
        self.assertEqual(checkpoint["step_index"], 2)
        self.assertEqual(checkpoint["step_label"], "rodar testes")
        self.assertIn("make test", checkpoint["next_step"])


if __name__ == "__main__":
    unittest.main()
