"""AI 코딩 도구 심층 기술 글 자동 생성."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from blog_i18n import get_gemini_client
from post_common import (
    FORBIDDEN_REPEAT_COUNT,
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

AI_CODING_TOOLS = (
    "OpenAI Codex", "Claude Code", "Grok Build", "Antigravity CLI",
    "Cursor", "GitHub Copilot", "Copilot", "Junie AI", "JetBrains AI Assistant",
    "ChatGPT", "OpenAI", "Anthropic", "Gemini", "Ollama", "LM Studio",
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
    return metadata, slug


def build_generation_prompt(recent_titles: list[str], recent_slugs: list[str], current_time: str) -> str:
    tools = ", ".join(AI_CODING_TOOLS)
    recent_titles_str = (
        "\n    ".join(f"- {t}" for t in recent_titles)
        if recent_titles else "- 아직 작성된 글이 없습니다."
    )
    token_counts = count_token_frequency(recent_titles, recent_slugs)
    forbidden_str = ", ".join(sorted(find_forbidden_tokens(token_counts))) or "없음"
    repeated_str = ", ".join(format_repeated_tokens(token_counts)) or "아직 뚜렷한 반복 패턴 없음"

    return f"""
당신은 시니어 풀스택 웹 개발자입니다. 이 블로그는 **AI 코딩 도구와 LLM 활용**을 주력 주제로 다룹니다.
아래 도구·서비스 중 하나를 중심으로, 실무에서 바로 쓸 수 있는 포스트를 작성하세요.

**[핵심 주제: AI 코딩 도구 & LLM]**
- 코딩 에이전트/CLI: OpenAI Codex, Claude Code, Grok Build, Antigravity CLI
- IDE AI: Cursor, GitHub Copilot, Copilot, Junie AI, JetBrains AI Assistant
- LLM 서비스: OpenAI, Anthropic, ChatGPT, Gemini
- 로컬 LLM: Ollama, LM Studio
- 공통 실무: 프롬프트 설계, 컨텍스트 관리, MCP/tool calling, 코드 리뷰·테스트 보조, 워크플로 비교

**[주제 선정 — 반드시 지킬 것]**
- 매 글마다 {tools} 중 **아직 다루지 않은 도구**를 우선 선택하세요.
- 제목·slug·태그 중 하나에는 선택한 도구명을 반드시 그대로 포함하세요. 없으면 자동으로 거부됩니다.
- RAG, AWS, Kubernetes 등은 선택한 AI 도구와 직접 연결될 때만 보조로 언급하세요.
- 설정 방법, 동작 원리, 트레이드오프, 실패 사례 중심으로 쓰세요.

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
- 해요체와 합니다체를 문단·섹션마다 자연스럽게 섞기 (한 어미로 통일 금지)
  - 해요체: 소감·체감·제안 / 합니다체: 사실·기술 설명
  - 섹션 안에서도 2~3문장마다 어미 리듬을 바꿀 것
- 짧고 명확한 문장. 불필요한 형용사·부사 최소화.
- 구조: 문제 → 원리 → 코드/설정 → 주의점 → 결론
- 코드: 의미 있는 이름, 짧은 단위, 필요한 주석만(왜 하는지)
- Secret은 플레이스홀더만 (`<YOUR_API_KEY>`)

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


def generate_blog_post() -> str:
    today = get_kst_now()
    current_time = today.strftime("%Y-%m-%d %H:%M:%S +0900")

    recent_titles = get_recent_titles(50)
    recent_slugs = get_recent_slugs(50)
    prompt = build_generation_prompt(recent_titles, recent_slugs, current_time)

    client = get_gemini_client()

    def validate(content: str) -> tuple[dict, str]:
        try:
            return validate_deep_dive_content(content)
        except ValueError as exc:
            preview = content[:300].replace("\n", " ")
            raise ValueError(f"{exc} | 응답 미리보기: {preview}") from exc

    content, metadata, slug = generate_with_retry(client, prompt, validate)

    clean_english_topic = slug.replace("-", " ")
    image_prompt = (
        f"Modern tech blog thumbnail about: '{clean_english_topic}'. "
        "AI coding tools, IDE, terminal, clean vector art, dark background."
    )

    return publish_post(
        client,
        content,
        metadata,
        slug,
        image_prompt=image_prompt,
        post_type="deep-dive",
        today=today,
    )


if __name__ == "__main__":
    generate_blog_post()