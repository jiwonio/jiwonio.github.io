import os
import re
import time
from google import genai
from datetime import datetime, timezone, timedelta

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

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
    
    # 최근 50개의 포스트 제목을 가져옵니다.
    recent_titles = get_recent_titles(50)
    recent_titles_str = "\n    ".join([f"- {t}" for t in recent_titles]) if recent_titles else "- 아직 작성된 글이 없습니다."
    
    # 100% 한국어로 작성하고, <!--more-->로 자르며, [HERO_IMAGE] 위치를 지정하는 완벽한 프롬프트
    prompt = f"""
    당신은 숙련된 서버 엔지니어이자 풀스택 웹 개발자입니다. 
    최신 웹 개발 트렌드, 서버 인프라 구축, 클라우드(AWS), Python/Django, Node.js, PHP 활용, 개발 환경 설정 등 전문적인 IT 기술 주제 중 하나를 스스로 무작위로 선정하여 완성된 블로그 포스트를 작성해 주세요.

    **[🔥 매우 중요: 주제 중복 방지]**
    아래는 최근에 블로그에 작성된 글의 제목들입니다. **아래 목록에 있는 주제나 이와 매우 유사한 내용은 절대 다시 작성하지 마세요.** 완전히 새롭고 다른 카테고리의 주제를 선정하세요.
    {recent_titles_str}

    **[💎 매우 중요: 최고 수준의 퀄리티와 SEO 최적화]**
    - 검색 엔진 최적화(SEO)를 고려하여 핵심 키워드를 제목, 메타 설명, 본문 첫 문단 및 소제목에 자연스럽게 배치하세요.
    - 단순한 개념 요약이나 초보적인 튜토리얼은 작성하지 마세요.
    - 글의 구조는 반드시 **[도입 배경 및 문제 정의] ➡️ [핵심 아키텍처 및 원리] ➡️ [실무 적용 코드/설정 딥다이브] ➡️ [성능 최적화 및 Best Practices] ➡️ [결론]** 의 논리적 흐름을 따르세요.
    - 현업에서 즉시 적용 가능한 수준의 구체적이고 실용적인 트러블슈팅, 코드 예시, 설정 파일(yaml, conf 등)을 풍부하게 담아주세요.

    반드시 아래의 **'블로그 작성 가이드라인'**을 완벽하게 준수해야 합니다. 마크다운 코드 외에 다른 부가적인 설명이나 인사말은 절대 출력하지 마세요.

    ## [블로그 작성 가이드라인]

    ### 1. Front Matter (YAML)
    반드시 아래 형식을 지켜서 작성하세요. `title`, `slug`, `meta`의 값은 반드시 큰따옴표(")로 감싸야 합니다.
    **[중요 주의사항]** `title`과 `meta` 내용 내부에는 절대 큰따옴표(")를 사용하지 마세요. 강조가 필요하다면 작은따옴표(')를 사용하세요. (YAML 파싱 에러 방지)
    ---
    layout: post
    title: "여기에 매력적이고 검색 가능한 한글 제목 작성"
    slug: "english-title-for-url-slug"
    date: {current_time}
    categories: [카테고리명] # 예: [Backend], [DevOps], [Frontend] 등 1~2개
    tags: [태그1, 태그2, 태그3]
    meta: "구글 검색 결과에 노출될 SEO 최적화 요약문. 핵심 키워드를 포함하여 150자 내외로 작성. (내부에 큰따옴표 절대 금지)"
    ---

    ### 2. 도입부 및 미리보기 자르기 (한국어 전용)
    - Front Matter 바로 아래에는 독자의 흥미를 끄는 **한국어 도입부(2~3문단)**를 작성하세요. 핵심 키워드를 자연스럽게 포함하세요.
    - 도입부 작성이 끝나면 반드시 빈 줄을 하나 두고 `<!--more-->` 태그를 삽입하세요. (이 태그를 기준으로 목록에서 미리보기가 잘립니다.)

    ### 3. 메인 썸네일 이미지 자리 표시자
    - `<!--more-->` 태그 바로 아래에 정확히 `[HERO_IMAGE]` 라고만 작성하세요. (이 부분은 파이썬 스크립트가 실제 생성된 이미지로 자동 치환합니다.)
    - 그 아래에 빈 줄을 하나 두고 `-----` (하이픈 5개)를 넣어 구분선을 만드세요.

    ### 4. 본문 (Korean Main Content)
    - 본문은 '~습니다', '~합니다' 체의 정중하고 전문적인 문체를 사용하세요.
    - **가독성 및 SEO:** 검색 엔진이 이해하기 쉽도록 `##` (H2 태그)와 `###` (H3 태그)를 의미에 맞게 계층적으로 사용하세요.
    - **강조:** 중요한 키워드나 개념은 `**굵게(Bold)**` 처리하여 독자의 시선이 머물게 하세요.
    - **인라인 코드:** 명령어, 변수명 등은 백틱(`)으로 감싸세요.
    - **코드 블록:** 프로그래밍 언어 태그를 포함한 마크다운 코드 블록을 작성하세요.
    - **링크 포맷:** 모든 외부 링크는 반드시 `[표시할 텍스트](URL "툴팁 텍스트"){{:target="_blank"}}` 형식을 따르세요.

    ### 5. 참고문헌
    - 글의 맨 마지막에는 `### 참고문헌` 소제목을 넣고, 본문에서 언급된 공식 문서, 신뢰할 수 있는 외부 레퍼런스 등을 리스트 형태로 정리하세요. (외부 링크는 SEO에 긍정적인 영향을 줍니다)
    """

    max_retries = 3

    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 AI 글쓰기 API 요청 중... (시도 {attempt}/{max_retries})")
            
            # 1. 텍스트 생성 (가장 안정적이고 똑똑한 Gemini 2.5 Pro 사용)
            response = client.models.generate_content(
                model="gemini-2.5-pro", 
                contents=prompt
            )
            
            content = response.text.strip()
            
            # 불필요한 마크다운 블록 기호 제거
            if content.startswith("```markdown"):
                content = content[11:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # Front Matter에서 title과 slug를 각각 추출
            title_match = re.search(r'title:\s*"([^"]+)"', content)
            slug_match = re.search(r'slug:\s*"([^"]+)"', content)
            
            if title_match:
                raw_title = title_match.group(1)
            else:
                title_match_fallback = re.search(r"title:\s*'([^']+)'", content)
                raw_title = title_match_fallback.group(1) if title_match_fallback else "AI 생성 기술 포스트"

            # slug 추출 및 파일명에 사용할 수 있도록 정제
            if slug_match:
                raw_slug = slug_match.group(1)
                slug = re.sub(r'[^a-zA-Z0-9]+', '-', raw_slug.lower()).strip('-')
            else:
                slug = "ai-generated-tech-post"

            # 2. 썸네일 이미지 자동 생성 (Imagen 4.0 모델 사용)
            image_md = ""
            try:
                print(f"🎨 '{raw_title}' 주제로 썸네일 이미지 생성 중...")
                # AI에게 이미지 생성을 요청할 프롬프트 (영어 slug를 활용하여 더 정확한 이미지 유도)
                clean_english_topic = slug.replace('-', ' ')
                image_prompt = f"A modern, high quality conceptual illustration for an IT tech blog post about: '{clean_english_topic}'. Clean vector art style, abstract representation of server, code, or cloud computing. Dark background."
                
                # 이미지 생성 API 호출
                image_result = client.models.generate_images(
                    model='imagen-4.0-generate-001',
                    prompt=image_prompt,
                    config={"number_of_images": 1, "aspect_ratio": "16:9"}
                )
                image_bytes = image_result.generated_images[0].image.image_bytes
                
                # 이미지를 저장할 uploads 하위 폴더 생성 (예: uploads/my-django-post/)
                upload_dir = f"uploads/{slug}"
                os.makedirs(upload_dir, exist_ok=True)
                image_path = f"{upload_dir}/thumbnail.jpg"
                
                # 이미지 파일 저장
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                
                print(f"✅ 썸네일 이미지 저장 완료: {image_path}")
                
                # 본문에 치환할 마크다운 이미지 태그 조립 (SEO를 위한 alt 및 title 속성 추가)
                image_md = f"![{raw_title}](/{image_path} \"{raw_title}\")\n\n<p style=\"text-align:center;opacity:0.8;\">\n    <small>&copy; AI Generated by Imagen 4.0</small>\n</p>"
                
            except Exception as img_e:
                print(f"⚠️ 썸네일 이미지 생성 실패 (텍스트 본문만 작성됩니다): {img_e}")
            
            # 본문에 있는 [HERO_IMAGE] 위치를 실제 이미지 태그로 치환
            if "[HERO_IMAGE]" in content:
                content = content.replace("[HERO_IMAGE]", image_md)
            else:
                # 만약 AI가 [HERO_IMAGE]를 빼먹었다면 <!--more--> 아래에 강제로 삽입
                content = content.replace("<!--more-->", f"<!--more-->\n\n{image_md}\n\n-----")

            # 3. 연도별 폴더 생성 및 파일 저장 (_posts/2026/...)
            post_dir = f"_posts/{year}"
            os.makedirs(post_dir, exist_ok=True)
            filename = f"{post_dir}/{today_date}-{slug}.md"

            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"✅ 포스트 저장 완료: {filename}")
            break  # 모든 과정 성공 시 반복문 탈출

        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "UNAVAILABLE" in error_msg:
                print(f"⚠️ 503 서버 혼잡 에러 발생. 15초 후 재시도합니다...")
                if attempt < max_retries:
                    time.sleep(15)
                else:
                    print("❌ 최대 재시도 횟수를 초과하여 스크립트를 종료합니다.")
            else:
                print(f"❌ Error during generation: {e}")
                break

if __name__ == "__main__":
    generate_blog_post()
