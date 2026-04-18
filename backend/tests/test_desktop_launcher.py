import tempfile
import unittest
from pathlib import Path

from app.desktop_launcher import build_desktop_entry, default_icon_path, default_ui_url, write_desktop_entry


class DesktopLauncherTest(unittest.TestCase):
    def test_build_desktop_entry(self):
        entry = build_desktop_entry("http://127.0.0.1:8000/ui", app_name="JARVIS\nLocal")

        self.assertIn("[Desktop Entry]", entry)
        self.assertIn("Name=JARVIS Local", entry)
        self.assertIn("Exec=xdg-open http://127.0.0.1:8000/ui", entry)
        self.assertIn(f"Icon={default_icon_path()}", entry)
        self.assertNotIn("\nName=JARVIS\n", entry)

    def test_default_ui_url(self):
        self.assertEqual(default_ui_url("http://127.0.0.1:8000/"), "http://127.0.0.1:8000/ui")

    def test_write_desktop_entry(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "jarvis.desktop"

            written = write_desktop_entry(str(path), "content")

            self.assertEqual(written, path)
            self.assertEqual(path.read_text(encoding="utf-8"), "content")
            self.assertTrue(path.stat().st_mode & 0o111)


if __name__ == "__main__":
    unittest.main()
