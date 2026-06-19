import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blog_i18n import resolve_effective_date


FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
REQUIRED_FIELDS = ("layout", "title", "tags", "image")
LANG_PATH = re.compile(r"(?:^|/)_posts/(en|ja|zh)(?:/|$)")
DEFAULT_LANG = "ko"
PROMPT_LEAK_PHRASES = ("Front Matter", "지침일 뿐이며", "결과물에 그대로 옮겨")
UNEXPECTED_SCRIPT_PATTERN = re.compile(r"[぀-ヿｦ-ﾝ]")
CODE_BLOCK_PATTERN = re.compile(r"```.*?```", re.DOTALL)
EXTERNAL_IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\(https?://[^)]+\)")


def detect_lang(path: Path, metadata: dict) -> str:
    if metadata.get("lang"):
        return str(metadata["lang"]).strip()
    if LANG_PATH.search(path.as_posix()):
        return LANG_PATH.search(path.as_posix()).group(1)
    return DEFAULT_LANG


def has_standalone_line(content, marker):
    return any(line.strip() == marker for line in content.splitlines())


def find_unexpected_scripts(content):
    prose = CODE_BLOCK_PATTERN.sub("", content)
    return sorted(set(UNEXPECTED_SCRIPT_PATTERN.findall(prose)))


def load_post(path):
    content = path.read_text(encoding="utf-8")
    match = FRONT_MATTER_PATTERN.match(content)
    if not match:
        raise ValueError("missing or malformed YAML front matter")

    metadata = yaml.safe_load(match.group(1))
    if not isinstance(metadata, dict):
        raise ValueError("front matter must be a YAML mapping")

    missing = [field for field in REQUIRED_FIELDS if not metadata.get(field)]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    if metadata["layout"] != "post":
        raise ValueError("layout must be 'post'")

    tags = metadata["tags"]
    if not isinstance(tags, list) or not all(isinstance(tag, str) and tag.strip() for tag in tags):
        raise ValueError("tags must be a non-empty list of strings")

    if not metadata.get("description") and not metadata.get("meta"):
        raise ValueError("description or meta is required for SEO")

    image = metadata.get("image")
    if not isinstance(image, str) or not image.startswith("/uploads/"):
        raise ValueError("image must be an absolute site path starting with /uploads/")

    return content, metadata


def validate_image_file(image_path, site_root):
    relative_path = image_path.lstrip("/")
    file_path = site_root / relative_path
    if not file_path.is_file():
        raise ValueError(f"image file not found: {image_path}")


def validate_posts(posts_dir, site_root=None):
    errors = []
    tag_spellings = defaultdict(set)
    output_paths = defaultdict(list)
    translation_groups = defaultdict(dict)
    if site_root is None:
        site_root = posts_dir.parent

    for path in sorted(posts_dir.rglob("*.md")):
        try:
            content, metadata = load_post(path)
            validate_image_file(metadata["image"], site_root)
        except (OSError, UnicodeError, yaml.YAMLError, ValueError) as exc:
            errors.append(f"{path}: {exc}")
            continue

        lang = detect_lang(path, metadata)
        for tag in metadata["tags"]:
            tag_spellings[tag.casefold()].add(tag)

        slug = metadata.get("slug") or path.stem[11:]
        normalized_slug = re.sub(r"[^a-z0-9]+", "-", str(slug).lower()).strip("-")
        output_paths[(lang, normalized_slug)].append(path)

        translation_key = metadata.get("translation_key") or normalized_slug
        translation_groups[translation_key][lang] = (path, metadata)

        if not has_standalone_line(content, "<!--more-->"):
            errors.append(f"{path}: missing standalone <!--more--> excerpt separator")

        if "[HERO_IMAGE]" in content:
            errors.append(f"{path}: unresolved [HERO_IMAGE] placeholder")

        leaked = [phrase for phrase in PROMPT_LEAK_PHRASES if phrase in content]
        if leaked:
            errors.append(f"{path}: prompt instruction text leaked into body: {', '.join(leaked)}")

        # 일본어 포스트는 가나·한자가 정상이므로, ko 원문에만 혼입 문자 검사를 적용합니다.
        if lang == DEFAULT_LANG:
            stray_chars = find_unexpected_scripts(content)
            if stray_chars:
                errors.append(f"{path}: unexpected characters mixed into text: {', '.join(stray_chars)}")

        if EXTERNAL_IMAGE_PATTERN.search(content):
            errors.append(f"{path}: contains an external image link")

    for spellings in tag_spellings.values():
        if len(spellings) > 1:
            errors.append(
                "tag names differ only by case and share an archive path: "
                + ", ".join(sorted(spellings))
            )

    for key, paths in output_paths.items():
        if len(paths) > 1:
            lang, slug = key
            errors.append(
                f"duplicate post output slug '{slug}' for lang '{lang}': "
                + ", ".join(str(path) for path in paths)
            )

    for key, langs in translation_groups.items():
        if len(langs) < 2:
            continue
        source = langs.get(DEFAULT_LANG)
        if not source:
            continue
        source_path, source_meta = source
        source_date = resolve_effective_date(source_path, source_meta)
        for lang, (path, metadata) in langs.items():
            if lang == DEFAULT_LANG:
                continue
            post_date = resolve_effective_date(path, metadata)
            if post_date != source_date:
                errors.append(
                    f"translation date mismatch for '{key}': "
                    f"{DEFAULT_LANG}={source_date}, {lang}={post_date} ({path})"
                )

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate Jekyll post metadata and archive paths.")
    parser.add_argument("--posts-dir", type=Path, default=Path("_posts"))
    args = parser.parse_args()

    errors = validate_posts(args.posts_dir)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Post validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())