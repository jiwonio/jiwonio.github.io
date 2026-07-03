"""Shared post content analysis helpers (validate + audit scripts)."""

from __future__ import annotations

import re
import subprocess
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import yaml

from post_schema import CODE_BLOCK_PATTERN, FRONT_MATTER_PATTERN, REFERENCE_URL_PATTERN

H2_PATTERN = re.compile(r"^## ", re.MULTILINE)
H3_PATTERN = re.compile(r"^### ", re.MULTILINE)
INTERNAL_POST_LINK = re.compile(r"\]\(/posts/([^)/\s#]+)")
TOKEN_PATTERN = re.compile(r"[a-z0-9가-힣]{3,}")
REFERENCE_HEADINGS = (
    "### 참고문헌",
    "## References",
    "### References",
    "## 参考",
    "### 参考",
    "## 参考文献",
    "### 参考文獻",
    "## 参考资料",
    "### 参考资料",
)
PLAIN_REF_URL_PATTERN = re.compile(r"^-\s+(https?://\S+)", re.MULTILINE)
REF_LINK_LINE = re.compile(
    r'^- \[([^\]]*)\]\(([^)\s"]+)(?:\s+"[^"]*")?\)(?:\{:target="_blank"\})?',
    re.MULTILINE,
)
REFERENCE_HEADING_BY_LANG = {
    "ko": "### 참고문헌",
    "en": "## References",
    "ja": "### 参考文献",
    "zh": "### 参考资料",
}
INFORMAL_KO_LINE = re.compile(
    r"(?:해요|돼요|이에요|예요|어요|아요|할게요|했어요|있어요|없어요)[.!?…]?$"
)
BODY_EXTERNAL_LINK = re.compile(r"(?<!!)\[[^\]]+\]\((https?://[^)\s\"]+)")

TOKEN_STOP_WORDS = frozenset({
    "and", "for", "on", "the", "with", "from", "into", "that", "this", "how",
    "are", "was", "were", "has", "have", "had", "not", "but", "can", "will",
    "your", "our", "all", "any", "its", "new", "now", "get", "use", "using",
    "full", "more", "also", "just", "one", "two", "way", "may", "via", "out",
    "about", "what", "when", "where", "who", "why", "than", "then", "over",
    "aws", "kubernetes",
})


def prose_body(content: str) -> str:
    match = FRONT_MATTER_PATTERN.match(content)
    body = content[match.end() :] if match else content
    return CODE_BLOCK_PATTERN.sub("", body)


def count_markdown_h2(content: str) -> int:
    return len(H2_PATTERN.findall(prose_body(content)))


def count_markdown_h3(content: str) -> int:
    return len(H3_PATTERN.findall(prose_body(content)))


def find_references_section_start(content: str) -> int:
    for heading in REFERENCE_HEADINGS:
        idx = content.find(heading)
        if idx >= 0:
            return idx
    return -1


def normalize_reference_url(url: str) -> str:
    cleaned = url.strip().rstrip(").,;")
    parsed = urlparse(cleaned)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def extract_reference_entries(content: str) -> list[tuple[str, str]]:
    start = find_references_section_start(content)
    if start < 0:
        return []
    section = content[start:]
    entries: list[tuple[str, str]] = []
    seen_urls: set[str] = set()
    for match in REF_LINK_LINE.finditer(section):
        title, url = match.group(1).strip(), normalize_reference_url(match.group(2))
        if url not in seen_urls:
            seen_urls.add(url)
            entries.append((title, url))
    for url in PLAIN_REF_URL_PATTERN.findall(section):
        cleaned = normalize_reference_url(url)
        if cleaned not in seen_urls:
            seen_urls.add(cleaned)
            entries.append(("", cleaned))
    return entries


def extract_reference_urls(content: str) -> list[str]:
    return [url for _, url in extract_reference_entries(content)]


def strip_references_section(content: str) -> str:
    start = find_references_section_start(content)
    if start < 0:
        return content
    return content[:start].rstrip()


def reference_heading_for_lang(lang: str) -> str:
    return REFERENCE_HEADING_BY_LANG.get(lang, "## References")


def rebuild_references_section(content: str, source_content: str, target_lang: str) -> str:
    """Rebuild the references block using source URLs and translated titles when available."""
    source_entries = extract_reference_entries(source_content)
    if not source_entries:
        return content

    translated_entries = extract_reference_entries(content)
    heading = reference_heading_for_lang(target_lang)
    lines = [heading]
    for index, (_, source_url) in enumerate(source_entries):
        title = (
            translated_entries[index][0]
            if index < len(translated_entries) and translated_entries[index][0]
            else source_entries[index][0] or source_url
        )
        lines.append(f'- [{title}]({source_url}){{:target="_blank"}}')

    ref_block = "\n".join(lines) + "\n"
    start = find_references_section_start(content)
    if start >= 0:
        return content[:start].rstrip() + "\n\n" + ref_block
    return content.rstrip() + "\n\n" + ref_block


def extract_body_external_urls(content: str) -> list[str]:
    return BODY_EXTERNAL_LINK.findall(prose_body(content))


def tokenize(text: str) -> set[str]:
    tokens = {token.casefold() for token in TOKEN_PATTERN.findall(text.casefold())}
    return {token for token in tokens if token not in TOKEN_STOP_WORDS and len(token) >= 3}


def title_similarity(a: str, b: str) -> float:
    left = tokenize(a)
    right = tokenize(b)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def find_informal_ko_lines(content: str) -> list[str]:
    prose = prose_body(content)
    hits: list[str] = []
    for line in prose.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|"):
            continue
        if INFORMAL_KO_LINE.search(stripped):
            hits.append(stripped[:120])
    return hits


def get_changed_post_paths(
    posts_dir: Path,
    *,
    include_untracked: bool = True,
    base_ref: str = "HEAD",
) -> list[Path]:
    """Return changed or new markdown files under posts_dir (git working tree)."""
    rel = posts_dir.as_posix()
    if not rel.endswith("/"):
        rel += "/"

    paths: set[Path] = set()
    commands = [
        ["git", "diff", "--name-only", base_ref, "--", rel],
        ["git", "diff", "--name-only", "--cached", base_ref, "--", rel],
    ]
    for command in commands:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
        except (subprocess.SubprocessError, OSError):
            continue
        if result.returncode != 0:
            continue
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.endswith(".md"):
                paths.add(Path(line))

    if include_untracked:
        try:
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard", rel],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
        except (subprocess.SubprocessError, OSError):
            result = None
        if result and result.returncode == 0:
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.endswith(".md"):
                    paths.add(Path(line))

    return sorted(paths)


def build_internal_link_graph(posts_dir: Path) -> tuple[dict[str, set[str]], dict[str, Path]]:
    """Map slug -> inbound link sources; slug -> canonical ko path."""
    slug_sources: dict[str, set[str]] = defaultdict(set)
    slug_paths: dict[str, Path] = {}

    for path in sorted(posts_dir.rglob("*.md")):
        rel = path.as_posix()
        if "/ko/" not in rel and not rel.startswith("_posts/ko/"):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        match = FRONT_MATTER_PATTERN.match(content)
        if not match:
            continue
        metadata = yaml.safe_load(match.group(1)) or {}
        slug = str(metadata.get("slug") or path.stem[11:]).strip()
        normalized = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
        slug_paths[normalized] = path

    for path in sorted(posts_dir.rglob("*.md")):
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        source_slug = path.stem[11:] if len(path.stem) > 11 else path.stem
        for target in INTERNAL_POST_LINK.findall(content):
            normalized = re.sub(r"[^a-z0-9]+", "-", target.lower()).strip("-")
            slug_sources[normalized].add(source_slug)

    return slug_sources, slug_paths


def pagefind_language_counts(site_dir: Path) -> dict[str, int]:
    """Count Pagefind index fragments that declare a lang filter (best-effort)."""
    pagefind_dir = site_dir / "pagefind"
    if not pagefind_dir.is_dir():
        return {}

    counts: dict[str, int] = defaultdict(int)
    for path in pagefind_dir.rglob("*.pf_fragment"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lang in ("ko", "en", "ja", "zh"):
            if f'"lang":"{lang}"' in text or f'"lang": "{lang}"' in text:
                counts[lang] += 1
    return dict(counts)