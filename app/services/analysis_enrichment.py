"""
2026 AI 신호 보강 헬퍼 (gaeoanalysis `lib/analyzer.ts` 4단계 포트).

기본값:
  - modern_ai_signals: 저비용 → 기본 활성
  - semantic_relevance: ENABLE_SEMANTIC_SCORING=true
  - citation_grounding: ENABLE_CITATION_GROUNDING=true
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.services.aio_citation_analyzer import (
    adjust_scores_with_modern_signals,
    calculate_aio_citation_scores,
)
from app.services.llm.citation_grounding import (
    GroundingInput,
    is_grounding_enabled,
    verify_citation_grounding,
)
from app.services.llm.semantic_relevance import compute_semantic_relevance
from app.services.modern_ai_signals import analyze_modern_ai_signals
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def _settings_flag(name: str) -> bool:
    try:
        from app.config import settings

        return bool(getattr(settings, name, False))
    except Exception:
        return False


async def _fetch_robots_txt(url: str) -> str:
    if not url:
        return ""
    try:
        origin = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        async with httpx.AsyncClient(timeout=3.0, follow_redirects=True) as client:
            response = await client.get(f"{origin}/robots.txt")
            if response.status_code == 200:
                return response.text
    except Exception:
        pass
    return ""


async def enrich_with_2026_signals(
    soup: BeautifulSoup,
    *,
    url: str = "",
    seo_score: float = 0.0,
    aeo_score: Optional[float] = None,
    geo_score: Optional[float] = None,
) -> Dict[str, Any]:
    """분석 결과에 붙일 2026 보강 신호를 계산한다 (fail-soft)."""
    enrichment: Dict[str, Any] = {}
    semantic_obj = None
    grounding_obj = None

    try:
        robots_txt = await _fetch_robots_txt(url) if url else ""
        modern = analyze_modern_ai_signals(soup, robots_txt=robots_txt, llms_txt=None)
        enrichment["modern_ai_signals"] = modern.to_dict()

        # AEO/GEO 점수가 없으면 휴리스틱 근사
        if aeo_score is None:
            aeo_score = min(100.0, seo_score * 0.9 + (10 if modern.has_speakable else 0))
        if geo_score is None:
            geo_score = min(100.0, seo_score * 0.85 + (modern.score * 0.15))

        aio_scores = calculate_aio_citation_scores(
            soup,
            aeo_score=aeo_score,
            geo_score=geo_score,
            seo_score=seo_score,
        )
        enrichment["aio_citation_scores"] = aio_scores
        enrichment["aeo_score"] = round(aeo_score, 1)
        enrichment["geo_score"] = round(geo_score, 1)

        page_title = ""
        if soup.title and soup.title.string:
            page_title = soup.title.string.strip()
        elif soup.find("h1"):
            page_title = soup.find("h1").get_text(" ", strip=True)

        if os.getenv("ENABLE_SEMANTIC_SCORING", "").lower() == "true" or _settings_flag(
            "enable_semantic_scoring"
        ):
            sections = []
            for el in soup.select("h1, h2, h3"):
                text = el.get_text(" ", strip=True)
                if text:
                    sections.append(text)
            for el in soup.select("p")[:12]:
                text = el.get_text(" ", strip=True)
                if len(text) > 40:
                    sections.append(text)
            queries = [page_title, f"{page_title} 방법", f"{page_title} 란"] if page_title else []
            rel = await compute_semantic_relevance(sections, queries)
            if rel:
                semantic_obj = rel
                enrichment["semantic_relevance"] = rel.to_dict()

        if (is_grounding_enabled() or _settings_flag("enable_citation_grounding")) and page_title and url:
            grounding = await verify_citation_grounding(
                GroundingInput(
                    url=url,
                    title=page_title,
                    questions=[page_title, f"{page_title}에 대해 알려줘"],
                )
            )
            grounding_obj = grounding
            enrichment["citation_grounding"] = grounding.to_dict()

        # 신호를 실제 인용 점수에 반영 (신호 없으면 값 불변)
        enrichment["aio_citation_scores"] = adjust_scores_with_modern_signals(
            aio_scores,
            blocked_crawlers=modern.blocked_crawlers,
            topical_coherence=semantic_obj.topical_coherence if semantic_obj else None,
            query_relevance=semantic_obj.query_relevance if semantic_obj else None,
            grounding_enabled=bool(grounding_obj and grounding_obj.enabled),
            target_domain_cited=bool(grounding_obj and grounding_obj.target_domain_cited),
        )

    except Exception as exc:
        logger.warning("2026 AI 신호 보강 중 오류 (계속 진행): %s", exc)

    return enrichment
