"""Multi-provider LLM client (Gemini, Anthropic, OpenAI, xAI)."""

from __future__ import annotations

import base64
import os
import time
from collections.abc import Callable
from typing import Literal, NamedTuple, TypeVar
from urllib.request import urlopen

from models_config import (
    IMAGE_PROVIDER_CHAIN,
    POST_TYPE_TEXT_PROVIDERS,
    PROVIDER_API_KEY_ENV,
    PROVIDER_MODELS,
    TRANSLATION_PROVIDER_CHAIN,
)

Provider = Literal["gemini", "anthropic", "openai", "xai"]
XAI_BASE_URL = "https://api.x.ai/v1"
MAX_OUTPUT_TOKENS = 16384
HTTP_TIMEOUT = 120
MAX_IMAGE_BYTES = 10_000_000
MAX_TRANSPORT_RETRIES = 3

T = TypeVar("T")


class TextGenerationResult(NamedTuple):
    text: str
    input_chars: int
    output_chars: int


def get_api_key(provider: str) -> str:
    env_name = PROVIDER_API_KEY_ENV.get(provider, "")
    return os.environ.get(env_name, "").strip()


def is_provider_available(provider: str) -> bool:
    return provider in PROVIDER_MODELS and bool(get_api_key(provider))


def list_available_providers() -> list[str]:
    return [provider for provider in PROVIDER_MODELS if is_provider_available(provider)]


def filter_available_providers(providers: tuple[str, ...] | list[str]) -> list[str]:
    return [provider for provider in providers if is_provider_available(provider)]


def get_text_model(provider: str) -> str:
    return PROVIDER_MODELS[provider]["text"]


def get_translation_models(provider: str) -> tuple[str, ...]:
    models = PROVIDER_MODELS[provider]["translation"]
    if isinstance(models, str):
        return (models,)
    return tuple(models)


def get_image_model(provider: str) -> str | None:
    return PROVIDER_MODELS[provider].get("image")


def resolve_text_providers(post_type: str, override: str | None = None) -> list[str]:
    if override and override.strip():
        primary = override.strip().lower()
        if primary not in PROVIDER_MODELS:
            raise ValueError(f"Unknown provider: {override}")
        chain = [primary]
        for provider in POST_TYPE_TEXT_PROVIDERS.get(post_type, ("gemini",)):
            if provider not in chain:
                chain.append(provider)
    else:
        env_override = os.environ.get("LLM_TEXT_PROVIDER", "").strip().lower()
        if env_override:
            return resolve_text_providers(post_type, env_override)
        chain = list(POST_TYPE_TEXT_PROVIDERS.get(post_type, ("gemini", "anthropic", "openai", "xai")))

    available = filter_available_providers(chain)
    if available:
        return available
    return list_available_providers()


def resolve_translation_providers(override: str | None = None) -> list[str]:
    if override and override.strip():
        primary = override.strip().lower()
        if primary not in PROVIDER_MODELS:
            raise ValueError(f"Unknown provider: {override}")
        chain = [primary]
        for provider in TRANSLATION_PROVIDER_CHAIN:
            if provider not in chain:
                chain.append(provider)
    else:
        env_override = os.environ.get("LLM_TRANSLATION_PROVIDER", "").strip().lower()
        if env_override:
            return resolve_translation_providers(env_override)
        chain = list(TRANSLATION_PROVIDER_CHAIN)

    available = filter_available_providers(chain)
    if available:
        return available
    return list_available_providers()


def resolve_image_providers() -> list[str]:
    available = filter_available_providers(IMAGE_PROVIDER_CHAIN)
    if available:
        return available
    if is_provider_available("gemini"):
        return ["gemini"]
    return []


def pick_provider_for_attempt(providers: list[str], attempt: int) -> str:
    if not providers:
        raise RuntimeError(
            "사용 가능한 LLM provider가 없습니다. "
            "GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, XAI_API_KEY 중 하나 이상을 설정하세요."
        )
    return providers[(attempt - 1) % len(providers)]


def pick_translation_target(providers: list[str], attempt: int) -> tuple[str, str]:
    provider = pick_provider_for_attempt(providers, attempt)
    models = get_translation_models(provider)
    model_round = (attempt - 1) // max(len(providers), 1)
    model = models[min(model_round, len(models) - 1)]
    return provider, model


def _is_retryable_error(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if status in {429, 500, 502, 503, 504, 529}:
        return True
    message = str(exc).lower()
    if "429" in message or "rate limit" in message or "too many requests" in message:
        return True
    return any(code in message for code in ("500", "502", "503", "504", "529", "unavailable"))


def with_transport_retry(func: Callable[[], T]) -> T:
    last_error: Exception | None = None
    for attempt in range(1, MAX_TRANSPORT_RETRIES + 1):
        try:
            return func()
        except Exception as exc:
            last_error = exc
            if not _is_retryable_error(exc) or attempt >= MAX_TRANSPORT_RETRIES:
                raise
            delay = 2**attempt
            time.sleep(delay)
    if last_error is not None:
        raise last_error
    raise RuntimeError("transport retry failed without an error")


def _read_url_with_size_cap(url: str, *, max_bytes: int = MAX_IMAGE_BYTES) -> bytes:
    with urlopen(url, timeout=HTTP_TIMEOUT) as remote:
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = remote.read(8192)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(f"Image exceeds {max_bytes} bytes")
            chunks.append(chunk)
        return b"".join(chunks)


def _generate_gemini_text(prompt: str, model: str, *, system_prompt: str | None = None) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=get_api_key("gemini"),
        http_options=types.HttpOptions(timeout=HTTP_TIMEOUT * 1000),
    )

    def _call() -> str:
        config = None
        if system_prompt:
            config = types.GenerateContentConfig(system_instruction=system_prompt)
        response = client.models.generate_content(model=model, contents=prompt, config=config)
        return response.text or ""

    return with_transport_retry(_call)


def _generate_anthropic_text(prompt: str, model: str, *, system_prompt: str | None = None) -> str:
    from anthropic import Anthropic

    client = Anthropic(api_key=get_api_key("anthropic"), timeout=HTTP_TIMEOUT)

    def _call() -> str:
        kwargs: dict = {
            "model": model,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        message = client.messages.create(**kwargs)
        parts = [block.text for block in message.content if hasattr(block, "text")]
        return "\n".join(parts).strip()

    return with_transport_retry(_call)


def _generate_openai_compatible_text(
    prompt: str, model: str, *, provider: str, system_prompt: str | None = None
) -> str:
    from openai import OpenAI

    kwargs = {"api_key": get_api_key(provider), "timeout": HTTP_TIMEOUT}
    if provider == "xai":
        kwargs["base_url"] = XAI_BASE_URL
    client = OpenAI(**kwargs)

    def _call() -> str:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model=model,
            max_tokens=MAX_OUTPUT_TOKENS,
            messages=messages,
        )
        return (response.choices[0].message.content or "").strip()

    return with_transport_retry(_call)


def generate_text(
    *,
    prompt: str,
    provider: str,
    model: str | None = None,
    system_prompt: str | None = None,
) -> TextGenerationResult:
    if not is_provider_available(provider):
        raise RuntimeError(f"{provider} API key가 설정되지 않았습니다.")

    model = model or get_text_model(provider)
    input_chars = len(prompt) + (len(system_prompt) if system_prompt else 0)
    if provider == "gemini":
        text = _generate_gemini_text(prompt, model, system_prompt=system_prompt)
    elif provider == "anthropic":
        text = _generate_anthropic_text(prompt, model, system_prompt=system_prompt)
    elif provider in {"openai", "xai"}:
        text = _generate_openai_compatible_text(
            prompt, model, provider=provider, system_prompt=system_prompt
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    return TextGenerationResult(text, input_chars, len(text))


def _generate_gemini_image(prompt: str, model: str) -> bytes:
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=get_api_key("gemini"),
        http_options=types.HttpOptions(timeout=HTTP_TIMEOUT * 1000),
    )

    def _call() -> bytes:
        response = client.models.generate_content(
            model=model,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="16:9"),
            ),
        )
        for part in response.parts:
            if part.inline_data is not None:
                return part.inline_data.data
        raise ValueError("Gemini 이미지 응답이 없습니다.")

    return with_transport_retry(_call)


def _generate_xai_image(prompt: str, model: str) -> bytes:
    from openai import OpenAI

    client = OpenAI(api_key=get_api_key("xai"), base_url=XAI_BASE_URL, timeout=HTTP_TIMEOUT)

    def _call() -> bytes:
        response = client.images.generate(
            model=model,
            prompt=prompt,
            response_format="b64_json",
            extra_body={"aspect_ratio": "16:9"},
        )
        item = response.data[0]
        if getattr(item, "b64_json", None):
            data = base64.b64decode(item.b64_json)
            if len(data) > MAX_IMAGE_BYTES:
                raise ValueError(f"Image exceeds {MAX_IMAGE_BYTES} bytes")
            return data
        if getattr(item, "url", None):
            return _read_url_with_size_cap(item.url)
        raise ValueError("xAI 이미지 응답이 없습니다.")

    return with_transport_retry(_call)


def generate_image(*, prompt: str, provider: str, model: str | None = None) -> bytes:
    if not is_provider_available(provider):
        raise RuntimeError(f"{provider} API key가 설정되지 않았습니다.")

    model = model or get_image_model(provider)
    if not model:
        raise ValueError(f"{provider}는 이미지 생성을 지원하지 않습니다.")

    if provider == "gemini":
        return _generate_gemini_image(prompt, model)
    if provider == "xai":
        return _generate_xai_image(prompt, model)
    raise ValueError(f"Unsupported image provider: {provider}")


def generate_image_with_fallback(prompt: str) -> tuple[bytes, str, str]:
    last_error: Exception | None = None
    for provider in resolve_image_providers():
        model = get_image_model(provider)
        if not model:
            continue
        try:
            return generate_image(prompt=prompt, provider=provider, model=model), provider, model
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"이미지 생성에 실패했습니다: {last_error}")