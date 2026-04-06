import os
import re
from google import genai
from datetime import datetime

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_blog_post():
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    # AI가 스스로 주제를 선정하고 완벽한 형식의 마크다운을 작성하도록 지시하는 마스터 프롬프트
    prompt = """
    당신은 숙련된 서버 엔지니어이자 풀스택 웹 개발자입니다. 
    최신 웹 개발 트렌드, 서버 인프라 구축, 클라우드(AWS), Python/Django, Node.js, PHP 활용, 혹은 개발 환경 설정(WSL2, Docker) 등 전문적인 IT 기술 주제 중 하나를 스스로 무작위로 선정하여 완성된 블로그 포스트를 작성해 주세요.

    반드시 아래의 **'블로그 작성 가이드라인'**을 완벽하게 준수해야 합니다. 마크다운 코드 외에 다른 부가적인 설명이나 인사말은 절대 출력하지 마세요.

    ## [블로그 작성 가이드라인]

    ### 1. Front Matter (YAML)
    반드시 아래 형식을 지켜서 작성하세요. 값들은 홑따옴표(')로 감싸야 합니다.
    ---
    layout: post
    title: '여기에 영어 제목 작성 (Title Case 형식)'
    meta: '포스트의 핵심 내용을 요약한 영문 2~3문장.'
    tags:
      - tech
      - 태그1
      - 태그2
    ---

    ### 2. 도입부 (English Intro)
    - Front Matter 바로 아래에는 `meta` 내용과 유사한 길이의 **영문 도입부**를 작성하세요.
    - 영문 도입부의 마지막 문장은 반드시 다음 문구로 끝내세요: "This post was generated with the assistance of **Gemini 3.0**."
    - 영문 도입부가 끝나면 반드시 빈 줄을 하나 두고 `` 태그를 삽입하세요.

    ### 3. Medium 동시 발행 문구
    - `` 태그 아래에 다음 HTML 코드를 삽입하세요.
    <small style="color:lightgray;text-decoration:line-through;font-style: italic;">[Medium](https://medium.com/@jiwonio "medium.com/@jiwonio"){:target="_blank"} 에도 발행하고 있어요.</small>

    ### 4. 메인 썸네일 이미지 및 출처 (Hero Image)
    - 포스트 주제와 어울리는 썸네일 이미지 마크다운과 캡션을 아래 HTML 및 마크다운 혼합 형식으로 작성하세요. 이미지 파일명은 소문자와 하이픈(-)으로 구성하세요.
    ![이미지 대체 텍스트](/uploads/폴더명/image-name.jpg)

    <p style="text-align:center;opacity:0.8;">
        <small>&copy; <a href="https://unsplash.com/" title="Unsplash" target="_blank">Unsplash</a></small>
        <small>&copy; <a href="https://unsplash.com/" title="Content copyright holder" target="_blank">Creator Name</a></small>
    </p>

    -----

    ### 5. 본문 (Korean Main Content)
    - 본문은 **한국어**로 작성하며, '~습니다', '~합니다' 체의 정중하고 전문적인 문체를 사용하세요.
    - **강조:** 중요한 키워드나 개념은 `**굵게(Bold)**` 처리하세요.
    - **인라인 코드:** 명령어, 변수명 등은 백틱(`)으로 감싸세요.
    - **코드 블록:** 프로그래밍 언어 태그(python, javascript, bash 등)를 포함한 마크다운 코드 블록을 작성하세요.
    - **링크 포맷:** 모든 외부 링크는 반드시 `[표시할 텍스트](URL "툴팁 텍스트"){:target="_blank"}` 형식을 따르세요.
    - **소제목:** `### 소제목` 형식을 사용하세요.

    ### 6. 본문 내 이미지 레이아웃 (HTML)
    - 본문 내용 중 여러 이미지를 나란히 배치하는 상황을 가정하여, 아래 HTML 구조를 최소 1회 이상 사용하세요.
    <div style="display:flex;gap:0.5rem;flex-direction:row;margin:1rem auto 0;max-width:100%;">
        <div>
            <img src="/uploads/폴더명/sub-image1.png" alt="설명" />
        </div>
        <div>
            <img src="/uploads/폴더명/sub-image2.png" alt="설명" />
        </div>
    </div>
    <p style="text-align:center;color:gray;"><small>설명 캡션</small></p>

    ### 7. 참고문헌 (References)
    - 글의 맨 마지막에는 `### 참고문헌` 소제목을 넣고, 리스트 형태로 링크를 정리하세요. (링크 포맷은 본문과 동일하게 `{:target="_blank"}` 적용)
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro", 
            contents=prompt
        )
        
        # 모델 응답 텍스트에서 불필요한 마크다운 코드 블록 마커(```markdown 등) 제거
        content = response.text.strip()
        if content.startswith("```markdown"):
            content = content[11:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        # Front Matter에서 title을 추출하여 파일명으로 활용 (예: My Python Project -> my-python-project)
        title_match = re.search(r"title:\s*'([^']+)'", content)
        if title_match:
            raw_title = title_match.group(1)
            # 영어 알파벳과 숫자만 남기고 나머지는 하이픈으로 치환
            slug = re.sub(r'[^a-zA-Z0-9]+', '-', raw_title.lower()).strip('-')
            filename = f"_posts/{today_date}-{slug}.md"
        else:
            filename = f"_posts/{today_date}-ai-generated-post.md"

        os.makedirs("_posts", exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"✅ Post generated successfully: {filename}")

    except Exception as e:
        print(f"❌ Error during generation: {e}")
        print("\n--- 🔍 사용 가능한 전체 모델 목록 ---")
        for m in client.models.list():
            print(f" - {m.name}")

if __name__ == "__main__":
    generate_blog_post()
