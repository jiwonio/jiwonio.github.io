import os
import re
import time
from datetime import datetime, timezone, timedelta
from io import BytesIO

import yaml
from google import genai

# 이미지 압축을 위해 PIL(Pillow) 모듈 임포트
try:
    from PIL import Image
except ImportError:
    print("⚠️ Pillow 라이브러리가 설치되지 않았습니다. 이미지를 원본으로 저장합니다.")
    Image = None

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
REQUIRED_FIELDS = ("layout", "title", "slug", "date", "categories", "tags", "description")


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


def get_existing_tag_spellings():
    spellings = {}
    for root, _, files in os.walk("_posts"):
        for file in files:
            if not file.endswith(".md"):
                continue
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as post_file:
                    metadata = parse_front_matter(post_file.read())
                for tag in metadata["tags"]:
                    spellings.setdefault(tag.casefold(), tag)
            except (OSError, UnicodeError, yaml.YAMLError, ValueError):
                continue
    return spellings


def validate_generated_content(content):
    metadata = parse_front_matter(content)

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(metadata["slug"]).lower()).strip("-")
    if not slug:
        raise ValueError("slug를 영문과 숫자로 생성해야 합니다.")

    if "<!--more-->" not in content:
        raise ValueError("<!--more--> 구분자가 없습니다.")
    if "[HERO_IMAGE]" not in content:
        raise ValueError("[HERO_IMAGE] 자리 표시자가 없습니다.")
    if "### 참고문헌" not in content:
        raise ValueError("참고문헌 섹션이 없습니다.")

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

    for root, _, files in os.walk("_posts"):
        for file in files:
            if file.endswith(f"-{slug}.md"):
                raise ValueError(f"이미 존재하는 slug입니다: {slug}")

    return metadata, slug

def get_recent_titles(limit=50):
    """기존 발행된 포스트의 제목들을 읽어와 중복을 방지하기 위한 리스트 반환"""
    files_list = []
    for root, dirs, files in os.walk('_posts'):
        for file in files:
            if file.endswith('.md'):
                files_list.append(os.path.join(root, file))
    
    # 파일명 기준 내림차순 정렬 (최신 글부터)
    files_list.sort(reverse=True)
    
    titles = []
    for filepath in files_list[:limit]:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # 정규식으로 title 추출
                title_match = re.search(r'title:\s*"([^"]+)"', content) or re.search(r"title:\s*'([^']+)'", content)
                if title_match:
                    titles.append(title_match.group(1))
        except Exception:
            continue
    return titles

def generate_blog_post():
    # KST (한국 표준시) 설정: UTC + 9시간
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst)
    year = today.strftime("%Y")
    today_date = today.strftime("%Y-%m-%d")
    current_time = today.strftime("%Y-%m-%d %H:%M:%S +0900")
    
    # 최근 포스트 제목 가져오기
    recent_titles = get_recent_titles(50)
    recent_titles_str = "\n    ".join([f"- {t}" for t in recent_titles]) if recent_titles else "- 아직 작성된 글이 없습니다."
    
    # [수정] meta -> description 변경, 고정 카테고리 풀 제공
    prompt = f"""
    당신은 AI 애플리케이션을 직접 설계하고 운영하는 숙련된 서버 엔지니어이자 풀스택 웹 개발자입니다.
    이 블로그는 **AI 개발 및 AI 엔지니어링을 주력 주제**로 다룹니다. 따라서 아래 AI 주제 중 하나를 선정하여 완성된 블로그 포스트를 작성해 주세요.

    **[최우선 주제: AI 개발 및 엔지니어링]**
    - AI 코딩 도구 실전 활용: OpenAI Codex, Claude Code, GitHub Copilot, Gemini CLI, Cursor, 코드 리뷰 및 테스트 자동화
    - AI 에이전트 및 워크플로: MCP(Model Context Protocol), tool calling, 멀티 에이전트, LangGraph, CrewAI, LlamaIndex
    - LLM 애플리케이션 설계: RAG, GraphRAG, 임베딩, 벡터 데이터베이스, reranking, structured output, 메모리와 컨텍스트 관리
    - LLMOps 및 운영: 평가(Evals), 관측성, 프롬프트 버전 관리, 캐싱, 비용 최적화, 지연 시간 개선, 안전장치와 장애 대응
    - 모델 API 및 오픈소스 모델: OpenAI, Anthropic, Google Gemini, xAI, 로컬 LLM, 추론 서버, 모델 라우팅
    - AI 보안과 품질: prompt injection, 데이터 유출 방지, hallucination 측정, 권한 통제, red teaming, AI 거버넌스
    - AI 제품 개발: 챗봇을 넘어선 백엔드 통합, 검색, 문서 처리, 음성·이미지 멀티모달, 업무 자동화 사례

    **[보조 주제: AI 인프라와 기반 기술]**
    서버, 웹, 클라우드, 데이터베이스, Kubernetes, AWS, Python 등의 전통적인 개발 주제는 반드시 **AI 시스템을 구축하거나 운영하는 문제와 직접 연결될 때만** 선택하세요.
    일반적인 웹 개발, 단순 서버 구축, AI와 무관한 클라우드 튜토리얼만을 단독 주제로 선택하지 마세요.

    **[주제 다양성 원칙]**
    - RAG와 멀티 에이전트에만 편중하지 말고 위 세부 분야를 번갈아 선택하세요.
    - 특정 제품 소개보다 실제 설계 판단, 구현, 평가, 운영 문제를 중심으로 작성하세요.
    - 최근 제목 목록과 겹치지 않는 AI 문제를 선택하고, 동일 프레임워크의 유사 튜토리얼을 반복하지 마세요.
    - 빠르게 변하는 모델명, API, 가격, 성능 수치는 단정하지 말고 공식 문서를 참고문헌으로 제시하세요.

    **[🔥 매우 중요: 주제 중복 방지]**
    아래는 최근에 블로그에 작성된 글의 제목들입니다. **아래 목록에 있는 주제나 이와 매우 유사한 내용은 절대 다시 작성하지 마세요.** 완전히 새롭고 다른 카테고리의 주제를 선정하세요.
    {recent_titles_str}

    **[💎 매우 중요: 최고 수준의 퀄리티와 SEO 최적화]**
    - 검색 엔진 최적화(SEO)를 고려하여 핵심 키워드를 제목, 메타 설명, 본문 첫 문단 및 소제목에 자연스럽게 배치하세요.
    - 단순한 개념 요약이나 초보적인 튜토리얼은 작성하지 마세요.
    - 글의 구조는 반드시 **[도입 배경 및 문제 정의] ➡️ [핵심 아키텍처 및 원리] ➡️ [실무 적용 코드/설정 딥다이브] ➡️ [성능 최적화 및 Best Practices] ➡️ [결론]** 의 논리적 흐름을 따르세요.
    - 현업에서 즉시 적용 가능한 수준의 구체적이고 실용적인 트러블슈팅, 코드 예시, 설정 파일(yaml, conf 등)을 풍부하게 담아주세요.
    - [🚨 보안 주의] 코드 예시나 설정 파일(yaml, json 등)을 작성할 때 Slack Webhook URL, AWS Access Key, DB 비밀번호, API Key 등 실제처럼 보이는 Secret 값은 절대 생성하지 마세요. 대신 반드시 `<YOUR_SLACK_WEBHOOK_URL>`, `https://hooks.slack.com/services/YOUR/DUMMY/TOKEN` 같이 명백한 플레이스홀더(Placeholder)를 사용하세요.

    반드시 아래의 **'블로그 작성 가이드라인'**을 완벽하게 준수해야 합니다. 마크다운 코드 외에 다른 부가적인 설명이나 인사말은 절대 출력하지 마세요.

    ## [블로그 작성 가이드라인]

    ### 1. Front Matter (YAML)
    반드시 아래 형식을 지켜서 작성하세요. `title`, `slug`, `description`의 값은 반드시 큰따옴표(")로 감싸야 합니다.
    **[중요 주의사항]** `title`과 `description` 내용 내부에는 절대 큰따옴표(")를 사용하지 마세요. 강조가 필요하다면 작은따옴표(')를 사용하세요. (YAML 파싱 에러 방지)
    ---
    layout: post
    title: "여기에 매력적이고 검색 가능한 한글 제목 작성"
    slug: "english-title-for-url-slug"
    date: {current_time}
    categories: [카테고리명] # [AI], [Backend], [DevOps], [Cloud], [CS] 중 1~2개 선택. 반드시 AI 포함
    tags: [태그1, 태그2, 태그3]
    description: "구글 검색 결과에 노출될 SEO 최적화 요약문. 핵심 키워드를 포함하여 150자 내외로 작성. (내부에 큰따옴표 절대 금지)"
    ---

    ### 2. 도입부 및 미리보기 자르기 (한국어 전용)
    - Front Matter 바로 아래에는 독자의 흥미를 끄는 **한국어 도입부(2~3문단)**를 작성하세요. 핵심 키워드를 자연스럽게 포함하세요.
    - 도입부 작성이 끝나면 반드시 빈 줄을 하나 두고 `<!--more-->` 태그를 삽입하세요. (이 태그를 기준으로 목록에서 미리보기가 잘립니다.)

    ### 3. 메인 썸네일 이미지 자리 표시자
    - `<!--more-->` 태그 바로 아래에 정확히 `[HERO_IMAGE]` 라고만 작성하세요. (이 부분은 파이썬 스크립트가 실제 생성된 이미지로 자동 치환합니다.)
    - 그 아래에 빈 줄을 하나 두고 `-----` (하이픈 5개)를 넣어 구분선을 만드세요.

    ### 4. 본문 (Korean Main Content)
    - 본문은 '~습니다', '~합니다' 체의 정중하고 전문적인 문체를 사용하세요.
    - **[🚨 매우 중요: 외부 이미지 사용 금지]** 본문 내에 가짜 외부 이미지 URL(예: `![설명](https://...)`)을 절대 삽입하지 마세요. 404 에러가 발생하는 것을 막기 위함입니다. 시각적 설명이 필요하다면 이미지 대신 마크다운 표(Table)나 코드 블록을 활용하세요. 이미지는 오직 `[HERO_IMAGE]` 하나만 허용됩니다.
    - **가독성 및 SEO:** 검색 엔진이 이해하기 쉽도록 `##` (H2 태그)와 `###` (H3 태그)를 의미에 맞게 계층적으로 사용하세요.
    - **강조:** 중요한 키워드나 개념은 `**굵게(Bold)**` 처리하여 독자의 시선이 머물게 하세요.
    - **인라인 코드:** 명령어, 변수명 등은 백틱(`)으로 감싸세요.
    - **코드 블록:** 프로그래밍 언어 태그를 포함한 마크다운 코드 블록을 작성하세요.
    - **링크 포맷:** 모든 외부 링크는 반드시 `[표시할 텍스트](URL "툴팁 텍스트"){{:target="_blank"}}` 형식을 따르세요.

    ### 5. 참고문헌
    - 글의 맨 마지막에는 `### 참고문헌` 소제목을 넣고, 본문에서 언급된 공식 문서, 신뢰할 수 있는 외부 레퍼런스 등을 리스트 형태로 정리하세요. (외부 링크는 SEO에 긍정적인 영향을 줍니다)
    """

    max_retries = 3
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 AI 글쓰기 API 요청 중... (시도 {attempt}/{max_retries})")
            
            # 1. 텍스트 생성 (Gemini 2.5 Pro)
            response = client.models.generate_content(
                model="gemini-2.5-pro", 
                contents=prompt
            )
            
            content = response.text.strip()
            
            # 마크다운 블록 기호 제거
            if content.startswith("```markdown"):
                content = content[11:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # 🚨 가짜 이미지 링크 강제 제거
            content = re.sub(r'!\[[^\]]*\]\(https?://[^\)]+\)', '', content)

            # GitHub Secret Scanning 차단 방지 (Slack Webhook 등 더미 처리)
            content = re.sub(
                r'https://hooks\.slack\.com/services/[A-Za-z0-9]+/[A-Za-z0-9]+/[A-Za-z0-9]+', 
                'https://hooks.slack.com/services/YOUR_WORKSPACE/YOUR_CHANNEL/YOUR_TOKEN', 
                content
            )
            content = re.sub(r'(?i)(api_key|secret_key|password|token)\s*[:=]\s*["\'][A-Za-z0-9_-]{15,}["\']', r'\1: "YOUR_DUMMY_SECRET_HERE"', content)

            metadata, slug = validate_generated_content(content)
            raw_title = str(metadata["title"])

            # 2. 썸네일 이미지 생성 및 WebP 압축 (Imagen 4.0)
            image_md = ""
            try:
                print(f"🎨 '{raw_title}' 주제로 썸네일 생성 중...")
                clean_english_topic = slug.replace('-', ' ')
                image_prompt = f"A modern, high quality conceptual illustration for an IT tech blog post about: '{clean_english_topic}'. Clean vector art style, abstract representation of server, code, or cloud computing. Dark background."
                
                image_result = client.models.generate_images(
                    model='imagen-4.0-generate-001',
                    prompt=image_prompt,
                    config={"number_of_images": 1, "aspect_ratio": "16:9"}
                )
                image_bytes = image_result.generated_images[0].image.image_bytes
                
                upload_dir = f"uploads/{slug}"
                os.makedirs(upload_dir, exist_ok=True)
                
                # [수정] Pillow를 이용한 이미지 리사이징 및 WebP 저장 (저장소 용량 최적화)
                if Image:
                    image_path = f"{upload_dir}/thumbnail.webp"
                    img = Image.open(BytesIO(image_bytes))
                    
                    # 너비 800px 기준으로 비율 맞춰 리사이징
                    base_width = 800
                    w_percent = (base_width / float(img.size[0]))
                    h_size = int((float(img.size[1]) * float(w_percent)))
                    img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
                    
                    # WebP 포맷으로 저장 (품질 85)
                    img.save(image_path, "WEBP", quality=85)
                    print(f"✅ 이미지 압축 저장 완료 (WebP): {image_path}")
                else:
                    # Pillow가 없으면 원본 그대로 jpg로 저장
                    image_path = f"{upload_dir}/thumbnail.jpg"
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
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
                print(f"⚠️ 503 에러. 15초 후 재시도...")
                if attempt < max_retries: time.sleep(15)
            else:
                print(f"❌ 생성 중 에러 발생: {e}")
                if attempt < max_retries:
                    time.sleep(5)

    raise RuntimeError(f"포스트 생성에 실패했습니다: {last_error}")

if __name__ == "__main__":
    generate_blog_post()
