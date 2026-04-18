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
        self.assertFalse(state["privacy"]["permissions"]["shell_enabled"])
        self.assertEqual(state["privacy"]["memory"]["commands_recorded"], 1)
        self.assertEqual(state["next_actions"][0], "confirmar checkpoint 1")
        self.assertEqual(state["actions"][0]["command"], "confirmar checkpoint 1")
        self.assertEqual(state["actions"][0]["risk"], "medium")
        self.assertTrue(state["actions"][0]["requires_confirmation"])
        self.assertEqual(state["actions"][1]["kind"], "suggestion")

    def test_build_ui_state_without_memory_store(self):
        session = SessionState().snapshot()

        state = build_ui_state(self.context, session=session, memory_store=None)

        self.assertEqual(state["history"]["commands"], [])
        self.assertFalse(state["privacy"]["memory"]["enabled"])
        self.assertEqual(state["actions"][0]["risk"], "low")


if __name__ == "__main__":
    unittest.main()
