"""Audit AI content quality: similarity, informal style, and ai-news URL health."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

import yaml

from blog_i18n import infer_ai_generated
from post_analysis import (
    extract_body_external_urls,
    find_informal_ko_lines,
    title_similarity,
    tokenize,
)
from post_schema import FRONT_MATTER_PATTERN
from validate_posts import REF_URL_SKIP_HOSTS, check_reference_url

SITE_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = SITE_ROOT / "_posts"
SIMILARITY_THRESHOLD = 0.55
MAX_AI_NEWS_URL_CHECKS = 12
URL_CHECK_TIMEOUT = 8


def encode_url(url: str) -> str:
    parts = urlsplit(url.strip())
    path = quote(parts.path, safe="/%:@")
    query = quote(parts.query, safe="=&%?") if parts.query else parts.query
    return urlunsplit((parts.scheme, parts.netloc, path, query, parts.fragment))


def fetch_url_status(url: str) -> int | None:
    headers = {"User-Agent": "blog.jiwon.io-quality-audit/1.0"}
    encoded = encode_url(url)
    for method in ("HEAD", "GET"):
        request = Request(encoded, method=method, headers=headers)
        try:
            with urlopen(request, timeout=URL_CHECK_TIMEOUT) as response:
                return response.status
        except HTTPError as exc:
            if method == "HEAD" and exc.code in {403, 405, 429, 500, 502, 503}:
                continue
            return exc.code
        except URLError:
            if method == "HEAD":
                continue
            return None
    return None


def load_ko_posts(posts_dir: Path) -> list[tuple[Path, dict, str]]:
    posts: list[tuple[Path, dict, str]] = []
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
            posts.append((path, metadata, content))
    return posts


def audit_title_similarity(posts: list[tuple[Path, dict, str]]) -> list[str]:
    warnings: list[str] = []
    entries = []
    for path, metadata, _content in posts:
        title = str(metadata.get("title", "")).strip()
        slug = str(metadata.get("slug") or path.stem[11:]).strip()
        entries.append((path, title, slug))

    for index, (left_path, left_title, left_slug) in enumerate(entries):
        left_text = f"{left_title} {left_slug}"
        for right_path, right_title, right_slug in entries[index + 1 :]:
            score = title_similarity(left_text, f"{right_title} {right_slug}")
            if score >= SIMILARITY_THRESHOLD:
                warnings.append(
                    f"similar topics ({score:.2f}): {left_path.name} ↔ {right_path.name}"
                )
    return warnings


def audit_informal_style(posts: list[tuple[Path, dict, str]]) -> list[str]:
    warnings: list[str] = []
    for path, metadata, content in posts:
        if not infer_ai_generated(metadata, path):
            continue
        informal_lines = find_informal_ko_lines(content)
        if informal_lines:
            sample = informal_lines[0]
            warnings.append(
                f"informal Korean style in {path.name}: '{sample}'"
                + (f" (+{len(informal_lines) - 1} more)" if len(informal_lines) > 1 else "")
            )
    return warnings


def audit_ai_news_urls(posts: list[tuple[Path, dict, str]]) -> list[str]:
    warnings: list[str] = []
    checked: dict[str, str | None] = {}

    for path, metadata, content in posts:
        if str(metadata.get("post_type", "")).strip() != "ai-news":
            continue

        urls = []
        for url in extract_body_external_urls(content):
            host = urlsplit(url).netloc.lower()
            if host in REF_URL_SKIP_HOSTS:
                continue
            if url not in urls:
                urls.append(url)
            if len(urls) >= MAX_AI_NEWS_URL_CHECKS:
                break

        for url in urls:
            if url not in checked:
                checked[url] = check_reference_url(url)
            error = checked[url]
            if error:
                warnings.append(f"ai-news URL issue in {path.name}: {error} for {url}")
    return warnings


def audit_slug_token_overlap(posts: list[tuple[Path, dict, str]]) -> list[str]:
    """Flag repeated slug tokens across AI-generated posts."""
    warnings: list[str] = []
    token_posts: dict[str, list[str]] = {}

    for path, metadata, _content in posts:
        if not infer_ai_generated(metadata, path):
            continue
        slug = str(metadata.get("slug") or path.stem[11:]).strip()
        for token in tokenize(slug.replace("-", " ")):
            token_posts.setdefault(token, []).append(path.name)

    for token, names in sorted(token_posts.items()):
        unique_names = sorted(set(names))
        if len(unique_names) >= 4:
            warnings.append(
                f"overused slug token '{token}' in {len(unique_names)} AI posts"
            )
    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit AI content quality signals")
    parser.add_argument("--posts-dir", type=Path, default=POSTS_DIR)
    parser.add_argument(
        "--skip-url-check",
        action="store_true",
        help="Skip live ai-news URL HEAD checks",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when warnings are found",
    )
    args = parser.parse_args(argv)

    posts = load_ko_posts(args.posts_dir)
    warnings: list[str] = []
    warnings.extend(audit_title_similarity(posts))
    warnings.extend(audit_informal_style(posts))
    warnings.extend(audit_slug_token_overlap(posts))
    if not args.skip_url_check:
        warnings.extend(audit_ai_news_urls(posts))

    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        print(f"Content quality audit finished with {len(warnings)} warning(s).")
        return 1 if args.strict else 0

    print("Content quality audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())