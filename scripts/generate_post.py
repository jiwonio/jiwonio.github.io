import os
from google import genai
from datetime import datetime

# API 설정
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_blog_post():
    # 프롬프트 설정
    prompt = """
    당신은 전문 기술 블로거입니다. 최신 IT 트렌드나 프로그래밍 주제 중 하나를 선정해 블로그 글을 작성하세요.
    반드시 아래의 Jekyll 마크다운 형식을 지켜주세요.
    ---
    layout: post
    title: "[여기에 제목 작성]"
    date: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S +0900") + """
    categories: tech
    tags: [AI, Automation, Gemini3]
    ---
    [여기에 마크다운 형식으로 본문 작성]
    """

    # 모델 호출: gemini-3.0-flash로 업데이트
    response = client.models.generate_content(
        model="gemini-3-flash", # 2.0 대신 3버전 사용
        contents=prompt
    )
    
    content = response.text

    # 파일명 생성 및 저장
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"_posts/{today}-ai-generated-post.md"

    os.makedirs("_posts", exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ Post generated successfully using Gemini 3 Flash: {filename}")

if __name__ == "__main__":
    generate_blog_post()
