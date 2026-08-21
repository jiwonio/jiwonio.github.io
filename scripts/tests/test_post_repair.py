import unittest
from unittest import mock

from post_analysis import rebuild_references_section
from post_common import (
    count_markdown_internal_links,
    drop_broken_reference_urls,
    has_standalone_line,
    repair_hero_image_placeholder,
    repair_internal_links,
    repair_internal_post_slugs,
    resolve_internal_post_slug,
)

class PostRepairTests(unittest.TestCase):
    def test_repair_hero_image_placeholder_inserts_block(self):
        content = """---
layout: post
---
intro

<!--more-->
## 1. News
"""
        repaired = repair_hero_image_placeholder(content)
        self.assertTrue(has_standalone_line(repaired, "[HERO_IMAGE]"))
        self.assertTrue(has_standalone_line(repaired, "-----"))

    def test_repair_internal_links_injects_before_references(self):
        content = """---
layout: post
---
<!--more-->
[HERO_IMAGE]
-----
## 1. News

### 참고문헌
- [a](https://example.com)
"""
        candidates = [
            {"url": "/posts/docker-guide/", "title": "Docker Guide"},
            {"url": "/posts/llm-agent/", "title": "LLM Agent"},
        ]
        repaired = repair_internal_links(content, candidates, min_links=2)
        self.assertGreaterEqual(count_markdown_internal_links(repaired), 2)
        self.assertIn("/posts/docker-guide/", repaired)
        self.assertLess(repaired.index("## 관련 블로그 글"), repaired.index("### 참고문헌"))

    def test_resolve_truncated_internal_slug(self):
        ko_slugs = {
            "building-a-production-ready-local-development-environment-with-docker-compose",
        }
        truncated = "building-a-production-ready-local-development-with-docker-compose"
        resolved = resolve_internal_post_slug(truncated, ko_slugs)
        self.assertEqual(
            resolved,
            "building-a-production-ready-local-development-environment-with-docker-compose",
        )

    def test_repair_internal_post_slugs_fixes_truncated_links(self):
        ko_slugs = {
            "building-a-production-ready-local-development-environment-with-docker-compose",
        }
        content = "See [Docker](/posts/building-a-production-ready-local-development-with-docker-compose/)."
        repaired = repair_internal_post_slugs(content, ko_slugs)
        self.assertIn("development-environment-with-docker-compose", repaired)

    def test_rebuild_references_section_restores_source_urls(self):
        source = """---
layout: post
---
### 참고문헌
- [원문](https://example.com/good){:target="_blank"}
- [둘째](https://example.com/also-good){:target="_blank"}
"""
        translated = """---
layout: post
---
## References
- [English title](https://example.com/broken){:target="_blank"}
- [Second](https://example.com/wrong){:target="_blank"}
"""
        repaired = rebuild_references_section(translated, source, "en")
        self.assertIn("https://example.com/good", repaired)
        self.assertIn("https://example.com/also-good", repaired)
        self.assertNotIn("https://example.com/broken", repaired)
        self.assertIn("## References", repaired)

    def test_drop_broken_reference_urls_removes_unreachable_links(self):
        content = """---
layout: post
---
### 참고문헌
- [good](https://example.com){:target="_blank"}
- [bad](https://example.com/definitely-missing-page-404){:target="_blank"}
"""
        with mock.patch("validate_posts.check_reference_url") as check_mock:
            check_mock.side_effect = lambda url: (
                "reference URL returned HTTP 404"
                if "missing-page" in url
                else None
            )
            repaired, dropped = drop_broken_reference_urls(content)

        self.assertEqual(dropped, ["https://example.com/definitely-missing-page-404"])
        self.assertIn("https://example.com", repaired)
        self.assertNotIn("missing-page-404", repaired)

if __name__ == "__main__":
    unittest.main()
