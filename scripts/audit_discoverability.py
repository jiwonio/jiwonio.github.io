"""Audit search index coverage, internal linking, and ai-news discoverability."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from post_analysis import build_internal_link_graph, pagefind_language_counts
from post_schema import FRONT_MATTER_PATTERN

SITE_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = SITE_ROOT / "_posts"
MIN_PAGEFIND_FRAGMENTS = 3
MIN_INBOUND_LINKS = 1


def load_ko_posts(posts_dir: Path) -> list[tuple[Path, dict]]:
    posts: list[tuple[Path, dict]] = []
    for path in sorted(posts_dir.rglob("*.md")):
        if "/ko/" not in path.as_posix() and not path.as_posix().startswith("_posts/ko/"):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        match = FRONT_MATTER_PATTERN.match(content)
        if not match:
            continue
        metadata = yaml.safe_load(match.group(1)) or {}
        if isinstance(metadata, dict):
            posts.append((path, metadata))
    return posts


def audit_pagefind(site_dir: Path) -> list[str]:
    warnings: list[str] = []
    counts = pagefind_language_counts(site_dir)
    if not counts:
        warnings.append(
            f"Pagefind index not found under {site_dir / 'pagefind'} "
            "(run Jekyll build + Pagefind first)"
        )
        return warnings

    for lang in ("ko", "en", "ja", "zh"):
        fragment_count = counts.get(lang, 0)
        if fragment_count < MIN_PAGEFIND_FRAGMENTS:
            warnings.append(
                f"Pagefind lang '{lang}' has only {fragment_count} indexed fragments "
                f"(expected >= {MIN_PAGEFIND_FRAGMENTS})"
            )
    return warnings


def collect_link_health(posts_dir: Path, *, hub_limit: int = 5) -> dict:
    inbound, slug_paths = build_internal_link_graph(posts_dir)
    orphans: list[dict[str, str]] = []
    for slug, path in sorted(slug_paths.items()):
        sources = inbound.get(slug, set())
        if len(sources) < MIN_INBOUND_LINKS:
            orphans.append({"slug": slug, "file": path.name})

    hubs = sorted(
        ((slug, len(inbound.get(slug, set()))) for slug in slug_paths),
        key=lambda item: item[1],
        reverse=True,
    )[:hub_limit]

    return {
        "total_posts": len(slug_paths),
        "orphan_count": len(orphans),
        "orphans_sample": orphans[:8],
        "top_hubs": [{"slug": slug, "inbound": count} for slug, count in hubs if count > 0],
    }


def audit_internal_links(posts_dir: Path) -> list[str]:
    warnings: list[str] = []
    inbound, slug_paths = build_internal_link_graph(posts_dir)

    for slug, path in sorted(slug_paths.items()):
        sources = inbound.get(slug, set())
        if len(sources) < MIN_INBOUND_LINKS:
            warnings.append(
                f"orphan post (no inbound /posts/ links): {slug} ({path.name})"
            )

    health = collect_link_health(posts_dir)
    if health["top_hubs"]:
        summary = ", ".join(
            f"{hub['slug']}({hub['inbound']})" for hub in health["top_hubs"]
        )
        print(f"Top linked posts: {summary}")

    return warnings


def audit_ai_news_series(posts_dir: Path) -> list[str]:
    warnings: list[str] = []
    ai_news_posts = 0
    tagged_ai_news = 0

    for path, metadata in load_ko_posts(posts_dir):
        post_type = str(metadata.get("post_type", "")).strip()
        tags = {str(tag).casefold() for tag in metadata.get("tags") or []}
        if post_type == "ai-news":
            ai_news_posts += 1
        if "ai-news" in tags:
            tagged_ai_news += 1

    if ai_news_posts == 0:
        warnings.append("no ko ai-news posts found")
    elif tagged_ai_news < ai_news_posts:
        warnings.append(
            f"ai-news tag missing on {ai_news_posts - tagged_ai_news} of {ai_news_posts} ai-news posts"
        )

    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit blog discoverability signals")
    parser.add_argument("--posts-dir", type=Path, default=POSTS_DIR)
    parser.add_argument(
        "--site-dir",
        type=Path,
        default=SITE_ROOT / "_site",
        help="Built site directory for Pagefind checks",
    )
    parser.add_argument(
        "--skip-pagefind",
        action="store_true",
        help="Skip Pagefind index checks",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when warnings are found",
    )
    args = parser.parse_args(argv)

    warnings: list[str] = []
    if not args.skip_pagefind:
        warnings.extend(audit_pagefind(args.site_dir))
    warnings.extend(audit_internal_links(args.posts_dir))
    warnings.extend(audit_ai_news_series(args.posts_dir))

    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        print(f"Discoverability audit finished with {len(warnings)} warning(s).")
        return 1 if args.strict else 0

    print("Discoverability audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())