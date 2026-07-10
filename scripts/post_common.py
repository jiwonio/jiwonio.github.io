"""블로그 자동 포스팅 공통 유틸 (generate_post, generate_ai_news에서 공유)."""

from __future__ import annotations

import io
import os
import re
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from blog_i18n import (
    DEFAULT_LANG,
    LANG_LABELS,
    detect_lang_from_path,
    inject_front_matter_field,
    parse_front_matter,
    permalink_for_lang,
    translation_langs_for_metadata,
    translation_output_path,
)
from blog_i18n import generate_translation as _generate_translation
from blog_i18n import generate_translation_content as _generate_translation_content
from post_schema import (
    EXTERNAL_IMAGE_PATTERN,
    POSTS_DIR,
    PROMPT_LEAK_PHRASES,
    REFERENCE_URL_PATTERN,
    has_standalone_line,
    sanitize_generated_content,
    write_bytes_atomic,
    write_text_atomic,
)
from llm_client import (
    generate_image_with_fallback,
    generate_text as llm_generate_text,
    get_text_model,
    pick_provider_for_attempt,
    resolve_text_providers,
)

try:
    from PIL import Image
except ImportError:
    Image = None
FORBIDDEN_REPEAT_COUNT = 3
UNEXPECTED_SCRIPT_PATTERN = re.compile(r"[぀-ヿｦ-ﾝ]")
CODE_BLOCK_PATTERN = re.compile(r"```.*?```", re.DOTALL)
TITLE_PATTERN = re.compile(r'title:\s*"([^"]+)"|title:\s*\'([^\']+)\'')
SLUG_FROM_FILE = re.compile(r"\d{4}-\d{2}-\d{2}-(.+)\.md$")
INTERNAL_LINK_PATTERN = re.compile(r"\]\(/posts/[^)]+\)")

REQUIRED_FIELDS = ("layout", "title", "slug", "date", "categories", "tags", "description", "image")
DEFAULT_THUMBNAIL_SOURCE = Path(__file__).resolve().parent.parent / "assets" / "og-default.webp"
TOKEN_STOP_WORDS = frozenset({
    "and", "for", "on", "the", "with", "from", "into", "that", "this", "how",
    "are", "was", "were", "has", "have", "had", "not", "but", "can", "will",
    "your", "our", "all", "any", "its", "new", "now", "get", "use", "using",
    "full", "more", "also", "just", "one", "two", "way", "may", "via", "out",
    "about", "what", "when", "where", "who", "why", "than", "then", "over",
})


def get_kst_now() -> datetime:
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst)


def list_post_files() -> list[str]:
    return [str(path) for path in sorted(POSTS_DIR.rglob("*.md"))]


def find_unexpected_scripts(content: str) -> list[str]:
    prose = CODE_BLOCK_PATTERN.sub("", content)
    return sorted(set(UNEXPECTED_SCRIPT_PATTERN.findall(prose)))


def extract_title(content: str) -> str | None:
    match = TITLE_PATTERN.search(content)
    if not match:
        return None
    return match.group(1) or match.group(2)


def extract_slug_from_path(path: str | Path) -> str | None:
    match = SLUG_FROM_FILE.match(os.path.basename(str(path)))
    return match.group(1) if match else None


def get_recent_post_files(limit: int = 50) -> list[str]:
    return sorted(list_post_files(), reverse=True)[:limit]


def get_recent_titles(limit: int = 50) -> list[str]:
    titles = []
    for path in get_recent_post_files(limit):
        try:
            with open(path, encoding="utf-8") as post_file:
                title = extract_title(post_file.read())
            if title:
                titles.append(title)
        except OSError:
            continue
    return titles


def get_recent_slugs(limit: int = 50) -> list[str]:
    return [
        slug
        for path in get_recent_post_files(limit)
        if (slug := extract_slug_from_path(path))
    ]


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[\w가-힣]+", text.casefold()) if len(t) >= 2]


def content_tokens(text: str) -> list[str]:
    """내부 링크 매칭용 토큰 (불용어 제외)."""
    return [token for token in tokenize(text) if token not in TOKEN_STOP_WORDS]


def count_token_frequency(titles: list[str], slugs: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for title in titles:
        for token in set(tokenize(title)):
            counts[token] = counts.get(token, 0) + 1
    for slug in slugs:
        for part in slug.split("-"):
            if len(part) >= 3:
                counts[part] = counts.get(part, 0) + 1
    return counts


def format_repeated_tokens(counts: dict[str, int], min_count: int = 2, limit: int = 20) -> list[str]:
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [f"{word}({count}회)" for word, count in ranked if count >= min_count][:limit]


def strip_preamble(text: str) -> str:
    if text.startswith("---"):
        return text
    match = re.search(r"^---\s*$", text, re.MULTILINE)
    return text[match.start() :] if match else text


def strip_code_fence(text: str) -> str:
    text = re.sub(r"\A```[a-zA-Z]*[ \t]*\r?\n", "", text.strip())
    text = re.sub(r"\r?\n```\s*\Z", "", text)
    return text.strip()


def parse_required_front_matter(content: str) -> dict:
    metadata = parse_front_matter(content)
    missing = [field for field in REQUIRED_FIELDS if not metadata.get(field)]
    if missing:
        raise ValueError(f"필수 front matter 누락: {', '.join(missing)}")
    if metadata["layout"] != "post":
        raise ValueError("layout은 post여야 합니다.")
    for field in ("categories", "tags"):
        values = metadata[field]
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value.strip() for value in values
        ):
            raise ValueError(f"{field}는 비어 있지 않은 문자열 목록이어야 합니다.")
    if "AI" not in metadata["categories"]:
        raise ValueError("AI 중심 포스트는 categories에 AI를 포함해야 합니다.")
    return metadata


def validate_base_content(content: str, *, require_hero_placeholder: bool = True) -> dict:
    metadata = parse_required_front_matter(content)

    if not has_standalone_line(content, "<!--more-->"):
        raise ValueError("<!--more--> 구분자가 단독 줄로 존재하지 않습니다.")
    if require_hero_placeholder and not has_standalone_line(content, "[HERO_IMAGE]"):
        raise ValueError("[HERO_IMAGE] 자리 표시자가 단독 줄로 존재하지 않습니다.")
    if "### 참고문헌" not in content:
        raise ValueError("참고문헌 섹션이 없습니다.")

    leaked = [phrase for phrase in PROMPT_LEAK_PHRASES if phrase in content]
    if leaked:
        raise ValueError("프롬프트 지침 문구가 본문에 노출되었습니다: " + ", ".join(leaked))

    stray = find_unexpected_scripts(content)
    if stray:
        raise ValueError("의도하지 않은 문자가 섞여 있습니다: " + ", ".join(stray))

    if EXTERNAL_IMAGE_PATTERN.search(content):
        raise ValueError("본문에 외부 이미지 링크가 포함되어 있습니다.")

    return metadata


def get_existing_tag_spellings() -> dict[str, str]:
    spellings: dict[str, str] = {}
    for path in list_post_files():
        try:
            with open(path, encoding="utf-8") as post_file:
                metadata = parse_front_matter(post_file.read())
            for tag in metadata.get("tags", []):
                spellings.setdefault(tag.casefold(), tag)
        except (OSError, UnicodeError, ValueError):
            continue
    return spellings


def validate_tag_consistency(metadata: dict) -> None:
    existing = get_existing_tag_spellings()
    inconsistent = [
        tag
        for tag in metadata["tags"]
        if tag.casefold() in existing and tag != existing[tag.casefold()]
    ]
    if inconsistent:
        expected = [existing[tag.casefold()] for tag in inconsistent]
        raise ValueError(
            "기존 태그와 대소문자가 다릅니다: "
            + ", ".join(f"{a} -> {b}" for a, b in zip(inconsistent, expected))
        )


def get_existing_ko_slugs() -> set[str]:
    slugs: set[str] = set()
    for path in list_post_files():
        if detect_lang_from_path(path) != DEFAULT_LANG:
            continue
        if slug := extract_slug_from_path(path):
            slugs.add(slug)
    return slugs


def normalize_slug(raw_slug: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(raw_slug).lower()).strip("-")
    if not slug:
        raise ValueError("slug를 영문과 숫자로 생성해야 합니다.")
    return slug


def body_after_more(content: str) -> str:
    parts = content.split("<!--more-->", 1)
    return parts[1] if len(parts) > 1 else ""


def repair_hero_image_placeholder(content: str) -> str:
    """Ensure [HERO_IMAGE] and ----- exist on standalone lines after <!--more-->."""
    if has_standalone_line(content, "[HERO_IMAGE]"):
        return content
    marker = "<!--more-->"
    if marker not in content:
        return content

    head, tail = content.split(marker, 1)
    tail = tail.replace("[HERO_IMAGE]", "")
    lines = tail.splitlines()
    while lines and lines[0].strip() in {"", "-----"}:
        lines.pop(0)
    rebuilt_tail = "\n".join(lines)
    if rebuilt_tail:
        rebuilt_tail = "\n" + rebuilt_tail
    return f"{head}{marker}\n\n[HERO_IMAGE]\n-----\n{rebuilt_tail}"


def count_markdown_internal_links(content: str) -> int:
    return len(INTERNAL_LINK_PATTERN.findall(content))


def normalize_post_slug(slug: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(slug).lower()).strip("-")


def resolve_internal_post_slug(link_slug: str, ko_slugs: set[str]) -> str | None:
    """Map a /posts/ slug to a known ko post slug (exact, prefix, or token overlap)."""
    raw = link_slug.strip().strip("/")
    if not raw:
        return None
    normalized = normalize_post_slug(raw)
    if raw in ko_slugs:
        return raw
    if normalized in ko_slugs:
        return normalized

    extensions = sorted(s for s in ko_slugs if s.startswith(f"{raw}-") or s.startswith(raw))
    if len(extensions) == 1:
        return extensions[0]

    link_tokens = {token for token in raw.split("-") if token}
    if len(link_tokens) < 3:
        return None

    scored: list[tuple[int, str]] = []
    for candidate in ko_slugs:
        cand_tokens = {token for token in candidate.split("-") if token}
        overlap = len(link_tokens & cand_tokens)
        if overlap >= max(3, int(len(link_tokens) * 0.85)):
            scored.append((overlap, candidate))

    if not scored:
        return None
    scored.sort(key=lambda item: (-item[0], item[1]))
    if len(scored) == 1 or scored[0][0] > scored[1][0]:
        return scored[0][1]
    return None


def repair_reference_urls(content: str, source_content: str, target_lang: str = "ko") -> str:
    from post_analysis import rebuild_references_section

    return rebuild_references_section(content, source_content, target_lang)


def find_broken_reference_urls(content: str) -> list[str]:
    from post_analysis import extract_reference_urls
    from validate_posts import check_reference_url

    broken: list[str] = []
    for url in extract_reference_urls(content):
        if check_reference_url(url):
            broken.append(url)
    return broken


def drop_broken_reference_urls(content: str) -> tuple[str, list[str]]:
    """Remove unreachable reference links and rebuild the references section."""
    from post_analysis import (
        extract_reference_entries,
        find_references_section_start,
        normalize_reference_url,
    )
    from validate_posts import check_reference_url

    entries = extract_reference_entries(content)
    if not entries:
        return content, []

    kept: list[tuple[str, str]] = []
    dropped: list[str] = []
    for title, url in entries:
        normalized = normalize_reference_url(url)
        if check_reference_url(normalized):
            dropped.append(normalized)
            continue
        kept.append((title, normalized))

    if not dropped:
        return content, []

    start = find_references_section_start(content)
    if start < 0:
        return content, dropped

    lines = ["### 참고문헌"]
    for title, url in kept:
        label = title or url
        lines.append(f'- [{label}]({url}){{:target="_blank"}}')
    ref_block = "\n".join(lines) + "\n"
    return content[:start].rstrip() + "\n\n" + ref_block, dropped


def repair_internal_post_slugs(content: str, ko_slugs: set[str]) -> str:
    """Fix truncated /posts/slug/ links when they uniquely match one ko post."""

    def replace_link(match: re.Match[str]) -> str:
        prefix, slug, suffix = match.group(1), match.group(2), match.group(3)
        resolved = resolve_internal_post_slug(slug, ko_slugs)
        if not resolved or resolved == slug:
            return match.group(0)
        return f"{prefix}{resolved}{suffix}"

    pattern = re.compile(r"(\]\(/posts/)([^)/\s]+)(/[^)]*\))")
    return pattern.sub(replace_link, content)


def find_invalid_internal_post_slugs(content: str, ko_slugs: set[str]) -> list[str]:
    invalid: list[str] = []
    for slug in re.findall(r"\]\(/posts/([^)/\s]+)", content):
        if resolve_internal_post_slug(slug, ko_slugs) is None:
            invalid.append(slug)
    return sorted(set(invalid))


def repair_internal_links(
    content: str,
    candidates: list[dict],
    *,
    min_links: int = 2,
) -> str:
    """Insert /posts/ links from candidates when the model omitted them."""
    if count_markdown_internal_links(content) >= min_links:
        return content
    if not candidates:
        return content

    needed = min_links - count_markdown_internal_links(content)
    inject_lines: list[str] = []
    for item in candidates:
        url = str(item.get("url", ""))
        title = str(item.get("title", "관련 글"))
        if not url.startswith("/posts/") or url in content:
            continue
        inject_lines.append(f'- [{title}]({url}){{:target="_blank"}}')
        if len(inject_lines) >= needed:
            break

    if not inject_lines:
        return content

    block = "## 관련 블로그 글\n" + "\n".join(inject_lines) + "\n\n"
    ref_marker = "### 참고문헌"
    if ref_marker in content:
        idx = content.index(ref_marker)
        return content[:idx] + block + content[idx:]
    return content.rstrip() + "\n\n" + block


def repair_ai_news_structure(content: str, internal_candidates: list[dict]) -> str:
    """Normalize common LLM formatting mistakes before strict validation."""
    ko_slugs = get_existing_ko_slugs()
    content = repair_hero_image_placeholder(content)
    content = repair_internal_links(content, internal_candidates)
    return repair_internal_post_slugs(content, ko_slugs)


def extract_reference_urls(content: str) -> list[str]:
    from post_analysis import extract_reference_urls as _extract_reference_urls

    return _extract_reference_urls(content)


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def collect_past_reference_urls(slug_prefix: str = "ai-news-") -> set[str]:
    urls: set[str] = set()
    for path in list_post_files():
        if detect_lang_from_path(path) != DEFAULT_LANG:
            continue
        slug = extract_slug_from_path(path)
        if not slug or not slug.startswith(slug_prefix):
            continue
        try:
            content = Path(path).read_text(encoding="utf-8")
            urls.update(extract_reference_urls(content))
        except OSError:
            continue
    return urls


def get_internal_link_candidates(rss_titles: list[str], limit: int = 8) -> list[dict]:
    """RSS 제목·태그와 매칭되는 기존 심층 글 후보."""
    rss_tokens: set[str] = set()
    for title in rss_titles:
        rss_tokens.update(content_tokens(title))

    candidates: list[tuple[int, dict]] = []
    for path in list_post_files():
        if detect_lang_from_path(path) != DEFAULT_LANG:
            continue
        slug = extract_slug_from_path(path)
        if not slug or slug.startswith("ai-news-"):
            continue
        try:
            content = Path(path).read_text(encoding="utf-8")
            metadata = parse_front_matter(content)
            title = str(metadata.get("title", ""))
            tags = metadata.get("tags", [])
        except (OSError, ValueError):
            continue

        post_tokens = set(content_tokens(title)) | set(content_tokens(slug.replace("-", " ")))
        for tag in tags:
            post_tokens.update(content_tokens(str(tag)))

        overlap = rss_tokens & post_tokens
        if not overlap:
            continue
        candidates.append(
            (
                len(overlap),
                {
                    "url": f"/posts/{slug}/",
                    "title": title,
                    "slug": slug,
                    "matched": sorted(overlap),
                },
            )
        )

    candidates.sort(key=lambda item: (-item[0], item[1]["slug"]))
    seen_slugs: set[str] = set()
    results: list[dict] = []
    for _, item in candidates:
        if item["slug"] in seen_slugs:
            continue
        seen_slugs.add(item["slug"])
        results.append(item)
        if len(results) >= limit:
            break
    return results


def format_internal_links_for_prompt(candidates: list[dict]) -> str:
    if not candidates:
        return "- (매칭되는 내부 글이 없습니다. 관련 주제가 있으면 /posts/ 경로로 직접 연결하세요.)"
    lines = []
    for item in candidates:
        matched = ", ".join(item["matched"][:3])
        lines.append(f"- {item['url']} — {item['title']} (매칭: {matched})")
    return "\n".join(lines)


def generate_thumbnail(prompt: str) -> tuple[bytes, str, str]:
    return generate_image_with_fallback(prompt)


def save_thumbnail(slug: str, thumbnail: bytes, title: str) -> tuple[str, str]:
    upload_dir = f"uploads/{slug}"
    os.makedirs(upload_dir, exist_ok=True)

    if Image:
        image_path = f"{upload_dir}/thumbnail.webp"
        img = Image.open(io.BytesIO(thumbnail))
        img = img.resize((1200, 630), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, "WEBP", quality=85)
        write_bytes_atomic(image_path, buffer.getvalue())
        print(f"✅ 이미지 압축 저장 완료 (WebP): {image_path}")
    else:
        image_path = f"{upload_dir}/thumbnail.jpg"
        write_bytes_atomic(image_path, thumbnail)
        print(f"✅ 원본 이미지 저장 완료: {image_path}")

    public_image_path = f"/{image_path}"
    image_md = (
        f"![{title}]({public_image_path} \"{title}\")\n\n"
        f"<p style=\"text-align:center;opacity:0.8;\">\n"
        f"    <small>&copy; AI Generated Image</small>\n"
        f"</p>"
    )
    return public_image_path, image_md


def copy_default_thumbnail(slug: str, title: str) -> tuple[str, str]:
    if not DEFAULT_THUMBNAIL_SOURCE.is_file():
        raise FileNotFoundError(f"기본 썸네일이 없습니다: {DEFAULT_THUMBNAIL_SOURCE}")

    upload_dir = f"uploads/{slug}"
    os.makedirs(upload_dir, exist_ok=True)
    image_path = f"{upload_dir}/thumbnail.webp"
    shutil.copy2(DEFAULT_THUMBNAIL_SOURCE, image_path)
    print(f"✅ 기본 썸네일 복사 완료: {image_path}")

    public_image_path = f"/{image_path}"
    image_md = (
        f"![{title}]({public_image_path} \"{title}\")\n\n"
        f"<p style=\"text-align:center;opacity:0.8;\">\n"
        f"    <small>Default thumbnail</small>\n"
        f"</p>"
    )
    return public_image_path, image_md


def inject_hero_image(content: str, image_md: str) -> str:
    if "[HERO_IMAGE]" in content:
        return content.replace("[HERO_IMAGE]", image_md)
    return content.replace("<!--more-->", f"<!--more-->\n\n{image_md}\n\n-----")


def _unpack_validate_result(
    original_content: str,
    validated: tuple,
) -> tuple[str, dict, str]:
    """Accept (metadata, slug) or (metadata, slug, repaired_content).

    Validators may repair content (broken refs, tone, structure). Returning the
    repaired body as a third tuple element ensures those fixes are persisted.
    """
    if not isinstance(validated, tuple):
        raise TypeError(
            f"validate_fn must return a tuple, got {type(validated).__name__}"
        )
    if len(validated) == 2:
        metadata, slug = validated
        return original_content, metadata, slug
    if len(validated) == 3:
        metadata, slug, repaired = validated
        if not isinstance(repaired, str):
            raise TypeError(
                "validate_fn 3-tuple third element must be repaired content str, "
                f"got {type(repaired).__name__}"
            )
        return repaired, metadata, slug
    raise TypeError(
        "validate_fn must return (metadata, slug) or "
        f"(metadata, slug, content), got length {len(validated)}"
    )


def generate_with_retry(
    prompt: str,
    validate_fn,
    *,
    post_type: str = "deep-dive",
    text_provider: str | None = None,
    system_prompt: str | None = None,
    max_retries: int = 5,
    retry_backoff_seconds: int = 15,
) -> tuple[str, dict, str]:
    providers = resolve_text_providers(post_type, text_provider)
    last_error = None
    current_prompt = prompt
    for attempt in range(1, max_retries + 1):
        provider = pick_provider_for_attempt(providers, attempt)
        model = get_text_model(provider)
        try:
            print(
                f"🔄 AI 글쓰기 API 요청 중... "
                f"({provider}/{model}, 시도 {attempt}/{max_retries})"
            )
            result = llm_generate_text(
                prompt=current_prompt,
                provider=provider,
                model=model,
                system_prompt=system_prompt,
            )
            content = sanitize_generated_content(
                strip_preamble(strip_code_fence(result.text))
            )
            validated = validate_fn(content)
            content, metadata, slug = _unpack_validate_result(content, validated)
            from api_monitor import notify_llm_usage

            notify_llm_usage(
                provider=provider,
                model=model,
                attempt=attempt,
                operation="generate_post",
                slug=slug,
                success=True,
                input_chars=result.input_chars,
                output_chars=result.output_chars,
            )
            return content, metadata, slug
        except Exception as exc:
            from api_monitor import notify_llm_usage

            notify_llm_usage(
                provider=provider,
                model=model,
                attempt=attempt,
                operation="generate_post",
                success=False,
                error=str(exc),
            )
            last_error = exc
            error_msg = str(exc)
            if attempt < max_retries:
                hints = ""
                if "[HERO_IMAGE]" in error_msg:
                    hints += (
                        "\n- After <!--more-->, put [HERO_IMAGE] on its own line, "
                        "then ----- on the next line."
                    )
                if "내부 링크" in error_msg or "/posts/" in error_msg:
                    hints += (
                        "\n- Include at least 2 markdown links like "
                        "[title](/posts/slug/) in the body."
                    )
                if "한 줄 정리" in error_msg or "bullet" in error_msg:
                    hints += (
                        "\n- In '이번 주 한 줄 정리', write 3-4 bullets that start "
                        "with action verbs (확인, 검토, 점검, 적용, 도입, 업데이트)."
                    )
                if "~요" in error_msg or "~다" in error_msg or "문체" in error_msg:
                    hints += (
                        "\n- Use formal '~습니다·입니다' endings only. "
                        "Do not use '~요' or plain '~다' style."
                    )
                if "front matter" in error_msg or "YAML" in error_msg:
                    hints += (
                        "\n- Start with valid YAML front matter (layout, title, slug, "
                        "lang, translation_key, post_type, date, categories, tags, "
                        "description, image) between --- fences."
                    )
                if (
                    "참고문헌" in error_msg
                    or "reference URL" in error_msg
                    or "404" in error_msg
                    or "410" in error_msg
                ):
                    hints += (
                        "\n- Use only real, publicly reachable reference URLs "
                        "(official docs, GitHub repos/releases). Do not invent domains "
                        "or paths. Prefer 2–5 well-known sources."
                    )
                current_prompt = (
                    f"{prompt}\n\n"
                    f"[Previous attempt failed validation: {error_msg}. "
                    f"Fix these issues and regenerate.{hints}]"
                )
            if "503" in error_msg or "UNAVAILABLE" in error_msg:
                wait = retry_backoff_seconds * attempt
                print(f"⚠️ 503 에러(서버 과부하). {wait}초 후 재시도...")
                if attempt < max_retries:
                    time.sleep(wait)
            else:
                print(f"❌ 생성 중 에러 발생 ({provider}): {exc}")
                if attempt < max_retries:
                    time.sleep(5)
    raise RuntimeError(f"포스트 생성에 실패했습니다: {last_error}")


def ko_post_path(slug: str, today: datetime) -> Path:
    year = today.strftime("%Y")
    today_date = today.strftime("%Y-%m-%d")
    return POSTS_DIR / DEFAULT_LANG / year / f"{today_date}-{slug}.md"


def save_ko_post(content: str, slug: str, today: datetime) -> str:
    filename = ko_post_path(slug, today)
    write_text_atomic(filename, content)
    print(f"✅ 포스트 저장 완료: {filename}")
    return str(filename)


def generate_translations(
    source_content: str,
    source_path: Path,
    *,
    translation_provider: str | None = None,
    fail_on_error: bool = False,
) -> None:
    metadata = parse_front_matter(source_content)
    langs = translation_langs_for_metadata(metadata)
    for target_lang in langs:
        try:
            print(f"🌐 {LANG_LABELS[target_lang]} 번역 생성 중...")
            output = _generate_translation(
                source_content,
                source_path,
                target_lang,
                translation_provider=translation_provider,
            )
            print(f"✅ 번역 포스트 저장 완료 ({target_lang}): {output}")
        except Exception as exc:
            if fail_on_error:
                raise RuntimeError(f"{target_lang} 번역 실패: {exc}") from exc
            print(f"⚠️ {target_lang} 번역 실패: {exc}")


def _cleanup_publish_artifacts(slug: str, written_paths: list[Path]) -> None:
    upload_dir = Path(f"uploads/{slug}")
    for path in written_paths:
        try:
            if path.is_file():
                path.unlink()
        except OSError:
            pass
    if upload_dir.is_dir():
        shutil.rmtree(upload_dir, ignore_errors=True)


def publish_post(
    content: str,
    metadata: dict,
    slug: str,
    *,
    image_prompt: str,
    post_type: str,
    today: datetime | None = None,
    require_translations: bool = False,
    translation_provider: str | None = None,
) -> str:
    today = today or get_kst_now()
    raw_title = str(metadata["title"])
    written_paths: list[Path] = []

    content = inject_front_matter_field(content, "lang", DEFAULT_LANG)
    content = inject_front_matter_field(content, "translation_key", slug)
    content = inject_front_matter_field(content, "post_type", post_type)
    content = inject_front_matter_field(content, "ai_generated", True)
    content = inject_front_matter_field(content, "permalink", permalink_for_lang(DEFAULT_LANG, slug))

    try:
        public_image_path = ""
        image_md = ""
        try:
            print(f"🎨 '{raw_title}' 주제로 썸네일 생성 중...")
            thumbnail, image_provider, image_model = generate_thumbnail(image_prompt)
            print(f"  이미지 provider: {image_provider} ({image_model})")
            public_image_path, image_md = save_thumbnail(slug, thumbnail, raw_title)
            from api_monitor import log_thumbnail_usage

            log_thumbnail_usage(
                provider=image_provider,
                model=image_model,
                slug=slug,
                prompt=image_prompt,
                thumbnail=thumbnail,
                success=True,
            )
        except Exception as exc:
            from api_monitor import log_thumbnail_usage

            log_thumbnail_usage(
                provider="unknown",
                model="unknown",
                slug=slug,
                prompt=image_prompt,
                success=False,
                error=str(exc),
            )
            print(f"⚠️ 이미지 생성 실패, 기본 썸네일로 대체합니다: {exc}")
            public_image_path, image_md = copy_default_thumbnail(slug, raw_title)

        written_paths.append(Path(public_image_path.lstrip("/")))

        content = inject_front_matter_field(content, "image", public_image_path)
        content = inject_hero_image(content, image_md)
        ko_path = ko_post_path(slug, today)

        if require_translations:
            langs = translation_langs_for_metadata(parse_front_matter(content))
            pending_writes: list[tuple[Path, str]] = [(ko_path, content)]
            for target_lang in langs:
                print(f"🌐 {LANG_LABELS[target_lang]} 번역 생성 중...")
                translated = _generate_translation_content(
                    content,
                    ko_path,
                    target_lang,
                    translation_provider=translation_provider,
                )
                pending_writes.append((translation_output_path(ko_path, target_lang), translated))

            for path, file_content in pending_writes:
                write_text_atomic(path, file_content)
                written_paths.append(path)
                if path != ko_path:
                    print(f"✅ 번역 포스트 저장 완료 ({path.parent.parent.name}): {path}")
            print(f"✅ 포스트 저장 완료: {ko_path}")
            return str(ko_path)

        filename = save_ko_post(content, slug, today)
        written_paths.append(Path(filename))
        generate_translations(
            content,
            Path(filename),
            translation_provider=translation_provider,
            fail_on_error=False,
        )
        return filename
    except Exception:
        _cleanup_publish_artifacts(slug, written_paths)
        raise