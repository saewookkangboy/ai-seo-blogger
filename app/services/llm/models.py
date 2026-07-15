"""
LLM 모델 레지스트리 — 모델 ID 단일 소스.

gaeoanalysis `lib/llm/models.ts` 포트.
태스크별 모델은 여기서만 관리하며 환경 변수로 오버라이드할 수 있다.
"""

from __future__ import annotations

import os
from typing import Dict, Literal

LLMTask = Literal["chat", "suggestions", "revision", "report", "preview", "translate", "generate"]

# 2026-07 기준 Gemini 별칭 (gaeoanalysis와 동일). 환경에 따라 고정 버전으로 오버라이드.
GEMINI_MODELS = {
    "flash": "gemini-flash-latest",
    "flash_lite": "gemini-flash-lite-latest",
    "pro": "gemini-pro-latest",
    "embedding": "gemini-embedding-001",
}


def _env_model(key: str, fallback: str) -> str:
    value = os.getenv(key)
    return value.strip() if value and value.strip() else fallback


MODEL_FOR_TASK: Dict[str, str] = {
    "chat": _env_model("GEMINI_MODEL_CHAT", GEMINI_MODELS["flash"]),
    "suggestions": _env_model("GEMINI_MODEL_SUGGESTIONS", GEMINI_MODELS["flash_lite"]),
    "revision": _env_model("GEMINI_MODEL_REVISION", GEMINI_MODELS["flash"]),
    "report": _env_model("GEMINI_MODEL_REPORT", GEMINI_MODELS["flash"]),
    "preview": _env_model("GEMINI_MODEL_PREVIEW", GEMINI_MODELS["flash_lite"]),
    "translate": _env_model("GEMINI_MODEL_TRANSLATE", GEMINI_MODELS["flash"]),
    "generate": _env_model(
        "GEMINI_MODEL_GENERATE",
        _env_model("GEMINI_MODEL", GEMINI_MODELS["flash"]),
    ),
}

EMBEDDING_MODEL = _env_model("GEMINI_EMBEDDING_MODEL", GEMINI_MODELS["embedding"])


def model_for_task(task: LLMTask) -> str:
    return MODEL_FOR_TASK[task]
