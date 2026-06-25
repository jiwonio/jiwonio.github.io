import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from post_common import (
    count_markdown_internal_links,
    has_standalone_line,
    repair_ai_news_structure,
    repair_hero_image_placeholder,
    repair_internal_links,
    repair_internal_post_slugs,
    resolve_internal_post_slug,
)


class AiNewsRepairTests(unittest.TestCase):
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

    def test_repair_ai_news_structure_combines_fixes(self):
        content = """---
layout: post
---
<!--more-->
## 1. News
body text

### 참고문헌
- [a](https://example.com)
"""
        candidates = [{"url": "/posts/foo/", "title": "Foo"}]
        repaired = repair_ai_news_structure(content, candidates)
        self.assertTrue(has_standalone_line(repaired, "[HERO_IMAGE]"))
        self.assertGreaterEqual(count_markdown_internal_links(repaired), 1)


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


if __name__ == "__main__":
    unittest.main()