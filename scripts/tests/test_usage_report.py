import json
import tempfile
import unittest
from pathlib import Path

from usage_report import (
    check_budget,
    format_markdown,
    format_summary,
    infer_record_category,
    is_production_llm_record,
    parse_jsonl,
    parse_llm_usage_line,
    summarize,
)

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
        summary = summarize(records, period_days=7)
        self.assertEqual(summary["total_calls"], 2)
        self.assertEqual(summary["successes"], 1)
        self.assertAlmostEqual(summary["success_rate"], 50.0)
        self.assertAlmostEqual(summary["total_cost_usd"], 0.03)
        self.assertEqual(summary["by_provider"]["gemini"]["calls"], 1)
        self.assertIn("by_category", summary)
        self.assertIn("monthly_estimate_usd", summary)

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
        summary = {"total_calls": 10, "total_cost_usd": 60.0, "monthly_estimate_usd": 60.0}
        self.assertFalse(check_budget(summary, 50.0))

    def test_check_budget_passes_when_under_threshold(self):
        summary = {"total_calls": 10, "total_cost_usd": 20.0, "monthly_estimate_usd": 20.0}
        self.assertTrue(check_budget(summary, 50.0))

    def test_parse_llm_usage_line_accepts_actions_log_format(self):
        line = (
            'build##[notice]llm_usage={"provider": "gemini", "model": "m", '
            '"success": true, "estimated_cost_usd": 0.01}'
        )
        record = parse_llm_usage_line(line)
        self.assertIsNotNone(record)
        self.assertEqual(record["provider"], "gemini")

    def test_is_production_llm_record_skips_unittest_notices(self):
        self.assertFalse(
            is_production_llm_record(
                {"source": "unittest", "operation": "generate_post", "slug": "real-slug", "input_chars": 5000}
            )
        )
        self.assertFalse(
            is_production_llm_record(
                {"operation": "generate_post", "slug": "demo", "input_chars": 0}
            )
        )
        self.assertFalse(
            is_production_llm_record(
                {"operation": "generate_post", "slug": "", "input_chars": 1000, "output_chars": 2000}
            )
        )
        self.assertFalse(
            is_production_llm_record(
                {"operation": "generate_thumbnail", "slug": "", "input_chars": 120}
            )
        )
        self.assertTrue(
            is_production_llm_record(
                {"operation": "translate_en", "slug": "ai-news-2026-06-25", "input_chars": 100}
            )
        )
        self.assertTrue(
            is_production_llm_record(
                {
                    "source": "production",
                    "operation": "generate_thumbnail",
                    "slug": "my-post",
                    "input_chars": 120,
                    "output_chars": 4096,
                }
            )
        )

    def test_format_summary_shows_none_when_empty(self):
        text = format_summary(summarize([]))
        self.assertIn("(none)", text)

    def test_infer_record_category(self):
        self.assertEqual(
            infer_record_category({"operation": "translate_en", "slug": "demo"}),
            "translation",
        )
        self.assertEqual(
            infer_record_category({"operation": "generate_post", "slug": "ai-news-2026-06-25"}),
            "ai-news",
        )
        self.assertEqual(
            infer_record_category({"operation": "generate_thumbnail", "slug": "my-post"}),
            "image",
        )

    def test_format_markdown_includes_tables(self):
        summary = summarize(
            [
                {
                    "provider": "gemini",
                    "model": "gemini-2.5-pro",
                    "operation": "generate_post",
                    "slug": "demo",
                    "success": True,
                    "estimated_cost_usd": 0.1,
                }
            ],
            period_days=1,
        )
        text = format_markdown(summary)
        self.assertIn("# LLM Usage Dashboard", text)
        self.assertIn("| gemini |", text)

if __name__ == "__main__":
    unittest.main()
