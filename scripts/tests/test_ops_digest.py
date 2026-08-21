import unittest
from unittest import mock

from ops_digest import (
    classify_post_file,
    collect_pipeline_section,
    format_digest,
    format_ops_section,
    format_url_section,
)


class OpsDigestTests(unittest.TestCase):
    def test_classify_post_file(self):
        self.assertEqual(
            classify_post_file("_posts/ko/2026/2026-06-17-cursor-ide.md"),
            "deep-dive",
        )

    def test_collect_pipeline_section_groups_by_slug(self):
        records = [
            {
                "slug": "post-a",
                "provider": "gemini",
                "operation": "generate_post",
                "success": True,
                "estimated_cost_usd": 0.1,
            },
            {
                "slug": "post-a",
                "provider": "anthropic",
                "operation": "translate_en",
                "success": True,
                "estimated_cost_usd": 0.05,
            },
            {
                "slug": "post-b",
                "provider": "gemini",
                "operation": "generate_thumbnail",
                "success": True,
                "estimated_cost_usd": 0.02,
            },
        ]
        with mock.patch("ops_digest.list_workflow_runs", return_value=[]):
            data = collect_pipeline_section(7, records)
        self.assertEqual(data["distinct_slugs"], 2)
        self.assertEqual(data["total_llm_calls"], 3)
        self.assertIn("post-a", data["fallback_slugs"])

    def test_format_ops_section_includes_llm_summary(self):
        text = "\n".join(
            format_ops_section(
                {
                    "days": 7,
                    "workflows": {
                        "totals": {"runs": 10, "success": 9, "failure": 1, "other": 0},
                        "workflows": {},
                    },
                    "new_posts": ["_posts/ko/2026/a.md"],
                    "post_types": {"deep-dive": 1},
                    "translation_gaps": 0,
                    "llm": {
                        "total_cost_usd": 1.5,
                        "total_calls": 12,
                        "monthly_estimate_usd": 6.4,
                    },
                }
            )
        )
        self.assertIn("Ops Digest", text)
        self.assertIn("$1.5000", text)
        self.assertIn("monthly est.", text)

    def test_format_url_section_shows_orphans(self):
        text = "\n".join(
            format_url_section(
                {
                    "check_live_urls": False,
                    "broken_ref_urls": 0,
                    "broken_samples": [],
                    "link_health": {
                        "total_posts": 31,
                        "orphan_count": 26,
                        "top_hubs": [{"slug": "hub-post", "inbound": 2}],
                    },
                }
            )
        )
        self.assertIn("Orphan posts: 26 / 31", text)
        self.assertIn("hub-post", text)

    def test_format_digest_contains_four_sections(self):
        digest = {
            "ops": {
                "days": 7,
                "workflows": {
                    "totals": {"runs": 0, "success": 0, "failure": 0, "other": 0},
                    "workflows": {},
                },
                "new_posts": [],
                "post_types": {},
                "translation_gaps": 0,
                "llm": {"total_cost_usd": 0, "total_calls": 0, "monthly_estimate_usd": 0},
            },
            "pipeline": {
                "pipeline_runs": {"AI Post": {"runs": 0, "success": 0, "failure": 0}},
                "total_llm_calls": 0,
                "distinct_slugs": 0,
                "avg_calls_per_slug": 0,
                "by_provider": {},
                "fallback_slugs": [],
                "slug_stats": [],
            },
            "url": {
                "check_live_urls": False,
                "broken_ref_urls": 0,
                "broken_samples": [],
                "link_health": {
                    "total_posts": 0,
                    "orphan_count": 0,
                    "top_hubs": [],
                },
            },
            "content": {
                "total_warnings": 0,
                "similarity": [],
                "informal_style": [],
                "overused_tokens": [],
            },
        }
        text = format_digest(digest)
        self.assertIn("1) Ops Digest", text)
        self.assertIn("2) Content Pipeline", text)
        self.assertIn("3) URL & Link Health", text)
        self.assertIn("4) Content Strategy", text)


if __name__ == "__main__":
    unittest.main()