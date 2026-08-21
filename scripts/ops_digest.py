"""Weekly operational digest: ops, pipeline, URL health, and content strategy."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from audit_content_quality import collect_content_warnings
from audit_discoverability import collect_link_health
from models_config import LLM_MONTHLY_BUDGET_USD
from usage_report import (
    fetch_from_actions,
    gh_env,
    post_slack,
    summarize,
)
from validate_posts import audit_translation_completeness, validate_posts

SITE_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = SITE_ROOT / "_posts"

MONITORED_WORKFLOWS = (
    ("jekyll.yml", "Deploy"),
    ("scheduled_ai_post.yml", "AI Post"),
    ("sync_maintenance.yml", "Sync"),
    ("weekly_ops.yml", "Weekly Ops"),
    ("weekly_site_health.yml", "Site Health"),
    ("e2e.yml", "E2E"),
    ("backfill_translations.yml", "Backfill"),
)

PIPELINE_WORKFLOWS = ("scheduled_ai_post.yml", "backfill_translations.yml")


def list_workflow_runs(workflow_file: str, days: int) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    try:
        result = subprocess.run(
            [
                "gh",
                "run",
                "list",
                "--workflow",
                workflow_file,
                "--limit",
                "80",
                "--json",
                "databaseId,conclusion,createdAt,displayTitle,event,status",
            ],
            capture_output=True,
            text=True,
            check=True,
            env=gh_env(),
            timeout=60,
        )
        runs = json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError, subprocess.TimeoutExpired):
        return []

    filtered: list[dict] = []
    for run in runs:
        created = run.get("createdAt", "")
        if not created:
            continue
        created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
        if created_at >= since:
            filtered.append(run)
    return filtered


def summarize_workflow_runs(days: int) -> dict:
    workflows: dict[str, dict] = {}
    totals = {"success": 0, "failure": 0, "other": 0, "runs": 0}

    for workflow_file, label in MONITORED_WORKFLOWS:
        runs = list_workflow_runs(workflow_file, days)
        success = sum(1 for run in runs if run.get("conclusion") == "success")
        failure = sum(1 for run in runs if run.get("conclusion") == "failure")
        other = len(runs) - success - failure
        workflows[label] = {
            "file": workflow_file,
            "runs": len(runs),
            "success": success,
            "failure": failure,
            "other": other,
        }
        totals["runs"] += len(runs)
        totals["success"] += success
        totals["failure"] += failure
        totals["other"] += other

    return {"workflows": workflows, "totals": totals}


def list_new_ko_posts(days: int) -> list[str]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date()
    files: list[str] = []
    date_prefix = re.compile(r"(\d{4}-\d{2}-\d{2})")

    for path in sorted(POSTS_DIR.rglob("*.md")):
        rel = path.relative_to(SITE_ROOT).as_posix()
        if not rel.startswith("_posts/ko/"):
            continue
        match = date_prefix.match(path.name)
        if not match:
            continue
        post_date = datetime.strptime(match.group(1), "%Y-%m-%d").date()
        if post_date >= cutoff:
            files.append(rel)
    return files


def classify_post_file(path: str) -> str:
    return "deep-dive"


def collect_ops_section(days: int, llm_records: list[dict]) -> dict:
    workflow_summary = summarize_workflow_runs(days)
    new_posts = list_new_ko_posts(days)
    post_types = defaultdict(int)
    for path in new_posts:
        post_types[classify_post_file(path)] += 1

    translation_gaps = audit_translation_completeness(POSTS_DIR)
    llm_summary = summarize(llm_records, period_days=days)

    return {
        "days": days,
        "workflows": workflow_summary,
        "new_posts": new_posts,
        "post_types": dict(post_types),
        "translation_gaps": len(translation_gaps),
        "llm": llm_summary,
    }


def collect_pipeline_section(days: int, llm_records: list[dict]) -> dict:
    pipeline_runs: dict[str, dict] = {}
    for workflow_file, label in (
        ("scheduled_ai_post.yml", "AI Post"),
        ("backfill_translations.yml", "Backfill"),
    ):
        runs = list_workflow_runs(workflow_file, days)
        pipeline_runs[label] = {
            "runs": len(runs),
            "success": sum(1 for run in runs if run.get("conclusion") == "success"),
            "failure": sum(1 for run in runs if run.get("conclusion") == "failure"),
        }

    by_slug: dict[str, list[dict]] = defaultdict(list)
    by_operation: dict[str, int] = defaultdict(int)
    by_provider: dict[str, int] = defaultdict(int)
    fallback_slugs: list[str] = []

    for record in llm_records:
        slug = str(record.get("slug", "")).strip() or "(no-slug)"
        operation = str(record.get("operation", "unknown"))
        provider = str(record.get("provider", "unknown"))
        by_slug[slug].append(record)
        by_operation[operation] += 1
        by_provider[provider] += 1

    for slug, records in by_slug.items():
        if slug == "(no-slug)":
            continue
        providers = [str(record.get("provider", "")) for record in records if record.get("success")]
        if len(set(providers)) > 1:
            fallback_slugs.append(slug)

    slug_stats = []
    for slug, records in sorted(by_slug.items(), key=lambda item: (-len(item[1]), item[0])):
        if slug == "(no-slug)":
            continue
        slug_stats.append(
            {
                "slug": slug,
                "calls": len(records),
                "cost_usd": round(
                    sum(float(record.get("estimated_cost_usd", 0) or 0) for record in records),
                    4,
                ),
                "providers": sorted({str(record.get("provider", "")) for record in records}),
            }
        )

    total_calls = len(llm_records)
    distinct_slugs = len([slug for slug in by_slug if slug != "(no-slug)"])
    avg_calls = round(total_calls / distinct_slugs, 1) if distinct_slugs else 0.0

    return {
        "days": days,
        "pipeline_runs": pipeline_runs,
        "total_llm_calls": total_calls,
        "distinct_slugs": distinct_slugs,
        "avg_calls_per_slug": avg_calls,
        "by_operation": dict(sorted(by_operation.items(), key=lambda item: (-item[1], item[0]))),
        "by_provider": dict(sorted(by_provider.items(), key=lambda item: (-item[1], item[0]))),
        "fallback_slugs": fallback_slugs[:10],
        "slug_stats": slug_stats[:10],
    }


def collect_url_section(*, check_live_urls: bool) -> dict:
    link_health = collect_link_health(POSTS_DIR)
    broken_ref_urls = 0
    broken_samples: list[str] = []

    if check_live_urls:
        errors = validate_posts(POSTS_DIR, site_root=SITE_ROOT, check_ref_urls=True)
        ref_errors = [error for error in errors if "reference URL" in error or "HTTP" in error]
        broken_ref_urls = len(ref_errors)
        broken_samples = ref_errors[:5]

    return {
        "broken_ref_urls": broken_ref_urls,
        "broken_samples": broken_samples,
        "link_health": link_health,
        "check_live_urls": check_live_urls,
    }


def collect_content_section() -> dict:
    return collect_content_warnings(POSTS_DIR)


def format_ops_section(data: dict) -> list[str]:
    lines = [
        "*1) Ops Digest*",
        f"- Period: last {data['days']} day(s)",
        (
            f"- Workflow runs: {data['workflows']['totals']['runs']} "
            f"(✅ {data['workflows']['totals']['success']} / "
            f"❌ {data['workflows']['totals']['failure']})"
        ),
        (
            f"- New ko posts: {len(data['new_posts'])} "
            f"(deep-dive {data['post_types'].get('deep-dive', 0)})"
        ),
        f"- Translation gaps: {data['translation_gaps']}",
        (
            f"- LLM: ${data['llm']['total_cost_usd']:.4f} "
            f"({data['llm']['total_calls']} calls, "
            f"monthly est. ${data['llm']['monthly_estimate_usd']:.2f})"
        ),
    ]
    failures = [
        (label, stats["failure"])
        for label, stats in data["workflows"]["workflows"].items()
        if stats["failure"] > 0
    ]
    if failures:
        lines.append("- Failed workflows: " + ", ".join(f"{label}({count})" for label, count in failures))
    return lines


def format_pipeline_section(data: dict) -> list[str]:
    ai = data["pipeline_runs"].get("AI Post", {})
    backfill = data["pipeline_runs"].get("Backfill", {})
    lines = [
        "*2) Content Pipeline*",
        (
            f"- AI Post runs: {ai.get('runs', 0)} "
            f"(✅ {ai.get('success', 0)} / ❌ {ai.get('failure', 0)})"
        ),
        (
            f"- Backfill runs: {backfill.get('runs', 0)} "
            f"(✅ {backfill.get('success', 0)} / ❌ {backfill.get('failure', 0)})"
        ),
        (
            f"- LLM calls: {data['total_llm_calls']} across "
            f"{data['distinct_slugs']} slug(s) (avg {data['avg_calls_per_slug']}/slug)"
        ),
    ]
    if data["by_provider"]:
        provider_bits = ", ".join(
            f"{name}({count})" for name, count in list(data["by_provider"].items())[:4]
        )
        lines.append(f"- Providers: {provider_bits}")
    if data["fallback_slugs"]:
        lines.append(
            "- Multi-provider slugs: " + ", ".join(data["fallback_slugs"][:5])
        )
    if data["slug_stats"]:
        top = data["slug_stats"][0]
        lines.append(
            f"- Top slug: `{top['slug']}` ({top['calls']} calls, ${top['cost_usd']:.4f})"
        )
    return lines


def format_url_section(data: dict) -> list[str]:
    health = data["link_health"]
    lines = [
        "*3) URL & Link Health*",
        f"- Orphan posts: {health['orphan_count']} / {health['total_posts']}",
    ]
    if health["top_hubs"]:
        hubs = ", ".join(
            f"{hub['slug']}({hub['inbound']})" for hub in health["top_hubs"][:3]
        )
        lines.append(f"- Top hubs: {hubs}")
    if data["check_live_urls"]:
        lines.append(f"- Broken reference URLs: {data['broken_ref_urls']}")
        for sample in data["broken_samples"][:3]:
            lines.append(f"  • {sample}")
    else:
        lines.append("- Broken reference URLs: (skipped live check)")
    return lines


def format_content_section(data: dict) -> list[str]:
    lines = [
        "*4) Content Strategy*",
        f"- Total warnings: {data['total_warnings']}",
        f"- Similar titles: {len(data['similarity'])}",
        f"- Informal style: {len(data['informal_style'])}",
        f"- Overused slug tokens: {len(data['overused_tokens'])}",
    ]
    for key, label in (
        ("similarity", "Similar"),
        ("informal_style", "Style"),
        ("overused_tokens", "Token"),
    ):
        items = data[key][:2]
        for item in items:
            lines.append(f"  • [{label}] {item}")
    return lines


def build_digest(
    days: int,
    *,
    check_live_urls: bool = True,
) -> dict:
    llm_records = fetch_from_actions(days)
    return {
        "ops": collect_ops_section(days, llm_records),
        "pipeline": collect_pipeline_section(days, llm_records),
        "url": collect_url_section(check_live_urls=check_live_urls),
        "content": collect_content_section(),
    }


def format_digest(digest: dict) -> str:
    lines = ["*blog.jiwon.io — Weekly Ops Report*", ""]
    lines.extend(format_ops_section(digest["ops"]))
    lines.append("")
    lines.extend(format_pipeline_section(digest["pipeline"]))
    lines.append("")
    lines.extend(format_url_section(digest["url"]))
    lines.append("")
    lines.extend(format_content_section(digest["content"]))
    return "\n".join(lines)


def format_digest_markdown(digest: dict) -> str:
    text = format_digest(digest)
    return text.replace("*", "**")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate weekly operational digest")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--slack", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--skip-live-urls",
        action="store_true",
        help="Skip network reference URL checks in section 3",
    )
    args = parser.parse_args(argv)

    digest = build_digest(
        args.days,
        check_live_urls=not args.skip_live_urls,
    )
    text = format_digest_markdown(digest) if args.markdown else format_digest(digest)
    print(text)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")

    if args.slack:
        post_slack(format_digest(digest))

    monthly = digest["ops"]["llm"].get("monthly_estimate_usd", 0)
    if monthly > LLM_MONTHLY_BUDGET_USD:
        print(
            f"::warning::Monthly LLM estimate ${monthly:.2f} exceeds "
            f"budget ${LLM_MONTHLY_BUDGET_USD:.2f}",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())