"""AI 소식 RSS 피드 설정 (Tier별 가중치)."""

from __future__ import annotations

# Tier 1: 공식·1차 출처 (가중치 3)
FEEDS_OFFICIAL = (
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml", "tier": 1},
    {"name": "Google AI", "url": "https://blog.google/technology/ai/rss/", "tier": 1},
    {"name": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml", "tier": 1},
    {"name": "GitHub Blog", "url": "https://github.blog/feed/", "tier": 1},
    {"name": "LangChain", "url": "https://www.langchain.com/blog/rss.xml", "tier": 1},
    {"name": "NVIDIA Developer", "url": "https://developer.nvidia.com/blog/feed", "tier": 1},
    {"name": "Ollama", "url": "https://ollama.com/blog/rss.xml", "tier": 1},
)

# Tier 2: 개발자·실무 (가중치 2)
FEEDS_DEVELOPER = (
    {"name": "Simon Willison", "url": "https://simonwillison.net/atom/everything/", "tier": 2},
    {"name": "Google Developers", "url": "https://developers.googleblog.com/atom.xml", "tier": 2},
    {"name": "AWS ML Blog", "url": "https://aws.amazon.com/blogs/machine-learning/feed/", "tier": 2},
    {"name": "Microsoft Dev Blog", "url": "https://devblogs.microsoft.com/feed/", "tier": 2},
    {"name": "JetBrains Blog", "url": "https://blog.jetbrains.com/feed/", "tier": 2},
)

# Tier 3: 뉴스 매체 (가중치 1)
FEEDS_NEWS = (
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "tier": 3},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "tier": 3},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "tier": 3},
)

FEED_TIERS = {
    "official": FEEDS_OFFICIAL,
    "developer": FEEDS_DEVELOPER,
    "news": FEEDS_NEWS,
}

ALL_FEEDS = FEEDS_OFFICIAL + FEEDS_DEVELOPER + FEEDS_NEWS

MAX_ITEMS_PER_FEED = 5
MAX_TOTAL_CANDIDATES = 30

# Tier별 수집 기간: 공식 블로그는 발행 주기가 길어 더 넓게 수집
RSS_DAYS_LOOKBACK_BY_TIER = {1: 14, 2: 10, 3: 7}
RSS_DAYS_LOOKBACK = 7  # 기본값 (하위 호환)

# 광범위 피드는 AI 키워드 필터 적용
AI_FILTER_FEEDS = frozenset({
    "GitHub Blog", "NVIDIA Developer", "Microsoft Dev Blog",
    "Google Developers", "AWS ML Blog", "JetBrains Blog",
})

# 개발자 관련 키워드 (가점)
DEVELOPER_KEYWORDS = (
    "api", "sdk", "model", "release", "open-source", "open source", "ide", "agent",
    "mcp", "rag", "fine-tuning", "fine tuning", "inference", "copilot", "cursor",
    "ollama", "llm", "gpt", "claude", "gemini", "github", "python", "typescript",
    "docker", "kubernetes", "embedding", "vector", "tool calling", "function calling",
    "code", "developer", "dev", "cli", "plugin", "extension", "vscode", "jetbrains",
    "hugging face", "langchain", "openai", "anthropic", "benchmark", "gpu",
)

# 투자·정책 위주 기사 감점 키워드
LOW_PRIORITY_KEYWORDS = (
    "funding", "raises", "billion", "million", "acquisition", "ipo", "lawsuit",
    "regulation", "congress", "senate", "ceo interview", "stock", "market cap",
)

TIER_WEIGHTS = {1: 3, 2: 2, 3: 1}

HN_ALGOLIA_URL = (
    "https://hn.algolia.com/api/v1/search_by_date"
    "?tags=story&query=AI+LLM+OpenAI+Claude+Gemini+Copilot&hitsPerPage=8"
)

RSS_FETCH_USER_AGENT = "jwjp-blog-ai-news-bot/1.0 (+https://blog.jiwon.io)"
RSS_FETCH_TIMEOUT = 15