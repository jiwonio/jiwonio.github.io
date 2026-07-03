import unittest

from generate_ai_news import (
    bullet_has_action_hint,
    deduplicate_items,
    ensure_action_bullet,
    filter_ai_relevant_entries,
    find_plain_da_tone_violations,
    keyword_score,
    normalize_title,
    repair_ai_news_front_matter,
    repair_korean_formal_tone,
    repair_summary_action_bullets,
    title_similarity,
)

class GenerateAiNewsTests(unittest.TestCase):
    def test_normalize_title_strips_punctuation(self):
        self.assertEqual(normalize_title("  OpenAI: Codex!! "), "openai codex")

    def test_title_similarity_detects_overlap(self):
        score = title_similarity("OpenAI releases new coding agent", "New coding agent from OpenAI")
        self.assertGreaterEqual(score, 0.5)

    def test_keyword_score_prefers_developer_terms(self):
        positive = keyword_score("AWS Lambda Kubernetes developer workflow")
        negative = keyword_score("celebrity gossip fashion sale")
        self.assertGreater(positive, negative)

    def test_filter_ai_relevant_entries_for_ai_feed(self):
        entries = [
            {"title": "New GPU cluster", "summary": "CUDA training"},
            {"title": "Local bakery opens", "summary": "bread and cakes"},
        ]
        filtered = filter_ai_relevant_entries(entries, "GitHub Blog")
        self.assertEqual(len(filtered), 1)

    def test_deduplicate_items_removes_duplicate_urls(self):
        items = [
            {"title": "OpenAI Codex update", "url": "https://example.com/post", "tier": 1, "summary": "agent"},
            {"title": "Different title", "url": "https://example.com/post", "tier": 1, "summary": "agent"},
        ]
        deduped = deduplicate_items(items)
        self.assertEqual(len(deduped), 1)

    def test_find_plain_da_tone_violations_detects_plain_style(self):
        prose = (
            "이번 주는 에이전트 인프라가 한 단계 구체화된 한 주였다.\n"
            "- **Copilot**: 컨텍스트 필터링이 개선되어 체감 품질이 좋아질 수 있다\n"
        )
        violations = find_plain_da_tone_violations(prose)
        self.assertIn("였다", violations)

    def test_find_plain_da_tone_violations_allows_formal_style(self):
        prose = (
            "이번 주는 에이전트 인프라가 한 단계 더 구체화된 한 주였습니다.\n"
            "- **Copilot**: 컨텍스트 필터링이 개선되어 체감 품질이 좋아질 수 있습니다.\n"
        )
        self.assertEqual(find_plain_da_tone_violations(prose), [])

    def test_repair_korean_formal_tone_fixes_yo_and_da_endings(self):
        content = (
            "---\nlayout: post\n---\n"
            "이번 주는 변화가 많았다.\n"
            "- **LangChain**: 에이전트 런타임이 정리됐어요.\n"
        )
        repaired = repair_korean_formal_tone(content)
        self.assertIn("많았습니다", repaired)
        self.assertIn("정리됐습니다", repaired)
        self.assertNotIn("많았다.", repaired)
        self.assertNotIn("정리됐어요", repaired)

    def test_ensure_action_bullet_prefixes_noun_only_line(self):
        bullet = "GitHub Copilot 보안 샌드박스 정책 변경"
        repaired = ensure_action_bullet(bullet)
        self.assertTrue(bullet_has_action_hint(repaired))

    def test_repair_summary_action_bullets_adds_action_verbs(self):
        content = """---
title: t
---
intro
<!--more-->
## 1. News
body
## 이번 주 한 줄 정리
- GitHub Copilot 보안 샌드박스 정책 변경
- LangChain 1.0 에이전트 런타임 정리
- API 가격 변경 공지
### 참고문헌
- [x](https://example.com)
"""
        repaired = repair_summary_action_bullets(content)
        bullets = repaired.split("## 이번 주 한 줄 정리", 1)[1].split("### 참고문헌")[0]
        self.assertGreaterEqual(bullets.count("확인"), 1)

    def test_repair_ai_news_front_matter_rebuilds_invalid_yaml(self):
        broken = """---
코딩 에이전트가 바뀌었다.
<!--more-->
[HERO_IMAGE]
-----
## 1. News
"""
        repaired = repair_ai_news_front_matter(
            broken,
            slug="ai-news-2026-07-03",
            current_time="2026-07-03 00:00:00 +0900",
        )
        self.assertIn('slug: ai-news-2026-07-03', repaired)
        self.assertIn("layout: post", repaired)
        self.assertIn("## 1. News", repaired)

if __name__ == "__main__":
    unittest.main()
