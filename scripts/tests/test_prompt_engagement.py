import unittest

from generate_ai_news import (
    annotate_items_with_ids,
    bullet_has_action_hint,
    extract_summary_bullets,
    fallback_edition_plan,
    item_relevance_score,
    parse_selection_json,
    resolve_selected_items,
    section_has_judgment,
)
from generate_post import has_application_table, BANNED_TITLE_PHRASES
from feeds_config import PRACTICAL_KEYWORDS


class PromptEngagementTests(unittest.TestCase):
    def test_item_relevance_score_boosts_practical_terms(self):
        practical = item_relevance_score(
            {"title": "OpenAI API pricing update", "summary": "security and deployment"}
        )
        fluff = item_relevance_score(
            {"title": "Celebrity gossip", "summary": "funding raises billion valuation"}
        )
        self.assertGreater(practical, fluff)

    def test_annotate_items_with_ids(self):
        items = annotate_items_with_ids([{"title": "A", "url": "https://a"}])
        self.assertEqual(items[0]["id"], 1)

    def test_parse_selection_json_from_fence(self):
        raw = '```json\n{"theme_question": "q", "primary_reader": "백엔드", "selected_ids": [1, 2, 3, 4, 5]}\n```'
        plan = parse_selection_json(raw)
        self.assertEqual(plan["selected_ids"], [1, 2, 3, 4, 5])

    def test_resolve_selected_items_respects_ids(self):
        ranked = [
            {"title": "A", "url": "https://a"},
            {"title": "B", "url": "https://b"},
            {"title": "C", "url": "https://c"},
            {"title": "D", "url": "https://d"},
            {"title": "E", "url": "https://e"},
        ]
        plan = {"selected_ids": [2, 4, 1, 5, 3]}
        selected = resolve_selected_items(ranked, plan)
        self.assertEqual(len(selected), 5)
        self.assertEqual(selected[0]["title"], "B")

    def test_fallback_edition_plan_returns_enough_items(self):
        ranked = [{"title": f"Item {i}", "url": f"https://ex/{i}"} for i in range(8)]
        plan, selected = fallback_edition_plan(ranked)
        self.assertGreaterEqual(len(selected), 5)
        self.assertIn("theme_question", plan)

    def test_extract_summary_bullets(self):
        content = """---
title: t
---
intro
<!--more-->
## 1. News
body
## 이번 주 한 줄 정리
- 팀 프롬프트 템플릿을 버전 관리하세요
- API 가격 변경을 확인하세요
- 에이전트 로그를 점검하세요
### 참고문헌
- [x](https://x)
"""
        bullets = extract_summary_bullets(content)
        self.assertEqual(len(bullets), 3)
        self.assertTrue(bullet_has_action_hint(bullets[0]))

    def test_section_has_judgment(self):
        block = "**이번 주 판단:** 이번 주는 관망이 맞습니다."
        self.assertTrue(section_has_judgment(block))
        self.assertFalse(section_has_judgment("**이번 주 판단:** 좋아 보입니다."))

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

    def test_practical_keywords_defined(self):
        self.assertIn("pricing", PRACTICAL_KEYWORDS)

    def test_banned_title_phrases_nonempty(self):
        self.assertIn("완벽 가이드", BANNED_TITLE_PHRASES)


if __name__ == "__main__":
    unittest.main()