"""
실제 검색 그라운딩 기반 인용 검증 (gaeoanalysis `lib/llm/citation-grounding.ts` 포트).

비용이 발생하므로 기본 비활성. ENABLE_CITATION_GROUNDING=true 일 때만 동작.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import List
from urllib.parse import urlparse

from app.services.llm.cache import TTLCache, hash_key
from app.services.llm.gemini import GenerateOptions, generate_text, is_gemini_configured
from app.services.llm.models import model_for_task


@dataclass
class GroundingInput:
    url: str
    title: str
    questions: List[str]


@dataclass
class GroundingResult:
    enabled: bool
    cited_sources: List[str] = field(default_factory=list)
    target_domain_cited: bool = False
    assessment: str = ""

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "cited_sources": self.cited_sources,
            "target_domain_cited": self.target_domain_cited,
            "assessment": self.assessment,
        }


_grounding_cache: TTLCache[GroundingResult] = TTLCache(6 * 60 * 60 * 1000, 200)


def _domain_of(url: str) -> str:
    try:
        return urlparse(url).hostname.replace("www.", "") if urlparse(url).hostname else ""
    except Exception:
        return ""


def is_grounding_enabled() -> bool:
    if not is_gemini_configured():
        return False
    if os.getenv("ENABLE_CITATION_GROUNDING", "").lower() == "true":
        return True
    try:
        from app.config import settings

        return bool(getattr(settings, "enable_citation_grounding", False))
    except Exception:
        return False


async def verify_citation_grounding(inp: GroundingInput) -> GroundingResult:
    if not is_grounding_enabled():
        return GroundingResult(
            enabled=False,
            assessment="그라운딩 검증 비활성 (ENABLE_CITATION_GROUNDING).",
        )

    target_domain = _domain_of(inp.url)
    cache_key = hash_key(f"{inp.url}|{'|'.join(inp.questions)}")

    async def _run() -> GroundingResult:
        questions = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(inp.questions))
        prompt = (
            "아래 질문들에 대해 웹 검색 근거를 바탕으로 간결히 답하고,\n"
            f'"{target_domain}" 도메인({inp.title})의 콘텐츠가 이런 질의에서 인용될 만한지 평가하세요.\n\n'
            f"질문:\n{questions}\n\n"
            '마지막 줄에 "평가:"로 시작하는 한 문장 요약을 포함하세요.'
        )
        result = await generate_text(
            GenerateOptions(
                model=model_for_task("report"),
                prompt=prompt,
                temperature=0.3,
                google_search=True,
            )
        )
        match = re.search(r"평가:\s*(.+)$", result.text, re.MULTILINE)
        assessment = match.group(1).strip() if match else result.text[-300:].strip()
        target_cited = any(_domain_of(u) == target_domain for u in result.grounding_urls)
        return GroundingResult(
            enabled=True,
            cited_sources=result.grounding_urls,
            target_domain_cited=target_cited,
            assessment=assessment,
        )

    return await _grounding_cache.wrap(cache_key, _run)
