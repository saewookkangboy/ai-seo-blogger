"""
Gemini 클라이언트 — Generative Language REST 래퍼.

gaeoanalysis `lib/llm/gemini.ts` 기능을 FastAPI에 이식.
기존 `google-generativeai` 의존과 충돌하지 않도록 REST(httpx)로 구현한다.
지원: 텍스트 생성, JSON 구조화 출력, Google Search 그라운딩, 임베딩.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from app.services.llm.models import EMBEDDING_MODEL

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


def _api_key() -> Optional[str]:
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if key and key.strip():
        return key.strip()
    try:
        from app.config import settings

        for candidate in (settings.gemini_api_key, settings.google_api_key):
            if candidate and str(candidate).strip():
                return str(candidate).strip()
    except Exception:
        pass
    return None


def is_gemini_configured() -> bool:
    key = _api_key()
    return bool(key and key.strip())


@dataclass
class GenerateOptions:
    model: str
    prompt: str
    system_instruction: Optional[str] = None
    temperature: Optional[float] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    max_output_tokens: Optional[int] = None
    thinking_budget: Optional[int] = None
    google_search: bool = False


@dataclass
class GenerateResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    grounding_urls: List[str] = field(default_factory=list)


def _build_generation_config(opts: GenerateOptions) -> Dict[str, Any]:
    config: Dict[str, Any] = {}
    if opts.temperature is not None:
        config["temperature"] = opts.temperature
    if opts.top_k is not None:
        config["topK"] = opts.top_k
    if opts.top_p is not None:
        config["topP"] = opts.top_p
    if opts.max_output_tokens is not None:
        config["maxOutputTokens"] = opts.max_output_tokens
    if opts.thinking_budget is not None:
        config["thinkingConfig"] = {"thinkingBudget": opts.thinking_budget}
    return config


def _extract_grounding_urls(payload: Dict[str, Any]) -> List[str]:
    urls: List[str] = []
    try:
        for candidate in payload.get("candidates") or []:
            meta = candidate.get("groundingMetadata") or {}
            for chunk in meta.get("groundingChunks") or []:
                uri = (chunk.get("web") or {}).get("uri")
                if uri and uri not in urls:
                    urls.append(uri)
    except Exception:
        pass
    return urls


def _extract_text(payload: Dict[str, Any]) -> str:
    parts: List[str] = []
    for candidate in payload.get("candidates") or []:
        content = candidate.get("content") or {}
        for part in content.get("parts") or []:
            text = part.get("text")
            if text:
                parts.append(text)
    return "".join(parts)


async def generate_text(opts: GenerateOptions) -> GenerateResult:
    api_key = _api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")

    body: Dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": opts.prompt}]}],
    }
    gen_config = _build_generation_config(opts)
    if gen_config:
        body["generationConfig"] = gen_config
    if opts.system_instruction:
        body["systemInstruction"] = {"parts": [{"text": opts.system_instruction}]}
    if opts.google_search:
        body["tools"] = [{"google_search": {}}]

    url = f"{BASE_URL}/models/{opts.model}:generateContent"
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, params={"key": api_key}, json=body)
        response.raise_for_status()
        data = response.json()

    usage = data.get("usageMetadata") or {}
    return GenerateResult(
        text=_extract_text(data),
        input_tokens=int(usage.get("promptTokenCount") or 0),
        output_tokens=int(usage.get("candidatesTokenCount") or 0),
        grounding_urls=_extract_grounding_urls(data),
    )


async def generate_json(
    *,
    model: str,
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
    response_schema: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """구조화 JSON 출력. responseMimeType=application/json (+ optional schema)."""
    api_key = _api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")

    generation_config: Dict[str, Any] = {
        "responseMimeType": "application/json",
    }
    if temperature is not None:
        generation_config["temperature"] = temperature
    if max_output_tokens is not None:
        generation_config["maxOutputTokens"] = max_output_tokens
    if response_schema:
        generation_config["responseSchema"] = response_schema

    body: Dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }
    if system_instruction:
        body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    url = f"{BASE_URL}/models/{model}:generateContent"
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, params={"key": api_key}, json=body)
        response.raise_for_status()
        data = response.json()

    raw = _extract_text(data)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"구조화 응답 JSON 파싱 실패: {exc}") from exc

    usage = data.get("usageMetadata") or {}
    return {
        "data": parsed,
        "raw": raw,
        "input_tokens": int(usage.get("promptTokenCount") or 0),
        "output_tokens": int(usage.get("candidatesTokenCount") or 0),
    }


async def embed_texts(texts: List[str], model: str = EMBEDDING_MODEL) -> List[List[float]]:
    if not texts:
        return []
    api_key = _api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")

    vectors: List[List[float]] = []
    url = f"{BASE_URL}/models/{model}:embedContent"
    async with httpx.AsyncClient(timeout=60.0) as client:
        for text in texts:
            body = {
                "model": f"models/{model}",
                "content": {"parts": [{"text": text}]},
            }
            response = await client.post(url, params={"key": api_key}, json=body)
            response.raise_for_status()
            data = response.json()
            values = (data.get("embedding") or {}).get("values") or []
            vectors.append([float(v) for v in values])
    return vectors
