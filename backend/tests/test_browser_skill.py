import unittest

from app.skills.browser import _normalize_url


class BrowserSkillTest(unittest.TestCase):
    def test_normalize_url_adds_https(self):
        self.assertEqual(_normalize_url("example.com"), "https://example.com")

    def test_normalize_url_keeps_https(self):
        self.assertEqual(_normalize_url("https://example.com/docs"), "https://example.com/docs")

    def test_normalize_url_rejects_non_http(self):
        self.assertIsNone(_normalize_url("file:///tmp/example"))


if __name__ == "__main__":
    unittest.main()
