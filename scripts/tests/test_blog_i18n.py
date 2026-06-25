import unittest

from blog_i18n import (
    infer_categories,
    permalink_for_lang,
    translation_langs_for_metadata,
)

class BlogI18nTests(unittest.TestCase):
    def test_permalink_for_default_lang(self):
        self.assertEqual(permalink_for_lang("ko", "sample-post"), "/posts/sample-post/")

    def test_permalink_for_translation(self):
        self.assertEqual(permalink_for_lang("en", "sample-post"), "/en/posts/sample-post/")

    def test_translation_langs_by_post_type(self):
        self.assertEqual(
            translation_langs_for_metadata({"post_type": "deep-dive"}),
            ("en", "ja", "zh"),
        )
        self.assertEqual(
            translation_langs_for_metadata({"post_type": "ai-news", "date": "2026-06-24"}),
            ("en", "ja", "zh"),
        )
        self.assertEqual(
            translation_langs_for_metadata({"post_type": "ai-news", "date": "2026-06-23"}),
            ("en",),
        )

    def test_infer_categories_defaults_to_devops(self):
        self.assertEqual(infer_categories({"tags": ["ubuntu"]}), ["DevOps"])

    def test_infer_categories_detects_ai_news(self):
        self.assertEqual(infer_categories({"post_type": "ai-news", "tags": []}), ["AI"])

    def test_infer_categories_detects_ai_tags(self):
        self.assertEqual(infer_categories({"tags": ["Ollama", "CLI"]}), ["AI"])

if __name__ == "__main__":
    unittest.main()
