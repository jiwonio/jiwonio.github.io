import unittest
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api_monitor import notify_llm_usage


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
    def test_notify_llm_usage_skips_slack_without_webhook(self, mock_urlopen):
        with patch.dict("os.environ", {}, clear=True):
            notify_llm_usage(
                provider="gemini",
                model="gemini-2.5-pro",
                attempt=1,
                operation="generate_post",
            )
        mock_urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()