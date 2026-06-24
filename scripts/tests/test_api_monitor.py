import json
import tempfile
import unittest
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api_monitor import estimate_cost_usd, notify_llm_usage


class ApiMonitorTests(unittest.TestCase):
    @patch("api_monitor.urlopen")
    def test_notify_llm_usage_posts_to_slack_when_configured(self, mock_urlopen):
        with patch.dict("os.environ", {"SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/x/y/z"}):
            notify_llm_usage(
                provider="gemini",
                model="gemini-2.5-pro",
                attempt=1,
                operation="generate_post",
                slug="demo",
            )
        mock_urlopen.assert_called_once()

    @patch("api_monitor.urlopen")
    def test_notify_llm_usage_sanitizes_error_for_slack(self, mock_urlopen):
        with patch.dict("os.environ", {"SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/x/y/z"}):
            notify_llm_usage(
                provider="gemini",
                model="gemini-2.5-pro",
                attempt=1,
                operation="generate_post",
                success=False,
                error='api_key: "super-secret-token-value-12345"',
            )
        body = mock_urlopen.call_args[0][0].data.decode("utf-8")
        self.assertNotIn("super-secret-token-value-12345", body)
        self.assertIn("REDACTED", body)

    @patch("api_monitor.urlopen")
    def test_notify_llm_usage_skips_slack_without_webhook(self, mock_urlopen):
        with patch.dict("os.environ", {}, clear=True):
            notify_llm_usage(
                provider="gemini",
                model="gemini-2.5-pro",
                attempt=1,
                operation="generate_post",
            )
        mock_urlopen.assert_not_called()

    def test_estimate_cost_usd_uses_model_rates(self):
        cost = estimate_cost_usd("gemini-2.5-pro", 1_000_000, 1_000_000)
        self.assertAlmostEqual(cost, 11.25)

    @patch("api_monitor.urlopen")
    def test_notify_llm_usage_writes_jsonl_log(self, mock_urlopen):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "usage.jsonl"
            with patch.dict("os.environ", {"LLM_USAGE_LOG": str(log_path)}, clear=True):
                notify_llm_usage(
                    provider="gemini",
                    model="gemini-2.5-pro",
                    attempt=1,
                    operation="generate_post",
                    input_chars=1000,
                    output_chars=2000,
                )
            lines = log_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertEqual(record["input_chars"], 1000)
            self.assertGreater(record["estimated_cost_usd"], 0)


if __name__ == "__main__":
    unittest.main()