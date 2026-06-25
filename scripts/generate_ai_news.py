"""개발자 관점 AI 소식 다이제스트 자동 생성."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import feedparser

from blog_i18n import FRONT_MATTER_PATTERN
from feeds_config import (
    AI_FILTER_FEEDS,
    ALL_FEEDS,
    DEVELOPER_KEYWORDS,
    HN_ALGOLIA_URL,
    LOW_PRIORITY_KEYWORDS,
    MAX_ITEMS_PER_FEED,
    MAX_TOTAL_CANDIDATES,
    RSS_DAYS_LOOKBACK_BY_TIER,
    RSS_FETCH_TIMEOUT,
    RSS_FETCH_USER_AGENT,
    TIER_WEIGHTS,
)
from post_common import (
    body_after_more,
    collect_past_reference_urls,
    extract_reference_urls,
    format_internal_links_for_prompt,
    get_internal_link_candidates,
    get_kst_now,
    normalize_slug,
    normalize_url,
    publish_post,
    repair_ai_news_structure,
    tokenize,
    validate_base_content,
    validate_tag_consistency,
    find_invalid_internal_post_slugs,
    get_existing_ko_slugs,
    generate_with_retry,
    INTERNAL_LINK_PATTERN,
)

MIN_BODY_CHARS = 1500
MIN_NEWS_SECTIONS = 5
MAX_NEWS_SECTIONS = 7
MIN_SECTION_CHARS = 150
MIN_INTERNAL_LINKS = 2
MIN_REFERENCE_URLS = 5
DEVELOPER_PERSPECTIVE_LABEL = "**개발자 관점:**"
SUMMARY_SECTIONS = ("이번 주 한 줄 정리",)
BANNED_INTRO_PHRASES = (
    "시니어 풀스택 개발자이자 기술 블로거",
    "안녕하세요, 시니어",
)
BANNED_CLI_NOTATIONS = ("gh?", "git?")
YO_ENDING_PATTERN = re.compile(
    r"(?:해요|했어요|이에요|예요|거예요|할게요|볼게요|보여요|같아요|있어요|없어요|되죠|있죠|하세요|줄게요|테니|테고요|었고요|였어요|일까요)"
)
FORMAL_ENDING_PATTERN = re.compile(r"(?:습니다|입니다|합니다|됩니다|습니까|입니까)")
PLAIN_DA_SUFFIX = re.compile(
    r"(?:했다|였다|겠다|된다|한다|같다|보인다|느꼈다|해졌다|생겼다|짚었다|내놨다|터졌다|밝혔다|"
    r"발표했다|공개했다|쏟아졌다|열었다|이었다|있었다|없었다|올렸다|줬다|왔다|갔다|봤다|썼다|"
    r"남았다|받았다|진화했다|가능해졌다|되었다)(?:\.|$)"
)
SKIP_TONE_LINES = frozenset({"<!--more-->", "[HERO_IMAGE]", "-----"})


def find_plain_da_tone_violations(prose: str) -> list[str]:
    """'~다' 체 문장/불릿을 찾아 정중체 위반 목록을 반환합니다."""
    violations: list[str] = []
    body = prose.split("### 참고문헌", 1)[0]
    for line in body.splitlines():
        stripped = line.strip().rstrip("-").strip()
        if not stripped or stripped.startswith("#") or stripped in SKIP_TONE_LINES:
            continue
        if FORMAL_ENDING_PATTERN.search(stripped):
            continue
        match = PLAIN_DA_SUFFIX.search(stripped)
        if match:
            violations.append(match.group(0).rstrip("."))
    return violations


def normalize_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title.strip().casefold())
    title = re.sub(r"[^\w가-힣\s]", "", title)
    return title


def title_similarity(a: str, b: str) -> float:
    ta, tb = set(tokenize(a)), set(tokenize(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def keyword_score(text: str) -> int:
    lowered = text.casefold()
    score = sum(1 for kw in DEVELOPER_KEYWORDS if kw in lowered)
    score -= sum(2 for kw in LOW_PRIORITY_KEYWORDS if kw in lowered)
    return score


def filter_ai_relevant_entries(entries: list, feed_name: str) -> list:
    if feed_name not in AI_FILTER_FEEDS:
        return entries
    ai_terms = (
        "ai", "copilot", "agent", "llm", "model", "machine learning", "gpt", "claude",
        "gemini", "inference", "gpu", "cuda", "transformer", "embedding", "rag",
        "openai", "anthropic", "hugging face", "fine-tun", "neural",
    )
    filtered = []
    for entry in entries:
        blob = f"{entry.get('title', '')} {entry.get('summary', '')}".casefold()
        if any(term in blob for term in ai_terms):
            filtered.append(entry)
    return filtered


def parse_entry_date(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
    return None


def fetch_rss_items() -> list[dict]:
    items: list[dict] = []

    for feed_cfg in ALL_FEEDS:
        name = feed_cfg["name"]
        tier = feed_cfg["tier"]
        lookback = RSS_DAYS_LOOKBACK_BY_TIER.get(tier, 7)
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback)
        try:
            request = Request(
                feed_cfg["url"],
                headers={"User-Agent": RSS_FETCH_USER_AGENT},
            )
            with urlopen(request, timeout=RSS_FETCH_TIMEOUT) as response:
                parsed = feedparser.parse(response.read())
            entries = filter_ai_relevant_entries(parsed.entries[: MAX_ITEMS_PER_FEED * 2], name)
            count = 0
            for entry in entries:
                if count >= MAX_ITEMS_PER_FEED:
                    break
                published = parse_entry_date(entry)
                if published and published < cutoff:
                    continue
                link = entry.get("link", "").strip()
                title = entry.get("title", "").strip()
                if not link or not title:
                    continue
                summary = re.sub(r"<[^>]+>", "", entry.get("summary", ""))[:400]
                items.append(
                    {
                        "title": title,
                        "url": link,
                        "summary": summary,
                        "source": name,
                        "tier": tier,
                        "published": published.isoformat() if published else "",
                    }
                )
                count += 1
            print(f"  📡 {name}: {count}건")
        except Exception as exc:
            print(f"  ⚠️ {name} 피드 실패: {exc}")

    return items


def fetch_hn_items() -> list[dict]:
    items: list[dict] = []
    try:
        request = Request(HN_ALGOLIA_URL, headers={"User-Agent": RSS_FETCH_USER_AGENT})
        with urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        for hit in data.get("hits", [])[:5]:
            title = hit.get("title", "").strip()
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
            if not title:
                continue
            items.append(
                {
                    "title": title,
                    "url": url,
                    "summary": f"HN points: {hit.get('points', 0)}, comments: {hit.get('num_comments', 0)}",
                    "source": "Hacker News",
                    "tier": 2,
                    "published": "",
                }
            )
        print(f"  📡 Hacker News: {len(items)}건")
    except Exception as exc:
        print(f"  ⚠️ Hacker News API 실패: {exc}")
    return items


def deduplicate_items(items: list[dict]) -> list[dict]:
    """URL·제목 유사도 기반 중복 제거. Tier가 높은 항목 우선."""
    ranked = sorted(
        items,
        key=lambda item: (
            -TIER_WEIGHTS.get(item["tier"], 1),
            -keyword_score(f"{item['title']} {item.get('summary', '')}"),
        ),
    )
    kept: list[dict] = []
    seen_urls: set[str] = set()
    seen_titles: list[str] = []

    for item in ranked:
        norm_url = normalize_url(item["url"])
        if norm_url in seen_urls:
            continue
        norm_title = normalize_title(item["title"])
        if any(title_similarity(norm_title, prev) >= 0.7 for prev in seen_titles):
            continue
        seen_urls.add(norm_url)
        seen_titles.append(norm_title)
        kept.append(item)

    return kept[:MAX_TOTAL_CANDIDATES]


def score_and_rank_items(items: list[dict]) -> list[dict]:
    return sorted(
        items,
        key=lambda item: (
            -TIER_WEIGHTS.get(item["tier"], 1) * 10
            - keyword_score(f"{item['title']} {item.get('summary', '')}"),
            item["title"],
        ),
    )


def count_news_sections(content: str) -> list[str]:
    body = body_after_more(content)
    sections = []
    for line in body.splitlines():
        if line.startswith("## ") and not line.startswith("### "):
            heading = line[3:].strip()
            if heading not in SUMMARY_SECTIONS:
                sections.append(heading)
    return sections


def section_char_counts(content: str) -> dict[str, int]:
    body = body_after_more(content)
    chunks = re.split(r"\n## ", body)
    counts: dict[str, int] = {}
    for chunk in chunks[1:]:
        lines = chunk.splitlines()
        heading = lines[0].strip()
        if heading in SUMMARY_SECTIONS:
            continue
        text = "\n".join(lines[1:])
        counts[heading] = len(re.sub(r"\s+", "", text))
    return counts


def count_internal_links(content: str) -> int:
    return len(INTERNAL_LINK_PATTERN.findall(content))


def resolve_edition_datetime(date_override: str | None = None) -> datetime:
    if date_override:
        parsed = datetime.strptime(date_override.strip(), "%Y-%m-%d")
        return parsed.replace(tzinfo=get_kst_now().tzinfo)
    return get_kst_now()


def validate_ai_news_content(
    content: str,
    past_urls: set[str],
    *,
    edition_date: datetime | None = None,
) -> tuple[dict, str]:
    metadata = validate_base_content(content)
    validate_tag_consistency(metadata)

    today = edition_date or get_kst_now()
    expected_slug = f"ai-news-{today.strftime('%Y-%m-%d')}"
    slug = normalize_slug(str(metadata["slug"]))

    if slug != expected_slug:
        raise ValueError(f"slug는 {expected_slug} 이어야 합니다. (생성됨: {slug})")
    if slug in get_existing_ko_slugs():
        raise ValueError(f"이미 존재하는 slug입니다: {slug}")

    tags = [str(tag) for tag in metadata["tags"]]
    if "AI-News" not in tags:
        raise ValueError("tags에 AI-News가 필수입니다.")

    body = body_after_more(content)
    body_chars = len(re.sub(r"\s+", "", body))
    if body_chars < MIN_BODY_CHARS:
        raise ValueError(f"본문(<!--more--> 이후)이 {MIN_BODY_CHARS}자 미만입니다: {body_chars}자")

    sections = count_news_sections(content)
    if not (MIN_NEWS_SECTIONS <= len(sections) <= MAX_NEWS_SECTIONS):
        raise ValueError(
            f"소식 H2 섹션이 {MIN_NEWS_SECTIONS}~{MAX_NEWS_SECTIONS}개여야 합니다: {len(sections)}개"
        )

    for heading, chars in section_char_counts(content).items():
        if chars < MIN_SECTION_CHARS:
            raise ValueError(f"'{heading}' 섹션이 {MIN_SECTION_CHARS}자 미만입니다: {chars}자")

    if content.count(DEVELOPER_PERSPECTIVE_LABEL) < len(sections):
        raise ValueError(f"각 소식에 {DEVELOPER_PERSPECTIVE_LABEL} 라벨이 필요합니다.")

    internal_links = count_internal_links(content)
    if internal_links < MIN_INTERNAL_LINKS:
        raise ValueError(f"내부 링크(/posts/)가 {MIN_INTERNAL_LINKS}개 이상 필요합니다: {internal_links}개")

    invalid_slugs = find_invalid_internal_post_slugs(content, get_existing_ko_slugs())
    if invalid_slugs:
        raise ValueError(
            "존재하지 않는 내부 링크 slug: "
            + ", ".join(invalid_slugs[:5])
            + " (slug를 잘라 쓰지 말고 후보 URL을 그대로 복사하세요)"
        )

    ref_urls = extract_reference_urls(content)
    if len(ref_urls) < MIN_REFERENCE_URLS:
        raise ValueError(f"참고문헌 URL이 {MIN_REFERENCE_URLS}개 이상 필요합니다: {len(ref_urls)}개")

    overlap = set(ref_urls) & past_urls
    if overlap:
        raise ValueError(f"이미 다룬 참고문헌 URL이 포함되어 있습니다: {list(overlap)[:3]}")

    excerpt = content.split("<!--more-->", 1)[0]
    for phrase in BANNED_INTRO_PHRASES:
        if phrase in excerpt:
            raise ValueError(f"도입부에 금지된 자기소개 표현이 있습니다: {phrase}")

    for notation in BANNED_CLI_NOTATIONS:
        if notation in content:
            raise ValueError(
                f"검증되지 않은 CLI 표기({notation})가 있습니다. "
                "슬래시 명령어는 /explain 형식이거나 한글로 설명하세요."
            )

    fm_match = FRONT_MATTER_PATTERN.match(content)
    prose = content[fm_match.end() :] if fm_match else content
    prose_body = prose.split("### 참고문헌", 1)[0]
    yo_matches = YO_ENDING_PATTERN.findall(prose_body)
    if yo_matches:
        raise ValueError(
            "본문에 '~요' 어미가 포함되어 있습니다. '~습니다·입니다' 체로 통일하세요: "
            + ", ".join(sorted(set(yo_matches))[:5])
        )

    da_violations = find_plain_da_tone_violations(prose)
    if da_violations:
        raise ValueError(
            "본문에 '~다' 체 표현이 포함되어 있습니다. 일반 기술 글과 같이 "
            "'~습니다·입니다' 체로 통일하세요: "
            + ", ".join(sorted(set(da_violations))[:5])
        )

    formal_count = len(FORMAL_ENDING_PATTERN.findall(prose_body))
    if formal_count < 12:
        raise ValueError(
            f"정중한 '~습니다·입니다' 문체가 부족합니다 (감지 {formal_count}회). "
            "심층 기술 글과 같은 자연스러운 존댓말로 작성하세요."
        )

    return metadata, slug


def build_generation_prompt(
    rss_items: list[dict],
    internal_links: str,
    past_urls: set[str],
    current_time: str,
    today_slug: str,
) -> str:
    items_json = json.dumps(rss_items, ensure_ascii=False, indent=2)
    past_urls_str = "\n".join(f"- {url}" for url in sorted(past_urls)[:30]) or "- 없음"

    return f"""
아래 RSS 수집 결과를 바탕으로 **개발자 관점 AI 소식 다이제스트**를 작성하세요.
이 블로그 주인이 직접 쓰는 1인칭 기술 글입니다.

**[글쓰기 톤]**
- 심층 기술 글과 같은 **'~습니다·입니다' 체**로 자연스럽게 작성 (~합니다, ~입니다, ~됩니다, ~었습니다)
- 1인칭 시점의 기술 블로그 글. 딱딱한 번역체나 뉴스 원고 톤은 피하고, 동료에게 설명하듯 읽기 쉽게
- "~다" 체(~했다, ~이다, ~된다, ~겠다)와 "~요", "~해요" 어미 금지
- "시니어 풀스택 개발자이자 기술 블로거입니다" 같은 자기소개·직함 나열 금지
- 도입부 2~3문단: 이번 주 소식 중 무엇이 왜 중요한지 개인적인 관점으로 시작
- 톤 예시 (나쁨 → 좋음):
  - 나쁨: "이번 주는 에이전트 인프라가 한 단계 구체화된 한 주였다."
  - 좋음: "이번 주는 에이전트 인프라가 한 단계 더 구체화된 한 주였습니다."
  - 나쁨: "Copilot 측에서 내부적으로 필터링해 준다는 건 체감 품질 향상으로 이어질 수 있다."
  - 좋음: "Copilot이 컨텍스트를 내부적으로 걸러 주면, 체감 품질이 눈에 띄게 좋아질 수 있습니다."

**[금지]**
- 헤드라인만 나열하는 뉴스 큐레이션
- "요약:" 한 줄로 끝나는 항목 (각 항목 최소 150자 이상)
- 이미 다룬 URL 재사용 (아래 목록)
- 일반 뉴스 사이트 톤, 투자·정책 중심 나열
- RSS 원문에 없는 CLI 표기 임의 생성 (예: gh?, git?) — 슬래시 명령어는 /explain, /fix 형식이거나 한글로 설명

**[필수]**
- 5~7개 소식 (H2 섹션, "이번 주 한 줄 정리" 제외)
- 각 소식마다 아래 형식:
  ## N. {{소식 제목}}
  **요약:** 1~2문장
  {DEVELOPER_PERSPECTIVE_LABEL} 2~3문장 (코딩 도구, API, 비용, 보안, 배포 영향)
  **관련 글:** [제목](/posts/slug/){{:target="_blank"}} (해당 시)
- 내부 링크 후보에서 관련 글 **2개 이상** 본문에 연결
- `/posts/` slug는 후보 URL을 **한 글자도 바꾸지 말고** 그대로 복사 (줄임·축약 금지)
- 본문(<!--more--> 이후) 1,500자 이상
- 마지막에 ## 이번 주 한 줄 정리 (bullet 3~4개)
- slug: {today_slug} (고정)
- tags에 AI-News, Developer-Digest, News-Digest 포함

**[이미 다룬 URL — 절대 재사용 금지]**
{past_urls_str}

**[RSS 수집 결과 — tier 낮을수록 보조]**
{items_json}

**[내부 링크 후보 — 관련 있으면 2개 이상 삽입]**
{internal_links}

아래는 출력 순서 지침입니다. 지침 문구를 결과물에 출력하지 마세요.

---
layout: post
title: "이번 주 AI 소식: {{핵심 키워드 2~3개}}"
slug: {today_slug}
lang: ko
translation_key: {today_slug}
post_type: ai-news
date: {current_time}
categories: [AI]
tags: [AI-News, Developer-Digest, News-Digest, ...]
description: "150자 내외 SEO 요약"
image: "/uploads/{today_slug}/thumbnail.webp"
---
(도입부 2~3문단)

<!--more-->

[HERO_IMAGE]
-----
(본문 H2 섹션들 — [HERO_IMAGE]와 -----는 반드시 위와 같이 각각 단독 한 줄)
### 참고문헌
- [원문 제목](URL){{:target="_blank"}}
"""


def generate_ai_news_post(
    *,
    text_provider: str | None = None,
    translation_provider: str | None = None,
    date_override: str | None = None,
) -> str:
    today = resolve_edition_datetime(date_override)
    today_slug = f"ai-news-{today.strftime('%Y-%m-%d')}"
    current_time = today.strftime("%Y-%m-%d %H:%M:%S +0900")
    if date_override:
        print(f"📅 edition date override: {date_override}")

    print("📡 RSS 피드 수집 중...")
    raw_items = fetch_rss_items() + fetch_hn_items()
    deduped = deduplicate_items(raw_items)
    ranked = score_and_rank_items(deduped)
    print(f"✅ 후보 {len(ranked)}건 (중복 제거 후)")

    if len(ranked) < MIN_REFERENCE_URLS:
        raise RuntimeError(f"RSS 후보가 부족합니다: {len(ranked)}건 (최소 {MIN_REFERENCE_URLS}건 필요)")

    past_urls = collect_past_reference_urls()
    rss_titles = [item["title"] for item in ranked]
    internal_candidates = get_internal_link_candidates(rss_titles)
    internal_links = format_internal_links_for_prompt(internal_candidates)

    prompt = build_generation_prompt(
        ranked,
        internal_links,
        past_urls,
        current_time,
        today_slug,
    )

    def validate(content: str) -> tuple[dict, str]:
        repaired = repair_ai_news_structure(content, internal_candidates)
        if repaired != content:
            print("🔧 LLM 출력 자동 보정 적용 (HERO_IMAGE 블록·내부 링크)")
            content = repaired
        try:
            return validate_ai_news_content(content, past_urls, edition_date=today)
        except ValueError as exc:
            preview = content[:300].replace("\n", " ")
            raise ValueError(f"{exc} | 응답 미리보기: {preview}") from exc

    content, metadata, slug = generate_with_retry(
        prompt,
        validate,
        post_type="ai-news",
        text_provider=text_provider,
    )

    image_prompt = (
        "Weekly AI developer news digest thumbnail. Calendar, code editor, "
        "headlines collage, dark tech blog style, clean vector art."
    )

    return publish_post(
        content,
        metadata,
        slug,
        image_prompt=image_prompt,
        post_type="ai-news",
        today=today,
        require_translations=True,
        translation_provider=translation_provider,
    )


def dry_run(*, strict: bool = False) -> int:
    """API 호출 없이 RSS 수집·후보·내부 링크만 확인합니다."""
    today = get_kst_now()
    today_slug = f"ai-news-{today.strftime('%Y-%m-%d')}"
    issues: list[str] = []

    print("🔍 AI News dry-run (API 호출 없음)")
    print(f"  예상 slug: {today_slug}")

    if today_slug in get_existing_ko_slugs():
        print(f"  ⚠️ 오늘 slug가 이미 존재합니다: {today_slug} (게시 완료 상태, strict 실패 조건 아님)")
    else:
        print("  ✅ slug 사용 가능")

    print("\n📡 RSS 피드 수집 중...")
    raw_items = fetch_rss_items() + fetch_hn_items()
    deduped = deduplicate_items(raw_items)
    ranked = score_and_rank_items(deduped)
    print(f"\n✅ 후보 {len(ranked)}건 (원본 {len(raw_items)}건 → 중복 제거 {len(deduped)}건)")

    if len(ranked) < MIN_REFERENCE_URLS:
        print(f"  ❌ 후보 부족: {len(ranked)}건 (최소 {MIN_REFERENCE_URLS}건 필요)")
        issues.append(f"insufficient RSS candidates: {len(ranked)}")
    else:
        print(f"  ✅ 후보 충분 (최소 {MIN_REFERENCE_URLS}건)")

    print("\n📰 상위 후보:")
    for index, item in enumerate(ranked[:10], start=1):
        print(f"  {index}. [tier {item['tier']}] {item['source']}: {item['title'][:80]}")

    past_urls = collect_past_reference_urls()
    print(f"\n🔗 과거 ai-news 참고 URL: {len(past_urls)}건")

    internal_candidates = get_internal_link_candidates([item["title"] for item in ranked])
    print(f"\n🏠 내부 링크 후보: {len(internal_candidates)}건")
    print(format_internal_links_for_prompt(internal_candidates))

    if len(internal_candidates) < MIN_INTERNAL_LINKS:
        print(f"  ⚠️ 내부 링크 후보가 {MIN_INTERNAL_LINKS}건 미만입니다.")
        issues.append(f"insufficient internal links: {len(internal_candidates)}")
    else:
        print(f"  ✅ 내부 링크 후보 충분 (최소 {MIN_INTERNAL_LINKS}건)")

    if strict and issues:
        print("\n❌ dry-run strict 모드 실패:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="개발자 관점 AI 소식 다이제스트 생성")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="RSS 수집·후보·내부 링크만 확인하고 API 호출 없이 종료",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="dry-run 시 RSS 후보·내부 링크 부족하면 exit code 1 반환 (slug 중복은 제외)",
    )
    parser.add_argument(
        "--text-provider",
        choices=["gemini", "anthropic", "openai", "xai"],
        help="글 생성에 사용할 LLM provider (기본: ai-news 라우팅)",
    )
    parser.add_argument(
        "--translation-provider",
        choices=["gemini", "anthropic", "openai", "xai"],
        help="번역에 사용할 LLM provider (기본: 번역 폴백 체인)",
    )
    parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="slug/날짜 고정 (누락 호수 복구용, 예: 2026-06-25)",
    )
    args = parser.parse_args()

    if args.dry_run:
        raise SystemExit(dry_run(strict=args.strict))
    generate_ai_news_post(
        text_provider=args.text_provider,
        translation_provider=args.translation_provider,
        date_override=args.date,
    )