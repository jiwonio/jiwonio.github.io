import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
            with patch.dict(
                "os.environ",
                {"LLM_USAGE_LOG": str(log_path), "LLM_USAGE_SOURCE": "unittest"},
                clear=True,
            ):
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
            self.assertEqual(record["source"], "unittest")
            self.assertGreater(record["estimated_cost_usd"], 0)

    @patch("api_monitor.notify_llm_usage")
    def test_log_thumbnail_usage_records_image_operation(self, mock_notify):
        from api_monitor import log_thumbnail_usage

        log_thumbnail_usage(
            provider="gemini",
            model="gemini-3.1-flash-image",
            slug="my-post",
            prompt="Modern tech blog thumbnail",
            thumbnail=b"\x00" * 2048,
            success=True,
        )
        mock_notify.assert_called_once()
        kwargs = mock_notify.call_args.kwargs
        self.assertEqual(kwargs["operation"], "generate_thumbnail")
        self.assertEqual(kwargs["slug"], "my-post")
        self.assertEqual(kwargs["input_chars"], len("Modern tech blog thumbnail"))
        self.assertEqual(kwargs["output_chars"], 2048)

if __name__ == "__main__":
    unittest.main()
