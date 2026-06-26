"""Summarize LLM usage from jsonl log or GitHub Actions workflow notices."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from models_config import LLM_MONTHLY_BUDGET_USD

SITE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG = SITE_ROOT / "llm-usage.jsonl"
LLM_USAGE_MARKER = "llm_usage="
ACTION_WORKFLOWS = (
    "scheduled_ai_post.yml",
    "backfill_translations.yml",
    "sync_maintenance.yml",
    "thumbnail_check.yml",
)


def is_production_llm_record(record: dict) -> bool:
    """Skip unittest/dry-run notices that share the same workflow logs."""
    operation = str(record.get("operation", ""))
    slug = str(record.get("slug", ""))
    input_chars = int(record.get("input_chars", 0) or 0)
    if operation == "generate_post" and slug in {"", "demo"} and input_chars == 0:
        return False
    return True


def parse_llm_usage_line(line: str) -> dict | None:
    """Parse llm_usage JSON from local (::notice::) or Actions (##[notice]) log lines."""
    index = line.find(LLM_USAGE_MARKER)
    if index < 0:
        return None
    payload = line[index + len(LLM_USAGE_MARKER) :].strip()
    try:
        record = json.loads(payload)
    except json.JSONDecodeError:
        return None
    return record if isinstance(record, dict) else None


def parse_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def summarize(records: list[dict]) -> dict:
    total = len(records)
    successes = sum(1 for record in records if record.get("success", True))
    by_provider: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"calls": 0, "cost": 0.0, "success": 0}
    )
    by_model: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"calls": 0, "cost": 0.0, "success": 0}
    )
    total_cost = 0.0

    for record in records:
        provider = str(record.get("provider", "unknown"))
        model = str(record.get("model", "unknown"))
        cost = float(record.get("estimated_cost_usd", 0) or 0)
        success = bool(record.get("success", True))

        by_provider[provider]["calls"] += 1
        by_provider[provider]["cost"] += cost
        if success:
            by_provider[provider]["success"] += 1

        by_model[model]["calls"] += 1
        by_model[model]["cost"] += cost
        if success:
            by_model[model]["success"] += 1

        total_cost += cost

    return {
        "total_calls": total,
        "successes": successes,
        "success_rate": (successes / total * 100) if total else 0.0,
        "total_cost_usd": round(total_cost, 4),
        "by_provider": {key: dict(value) for key, value in by_provider.items()},
        "by_model": {key: dict(value) for key, value in by_model.items()},
    }


def format_summary(summary: dict) -> str:
    lines = [
        "LLM Usage Summary",
        f"Total calls: {summary['total_calls']}",
        (
            f"Success rate: {summary['success_rate']:.1f}% "
            f"({summary['successes']}/{summary['total_calls']})"
        ),
        f"Estimated cost: ${summary['total_cost_usd']:.4f}",
        "",
        "By provider:",
    ]
    if summary["by_provider"]:
        for provider, stats in sorted(summary["by_provider"].items()):
            calls = int(stats["calls"])
            rate = int(stats["success"]) / calls * 100 if calls else 0
            lines.append(
                f"  {provider}: {calls} calls, {rate:.0f}% success, ${stats['cost']:.4f}"
            )
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append("By model:")
    if summary["by_model"]:
        for model, stats in sorted(summary["by_model"].items()):
            calls = int(stats["calls"])
            rate = int(stats["success"]) / calls * 100 if calls else 0
            lines.append(
                f"  {model}: {calls} calls, {rate:.0f}% success, ${stats['cost']:.4f}"
            )
    else:
        lines.append("  (none)")
    return "\n".join(lines)


def post_slack(text: str) -> None:
    webhook = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not webhook:
        print("SLACK_WEBHOOK_URL not set, skipping Slack notification.")
        return
    body = json.dumps({"text": text}).encode("utf-8")
    request = Request(
        webhook,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10):
        pass


def gh_env() -> dict[str, str]:
    env = dict(os.environ)
    token = env.get("GH_TOKEN") or env.get("GITHUB_TOKEN", "")
    if token:
        env["GH_TOKEN"] = token
    return env


def fetch_from_actions(days: int) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    records: list[dict] = []

    for workflow_file in ACTION_WORKFLOWS:
        try:
            result = subprocess.run(
                [
                    "gh",
                    "run",
                    "list",
                    "--workflow",
                    workflow_file,
                    "--limit",
                    "50",
                    "--json",
                    "databaseId,createdAt",
                ],
                capture_output=True,
                text=True,
                check=True,
                env=gh_env(),
            )
            runs = json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as exc:
            print(f"::warning::Failed to list runs for {workflow_file}: {exc}", file=sys.stderr)
            continue

        for run in runs:
            created = run.get("createdAt", "")
            if created:
                created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if created_at < since:
                    continue

            run_id = run["databaseId"]
            try:
                log_result = subprocess.run(
                    ["gh", "run", "view", str(run_id), "--log"],
                    capture_output=True,
                    text=True,
                    timeout=180,
                    env=gh_env(),
                )
            except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
                print(f"::warning::Log fetch failed for run {run_id}: {exc}", file=sys.stderr)
                continue

            if log_result.returncode != 0:
                continue

            for line in log_result.stdout.splitlines():
                record = parse_llm_usage_line(line)
                if record and is_production_llm_record(record):
                    records.append(record)

    return records


def check_budget(summary: dict, budget: float) -> bool:
    total_calls = summary["total_calls"]
    if total_calls == 0:
        return True

    avg_cost = summary["total_cost_usd"] / total_calls
    monthly_estimate = avg_cost * total_calls
    if monthly_estimate > budget:
        print(
            f"::warning::LLM monthly estimate ${monthly_estimate:.2f} "
            f"exceeds budget ${budget:.2f}"
        )
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize LLM usage")
    parser.add_argument("log_file", nargs="?", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--from-actions", action="store_true")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--slack", action="store_true")
    parser.add_argument("--warn-budget", type=float, default=LLM_MONTHLY_BUDGET_USD)
    args = parser.parse_args(argv)

    if args.from_actions:
        records = fetch_from_actions(args.days)
    else:
        records = parse_jsonl(args.log_file)

    summary = summarize(records)
    text = format_summary(summary)
    print(text)
    check_budget(summary, args.warn_budget)

    if args.slack:
        post_slack(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())