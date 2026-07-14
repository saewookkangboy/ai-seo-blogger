"""
AI 모델별 인용 확률 계산 (gaeoanalysis `lib/ai-citation-analyzer.ts` 핵심 포트).

2026 AIO 가중치(Gemini SEO/AEO 재보정)를 사용해 SEO/AEO/GEO 점수를 합성한다.
보너스는 BeautifulSoup 기준 간이 휴리스틱이다.
"""

from __future__ import annotations

import re
from typing import Dict, Optional

from bs4 import BeautifulSoup

from app.services.algorithm_defaults import DEFAULT_AIO_WEIGHTS, ENHANCED_AIO_WEIGHTS

AIOCitationScores = Dict[str, int]


def calculate_aio_citation_scores(
    soup: BeautifulSoup,
    aeo_score: float,
    geo_score: float,
    seo_score: float,
    *,
    is_website: bool = False,
    weight_overrides: Optional[Dict[str, float]] = None,
) -> AIOCitationScores:
    weights = dict(ENHANCED_AIO_WEIGHTS if is_website else DEFAULT_AIO_WEIGHTS)
    if weight_overrides:
        weights.update(weight_overrides)

    chatgpt_base = (
        seo_score * weights["chatgpt_seo_weight"]
        + aeo_score * weights["chatgpt_aeo_weight"]
        + geo_score * weights["chatgpt_geo_weight"]
    )
    perplexity_base = (
        geo_score * weights["perplexity_geo_weight"]
        + seo_score * weights["perplexity_seo_weight"]
        + aeo_score * weights["perplexity_aeo_weight"]
    )
    grok_base = (
        geo_score * weights["grok_geo_weight"]
        + seo_score * weights["grok_seo_weight"]
        + aeo_score * weights["grok_aeo_weight"]
    )
    gemini_base = (
        geo_score * weights["gemini_geo_weight"]
        + seo_score * weights["gemini_seo_weight"]
        + aeo_score * weights["gemini_aeo_weight"]
    )
    claude_base = (
        aeo_score * weights["claude_aeo_weight"]
        + geo_score * weights["claude_geo_weight"]
        + seo_score * weights["claude_seo_weight"]
    )

    return {
        "chatgpt": min(100, round(chatgpt_base + _chatgpt_bonus(soup))),
        "perplexity": min(100, round(perplexity_base + _perplexity_bonus(soup))),
        "grok": min(100, round(grok_base + _grok_bonus(soup))),
        "gemini": min(100, round(gemini_base + _gemini_bonus(soup))),
        "claude": min(100, round(claude_base + _claude_bonus(soup))),
    }


def _structured_text(soup: BeautifulSoup) -> str:
    return " ".join(t.get_text(" ", strip=True) for t in soup.select('script[type="application/ld+json"]'))


def _chatgpt_bonus(soup: BeautifulSoup) -> float:
    bonus = 0.0
    structured = _structured_text(soup)
    if "FAQPage" in structured:
        bonus += 12
    if soup.select('script[type="application/ld+json"]'):
        bonus += 10
    if soup.select("ol") and re.search(r"단계|step", soup.get_text(" ", strip=True), re.I):
        bonus += 7
    if soup.find(string=re.compile(r"FAQ|자주 묻는 질문", re.I)):
        bonus += 8
    return min(40.0, bonus)


def _perplexity_bonus(soup: BeautifulSoup) -> float:
    bonus = 0.0
    text = soup.get_text(" ", strip=True)
    if soup.select("time, [datetime], [class*='date'], [class*='updated']"):
        bonus += 10
    if re.search(r"202[4-9]|최근|recent|updated|latest", text, re.I):
        bonus += 5
    if soup.select("a[href^='http']"):
        bonus += 8
    return min(35.0, bonus)


def _grok_bonus(soup: BeautifulSoup) -> float:
    bonus = 0.0
    text = soup.get_text(" ", strip=True)
    if re.search(r"요약|summary|tl;dr|한줄", text, re.I):
        bonus += 8
    if soup.select("ul, ol"):
        bonus += 5
    return min(25.0, bonus)


def _gemini_bonus(soup: BeautifulSoup) -> float:
    bonus = 0.0
    structured = _structured_text(soup)
    if re.search(r"HowTo|FAQPage|Article", structured):
        bonus += 12
    if soup.select("h2, h3"):
        bonus += 6
    # AI Overviews 직답 신호: 질문형 헤딩 + 짧은 직답 단락
    if soup.find(["h2", "h3"], string=re.compile(r"\?|이란|무엇|how|what", re.I)):
        bonus += 8
    return min(35.0, bonus)


def _claude_bonus(soup: BeautifulSoup) -> float:
    bonus = 0.0
    text = soup.get_text(" ", strip=True)
    words = len(text.split())
    if words >= 1500:
        bonus += 10
    if re.search(r"근거|출처|citation|reference|연구", text, re.I):
        bonus += 8
    if soup.select("blockquote, cite"):
        bonus += 5
    return min(30.0, bonus)
