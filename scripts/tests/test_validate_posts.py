import tempfile
import unittest
from pathlib import Path

from validate_posts import validate_posts

def write_post(root: Path, relative: str, body: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")

def make_post(lang: str, slug: str, post_type: str, prose: str) -> str:
    return f"""---
layout: post
title: "Sample {lang}"
slug: {slug}
lang: {lang}
translation_key: {slug}
post_type: {post_type}
date: 2026-06-01 10:00:00 +0900
categories:
- AI
tags:
- sample
description: Sample description
image: /uploads/{slug}/thumbnail.webp
---
{prose}
"""

KO_PROSE = """한국어 도입부입니다. 실무에서 바로 쓸 수 있는 설정과 트러블슈팅을 정리합니다.

<!--more-->

한국어 본문입니다. 세부 설정과 주의할 점을 단계별로 설명합니다.
"""
EN_PROSE = """English intro for the translation group test with enough words.

<!--more-->

English body with enough prose for validation checks.
"""
JA_PROSE = """日本語の導入です。実務で使える設定とトラブルシューティングをまとめます。

<!--more-->

日本語の本文です。手順と注意点を説明します。
"""
ZH_PROSE = """中文导语。记录可直接用于生产的配置与排错经验。

<!--more-->

中文正文。分步说明配置方法与注意事项。
"""

class ValidatePostsTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.posts = self.root / "_posts"
        uploads = self.root / "uploads" / "sample-post"
        uploads.mkdir(parents=True)
        (uploads / "thumbnail.webp").write_bytes(b"webp")

    def tearDown(self):
        self.tempdir.cleanup()

    def test_valid_translation_group_passes(self):
        for lang, prose in (
            ("ko", KO_PROSE),
            ("en", EN_PROSE),
            ("ja", JA_PROSE),
            ("zh", ZH_PROSE),
        ):
            write_post(
                self.posts,
                f"{lang}/2026/2026-06-01-sample-post.md",
                make_post(lang, "sample-post", "deep-dive", prose),
            )

        errors = validate_posts(self.posts, site_root=self.root)
        self.assertEqual(errors, [])

    def test_missing_translation_is_reported(self):
        write_post(
            self.posts,
            "ko/2026/2026-06-01-sample-post.md",
            make_post("ko", "sample-post", "deep-dive", KO_PROSE),
        )

        errors = validate_posts(self.posts, site_root=self.root)
        self.assertTrue(any("missing translations" in error for error in errors))

    def test_broken_internal_link_is_reported(self):
        prose = KO_PROSE + "\nSee [missing](/posts/does-not-exist/).\n"
        write_post(
            self.posts,
            "ko/2026/2026-06-01-sample-post.md",
            make_post("ko", "sample-post", "deep-dive", prose),
        )
        for lang, body_prose in (("en", EN_PROSE), ("ja", JA_PROSE), ("zh", ZH_PROSE)):
            write_post(
                self.posts,
                f"{lang}/2026/2026-06-01-sample-post.md",
                make_post(lang, "sample-post", "deep-dive", body_prose),
            )

        errors = validate_posts(self.posts, site_root=self.root)
        self.assertTrue(any("broken internal link" in error for error in errors))

    def test_translation_structure_mismatch_is_reported(self):
        ko_prose = KO_PROSE + "\n## 첫 번째 섹션\n\n## 두 번째 섹션\n"
        en_prose = """English intro for the translation group test with enough words.

<!--more-->

English body only.
"""
        for lang, prose in (
            ("ko", ko_prose),
            ("en", en_prose),
            ("ja", JA_PROSE),
            ("zh", ZH_PROSE),
        ):
            write_post(
                self.posts,
                f"{lang}/2026/2026-06-01-sample-post.md",
                make_post(lang, "sample-post", "deep-dive", prose),
            )

        errors = validate_posts(self.posts, site_root=self.root)
        self.assertTrue(any("translation structure mismatch" in error for error in errors))

if __name__ == "__main__":
    unittest.main()
