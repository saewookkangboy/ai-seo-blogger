"""
멀티 프로바이더 LLM 추상화 (gaeoanalysis `lib/llm/provider.ts` 포트).

기본 경로는 Gemini. 다른 프로바이더는 API 키가 있을 때만 활성화된다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Protocol

import httpx

from app.services.llm.gemini import GenerateOptions, generate_text, is_gemini_configured
from app.services.llm.models import LLMTask, model_for_task

ProviderName = Literal["gemini", "openai", "anthropic", "perplexity", "xai"]


@dataclass
class LLMGenerateOptions:
    prompt: str
    system_instruction: Optional[str] = None
    temperature: Optional[float] = None
    max_output_tokens: Optional[int] = None
    task: LLMTask = "chat"
    google_search: bool = False


@dataclass
class LLMGenerateResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    provider: ProviderName = "gemini"
    grounding_urls: List[str] = field(default_factory=list)


class ProviderConfigError(Exception):
    def __init__(self, provider: ProviderName, detail: str) -> None:
        self.provider = provider
        super().__init__(f"{provider} 프로바이더 설정 오류: {detail}")


class LLMProvider(Protocol):
    name: ProviderName

    def is_configured(self) -> bool: ...

    async def generate_text(self, opts: LLMGenerateOptions) -> LLMGenerateResult: ...


class GeminiProvider:
    name: ProviderName = "gemini"

    def is_configured(self) -> bool:
        return is_gemini_configured()

    async def generate_text(self, opts: LLMGenerateOptions) -> LLMGenerateResult:
        result = await generate_text(
            GenerateOptions(
                model=model_for_task(opts.task),
                prompt=opts.prompt,
                system_instruction=opts.system_instruction,
                temperature=opts.temperature,
                max_output_tokens=opts.max_output_tokens,
                google_search=opts.google_search,
            )
        )
        return LLMGenerateResult(
            text=result.text,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            provider=self.name,
            grounding_urls=result.grounding_urls,
        )


class OpenAICompatibleProvider:
    def __init__(
        self,
        name: ProviderName,
        base_url: str,
        key_env: str,
        model_env: str,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.key_env = key_env
        self.model_env = model_env

    def is_configured(self) -> bool:
        if os.getenv(self.key_env):
            return True
        if self.key_env == "OPENAI_API_KEY":
            try:
                from app.config import settings

                return bool(settings.get_openai_api_key())
            except Exception:
                return False
        return False

    async def generate_text(self, opts: LLMGenerateOptions) -> LLMGenerateResult:
        api_key = os.getenv(self.key_env)
        model = os.getenv(self.model_env)
        if not api_key and self.key_env == "OPENAI_API_KEY":
            try:
                from app.config import settings

                api_key = settings.get_openai_api_key()
            except Exception:
                pass
        if not model and self.model_env == "OPENAI_MODEL":
            try:
                from app.config import settings

                model = settings.openai_model
            except Exception:
                pass
        if not api_key:
            raise ProviderConfigError(self.name, f"{self.key_env} 미설정")
        if not model:
            raise ProviderConfigError(self.name, f"{self.model_env} 미설정(모델 ID 필요)")

        messages = []
        if opts.system_instruction:
            messages.append({"role": "system", "content": opts.system_instruction})
        messages.append({"role": "user", "content": opts.prompt})

        body = {
            "model": model,
            "messages": messages,
            "temperature": opts.temperature,
            "max_tokens": opts.max_output_tokens,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            if response.status_code >= 400:
                raise ProviderConfigError(
                    self.name, f"HTTP {response.status_code}: {response.text}"
                )
            data = response.json()

        usage = data.get("usage") or {}
        choices = data.get("choices") or []
        text = ""
        if choices:
            text = ((choices[0].get("message") or {}).get("content")) or ""
        return LLMGenerateResult(
            text=text,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            provider=self.name,
            grounding_urls=[],
        )


class AnthropicProvider:
    name: ProviderName = "anthropic"

    def is_configured(self) -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY"))

    async def generate_text(self, opts: LLMGenerateOptions) -> LLMGenerateResult:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model = os.getenv("ANTHROPIC_MODEL")
        if not api_key:
            raise ProviderConfigError(self.name, "ANTHROPIC_API_KEY 미설정")
        if not model:
            raise ProviderConfigError(self.name, "ANTHROPIC_MODEL 미설정(모델 ID 필요)")

        body = {
            "model": model,
            "max_tokens": opts.max_output_tokens or 4096,
            "temperature": opts.temperature,
            "system": opts.system_instruction,
            "messages": [{"role": "user", "content": opts.prompt}],
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            if response.status_code >= 400:
                raise ProviderConfigError(
                    self.name, f"HTTP {response.status_code}: {response.text}"
                )
            data = response.json()

        text = "".join(
            block.get("text") or ""
            for block in (data.get("content") or [])
            if block.get("type") == "text"
        )
        usage = data.get("usage") or {}
        return LLMGenerateResult(
            text=text,
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            provider=self.name,
            grounding_urls=[],
        )


PROVIDERS = {
    "gemini": GeminiProvider(),
    "openai": OpenAICompatibleProvider(
        "openai", "https://api.openai.com/v1", "OPENAI_API_KEY", "OPENAI_MODEL"
    ),
    "anthropic": AnthropicProvider(),
    "perplexity": OpenAICompatibleProvider(
        "perplexity", "https://api.perplexity.ai", "PERPLEXITY_API_KEY", "PERPLEXITY_MODEL"
    ),
    "xai": OpenAICompatibleProvider(
        "xai", "https://api.x.ai/v1", "XAI_API_KEY", "XAI_MODEL"
    ),
}

PREFERENCE: List[ProviderName] = ["gemini", "openai", "anthropic", "perplexity", "xai"]


def get_provider(name: ProviderName):
    return PROVIDERS[name]


def get_default_provider():
    for name in PREFERENCE:
        if PROVIDERS[name].is_configured():
            return PROVIDERS[name]
    return PROVIDERS["gemini"]


def provider_status() -> Dict[str, bool]:
    return {name: provider.is_configured() for name, provider in PROVIDERS.items()}
