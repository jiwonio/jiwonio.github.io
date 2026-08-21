"""운영자가 정한 주제로 심층 기술 글 초안을 생성합니다."""

from __future__ import annotations

import argparse
import os

from llm_client import list_available_providers
from post_common import (
    body_after_more,
    drop_broken_reference_urls,
    extract_reference_urls,
    find_broken_reference_urls,
    generate_with_retry,
    get_existing_ko_slugs,
    get_recent_titles,
    inject_front_matter_field,
    normalize_slug,
    publish_post,
    resolve_edition_datetime,
    validate_base_content,
    validate_tag_consistency,
)
from prompt_config import DEEP_DIVE_SYSTEM_PROMPT

MIN_REFERENCE_URLS = 2

BANNED_TITLE_PHRASES = (
    "완벽 가이드", "완벽한", "프로덕션급", "Ultimate Guide", "ultimate guide",
    "완전 정복", "마스터하기",
)

POST_ANGLES = {
    "before-after": "Before/After: 도입 전·후 워크플로 비교",
    "failure": "실패 사례: 잘못 쓰면 생기는 문제 + 재현 가능한 증상",
    "decision": "의사결정: A vs B 선택 기준표",
    "hidden-cost": "숨은 비용: API·토큰·CI·인지 부하 등 간과되는 비용",
    "team": "팀 도입: 1인 → 3인 → 10인 팀에서 바뀌는 설정·규칙",
    "freeform": "운영자 메모의 각도를 그대로 따른다",
}


def validate_deep_dive_content(content: str) -> tuple[dict, str]:
    metadata = validate_base_content(content)
    validate_tag_consistency(metadata)

    slug = normalize_slug(str(metadata["slug"]))
    if slug in get_existing_ko_slugs():
        raise ValueError(f"이미 존재하는 slug입니다: {slug}")

    title_lower = str(metadata["title"]).casefold()
    for phrase in BANNED_TITLE_PHRASES:
        if phrase.casefold() in title_lower:
            raise ValueError(f"제목에 금지된 포괄 표현이 있습니다: {phrase}")

    if not has_application_table(content):
        raise ValueError(
            "결론에 적용 조건 표가 필요합니다. | 상황 | 추천 | 이유 | 형식의 마크다운 표를 포함하세요."
        )

    ref_urls = extract_reference_urls(content)
    if len(ref_urls) < MIN_REFERENCE_URLS:
        raise ValueError(
            f"참고문헌 URL이 {MIN_REFERENCE_URLS}개 이상 필요합니다: {len(ref_urls)}개"
        )

    broken_refs = find_broken_reference_urls(content)
    if broken_refs:
        raise ValueError(
            "참고문헌 URL이 유효하지 않습니다 (404/410): "
            + ", ".join(broken_refs[:3])
        )

    return metadata, slug


def resolve_generation_inputs(
    topic: str | None = None,
    angle: str | None = None,
    notes: str | None = None,
    environ: dict[str, str] | None = None,
) -> tuple[str, str, str]:
    """CLI 값이 비면 POST_TOPIC / POST_ANGLE / POST_NOTES 환경 변수를 씁니다."""
    env = os.environ if environ is None else environ
    resolved_topic = (topic or "").strip() or str(env.get("POST_TOPIC", "")).strip()
    resolved_angle = (angle or "").strip() or str(env.get("POST_ANGLE", "")).strip() or "freeform"
    resolved_notes = str(env.get("POST_NOTES", "")) if notes is None else notes
    return resolved_topic, resolved_angle, resolved_notes


def has_application_table(content: str) -> bool:
    body = body_after_more(content).split("### 참고문헌", 1)[0]
    if "|" not in body:
        return False
    return ("상황" in body and "추천" in body and "이유" in body)


def build_generation_prompt(
    *,
    topic: str,
    angle: str,
    notes: str,
    recent_titles: list[str],
    current_time: str,
) -> str:
    angle_label = POST_ANGLES.get(angle, POST_ANGLES["freeform"])
    recent_titles_str = (
        "\n    ".join(f"- {title}" for title in recent_titles)
        if recent_titles else "- 아직 작성된 글이 없습니다."
    )
    notes_block = notes.strip() if notes.strip() else (
        "없음. 수치·실패 사례·명령 출력을 지어내지 마세요. "
        "모르면 '측정 필요'라고 쓰세요."
    )

    return f"""
운영자가 정한 주제로 실무 기술 포스트 초안을 작성하세요.
주제를 바꾸거나 다른 도구로 바꾸지 마세요.

**[운영자가 정한 주제]**
{topic}

**[글 각도]**
{angle_label}

**[운영자 메모 — 실측·경험. 창작 금지]**
{notes_block}

**[제목]**
- 운영자 주제를 제목에 반영하세요. 포괄 표현 금지: "완벽 가이드", "프로덕션급", "완전 정복"
- 클릭베이트·마케팅 문구 금지

**[도입부 필수]**
- 첫 2문단: 운영자 메모에 있는 구체적 상황. 메모가 없으면 일반적인 상황을 짧게 잡고 수치를 넣지 마세요.
- 세 번째 문단: 이 글을 읽으면 해결되는 한 가지를 명시

**[최근 제목 — 같은 글을 다시 쓰지 말 것]**
{recent_titles_str}

**[글쓰기 스타일]**
- 블로그 주인이 직접 쓰는 1인칭 기술 글 (자기소개·직함 나열로 시작하지 않기)
- 문장 끝은 '~습니다·입니다' 체로 자연스럽게 통일. '~요', '~해요', '~다' 체 금지
- 짧고 명확한 문장. 불필요한 형용사·부사·마케팅 문구 최소화
- 구조: 문제 → 원리 → 코드/설정 → 주의점 → 결론
- 코드: 의미 있는 이름, 짧은 단위, 필요한 주석만(왜 하는지)
- Secret은 플레이스홀더만 (`<YOUR_API_KEY>`)
- 없는 벤치마크·시간·비용을 만들지 마세요.

**[결론 필수]**
| 상황 | 추천 | 이유 |
형식의 마크다운 표를 포함하세요. 최소 3행(1인 사이드, 스타트업 5인, 레거시 많음 등).

아래는 출력 순서를 안내하는 지침입니다. 번호와 설명("Front Matter", "도입부" 등)은
지침일 뿐이며 결과물에 그대로 옮겨 쓰면 안 됩니다. 마크다운 글 본문 외 다른 설명은 출력하지 마세요.

[출력 순서]
1) 아래 형식의 YAML Front Matter를 값만 채워서 그대로 작성합니다.
   categories는 `AI` 또는 `DevOps` 하나만. 코딩 도구·LLM이면 AI, 인프라면 DevOps. 한글 설명 금지.
---
layout: post
title: "구체적인 한글 제목"
slug: "english-slug-for-this-topic"
lang: ko
translation_key: "english-slug-for-this-topic"
post_type: deep-dive
date: {current_time}
categories:
- AI
tags: [태그1, 태그2, 태그3]
description: "150자 내외 SEO 요약"
image: "/uploads/english-slug-for-this-topic/thumbnail.webp"
---
2) 도입부 2~3문단을 작성한 뒤, 줄을 바꿔 `<!--more-->` 한 줄만 단독으로 작성합니다.
3) 바로 다음 줄에 `[HERO_IMAGE]` 한 줄만 단독으로 작성하고, 그다음 줄에 `-----` 한 줄만 단독으로 작성합니다.
4) 본문을 작성합니다. '~습니다' 체, H2/H3 계층, 외부 이미지 URL 금지.
   링크: `[텍스트](URL "툴팁"){{:target="_blank"}}`
5) 마지막에 `### 참고문헌` 섹션을 작성하고 출처 링크를 **최소 2개** 나열합니다.
   - URL은 실제로 열리는 공식 문서·GitHub 저장소/릴리즈/이슈·벤더 블로그만 사용하세요.
   - 존재하지 않는 도메인·경로·조직을 지어내지 마세요. (404 링크는 자동 거부됩니다)
   - 불확실하면 잘 알려진 상위 문서(제품 홈, docs 루트, 공식 blog)만 넣으세요.

주의: 1)~5)는 작성 순서 설명일 뿐 실제 헤더가 아닙니다. "Front Matter", "도입부", "본문" 같은
지침 단어나 1) 2) 3) 같은 번호를 결과물에 절대 출력하지 마세요.
"""


def generate_blog_post(
    *,
    topic: str,
    angle: str = "freeform",
    notes: str = "",
    text_provider: str | None = None,
    translation_provider: str | None = None,
    date_override: str | None = None,
) -> str:
    topic = topic.strip()
    if not topic:
        raise ValueError("주제가 비어 있습니다. 운영자가 주제를 정한 뒤에 생성하세요.")
    if angle not in POST_ANGLES:
        raise ValueError(f"알 수 없는 각도입니다: {angle}")

    today = resolve_edition_datetime(date_override)
    current_time = today.strftime("%Y-%m-%d %H:%M:%S +0900")
    if date_override:
        print(f"📅 날짜 고정: {today.strftime('%Y-%m-%d')}")
    print(f"📌 주제: {topic}")
    print(f"📐 각도: {POST_ANGLES[angle]}")

    recent_titles = get_recent_titles(50)
    prompt = build_generation_prompt(
        topic=topic,
        angle=angle,
        notes=notes,
        recent_titles=recent_titles,
        current_time=current_time,
    )

    def validate(content: str) -> tuple[dict, str, str]:
        content, dropped_refs = drop_broken_reference_urls(content)
        if dropped_refs:
            print(
                "🔧 유효하지 않은 참고문헌 URL 제거: "
                + ", ".join(dropped_refs[:3])
            )
        try:
            metadata, slug = validate_deep_dive_content(content)
        except ValueError as exc:
            preview = content[:300].replace("\n", " ")
            raise ValueError(f"{exc} | 응답 미리보기: {preview}") from exc
        return metadata, slug, content

    content, metadata, slug = generate_with_retry(
        prompt,
        validate,
        post_type="deep-dive",
        text_provider=text_provider,
        system_prompt=DEEP_DIVE_SYSTEM_PROMPT,
    )
    content = inject_front_matter_field(content, "date", current_time)
    metadata["date"] = current_time

    image_prompt = (
        f"Modern tech blog thumbnail about: '{topic}'. "
        "Clean vector art, dark background, no readable text."
    )

    return publish_post(
        content,
        metadata,
        slug,
        image_prompt=image_prompt,
        post_type="deep-dive",
        today=today,
        require_translations=True,
        translation_provider=translation_provider,
    )


def dry_run(*, topic: str = "", angle: str = "freeform") -> int:
    """API 호출 없이 생성 전제 조건만 확인합니다."""
    issues: list[str] = []

    print("🔍 Draft dry-run (API 호출 없음)")

    available = list_available_providers()
    print(f"  사용 가능 provider: {', '.join(available) or '없음'}")
    if not available:
        issues.append("No LLM API keys configured (GEMINI/ANTHROPIC/OPENAI/XAI)")

    print(f"  기존 ko slug 수: {len(get_existing_ko_slugs())}")
    if topic.strip():
        print(f"  주제: {topic.strip()}")
        print(f"  각도: {POST_ANGLES.get(angle, POST_ANGLES['freeform'])}")
    else:
        print("  주제: (미입력 — 실제 생성 시 --topic 필수)")

    if issues:
        print("\n❌ dry-run 실패:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("  ✅ 사전 조건 통과")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="운영자가 정한 주제로 심층 기술 글 초안을 생성합니다."
    )
    parser.add_argument(
        "--topic",
        default=None,
        help="운영자가 정한 주제 (또는 환경 변수 POST_TOPIC)",
    )
    parser.add_argument(
        "--angle",
        choices=sorted(POST_ANGLES),
        default=None,
        help="글 각도 (또는 POST_ANGLE, 기본: freeform)",
    )
    parser.add_argument(
        "--notes",
        default=None,
        help="실측·실패·경험 메모 (또는 POST_NOTES)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="API 호출 없이 사전 조건만 확인하고 종료",
    )
    parser.add_argument(
        "--text-provider",
        choices=["gemini", "anthropic", "openai", "xai"],
        help="글 생성에 사용할 LLM provider (기본: deep-dive 라우팅)",
    )
    parser.add_argument(
        "--translation-provider",
        choices=["gemini", "anthropic", "openai", "xai"],
        help="번역에 사용할 LLM provider (기본: 번역 폴백 체인)",
    )
    parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="파일명/front matter 날짜 고정 (예: 2026-07-06)",
    )
    args = parser.parse_args()
    topic, angle, notes = resolve_generation_inputs(
        topic=args.topic,
        angle=args.angle,
        notes=args.notes,
    )

    if args.dry_run:
        raise SystemExit(dry_run(topic=topic, angle=angle))
    if not topic:
        parser.error("주제가 필요합니다. --topic 또는 POST_TOPIC 으로 운영자가 정한 주제를 넣으세요.")
    generate_blog_post(
        topic=topic,
        angle=angle,
        notes=notes,
        text_provider=args.text_provider,
        translation_provider=args.translation_provider,
        date_override=args.date,
    )
