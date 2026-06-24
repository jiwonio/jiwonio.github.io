import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from blog_i18n import infer_ai_generated
from validate_posts import validate_language_content, prose_body


class ModelsAndValidationTests(unittest.TestCase):
    def test_infer_ai_generated_for_ai_news(self):
        metadata = {"post_type": "ai-news", "categories": ["AI"]}
        self.assertTrue(infer_ai_generated(metadata, Path("_posts/ko/2026/2026-06-23-ai-news.md")))

    def test_infer_ai_generated_for_recent_ai_deep_dive(self):
        metadata = {"post_type": "deep-dive", "categories": ["AI"]}
        path = Path("_posts/ko/2026/2026-06-22-ollama-self-hosted-language-model-runner.md")
        self.assertTrue(infer_ai_generated(metadata, path))

    def test_infer_ai_generated_false_for_legacy_devops(self):
        metadata = {"post_type": "deep-dive", "categories": ["DevOps"]}
        path = Path("_posts/ko/2024/2024-08-15-ubuntu22-swap-memory.md")
        self.assertFalse(infer_ai_generated(metadata, path))

    def test_validate_korean_content_passes(self):
        content = """---
layout: post
---
한국어 도입부입니다. 실무에서 바로 쓸 수 있는 설정과 트러블슈팅을 정리합니다.
<!--more-->
한국어 본문입니다. 세부 설정과 주의할 점을 단계별로 설명합니다.
"""
        self.assertIsNone(validate_language_content("ko", content))

    def test_validate_japanese_content_fails_without_script(self):
        content = """---
layout: post
---
This is mostly English without Japanese script.
<!--more-->
Body.
"""
        self.assertIsNotNone(validate_language_content("ja", content))


if __name__ == "__main__":
    unittest.main()