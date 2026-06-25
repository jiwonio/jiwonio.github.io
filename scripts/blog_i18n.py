"""블로그 다국어 공통 유틸 (generate_post, backfill_translations에서 공유)."""

from __future__ import annotations

import re
import warnings
from pathlib import Path

import yaml

from post_schema import (
    EXTERNAL_IMAGE_PATTERN,
    FRONT_MATTER_PATTERN,
    POSTS_DIR,
    PROMPT_LEAK_PHRASES,
    extract_reference_urls,
    has_standalone_line,
    sanitize_generated_content,
    strip_references_section,
    write_text_atomic,
)

SLUG_FROM_FILE = re.compile(r"\d{4}-\d{2}-\d{2}-(.+)\.md$")
DATE_FROM_FILE = re.compile(r"(\d{4}-\d{2}-\d{2})")
LANG_PATH = re.compile(r"_posts/(en|ja|zh|ko)/")

SITE_ROOT = Path(__file__).resolve().parent.parent

from llm_client import (
    generate_text as llm_generate_text,
    pick_translation_target,
    resolve_translation_providers,
)
from models_config import TRANSLATION_MODELS as _TRANSLATION_MODELS

DEFAULT_LANG = "ko"
TRANSLATION_LANGS = ("en", "ja", "zh")
AI_GENERATION_START_DATE = "2026-04-01"

LEGACY_KO_TITLES = {
    "style-guide": "스타일 가이드",
    "ubuntu22-swap-memory": "Ubuntu 22.04 LTS 스왑 메모리 설정하기",
    "datagrip-driver-error": "DataGrip에서 Amazon RDS 연결 시 드라이버 오류 해결",
    "ubuntu22-default-setting": "AWS EC2 Ubuntu 초기 설정 가이드",
    "nodejs-installation-failure": "Windows 11 Node.js 설치 오류 해결",
    "cloudflare-invalid-ssl": "Cloudflare Full (strict) SSL 오류 원인과 해결",
    "multiple-wsl2-instances": "Windows 11 WSL2로 여러 개발 환경 만들기",
}

LEGACY_KO_DESCRIPTIONS = {
    "style-guide": "Jekyll 기반 GitHub Pages 블로그의 제목·본문·코드·인용문 등 기본 스타일 가이드를 정리합니다.",
    "ubuntu22-swap-memory": "Ubuntu 22.04 LTS에서 스왑 메모리를 설정해 저사양 EC2·자체 호스팅 서버의 RAM 부족 문제를 완화하는 방법을 설명합니다.",
    "datagrip-driver-error": "JetBrains DataGrip에서 Amazon RDS에 연결할 때 발생하는 드라이버 오류의 원인과 해결 방법을 정리합니다.",
    "ubuntu22-default-setting": "AWS EC2 프리티어 Ubuntu 22.04 LTS 인스턴스의 키 페어, 방화벽, 스토리지 등 초기 설정 절차를 안내합니다.",
    "nodejs-installation-failure": "Windows 11에서 Node.js 설치 시 Chocolatey·Visual Studio Build Tools 관련 오류를 해결하는 방법을 설명합니다.",
    "cloudflare-invalid-ssl": "Cloudflare Full (strict) SSL 모드가 실패하고 Full 모드만 동작하는 원인과 GitHub Pages 연동 시 해결 방법을 정리합니다.",
    "multiple-wsl2-instances": "Windows 11 WSL2로 프로젝트별 분리된 개발 환경을 만들고 관리하는 방법을 단계별로 설명합니다.",
}

LEGACY_KO_INTROS = {
    "style-guide": (
        "이 글은 Jekyll로 운영하는 GitHub Pages 블로그의 **스타일 가이드**입니다. "
        "오랜만에 글을 쓸 때마다 서식이 뒤섞이는 걸 막기 위해, 제목·본문·코드·인용문 등 기본 규칙을 한곳에 기록해 두었습니다. "
        "아래 예시는 영어 UI 기준으로 작성했지만, 한국어 글에도 같은 구조를 그대로 적용할 수 있습니다."
    ),
    "ubuntu22-swap-memory": (
        "AWS EC2 프리티어나 저사양 자체 호스팅 서버에서 대용량 패키지를 설치하다 보면 RAM 부족으로 서버가 멈추거나 다운되는 경우가 있습니다. "
        "마이크로서비스를 낮은 사양에서 운영할 때도 같은 문제가 생길 수 있는데, 이때 **스왑 메모리**로 디스크 일부를 RAM처럼 쓰면 도움이 됩니다. "
        "Ubuntu 22.04 LTS에서 스왑을 설정하는 방법을 정리합니다."
    ),
    "datagrip-driver-error": (
        "JetBrains **DataGrip**은 MySQL, PostgreSQL, MongoDB 등 다양한 DB를 한 곳에서 다루는 크로스 플랫폼 도구입니다. "
        "최근 **AI Assistant** 플러그인도 추가되어 쿼리 작성이 더 편해졌습니다. "
        "이 글에서는 **Amazon RDS** 연결 시 발생하는 **드라이버 오류**의 원인과 해결 방법을 정리합니다."
    ),
    "ubuntu22-default-setting": (
        "AWS EC2 프리티어로 개발·테스트 환경을 만들 때 **Ubuntu 22.04 LTS** 인스턴스의 초기 설정이 중요합니다. "
        "Route 53, ELB, RDS 같은 서비스는 다루지 않고, 키 페어, 방화벽, 스토리지 등 필수 구성만 단계별로 설명합니다. "
        "초기에 올바르게 설정해 두면 이후 트러블슈팅 시간을 크게 줄일 수 있습니다."
    ),
    "nodejs-installation-failure": (
        "Windows 11에서 **Node.js**를 설치할 때 C/C++, Python 컴파일이 필요한 네이티브 패키지 때문에 오류가 나는 경우가 많습니다. "
        "**Chocolatey**로 추가 도구를 설치하는 과정에서 `visualstudio2019-workload-vctools` 설치 실패로 깨끗한 설치가 안 되는 문제를 해결하는 방법을 정리합니다."
    ),
    "cloudflare-invalid-ssl": (
        "**Cloudflare**의 **Full (strict)** SSL 모드는 동작하는데 **Full**만 되는 경우, 원본 서버(**GitHub Pages**) 인증서가 "
        "CA 신뢰·도메인 일치·체인 구성을 완전히 만족하지 못할 때 발생합니다. "
        "Full (strict)과 Full의 차이와 GitHub Pages 연동 시 해결 방법을 설명합니다."
    ),
    "multiple-wsl2-instances": (
        "프로젝트마다 분리된 개발 환경이 필요할 때 **Windows 11**의 **WSL2**로 여러 리눅스 인스턴스를 운영하면 충돌을 줄일 수 있습니다. "
        "설정·테스트·레거시 환경을 각각 격리해 두면 워크플로가 훨씬 수월해집니다. "
        "WSL2 다중 환경 설치와 설정 방법을 정리합니다."
    ),
}

TRANSLATION_ATTRIBUTION_PATTERN = re.compile(
    r"^This translation was provided.*\n",
    flags=re.MULTILINE | re.IGNORECASE,
)
TRANSLATION_LANGS_BY_TYPE = {
    "deep-dive": ("en", "ja", "zh"),
    "ai-news": ("en", "ja", "zh"),
}
# 이 날짜 이전 ai-news는 en만 요구 (기존 글 호환). 이후 생성분은 en/ja/zh.
AI_NEWS_FULL_I18N_START = "2026-06-24"
LANG_LABELS = {
    "en": "English",
    "ja": "Japanese",
    "zh": "Simplified Chinese",
}

def translation_langs_for_metadata(metadata: dict) -> tuple[str, ...]:
    post_type = str(metadata.get("post_type", "deep-dive")).strip()
    langs = TRANSLATION_LANGS_BY_TYPE.get(post_type, TRANSLATION_LANGS)
    if post_type == "ai-news":
        date_raw = metadata.get("date")
        date_str = str(date_raw)[:10] if date_raw else ""
        if date_str and date_str < AI_NEWS_FULL_I18N_START:
            return ("en",)
    return langs


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
    if "ai_generated" in source_metadata:
        metadata["ai_generated"] = source_metadata["ai_generated"]

    body = content[FRONT_MATTER_PATTERN.match(content).end() :]
    return dump_front_matter(metadata) + body


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


def infer_ai_generated(metadata: dict, path: Path) -> bool:
    if metadata.get("ai_generated") is True:
        return True
    if metadata.get("ai_generated") is False:
        return False

    post_type = str(metadata.get("post_type", "deep-dive")).strip()
    if post_type == "ai-news":
        return True

    try:
        date_prefix = resolve_date_prefix(path)
    except ValueError:
        return False
    return date_prefix >= AI_GENERATION_START_DATE


def ensure_updated_field(metadata: dict, path: Path) -> None:
    if metadata.get("updated"):
        return
    if metadata.get("date"):
        metadata["updated"] = metadata["date"]
        return
    try:
        metadata["updated"] = f"{resolve_date_prefix(path)} 10:00:00 +0900"
    except ValueError:
        pass


def normalize_legacy_ko_body(content: str, slug: str) -> str:
    if slug not in LEGACY_KO_INTROS:
        return content

    match = FRONT_MATTER_PATTERN.match(content)
    if not match:
        return content

    body = content[match.end() :]
    body = TRANSLATION_ATTRIBUTION_PATTERN.sub("", body)
    more_index = body.find("<!--more-->")
    if more_index < 0:
        return dump_front_matter(parse_front_matter(content)) + body

    tail = body[more_index:]
    intro = LEGACY_KO_INTROS[slug].strip()
    return dump_front_matter(parse_front_matter(content)) + f"{intro}\n\n{tail}"


def infer_categories(metadata: dict) -> list[str]:
    categories = metadata.get("categories")
    if isinstance(categories, list) and categories:
        return [str(category).strip() for category in categories if str(category).strip()]

    post_type = str(metadata.get("post_type", "deep-dive")).strip()
    if post_type == "ai-news":
        return ["AI"]

    tags = [str(tag).casefold() for tag in metadata.get("tags", [])]
    ai_markers = (
        "ai", "llm", "copilot", "cursor", "ollama", "gemini", "langchain",
        "openai", "rag", "crewai", "langsmith", "jetbrains",
    )
    if any(marker in tag for tag in tags for marker in ai_markers):
        return ["AI"]
    return ["DevOps"]


def prepare_ko_post_content(path: Path) -> str:
    """레거시 포스트에 lang, translation_key, slug, description, post_type, categories를 보강합니다."""
    content = path.read_text(encoding="utf-8")
    metadata = parse_front_matter(content)
    slug = resolve_slug(path, metadata)

    metadata["lang"] = DEFAULT_LANG
    metadata["translation_key"] = metadata.get("translation_key") or slug
    metadata["slug"] = slug
    if not metadata.get("post_type"):
        metadata["post_type"] = "deep-dive"
    if not metadata.get("description") and metadata.get("meta"):
        metadata["description"] = str(metadata["meta"]).strip()
    metadata["categories"] = infer_categories(metadata)
    slug = metadata["slug"]
    if slug in LEGACY_KO_TITLES:
        metadata["title"] = LEGACY_KO_TITLES[slug]
    if slug in LEGACY_KO_DESCRIPTIONS:
        metadata["description"] = LEGACY_KO_DESCRIPTIONS[slug]
        metadata.pop("meta", None)
    ensure_updated_field(metadata, path)
    if infer_ai_generated(metadata, path):
        metadata["ai_generated"] = True

    normalized = dump_front_matter(metadata) + content[FRONT_MATTER_PATTERN.match(content).end() :]
    return normalize_legacy_ko_body(normalized, slug)


def build_translation_prompt(source_content: str, target_lang: str, slug: str) -> str:
    label = LANG_LABELS[target_lang]
    ref_urls = extract_reference_urls(source_content)
    translation_input = strip_references_section(source_content)
    urls_note = ""
    if ref_urls:
        urls_note = (
            "\n- Add a translated references section at the end. "
            "Keep these reference URLs unchanged:\n"
            + "\n".join(f"  - {url}" for url in ref_urls)
        )
    return f"""
You are a senior technical translator. Translate the Jekyll blog post below into {label}.

Rules:
- Output only the translated markdown file. No preamble or explanation.
- Keep these front matter fields exactly unchanged: layout, slug, date, categories, tags, image, post_type, ai_generated
- Set lang: {target_lang}
- Set translation_key: {slug}
- Translate title, description, and all prose. Keep code blocks unchanged.
- Preserve a natural first-person blog voice. Avoid stiff self-introductions like "I am a senior full-stack developer and tech blogger."
- Use concise declarative sentences. Avoid overly formal or repetitive phrasing.
- Preserve marker lines exactly as standalone lines: <!--more-->, -----
- Do not output [HERO_IMAGE]; keep hero images that already exist in the body.
- Keep markdown internal links like [title](/posts/exact-slug/) unchanged (do not shorten or rewrite slugs).
- Translate the references heading appropriately for {label}, but keep link URLs unchanged.
- Remove lines like "This translation was provided by ..." from the body.
- Do not add external image URLs.{urls_note}

Source post (references section omitted from input):
{translation_input}
"""


def validate_translation_content(content: str, target_lang: str, slug: str) -> dict:
    from post_common import find_invalid_internal_post_slugs, get_existing_ko_slugs
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

    invalid_slugs = find_invalid_internal_post_slugs(content, get_existing_ko_slugs())
    if invalid_slugs:
        raise ValueError(
            "존재하지 않는 내부 링크 slug: "
            + ", ".join(invalid_slugs[:5])
            + " (번역 시 /posts/ slug를 변경하지 마세요)"
        )

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
    write_text_atomic(output_path, content)
    return output_path


def get_gemini_client():
    """Deprecated: use llm_client instead."""
    warnings.warn(
        "get_gemini_client() is deprecated; use llm_client.generate_text instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from google import genai

    import os

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경 변수가 필요합니다.")
    return genai.Client(api_key=api_key)


TRANSLATION_MODELS = _TRANSLATION_MODELS


def generate_translation_content(
    source_content: str,
    source_path: Path,
    target_lang: str,
    *,
    translation_provider: str | None = None,
    max_retries: int = 5,
) -> str:
    slug = resolve_slug(source_path, parse_front_matter(source_content))

    if target_lang == "en" and is_primarily_english(source_content):
        content = copy_as_english_translation(source_content, slug)
        content = ensure_translation_metadata(content, source_content, target_lang, slug)
        validate_translation_content(content, target_lang, slug)
        return content

    base_prompt = build_translation_prompt(source_content, target_lang, slug)
    providers = resolve_translation_providers(translation_provider)
    last_error = None
    current_prompt = base_prompt

    for attempt in range(1, max_retries + 1):
        provider, model = pick_translation_target(providers, attempt)
        try:
            print(f"  번역 API: {provider}/{model} (시도 {attempt}/{max_retries})")
            result = llm_generate_text(prompt=current_prompt, provider=provider, model=model)
            content = sanitize_generated_content(
                strip_preamble(strip_code_fence(result.text))
            )
            content = ensure_translation_metadata(content, source_content, target_lang, slug)
            from post_common import get_existing_ko_slugs, repair_internal_post_slugs

            content = repair_internal_post_slugs(content, get_existing_ko_slugs())
            validate_translation_content(content, target_lang, slug)
            from api_monitor import notify_llm_usage

            notify_llm_usage(
                provider=provider,
                model=model,
                attempt=attempt,
                operation=f"translate_{target_lang}",
                slug=slug,
                success=True,
                input_chars=result.input_chars,
                output_chars=result.output_chars,
            )
            return content
        except Exception as exc:
            from api_monitor import notify_llm_usage

            notify_llm_usage(
                provider=provider,
                model=model,
                attempt=attempt,
                operation=f"translate_{target_lang}",
                slug=slug,
                success=False,
                error=str(exc),
            )
            last_error = exc
            if attempt < max_retries:
                current_prompt = (
                    f"{base_prompt}\n\n"
                    f"[Previous attempt failed validation: {exc}. "
                    "Fix these issues and regenerate.]"
                )
                import time

                time.sleep(20 * attempt)

    raise RuntimeError(f"{target_lang} 번역 실패 ({source_path.name}): {last_error}") from last_error


def generate_translation(
    source_content: str,
    source_path: Path,
    target_lang: str,
    *,
    translation_provider: str | None = None,
    max_retries: int = 5,
) -> Path:
    content = generate_translation_content(
        source_content,
        source_path,
        target_lang,
        translation_provider=translation_provider,
        max_retries=max_retries,
    )
    return save_translation(content, source_path, target_lang)