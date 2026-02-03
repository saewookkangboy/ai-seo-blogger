# app/services/target_analyzer.py

import openai
from typing import Optional, Dict, List, Any
from ..config import settings
from ..exceptions import ContentGenerationError, APIKeyError
from ..utils.logger import setup_logger
import os
import json
import asyncio
from datetime import datetime

logger = setup_logger(__name__)

# OpenAI 클라이언트 인스턴스
client = None

def _initialize_client():
    """OpenAI 클라이언트 초기화"""
    global client
    
    api_key = settings.get_openai_api_key()
    if not api_key:
        logger.warning("유효한 OPENAI_API_KEY가 설정되지 않았습니다.")
        return False
    
    try:
        client = openai.AsyncOpenAI(
            api_key=api_key,
            timeout=openai.Timeout(30)
        )
        logger.info("OpenAI 클라이언트가 성공적으로 초기화되었습니다.")
        return True
    except Exception as e:
        logger.error(f"OpenAI 클라이언트 초기화 중 오류 발생: {e}")
        return False

async def analyze_target_with_openai(
    target_keyword: str,
    target_type: str = "keyword",  # "keyword", "audience", "competitor"
    additional_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    OpenAI를 사용하여 타겟 분석을 수행합니다.
    
    Args:
        target_keyword: 분석할 타겟 키워드 또는 주제
        target_type: 분석 유형 ("keyword", "audience", "competitor")
        additional_context: 추가 컨텍스트 정보
    
    Returns:
        분석 결과 딕셔너리
    """
    global client
    
    if not client and not _initialize_client():
        raise ContentGenerationError("OpenAI 클라이언트 초기화 실패")
    
    try:
        # 분석 유형에 따른 프롬프트 구성
        if target_type == "keyword":
            prompt = f"""
다음 키워드에 대한 심층적인 타겟 분석을 수행해주세요.

**분석 대상 키워드**: {target_keyword}
{f"**추가 컨텍스트**: {additional_context}" if additional_context else ""}

다음 항목들을 포함하여 JSON 형식으로 분석 결과를 제공해주세요:

1. **키워드 분석**:
   - 검색 의도 (Informational, Navigational, Transactional, Commercial)
   - 경쟁도 (낮음/중간/높음)
   - 검색량 추정 (낮음/중간/높음)
   - 관련 키워드 제안 (5-10개)

2. **타겟 오디언스**:
   - 주요 타겟 그룹 (3-5개)
   - 각 그룹의 특성 및 니즈
   - 관심사 및 행동 패턴

3. **콘텐츠 전략**:
   - 추천 콘텐츠 유형
   - 최적의 콘텐츠 길이
   - SEO 최적화 포인트

4. **경쟁 분석**:
   - 경쟁 강도 평가
   - 차별화 포인트 제안

반드시 다음 JSON 형식으로 응답해주세요:
{{
    "keyword_analysis": {{
        "search_intent": "...",
        "competition_level": "...",
        "search_volume_estimate": "...",
        "related_keywords": ["...", "..."]
    }},
    "target_audience": {{
        "primary_groups": [
            {{
                "group_name": "...",
                "characteristics": "...",
                "needs": "...",
                "interests": "..."
            }}
        ]
    }},
    "content_strategy": {{
        "recommended_types": ["..."],
        "optimal_length": "...",
        "seo_points": ["..."]
    }},
    "competition_analysis": {{
        "competition_strength": "...",
        "differentiation_points": ["..."]
    }}
}}
"""
        elif target_type == "audience":
            prompt = f"""
다음 타겟 오디언스에 대한 심층적인 분석을 수행해주세요.

**분석 대상**: {target_keyword}
{f"**추가 컨텍스트**: {additional_context}" if additional_context else ""}

다음 항목들을 포함하여 JSON 형식으로 분석 결과를 제공해주세요:

1. **오디언스 세그먼트**:
   - 주요 세그먼트 (3-5개)
   - 각 세그먼트의 인구통계학적 특성
   - 심리적 특성 및 가치관

2. **행동 패턴**:
   - 미디어 소비 패턴
   - 구매 행동
   - 온라인 활동 패턴

3. **콘텐츠 선호도**:
   - 선호하는 콘텐츠 유형
   - 선호하는 톤앤매너
   - 참여도가 높은 콘텐츠 특성

4. **마케팅 인사이트**:
   - 효과적인 커뮤니케이션 채널
   - 메시징 전략
   - 타겟팅 키워드

반드시 다음 JSON 형식으로 응답해주세요:
{{
    "audience_segments": [
        {{
            "segment_name": "...",
            "demographics": "...",
            "psychographics": "...",
            "size_estimate": "..."
        }}
    ],
    "behavior_patterns": {{
        "media_consumption": "...",
        "purchase_behavior": "...",
        "online_activity": "..."
    }},
    "content_preferences": {{
        "preferred_types": ["..."],
        "tone_and_manner": "...",
        "engagement_factors": ["..."]
    }},
    "marketing_insights": {{
        "effective_channels": ["..."],
        "messaging_strategy": "...",
        "targeting_keywords": ["..."]
    }}
}}
"""
        else:  # competitor
            prompt = f"""
다음 경쟁사 또는 경쟁 키워드에 대한 분석을 수행해주세요.

**분석 대상**: {target_keyword}
{f"**추가 컨텍스트**: {additional_context}" if additional_context else ""}

다음 항목들을 포함하여 JSON 형식으로 분석 결과를 제공해주세요:

1. **경쟁 환경 분석**:
   - 주요 경쟁자 식별
   - 경쟁 강도 평가
   - 시장 포지셔닝

2. **경쟁자 강점/약점**:
   - 경쟁자의 주요 강점
   - 경쟁자의 약점 및 기회
   - 차별화 포인트

3. **전략적 제안**:
   - 경쟁 우위 확보 방안
   - 시장 진입 전략
   - 콘텐츠 차별화 전략

반드시 다음 JSON 형식으로 응답해주세요:
{{
    "competitive_environment": {{
        "main_competitors": ["..."],
        "competition_intensity": "...",
        "market_positioning": "..."
    }},
    "competitor_analysis": {{
        "strengths": ["..."],
        "weaknesses": ["..."],
        "differentiation_points": ["..."]
    }},
    "strategic_recommendations": {{
        "competitive_advantages": ["..."],
        "market_entry_strategy": "...",
        "content_differentiation": ["..."]
    }}
}}
"""
        
        # OpenAI API 호출
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "당신은 전문적인 마케팅 및 SEO 분석가입니다. 정확하고 실용적인 분석을 제공해주세요."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        # 응답 파싱
        content = response.choices[0].message.content
        analysis_result = json.loads(content)
        
        # 메타데이터 추가
        analysis_result["metadata"] = {
            "target": target_keyword,
            "analysis_type": target_type,
            "analyzed_at": datetime.now().isoformat(),
            "model": settings.openai_model
        }
        
        logger.info(f"타겟 분석 완료: {target_keyword} ({target_type})")
        return analysis_result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        raise ContentGenerationError(f"분석 결과 파싱 실패: {e}")
    except Exception as e:
        logger.error(f"타겟 분석 중 오류: {e}")
        raise ContentGenerationError(f"타겟 분석 실패: {e}")

async def analyze_target_with_gemini(
    target_keyword: str,
    target_type: str = "keyword",
    additional_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Gemini API를 사용하여 타겟 분석을 수행합니다.
    """
    try:
        import httpx
        from .translator import get_gemini_api_key
        
        api_key = get_gemini_api_key()
        if not api_key:
            raise ContentGenerationError("Gemini API 키가 설정되지 않았습니다.")
        
        # 프롬프트 구성 (OpenAI와 동일한 구조)
        if target_type == "keyword":
            prompt = f"""
다음 키워드에 대한 심층적인 타겟 분석을 수행해주세요.

**분석 대상 키워드**: {target_keyword}
{f"**추가 컨텍스트**: {additional_context}" if additional_context else ""}

다음 항목들을 포함하여 JSON 형식으로 분석 결과를 제공해주세요:

1. **키워드 분석**:
   - 검색 의도 (Informational, Navigational, Transactional, Commercial)
   - 경쟁도 (낮음/중간/높음)
   - 검색량 추정 (낮음/중간/높음)
   - 관련 키워드 제안 (5-10개)

2. **타겟 오디언스**:
   - 주요 타겟 그룹 (3-5개)
   - 각 그룹의 특성 및 니즈
   - 관심사 및 행동 패턴

3. **콘텐츠 전략**:
   - 추천 콘텐츠 유형
   - 최적의 콘텐츠 길이
   - SEO 최적화 포인트

4. **경쟁 분석**:
   - 경쟁 강도 평가
   - 차별화 포인트 제안

반드시 JSON 형식으로 응답해주세요.
"""
        else:
            prompt = f"""
다음 타겟에 대한 심층적인 분석을 수행해주세요.

**분석 대상**: {target_keyword}
{f"**추가 컨텍스트**: {additional_context}" if additional_context else ""}

상세한 분석 결과를 JSON 형식으로 제공해주세요.
"""
        
        # Gemini API 호출
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={api_key}"
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                url,
                json={
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 2000,
                        "responseMimeType": "application/json"
                    }
                }
            )
            
            if response.status_code != 200:
                error_text = response.text
                raise ContentGenerationError(f"Gemini API 오류: {error_text}")
            
            result = response.json()
            
            if "candidates" not in result or not result["candidates"]:
                raise ContentGenerationError("Gemini API 응답 형식 오류")
            
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            analysis_result = json.loads(content)
            
            # 메타데이터 추가
            analysis_result["metadata"] = {
                "target": target_keyword,
                "analysis_type": target_type,
                "analyzed_at": datetime.now().isoformat(),
                "model": settings.gemini_model
            }
            
            logger.info(f"타겟 분석 완료 (Gemini): {target_keyword} ({target_type})")
            return analysis_result
            
    except Exception as e:
        logger.error(f"Gemini 타겟 분석 중 오류: {e}")
        raise ContentGenerationError(f"타겟 분석 실패: {e}")

async def analyze_target(
    target_keyword: str,
    target_type: str = "keyword",
    additional_context: Optional[str] = None,
    use_gemini: bool = False
) -> Dict[str, Any]:
    """
    타겟 분석을 수행합니다. (OpenAI 또는 Gemini 사용)
    
    Args:
        target_keyword: 분석할 타겟 키워드 또는 주제
        target_type: 분석 유형 ("keyword", "audience", "competitor")
        additional_context: 추가 컨텍스트 정보
        use_gemini: Gemini 사용 여부 (기본값: False, OpenAI 사용)
    
    Returns:
        분석 결과 딕셔너리
    """
    try:
        if use_gemini:
            return await analyze_target_with_gemini(target_keyword, target_type, additional_context)
        else:
            return await analyze_target_with_openai(target_keyword, target_type, additional_context)
    except Exception as e:
        logger.error(f"타겟 분석 실패: {e}")
        # Fallback: 기본 분석 결과 반환
        return {
            "error": str(e),
            "basic_analysis": {
                "target": target_keyword,
                "type": target_type,
                "note": "AI 분석 실패로 기본 정보만 제공됩니다."
            },
            "metadata": {
                "target": target_keyword,
                "analysis_type": target_type,
                "analyzed_at": datetime.now().isoformat(),
                "error": True
            }
        }
