"""AI 코딩 도구 심층 기술 글 자동 생성."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from llm_client import list_available_providers
from post_common import (
    FORBIDDEN_REPEAT_COUNT,
    body_after_more,
    count_token_frequency,
    format_repeated_tokens,
    generate_with_retry,
    get_existing_ko_slugs,
    get_kst_now,
    get_recent_slugs,
    get_recent_titles,
    normalize_slug,
    publish_post,
    tokenize,
    validate_base_content,
    validate_tag_consistency,
)
from prompt_config import DEEP_DIVE_SYSTEM_PROMPT

AI_CODING_TOOLS = (
    "OpenAI Codex", "Claude Code", "Grok Build", "Antigravity CLI",
    "Cursor", "GitHub Copilot", "Copilot", "Junie AI", "JetBrains AI Assistant",
    "ChatGPT", "OpenAI", "Anthropic", "Gemini", "Ollama", "LM Studio",
)

BANNED_TITLE_PHRASES = (
    "완벽 가이드", "완벽한", "프로덕션급", "Ultimate Guide", "ultimate guide",
    "완전 정복", "마스터하기",
)

POST_ANGLES = (
    "Before/After: 도입 전·후 워크플로 비교",
    "실패 사례: 잘못 쓰면 생기는 문제 + 재현 가능한 증상",
    "의사결정: A vs B 선택 기준표",
    "숨은 비용: API·토큰·CI·인지 부하 등 간과되는 비용",
    "팀 도입: 1인 → 3인 → 10인 팀에서 바뀌는 설정·규칙",
)


def find_forbidden_tokens(counts: dict[str, int]) -> set[str]:
    return {word for word, count in counts.items() if count >= FORBIDDEN_REPEAT_COUNT}


def contains_ai_tool(*texts: str) -> bool:
    combined = " ".join(texts).casefold()
    return any(tool.casefold() in combined for tool in AI_CODING_TOOLS)


def check_title_not_repetitive(new_title: str, recent_titles: list[str], recent_slugs: list[str], threshold: float = 0.55) -> None:
    new_tokens = set(tokenize(new_title))
    if len(new_tokens) < 2:
        return

    for recent in recent_titles:
        recent_tokens = set(tokenize(recent))
        if not recent_tokens:
            continue
        overlap = len(new_tokens & recent_tokens) / len(new_tokens | recent_tokens)
        if overlap >= threshold:
            raise ValueError(
                f"제목이 최근 글 '{recent}'과 표현이 겹칩니다. "
                "반복 패턴을 피해 다시 작성하세요."
            )

    forbidden = new_tokens & find_forbidden_tokens(count_token_frequency(recent_titles, recent_slugs))
    if forbidden:
        raise ValueError(
            "다음 단어는 최근 글에서 과도하게 반복되어 사용이 금지되었습니다: "
            + ", ".join(sorted(forbidden))
        )


def validate_deep_dive_content(content: str) -> tuple[dict, str]:
    metadata = validate_base_content(content)
    validate_tag_consistency(metadata)

    slug = normalize_slug(str(metadata["slug"]))
    if slug in get_existing_ko_slugs():
        raise ValueError(f"이미 존재하는 slug입니다: {slug}")

    if not contains_ai_tool(metadata["title"], slug, *metadata["tags"]):
        raise ValueError(
            "제목·slug·태그 어디에도 AI 코딩 도구/서비스명이 없습니다. "
            f"{', '.join(AI_CODING_TOOLS)} 중 하나를 중심으로 다시 작성하세요."
        )

    check_title_not_repetitive(metadata["title"], get_recent_titles(50), get_recent_slugs(50))

    title_lower = str(metadata["title"]).casefold()
    for phrase in BANNED_TITLE_PHRASES:
        if phrase.casefold() in title_lower:
            raise ValueError(f"제목에 금지된 포괄 표현이 있습니다: {phrase}")

    if not has_application_table(content):
        raise ValueError(
            "결론에 적용 조건 표가 필요합니다. | 상황 | 추천 | 이유 | 형식의 마크다운 표를 포함하세요."
        )

    return metadata, slug


def has_application_table(content: str) -> bool:
    body = body_after_more(content).split("### 참고문헌", 1)[0]
    if "|" not in body:
        return False
    return ("상황" in body and "추천" in body and "이유" in body)


def build_generation_prompt(recent_titles: list[str], recent_slugs: list[str], current_time: str) -> str:
    tools = ", ".join(AI_CODING_TOOLS)
    recent_titles_str = (
        "\n    ".join(f"- {t}" for t in recent_titles)
        if recent_titles else "- 아직 작성된 글이 없습니다."
    )
    token_counts = count_token_frequency(recent_titles, recent_slugs)
    forbidden_str = ", ".join(sorted(find_forbidden_tokens(token_counts))) or "없음"
    repeated_str = ", ".join(format_repeated_tokens(token_counts)) or "아직 뚜렷한 반복 패턴 없음"

    angles_str = "\n".join(f"- {angle}" for angle in POST_ANGLES)

    return f"""
이 블로그는 **AI 코딩 도구와 LLM 활용**을 주력 주제로 다룹니다.
아래 도구·서비스 중 하나를 중심으로, 실무에서 바로 쓸 수 있는 포스트를 작성하세요.

**[핵심 주제: AI 코딩 도구 & LLM]**
- 코딩 에이전트/CLI: OpenAI Codex, Claude Code, Grok Build, Antigravity CLI
- IDE AI: Cursor, GitHub Copilot, Copilot, Junie AI, JetBrains AI Assistant
- LLM 서비스: OpenAI, Anthropic, ChatGPT, Gemini
- 로컬 LLM: Ollama, LM Studio
- 공통 실무: 프롬프트 설계, 컨텍스트 관리, MCP/tool calling, 코드 리뷰·테스트 보조, 워크플로 비교

**[글 각도 — 매 글 하나만 선택, 제목에 반영]**
{angles_str}

**[주제 선정 — 반드시 지킬 것]**
- 매 글마다 {tools} 중 **아직 다루지 않은 도구**를 우선 선택하세요.
- 제목·slug·태그 중 하나에는 선택한 도구명을 반드시 그대로 포함하세요. 없으면 자동으로 거부됩니다.
- RAG, AWS, Kubernetes 등은 선택한 AI 도구와 직접 연결될 때만 보조로 언급하세요.
- 설정 나열만 하지 말고, 선택한 각도에 맞는 비교·실패·비용·팀 도입 관점을 유지하세요.

**[제목 패턴 — 아래 중 하나]**
- "{{도구}}로 {{문제}} 줄이기: {{방법 한 줄}}"
- "{{도구}} {{기능}} 써 봤을 때 생긴 {{실수/비용}}"
- "팀에 {{도구}} 도입할 때 {{역할}}이 먼저 정해야 할 것"
"완벽 가이드", "프로덕션급", "완전 정복" 같은 포괄 표현 금지

**[도입부 필수]**
- 첫 2문단: 구체적 상황 1개 (PR 리뷰 밀림, 레거시 수정, 온콜 중 장애, 토큰 비용 폭증 등)
- 세 번째 문단: 이 글을 읽으면 해결되는 한 가지를 명시

**[최근 제목 — 주제·표현 모두 참고]**
{recent_titles_str}

**[사용 금지 단어 — {FORBIDDEN_REPEAT_COUNT}회 이상 반복됨]**
{forbidden_str}
위 단어는 제목·slug·description에 절대 사용하지 마세요. 포함되면 자동으로 거부되고 다시 작성해야 합니다.

**[추가 참고 — 2회 이상 등장한 표현]**
{repeated_str}
위 표현이 만드는 클리셰·문장 틀(예: '완벽 가이드', '프로덕션급 ~ 구축')도 스스로 점검해 피하세요.

**[글쓰기 스타일]**
- 블로그 주인이 직접 쓰는 1인칭 기술 글 (자기소개·직함 나열로 시작하지 않기)
- 문장 끝은 '~습니다·입니다' 체로 자연스럽게 통일. '~요', '~해요', '~다' 체 금지
- 짧고 명확한 문장. 불필요한 형용사·부사·마케팅 문구 최소화
- 구조: 문제 → 원리 → 코드/설정 → 주의점 → 결론
- 코드: 의미 있는 이름, 짧은 단위, 필요한 주석만(왜 하는지)
- Secret은 플레이스홀더만 (`<YOUR_API_KEY>`)

**[결론 필수]**
| 상황 | 추천 | 이유 |
형식의 마크다운 표를 포함하세요. 최소 3행(1인 사이드, 스타트업 5인, 레거시 많음 등).

아래는 출력 순서를 안내하는 지침입니다. 번호와 설명("Front Matter", "도입부" 등)은
지침일 뿐이며 결과물에 그대로 옮겨 쓰면 안 됩니다. 마크다운 글 본문 외 다른 설명은 출력하지 마세요.

[출력 순서]
1) 아래 형식의 YAML Front Matter를 값만 채워서 그대로 작성합니다.
---
layout: post
title: "구체적인 한글 제목"
slug: "english-slug-for-this-topic"
lang: ko
translation_key: "english-slug-for-this-topic"
post_type: deep-dive
date: {current_time}
categories: [AI]
tags: [태그1, 태그2, 태그3]
description: "150자 내외 SEO 요약"
image: "/uploads/english-slug-for-this-topic/thumbnail.webp"
---
2) 도입부 2~3문단을 작성한 뒤, 줄을 바꿔 `<!--more-->` 한 줄만 단독으로 작성합니다.
3) 바로 다음 줄에 `[HERO_IMAGE]` 한 줄만 단독으로 작성하고, 그다음 줄에 `-----` 한 줄만 단독으로 작성합니다.
4) 본문을 작성합니다. '~습니다' 체, H2/H3 계층, 외부 이미지 URL 금지.
   링크: `[텍스트](URL "툴팁"){{:target="_blank"}}`
5) 마지막에 `### 참고문헌` 섹션을 작성하고 출처 링크를 나열합니다.

주의: 1)~5)는 작성 순서 설명일 뿐 실제 헤더가 아닙니다. "Front Matter", "도입부", "본문" 같은
지침 단어나 1) 2) 3) 같은 번호를 결과물에 절대 출력하지 마세요.
"""


def generate_blog_post(*, text_provider: str | None = None, translation_provider: str | None = None) -> str:
    today = get_kst_now()
    current_time = today.strftime("%Y-%m-%d %H:%M:%S +0900")

    recent_titles = get_recent_titles(50)
    recent_slugs = get_recent_slugs(50)
    prompt = build_generation_prompt(recent_titles, recent_slugs, current_time)

    def validate(content: str) -> tuple[dict, str]:
        try:
            return validate_deep_dive_content(content)
        except ValueError as exc:
            preview = content[:300].replace("\n", " ")
            raise ValueError(f"{exc} | 응답 미리보기: {preview}") from exc

    content, metadata, slug = generate_with_retry(
        prompt,
        validate,
        post_type="deep-dive",
        text_provider=text_provider,
        system_prompt=DEEP_DIVE_SYSTEM_PROMPT,
    )

    clean_english_topic = slug.replace("-", " ")
    image_prompt = (
        f"Modern tech blog thumbnail about: '{clean_english_topic}'. "
        "AI coding tools, IDE, terminal, clean vector art, dark background."
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


def dry_run() -> int:
    """API 호출 없이 생성 전제 조건만 확인합니다."""
    issues: list[str] = []

    print("🔍 Deep-dive dry-run (API 호출 없음)")

    available = list_available_providers()
    print(f"  사용 가능 provider: {', '.join(available) or '없음'}")
    if not available:
        issues.append("No LLM API keys configured (GEMINI/ANTHROPIC/OPENAI/XAI)")

    recent_titles = get_recent_titles(50)
    recent_slugs = get_recent_slugs(50)
    token_counts = count_token_frequency(recent_titles, recent_slugs)
    forbidden = find_forbidden_tokens(token_counts)
    print(f"  금지 토큰: {', '.join(sorted(forbidden)) or '없음'}")
    print(f"  기존 ko slug 수: {len(get_existing_ko_slugs())}")

    if recent_slugs:
        print(f"  최근 slug: {', '.join(recent_slugs[:5])}")
    else:
        print("  최근 slug: 없음")

    if issues:
        print("\n❌ dry-run 실패:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("  ✅ 사전 조건 통과")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI 코딩 도구 심층 기술 글 자동 생성")
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
    args = parser.parse_args()

    if args.dry_run:
        raise SystemExit(dry_run())
    generate_blog_post(
        text_provider=args.text_provider,
        translation_provider=args.translation_provider,
    )