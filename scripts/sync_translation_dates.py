"""translation_key 그룹의 날짜를 원문(ko) 기준으로 맞춥니다."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from blog_i18n import (
    DEFAULT_LANG,
    POSTS_DIR,
    detect_lang_from_path,
    dump_front_matter,
    explicit_post_date,
    parse_front_matter,
    resolve_effective_date,
    resolve_slug,
)

ROOT = Path(__file__).resolve().parent.parent


def load_groups() -> dict[str, dict[str, Path]]:
    groups: dict[str, dict[str, Path]] = defaultdict(dict)
    for path in sorted(POSTS_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8")
        metadata = parse_front_matter(content)
        key = metadata.get("translation_key") or resolve_slug(path, metadata)
        lang = metadata.get("lang") or detect_lang_from_path(path)
        groups[key][lang] = path
    return groups


def sync_group(key: str, paths: dict[str, Path], dry_run: bool) -> int:
    source_path = paths.get(DEFAULT_LANG)
    if not source_path:
        return 0

    source_meta = parse_front_matter(source_path.read_text(encoding="utf-8"))
    source_date = explicit_post_date(source_meta)
    source_effective = resolve_effective_date(source_path, source_meta)
    changed = 0

    for lang, path in paths.items():
        if lang == DEFAULT_LANG:
            continue

        content = path.read_text(encoding="utf-8")
        metadata = parse_front_matter(content)
        current_effective = resolve_effective_date(path, metadata)

        if current_effective == source_effective and (
            (source_date is None and "date" not in metadata)
            or (source_date is not None and metadata.get("date") == source_date)
        ):
            continue

        if source_date:
            metadata["date"] = source_date
        else:
            metadata.pop("date", None)

        body = content.split("---", 2)[2]
        updated = dump_front_matter(metadata) + body
        rel = path.relative_to(ROOT)
        print(f"[sync] {rel}: {current_effective} -> {source_effective}")
        if not dry_run:
            path.write_text(updated, encoding="utf-8")
        changed += 1

    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync translation post dates from Korean source posts.")
    parser.add_argument("--dry-run", action="store_true", help="변경 없이 대상만 출력")
    args = parser.parse_args()

    total = 0
    for key, paths in sorted(load_groups().items()):
        if len(paths) < 2:
            continue
        total += sync_group(key, paths, args.dry_run)

    if total == 0:
        print("No date changes needed.")
        return 0

    print(f"{'Would update' if args.dry_run else 'Updated'} {total} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())