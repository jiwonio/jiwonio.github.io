import os
import re
import time
from google import genai
from datetime import datetime, timezone, timedelta

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_blog_post():
    # KST (한국 표준시) 설정: UTC + 9시간
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst)
    year = today.strftime("%Y")
    today_date = today.strftime("%Y-%m-%d")
    current_time = today.strftime("%Y-%m-%d %H:%M:%S +0900")
    
    # 100% 한국어로 작성하고, <!--more-->로 자르며, [HERO_IMAGE] 위치를 지정하는 완벽한 프롬프트
    prompt = f"""
    당신은 숙련된 서버 엔지니어이자 풀스택 웹 개발자입니다. 
    최신 웹 개발 트렌드, 서버 인프라 구축, 클라우드(AWS), Python/Django, Node.js, PHP 활용, 개발 환경 설정 등 전문적인 IT 기술 주제 중 하나를 스스로 무작위로 선정하여 완성된 블로그 포스트를 작성해 주세요.

    반드시 아래의 **'블로그 작성 가이드라인'**을 완벽하게 준수해야 합니다. 마크다운 코드 외에 다른 부가적인 설명이나 인사말은 절대 출력하지 마세요.

    ## [블로그 작성 가이드라인]

    ### 1. Front Matter (YAML)
    반드시 아래 형식을 지켜서 작성하세요. `title`과 `meta`의 값은 반드시 큰따옴표(")로 감싸야 합니다.
    **[중요 주의사항]** `title`과 `meta` 내용 내부에는 절대 큰따옴표(")를 사용하지 마세요. 강조가 필요하다면 작은따옴표(')를 사용하세요. (YAML 파싱 에러 방지)
    ---
    layout: post
    title: "여기에 영어 제목 작성 (Title Case 형식)"
    date: {current_time}
    meta: "포스트의 핵심 내용을 요약한 한글 2~3문장. (내부에 큰따옴표 절대 금지)"
    tags:
      - tech
      - 태그1
    ---

    ### 2. 도입부 및 미리보기 자르기 (한국어 전용)
    - Front Matter 바로 아래에는 독자의 흥미를 끄는 **한국어 도입부(2~3문단)**를 작성하세요. (영문 도입부는 작성하지 마세요)
    - 도입부 작성이 끝나면 반드시 빈 줄을 하나 두고 `<!--more-->` 태그를 삽입하세요. (이 태그를 기준으로 목록에서 미리보기가 잘립니다.)

    ### 3. 메인 썸네일 이미지 자리 표시자
    - `<!--more-->` 태그 바로 아래에 정확히 `[HERO_IMAGE]` 라고만 작성하세요. (이 부분은 파이썬 스크립트가 실제 생성된 이미지로 자동 치환합니다.)
    - 그 아래에 빈 줄을 하나 두고 `-----` (하이픈 5개)를 넣어 구분선을 만드세요.

    ### 4. 본문 (Korean Main Content)
    - 본문은 '~습니다', '~합니다' 체의 정중하고 전문적인 문체를 사용하세요.
    - **강조:** 중요한 키워드나 개념은 `**굵게(Bold)**` 처리하세요.
    - **인라인 코드:** 명령어, 변수명 등은 백틱(`)으로 감싸세요.
    - **코드 블록:** 프로그래밍 언어 태그를 포함한 마크다운 코드 블록을 작성하세요.
    - **링크 포맷:** 모든 외부 링크는 반드시 `[표시할 텍스트](URL "툴팁 텍스트"){{:target="_blank"}}` 형식을 따르세요.
    - **소제목:** `### 소제목` 형식을 사용하세요.

    ### 5. 참고문헌
    - 글의 맨 마지막에는 `### 참고문헌` 소제목을 넣고, 본문에서 언급된 도구, 공식 문서, 참고 사이트 등을 리스트 형태로 정리하세요. 
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

            # Front Matter에서 title을 추출하여 슬러그 생성 (예: "My Django Post" -> my-django-post)
            # 큰따옴표(")를 사용하는 것으로 정규식 변경
            title_match = re.search(r'title:\s*"([^"]+)"', content)
            if title_match:
                raw_title = title_match.group(1)
                slug = re.sub(r'[^a-zA-Z0-9]+', '-', raw_title.lower()).strip('-')
            else:
                # 홑따옴표로 작성했을 경우에 대한 대비책
                title_match_fallback = re.search(r"title:\s*'([^']+)'", content)
                if title_match_fallback:
                    raw_title = title_match_fallback.group(1)
                    slug = re.sub(r'[^a-zA-Z0-9]+', '-', raw_title.lower()).strip('-')
                else:
                    raw_title = "AI Generated Tech Post"
                    slug = "ai-generated-tech-post"

            # 2. 썸네일 이미지 자동 생성 (Imagen 4.0 모델 사용)
            image_md = ""
            try:
                print(f"🎨 '{raw_title}' 주제로 썸네일 이미지 생성 중...")
                # AI에게 이미지 생성을 요청할 프롬프트 (영어 권장)
                image_prompt = f"A modern, high quality conceptual illustration for an IT tech blog post titled: '{raw_title}'. Clean vector art style, abstract representation of server, code, or cloud computing. Dark background."
                
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
                
                # 본문에 치환할 마크다운 이미지 태그 조립
                image_md = f"![{raw_title}](/{image_path})\n\n<p style=\"text-align:center;opacity:0.8;\">\n    <small>&copy; AI Generated by Imagen 4.0</small>\n</p>"
                
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
