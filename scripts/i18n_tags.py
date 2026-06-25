"""Mirror of _plugins/i18n.rb tag slug translation logic for unit tests."""

from __future__ import annotations

from typing import Callable


def build_tag_slug_translations(
    translations: dict[str, dict[str, dict]],
    *,
    tag_slug: Callable[[str], str | None],
) -> dict[str, dict[str, str]]:
    """Build lang|slug -> {target_lang: target_slug} map from translation groups."""
    result: dict[str, dict[str, str]] = {}

    for _key, lang_posts in translations.items():
        if len(lang_posts) < 2:
            continue

        slugs_by_lang: dict[str, list[tuple[str, str]]] = {}
        for lang, post in lang_posts.items():
            pairs: list[tuple[str, str]] = []
            seen_slugs: set[str] = set()
            for tag_name in post.get("tags", []):
                slug = tag_slug(str(tag_name))
                if not slug or slug in seen_slugs:
                    continue
                seen_slugs.add(slug)
                pairs.append((str(tag_name), slug))
            slugs_by_lang[lang] = pairs

        all_langs = sorted(slugs_by_lang)
        slug_langs: dict[str, list[str]] = {}
        for lang, pairs in slugs_by_lang.items():
            for _, slug in pairs:
                slug_langs.setdefault(slug, [])
                if lang not in slug_langs[slug]:
                    slug_langs[slug].append(lang)

        all_slugs = list(slug_langs)
        universal_slugs = [
            slug for slug in all_slugs if sorted(slug_langs[slug]) == all_langs
        ]
        non_universal_slugs = [slug for slug in all_slugs if slug not in universal_slugs]
        if not non_universal_slugs:
            continue

        lang_sets = {slug: sorted(slug_langs[slug]) for slug in non_universal_slugs}
        disjoint = all(
            not (set(left) & set(right))
            for left in lang_sets.values()
            for right in lang_sets.values()
            if left is not right
        )
        covered_langs = sorted({lang for langs in lang_sets.values() for lang in langs})
        if not disjoint or covered_langs != all_langs:
            continue

        for from_slug, from_langs in lang_sets.items():
            for from_lang in from_langs:
                for to_slug in lang_sets:
                    if from_slug == to_slug:
                        continue
                    for to_lang in slug_langs[to_slug]:
                        if from_lang == to_lang:
                            continue
                        key = f"{from_lang}|{from_slug}"
                        result.setdefault(key, {})
                        result[key][to_lang] = to_slug

    return result