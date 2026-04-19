import unittest

from app.ui_frontend import read_ui_asset, read_ui_index


class UIFrontendTest(unittest.TestCase):
    def test_read_ui_index_contains_app_shell(self):
        html = read_ui_index()

        self.assertIn("<title>JARVIS</title>", html)
        self.assertIn('id="command-form"', html)
        self.assertIn('id="checkpoint-events"', html)
        self.assertIn('id="refresh-interval"', html)
        self.assertIn('/ui/assets/manifest.webmanifest', html)
        self.assertIn('/ui/assets/icon.svg', html)
        self.assertIn('/ui/assets/app.js', html)

    def test_read_ui_assets_are_whitelisted(self):
        script = read_ui_asset("app.js")
        styles = read_ui_asset("styles.css")
        manifest = read_ui_asset("manifest.webmanifest")
        icon = read_ui_asset("icon.svg")
        missing = read_ui_asset("../main.py")

        self.assertIsNotNone(script)
        self.assertIsNotNone(styles)
        self.assertIsNotNone(manifest)
        self.assertIsNotNone(icon)
        self.assertEqual(script[1], "text/javascript")
        self.assertEqual(styles[1], "text/css")
        self.assertEqual(manifest[1], "application/manifest+json")
        self.assertEqual(icon[1], "image/svg+xml")
        self.assertIn("renderCheckpointEvents", script[0])
        self.assertIn("normalizeAction", script[0])
        self.assertIn("requires_confirmation", script[0])
        self.assertIn("next_step", script[0])
        self.assertIn("blocked_count", script[0])
        self.assertIn("tracked_count", script[0])
        self.assertIn("jarvis.refreshInterval", script[0])
        self.assertIn('"start_url": "/ui"', manifest[0])
        self.assertIsNone(missing)


if __name__ == "__main__":
    unittest.main()
