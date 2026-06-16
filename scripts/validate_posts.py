import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml


FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
REQUIRED_FIELDS = ("layout", "title", "tags")
# AI 생성 스크립트의 프롬프트 지침 문구가 본문에 그대로 남으면 등장하는 표현 (누출 감지용)
PROMPT_LEAK_PHRASES = ("Front Matter", "지침일 뿐이며", "결과물에 그대로 옮겨")
# 한글 단어 사이에 일본어 가나가 섞이는 등의 모델 출력 오류 감지 (예: '네이ティブ')
UNEXPECTED_SCRIPT_PATTERN = re.compile(r"[぀-ヿｦ-ﾝ�]")
CODE_BLOCK_PATTERN = re.compile(r"```.*?```", re.DOTALL)
EXTERNAL_IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\(https?://[^)]+\)")


def has_standalone_line(content, marker):
    """marker가 다른 텍스트와 섞이지 않고 한 줄을 단독으로 차지하는지 확인."""
    return any(line.strip() == marker for line in content.splitlines())


def find_unexpected_scripts(content):
    """코드 블록을 제외한 본문에서 일본어 가나·치환 문자 등 의도치 않은 문자를 찾는다."""
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

    return content, metadata


def validate_posts(posts_dir):
    errors = []
    tag_spellings = defaultdict(set)
    output_paths = defaultdict(list)

    for path in sorted(posts_dir.rglob("*.md")):
        try:
            content, metadata = load_post(path)
        except (OSError, UnicodeError, yaml.YAMLError, ValueError) as exc:
            errors.append(f"{path}: {exc}")
            continue

        for tag in metadata["tags"]:
            tag_spellings[tag.casefold()].add(tag)

        slug = metadata.get("slug") or path.stem[11:]
        normalized_slug = re.sub(r"[^a-z0-9]+", "-", str(slug).lower()).strip("-")
        output_paths[normalized_slug].append(path)

        if not has_standalone_line(content, "<!--more-->"):
            errors.append(f"{path}: missing standalone <!--more--> excerpt separator")

        if "[HERO_IMAGE]" in content:
            errors.append(f"{path}: unresolved [HERO_IMAGE] placeholder")

        leaked = [phrase for phrase in PROMPT_LEAK_PHRASES if phrase in content]
        if leaked:
            errors.append(f"{path}: prompt instruction text leaked into body: {', '.join(leaked)}")

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

    for slug, paths in output_paths.items():
        if len(paths) > 1:
            errors.append(
                f"duplicate post output slug '{slug}': "
                + ", ".join(str(path) for path in paths)
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
