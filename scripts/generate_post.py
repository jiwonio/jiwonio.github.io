import os
from google import genai
from datetime import datetime

# API 설정 (새로운 Client 방식)
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
    tags: [AI, Automation]
    ---
    [여기에 마크다운 형식으로 본문 작성]
    """

    # 모델 호출 (모델명 앞에 'models/'를 붙이지 않아도 됩니다)
    response = client.models.generate_content(
        model="gemini-2.0-flash", # 혹은 "gemini-1.5-pro"
        contents=prompt
    )
    
    content = response.text

    # 파일명 생성 (YYYY-MM-DD-ai-post.md)
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"_posts/{today}-ai-generated-post.md"

    # 폴더가 없으면 생성 (안전장치)
    os.makedirs("_posts", exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ Post generated successfully: {filename}")

if __name__ == "__main__":
    generate_blog_post()
