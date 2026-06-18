"""
썸네일이 없는 포스트용 OG 이미지를 생성합니다.

- 저장 위치: uploads/{slug}/thumbnail.webp
- 크기: 1200×630 (Open Graph 권장 비율)
- Pillow만 사용하므로 API 키 없이 로컬에서 실행 가능합니다.

사용법:
    python scripts/generate_missing_thumbnails.py
    python scripts/generate_missing_thumbnails.py --force   # 기존 파일도 덮어쓰기
"""

from __future__ import annotations

import argparse
import re
import textwrap
from pathlib import Path

import yaml

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise SystemExit("Pillow가 필요합니다: pip install Pillow") from exc


ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "_posts"
UPLOADS_DIR = ROOT / "uploads"
ASSETS_DIR = ROOT / "assets"

FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
SLUG_FROM_FILE = re.compile(r"\d{4}-\d{2}-\d{2}-(.+)\.md$")

# 블로그 테마 색상 (_sass/_base.scss 기준)
COLORS = {
    "background": "#1a1a2e",
    "accent": "#268bd2",
    "title": "#ffffff",
    "subtitle": "#a8b2c1",
    "brand": "#515151",
}

IMAGE_SIZE = (1200, 630)
FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/malgunbd.ttf"),
    Path("C:/Windows/Fonts/malgun.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def parse_front_matter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    match = FRONT_MATTER_PATTERN.match(content)
    if not match:
        raise ValueError(f"front matter 없음: {path}")
    metadata = yaml.safe_load(match.group(1))
    if not isinstance(metadata, dict):
        raise ValueError(f"front matter 형식 오류: {path}")
    return metadata


def resolve_slug(path: Path, metadata: dict) -> str:
    if metadata.get("slug"):
        return str(metadata["slug"]).strip()
    match = SLUG_FROM_FILE.match(path.name)
    if match:
        return match.group(1)
    raise ValueError(f"slug를 알 수 없음: {path}")


def find_thumbnail(slug: str) -> Path | None:
    folder = UPLOADS_DIR / slug
    for name in ("thumbnail.webp", "thumbnail.jpg", "thumbnail.png"):
        candidate = folder / name
        if candidate.exists():
            return candidate
    return None


def wrap_title(title: str, max_chars: int = 22) -> list[str]:
    wrapped = textwrap.wrap(title, width=max_chars)
    return wrapped[:3] if wrapped else [title]


def draw_thumbnail(title: str, slug: str) -> Image.Image:
    image = Image.new("RGB", IMAGE_SIZE, COLORS["background"])
    draw = ImageDraw.Draw(image)

    # 상단 악센트 바
    draw.rectangle([(0, 0), (IMAGE_SIZE[0], 8)], fill=COLORS["accent"])

    title_font = load_font(52)
    brand_font = load_font(28)
    slug_font = load_font(22)

    lines = wrap_title(title)
    line_height = 64
    block_height = len(lines) * line_height
    start_y = (IMAGE_SIZE[1] - block_height) // 2 - 20

    for index, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (IMAGE_SIZE[0] - text_width) // 2
        y = start_y + index * line_height
        draw.text((x, y), line, font=title_font, fill=COLORS["title"])

    brand = "Jiwon Min · Developer Blog"
    bbox = draw.textbbox((0, 0), brand, font=brand_font)
    brand_width = bbox[2] - bbox[0]
    draw.text(
        ((IMAGE_SIZE[0] - brand_width) // 2, IMAGE_SIZE[1] - 120),
        brand,
        font=brand_font,
        fill=COLORS["subtitle"],
    )

    draw.text((48, IMAGE_SIZE[1] - 56), slug, font=slug_font, fill=COLORS["brand"])

    return image


def create_default_og_image() -> Path:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    output = ASSETS_DIR / "og-default.webp"

    image = Image.new("RGB", IMAGE_SIZE, COLORS["background"])
    draw = ImageDraw.Draw(image)
    draw.rectangle([(0, 0), (IMAGE_SIZE[0], 8)], fill=COLORS["accent"])

    title_font = load_font(64)
    subtitle_font = load_font(30)

    title = "Jiwon Min"
    subtitle = "Developer Blog"

    for text, font, color, y in [
        (title, title_font, COLORS["title"], 220),
        (subtitle, subtitle_font, COLORS["subtitle"], 310),
        ("blog.jiwon.io", subtitle_font, COLORS["accent"], 380),
    ]:
        bbox = draw.textbbox((0, 0), text, font=font)
        width = bbox[2] - bbox[0]
        draw.text(((IMAGE_SIZE[0] - width) // 2, y), text, font=font, fill=color)

    image.save(output, "WEBP", quality=88)
    return output


def generate_for_posts(force: bool = False) -> list[Path]:
    created: list[Path] = []

    for path in sorted(POSTS_DIR.rglob("*.md")):
        metadata = parse_front_matter(path)
        slug = resolve_slug(path, metadata)
        existing = find_thumbnail(slug)

        if existing and not force:
            continue

        title = str(metadata.get("title", slug))
        output_dir = UPLOADS_DIR / slug
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / "thumbnail.webp"

        image = draw_thumbnail(title, slug)
        image.save(output, "WEBP", quality=88)
        created.append(output)
        print(f"✅ 생성: {output.relative_to(ROOT)}")

    return created


def main() -> int:
    parser = argparse.ArgumentParser(description="누락된 포스트 썸네일과 기본 OG 이미지를 생성합니다.")
    parser.add_argument("--force", action="store_true", help="기존 썸네일도 덮어씁니다.")
    args = parser.parse_args()

    default_path = create_default_og_image()
    print(f"✅ 기본 OG 이미지: {default_path.relative_to(ROOT)}")

    created = generate_for_posts(force=args.force)
    if not created:
        print("ℹ️  새로 생성한 포스트 썸네일이 없습니다. (이미 모두 존재)")
    else:
        print(f"✅ 포스트 썸네일 {len(created)}개 생성 완료")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())