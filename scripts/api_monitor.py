"""LLM API 호출 모니터링 (GitHub Actions notice + 선택적 Slack 알림)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from models_config import DEFAULT_COST_PER_1M, ESTIMATED_COST_PER_1M
from post_schema import sanitize_error_for_slack

SLACK_TIMEOUT = 8
SITE_ROOT = Path(__file__).resolve().parent.parent


def estimate_cost_usd(model: str, input_chars: int, output_chars: int) -> float:
    rates = ESTIMATED_COST_PER_1M.get(model, DEFAULT_COST_PER_1M)
    return round(
        (input_chars / 1_000_000) * rates["input"]
        + (output_chars / 1_000_000) * rates["output"],
        6,
    )


def append_usage_log(record: dict, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def notify_llm_usage(
    *,
    provider: str = "gemini",
    model: str,
    attempt: int,
    operation: str,
    slug: str | None = None,
    success: bool = True,
    error: str | None = None,
    input_chars: int | None = None,
    output_chars: int | None = None,
) -> None:
    in_chars = input_chars or 0
    out_chars = output_chars or 0
    estimated_cost_usd = estimate_cost_usd(model, in_chars, out_chars) if (in_chars or out_chars) else 0.0

    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "model": model,
        "attempt": attempt,
        "operation": operation,
        "slug": slug or "",
        "success": success,
        "error": error or "",
        "input_chars": in_chars,
        "output_chars": out_chars,
        "estimated_cost_usd": estimated_cost_usd,
    }
    print(f"::notice::llm_usage={json.dumps(payload, ensure_ascii=False)}")

    log_env = os.environ.get("LLM_USAGE_LOG", "").strip()
    log_path = Path(log_env) if log_env else SITE_ROOT / "llm-usage.jsonl"
    if not log_path.is_absolute():
        log_path = SITE_ROOT / log_path
    append_usage_log(payload, log_path)

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
    if in_chars or out_chars:
        lines.append(f"- chars: in={in_chars}, out={out_chars}, est=${estimated_cost_usd:.4f}")
    if error:
        lines.append(f"- error: {sanitize_error_for_slack(error)}")

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