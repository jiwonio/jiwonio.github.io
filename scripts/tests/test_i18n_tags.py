import unittest

from i18n_tags import build_tag_slug_translations

def _slugify(tag_name: str) -> str | None:
    """Simplified slugify matching Jekyll behavior for test fixtures."""
    slug = tag_name.strip().lower().replace(" ", "-")
    return slug or None

class BuildTagSlugTranslationsTests(unittest.TestCase):
    def test_maps_disjoint_language_specific_slugs(self):
        translations = {
            "dockerizing": {
                "ko": {"tags": ["개발 환경"]},
                "en": {"tags": ["Development Environment"]},
                "ja": {"tags": ["開発環境"]},
            }
        }
        slug_map = {
            "개발 환경": "개발-환경",
            "Development Environment": "development-environment",
            "開発環境": "開発環境",
        }

        result = build_tag_slug_translations(
            translations,
            tag_slug=lambda name: slug_map.get(name, _slugify(name)),
        )

        self.assertEqual(
            result["ko|개발-환경"],
            {"en": "development-environment", "ja": "開発環境"},
        )
        self.assertEqual(
            result["en|development-environment"],
            {"ko": "개발-환경", "ja": "開発環境"},
        )

    def test_skips_when_slugs_are_universal_across_langs(self):
        translations = {
            "shared-tech": {
                "ko": {"tags": ["Docker", "tech"]},
                "en": {"tags": ["Docker", "tech"]},
            }
        }

        result = build_tag_slug_translations(
            translations,
            tag_slug=_slugify,
        )

        self.assertEqual(result, {})

    def test_skips_overlapping_language_sets(self):
        translations = {
            "ambiguous": {
                "ko": {"tags": ["tag-a"]},
                "en": {"tags": ["tag-a", "tag-b"]},
                "ja": {"tags": ["tag-b"]},
            }
        }

        result = build_tag_slug_translations(
            translations,
            tag_slug=_slugify,
        )

        self.assertEqual(result, {})

    def test_single_language_group_produces_no_mappings(self):
        translations = {"solo": {"ko": {"tags": ["개발 환경"]}}}

        result = build_tag_slug_translations(
            translations,
            tag_slug=lambda name: "개발-환경",
        )

        self.assertEqual(result, {})

if __name__ == "__main__":
    unittest.main()
