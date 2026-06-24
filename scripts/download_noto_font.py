#!/usr/bin/env python3
"""Download Noto Sans woff2 files for self-hosted fonts."""

from __future__ import annotations

import argparse
import re
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PRELOAD_DATA = ROOT / "_data" / "noto_preload.yml"
# Chrome UA so Google Fonts serves woff2 instead of ttf.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

FAMILIES: dict[str, dict[str, str]] = {
    "Noto+Sans+KR": {
        "dir": "noto-sans-kr",
        "css_name": "noto-sans-kr.css",
        "lang": "ko",
    },
    "Noto+Sans+JP": {
        "dir": "noto-sans-jp",
        "css_name": "noto-sans-jp.css",
        "lang": "ja",
    },
    "Noto+Sans+SC": {
        "dir": "noto-sans-sc",
        "css_name": "noto-sans-sc.css",
        "lang": "zh",
    },
}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def filename_from_url(url: str) -> str:
    return url.split("/")[-1].split("?")[0]


def first_preload_face(css: str) -> str | None:
    blocks = re.findall(r"@font-face\s*\{([^}]+)\}", css, flags=re.DOTALL)
    for block in blocks:
        if "font-weight: 400" not in block:
            continue
        url_match = re.search(r"url\(([^)]+)\)", block)
        if url_match:
            return url_match.group(1)
    return None


def download_family(family_key: str, preload_map: dict[str, str]) -> None:
    config = FAMILIES[family_key]
    out_dir = ROOT / "assets" / "vendor" / config["dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    css_url = (
        "https://fonts.googleapis.com/css2?"
        f"family={family_key}:wght@400;700&display=swap"
    )
    css = fetch(css_url).decode("utf-8")
    urls = re.findall(r"url\((https://[^)]+)\)", css)
    rewritten = css

    for url in urls:
        filename = filename_from_url(url)
        destination = out_dir / filename
        if not destination.exists():
            destination.write_bytes(fetch(url))
            print(f"downloaded {filename}")
        rewritten = rewritten.replace(url, filename)

    css_path = out_dir / config["css_name"]
    css_path.write_text(rewritten, encoding="utf-8")
    print(f"wrote {css_path} ({len(urls)} files)")

    preload_face = first_preload_face(rewritten)
    if preload_face:
        preload_map[config["lang"]] = f"/assets/vendor/{config['dir']}/{preload_face}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--family",
        action="append",
        choices=sorted(FAMILIES),
        help="Google Fonts family key (repeatable). Defaults to all families.",
    )
    args = parser.parse_args()
    families = args.family or sorted(FAMILIES)

    preload_map: dict[str, str] = {}
    if PRELOAD_DATA.exists():
        preload_map = yaml.safe_load(PRELOAD_DATA.read_text(encoding="utf-8")) or {}

    for family_key in families:
        download_family(family_key, preload_map)

    PRELOAD_DATA.parent.mkdir(parents=True, exist_ok=True)
    PRELOAD_DATA.write_text(
        yaml.safe_dump(preload_map, sort_keys=True, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"wrote {PRELOAD_DATA}")


if __name__ == "__main__":
    main()