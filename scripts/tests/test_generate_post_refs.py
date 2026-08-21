import unittest
from unittest import mock

from generate_post import MIN_REFERENCE_URLS, validate_deep_dive_content


def _deep_dive_body(*, title: str, slug: str, tags: str, refs: list[tuple[str, str]]) -> str:
    ref_lines = "\n".join(
        f'- [{name}]({url}){{:target="_blank"}}' for name, url in refs
    )
    return f"""---
layout: post
title: "{title}"
slug: "{slug}"
lang: ko
translation_key: "{slug}"
post_type: deep-dive
date: 2026-07-10 09:00:00 +0900
categories: [DevOps]
tags: {tags}
description: "운영자가 정한 주제로 쓴 초안입니다."
image: "/uploads/{slug}/thumbnail.webp"
---
도입부 첫 문단입니다. 실무에서 겪은 상황을 적습니다.

두번째 문단입니다. 팀 온보딩 때 바로 쓸 수 있습니다.

세 번째 문단: 이 글을 읽으면 한 가지를 결정할 수 있습니다.
<!--more-->
[HERO_IMAGE]
-----

## 본문
실무 적용 방법을 설명합니다.

| 상황 | 추천 | 이유 |
| --- | --- | --- |
| 1인 사이드 | 도입 | 빠른 피드백 |
| 스타트업 5인 | 부분 도입 | 리뷰 병목 완화 |
| 레거시 많음 | 점진 도입 | 컨텍스트 부담 분산 |

### 참고문헌
{ref_lines}
"""


class GeneratePostRefsTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch("generate_post.validate_tag_consistency")
        patcher.start()
        self.addCleanup(patcher.stop)

    @mock.patch("generate_post.get_existing_ko_slugs", return_value=set())
    @mock.patch("generate_post.find_broken_reference_urls", return_value=[])
    def test_validate_deep_dive_accepts_live_refs(self, _broken, _existing):
        content = _deep_dive_body(
            title="Ubuntu 스왑 설정으로 OOM 줄이기",
            slug="ubuntu-swap-oom-notes",
            tags="[Ubuntu, Swap, Memory]",
            refs=[
                ("Ubuntu Docs", "https://ubuntu.com/"),
                ("GitHub", "https://github.com/"),
            ],
        )
        metadata, slug = validate_deep_dive_content(content)
        self.assertEqual(slug, "ubuntu-swap-oom-notes")
        self.assertEqual(metadata["post_type"], "deep-dive")

    @mock.patch("generate_post.get_existing_ko_slugs", return_value=set())
    @mock.patch(
        "generate_post.find_broken_reference_urls",
        return_value=["https://example.invalid/missing"],
    )
    def test_validate_deep_dive_rejects_broken_refs(self, _broken, _existing):
        content = _deep_dive_body(
            title="Ubuntu 스왑 설정으로 OOM 줄이기",
            slug="ubuntu-swap-oom-notes",
            tags="[Ubuntu, Swap]",
            refs=[
                ("Good", "https://example.com/ok"),
                ("Bad", "https://example.invalid/missing"),
            ],
        )
        with self.assertRaises(ValueError) as ctx:
            validate_deep_dive_content(content)
        self.assertIn("참고문헌 URL이 유효하지 않습니다", str(ctx.exception))

    @mock.patch("generate_post.get_existing_ko_slugs", return_value=set())
    @mock.patch("generate_post.find_broken_reference_urls", return_value=[])
    def test_validate_deep_dive_requires_min_refs(self, _broken, _existing):
        content = _deep_dive_body(
            title="Ubuntu 스왑 설정으로 OOM 줄이기",
            slug="ubuntu-swap-oom-notes",
            tags="[Ubuntu, Swap]",
            refs=[("Only one", "https://example.com/only")],
        )
        with self.assertRaises(ValueError) as ctx:
            validate_deep_dive_content(content)
        self.assertIn(f"{MIN_REFERENCE_URLS}개 이상", str(ctx.exception))

    @mock.patch("generate_post.get_existing_ko_slugs", return_value=set())
    @mock.patch("generate_post.find_broken_reference_urls", return_value=[])
    def test_validate_rejects_banned_title(self, _broken, _existing):
        content = _deep_dive_body(
            title="Ubuntu 스왑 완벽 가이드",
            slug="ubuntu-swap-guide",
            tags="[Ubuntu]",
            refs=[
                ("Ubuntu Docs", "https://ubuntu.com/"),
                ("GitHub", "https://github.com/"),
            ],
        )
        with self.assertRaises(ValueError) as ctx:
            validate_deep_dive_content(content)
        self.assertIn("금지된 포괄 표현", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
