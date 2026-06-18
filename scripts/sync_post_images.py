"""
각 포스트 front matter에 image 필드를 동기화합니다.

우선순위:
  1. uploads/{slug}/thumbnail.webp
  2. uploads/{slug}/thumbnail.jpg
  3. uploads/{slug}/thumbnail.png

사용법:
    python scripts/sync_post_images.py
    python scripts/sync_post_images.py --dry-run
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "_posts"
UPLOADS_DIR = ROOT / "uploads"

FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)
SLUG_FROM_FILE = re.compile(r"\d{4}-\d{2}-\d{2}-(.+)\.md$")


def resolve_slug(path: Path, metadata: dict) -> str:
    if metadata.get("slug"):
        return str(metadata["slug"]).strip()
    match = SLUG_FROM_FILE.match(path.name)
    if match:
        return match.group(1)
    raise ValueError(f"slug를 알 수 없음: {path}")


def find_thumbnail_path(slug: str) -> str | None:
    folder = UPLOADS_DIR / slug
    for name in ("thumbnail.webp", "thumbnail.jpg", "thumbnail.png"):
        if (folder / name).exists():
            return f"/uploads/{slug}/{name}"
    return None


def sync_post(path: Path, dry_run: bool) -> bool:
    content = path.read_text(encoding="utf-8")
    match = FRONT_MATTER_PATTERN.match(content)
    if not match:
        raise ValueError(f"front matter 없음: {path}")

    front_matter_raw, body = match.groups()
    metadata = yaml.safe_load(front_matter_raw)
    if not isinstance(metadata, dict):
        raise ValueError(f"front matter 형식 오류: {path}")

    slug = resolve_slug(path, metadata)
    image_path = find_thumbnail_path(slug)
    if not image_path:
        print(f"⚠️  썸네일 없음 (건너뜀): {path.relative_to(ROOT)}")
        return False

    if metadata.get("image") == image_path:
        return False

    metadata["image"] = image_path
    updated_front_matter = "---\n" + yaml.dump(
        metadata,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ).strip() + "\n---\n"
    updated_content = updated_front_matter + body

    if dry_run:
        print(f"DRY-RUN: {path.relative_to(ROOT)} → image: {image_path}")
    else:
        path.write_text(updated_content, encoding="utf-8")
        print(f"✅ 동기화: {path.relative_to(ROOT)} → {image_path}")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="포스트 front matter의 image 필드를 동기화합니다.")
    parser.add_argument("--dry-run", action="store_true", help="파일을 수정하지 않고 결과만 출력합니다.")
    args = parser.parse_args()

    updated_count = 0
    for path in sorted(POSTS_DIR.rglob("*.md")):
        if sync_post(path, dry_run=args.dry_run):
            updated_count += 1

    print(f"완료: {updated_count}개 포스트 image 필드 갱신")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())