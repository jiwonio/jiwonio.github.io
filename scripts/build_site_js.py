#!/usr/bin/env python3
"""Concatenate site JS modules into a single deferred bundle."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = [
    ROOT / "assets/js/icons.js",
    ROOT / "assets/js/theme.js",
    ROOT / "assets/js/lang-switcher.js",
    ROOT / "assets/js/consent.js",
]
OUTPUT = ROOT / "assets/js/site.js"


def build() -> None:
    parts: list[str] = []
    for path in SOURCES:
        parts.append(path.read_text(encoding="utf-8").strip())
    OUTPUT.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT} ({len(SOURCES)} modules)")


if __name__ == "__main__":
    build()