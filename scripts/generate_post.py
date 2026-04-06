import os
import google.generativeai as genai
from datetime import datetime

# API 설정
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-pro')

def generate_blog_post():
    # 프롬프트 설정 (개발자 취향에 맞게 수정 가능)
    prompt = """
    당신은 전문 기술 블로거입니다. 최신 IT 트렌드나 프로그래밍 주제 중 하나를 선정해 블로그 글을 작성하세요.
    반드시 아래의 Jekyll 마크다운 형식을 지켜주세요.
    ---
    layout: post
    title: "[제목]"
    date: YYYY-MM-DD HH:MM:SS +0900
    categories: tech
    tags: [tag1, tag2]
    ---
    [여기에 마크다운 형식으로 본문 작성]
    """

    response = model.generate_content(prompt)
    content = response.text

    # 파일명 생성 (YYYY-MM-DD-title.md)
    today = datetime.now().strftime("%Y-%m-%d")
    # 간단한 파일명 생성을 위해 제목 대신 날짜와 랜덤한 숫자를 사용하거나 AI에게 제목을 요청할 수 있습니다.
    filename = f"_posts/{today}-ai-generated-post.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Post generated: {filename}")

if __name__ == "__main__":
    generate_blog_post()
