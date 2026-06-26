#!/usr/bin/env python3
"""Verify IndexNow key file and re-submit recent URLs."""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

from submit_indexnow import load_site_config, submit_urls

ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = (
    "Mozilla/5.0 (compatible; blog-indexnow-audit/1.0; +https://blog.jiwon.io)"
)
SLUG_FROM_FILE = re.compile(r"\d{4}-\d{2}-\d{2}-(.+)\.md$")
DEFAULT_LANG = "ko"


def recent_post_urls(site_url: str, default_lang: str, limit: int) -> list[str]:
    posts_dir = ROOT / "_posts" / default_lang
    paths = sorted(posts_dir.rglob("*.md"), reverse=True)[:limit]
    urls: list[str] = []
    for path in paths:
        match = SLUG_FROM_FILE.match(path.name)
        if not match:
            continue
        slug = match.group(1)
        urls.append(f"{site_url}/posts/{slug}/")
    return urls


def verify_key_file(site_url: str, key: str) -> bool:
    url = f"{site_url}/{key}.txt"
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace").strip()
    except urllib.error.URLError as exc:
        print(f"IndexNow key check failed: {exc}", file=sys.stderr)
        return False

    if body != key:
        print(f"IndexNow key mismatch at {url}", file=sys.stderr)
        return False

    print(f"IndexNow key file OK: {url}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--recent", type=int, default=5, help="Recent ko posts to submit.")
    parser.add_argument("--skip-submit", action="store_true")
    args = parser.parse_args()

    site_url, key, default_lang = load_site_config(args.root)
    ok = verify_key_file(site_url, key)

    if args.skip_submit:
        return 0 if ok else 1

    urls = [f"{site_url}/", *recent_post_urls(site_url, default_lang, args.recent)]
    submit_code = submit_urls(site_url, key, urls)
    return 0 if ok and submit_code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())