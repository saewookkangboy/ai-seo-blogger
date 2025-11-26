"""
SEO Guidelines Configuration
Modern SEO optimization policies including AI SEO, AEO, GEO, AIO, and AI Search
Version: 2025-01-25
Last Updated: 2025-01-25T01:06:54+09:00
"""

from datetime import datetime
from typing import Dict, List, Any

# Version information
SEO_VERSION = "2025-01-25"
SEO_LAST_UPDATED = "2025-01-25T01:06:54+09:00"

# ============================================================================
# AI SEO (AI Search Engine Optimization)
# ============================================================================
AI_SEO_GUIDELINES = {
    "enabled": True,
    "version": SEO_VERSION,
    "last_updated": SEO_LAST_UPDATED,
    "description": "AI 기반 검색 엔진 최적화 - E-E-A-T 원칙 기반",
    
    "e_e_a_t": {
        "experience": {
            "enabled": True,
            "description": "실제 경험 기반 콘텐츠 작성",
            "requirements": [
                "실제 사용 경험 포함",
                "구체적인 사례 제시",
                "개인적 인사이트 추가"
            ]
        },
        "expertise": {
            "enabled": True,
            "description": "전문성 입증",
            "requirements": [
                "출처 인용 및 데이터 기반",
                "전문 용어 정확한 사용",
                "최신 정보 반영"
            ]
        },
        "authoritativeness": {
            "enabled": True,
            "description": "권위 있는 정보 제공",
            "requirements": [
                "신뢰할 수 있는 출처 참조",
                "업계 표준 준수",
                "검증된 정보 제공"
            ]
        },
        "trustworthiness": {
            "enabled": True,
            "description": "신뢰성 및 정확성",
            "requirements": [
                "사실 확인",
                "투명한 정보 제공",
                "편향 없는 객관적 서술"
            ]
        }
    },
    
    "content_quality": {
        "min_length": 1500,
        "max_length": 5000,
        "originality_required": True,
        "depth": "comprehensive",
        "freshness": "regular_updates",
        "readability_level": "intermediate"
    },
    
    "technical_requirements": {
        "schema_markup": True,
        "mobile_first": True,
        "page_speed": "fast",
        "structured_data_types": ["Article", "FAQ", "HowTo", "BreadcrumbList"],
        "clean_html": True,
        "semantic_markup": True
    },
    
    "keyword_strategy": {
        "type": "long_tail",
        "conversational": True,
        "natural_language": True,
        "user_intent_focused": True,
        "semantic_variations": True
    }
}

# ============================================================================
# AEO (Answer Engine Optimization)
# ============================================================================
AEO_GUIDELINES = {
    "enabled": True,
    "version": SEO_VERSION,
    "last_updated": SEO_LAST_UPDATED,
    "description": "답변 엔진 최적화 - ChatGPT, Perplexity AI 등",
    
    "content_format": {
        "qa_sections": True,
        "faq_sections": True,
        "direct_answers": True,
        "answer_first_structure": True,
        "follow_up_questions": True
    },
    
    "language_style": {
        "clarity": "simple",
        "sentence_length": "short",
        "tone": "conversational",
        "jargon_level": "minimal",
        "active_voice": True,
        "plain_language": True
    },
    
    "content_structure": {
        "headings": ["H2", "H3", "H4"],
        "lists": {
            "bullet_points": True,
            "numbered_lists": True,
            "definition_lists": True
        },
        "tables": True,
        "callout_boxes": True
    },
    
    "schema_markup": {
        "types": ["FAQPage", "HowTo", "QAPage"],
        "required": True
    },
    
    "optimization_targets": [
        "ChatGPT",
        "Perplexity AI",
        "Claude",
        "Gemini",
        "Answer engines"
    ]
}

# ============================================================================
# GEO (Generative Engine Optimization)
# ============================================================================
GEO_GUIDELINES = {
    "enabled": True,
    "version": SEO_VERSION,
    "last_updated": SEO_LAST_UPDATED,
    "description": "생성형 엔진 최적화 - Google SGE, Bing Chat 등",
    
    "target_platforms": [
        "Google SGE (Search Generative Experience)",
        "Bing Chat (Microsoft Copilot)",
        "Perplexity AI",
        "ChatGPT Search"
    ],
    
    "content_structure": {
        "clear_hierarchy": True,
        "contextual_relevance": True,
        "topic_depth": "comprehensive",
        "citations_required": True,
        "source_attribution": True
    },
    
    "entity_optimization": {
        "brand_mentions": True,
        "entity_recognition": True,
        "topic_clusters": True,
        "internal_linking": True,
        "related_entities": True
    },
    
    "technical_requirements": {
        "crawlable": True,
        "clean_html": True,
        "structured_data": True,
        "ai_bot_accessible": True,
        "robots_txt_optimized": True
    },
    
    "content_quality": {
        "accuracy": "high",
        "comprehensiveness": "detailed",
        "relevance": "contextual",
        "authority": "established"
    }
}

# ============================================================================
# AIO (AI Overviews Optimization)
# ============================================================================
AIO_GUIDELINES = {
    "enabled": True,
    "version": SEO_VERSION,
    "last_updated": SEO_LAST_UPDATED,
    "description": "Google AI Overviews 최적화",
    
    "google_ai_overviews": {
        "concise_answers": True,
        "factual_content": True,
        "early_placement": True,
        "framework": "question_answer_expand",
        "snippet_optimization": True
    },
    
    "html_structure": {
        "clear_headings": True,
        "heading_hierarchy": ["H1", "H2", "H3"],
        "bullet_points": True,
        "numbered_lists": True,
        "tables": True,
        "semantic_html": True
    },
    
    "content_freshness": {
        "regular_updates": True,
        "latest_data": True,
        "current_statistics": True,
        "date_stamping": True
    },
    
    "multimedia": {
        "images": True,
        "alt_text_required": True,
        "descriptive_captions": True,
        "videos": False,  # Optional
        "infographics": True
    },
    
    "optimization_tactics": [
        "Top 10 organic ranking",
        "Featured snippet targeting",
        "Schema markup implementation",
        "E-E-A-T signals",
        "Topic authority building"
    ]
}

# ============================================================================
# AI Search (Unified AI Search Optimization)
# ============================================================================
AI_SEARCH_GUIDELINES = {
    "enabled": True,
    "version": SEO_VERSION,
    "last_updated": SEO_LAST_UPDATED,
    "description": "통합 AI 검색 플랫폼 최적화",
    
    "target_platforms": [
        "ChatGPT",
        "Claude",
        "Perplexity AI",
        "Google Gemini",
        "Bing AI",
        "Other AI assistants"
    ],
    
    "core_principles": {
        "clarity": "maximum",
        "authority": "established",
        "usefulness": "high",
        "accessibility": "universal"
    },
    
    "crawler_accessibility": {
        "gptbot_allowed": True,
        "google_extended_allowed": True,
        "other_ai_bots_allowed": True,
        "robots_txt_configured": True
    },
    
    "content_formatting": {
        "clean_code": True,
        "proper_html_tags": True,
        "semantic_structure": True,
        "minimal_javascript": True,
        "fast_loading": True
    },
    
    "optimization_focus": [
        "Direct answer provision",
        "Structured information",
        "Authoritative sources",
        "Clear formatting",
        "Comprehensive coverage"
    ]
}

# ============================================================================
# Combined SEO Guidelines
# ============================================================================
SEO_GUIDELINES_DEFAULT = {
    "version": SEO_VERSION,
    "last_updated": SEO_LAST_UPDATED,
    "guidelines": {
        "ai_seo": AI_SEO_GUIDELINES,
        "aeo": AEO_GUIDELINES,
        "geo": GEO_GUIDELINES,
        "aio": AIO_GUIDELINES,
        "ai_search": AI_SEARCH_GUIDELINES
    },
    "metadata": {
        "total_guidelines": 5,
        "all_enabled": True,
        "implementation_date": "2025-01-25",
        "next_review_date": "2025-04-25"
    }
}

import json
import os
import logging

logger = logging.getLogger(__name__)
GUIDELINES_FILE = os.path.join(os.path.dirname(__file__), "seo_guidelines.json")

def load_seo_guidelines_from_file() -> Dict[str, Any]:
    """파일에서 가이드라인 로드"""
    if os.path.exists(GUIDELINES_FILE):
        try:
            with open(GUIDELINES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load guidelines from file: {e}")
    return SEO_GUIDELINES_DEFAULT

def save_seo_guidelines(guidelines: Dict[str, Any]) -> bool:
    """가이드라인을 파일에 저장"""
    try:
        with open(GUIDELINES_FILE, 'w', encoding='utf-8') as f:
            json.dump(guidelines, f, indent=2, ensure_ascii=False)
        
        # 메모리 상의 가이드라인 업데이트
        global SEO_GUIDELINES
        SEO_GUIDELINES = guidelines
        return True
    except Exception as e:
        logger.error(f"Failed to save guidelines to file: {e}")
        return False

# 초기 로드
SEO_GUIDELINES = load_seo_guidelines_from_file()

def get_seo_guidelines() -> Dict[str, Any]:
    """현재 SEO 가이드라인 반환"""
    return SEO_GUIDELINES

def get_guideline_by_type(guideline_type: str) -> Dict[str, Any]:
    """특정 타입의 가이드라인 반환"""
    return SEO_GUIDELINES["guidelines"].get(guideline_type, {})

def get_all_enabled_guidelines() -> List[str]:
    """활성화된 모든 가이드라인 목록 반환"""
    enabled = []
    for name, guideline in SEO_GUIDELINES["guidelines"].items():
        if guideline.get("enabled", False):
            enabled.append(name)
    return enabled

def get_guideline_version_info() -> Dict[str, str]:
    """버전 정보 반환"""
    return {
        "version": SEO_VERSION,
        "last_updated": SEO_LAST_UPDATED,
        "total_guidelines": len(SEO_GUIDELINES["guidelines"]),
        "enabled_count": len(get_all_enabled_guidelines())
    }
