import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from http.client import InvalidURL
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

import yaml

from blog_i18n import DEFAULT_LANG, resolve_effective_date, translation_langs_for_metadata
from post_analysis import (
    count_markdown_h2,
    extract_reference_urls as analysis_extract_reference_urls,
    get_changed_post_paths,
    prose_body,
)
from post_common import find_invalid_internal_post_slugs, get_existing_ko_slugs
from post_schema import (
    CODE_BLOCK_PATTERN,
    EXTERNAL_IMAGE_PATTERN,
    FRONT_MATTER_PATTERN,
    PROMPT_LEAK_PHRASES,
    UNEXPECTED_SCRIPT_PATTERN,
    has_standalone_line,
)

REQUIRED_FIELDS = ("layout", "title", "tags", "image", "categories", "post_type")
LANG_PATH = re.compile(r"(?:^|/)_posts/(en|ja|zh|ko)(?:/|$)")
INTERNAL_LINK_PATTERN = re.compile(r"\]\(/posts/([^)/\s]+)")
REFERENCE_URL_PATTERN = re.compile(r"\[[^\]]+\]\((https?://[^)\s\"]+)")
BODY_EXTERNAL_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\((https?://[^)\s\"]+)")
KOREAN_PATTERN = re.compile(r"[가-힣]")
KANA_PATTERN = re.compile(r"[\u3040-\u30ff]")
JAPANESE_PATTERN = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]")
MIN_KO_CHARS = 40
MIN_JA_CHARS = 20
MIN_ZH_CHARS = 20
MAX_EN_KO_CHARS = 120
REF_CHECK_TIMEOUT = 8
H2_COUNT_TOLERANCE = 3
REF_URL_COUNT_TOLERANCE = 2
# Hosts that block automated HEAD/GET checks but serve valid pages in browsers.
REF_URL_SKIP_HOSTS = frozenset({
    "marketplace.visualstudio.com",
    "medium.com",
    "www.gravatar.com",
    "gravatar.com",
    "unsplash.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "news.ycombinator.com",
    "community.chocolatey.org",
    "visualstudio.microsoft.com",
})


def detect_lang(path: Path, metadata: dict) -> str:
    if metadata.get("lang"):
        return str(metadata["lang"]).strip()
    if LANG_PATH.search(path.as_posix()):
        return LANG_PATH.search(path.as_posix()).group(1)
    return DEFAULT_LANG


def find_unexpected_scripts(content):
    prose = CODE_BLOCK_PATTERN.sub("", content)
    return sorted(set(UNEXPECTED_SCRIPT_PATTERN.findall(prose)))


def extract_body_external_urls(content: str) -> list[str]:
    prose = prose_body(content)
    return BODY_EXTERNAL_LINK_PATTERN.findall(prose)


def extract_reference_urls(content: str) -> list[str]:
    return analysis_extract_reference_urls(content)


def validate_translation_structure(translation_groups: dict) -> list[str]:
    """Compare H2 and reference URL counts across translation_key groups."""
    errors: list[str] = []

    for key, langs in translation_groups.items():
        source = langs.get(DEFAULT_LANG)
        if not source or len(langs) < 2:
            continue

        source_path, _source_meta = source
        try:
            source_content = source_path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{source_path}: cannot read source for structure check: {exc}")
            continue

        source_h2 = count_markdown_h2(source_content)
        source_refs = len(extract_reference_urls(source_content))

        for lang, (path, _metadata) in langs.items():
            if lang == DEFAULT_LANG:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except OSError as exc:
                errors.append(f"{path}: cannot read translation for structure check: {exc}")
                continue

            h2_count = count_markdown_h2(content)
            ref_count = len(extract_reference_urls(content))

            if source_h2 > 0:
                min_h2 = max(1, source_h2 - H2_COUNT_TOLERANCE)
                max_h2 = source_h2 + H2_COUNT_TOLERANCE
                if not (min_h2 <= h2_count <= max_h2):
                    errors.append(
                        f"translation structure mismatch for '{key}': "
                        f"{DEFAULT_LANG} has {source_h2} H2 sections but {lang} has {h2_count} "
                        f"(expected {min_h2}~{max_h2}, {path})"
                    )

            if source_refs > 0 and abs(ref_count - source_refs) > REF_URL_COUNT_TOLERANCE:
                errors.append(
                    f"translation reference count mismatch for '{key}': "
                    f"{DEFAULT_LANG} has {source_refs} reference URLs but {lang} has {ref_count} "
                    f"(tolerance ±{REF_URL_COUNT_TOLERANCE}, {path})"
                )

    return errors


def validate_language_content(lang: str, content: str) -> str | None:
    prose = prose_body(content)
    if lang == DEFAULT_LANG:
        if len(KOREAN_PATTERN.findall(prose)) < MIN_KO_CHARS:
            return f"ko post needs at least {MIN_KO_CHARS} Korean characters in prose"
    elif lang == "en":
        if len(KOREAN_PATTERN.findall(prose)) > MAX_EN_KO_CHARS:
            return f"en translation contains too much Korean text (> {MAX_EN_KO_CHARS} chars)"
    elif lang == "ja":
        if len(JAPANESE_PATTERN.findall(prose)) < MIN_JA_CHARS:
            return f"ja translation needs at least {MIN_JA_CHARS} Japanese characters in prose"
        if not KANA_PATTERN.search(prose):
            return "ja translation must include Japanese kana (hiragana/katakana)"
    elif lang == "zh":
        if len(CHINESE_PATTERN.findall(prose)) < MIN_ZH_CHARS:
            return f"zh translation needs at least {MIN_ZH_CHARS} Chinese characters in prose"
        if KANA_PATTERN.search(prose):
            return "zh translation must not contain Japanese kana"
    return None


def encode_url(url: str) -> str:
    parts = urlsplit(url.strip())
    path = quote(parts.path, safe="/%:@")
    query = quote(parts.query, safe="=&%?") if parts.query else parts.query
    return urlunsplit((parts.scheme, parts.netloc, path, query, parts.fragment))


def fetch_reference_status(url: str) -> int | None:
    headers = {"User-Agent": "blog.jiwon.io-validate/1.0"}
    encoded = encode_url(url)
    for method in ("HEAD", "GET"):
        request = Request(encoded, method=method, headers=headers)
        try:
            with urlopen(request, timeout=REF_CHECK_TIMEOUT) as response:
                return response.status
        except HTTPError as exc:
            if method == "HEAD" and exc.code in {403, 405, 429, 500, 502, 503}:
                continue
            return exc.code
        except (URLError, InvalidURL, ValueError):
            if method == "HEAD":
                continue
            return None
    return None


def check_reference_url(url: str) -> str | None:
    url = url.strip().rstrip(")")
    if not url.startswith(("http://", "https://")):
        return "reference URL must start with http:// or https://"
    try:
        parts = urlsplit(url)
    except ValueError:
        return "reference URL is malformed"
    host = parts.netloc.lower()
    if not host or any(ord(char) < 32 for char in host):
        return "reference URL has invalid host"
    if host in REF_URL_SKIP_HOSTS:
        return None
    status = fetch_reference_status(url)
    if status is None:
        return None
    if status in {404, 410}:
        return f"reference URL returned HTTP {status}"
    return None


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

    post_type = str(metadata.get("post_type", "")).strip()
    if post_type != "deep-dive":
        raise ValueError("post_type must be 'deep-dive'")

    tags = metadata["tags"]
    if not isinstance(tags, list) or not all(isinstance(tag, str) and tag.strip() for tag in tags):
        raise ValueError("tags must be a non-empty list of strings")

    if not metadata.get("description") and not metadata.get("meta"):
        raise ValueError("description or meta is required for SEO")

    categories = metadata.get("categories")
    if not isinstance(categories, list) or not all(
        isinstance(category, str) and category.strip() for category in categories
    ):
        raise ValueError("categories must be a non-empty list of strings")

    image = metadata.get("image")
    if not isinstance(image, str) or not image.startswith("/uploads/"):
        raise ValueError("image must be an absolute site path starting with /uploads/")

    return content, metadata


def validate_image_file(image_path, site_root):
    relative_path = image_path.lstrip("/")
    file_path = site_root / relative_path
    if not file_path.is_file():
        raise ValueError(f"image file not found: {image_path}")


def validate_posts(
    posts_dir,
    site_root=None,
    *,
    check_ref_urls: bool = False,
    check_external_urls: bool = False,
    changed_only: bool = False,
    changed_base_ref: str = "HEAD",
):
    errors = []
    tag_spellings = defaultdict(set)
    output_paths = defaultdict(list)
    translation_groups = defaultdict(dict)
    if site_root is None:
        site_root = posts_dir.parent

    checked_reference_urls: dict[str, str | None] = {}
    changed_paths: set[Path] | None = None
    if changed_only:
        changed_paths = set(get_changed_post_paths(posts_dir, base_ref=changed_base_ref))
        if not changed_paths:
            print("No changed posts detected; skipping validation.")
            return []

    all_paths = sorted(posts_dir.rglob("*.md"))
    for path in all_paths:
        try:
            _, metadata = load_post(path)
        except (OSError, UnicodeError, yaml.YAMLError, ValueError):
            continue
        lang = detect_lang(path, metadata)
        slug = metadata.get("slug") or path.stem[11:]
        normalized_slug = re.sub(r"[^a-z0-9]+", "-", str(slug).lower()).strip("-")
        translation_key = metadata.get("translation_key") or normalized_slug
        translation_groups[translation_key][lang] = (path, metadata)

    paths_to_scan = all_paths
    if changed_paths is not None:
        paths_to_scan = [path for path in all_paths if path in changed_paths]

    for path in paths_to_scan:
        try:
            content, metadata = load_post(path)
            validate_image_file(metadata["image"], site_root)
        except (OSError, UnicodeError, yaml.YAMLError, ValueError) as exc:
            errors.append(f"{path}: {exc}")
            continue

        lang = detect_lang(path, metadata)
        for tag in metadata["tags"]:
            tag_spellings[tag.casefold()].add(tag)
            tag_text = str(tag)
            if lang == "en" and KOREAN_PATTERN.search(tag_text):
                errors.append(f"{path}: en post has Korean tag '{tag}' (localize to English)")
            elif lang == "ja" and KOREAN_PATTERN.search(tag_text):
                errors.append(f"{path}: ja post has Korean tag '{tag}' (localize to Japanese)")
            elif lang == "zh" and KOREAN_PATTERN.search(tag_text):
                errors.append(f"{path}: zh post has Korean tag '{tag}' (localize to Chinese)")

        slug = metadata.get("slug") or path.stem[11:]
        normalized_slug = re.sub(r"[^a-z0-9]+", "-", str(slug).lower()).strip("-")
        output_paths[(lang, normalized_slug)].append(path)

        if not has_standalone_line(content, "<!--more-->"):
            errors.append(f"{path}: missing standalone <!--more--> excerpt separator")

        if "[HERO_IMAGE]" in content:
            errors.append(f"{path}: unresolved [HERO_IMAGE] placeholder")

        leaked = [phrase for phrase in PROMPT_LEAK_PHRASES if phrase in content]
        if leaked:
            errors.append(f"{path}: prompt instruction text leaked into body: {', '.join(leaked)}")

        if lang == DEFAULT_LANG:
            stray_chars = find_unexpected_scripts(content)
            if stray_chars:
                errors.append(f"{path}: unexpected characters mixed into text: {', '.join(stray_chars)}")

        if EXTERNAL_IMAGE_PATTERN.search(content):
            errors.append(f"{path}: contains an external image link")

        language_error = validate_language_content(lang, content)
        if language_error:
            errors.append(f"{path}: {language_error}")

        urls_to_check: list[str] = []
        if check_ref_urls:
            urls_to_check.extend(extract_reference_urls(content))
        if check_external_urls:
            urls_to_check.extend(extract_body_external_urls(content))

        for ref_url in urls_to_check:
            if not ref_url.startswith(("http://", "https://")):
                errors.append(f"{path}: invalid external URL format: {ref_url}")
                continue
            if ref_url not in checked_reference_urls:
                checked_reference_urls[ref_url] = check_reference_url(ref_url)
            ref_error = checked_reference_urls[ref_url]
            if ref_error:
                errors.append(f"{path}: {ref_error} for {ref_url}")

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

    if changed_paths is None:
        for key, langs in translation_groups.items():
            source = langs.get(DEFAULT_LANG)
            if not source:
                continue

            source_path, source_meta = source
            expected_langs = set(translation_langs_for_metadata(source_meta))
            present_langs = set(langs)
            missing_langs = sorted(expected_langs - present_langs)
            if missing_langs:
                errors.append(
                    f"missing translations for '{key}' ({source_path.name}): "
                    + ", ".join(missing_langs)
                )

            if len(langs) < 2:
                continue

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
        errors.extend(validate_translation_structure(translation_groups))
    else:
        affected_keys: set[str] = set()
        for path in changed_paths:
            langs = translation_groups
            for key, group in langs.items():
                if any(item_path == path for item_path, _meta in group.values()):
                    affected_keys.add(key)
        partial_groups = {
            key: translation_groups[key]
            for key in affected_keys
            if key in translation_groups
        }
        errors.extend(validate_translation_structure(partial_groups))

    ko_slug_set = set(get_existing_ko_slugs())
    internal_link_scan = paths_to_scan if changed_paths is not None else sorted(posts_dir.rglob("*.md"))
    for path in internal_link_scan:
        try:
            content, metadata = load_post(path)
        except (OSError, UnicodeError, yaml.YAMLError, ValueError):
            continue
        for invalid_slug in find_invalid_internal_post_slugs(content, ko_slug_set):
            errors.append(f"{path}: broken internal link to /posts/{invalid_slug}/")

    return errors


def audit_translation_completeness(posts_dir) -> list[str]:
    """Report missing translations per post_type policy (deep-dive)."""
    errors = []
    translation_groups: dict[str, dict] = defaultdict(dict)

    for path in sorted(posts_dir.rglob("*.md")):
        try:
            _, metadata = load_post(path)
        except (OSError, UnicodeError, yaml.YAMLError, ValueError):
            continue

        lang = detect_lang(path, metadata)
        slug = metadata.get("slug") or path.stem[11:]
        normalized_slug = re.sub(r"[^a-z0-9]+", "-", str(slug).lower()).strip("-")
        translation_key = metadata.get("translation_key") or normalized_slug
        translation_groups[translation_key][lang] = (path, metadata)

    for key, langs in translation_groups.items():
        source = langs.get(DEFAULT_LANG)
        if not source:
            continue

        source_path, source_meta = source
        expected_langs = set(translation_langs_for_metadata(source_meta))
        missing_langs = sorted(expected_langs - set(langs))
        if missing_langs:
            post_type = str(source_meta.get("post_type", "deep-dive")).strip()
            errors.append(
                f"missing translations for '{key}' ({post_type}, {source_path.name}): "
                + ", ".join(missing_langs)
            )

    return errors


def audit_deep_dive_translations(posts_dir) -> list[str]:
    """Backward-compatible alias: deep-dive posts only."""
    return [
        error
        for error in audit_translation_completeness(posts_dir)
        if "deep-dive" in error
    ]


def main():
    parser = argparse.ArgumentParser(description="Validate Jekyll post metadata and archive paths.")
    parser.add_argument("--posts-dir", type=Path, default=Path("_posts"))
    parser.add_argument(
        "--check-ref-urls",
        action="store_true",
        help="HEAD-check reference URLs in posts (slower, needs network)",
    )
    parser.add_argument(
        "--check-external-urls",
        action="store_true",
        help="HEAD-check all external markdown links in post bodies (slower, needs network)",
    )
    parser.add_argument(
        "--audit-translations",
        action="store_true",
        help="Audit translation completeness for all post types",
    )
    parser.add_argument(
        "--audit-deep-dive",
        action="store_true",
        help="Audit deep-dive translation completeness only (legacy alias)",
    )
    parser.add_argument(
        "--changed-only",
        action="store_true",
        help="Validate only git-changed or untracked posts under --posts-dir",
    )
    parser.add_argument(
        "--changed-base-ref",
        default="HEAD",
        help="Git base ref for --changed-only (default: HEAD)",
    )
    args = parser.parse_args()

    if args.audit_translations:
        errors = audit_translation_completeness(args.posts_dir)
        label = "Translation audit"
    elif args.audit_deep_dive:
        errors = audit_deep_dive_translations(args.posts_dir)
        label = "Deep-dive translation audit"
    else:
        errors = None

    if errors is not None:
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"{label} passed.")
        return 0

    errors = validate_posts(
        args.posts_dir,
        check_ref_urls=args.check_ref_urls,
        check_external_urls=args.check_external_urls,
        changed_only=args.changed_only,
        changed_base_ref=args.changed_base_ref,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Post validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())