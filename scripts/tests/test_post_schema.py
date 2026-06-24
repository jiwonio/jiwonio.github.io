import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from post_schema import (
    has_standalone_line,
    sanitize_error_for_slack,
    sanitize_generated_content,
    strip_references_section,
)


class PostSchemaTests(unittest.TestCase):
    def test_has_standalone_line(self):
        content = "intro\n<!--more-->\nbody"
        self.assertTrue(has_standalone_line(content, "<!--more-->"))
        self.assertFalse(has_standalone_line(content, "[HERO_IMAGE]"))

    def test_sanitize_stripe_key(self):
        content = "key sk-live-abcdefghijklmnopqrstuvwxyz123456"
        sanitized = sanitize_generated_content(content)
        self.assertNotIn("sk-live-abcdefghijklmnopqrstuvwxyz123456", sanitized)
        self.assertIn("sk-YOUR_STRIPE_SECRET_KEY", sanitized)

    def test_sanitize_github_token(self):
        content = "token ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        sanitized = sanitize_generated_content(content)
        self.assertNotIn("ghp_abcdefghijklmnopqrstuvwxyz1234567890", sanitized)

    def test_sanitize_aws_key(self):
        content = "AKIAIOSFODNN7EXAMPLE"
        sanitized = sanitize_generated_content(content)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", sanitized)

    def test_sanitize_bearer_token(self):
        content = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.extra"
        sanitized = sanitize_generated_content(content)
        self.assertIn("Bearer YOUR_TOKEN_HERE", sanitized)

    def test_sanitize_pem_block(self):
        content = (
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEpAIBAAKCAQEA1234567890\n"
            "-----END RSA PRIVATE KEY-----"
        )
        sanitized = sanitize_generated_content(content)
        self.assertNotIn("MIIEpAIBAAKCAQEA1234567890", sanitized)

    def test_sanitize_error_for_slack_truncates(self):
        error = "x" * 600
        sanitized = sanitize_error_for_slack(error)
        self.assertLessEqual(len(sanitized), 500)
        self.assertTrue(sanitized.endswith("..."))

    def test_sanitize_error_for_slack_redacts_secrets(self):
        error = 'failed: api_key: "super-secret-token-value-12345"'
        sanitized = sanitize_error_for_slack(error)
        self.assertNotIn("super-secret-token-value-12345", sanitized)

    def test_strip_references_section(self):
        content = "body\n\n### 참고문헌\n- [link](https://example.com)"
        stripped = strip_references_section(content)
        self.assertNotIn("### 참고문헌", stripped)
        self.assertIn("body", stripped)


if __name__ == "__main__":
    unittest.main()