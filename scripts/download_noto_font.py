#!/usr/bin/env python3
"""Download Noto Sans woff2 files for self-hosted fonts."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import tempfile
import urllib.parse
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
        "display_name": "Noto Sans KR",
        "woff2_name": "noto-sans-kr.woff2",
        "variable_ttf_url": (
            "https://github.com/google/fonts/raw/main/ofl/notosanskr/"
            "NotoSansKR%5Bwght%5D.ttf"
        ),
    },
    "Noto+Sans+JP": {
        "dir": "noto-sans-jp",
        "css_name": "noto-sans-jp.css",
        "lang": "ja",
        "display_name": "Noto Sans JP",
        "woff2_name": "noto-sans-jp.woff2",
        "variable_ttf_url": (
            "https://github.com/google/fonts/raw/main/ofl/notosansjp/"
            "NotoSansJP%5Bwght%5D.ttf"
        ),
    },
    "Noto+Sans+SC": {
        "dir": "noto-sans-sc",
        "css_name": "noto-sans-sc.css",
        "lang": "zh",
        "display_name": "Noto Sans SC",
        "woff2_name": "noto-sans-sc.woff2",
        "variable_ttf_url": (
            "https://github.com/google/fonts/raw/main/ofl/notosanssc/"
            "NotoSansSC%5Bwght%5D.ttf"
        ),
    },
}

SITE_TEXT_GLOBS = (
    "_posts/**/*.md",
    "_includes/**/*.html",
    "_layouts/**/*.html",
    "_data/languages.yml",
    "_config.yml",
    "index.html",
    "archive.html",
    "search.html",
    "en/**/*.html",
    "ja/**/*.html",
    "zh/**/*.html",
)


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def filename_from_url(url: str) -> str:
    return url.split("/")[-1].split("?")[0]


def local_font_filename(url: str) -> str:
    """Stable local filename for remote font kit URLs."""
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    return f"noto-{digest}.woff2"


def preload_faces(css: str, limit: int = 1) -> list[str]:
    """Return up to `limit` unique woff2 paths for weight-400 faces (above-the-fold)."""
    seen: list[str] = []
    blocks = re.findall(r"@font-face\s*\{([^}]+)\}", css, flags=re.DOTALL)
    for block in blocks:
        if "font-weight: 400" not in block:
            continue
        url_match = re.search(r"url\(([^)]+\.woff2)\)", block)
        if not url_match:
            continue
        face = url_match.group(1)
        if face not in seen:
            seen.append(face)
        if len(seen) >= limit:
            break
    return seen


def build_single_file_css(
    display_name: str,
    woff2_filename: str,
    *,
    weight: int = 400,
) -> str:
    """Minimal @font-face CSS for a single woff2 file."""
    return (
        "@font-face {\n"
        f"  font-family: '{display_name}';\n"
        "  font-style: normal;\n"
        f"  font-weight: {weight};\n"
        "  font-display: swap;\n"
        f"  src: url({woff2_filename}) format('woff2');\n"
        "}\n"
    )


def instance_static_weight(ttf_bytes: bytes, weight: int) -> bytes:
    """Pin a variable TTF to one weight (smaller woff2 after subsetting)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        source = tmp_dir / "source.ttf"
        instanced = tmp_dir / "static.ttf"
        source.write_bytes(ttf_bytes)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "fontTools.varLib.instancer",
                str(source),
                f"wght={weight}",
                "-o",
                str(instanced),
            ],
            check=True,
        )
        return instanced.read_bytes()


def collect_site_characters(root: Path = ROOT) -> str:
    """Gather unique characters used across site content for font subsetting."""
    chars: set[str] = set()
    for pattern in SITE_TEXT_GLOBS:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            chars.update(path.read_text(encoding="utf-8", errors="ignore"))

    # Keep printable glyphs plus common whitespace used in copy.
    filtered = sorted(
        char
        for char in chars
        if char.isprintable() or char in {"\n", "\t"}
    )
    return "".join(filtered)


def prune_unused_font_files(out_dir: Path, css_text: str) -> int:
    """Remove woff2 files no longer referenced by the generated CSS."""
    referenced = {
        match.group(1)
        for match in re.finditer(r"url\(([^)]+\.woff2)\)", css_text)
    }
    removed = 0
    for path in out_dir.glob("*.woff2"):
        if path.name not in referenced:
            path.unlink()
            removed += 1
    return removed


def chunk_text_for_font_api(text: str, max_chars: int = 400) -> list[str]:
    """Split glyph list so each Google Fonts request stays under URL limits."""
    if len(text) <= max_chars:
        return [text]
    return [text[index : index + max_chars] for index in range(0, len(text), max_chars)]


def fetch_family_css(family_key: str, subset_text: str | None = None) -> str:
    base_url = (
        "https://fonts.googleapis.com/css2?"
        f"family={family_key}:wght@400;700&display=swap"
    )
    if not subset_text:
        return fetch(base_url).decode("utf-8")

    blocks: list[str] = []
    for chunk in chunk_text_for_font_api(subset_text):
        css_url = f"{base_url}&text={urllib.parse.quote(chunk, safe='')}"
        blocks.append(fetch(css_url).decode("utf-8"))
    return "\n".join(blocks)


def subset_variable_font(
    ttf_bytes: bytes,
    subset_text: str,
    destination: Path,
) -> None:
    """Subset a variable TTF to a single woff2 using fonttools."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        source = tmp_dir / "source.ttf"
        text_file = tmp_dir / "chars.txt"
        source.write_bytes(ttf_bytes)
        text_file.write_text(subset_text, encoding="utf-8")

        command = [
            sys.executable,
            "-m",
            "fontTools.subset",
            str(source),
            f"--text-file={text_file}",
            "--flavor=woff2",
            f"--output-file={destination}",
            "--layout-features=*",
            "--glyph-names",
            "--symbol-cmap",
            "--legacy-cmap",
            "--notdef-glyph",
            "--notdef-outline",
            "--recommended-glyphs",
            "--name-IDs=*",
            "--name-legacy",
            "--name-languages=*",
        ]
        subprocess.run(command, check=True)


def save_subset_fingerprint(out_dir: Path, subset_text: str) -> None:
    digest = hashlib.sha256(subset_text.encode("utf-8")).hexdigest()
    (out_dir / ".subset-sha256").write_text(digest + "\n", encoding="utf-8")


def download_family_single_file(
    family_key: str,
    preload_map: dict[str, str],
    *,
    subset_text: str,
    prune: bool = False,
    static_weight: int = 400,
) -> None:
    config = FAMILIES[family_key]
    out_dir = ROOT / "assets" / "vendor" / config["dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    woff2_name = config["woff2_name"]
    destination = out_dir / woff2_name
    ttf_url = config["variable_ttf_url"]

    print(f"downloading variable TTF for {family_key}")
    ttf_bytes = instance_static_weight(fetch(ttf_url), static_weight)
    subset_variable_font(ttf_bytes, subset_text, destination)
    print(f"wrote {destination} ({destination.stat().st_size} bytes)")

    css_text = build_single_file_css(
        config["display_name"],
        woff2_name,
        weight=static_weight,
    )
    css_path = out_dir / config["css_name"]
    css_path.write_text(css_text, encoding="utf-8")
    print(f"wrote {css_path} (1 file)")

    if prune:
        removed = prune_unused_font_files(out_dir, css_text)
        if removed:
            print(f"pruned {removed} unused woff2 files from {out_dir}")

    save_subset_fingerprint(out_dir, subset_text)
    preload_map[config["lang"]] = [
        f"/assets/vendor/{config['dir']}/{woff2_name}"
    ]


def download_family(
    family_key: str,
    preload_map: dict[str, str],
    *,
    subset_text: str | None = None,
    prune: bool = False,
    single_file: bool = False,
    static_weight: int = 400,
) -> None:
    if single_file:
        if not subset_text:
            raise SystemExit("--single-file requires --subset-from-site")
        download_family_single_file(
            family_key,
            preload_map,
            subset_text=subset_text,
            prune=prune,
            static_weight=static_weight,
        )
        return

    config = FAMILIES[family_key]
    out_dir = ROOT / "assets" / "vendor" / config["dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    css = fetch_family_css(family_key, subset_text)
    remote_urls = sorted(set(re.findall(r"url\((https://[^)]+)\)", css)))
    rewritten = css

    for url in remote_urls:
        filename = local_font_filename(url) if subset_text else filename_from_url(url)
        destination = out_dir / filename
        if not destination.exists():
            destination.write_bytes(fetch(url))
            print(f"downloaded {filename}")
        rewritten = rewritten.replace(url, filename)

    css_path = out_dir / config["css_name"]
    css_path.write_text(rewritten, encoding="utf-8")
    referenced = set(re.findall(r"url\(([^)]+\.woff2)\)", rewritten))
    print(f"wrote {css_path} ({len(referenced)} files)")

    if prune:
        removed = prune_unused_font_files(out_dir, rewritten)
        if removed:
            print(f"pruned {removed} unused woff2 files from {out_dir}")

    faces = preload_faces(rewritten)
    if faces:
        preload_map[config["lang"]] = [
            f"/assets/vendor/{config['dir']}/{face}" for face in faces
        ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--family",
        action="append",
        choices=sorted(FAMILIES),
        help="Google Fonts family key (repeatable). Defaults to all families.",
    )
    parser.add_argument(
        "--subset-from-site",
        action="store_true",
        help="Request only glyphs used in site content (smaller woff2 set).",
    )
    parser.add_argument(
        "--single-file",
        action="store_true",
        help=(
            "Subset a variable TTF locally into one woff2 per family "
            "(requires --subset-from-site)."
        ),
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Delete woff2 files in the vendor dir that are not referenced by CSS.",
    )
    parser.add_argument(
        "--static-weight",
        type=int,
        default=400,
        help="Pin variable TTF to one weight before subsetting (default: 400).",
    )
    args = parser.parse_args()
    families = args.family or sorted(FAMILIES)

    subset_text = collect_site_characters() if args.subset_from_site else None
    if subset_text:
        print(f"subset text: {len(subset_text)} unique characters")

    preload_map: dict[str, str] = {}
    if PRELOAD_DATA.exists():
        preload_map = yaml.safe_load(PRELOAD_DATA.read_text(encoding="utf-8")) or {}

    for family_key in families:
        download_family(
            family_key,
            preload_map,
            subset_text=subset_text,
            prune=args.prune,
            single_file=args.single_file,
            static_weight=args.static_weight,
        )

    PRELOAD_DATA.parent.mkdir(parents=True, exist_ok=True)
    PRELOAD_DATA.write_text(
        yaml.safe_dump(preload_map, sort_keys=True, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"wrote {PRELOAD_DATA}")


if __name__ == "__main__":
    main()