import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_ai_news import (
    deduplicate_items,
    filter_ai_relevant_entries,
    keyword_score,
    normalize_title,
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


if __name__ == "__main__":
    unittest.main()