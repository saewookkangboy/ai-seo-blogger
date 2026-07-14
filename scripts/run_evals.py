#!/usr/bin/env python3
"""
LLM/알고리즘 회귀 평가(evals) — gaeoanalysis `scripts/run-evals.ts` 포트.

실행:  python scripts/run_evals.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bs4 import BeautifulSoup

from app.services.algorithm_defaults import (
    AIO_WEIGHT_GROUPS,
    DEFAULT_AIO_WEIGHTS,
    ENHANCED_AIO_WEIGHTS,
)
from app.services.llm.models import EMBEDDING_MODEL, MODEL_FOR_TASK
from app.services.llm.provider import provider_status
from app.services.modern_ai_signals import analyze_modern_ai_signals, is_crawler_blocked
from app.services.aio_citation_analyzer import adjust_scores_with_modern_signals

passed = 0
failed = 0


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def run_case(name: str, fn) -> None:
    global passed, failed
    try:
        result = fn()
        if asyncio.iscoroutine(result):
            asyncio.run(result)
        passed += 1
        print(f"  ✅ {name}")
    except Exception as exc:
        failed += 1
        print(f"  ❌ {name}\n     → {exc}")


def case_model_registry() -> None:
    for task, model in MODEL_FOR_TASK.items():
        assert_true(isinstance(model, str) and len(model) > 0, f"빈 모델 ID: {task}")
    assert_true(len(EMBEDDING_MODEL) > 0, "임베딩 모델 미설정")


def case_aio_weight_sums() -> None:
    for label, weights in (("DEFAULT", DEFAULT_AIO_WEIGHTS), ("ENHANCED", ENHANCED_AIO_WEIGHTS)):
        for group, keys in AIO_WEIGHT_GROUPS.items():
            total = sum(weights[k] for k in keys)
            assert_true(abs(total - 1.0) < 1e-9, f"{label}.{group} 합={total}")


def case_enhanced_aeo() -> None:
    assert_true(
        ENHANCED_AIO_WEIGHTS["chatgpt_aeo_weight"] >= DEFAULT_AIO_WEIGHTS["chatgpt_aeo_weight"],
        "chatgpt_aeo",
    )
    assert_true(
        ENHANCED_AIO_WEIGHTS["claude_aeo_weight"] >= DEFAULT_AIO_WEIGHTS["claude_aeo_weight"],
        "claude_aeo",
    )


def case_robots_parser() -> None:
    robots = "User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nAllow: /"
    assert_true(is_crawler_blocked(robots, "GPTBot"), "GPTBot 차단 미감지")
    assert_true(not is_crawler_blocked(robots, "PerplexityBot"), "PerplexityBot 오탐")


def case_modern_signals() -> None:
    soup = BeautifulSoup(
        '<html><head><link href="/llms.txt"></head><body><h1>x</h1></body></html>',
        "html.parser",
    )
    sig = analyze_modern_ai_signals(soup, robots_txt="", llms_txt=None)
    assert_true(sig.has_llms_txt_hint, "llms.txt 링크 미감지")
    assert_true(0 <= sig.score <= 100, "점수 범위 오류")


def case_provider_status() -> None:
    status = provider_status()
    for key in ("gemini", "openai", "anthropic", "perplexity", "xai"):
        assert_true(key in status, f"프로바이더 누락: {key}")


def case_signal_adjustment() -> None:
    base = {"chatgpt": 80, "perplexity": 80, "grok": 80, "gemini": 80, "claude": 80}
    unchanged = adjust_scores_with_modern_signals(base)
    assert_true(unchanged == base, "신호 없는데 점수 변함")

    blocked = adjust_scores_with_modern_signals(
        base, blocked_crawlers=["GPTBot", "OAI-SearchBot", "ChatGPT-User"]
    )
    assert_true(blocked["chatgpt"] < base["chatgpt"], "GPTBot 전면 차단인데 chatgpt 감점 없음")
    assert_true(blocked["perplexity"] == base["perplexity"], "perplexity가 영향받음(오류)")

    cited = adjust_scores_with_modern_signals(base, grounding_enabled=True, target_domain_cited=True)
    assert_true(cited["gemini"] > base["gemini"], "실제 인용인데 가점 없음")


async def case_live_structured() -> None:
    from app.services.llm.gemini import generate_json

    result = await generate_json(
        model=MODEL_FOR_TASK["suggestions"],
        prompt='반드시 {"ok": true} 만 JSON으로 반환하세요.',
        response_schema={
            "type": "OBJECT",
            "properties": {"ok": {"type": "BOOLEAN"}},
            "required": ["ok"],
        },
        max_output_tokens=32,
    )
    assert_true(isinstance(result["data"].get("ok"), bool), "ok 필드 아님")


def main() -> int:
    cases = [
        ("모델 레지스트리: 모든 태스크가 비어있지 않은 모델 ID로 해석됨", case_model_registry),
        ("AIO 가중치: 각 그룹 합 = 1.0 (DEFAULT/ENHANCED)", case_aio_weight_sums),
        ("AIO 가중치: ENHANCED ≥ DEFAULT (chatgpt_aeo, claude_aeo)", case_enhanced_aeo),
        ("robots.txt 파서: GPTBot 차단 감지", case_robots_parser),
        ("modern-ai-signals: 기본 신호 점수 계산", case_modern_signals),
        ("프로바이더 상태 스냅샷: 5개 프로바이더 키 존재", case_provider_status),
        ("신호 반영: 신호 없으면 불변, GPTBot 차단 시 chatgpt 감점", case_signal_adjustment),
    ]

    live_on = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    print(f"\n▶ GAEO evals — structural {len(cases)}건 (LIVE {'ON' if live_on else 'OFF'})\n")
    for name, fn in cases:
        run_case(name, fn)

    if live_on:
        run_case("[LIVE] 구조화 출력 스모크: {ok:boolean} 반환", case_live_structured)

    print(f"\n결과: {passed} passed, {failed} failed\n")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
