import io
import os
import re
import time
from datetime import datetime, timezone, timedelta

import yaml
from google import genai
from google.genai import types

# 이미지 압축을 위해 PIL(Pillow) 모듈 임포트
try:
    from PIL import Image
except ImportError:
    print("⚠️ Pillow 라이브러리가 설치되지 않았습니다. 이미지를 원본으로 저장합니다.")
    Image = None

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
REQUIRED_FIELDS = ("layout", "title", "slug", "date", "categories", "tags", "description")
TITLE_PATTERN = re.compile(r'title:\s*"([^"]+)"|title:\s*\'([^\']+)\'')
SLUG_FROM_FILE = re.compile(r"\d{4}-\d{2}-\d{2}-(.+)\.md$")

AI_CODING_TOOLS = (
    "OpenAI Codex", "Claude Code", "Grok Build", "Antigravity CLI",
    "Cursor", "GitHub Copilot", "Copilot", "Junie AI", "JetBrains AI Assistant",
    "ChatGPT", "OpenAI", "Anthropic", "Gemini", "Ollama", "LM Studio",
)
IMAGE_MODEL = "gemini-3.1-flash-image"
FORBIDDEN_REPEAT_COUNT = 3  # 이 횟수 이상 반복된 단어는 다음 글 제목에서 하드 차단
# 모델이 프롬프트의 출력 지침 문구를 본문에 그대로 베껴 쓰면 등장하는 표현 (누출 감지용)
PROMPT_LEAK_PHRASES = ("Front Matter", "지침일 뿐이며", "결과물에 그대로 옮겨")
# 한글 단어 사이에 일본어 가나가 섞이는 등의 모델 출력 오류 감지 (예: '네이ティブ')
UNEXPECTED_SCRIPT_PATTERN = re.compile(r"[぀-ヿｦ-ﾝ�]")
CODE_BLOCK_PATTERN = re.compile(r"```.*?```", re.DOTALL)
EXTERNAL_IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\(https?://[^)]+\)")


def parse_front_matter(content):
    match = FRONT_MATTER_PATTERN.match(content)
    if not match:
        raise ValueError("YAML front matter가 없거나 형식이 잘못되었습니다.")

    metadata = yaml.safe_load(match.group(1))
    if not isinstance(metadata, dict):
        raise ValueError("Front matter는 YAML mapping 형식이어야 합니다.")

    missing = [field for field in REQUIRED_FIELDS if not metadata.get(field)]
    if missing:
        raise ValueError(f"필수 front matter 누락: {', '.join(missing)}")

    if metadata["layout"] != "post":
        raise ValueError("layout은 post여야 합니다.")

    for field in ("categories", "tags"):
        values = metadata[field]
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value.strip() for value in values
        ):
            raise ValueError(f"{field}는 비어 있지 않은 문자열 목록이어야 합니다.")

    if "AI" not in metadata["categories"]:
        raise ValueError("AI 중심 포스트는 categories에 AI를 포함해야 합니다.")

    return metadata


def list_post_files():
    """_posts 디렉터리의 모든 마크다운 포스트 경로."""
    return [
        os.path.join(root, name)
        for root, _, names in os.walk("_posts")
        for name in names
        if name.endswith(".md")
    ]


def get_existing_tag_spellings():
    spellings = {}
    for path in list_post_files():
        try:
            with open(path, "r", encoding="utf-8") as post_file:
                metadata = parse_front_matter(post_file.read())
            for tag in metadata["tags"]:
                spellings.setdefault(tag.casefold(), tag)
        except (OSError, UnicodeError, yaml.YAMLError, ValueError):
            continue
    return spellings


def contains_ai_tool(*texts):
    """제목·slug·태그 중 하나라도 AI_CODING_TOOLS의 도구명을 포함하는지 확인."""
    combined = " ".join(texts).casefold()
    return any(tool.casefold() in combined for tool in AI_CODING_TOOLS)


def validate_generated_content(content):
    metadata = parse_front_matter(content)

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(metadata["slug"]).lower()).strip("-")
    if not slug:
        raise ValueError("slug를 영문과 숫자로 생성해야 합니다.")

    if not has_standalone_line(content, "<!--more-->"):
        raise ValueError("<!--more--> 구분자가 단독 줄로 존재하지 않습니다(프롬프트 지침 문구 누출 가능성).")
    if not has_standalone_line(content, "[HERO_IMAGE]"):
        raise ValueError("[HERO_IMAGE] 자리 표시자가 단독 줄로 존재하지 않습니다(프롬프트 지침 문구 누출 가능성).")
    if "### 참고문헌" not in content:
        raise ValueError("참고문헌 섹션이 없습니다.")

    leaked_phrases = [phrase for phrase in PROMPT_LEAK_PHRASES if phrase in content]
    if leaked_phrases:
        raise ValueError(
            "프롬프트 지침 문구가 본문에 그대로 노출되었습니다: " + ", ".join(leaked_phrases)
        )

    stray_chars = find_unexpected_scripts(content)
    if stray_chars:
        raise ValueError(
            "한글 문장에 의도하지 않은 문자가 섞여 있습니다(예: '네이ティブ'): "
            + ", ".join(stray_chars)
        )

    if EXTERNAL_IMAGE_PATTERN.search(content):
        raise ValueError("본문에 외부 이미지 링크가 포함되어 있습니다. 이미지는 [HERO_IMAGE]만 사용하세요.")

    existing_tags = get_existing_tag_spellings()
    inconsistent_tags = [
        tag for tag in metadata["tags"]
        if tag.casefold() in existing_tags and tag != existing_tags[tag.casefold()]
    ]
    if inconsistent_tags:
        expected = [existing_tags[tag.casefold()] for tag in inconsistent_tags]
        raise ValueError(
            "기존 태그와 대소문자가 다릅니다: "
            + ", ".join(f"{tag} -> {canonical}" for tag, canonical in zip(inconsistent_tags, expected))
        )

    existing_slugs = {extract_slug_from_path(path) for path in list_post_files()}
    if slug in existing_slugs:
        raise ValueError(f"이미 존재하는 slug입니다: {slug}")

    if not contains_ai_tool(metadata["title"], slug, *metadata["tags"]):
        raise ValueError(
            "제목·slug·태그 어디에도 AI 코딩 도구/서비스명이 없습니다. "
            f"{', '.join(AI_CODING_TOOLS)} 중 하나를 중심으로 다시 작성하세요."
        )

    check_title_not_repetitive(metadata["title"], get_recent_titles(), get_recent_slugs())

    return metadata, slug


def tokenize(text):
    return [t for t in re.findall(r"[\w가-힣]+", text.casefold()) if len(t) >= 2]


def has_standalone_line(content, marker):
    """marker가 다른 텍스트와 섞이지 않고 한 줄을 단독으로 차지하는지 확인."""
    return any(line.strip() == marker for line in content.splitlines())


def find_unexpected_scripts(content):
    """코드 블록을 제외한 본문에서 일본어 가나·치환 문자 등 의도치 않은 문자를 찾는다."""
    prose = CODE_BLOCK_PATTERN.sub("", content)
    return sorted(set(UNEXPECTED_SCRIPT_PATTERN.findall(prose)))


def extract_title(content):
    match = TITLE_PATTERN.search(content)
    if not match:
        return None
    return match.group(1) or match.group(2)


def extract_slug_from_path(path):
    match = SLUG_FROM_FILE.match(os.path.basename(path))
    return match.group(1) if match else None


def get_recent_post_files(limit=50):
    return sorted(list_post_files(), reverse=True)[:limit]


def get_recent_titles(limit=50):
    titles = []
    for path in get_recent_post_files(limit):
        try:
            with open(path, encoding="utf-8") as post_file:
                title = extract_title(post_file.read())
            if title:
                titles.append(title)
        except OSError:
            continue
    return titles


def get_recent_slugs(limit=50):
    return [
        slug for path in get_recent_post_files(limit)
        if (slug := extract_slug_from_path(path))
    ]


def count_token_frequency(titles, slugs):
    """최근 제목·slug에서 토큰별 등장 횟수를 집계 (하드코딩 없음)."""
    counts = {}
    for title in titles:
        for token in set(tokenize(title)):
            counts[token] = counts.get(token, 0) + 1
    for slug in slugs:
        for part in slug.split("-"):
            if len(part) >= 3:
                counts[part] = counts.get(part, 0) + 1
    return counts


def format_repeated_tokens(counts, min_count=2, limit=20):
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [f"{word}({count}회)" for word, count in ranked if count >= min_count][:limit]


def find_forbidden_tokens(counts):
    """FORBIDDEN_REPEAT_COUNT회 이상 반복되어 다음 제목에 쓸 수 없는 단어 집합."""
    return {word for word, count in counts.items() if count >= FORBIDDEN_REPEAT_COUNT}


def check_title_not_repetitive(new_title, recent_titles, recent_slugs, threshold=0.55):
    """최근 제목과 표현이 겹치거나 과사용된 단어를 쓰면 재생성을 유도."""
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


def generate_thumbnail(client, prompt):
    """Gemini 3.1 Flash Image로 썸네일 생성 (Imagen 4 대체)."""
    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="16:9"),
        ),
    )
    for part in response.parts:
        if part.inline_data is not None:
            return part.inline_data.data
    raise ValueError("이미지 응답이 없습니다.")


def build_generation_prompt(recent_titles, recent_slugs, current_time):
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
date: {current_time}
categories: [AI]
tags: [태그1, 태그2, 태그3]
description: "150자 내외 SEO 요약"
---
2) 도입부 2~3문단을 작성한 뒤, 줄을 바꿔 `<!--more-->` 한 줄만 단독으로 작성합니다.
3) 바로 다음 줄에 `[HERO_IMAGE]` 한 줄만 단독으로 작성하고, 그다음 줄에 `-----` 한 줄만 단독으로 작성합니다.
4) 본문을 작성합니다. '~습니다' 체, H2/H3 계층, 외부 이미지 URL 금지.
   링크: `[텍스트](URL "툴팁"){{:target="_blank"}}`
5) 마지막에 `### 참고문헌` 섹션을 작성하고 출처 링크를 나열합니다.

주의: 1)~5)는 작성 순서 설명일 뿐 실제 헤더가 아닙니다. "Front Matter", "도입부", "본문" 같은
지침 단어나 1) 2) 3) 같은 번호를 결과물에 절대 출력하지 마세요.
"""


def strip_code_fence(text):
    """선두/말미의 마크다운 코드펜스(```, ```markdown 등)를 제거."""
    text = re.sub(r"\A```[a-zA-Z]*[ \t]*\r?\n", "", text.strip())
    text = re.sub(r"\r?\n```\s*\Z", "", text)
    return text.strip()


def strip_preamble(text):
    """front matter(---) 앞에 모델이 덧붙인 설명 문구가 있으면 제거."""
    if text.startswith("---"):
        return text
    match = re.search(r"^---\s*$", text, re.MULTILINE)
    return text[match.start():] if match else text


def generate_blog_post():
    # KST (한국 표준시) 설정: UTC + 9시간
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst)
    year = today.strftime("%Y")
    today_date = today.strftime("%Y-%m-%d")
    current_time = today.strftime("%Y-%m-%d %H:%M:%S +0900")
    
    recent_titles = get_recent_titles(50)
    recent_slugs = get_recent_slugs(50)
    prompt = build_generation_prompt(recent_titles, recent_slugs, current_time)

    max_retries = 5
    retry_backoff_seconds = 15
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 AI 글쓰기 API 요청 중... (시도 {attempt}/{max_retries})")
            
            # 1. 텍스트 생성 (Gemini 2.5 Pro)
            response = client.models.generate_content(
                model="gemini-2.5-pro", 
                contents=prompt
            )
            
            content = strip_preamble(strip_code_fence(response.text))

            # GitHub Secret Scanning 차단 방지 (Slack Webhook 등 더미 처리)
            content = re.sub(
                r'https://hooks\.slack\.com/services/[A-Za-z0-9]+/[A-Za-z0-9]+/[A-Za-z0-9]+', 
                'https://hooks.slack.com/services/YOUR_WORKSPACE/YOUR_CHANNEL/YOUR_TOKEN', 
                content
            )
            content = re.sub(r'(?i)(api_key|secret_key|password|token)\s*[:=]\s*["\'][A-Za-z0-9_-]{15,}["\']', r'\1: "YOUR_DUMMY_SECRET_HERE"', content)

            try:
                metadata, slug = validate_generated_content(content)
            except ValueError as e:
                preview = content[:300].replace("\n", " ")
                raise ValueError(f"{e} | 응답 미리보기: {preview}") from e
            raw_title = str(metadata["title"])

            # 2. 썸네일 이미지 생성 및 WebP 압축 (Gemini 3.1 Flash Image)
            image_md = ""
            try:
                print(f"🎨 '{raw_title}' 주제로 썸네일 생성 중...")
                clean_english_topic = slug.replace('-', ' ')
                image_prompt = (
                    f"Modern tech blog thumbnail about: '{clean_english_topic}'. "
                    "AI coding tools, IDE, terminal, clean vector art, dark background."
                )

                thumbnail = generate_thumbnail(client, image_prompt)
                upload_dir = f"uploads/{slug}"
                os.makedirs(upload_dir, exist_ok=True)

                if Image:
                    image_path = f"{upload_dir}/thumbnail.webp"
                    img = Image.open(io.BytesIO(thumbnail))
                    base_width = 800
                    ratio = base_width / img.size[0]
                    img = img.resize(
                        (base_width, int(img.size[1] * ratio)),
                        Image.Resampling.LANCZOS,
                    )
                    img.save(image_path, "WEBP", quality=85)
                    print(f"✅ 이미지 압축 저장 완료 (WebP): {image_path}")
                else:
                    image_path = f"{upload_dir}/thumbnail.jpg"
                    with open(image_path, "wb") as f:
                        f.write(thumbnail)
                    print(f"✅ 원본 이미지 저장 완료: {image_path}")
                
                # SEO용 Alt/Title 추가
                image_md = f"![{raw_title}](/{image_path} \"{raw_title}\")\n\n<p style=\"text-align:center;opacity:0.8;\">\n    <small>&copy; AI Generated Image</small>\n</p>"
                
            except Exception as img_e:
                print(f"⚠️ 이미지 생성 실패 (본문만 작성됨): {img_e}")
            
            # 본문에 치환
            if "[HERO_IMAGE]" in content:
                content = content.replace("[HERO_IMAGE]", image_md)
            else:
                content = content.replace("<!--more-->", f"<!--more-->\n\n{image_md}\n\n-----")

            # 3. 파일 저장
            post_dir = f"_posts/{year}"
            os.makedirs(post_dir, exist_ok=True)
            filename = f"{post_dir}/{today_date}-{slug}.md"

            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"✅ 포스트 저장 완료: {filename}")
            return filename

        except Exception as e:
            last_error = e
            error_msg = str(e)
            if "503" in error_msg or "UNAVAILABLE" in error_msg:
                wait = retry_backoff_seconds * attempt
                print(f"⚠️ 503 에러(서버 과부하). {wait}초 후 재시도...")
                if attempt < max_retries:
                    time.sleep(wait)
            else:
                print(f"❌ 생성 중 에러 발생: {e}")
                if attempt < max_retries:
                    time.sleep(5)

    raise RuntimeError(f"포스트 생성에 실패했습니다: {last_error}")

if __name__ == "__main__":
    generate_blog_post()
