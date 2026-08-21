import unittest

from blog_i18n import (
    infer_categories,
    permalink_for_lang,
    translation_langs_for_metadata,
    validate_translation_content,
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

    def test_infer_categories_defaults_to_devops(self):
        self.assertEqual(infer_categories({"tags": ["ubuntu"]}), ["DevOps"])

    def test_infer_categories_detects_ai_tags(self):
        self.assertEqual(infer_categories({"tags": ["Ollama", "CLI"]}), ["AI"])

    def test_validate_translation_accepts_english_references_heading(self):
        source = """---
layout: post
title: "원문"
slug: sample-post
lang: ko
translation_key: sample-post
post_type: deep-dive
date: 2026-07-03 00:00:00 +0900
categories: [AI]
tags: [Cursor]
description: 원문
image: /uploads/sample-post/thumbnail.webp
---
intro

<!--more-->

body

### 참고문헌
- [원문](https://example.com/source){:target="_blank"}
"""
        translated = source.replace('lang: ko', 'lang: en').replace(
            "### 참고문헌",
            "## References",
        ).replace("[원문](https://example.com/source)", "[Source](https://example.com/source)")

        validate_translation_content(
            translated,
            "en",
            "sample-post",
            source_content=source,
        )

if __name__ == "__main__":
    unittest.main()
