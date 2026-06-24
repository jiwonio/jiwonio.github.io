"""
배포된 새·변경 포스트 URL을 IndexNow API에 제출합니다.

사용법:
    python scripts/submit_indexnow.py --from-git <before_sha> <after_sha>
    python scripts/submit_indexnow.py --url https://blog.jiwon.io/posts/example/
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parent.parent
FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
SLUG_FROM_FILE = re.compile(r"\d{4}-\d{2}-\d{2}-(.+)\.md$")
LANG_PATH = re.compile(r"(?:^|/)_posts/(en|ja|zh|ko)(?:/|$)")
DEFAULT_LANG = "ko"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
INVALID_BEFORE_SHA = "0" * 40


def load_site_config(root: Path) -> tuple[str, str, str]:
    config = yaml.safe_load((root / "_config.yml").read_text(encoding="utf-8"))
    site_url = str(config["url"]).rstrip("/")
    key = str(config.get("seo", {}).get("indexnow_key", "")).strip()
    default_lang = str(config.get("default_lang", DEFAULT_LANG)).strip() or DEFAULT_LANG
    return site_url, key, default_lang


def detect_lang(path: Path, metadata: dict) -> str:
    if metadata.get("lang"):
        return str(metadata["lang"]).strip()
    match = LANG_PATH.search(path.as_posix())
    if match:
        return match.group(1)
    return DEFAULT_LANG


def resolve_post_slug(path: Path, metadata: dict) -> str:
    if metadata.get("slug"):
        return str(metadata["slug"]).strip()
    match = SLUG_FROM_FILE.match(path.name)
    if match:
        return match.group(1)
    return re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-")


def post_public_url(site_url: str, slug: str, lang: str, default_lang: str = DEFAULT_LANG) -> str:
    if lang == default_lang:
        return f"{site_url}/posts/{slug}/"
    return f"{site_url}/{lang}/posts/{slug}/"


def post_public_url_from_path(site_url: str, path: Path, default_lang: str = DEFAULT_LANG) -> str:
    content = path.read_text(encoding="utf-8")
    match = FRONT_MATTER_PATTERN.match(content)
    if not match:
        raise ValueError(f"missing front matter: {path}")

    metadata = yaml.safe_load(match.group(1))
    if not isinstance(metadata, dict):
        raise ValueError(f"invalid front matter: {path}")

    slug = resolve_post_slug(path, metadata)
    lang = detect_lang(path, metadata)
    return post_public_url(site_url, slug, lang, default_lang)


def load_translation_groups(posts_dir: Path) -> dict[str, dict[str, Path]]:
    groups: dict[str, dict[str, Path]] = defaultdict(dict)
    for path in sorted(posts_dir.rglob("*.md")):
        content = path.read_text(encoding="utf-8")
        match = FRONT_MATTER_PATTERN.match(content)
        if not match:
            continue
        metadata = yaml.safe_load(match.group(1))
        if not isinstance(metadata, dict):
            continue
        slug = resolve_post_slug(path, metadata)
        key = str(metadata.get("translation_key") or slug).strip()
        lang = detect_lang(path, metadata)
        groups[key][lang] = path
    return groups


def git_changed_post_paths(before_sha: str, after_sha: str, root: Path) -> list[Path]:
    if not before_sha or before_sha == INVALID_BEFORE_SHA:
        print("No previous commit to compare; skipping IndexNow.")
        return []

    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=AM",
            before_sha,
            after_sha,
            "--",
            "_posts",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [root / line for line in result.stdout.splitlines() if line.endswith(".md")]


def collect_group_urls(
    changed_paths: list[Path],
    posts_dir: Path,
    site_url: str,
    default_lang: str,
) -> list[str]:
    groups = load_translation_groups(posts_dir)
    urls: list[str] = []

    for changed in changed_paths:
        try:
            content = changed.read_text(encoding="utf-8")
            match = FRONT_MATTER_PATTERN.match(content)
            metadata = yaml.safe_load(match.group(1)) if match else {}
            slug = resolve_post_slug(changed, metadata if isinstance(metadata, dict) else {})
            key = str((metadata or {}).get("translation_key") or slug).strip()
        except (OSError, UnicodeError, yaml.YAMLError):
            continue

        siblings = groups.get(key, {})
        if siblings:
            for lang, path in sorted(siblings.items()):
                try:
                    urls.append(post_public_url_from_path(site_url, path, default_lang))
                except (OSError, UnicodeError, yaml.YAMLError, ValueError) as exc:
                    print(f"WARNING: {path}: {exc}", file=sys.stderr)
        else:
            try:
                urls.append(post_public_url_from_path(site_url, changed, default_lang))
            except (OSError, UnicodeError, yaml.YAMLError, ValueError) as exc:
                print(f"WARNING: {changed}: {exc}", file=sys.stderr)

    return list(dict.fromkeys(urls))


def submit_urls(site_url: str, key: str, urls: list[str]) -> int:
    if not key:
        print("IndexNow key is not configured; skipping.")
        return 0

    if not urls:
        print("No new post URLs to submit.")
        return 0

    host = urlparse(site_url).netloc
    payload = {
        "host": host,
        "key": key,
        "keyLocation": f"{site_url}/{key}.txt",
        "urlList": urls,
    }
    request = urllib.request.Request(
        INDEXNOW_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"IndexNow request failed: HTTP {exc.code} {body}", file=sys.stderr)
        return 1

    print(f"IndexNow accepted {len(urls)} URL(s); HTTP {status}")
    for url in urls:
        print(f"  - {url}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit new blog post URLs to IndexNow.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--from-git", nargs=2, metavar=("BEFORE", "AFTER"))
    parser.add_argument("--url", action="append", dest="urls")
    args = parser.parse_args()

    site_url, key, default_lang = load_site_config(args.root)
    urls: list[str] = list(args.urls or [])

    if args.from_git:
        before_sha, after_sha = args.from_git
        changed_paths = git_changed_post_paths(before_sha, after_sha, args.root)
        urls.extend(
            collect_group_urls(
                changed_paths,
                args.root / "_posts",
                site_url,
                default_lang,
            )
        )

    urls = list(dict.fromkeys(urls))
    return submit_urls(site_url, key, urls)


if __name__ == "__main__":
    raise SystemExit(main())