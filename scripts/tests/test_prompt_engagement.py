import unittest

from generate_post import has_application_table, BANNED_TITLE_PHRASES


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


if __name__ == "__main__":
    unittest.main()
