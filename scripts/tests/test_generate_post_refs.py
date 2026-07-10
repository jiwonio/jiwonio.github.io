import unittest
from unittest import mock

from generate_post import MIN_REFERENCE_URLS, validate_deep_dive_content


def _deep_dive_body(*, refs: list[tuple[str, str]]) -> str:
    ref_lines = "\n".join(
        f'- [{title}]({url}){{:target="_blank"}}' for title, url in refs
    )
    return f"""---
layout: post
title: "Cursor로 PR 리뷰 밀림 줄이기: 체크리스트 한 장"
slug: "cursor-pr-review-checklist-workflow"
lang: ko
translation_key: "cursor-pr-review-checklist-workflow"
post_type: deep-dive
date: 2026-07-10 09:00:00 +0900
categories: [AI]
tags: [Cursor, Code Review, Workflow]
description: "Cursor로 PR 리뷰 병목을 줄이는 실무 체크리스트를 정리합니다."
image: "/uploads/cursor-pr-review-checklist-workflow/thumbnail.webp"
---
PR 리뷰가 밀리는 상황에서 Cursor를 쓰는 방법을 정리합니다.

두번째 문단입니다. 팀 온보딩 때 바로 쓸 수 있습니다.

세 번째 문단: 이 글을 읽으면 리뷰 체크리스트를 팀에 맞출 수 있습니다.
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
    @mock.patch("generate_post.get_existing_ko_slugs", return_value=set())
    @mock.patch("generate_post.get_recent_titles", return_value=[])
    @mock.patch("generate_post.get_recent_slugs", return_value=[])
    @mock.patch("generate_post.find_broken_reference_urls", return_value=[])
    def test_validate_deep_dive_accepts_live_refs(
        self,
        _broken,
        _slugs,
        _titles,
        _existing,
    ):
        content = _deep_dive_body(
            refs=[
                ("Cursor Docs", "https://docs.cursor.com/"),
                ("GitHub", "https://github.com/"),
            ]
        )
        metadata, slug = validate_deep_dive_content(content)
        self.assertEqual(slug, "cursor-pr-review-checklist-workflow")
        self.assertEqual(metadata["post_type"], "deep-dive")

    @mock.patch("generate_post.get_existing_ko_slugs", return_value=set())
    @mock.patch("generate_post.get_recent_titles", return_value=[])
    @mock.patch("generate_post.get_recent_slugs", return_value=[])
    @mock.patch(
        "generate_post.find_broken_reference_urls",
        return_value=["https://example.invalid/missing"],
    )
    def test_validate_deep_dive_rejects_broken_refs(
        self,
        _broken,
        _slugs,
        _titles,
        _existing,
    ):
        content = _deep_dive_body(
            refs=[
                ("Good", "https://example.com/ok"),
                ("Bad", "https://example.invalid/missing"),
            ]
        )
        with self.assertRaises(ValueError) as ctx:
            validate_deep_dive_content(content)
        self.assertIn("참고문헌 URL이 유효하지 않습니다", str(ctx.exception))

    @mock.patch("generate_post.get_existing_ko_slugs", return_value=set())
    @mock.patch("generate_post.get_recent_titles", return_value=[])
    @mock.patch("generate_post.get_recent_slugs", return_value=[])
    @mock.patch("generate_post.find_broken_reference_urls", return_value=[])
    def test_validate_deep_dive_requires_min_refs(
        self,
        _broken,
        _slugs,
        _titles,
        _existing,
    ):
        content = _deep_dive_body(
            refs=[("Only one", "https://example.com/only")]
        )
        with self.assertRaises(ValueError) as ctx:
            validate_deep_dive_content(content)
        self.assertIn(f"{MIN_REFERENCE_URLS}개 이상", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
