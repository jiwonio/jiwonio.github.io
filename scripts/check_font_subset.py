#!/usr/bin/env python3
"""Regenerate Noto single-file fonts when site glyphs change."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

from download_noto_font import FAMILIES, collect_site_characters

ROOT = Path(__file__).resolve().parent.parent
FINGERPRINT_NAME = ".subset-sha256"


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def vendor_dir(family_key: str) -> Path:
    return ROOT / "assets" / "vendor" / FAMILIES[family_key]["dir"]


def is_stale(family_key: str, subset_text: str) -> bool:
    out_dir = vendor_dir(family_key)
    woff2 = out_dir / FAMILIES[family_key]["woff2_name"]
    if not woff2.exists():
        return True

    digest = fingerprint(subset_text)
    stored_path = out_dir / FINGERPRINT_NAME
    if not stored_path.exists():
        return True
    return stored_path.read_text(encoding="utf-8").strip() != digest


def regenerate(family_key: str) -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "download_noto_font.py"),
            "--family",
            family_key,
            "--subset-from-site",
            "--single-file",
            "--prune",
        ],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--family",
        action="append",
        choices=sorted(FAMILIES),
        help="Check only selected families (default: all).",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Regenerate stale font files.",
    )
    args = parser.parse_args()

    subset_text = collect_site_characters()
    families = args.family or sorted(FAMILIES)
    stale = [family for family in families if is_stale(family, subset_text)]

    if not stale:
        print("Font subsets are up to date.")
        return 0

    for family in stale:
        print(f"Stale font subset: {family}")

    if not args.fix:
        print("Run with --fix to regenerate.")
        return 1

    for family in stale:
        regenerate(family)
    print(f"Regenerated {len(stale)} font family(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())