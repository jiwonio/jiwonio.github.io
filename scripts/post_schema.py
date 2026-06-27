"""Shared post constants and sanitization helpers (no blog_i18n imports)."""

from __future__ import annotations

import re
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parent.parent / "_posts"

FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
PROMPT_LEAK_PHRASES = ("Front Matter", "지침일 뿐이며", "결과물에 그대로 옮겨")
EXTERNAL_IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\(https?://[^)]+\)")
REFERENCE_URL_PATTERN = re.compile(r"\[[^\]]+\]\((https?://[^)\s\"]+)")
CODE_BLOCK_PATTERN = re.compile(r"```.*?```", re.DOTALL)
UNEXPECTED_SCRIPT_PATTERN = re.compile(r"[぀-ヿｦ-ﾝ]")

_SLACK_WEBHOOK_PATTERN = re.compile(
    r"https://hooks\.slack\.com/services/[A-Za-z0-9]+/[A-Za-z0-9]+/[A-Za-z0-9]+"
)
_SECRET_KV_PATTERN = re.compile(
    r'(?i)(api_key|secret_key|password|token)\s*[:=]\s*["\'][A-Za-z0-9_-]{15,}["\']'
)
_STRIPE_KEY_PATTERN = re.compile(r"sk-[a-zA-Z0-9_-]{20,}")
_GITHUB_TOKEN_PATTERN = re.compile(r"ghp_[a-zA-Z0-9]{20,}")
_AWS_KEY_PATTERN = re.compile(r"AKIA[0-9A-Z]{16}")
_BEARER_TOKEN_PATTERN = re.compile(r"(?i)Bearer\s+[A-Za-z0-9._\-]{20,}")
_PEM_BLOCK_PATTERN = re.compile(
    r"-----BEGIN (?:RSA )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA )?PRIVATE KEY-----"
)

_SLACK_ERROR_MAX_LEN = 500


def has_standalone_line(content: str, marker: str) -> bool:
    return any(line.strip() == marker for line in content.splitlines())


def extract_reference_urls(content: str) -> list[str]:
    refs_start = content.find("### 참고문헌")
    if refs_start < 0:
        return []
    section = content[refs_start:]
    return REFERENCE_URL_PATTERN.findall(section)


def strip_references_section(content: str) -> str:
    refs_start = content.find("### 참고문헌")
    if refs_start < 0:
        return content
    return content[:refs_start].rstrip()


def sanitize_generated_content(content: str) -> str:
    content = _SLACK_WEBHOOK_PATTERN.sub(
        "https://hooks.slack.com/services/YOUR_WORKSPACE/YOUR_CHANNEL/YOUR_TOKEN",
        content,
    )
    content = _SECRET_KV_PATTERN.sub(r'\1: "YOUR_DUMMY_SECRET_HERE"', content)
    content = _STRIPE_KEY_PATTERN.sub("sk-YOUR_STRIPE_SECRET_KEY", content)
    content = _GITHUB_TOKEN_PATTERN.sub("ghp_YOUR_GITHUB_TOKEN", content)
    content = _AWS_KEY_PATTERN.sub("AKIAYOURAWSACCESSKEY", content)
    content = _BEARER_TOKEN_PATTERN.sub("Bearer YOUR_TOKEN_HERE", content)
    content = _PEM_BLOCK_PATTERN.sub(
        "-----BEGIN PRIVATE KEY-----\nYOUR_DUMMY_KEY\n-----END PRIVATE KEY-----",
        content,
    )
    return content


def _redact_secrets(text: str) -> str:
    text = _SLACK_WEBHOOK_PATTERN.sub("https://hooks.slack.com/services/[REDACTED]", text)
    text = _SECRET_KV_PATTERN.sub(r"\1: [REDACTED]", text)
    text = _STRIPE_KEY_PATTERN.sub("sk-[REDACTED]", text)
    text = _GITHUB_TOKEN_PATTERN.sub("ghp_[REDACTED]", text)
    text = _AWS_KEY_PATTERN.sub("AKIA[REDACTED]", text)
    text = _BEARER_TOKEN_PATTERN.sub("Bearer [REDACTED]", text)
    text = _PEM_BLOCK_PATTERN.sub("[REDACTED PEM BLOCK]", text)
    return text


def sanitize_error_for_slack(error: str, *, max_len: int = _SLACK_ERROR_MAX_LEN) -> str:
    redacted = _redact_secrets(error.strip())
    if len(redacted) <= max_len:
        return redacted
    return redacted[: max_len - 3] + "..."


def write_text_atomic(path: Path | str, content: str, *, encoding: str = "utf-8") -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.with_suffix(target.suffix + ".tmp")
    tmp_path.write_text(content, encoding=encoding)
    tmp_path.replace(target)


def write_bytes_atomic(path: Path | str, data: bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.with_suffix(target.suffix + ".tmp")
    tmp_path.write_bytes(data)
    tmp_path.replace(target)