import unittest

from app.ui_frontend import read_ui_asset, read_ui_index


class UIFrontendTest(unittest.TestCase):
    def test_read_ui_index_contains_app_shell(self):
        html = read_ui_index()

        self.assertIn("<title>JARVIS</title>", html)
        self.assertIn('id="command-form"', html)
        self.assertIn('/ui/assets/app.js', html)

    def test_read_ui_assets_are_whitelisted(self):
        script = read_ui_asset("app.js")
        styles = read_ui_asset("styles.css")
        missing = read_ui_asset("../main.py")

        self.assertIsNotNone(script)
        self.assertIsNotNone(styles)
        self.assertEqual(script[1], "text/javascript")
        self.assertEqual(styles[1], "text/css")
        self.assertIsNone(missing)


if __name__ == "__main__":
    unittest.main()
