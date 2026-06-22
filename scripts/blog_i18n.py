"""블로그 다국어 공통 유틸 (generate_post, backfill_translations에서 공유)."""

from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
SLUG_FROM_FILE = re.compile(r"\d{4}-\d{2}-\d{2}-(.+)\.md$")
DATE_FROM_FILE = re.compile(r"(\d{4}-\d{2}-\d{2})")
LANG_PATH = re.compile(r"_posts/(en|ja|zh)/")

SITE_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = SITE_ROOT / "_posts"

DEFAULT_LANG = "ko"
TRANSLATION_LANGS = ("en", "ja", "zh")
TRANSLATION_LANGS_BY_TYPE = {
    "deep-dive": ("en", "ja", "zh"),
    "ai-news": ("en",),
}
LANG_LABELS = {
    "en": "English",
    "ja": "Japanese",
    "zh": "Simplified Chinese",
}

PROMPT_LEAK_PHRASES = ("Front Matter", "지침일 뿐이며", "결과물에 그대로 옮겨")
EXTERNAL_IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\(https?://[^)]+\)")


def translation_langs_for_metadata(metadata: dict) -> tuple[str, ...]:
    post_type = str(metadata.get("post_type", "deep-dive")).strip()
    return TRANSLATION_LANGS_BY_TYPE.get(post_type, TRANSLATION_LANGS)


def detect_lang_from_path(path: str | Path) -> str:
    normalized = str(path).replace("\\", "/")
    match = LANG_PATH.search(normalized)
    return match.group(1) if match else DEFAULT_LANG


def parse_front_matter(content: str) -> dict:
    match = FRONT_MATTER_PATTERN.match(content)
    if not match:
        raise ValueError("YAML front matter가 없거나 형식이 잘못되었습니다.")
    metadata = yaml.safe_load(match.group(1))
    if not isinstance(metadata, dict):
        raise ValueError("Front matter는 YAML mapping 형식이어야 합니다.")
    return metadata


def inject_front_matter_field(content: str, field_name: str, field_value) -> str:
    match = FRONT_MATTER_PATTERN.match(content)
    if not match:
        raise ValueError("front matter를 찾을 수 없습니다.")
    metadata = yaml.safe_load(match.group(1))
    metadata[field_name] = field_value
    updated = (
        "---\n"
        + yaml.dump(metadata, allow_unicode=True, default_flow_style=False, sort_keys=False).strip()
        + "\n---\n"
    )
    return updated + content[match.end() :]


def dump_front_matter(metadata: dict) -> str:
    return (
        "---\n"
        + yaml.dump(metadata, allow_unicode=True, default_flow_style=False, sort_keys=False).strip()
        + "\n---\n"
    )


def resolve_slug(path: Path, metadata: dict | None = None) -> str:
    if metadata and metadata.get("slug"):
        return str(metadata["slug"]).strip()
    match = SLUG_FROM_FILE.match(path.name)
    if match:
        return match.group(1)
    return re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-")


def resolve_date_prefix(path: Path) -> str:
    match = DATE_FROM_FILE.search(path.name)
    if match:
        return match.group(1)
    raise ValueError(f"파일명에서 날짜를 찾을 수 없습니다: {path}")


def resolve_year(path: Path) -> str:
    return resolve_date_prefix(path)[:4]


def resolve_effective_date(path: Path, metadata: dict | None = None) -> str:
    """front matter date가 있으면 우선, 없으면 파일명 날짜를 사용합니다."""
    if metadata and metadata.get("date"):
        return str(metadata["date"])[:10]
    return resolve_date_prefix(path)


def explicit_post_date(metadata: dict) -> str | None:
    """front matter에 명시된 date만 반환합니다. 없으면 None(파일명 사용)."""
    return metadata.get("date") if metadata.get("date") else None


def permalink_for_lang(lang: str, slug: str) -> str:
    if lang == DEFAULT_LANG:
        return f"/posts/{slug}/"
    return f"/{lang}/posts/{slug}/"


def translation_output_path(source_path: Path, target_lang: str) -> Path:
    year = resolve_year(source_path)
    return POSTS_DIR / target_lang / year / source_path.name


def ensure_translation_metadata(content: str, source_content: str, target_lang: str, slug: str) -> str:
    """번역본 front matter에 date 등 누락 필드를 원문에서 보강합니다."""
    metadata = parse_front_matter(content)
    source_metadata = parse_front_matter(source_content)

    metadata["lang"] = target_lang
    metadata["translation_key"] = slug
    metadata["slug"] = slug
    metadata["permalink"] = permalink_for_lang(target_lang, slug)

    source_date = explicit_post_date(source_metadata)
    if source_date:
        metadata["date"] = source_date
    else:
        metadata.pop("date", None)
    if not metadata.get("description") and metadata.get("meta"):
        metadata["description"] = str(metadata["meta"]).strip()
    if not metadata.get("layout"):
        metadata["layout"] = "post"
    if source_metadata.get("post_type"):
        metadata["post_type"] = source_metadata["post_type"]

    body = content[FRONT_MATTER_PATTERN.match(content).end() :]
    return dump_front_matter(metadata) + body


def has_standalone_line(content: str, marker: str) -> bool:
    return any(line.strip() == marker for line in content.splitlines())


def strip_preamble(text: str) -> str:
    if text.startswith("---"):
        return text
    match = re.search(r"^---\s*$", text, re.MULTILINE)
    return text[match.start() :] if match else text


def strip_code_fence(text: str) -> str:
    text = re.sub(r"\A```[a-zA-Z]*[ \t]*\r?\n", "", text.strip())
    text = re.sub(r"\r?\n```\s*\Z", "", text)
    return text.strip()


def is_primarily_english(content: str) -> bool:
    body = FRONT_MATTER_PATTERN.sub("", content)
    korean_chars = len(re.findall(r"[가-힣]", body))
    return korean_chars < 40


def prepare_ko_post_content(path: Path) -> str:
    """레거시 포스트에 lang, translation_key, slug, description을 보강합니다."""
    content = path.read_text(encoding="utf-8")
    metadata = parse_front_matter(content)
    slug = resolve_slug(path, metadata)

    metadata["lang"] = DEFAULT_LANG
    metadata["translation_key"] = metadata.get("translation_key") or slug
    metadata["slug"] = slug
    if not metadata.get("description") and metadata.get("meta"):
        metadata["description"] = str(metadata["meta"]).strip()

    return dump_front_matter(metadata) + content[FRONT_MATTER_PATTERN.match(content).end() :]


def build_translation_prompt(source_content: str, target_lang: str, slug: str) -> str:
    label = LANG_LABELS[target_lang]
    return f"""
You are a senior technical translator. Translate the Jekyll blog post below into {label}.

Rules:
- Output only the translated markdown file. No preamble or explanation.
- Keep these front matter fields exactly unchanged: layout, slug, date, categories, tags, image, post_type
- Set lang: {target_lang}
- Set translation_key: {slug}
- Translate title, description, and all prose. Keep code blocks unchanged.
- Preserve marker lines exactly as standalone lines: <!--more-->, -----
- Do not output [HERO_IMAGE]; keep hero images that already exist in the body.
- Translate the references heading appropriately for {label}, but keep link URLs unchanged.
- Remove lines like "This translation was provided by ..." from the body.
- Do not add external image URLs.

Source post:
{source_content}
"""


def validate_translation_content(content: str, target_lang: str, slug: str) -> dict:
    metadata = parse_front_matter(content)

    if metadata.get("lang") != target_lang:
        raise ValueError(f"lang은 {target_lang}이어야 합니다.")
    if metadata.get("translation_key") != slug:
        raise ValueError(f"translation_key는 {slug}이어야 합니다.")
    if metadata.get("slug") != slug:
        raise ValueError(f"slug는 {slug}이어야 합니다.")
    if not has_standalone_line(content, "<!--more-->"):
        raise ValueError("<!--more--> 구분자가 없습니다.")
    if "[HERO_IMAGE]" in content:
        raise ValueError("[HERO_IMAGE] 자리 표시자가 남아 있습니다.")

    leaked = [phrase for phrase in PROMPT_LEAK_PHRASES if phrase in content]
    if leaked:
        raise ValueError("프롬프트 지침 문구가 본문에 노출되었습니다.")

    if EXTERNAL_IMAGE_PATTERN.search(content):
        raise ValueError("외부 이미지 링크가 포함되어 있습니다.")

    return metadata


def copy_as_english_translation(source_content: str, slug: str) -> str:
    """이미 영어로 작성된 글은 en 번역본으로 메타만 맞춰 복사합니다."""
    metadata = parse_front_matter(source_content)
    body = source_content[FRONT_MATTER_PATTERN.match(source_content).end() :]
    metadata["lang"] = "en"
    metadata["translation_key"] = slug
    metadata["slug"] = slug
    if not metadata.get("description") and metadata.get("meta"):
        metadata["description"] = str(metadata["meta"]).strip()
    body = re.sub(
        r"^This translation was provided.*\n",
        "",
        body,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    return dump_front_matter(metadata) + body


def save_translation(content: str, source_path: Path, target_lang: str) -> Path:
    output_path = translation_output_path(source_path, target_lang)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def get_gemini_client():
    from google import genai

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경 변수가 필요합니다.")
    return genai.Client(api_key=api_key)


def generate_translation(
    client,
    source_content: str,
    source_path: Path,
    target_lang: str,
    *,
    max_retries: int = 3,
) -> Path:
    slug = resolve_slug(source_path, parse_front_matter(source_content))

    if target_lang == "en" and is_primarily_english(source_content):
        content = copy_as_english_translation(source_content, slug)
        content = ensure_translation_metadata(content, source_content, target_lang, slug)
        validate_translation_content(content, target_lang, slug)
        return save_translation(content, source_path, target_lang)

    prompt = build_translation_prompt(source_content, target_lang, slug)
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(model="gemini-2.5-pro", contents=prompt)
            content = strip_preamble(strip_code_fence(response.text))
            content = ensure_translation_metadata(content, source_content, target_lang, slug)
            validate_translation_content(content, target_lang, slug)
            return save_translation(content, source_path, target_lang)
        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                import time

                time.sleep(10 * attempt)

    raise RuntimeError(f"{target_lang} 번역 실패 ({source_path.name}): {last_error}") from last_error