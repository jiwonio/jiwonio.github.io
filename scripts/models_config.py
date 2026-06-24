"""LLM provider·모델 설정 (생성·번역·이미지 스크립트 공통)."""

PROVIDER_API_KEY_ENV = {
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "xai": "XAI_API_KEY",
}

PROVIDER_MODELS = {
    "gemini": {
        "text": "gemini-2.5-pro",
        "translation": (
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.5-flash-lite",
        ),
        "image": "gemini-3.1-flash-image",
    },
    "anthropic": {
        "text": "claude-sonnet-4-20250514",
        "translation": ("claude-3-5-haiku-20241022",),
        "image": None,
    },
    "openai": {
        "text": "gpt-4.1",
        "translation": ("gpt-4.1-mini",),
        "image": None,
    },
    "xai": {
        "text": "grok-4",
        "translation": ("grok-4-fast",),
        "image": "grok-imagine-image-quality",
    },
}

# post_type별 1차 provider + 폴백 순서
POST_TYPE_TEXT_PROVIDERS = {
    "deep-dive": ("gemini", "anthropic", "openai", "xai"),
    "ai-news": ("anthropic", "openai", "xai", "gemini"),
}

TRANSLATION_PROVIDER_CHAIN = ("gemini", "anthropic", "openai", "xai")
IMAGE_PROVIDER_CHAIN = ("gemini", "xai")

# 하위 호환 (기존 import)
TEXT_MODEL = PROVIDER_MODELS["gemini"]["text"]
IMAGE_MODEL = PROVIDER_MODELS["gemini"]["image"]
TRANSLATION_MODELS = PROVIDER_MODELS["gemini"]["translation"]