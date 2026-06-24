import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from post_common import sanitize_generated_content


class SanitizeGeneratedContentTests(unittest.TestCase):
    def test_masks_slack_webhook(self):
        content = "webhook https://hooks.slack.com/services/T000/B000/XXXX in body"
        sanitized = sanitize_generated_content(content)
        self.assertNotIn("/services/T000/B000/XXXX", sanitized)
        self.assertIn("YOUR_WORKSPACE", sanitized)

    def test_masks_secret_like_values(self):
        content = 'api_key: "super-secret-token-value-12345"'
        sanitized = sanitize_generated_content(content)
        self.assertIn("YOUR_DUMMY_SECRET_HERE", sanitized)
        self.assertNotIn("super-secret-token-value-12345", sanitized)

    def test_leaves_normal_text_untouched(self):
        content = "OpenAI Codex and Docker Compose example."
        self.assertEqual(sanitize_generated_content(content), content)


if __name__ == "__main__":
    unittest.main()