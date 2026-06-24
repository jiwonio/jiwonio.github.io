#!/usr/bin/env python3
"""
기존 한국어(기본) 포스트의 en/ja/zh 번역을 백필합니다.

사용법:
    python scripts/backfill_translations.py --prepare          # 메타데이터 정규화만
    python scripts/backfill_translations.py --limit 5          # 5개 포스트 × 누락 언어
    python scripts/backfill_translations.py --slug my-post     # 특정 slug만
    python scripts/backfill_translations.py --langs en,ja      # 특정 언어만
    python scripts/backfill_translations.py --dry-run          # 대상만 출력
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from blog_i18n import (
    DEFAULT_LANG,
    TRANSLATION_LANGS,
    LANG_LABELS,
    detect_lang_from_path,
    dump_front_matter,
    ensure_updated_field,
    generate_translation,
    infer_ai_generated,
    infer_categories,
    parse_front_matter,
    prepare_ko_post_content,
    resolve_slug,
    translation_langs_for_metadata,
    translation_output_path,
    FRONT_MATTER_PATTERN,
)

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "_posts"


def list_ko_posts() -> list[Path]:
    return [
        path
        for path in sorted(POSTS_DIR.rglob("*.md"))
        if detect_lang_from_path(path) == DEFAULT_LANG
    ]


def missing_translations(
    source_path: Path,
    langs: tuple[str, ...],
    *,
    metadata: dict | None = None,
) -> list[str]:
    if metadata is None:
        metadata = parse_front_matter(source_path.read_text(encoding="utf-8"))
    allowed = set(translation_langs_for_metadata(metadata))
    return [
        lang
        for lang in langs
        if lang in allowed and not translation_output_path(source_path, lang).exists()
    ]


def prepare_translation_post_content(path: Path, source_metadata: dict, source_path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    metadata = parse_front_matter(content)
    metadata["categories"] = infer_categories({**metadata, "categories": metadata.get("categories") or source_metadata.get("categories")})
    if not metadata.get("post_type") and source_metadata.get("post_type"):
        metadata["post_type"] = source_metadata["post_type"]
    if infer_ai_generated(source_metadata, source_path):
        metadata["ai_generated"] = True
    elif "ai_generated" in source_metadata:
        metadata["ai_generated"] = source_metadata["ai_generated"]
    ensure_updated_field(metadata, path)
    return dump_front_matter(metadata) + content[FRONT_MATTER_PATTERN.match(content).end() :]


def prepare_posts(posts: list[Path], *, dry_run: bool) -> int:
    updated = 0
    for path in posts:
        new_content = prepare_ko_post_content(path)
        old_content = path.read_text(encoding="utf-8")
        if new_content != old_content:
            if dry_run:
                print(f"[prepare] would update {path.relative_to(ROOT)}")
            else:
                path.write_text(new_content, encoding="utf-8")
                print(f"[prepare] updated {path.relative_to(ROOT)}")
            updated += 1

        source_metadata = parse_front_matter(new_content if new_content != old_content else old_content)
        for lang in TRANSLATION_LANGS:
            translation_path = translation_output_path(path, lang)
            if not translation_path.exists():
                continue
            translated_content = prepare_translation_post_content(translation_path, source_metadata, path)
            old_translation = translation_path.read_text(encoding="utf-8")
            if translated_content == old_translation:
                continue
            if dry_run:
                print(f"[prepare] would update {translation_path.relative_to(ROOT)}")
            else:
                translation_path.write_text(translated_content, encoding="utf-8")
                print(f"[prepare] updated {translation_path.relative_to(ROOT)}")
            updated += 1
    return updated


def backfill(
    posts: list[Path],
    langs: tuple[str, ...],
    *,
    dry_run: bool,
    sleep_seconds: float,
    translation_provider: str | None = None,
) -> tuple[int, int]:
    created = 0
    skipped = 0
    failures = 0

    for index, source_path in enumerate(posts, start=1):
        source_content = source_path.read_text(encoding="utf-8")
        metadata = parse_front_matter(source_content)
        slug = resolve_slug(source_path, metadata)
        pending_langs = missing_translations(source_path, langs, metadata=metadata)

        if not pending_langs:
            print(f"[{index}/{len(posts)}] skip (complete): {slug}")
            skipped += 1
            continue

        print(f"[{index}/{len(posts)}] {slug} → {', '.join(pending_langs)}")

        if dry_run:
            for lang in pending_langs:
                out = translation_output_path(source_path, lang)
                print(f"  would create {out.as_posix()}")
            continue

        for lang in pending_langs:
            print(f"  🌐 {LANG_LABELS[lang]} ({lang})...")
            try:
                output = generate_translation(
                    source_content,
                    source_path,
                    lang,
                    translation_provider=translation_provider,
                )
                print(f"  ✅ {output.as_posix()}")
                created += 1
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
            except Exception as exc:
                failures += 1
                print(f"  ⚠️ {lang} 실패 ({slug}): {exc}")

    return created, skipped, failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill blog post translations.")
    parser.add_argument("--prepare", action="store_true", help="Normalize ko metadata only.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without API calls.")
    parser.add_argument("--limit", type=int, default=0, help="Max source posts (0 = all).")
    parser.add_argument("--slug", type=str, default="", help="Process a single slug.")
    parser.add_argument("--langs", type=str, default=",".join(TRANSLATION_LANGS))
    parser.add_argument("--sleep", type=float, default=5.0, help="Seconds between API calls.")
    parser.add_argument(
        "--translation-provider",
        choices=["gemini", "anthropic", "openai", "xai"],
        help="번역에 사용할 LLM provider (기본: 번역 폴백 체인)",
    )
    args = parser.parse_args()

    langs = tuple(lang.strip() for lang in args.langs.split(",") if lang.strip())
    invalid = [lang for lang in langs if lang not in TRANSLATION_LANGS]
    if invalid:
        print(f"ERROR: unsupported langs: {', '.join(invalid)}", file=sys.stderr)
        return 1

    posts = list_ko_posts()
    if args.slug:
        posts = [p for p in posts if resolve_slug(p) == args.slug]
        if not posts:
            print(f"ERROR: slug not found: {args.slug}", file=sys.stderr)
            return 1
    if args.limit > 0:
        posts = posts[: args.limit]

    print(f"Found {len(posts)} source post(s).")

    prepared = prepare_posts(posts, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"Prepared {prepared} post(s).")

    if args.prepare:
        return 0

    created, skipped, failures = backfill(
        posts,
        langs,
        dry_run=args.dry_run,
        sleep_seconds=args.sleep,
        translation_provider=args.translation_provider,
    )
    print(f"Done. created={created}, skipped_complete={skipped}, failures={failures}")

    if not args.dry_run and failures > 0:
        print("ERROR: one or more translations failed.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())