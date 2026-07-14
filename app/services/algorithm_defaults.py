"""
SEO / AEO / GEO / AIO 기본 가중치 (gaeoanalysis `lib/algorithm-defaults.ts` 포트).

AIO Gemini 그룹은 2026-07 재보정:
  SEO 0.35→0.30, AEO 0.25→0.30 (GEO 0.40 유지), 그룹 합 1.0.
"""

from __future__ import annotations

from typing import Dict

DEFAULT_SEO_WEIGHTS: Dict[str, float] = {
    "h1_tag": 20,
    "title_tag": 15,
    "meta_description": 15,
    "alt_text": 10,
    "structured_data": 10,
    "meta_keywords": 5,
    "og_tags": 10,
    "canonical_url": 5,
    "internal_links": 5,
    "heading_structure": 5,
}

DEFAULT_AEO_WEIGHTS: Dict[str, float] = {
    "question_format": 20,
    "faq_section": 15,
    "clear_answer_structure": 20,
    "keyword_density": 10,
    "structured_answer": 15,
    "content_freshness": 10,
    "term_explanation": 10,
    "statistics_bonus": 5,
    "quotations_bonus": 3,
}

DEFAULT_GEO_WEIGHTS: Dict[str, float] = {
    "content_length_2000": 20,
    "content_length_1500": 18,
    "content_length_1000": 15,
    "content_length_500": 10,
    "multimedia_optimal": 15,
    "multimedia_good": 10,
    "section_structure_optimal": 15,
    "section_structure_basic": 10,
    "keyword_diversity": 15,
    "update_date_optimal": 10,
    "update_date_partial": 7,
    "social_meta_optimal": 10,
    "social_meta_partial": 6,
    "structured_data_optimal": 15,
    "structured_data_basic": 10,
    "voice_search_bonus": 5,
}

DEFAULT_AIO_WEIGHTS: Dict[str, float] = {
    "chatgpt_seo_weight": 0.4,
    "chatgpt_aeo_weight": 0.35,
    "chatgpt_geo_weight": 0.25,
    "perplexity_geo_weight": 0.45,
    "perplexity_seo_weight": 0.3,
    "perplexity_aeo_weight": 0.25,
    "grok_geo_weight": 0.45,
    "grok_seo_weight": 0.3,
    "grok_aeo_weight": 0.25,
    "gemini_geo_weight": 0.4,
    "gemini_seo_weight": 0.3,
    "gemini_aeo_weight": 0.3,
    "claude_aeo_weight": 0.4,
    "claude_geo_weight": 0.35,
    "claude_seo_weight": 0.25,
}

ENHANCED_AIO_WEIGHTS: Dict[str, float] = {
    "chatgpt_seo_weight": 0.35,
    "chatgpt_aeo_weight": 0.40,
    "chatgpt_geo_weight": 0.25,
    "perplexity_geo_weight": 0.45,
    "perplexity_seo_weight": 0.30,
    "perplexity_aeo_weight": 0.25,
    "grok_geo_weight": 0.45,
    "grok_seo_weight": 0.3,
    "grok_aeo_weight": 0.25,
    "gemini_geo_weight": 0.4,
    "gemini_seo_weight": 0.3,
    "gemini_aeo_weight": 0.3,
    "claude_aeo_weight": 0.45,
    "claude_geo_weight": 0.30,
    "claude_seo_weight": 0.25,
}

AIO_WEIGHT_GROUPS = {
    "chatgpt": ["chatgpt_seo_weight", "chatgpt_aeo_weight", "chatgpt_geo_weight"],
    "perplexity": ["perplexity_geo_weight", "perplexity_seo_weight", "perplexity_aeo_weight"],
    "grok": ["grok_geo_weight", "grok_seo_weight", "grok_aeo_weight"],
    "gemini": ["gemini_geo_weight", "gemini_seo_weight", "gemini_aeo_weight"],
    "claude": ["claude_aeo_weight", "claude_geo_weight", "claude_seo_weight"],
}
