"""LLM API 호출 모니터링 (GitHub Actions notice + 선택적 Slack 알림)."""

from __future__ import annotations

import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen

SLACK_TIMEOUT = 8


def notify_llm_usage(
    *,
    provider: str = "gemini",
    model: str,
    attempt: int,
    operation: str,
    slug: str | None = None,
    success: bool = True,
    error: str | None = None,
) -> None:
    payload = {
        "provider": provider,
        "model": model,
        "attempt": attempt,
        "operation": operation,
        "slug": slug or "",
        "success": success,
        "error": error or "",
    }
    print(
        "::notice::"
        + " ".join(
            f"{key}={json.dumps(value, ensure_ascii=False)}"
            for key, value in payload.items()
            if value != ""
        )
    )

    webhook = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not webhook:
        return

    status = "성공" if success else "실패"
    lines = [
        f"*AI API {status}* ({provider})",
        f"- operation: `{operation}`",
        f"- model: `{model}`",
        f"- attempt: {attempt}",
    ]
    if slug:
        lines.append(f"- slug: `{slug}`")
    if error:
        lines.append(f"- error: {error}")

    body = json.dumps({"text": "\n".join(lines)}).encode("utf-8")
    request = Request(
        webhook,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=SLACK_TIMEOUT):
            pass
    except URLError as exc:
        print(f"::warning::slack_notification_failed={exc}")


# 하위 호환 alias
notify_gemini_usage = notify_llm_usage