import tempfile
import unittest
from pathlib import Path

from audit_content_quality import audit_informal_style, audit_title_similarity
from audit_discoverability import audit_ai_news_series, audit_internal_links
from validate_posts import validate_translation_structure


def write_post(root: Path, relative: str, body: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


KO_BASE = """---
layout: post
title: "샘플"
slug: sample-post
lang: ko
translation_key: sample-post
post_type: deep-dive
date: 2026-06-01 10:00:00 +0900
categories:
- AI
tags:
- sample
description: 샘플 설명
image: /uploads/sample-post/thumbnail.webp
ai_generated: true
---
한국어 도입부입니다. 실무에서 바로 쓸 수 있는 설정과 트러블슈팅을 정리합니다.

<!--more-->

## 첫 섹션

본문입니다.

### 참고문헌
- [Example](https://example.com/a)
"""


class AuditScriptTests(unittest.TestCase):
    def test_validate_translation_structure_flags_h2_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ko = write_post(root, "_posts/ko/2026/2026-06-01-sample-post.md", KO_BASE)
            en = write_post(
                root,
                "_posts/en/2026/2026-06-01-sample-post.md",
                KO_BASE.replace("lang: ko", "lang: en").replace("한국어", "English"),
            )
            groups = {
                "sample-post": {
                    "ko": (ko, {}),
                    "en": (en, {}),
                }
            }
            errors = validate_translation_structure(groups)
            self.assertEqual(errors, [])

    def test_audit_title_similarity_warns_on_overlap(self):
        posts = [
            (
                Path("a.md"),
                {"title": "Cursor IDE review", "slug": "cursor-ide-review"},
                "",
            ),
            (
                Path("b.md"),
                {"title": "Cursor IDE real world review", "slug": "cursor-review"},
                "",
            ),
        ]
        warnings = audit_title_similarity(posts)
        self.assertTrue(warnings)

    def test_audit_informal_style_detects_haeyo(self):
        posts = [
            (
                Path("a.md"),
                {"ai_generated": True, "post_type": "deep-dive", "date": "2026-06-01"},
                KO_BASE + "\n이 문장은 해요.\n",
            )
        ]
        warnings = audit_informal_style(posts)
        self.assertTrue(any("informal Korean" in warning for warning in warnings))

    def test_audit_ai_news_series_requires_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            posts_dir = Path(tmp) / "_posts"
            write_post(
                posts_dir,
                "ko/2026/2026-06-01-ai-news.md",
                KO_BASE.replace("post_type: deep-dive", "post_type: ai-news").replace(
                    "tags:\n- sample", "tags:\n- news"
                ),
            )
            warnings = audit_ai_news_series(posts_dir)
            self.assertTrue(any("ai-news tag missing" in warning for warning in warnings))

    def test_audit_internal_links_reports_orphans(self):
        with tempfile.TemporaryDirectory() as tmp:
            posts_dir = Path(tmp) / "_posts"
            uploads = Path(tmp) / "uploads" / "solo-post"
            uploads.mkdir(parents=True)
            (uploads / "thumbnail.webp").write_bytes(b"x")
            write_post(
                posts_dir,
                "ko/2026/2026-06-01-solo-post.md",
                KO_BASE.replace("sample-post", "solo-post"),
            )
            warnings = audit_internal_links(posts_dir)
            self.assertTrue(any("orphan post" in warning for warning in warnings))


if __name__ == "__main__":
    unittest.main()