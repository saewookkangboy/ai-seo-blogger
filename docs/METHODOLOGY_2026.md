# GAEO / AI SEO 분석 방법론 — 2026 리프레시

이 문서는 [gaeoanalysis](https://github.com/saewookkangboy/gaeoanalysis) 최신 LLM 업그레이드(PR #2)를
`ai-seo-blogger`(FastAPI)에 이식한 내용을 정리합니다.

코드: `app/services/llm/*`, `app/services/modern_ai_signals.py`,
`app/services/algorithm_defaults.py`, `app/services/analysis_enrichment.py`

## 1. 모델·클라이언트 최신화

- 모델 ID는 `app/services/llm/models.py`에서 중앙 관리. 기본 `gemini-flash-latest` 별칭.
- Gemini 호출은 `app/services/llm/gemini.py` REST 래퍼(텍스트 / JSON 구조화 / 그라운딩 / 임베딩).
- 기존 `content_generator` 등 레거시 경로는 `settings.gemini_model`(기본 `gemini-2.0-flash`) 유지.

## 2. 휴리스틱 → 하이브리드(그라운딩) 신호

- AIO 인용 확률: `app/services/aio_citation_analyzer.py` (가중치 + 간이 보너스).
- `citation_grounding.py`가 Google Search 그라운딩으로 실제 인용 여부를 검증(옵트인).
  - `ENABLE_CITATION_GROUNDING=true` 또는 `enable_citation_grounding`.

## 3. 의미 기반 점수 (임베딩)

- `semantic_relevance.py`: 임베딩 코사인으로 주제 일관성·질의 관련도 측정.
  - `ENABLE_SEMANTIC_SCORING=true` 또는 `enable_semantic_scoring`.

## 4. 2026 AI 검색 전용 신호

- AI 크롤러 robots.txt 접근성, llms.txt, Speakable 스키마.
- SEO 분석(`AdvancedSEOAnalyzer.analyze_content`)에 기본 포함.

## 5. 가중치 재보정 (2026)

- Gemini 그룹: SEO 0.35→0.30, AEO 0.25→0.30 (GEO 0.40 유지). 합 1.0 불변식.

## 6. 프로바이더 추상화

- `app/services/llm/provider.py`: gemini / openai / anthropic / perplexity / xai.
- `/health`의 `checks.llm_providers`에 설정 상태 스냅샷.

## 7. 회귀 게이트 (evals)

```bash
python scripts/run_evals.py
```

키 없이도 구조 검증. `GEMINI_API_KEY`가 있으면 구조화 출력 스모크까지 실행.
