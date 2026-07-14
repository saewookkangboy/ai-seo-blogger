"""
2026 AI 검색 신선 신호 (gaeoanalysis `lib/modern-ai-signals.ts` 포트).

- AI 크롤러 robots.txt 접근성
- llms.txt 힌트
- Speakable 스키마
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from bs4 import BeautifulSoup

AI_CRAWLERS = [
    "GPTBot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "ClaudeBot",
    "Claude-Web",
    "PerplexityBot",
    "Perplexity-User",
    "Google-Extended",
    "Applebot-Extended",
    "CCBot",
]


@dataclass
class ModernAISignals:
    allowed_crawlers: List[str] = field(default_factory=list)
    blocked_crawlers: List[str] = field(default_factory=list)
    has_llms_txt_hint: bool = False
    has_speakable: bool = False
    score: int = 0

    def to_dict(self) -> dict:
        return {
            "allowed_crawlers": self.allowed_crawlers,
            "blocked_crawlers": self.blocked_crawlers,
            "has_llms_txt_hint": self.has_llms_txt_hint,
            "has_speakable": self.has_speakable,
            "score": self.score,
        }


def is_crawler_blocked(robots_txt: str, user_agent: str) -> bool:
    """robots.txt에서 특정 봇이 루트 Disallow로 차단되는지 판별(간이 파서)."""
    if not robots_txt:
        return False

    lines = [line.strip() for line in robots_txt.splitlines()]
    in_block = False
    applies = False

    for line in lines:
        if re.match(r"^user-agent:", line, re.I):
            ua = line.split(":", 1)[1].strip() if ":" in line else ""
            if not in_block:
                applies = False
            in_block = True
            if ua == "*" or ua.lower() == user_agent.lower():
                applies = True
        elif re.match(r"^(allow|disallow):", line, re.I):
            in_block = False
            if applies and re.match(r"^disallow:\s*/\s*$", line, re.I):
                return True
        elif line == "":
            in_block = False
            applies = False
    return False


def analyze_modern_ai_signals(
    soup: BeautifulSoup,
    robots_txt: str = "",
    llms_txt: Optional[str] = None,
) -> ModernAISignals:
    allowed: List[str] = []
    blocked: List[str] = []
    for bot in AI_CRAWLERS:
        if is_crawler_blocked(robots_txt, bot):
            blocked.append(bot)
        else:
            allowed.append(bot)

    structured_data = " ".join(
        tag.get_text(" ", strip=True)
        for tag in soup.select('script[type="application/ld+json"]')
    )
    has_speakable = bool(re.search(r"speakable", structured_data, re.I)) or bool(
        soup.select('[class*="speakable"]')
    )

    has_llms_txt_hint = bool(llms_txt and llms_txt.strip()) or bool(
        soup.select('link[href*="llms.txt"], a[href$="llms.txt"]')
    )

    crawler_score = round((len(allowed) / len(AI_CRAWLERS)) * 70)
    score = min(100, crawler_score + (20 if has_llms_txt_hint else 0) + (10 if has_speakable else 0))

    return ModernAISignals(
        allowed_crawlers=allowed,
        blocked_crawlers=blocked,
        has_llms_txt_hint=has_llms_txt_hint,
        has_speakable=has_speakable,
        score=score,
    )
