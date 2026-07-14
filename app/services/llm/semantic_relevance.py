"""
임베딩 기반 의미 관련도/주제 일관성 점수
(gaeoanalysis `lib/llm/semantic-relevance.ts` 포트).

ENABLE_SEMANTIC_SCORING=true 일 때 분석 파이프라인에서 호출한다.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from app.services.llm.cache import TTLCache, hash_key
from app.services.llm.gemini import embed_texts, is_gemini_configured

_embed_cache: TTLCache[List[float]] = TTLCache(6 * 60 * 60 * 1000, 1000)


@dataclass
class SemanticRelevance:
    topical_coherence: float
    query_relevance: Optional[float]

    def to_dict(self) -> dict:
        return {
            "topical_coherence": self.topical_coherence,
            "query_relevance": self.query_relevance,
        }


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


async def _embed_cached(texts: List[str]) -> List[List[float]]:
    result: List[Optional[List[float]]] = [None] * len(texts)
    missing_idx: List[int] = []
    missing_text: List[str] = []

    for i, text in enumerate(texts):
        cached = _embed_cache.get(hash_key(text))
        if cached is not None:
            result[i] = cached
        else:
            missing_idx.append(i)
            missing_text.append(text)

    if missing_text:
        vectors = await embed_texts(missing_text)
        for j, idx in enumerate(missing_idx):
            vec = vectors[j] if j < len(vectors) else []
            _embed_cache.set(hash_key(missing_text[j]), vec)
            result[idx] = vec

    return [v or [] for v in result]


async def compute_semantic_relevance(
    sections: List[str],
    queries: Optional[List[str]] = None,
) -> Optional[SemanticRelevance]:
    if not is_gemini_configured():
        return None

    queries = queries or []
    cleaned = [s.strip() for s in sections if s and s.strip()][:20]
    if len(cleaned) < 2:
        return SemanticRelevance(
            topical_coherence=0,
            query_relevance=0 if queries else None,
        )

    try:
        section_vecs = await _embed_cached(cleaned)
        dim = len(section_vecs[0]) if section_vecs else 0
        centroid = [0.0] * dim
        for vec in section_vecs:
            for i in range(dim):
                centroid[i] += vec[i] if i < len(vec) else 0.0
        if section_vecs:
            centroid = [v / len(section_vecs) for v in centroid]

        coherence = (
            sum(_cosine(v, centroid) for v in section_vecs) / len(section_vecs)
            if section_vecs
            else 0.0
        )

        query_relevance: Optional[float] = None
        if queries:
            query_vecs = await _embed_cached(queries)
            rel = 0.0
            for qv in query_vecs:
                best = max((_cosine(qv, sv) for sv in section_vecs), default=0.0)
                rel += best
            rel /= max(len(query_vecs), 1)
            query_relevance = round(max(0.0, min(1.0, rel)) * 100)

        return SemanticRelevance(
            topical_coherence=round(max(0.0, min(1.0, coherence)) * 100),
            query_relevance=query_relevance,
        )
    except Exception as exc:
        print(f"의미 관련도 계산 실패 — 폴백(None): {exc}")
        return None
