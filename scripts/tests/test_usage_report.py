import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from usage_report import check_budget, format_summary, parse_jsonl, summarize


class UsageReportTests(unittest.TestCase):
    def test_summarize_counts_calls_and_cost(self):
        records = [
            {
                "provider": "gemini",
                "model": "gemini-2.5-pro",
                "success": True,
                "estimated_cost_usd": 0.01,
            },
            {
                "provider": "anthropic",
                "model": "claude-sonnet-4-6",
                "success": False,
                "estimated_cost_usd": 0.02,
            },
        ]
        summary = summarize(records)
        self.assertEqual(summary["total_calls"], 2)
        self.assertEqual(summary["successes"], 1)
        self.assertAlmostEqual(summary["success_rate"], 50.0)
        self.assertAlmostEqual(summary["total_cost_usd"], 0.03)
        self.assertEqual(summary["by_provider"]["gemini"]["calls"], 1)

    def test_parse_jsonl_skips_invalid_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "usage.jsonl"
            path.write_text(
                json.dumps({"provider": "gemini", "model": "m", "success": True}) + "\n"
                "not-json\n",
                encoding="utf-8",
            )
            records = parse_jsonl(path)
        self.assertEqual(len(records), 1)

    def test_format_summary_includes_provider_breakdown(self):
        summary = summarize(
            [
                {
                    "provider": "openai",
                    "model": "gpt-4.1",
                    "success": True,
                    "estimated_cost_usd": 0.5,
                }
            ]
        )
        text = format_summary(summary)
        self.assertIn("openai", text)
        self.assertIn("gpt-4.1", text)

    def test_check_budget_warns_when_over_threshold(self):
        summary = {"total_calls": 10, "total_cost_usd": 60.0}
        self.assertFalse(check_budget(summary, 50.0))

    def test_check_budget_passes_when_under_threshold(self):
        summary = {"total_calls": 10, "total_cost_usd": 20.0}
        self.assertTrue(check_budget(summary, 50.0))


if __name__ == "__main__":
    unittest.main()