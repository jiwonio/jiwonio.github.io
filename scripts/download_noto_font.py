#!/usr/bin/env python3
"""Download Noto Sans KR woff2 files for self-hosted fonts."""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "vendor" / "noto-sans-kr"
CSS_URL = "https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap"
USER_AGENT = "Mozilla/5.0"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    css = fetch(CSS_URL).decode("utf-8")
    urls = re.findall(r"url\((https://[^)]+)\)", css)
    rewritten = css
    for url in urls:
        filename = url.split("/")[-1].split("?")[0]
        destination = OUT_DIR / filename
        if not destination.exists():
            destination.write_bytes(fetch(url))
            print(f"downloaded {filename}")
        rewritten = rewritten.replace(url, filename)
    (OUT_DIR / "noto-sans-kr.css").write_text(rewritten, encoding="utf-8")
    print(f"wrote {OUT_DIR / 'noto-sans-kr.css'} ({len(urls)} faces)")


if __name__ == "__main__":
    main()