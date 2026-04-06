import os
from google import genai
from datetime import datetime

# API 설정
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_blog_post():
    prompt = """
    당신은 전문 기술 블로거입니다. 최신 IT 트렌드나 프로그래밍 주제 중 하나를 선정해 블로그 글을 작성하세요.
    반드시 아래의 Jekyll 마크다운 형식을 지켜주세요.
    ---
    layout: post
    title: "[여기에 제목 작성]"
    date: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S +0900") + """
    categories: tech
    tags: [AI, Automation, Gemini]
    ---
    [여기에 마크다운 형식으로 본문 작성]
    """

    try:
        # 일단 가장 범용적인 모델명 중 하나로 시도해 봅니다.
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        
        content = response.text

        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"_posts/{today}-ai-generated-post.md"

        os.makedirs("_posts", exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"✅ Post generated successfully: {filename}")

    except Exception as e:
        print(f"❌ Error during generation: {e}")
        print("\n--- 🔍 사용 가능한 전체 모델 목록 ---")
        # AttributeError를 방지하기 위해 조건 검사 없이 무조건 이름만 출력합니다.
        for m in client.models.list():
            print(f" - {m.name}")

if __name__ == "__main__":
    generate_blog_post()
