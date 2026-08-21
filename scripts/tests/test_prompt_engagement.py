import unittest

from generate_post import (
    BANNED_TITLE_PHRASES,
    POST_ANGLES,
    build_generation_prompt,
    generate_blog_post,
    has_application_table,
)


class PromptEngagementTests(unittest.TestCase):
    def test_has_application_table(self):
        content = """---
title: t
---
intro
<!--more-->
## 본문
내용입니다.
| 상황 | 추천 | 이유 |
| 1인 | 적용 | 빠름 |
### 참고문헌
"""
        self.assertTrue(has_application_table(content))
        self.assertFalse(has_application_table("no table here"))

    def test_banned_title_phrases_nonempty(self):
        self.assertIn("완벽 가이드", BANNED_TITLE_PHRASES)

    def test_prompt_uses_operator_topic_and_notes(self):
        prompt = build_generation_prompt(
            topic="WSL2에서 Docker Desktop 대신 엔진만 쓰기",
            angle="failure",
            notes="디스크가 90GB까지 늘었고, 재시작 후 컨테이너가 사라졌습니다.",
            recent_titles=["다른 글"],
            current_time="2026-08-21 10:00:00 +0900",
        )
        self.assertIn("WSL2에서 Docker Desktop 대신 엔진만 쓰기", prompt)
        self.assertIn("디스크가 90GB까지 늘었고", prompt)
        self.assertIn(POST_ANGLES["failure"], prompt)
        self.assertIn("주제를 바꾸거나 다른 도구로 바꾸지 마세요", prompt)
        self.assertNotIn("아직 다루지 않은 도구", prompt)

    def test_prompt_without_notes_forbids_invented_metrics(self):
        prompt = build_generation_prompt(
            topic="Nginx 캐시 히트율 보기",
            angle="freeform",
            notes="",
            recent_titles=[],
            current_time="2026-08-21 10:00:00 +0900",
        )
        self.assertIn("지어내지 마세요", prompt)
        self.assertIn("측정 필요", prompt)

    def test_generate_blog_post_requires_topic(self):
        with self.assertRaises(ValueError) as ctx:
            generate_blog_post(topic="  ")
        self.assertIn("주제", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
