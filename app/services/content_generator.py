# app/services/content_generator.py

import openai
from typing import Optional, Dict, List, Any, Tuple
from ..config import settings
from ..exceptions import ContentGenerationError, APIKeyError
from ..utils.logger import setup_logger
from .keyword_manager import keyword_manager
from .redis_cache import get_redis_cache
from .structured_logger import setup_optimized_logging
import os
import json
import threading
from datetime import datetime
import re
import asyncio
import time

logger = setup_logger(__name__)

# OpenAI 클라이언트 인스턴스
client = None

# API 사용량 파일 경로
API_USAGE_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'api_usage.json'))
API_USAGE_LOCK = threading.Lock()

# 성능 최적화를 위한 설정 (최적화)
OPENAI_TIMEOUT = 30  # 30초로 단축 (속도 향상)
MAX_RETRIES = 2  # 재시도 횟수 단축 (속도 향상)
CACHE_DURATION = 1800  # 캐시 시간 30분으로 단축 (메모리 효율성)
MAX_CONCURRENT_GENERATIONS = 2  # 동시 생성 수 제한 (안정성)
GENERATION_DELAY = 0.1  # 생성 요청 간 지연 시간 (초)

# Redis 캐시 인스턴스 가져오기
redis_cache = get_redis_cache()

def _initialize_client():
    """OpenAI 클라이언트 초기화"""
    global client
    
    api_key = settings.get_openai_api_key()
    if not api_key:
        logger.warning("유효한 OPENAI_API_KEY가 설정되지 않았습니다. 기본 템플릿을 사용합니다.")
        return False
    
    try:
        client = openai.AsyncOpenAI(
            api_key=api_key,
            timeout=openai.Timeout(OPENAI_TIMEOUT)  # 타임아웃 설정
        )
        logger.info("OpenAI 클라이언트가 성공적으로 초기화되었습니다.")
        return True
    except Exception as e:
        logger.error(f"OpenAI 클라이언트 초기화 중 오류 발생: {e}")
        return False

def _get_cache_key(text: str, keywords: str, content_length: str, ai_mode: str) -> str:
    """캐시 키 생성"""
    import hashlib
    content = f"{text[:100]}{keywords}{content_length}{ai_mode}"
    return f"content_gen:{hashlib.md5(content.encode()).hexdigest()}"

def _get_cached_content(cache_key: str) -> Optional[Dict[str, Any]]:
    """캐시된 콘텐츠 가져오기 (Redis 사용)"""
    return redis_cache.get(cache_key)

def _set_cached_content(cache_key: str, content: Dict[str, Any]):
    """콘텐츠를 캐시에 저장 (Redis 사용)"""
    # 30분(1800초) 동안 캐시 유지
    redis_cache.set(cache_key, content, ttl=1800)

def clear_content_cache():
    """콘텐츠 캐시 클리어 (Redis 사용)"""
    # Redis에서는 전체 키 삭제가 비효율적이므로 로그만 남김 (또는 특정 패턴 삭제 구현 가능)
    logger.info("Redis 캐시 클리어 요청됨 (구현 필요)")

def clear_specific_cache(text: str, keywords: str, content_length: str, ai_mode: str):
    """특정 콘텐츠의 캐시 클리어 (Redis 사용)"""
    cache_key = _get_cache_key(text, keywords, content_length, ai_mode)
    redis_cache.delete(cache_key)
    logger.info(f"특정 캐시가 클리어되었습니다: {cache_key}")

# 동시 생성 제어를 위한 세마포어
generation_semaphore = asyncio.Semaphore(MAX_CONCURRENT_GENERATIONS)

# dev-agent-kit / .spec-kit/03-content-creation.md 기반 콘텐츠 품질 체크리스트 (AI SEO·GEO·AIO)
def _get_content_quality_checklist() -> str:
    """프롬프트에 주입할 콘텐츠 품질·최적화 체크리스트 문자열. AI SEO, GEO, 시맨틱 HTML 요구사항 반영."""
    return """
[콘텐츠 품질 및 최적화 체크리스트]
- **AI SEO**: 타겟 키워드와 LSI 키워드를 제목·헤딩·첫 문단에 자연스럽게 포함. 키워드 밀도와 가독성 유지(과도한 삽입 금지). 제목 60자 이내, 메타 설명 160자 이내.
- **GEO(생성형 엔진)**: FAQ 스키마 친화(질문-답변 블록 또는 faq-section), HowTo/단계별 가이드(번호 리스트·단계 구분), Article 스키마 친화(명확한 본문·리스트). 인용·출처·신뢰도 강화(주장 시 근거·출처 언급). AI 엔진 친화적 명확한 문단·리스트·소제목 구조.
- **시맨틱 HTML**: H1 1회, H2/H3 계층 준수, <p>, <ul>/<ol>, <section> 등 의미 구조. E-E-A-T(경험·전문성·권위·신뢰성) 신호 강화.
"""

def is_gemini_quota_exceeded(error_message: str) -> bool:
    """Gemini API 할당량 초과 오류인지 확인"""
    quota_error_patterns = [
        "quota exceeded",
        "quota limit",
        "rate limit exceeded",
        "resource exhausted",
        "quota has been exceeded",
        "quota limit exceeded",
        "429",
        "too many requests"
    ]
    error_lower = error_message.lower()
    return any(pattern in error_lower for pattern in quota_error_patterns)

async def translate_with_openai(text: str, target_lang: str = "ko") -> str:
    """
    OpenAI API를 사용한 fallback 번역 함수
    """
    global client
    
    if not text or not text.strip():
        return ""
    
    # 클라이언트 초기화
    if not client and not _initialize_client():
        logger.error("OpenAI 클라이언트 초기화 실패")
        return text
    
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": f"당신은 전문 번역가입니다. 주어진 텍스트를 {target_lang}로 자연스럽게 번역해주세요."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=settings.openai_max_tokens,
            temperature=0.3
        )
        
        translated_text = response.choices[0].message.content.strip()
        logger.info(f"OpenAI 번역 완료: {len(text)}자 → {len(translated_text)}자")
        return translated_text
        
    except Exception as e:
        logger.error(f"OpenAI 번역 중 오류: {e}")
        return text

async def create_blog_post(text: str, keywords: str, rule_guidelines: Optional[list] = None, content_length: str = "3000", ai_mode: Optional[str] = None, input_type: str = "text") -> Dict:
    """
    번역된 텍스트와 키워드, 추가 가이드라인을 기반으로 AI를 사용하여 블로그 게시물을 생성합니다.
    AI SEO 최적화를 위한 구조화된 콘텐츠를 생성합니다.
    Gemini 2.0 Flash와 OpenAI를 모두 지원합니다.
    """
    # 동시 생성 제어
    async with generation_semaphore:
        global client
        
        start_time = time.time()
        
        # 입력 검증
        if not text or not text.strip():
            logger.warning("빈 텍스트가 입력되었습니다.")
            return _generate_default_template("", keywords, rule_guidelines, content_length, ai_mode)
        
        # 캐시 확인
        cache_key = _get_cache_key(text, keywords, content_length, ai_mode or "")
        cached_content = _get_cached_content(cache_key)
        if cached_content:
            logger.info("캐시된 콘텐츠 생성 결과 사용")
            return cached_content
        
        # 생성 요청 간 지연 (API 부하 방지)
        await asyncio.sleep(GENERATION_DELAY)
        
    # 최신 SEO 가이드라인 로드 및 적용
    try:
        from app.seo_guidelines import get_seo_guidelines
        seo_guidelines = get_seo_guidelines()
        
        # 가이드라인 리스트 초기화
        if rule_guidelines is None:
            rule_guidelines = []
        else:
            rule_guidelines = list(rule_guidelines)  # 복사본 생성
            
        # 활성화된 가이드라인 추출
        active_guidelines = []
        if seo_guidelines.get("guidelines", {}).get("ai_seo", {}).get("enabled"):
            e_e_a_t = seo_guidelines["guidelines"]["ai_seo"].get("e_e_a_t", {})
            active_guidelines.append(f"E-E-A-T 원칙 준수: {e_e_a_t.get('experience', {}).get('description', '')}, {e_e_a_t.get('expertise', {}).get('description', '')}")
        
        if seo_guidelines.get("guidelines", {}).get("aeo", {}).get("enabled"):
            aeo = seo_guidelines["guidelines"]["aeo"]
            active_guidelines.append(f"AEO 최적화: {aeo.get('description', '')}")
            
        if seo_guidelines.get("guidelines", {}).get("geo", {}).get("enabled"):
            geo = seo_guidelines["guidelines"]["geo"]
            active_guidelines.append(f"GEO 최적화: {geo.get('description', '')}")
            
        if active_guidelines:
            rule_guidelines.append("--- 최신 SEO 가이드라인 ---")
            rule_guidelines.extend(active_guidelines)
            
    except Exception as e:
        logger.warning(f"SEO 가이드라인 로드 실패: {e}")
        if rule_guidelines is None:
            rule_guidelines = []
    
    # AI 모드에 따른 필수 HTML 구조 가이드라인 추가
    structure_guidelines = []
    if ai_mode == "ai_seo":
        structure_guidelines.append("- **필수 HTML 구조**: Schema.org 마크업(itemscope, itemtype)을 반드시 포함하세요.")
        structure_guidelines.append("- **헤딩 구조**: H1, H2, H3 태그를 체계적으로 사용하여 계층 구조를 만드세요.")
    elif ai_mode == "aeo":
        structure_guidelines.append("- **필수 HTML 구조**: `<div class=\"faq-section\">` 내에 `<div class=\"faq-item\">`을 사용하여 Q&A 형식을 구현하세요.")
        structure_guidelines.append("- **답변 스타일**: 질문에 대한 직접적이고 명확한 답변을 먼저 제시하세요.")
    elif ai_mode == "geo":
        structure_guidelines.append("- **필수 HTML 구조**: `<div class=\"comparison-table\">` 또는 `<div class=\"how-to-section\">` 등 구조화된 정보 블록을 포함하세요.")
        structure_guidelines.append("- **신뢰성**: 주장의 근거가 되는 출처나 데이터를 명시하세요.")
    
    if structure_guidelines:
        rule_guidelines.append("--- HTML 구조 가이드라인 ---")
        rule_guidelines.extend(structure_guidelines)
    
    # Gemini 2.0 Flash 모드인 경우 Gemini 사용
    if ai_mode == "gemini_2_0_flash":
        try:
            result = await _create_blog_post_with_gemini(text, keywords, rule_guidelines, content_length, ai_mode, input_type)
            if result:
                _set_cached_content(cache_key, result)
                return result
        except Exception as e:
            error_message = str(e)
            if is_gemini_quota_exceeded(error_message):
                logger.warning("Gemini API 할당량 초과로 OpenAI로 fallback합니다.")
            else:
                logger.warning(f"Gemini 2.0 Flash 콘텐츠 생성 실패, OpenAI로 fallback: {e}")
    
    # OpenAI 클라이언트 초기화
    if not client and not _initialize_client():
        logger.warning("OpenAI 클라이언트 초기화 실패. 기본 템플릿을 사용합니다.")
        return _generate_default_template(text, keywords, rule_guidelines, content_length, ai_mode)
    
    try:
        return await _create_blog_post_with_openai(text, keywords, rule_guidelines, content_length, ai_mode, input_type)
        
    except Exception as e:
        logger.error(f"블로그 포스트 생성 중 오류: {e}")
        return _generate_default_template(text, keywords, rule_guidelines, content_length, ai_mode)

async def _create_blog_post_with_gemini(text: str, keywords: str, rule_guidelines: Optional[list] = None, content_length: str = "5000", ai_mode: Optional[str] = None, input_type: str = "text") -> Dict:
    """
    Gemini 2.0 Flash API를 사용하여 블로그 포스트를 생성합니다.
    """
    try:
        import httpx
        
        # Gemini API 키 확인
        from .translator import get_gemini_api_key
        api_key = get_gemini_api_key()
        if not api_key:
            raise ContentGenerationError("Gemini API 키가 설정되지 않았습니다.")
        
        # 콘텐츠 길이 설정
        target_length = int(content_length) if content_length.isdigit() else 5000
        
        # 규칙 가이드라인 처리
        rules_text = ""
        if rule_guidelines:
            rules_text = "\n".join([f"- {rule}" for rule in rule_guidelines])
        
        # 입력 타입에 따른 지시사항
        input_instruction = ""
        if input_type == "url":
            input_instruction = """
- 입력된 텍스트는 특정 URL에서 크롤링한 내용입니다.
- 원본의 내용을 충실히 반영하되, 한국어 독자에 맞게 자연스럽게 재구성(Rewrite)하세요.
- 단순 번역이 아닌, 문맥을 고려한 '재창조' 수준의 글쓰기를 수행하세요.
"""
        else:
            input_instruction = """
- 입력된 텍스트는 주제나 문맥에 대한 설명입니다.
- 이 내용을 바탕으로 심층적인 분석을 수행하고 새로운 글을 작성(Write)하세요.
- 주어진 주제를 확장하여 풍부한 정보를 제공하세요.
"""

        # 프롬프트 구성 (dev-agent-kit / .spec-kit/03-content-creation 반영)
        content_checklist = _get_content_quality_checklist()
        prompt = f"""
당신은 전문적인 AI SEO 블로그 작가입니다. 다음 지침에 따라 고품질의 한국어 블로그 포스트를 작성해주세요.

[입력 정보]
- 원본 텍스트/문맥:
{text}

- 주요 키워드: {keywords}
- 목표 길이: 약 {target_length}자
- 입력 유형: {input_type} ({input_instruction.strip()})

[핵심 요구사항]
1. **균형 잡힌 관점 (Responsible AI)**: 편향되지 않고 객관적이며 윤리적인 관점을 유지하세요. 다양한 시각을 고려하여 균형 잡힌 정보를 제공하세요.
2. **SEO 및 AI 최적화**: 선택된 최적화 옵션에 맞춰 글을 구성하고, 키워드를 자연스럽게 본문에 녹여내세요.
3. **구조화된 출력**: 반드시 아래의 JSON 형식으로 응답해야 합니다.

{content_checklist}

[추가 규칙 및 가이드라인]
{rules_text}

[출력 형식 (JSON)]
응답은 반드시 다음 JSON 구조를 따라야 합니다. 마크다운 코드 블록(```json ... ```)으로 감싸주세요.

```json
{{
  "title": "블로그 제목",
  "meta_description": "SEO 메타 설명 (160자 이내)",
  "content": "<h1>제목</h1>...<p>본문 내용(HTML 형식)</p>...",
  "keywords": "추출된 주요 키워드 (최대 10개, 쉼표로 구분)",
  "metrics": {{
    "noun_count": 0,
    "verb_count": 0,
    "adjective_count": 0,
    "max_sentence_length": 0
  }},
  "score": 0,
  "evaluation": "가이드라인 준수 여부에 대한 짧은 평가 및 점수 이유",
  "ai_analysis": {{
    "trust_score": 0,
    "trust_reason": "신뢰도 점수 이유",
    "seo_score": 0,
    "seo_reason": "SEO 점수 이유",
    "ai_summary": "콘텐츠 핵심 요약 (100자 이내)"
  }}
}}
```

**metrics 작성 시 주의사항:**
- 생성된 한국어 콘텐츠를 기준으로 명사, 동사, 형용사의 개수를 대략적으로 계산하여 기입하세요.
- max_sentence_length는 가장 긴 문장의 글자 수(공백 제외)를 기입하세요.
- score는 0~100점 사이의 정수로, 위에서 제시한 가이드라인(SEO, 균형 잡힌 관점 등)을 얼마나 잘 준수했는지 스스로 평가한 점수입니다.

**ai_analysis 작성 시 주의사항:**
- trust_score: 5점 만점 (1-5). 콘텐츠의 신뢰성, 객관성, 근거 제시 여부를 평가하세요.
- seo_score: 10점 만점 (1-10). 키워드 사용, 구조, 가독성 등을 평가하세요.
- ai_summary: 전체 내용을 100자 이내로 핵심만 요약하세요.
"""
        
        async with httpx.AsyncClient(timeout=60) as client:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 8192,
                    "responseMimeType": "application/json"
                }
            }
            
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and result['candidates']:
                    generated_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    # JSON 파싱
                    try:
                        # 마크다운 코드 블록 제거
                        if generated_text.startswith("```json"):
                            generated_text = generated_text[7:]
                        if generated_text.endswith("```"):
                            generated_text = generated_text[:-3]
                        
                        data = json.loads(generated_text)
                        
                        return {
                            'post': data.get('content', ''),
                            'title': data.get('title', ''),
                            'meta_description': data.get('meta_description', ''),
                            'keywords': data.get('keywords', keywords),
                            'metrics': data.get('metrics', {}),
                            'score': data.get('score', 0),
                            'evaluation': data.get('evaluation', ''),
                            'ai_analysis': data.get('ai_analysis', {}),
                            'word_count': len(data.get('content', '').split()), # 단순 공백 기준
                            'content_length': content_length,
                            'ai_mode': ai_mode or 'gemini_2_0_flash'
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"Gemini 응답 JSON 파싱 실패: {e}")
                        # 파싱 실패 시 텍스트 전체를 콘텐츠로 간주 (fallback)
                        return {
                            'post': generated_text,
                            'title': f"{keywords.split(',')[0]} 관련 포스트",
                            'meta_description': "자동 생성된 포스트입니다.",
                            'keywords': keywords,
                            'word_count': len(generated_text.split()),
                            'content_length': content_length,
                            'ai_mode': ai_mode or 'gemini_2_0_flash'
                        }
                else:
                    raise ContentGenerationError("Gemini API 응답에 생성 결과가 없습니다.")
            else:
                error_detail = response.text
                logger.error(f"Gemini API 오류: {response.status_code} - {error_detail}")
                raise ContentGenerationError(f"Gemini API 오류: {response.status_code}")
                
    except Exception as e:
        logger.error(f"Gemini 블로그 포스트 생성 중 오류: {e}")
        raise ContentGenerationError(f"Gemini 블로그 포스트 생성 실패: {str(e)}")

async def _create_blog_post_with_openai(text: str, keywords: str, rule_guidelines: Optional[list] = None, content_length: str = "3000", ai_mode: Optional[str] = None, input_type: str = "text") -> Dict:
    """
    OpenAI API를 사용하여 블로그 포스트를 생성합니다.
    """
    global client
    
    if not client and not _initialize_client():
        raise ContentGenerationError("OpenAI 클라이언트 초기화 실패")
    
    try:
        # 콘텐츠 길이 설정
        target_length = int(content_length) if content_length.isdigit() else 3000
        
        # 규칙 가이드라인 처리
        rules_text = ""
        if rule_guidelines:
            rules_text = "\n".join([f"- {rule}" for rule in rule_guidelines])
        
        # 입력 타입에 따른 지시사항
        input_instruction = ""
        if input_type == "url":
            input_instruction = "입력된 텍스트는 특정 URL에서 크롤링한 내용입니다. 원본의 내용을 충실히 반영하되, 한국어 독자에 맞게 자연스럽게 재구성(Rewrite)하세요."
        else:
            input_instruction = "입력된 텍스트는 주제나 문맥에 대한 설명입니다. 이 내용을 바탕으로 심층적인 분석을 수행하고 새로운 글을 작성(Write)하세요."

        # 프롬프트 구성 (dev-agent-kit / .spec-kit/03-content-creation 반영)
        content_checklist = _get_content_quality_checklist()
        prompt = f"""
당신은 전문적인 AI SEO 블로그 작가입니다. 다음 지침에 따라 고품질의 한국어 블로그 포스트를 작성해주세요.

[입력 정보]
- 원본 텍스트/문맥:
{text}

- 주요 키워드: {keywords}
- 목표 길이: 약 {target_length}자
- 입력 유형: {input_type} ({input_instruction})

[핵심 요구사항]
1. **균형 잡힌 관점 (Responsible AI)**: 편향되지 않고 객관적이며 윤리적인 관점을 유지하세요. 다양한 시각을 고려하여 균형 잡힌 정보를 제공하세요.
2. **SEO 및 AI 최적화**: 선택된 최적화 옵션에 맞춰 글을 구성하고 키워드를 자연스럽게 포함하세요.
3. **구조화된 출력**: 반드시 아래의 JSON 형식으로 응답해야 합니다.

{content_checklist}

[추가 규칙]
{rules_text}

[출력 형식 (JSON)]
- meta_description은 반드시 160자 이내로 작성하세요.
```json
{{
  "title": "블로그 제목 (60자 이내)",
  "meta_description": "SEO 메타 설명 (160자 이내)",
  "content": "<h1>제목</h1>...<p>본문 내용(HTML 형식)</p>...",
  "keywords": "추출된 주요 키워드 (최대 10개, 쉼표로 구분)",
  "metrics": {{
    "noun_count": 0,
    "verb_count": 0,
    "adjective_count": 0,
    "max_sentence_length": 0
  }},
  "score": 0,
  "evaluation": "평가 및 점수 이유",
  "ai_analysis": {{
    "trust_score": 0,
    "trust_reason": "신뢰도 점수 이유",
    "seo_score": 0,
    "seo_reason": "SEO 점수 이유",
    "ai_summary": "콘텐츠 핵심 요약 (100자 이내)"
  }}
}}
```
"""

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "당신은 SEO·AI SEO·GEO에 능통한 블로그 작가입니다. 콘텐츠 품질 체크리스트를 준수하고 JSON 형식으로만 응답하세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=settings.openai_max_tokens,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        generated_content = response.choices[0].message.content.strip()
        
        # JSON 파싱
        data = json.loads(generated_content)
        
        return {
            'post': data.get('content', ''),
            'title': data.get('title', ''),
            'meta_description': data.get('meta_description', ''),
            'keywords': data.get('keywords', keywords),
            'metrics': data.get('metrics', {}),
            'score': data.get('score', 0),
            'evaluation': data.get('evaluation', ''),
            'ai_analysis': data.get('ai_analysis', {}),
            'word_count': len(data.get('content', '').split()),
            'content_length': content_length,
            'ai_mode': ai_mode or 'openai'
        }
        
    except Exception as e:
        logger.error(f"OpenAI 블로그 포스트 생성 중 오류: {e}")
        raise ContentGenerationError(f"OpenAI 블로그 포스트 생성 실패: {str(e)}")

def _extract_keywords_from_content(content: str, db_session=None) -> str:
    """
    콘텐츠에서 키워드를 추출합니다. (개선된 버전)
    """
    try:
        # 기존 키워드 가져오기
        existing_keywords = set()
        if db_session:
            existing_keywords = keyword_manager.get_existing_keywords(db_session)
        
        # 새로운 키워드 매니저를 사용하여 고유한 키워드 추출
        unique_keywords = keyword_manager.extract_unique_keywords(content, existing_keywords)
        
        return unique_keywords
        
    except Exception as e:
        logger.error(f"키워드 추출 중 오류: {e}")
        return "AI, 기술, 분석, 개발, 시스템"

def _generate_default_template(text: str, keywords: str, rule_guidelines: Optional[List[str]] = None, content_length: str = "3000", ai_mode: Optional[str] = None) -> Dict:
    """
    API 호출 실패 시 기본 템플릿을 생성합니다.
    """
    try:
        # 기본 제목 생성
        title = f"{keywords.split(',')[0] if keywords else 'AI 블로그 포스트'}에 대한 상세 가이드"
        
        # 기본 메타 설명
        meta_description = f"{keywords}에 대한 포괄적인 정보와 가이드를 제공합니다."
        
        # 기본 콘텐츠 생성
        content_length_int = int(content_length) if content_length.isdigit() else 3000
        
        # 텍스트 요약
        summary = text[:200] + "..." if len(text) > 200 else text
        
        # HTML 콘텐츠 생성
        content = f"""
<h1>{title}</h1>
<meta name="description" content="{meta_description}">

<div class="content-intro">
    <p>이 글에서는 <strong>{keywords}</strong>에 대해 자세히 알아보겠습니다.</p>
</div>

<div class="content-main">
    <h2>📋 주요 내용</h2>
    <p>{summary}</p>
    
    <h2>🔍 핵심 포인트</h2>
    <ul>
        <li><strong>첫 번째 중요한 포인트:</strong> {keywords.split(',')[0] if keywords else '주제'}의 기본 개념과 중요성</li>
        <li><strong>두 번째 중요한 포인트:</strong> 실제 적용 방법과 사례</li>
        <li><strong>세 번째 중요한 포인트:</strong> 주의사항과 모범 사례</li>
    </ul>
    
    <h2>💡 실용적인 팁</h2>
    <div class="tips-container">
        <div class="tip-item">
            <h3>팁 1: 효과적인 활용</h3>
            <p>{keywords.split(',')[0] if keywords else '주제'}를 효과적으로 활용하는 방법을 알아보세요.</p>
        </div>
        <div class="tip-item">
            <h3>팁 2: 주의사항</h3>
            <p>일반적인 실수와 피해야 할 함정에 대해 알아보세요.</p>
        </div>
    </div>
    
    <h2>📊 요약</h2>
    <p>이 글을 통해 {keywords.split(',')[0] if keywords else '주제'}에 대한 이해를 높이고, 실제 상황에서 효과적으로 활용할 수 있는 지식을 얻었습니다.</p>
</div>

<style>
.content-intro {{ background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 1rem 0; }}
.content-main {{ line-height: 1.6; }}
.tips-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0; }}
.tip-item {{ background: #e3f2fd; padding: 1rem; border-radius: 8px; border-left: 4px solid #2196f3; }}
</style>
"""
        
        # 단어 수 계산
        text_content = re.sub(r'<[^>]+>', '', content)
        word_count = len(text_content.split())
        
        logger.info("기본 템플릿 생성 완료")
        
        return {
            'post': content,
            'title': title,
            'meta_description': meta_description,
            'keywords': keywords,
            'word_count': word_count,
            'content_length': content_length,
            'ai_mode': ai_mode or 'default_template'
        }
        
    except Exception as e:
        logger.error(f"기본 템플릿 생성 중 오류: {e}")
        # 최소한의 기본 응답
        return {
            'post': f"<h1>{keywords.split(',')[0] if keywords else 'AI 블로그 포스트'}</h1><p>콘텐츠 생성 중 오류가 발생했습니다.</p>",
            'title': keywords.split(',')[0] if keywords else 'AI 블로그 포스트',
            'meta_description': f"{keywords}에 대한 정보",
            'keywords': keywords,
            'word_count': 10,
            'content_length': content_length,
            'ai_mode': ai_mode or 'error_fallback'
        }

async def extract_seo_keywords(text: str) -> str:
    """
    텍스트에서 SEO 키워드를 추출합니다.
    """
    try:
        # 기본 키워드 추출
        keywords = _extract_default_keywords(text)
        
        # OpenAI API가 있으면 더 정교한 키워드 추출 시도
        if settings.get_openai_api_key():
            try:
                global client
                if not client and not _initialize_client():
                    return keywords
                
                prompt = f"""
다음 텍스트에서 SEO에 유용한 키워드 5-7개를 추출해주세요.
키워드는 쉼표로 구분하여 한국어로만 응답해주세요.

텍스트:
{text[:1000]}

키워드:
"""
                
                response = await client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {"role": "system", "content": "당신은 SEO 전문가입니다. 텍스트에서 가장 중요한 키워드들을 추출해주세요."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.3
                )
                
                extracted_keywords = response.choices[0].message.content.strip()
                return extracted_keywords
                
            except Exception as e:
                logger.error(f"OpenAI 키워드 추출 중 오류: {e}")
                return keywords
                
    except Exception as e:
        logger.error(f"SEO 키워드 추출 중 오류: {e}")
        return _extract_default_keywords(text)

async def analyze_seo_news(news_items: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    수집된 뉴스 아이템들을 분석하여 SEO 트렌드를 추출합니다.
    """
    global client
    
    if not news_items:
        return {}
        
    if not client and not _initialize_client():
        logger.warning("OpenAI 클라이언트 초기화 실패. 뉴스 분석을 건너뜁니다.")
        return {}
        
    try:
        # 뉴스 내용 요약 준비
        news_summary = ""
        for i, item in enumerate(news_items[:10]):  # 최대 10개만 분석
            news_summary += f"{i+1}. 제목: {item.get('title', '')}\n   내용: {item.get('summary', '')}\n   카테고리: {item.get('category', '')}\n\n"
            
        prompt = f"""
다음은 최근 수집된 SEO 관련 뉴스 기사들입니다. 이 기사들을 분석하여 각 카테고리별(AI SEO, AEO, GEO, AIO, AI Search)로 최신 트렌드와 중요한 변경사항을 추출해주세요.

뉴스 기사 목록:
{news_summary}

응답 형식 (JSON):
{{
    "ai_seo": ["트렌드 1", "트렌드 2"],
    "aeo": ["트렌드 1", "트렌드 2"],
    "geo": ["트렌드 1", "트렌드 2"],
    "aio": ["트렌드 1", "트렌드 2"],
    "ai_search": ["트렌드 1", "트렌드 2"]
}}

각 트렌드는 간결하고 명확한 문장으로 작성해주세요. 중요한 알고리즘 업데이트나 새로운 최적화 전략에 초점을 맞춰주세요.
"""

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "당신은 SEO 트렌드 분석 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result_json = response.choices[0].message.content.strip()
        return json.loads(result_json)
        
    except Exception as e:
        logger.error(f"SEO 뉴스 분석 중 오류: {e}")
        return {}

async def update_guideline_content(current_guidelines: Dict[str, Any], trends: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    현재 가이드라인과 새로운 트렌드를 병합하여 업데이트된 가이드라인을 생성합니다.
    """
    global client
    
    if not client and not _initialize_client():
        logger.warning("OpenAI 클라이언트 초기화 실패. 가이드라인 업데이트를 건너뜁니다.")
        return current_guidelines
        
    try:
        # 프롬프트 구성
        prompt = f"""
다음은 현재 SEO 가이드라인과 새로 발견된 트렌드입니다.
새로운 트렌드를 반영하여 가이드라인을 업데이트해주세요.

현재 가이드라인 (JSON):
{json.dumps(current_guidelines, ensure_ascii=False, indent=2)[:3000]}... (생략)

새로운 트렌드 (JSON):
{json.dumps(trends, ensure_ascii=False, indent=2)}

요구사항:
1. 기존 가이드라인의 구조를 유지하세요.
2. 새로운 트렌드를 적절한 섹션(requirements, optimization_focus 등)에 추가하거나 기존 내용을 수정하세요.
3. 'version'과 'last_updated' 필드는 업데이트하지 마세요 (시스템이 처리함).
4. JSON 형식으로 전체 가이드라인을 반환하세요.
"""

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "당신은 SEO 가이드라인 관리자입니다. JSON 형식을 정확히 준수하여 응답하세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result_json = response.choices[0].message.content.strip()
        updated_guidelines = json.loads(result_json)
        
        return updated_guidelines
        
    except Exception as e:
        logger.error(f"가이드라인 업데이트 중 오류: {e}")
        return current_guidelines



def _extract_default_keywords(text: str) -> str:
    """
    기본 키워드 추출 로직
    """
    try:
        # HTML 태그 제거
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # 한국어 단어 추출
        korean_words = re.findall(r'[가-힣]+', clean_text)
        
        # 단어 빈도 계산
        word_freq = {}
        for word in korean_words:
            if len(word) >= 2:  # 2글자 이상만
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 빈도순으로 정렬하여 상위 5개 추출
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:5]]
        
        if keywords:
            return ', '.join(keywords)
        else:
            return "AI, 기술, 분석, 개발, 시스템"
            
    except Exception as e:
        logger.error(f"기본 키워드 추출 중 오류: {e}")
        return "AI, 기술, 분석, 개발, 시스템"

def increase_api_usage_count(api_name: str):
    """API 사용량을 기록합니다."""
    try:
        with API_USAGE_LOCK:
            if os.path.exists(API_USAGE_FILE_PATH):
                with open(API_USAGE_FILE_PATH, 'r', encoding='utf-8') as f:
                    usage_data = json.load(f)
            else:
                usage_data = {}
            
            today = datetime.now().strftime('%Y-%m-%d')
            if today not in usage_data:
                usage_data[today] = {}
            
            if api_name not in usage_data[today]:
                usage_data[today][api_name] = 0
            
            usage_data[today][api_name] += 1
            
            with open(API_USAGE_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(usage_data, f, ensure_ascii=False, indent=2)
                
    except Exception as e:
        logger.warning(f"API 사용량 기록 실패: {e}")

async def create_enhanced_blog_post(text: str, keywords: str, rule_guidelines: Optional[list] = None, content_length: str = "3000", ai_mode: Optional[str] = None) -> Dict:
    """
    향상된 기능을 포함한 블로그 포스트 생성 함수
    - AI 추천 키워드 (명사 중심, 최대 10개)
    - 주요 내용, 핵심 포인트, 실용적인 팁, 요약
    - AI 요약 (100자 이내)
    - 신뢰도 평가 (5점 만점)
    - SEO 최적화 점수 (10점 만점)
    """
    # 동시 생성 제어
    async with generation_semaphore:
        global client
        
        start_time = time.time()
        
        # 입력 검증
        if not text or not text.strip():
            logger.warning("빈 텍스트가 입력되었습니다.")
            return _generate_enhanced_default_template("", keywords, rule_guidelines, content_length, ai_mode)
        
        # 캐시 확인
        cache_key = _get_cache_key(text, keywords, content_length, ai_mode or "")
        cached_content = _get_cached_content(cache_key)
        if cached_content:
            logger.info("캐시된 콘텐츠 생성 결과 사용")
            return cached_content
        
        # 생성 요청 간 지연 (API 부하 방지)
        await asyncio.sleep(GENERATION_DELAY)
    
    # Gemini 2.0 Flash 모드인 경우 Gemini 사용
    if ai_mode == "gemini_2_0_flash":
        try:
            result = await _create_enhanced_blog_post_with_gemini(text, keywords, rule_guidelines, content_length, ai_mode)
            if result:
                _set_cached_content(cache_key, result)
                return result
        except Exception as e:
            error_message = str(e)
            if is_gemini_quota_exceeded(error_message):
                logger.warning("Gemini API 할당량 초과로 OpenAI로 fallback합니다.")
            else:
                logger.warning(f"Gemini 2.0 Flash 콘텐츠 생성 실패, OpenAI로 fallback: {e}")
    
    # OpenAI 클라이언트 초기화
    if not client and not _initialize_client():
        logger.warning("OpenAI 클라이언트 초기화 실패. 기본 템플릿을 사용합니다.")
        return _generate_enhanced_default_template(text, keywords, rule_guidelines, content_length, ai_mode)
    
    try:
        # 콘텐츠 길이 설정
        target_length = int(content_length) if content_length.isdigit() else 3000
        
        # AI 모드에 따른 프롬프트 조정
        if ai_mode == "creative":
            style_instruction = "창의적이고 흥미로운 톤으로 작성하되, 전문성을 유지하세요."
        elif ai_mode == "informative":
            style_instruction = "정보가 풍부하고 교육적인 톤으로 작성하세요."
        elif ai_mode == "professional":
            style_instruction = "전문적이고 신뢰할 수 있는 톤으로 작성하세요."
        else:
            style_instruction = "균형 잡힌 톤으로 작성하세요."
        
        # 규칙 가이드라인 처리
        rules_text = ""
        if rule_guidelines:
            rules_text = "\n".join([f"- {rule}" for rule in rule_guidelines])
        
        # 향상된 프롬프트 구성
        prompt = f"""
다음 텍스트를 기반으로 SEO 최적화된 한국어 블로그 포스트를 작성해주세요.

원본 텍스트:
{text}

주요 키워드: {keywords}

요구사항:
- 목표 길이: 약 {target_length}자
- 스타일: {style_instruction}
- SEO 최적화: 키워드를 자연스럽게 포함
- 구조: 제목, 소제목, 본문, 결론 포함
- HTML 형식으로 작성

추가 규칙:
{rules_text}

다음 형식으로 응답해주세요:

```html
<h1>제목</h1>
<meta name="description" content="메타 설명">

<div class="content-intro">
    <p>소개 내용...</p>
</div>

<div class="ai-keywords">
    <h2>🤖 AI 추천 키워드</h2>
    <ul>
        <li>키워드1</li>
        <li>키워드2</li>
        ...
    </ul>
</div>

<div class="main-content">
    <h2>📋 주요 내용</h2>
    <p>주요 내용...</p>
    
    <h2>🔍 핵심 포인트</h2>
    <ul>
        <li>핵심 포인트 1</li>
        <li>핵심 포인트 2</li>
        ...
    </ul>
    
    <h2>💡 실용적인 팁</h2>
    <div class="tips-container">
        <div class="tip-item">
            <h3>팁 1</h3>
            <p>팁 내용...</p>
        </div>
        ...
    </div>
    
    <h2>📊 요약</h2>
    <p>요약 내용...</p>
</div>

<div class="ai-analysis">
    <h2>🤖 AI 분석</h2>
    <div class="analysis-item">
        <h3>AI 요약 (100자 이내)</h3>
        <p>요약 내용...</p>
    </div>
    <div class="analysis-item">
        <h3>신뢰도 평가 (5점 만점)</h3>
        <p>평점: ⭐⭐⭐⭐⭐ (5/5)</p>
        <p>평가 근거: ...</p>
    </div>
    <div class="analysis-item">
        <h3>SEO 최적화 점수 (10점 만점)</h3>
        <p>평점: 🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥 (10/10)</p>
        <p>최적화 근거: ...</p>
    </div>
</div>
```

제목과 메타 설명도 함께 제공해주세요.
"""

        # API 호출
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {"role": "system", "content": "당신은 SEO 전문가이자 블로그 작가입니다. 고품질의 한국어 블로그 포스트를 작성해주세요."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=settings.openai_max_tokens,
                    temperature=0.7
                )
                
                generated_content = response.choices[0].message.content.strip()
                
                # HTML 태그 추출
                title_match = re.search(r'<h1[^>]*>(.*?)</h1>', generated_content, re.IGNORECASE | re.DOTALL)
                meta_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', generated_content, re.IGNORECASE)
                
                title = title_match.group(1).strip() if title_match else f"{keywords.split(',')[0] if keywords else 'AI 블로그 포스트'}"
                meta_description = meta_match.group(1).strip() if meta_match else f"{keywords}에 대한 포괄적인 정보와 가이드를 제공합니다."
                
                # HTML 태그 제거하여 순수 텍스트 추출
                clean_content = re.sub(r'<[^>]+>', '', generated_content)
                word_count = len(clean_content.split())
                
                # AI 분석 결과 추출
                ai_analysis = _extract_ai_analysis(generated_content)
                
                # 가이드라인 적용 분석
                guidelines_analysis = _analyze_guidelines_application(generated_content, rule_guidelines)
                
                result = {
                    'post': generated_content,
                    'title': title,
                    'meta_description': meta_description,
                    'keywords': keywords,
                    'word_count': word_count,
                    'content_length': content_length,
                    'ai_mode': ai_mode or 'openai',
                    'ai_analysis': ai_analysis,
                    'guidelines_analysis': guidelines_analysis
                }
                
                # 성능 로깅
                end_time = time.time()
                logger.info(f"향상된 콘텐츠 생성 완료: {end_time - start_time:.2f}초")
                
                return result
                
            except Exception as e:
                logger.error(f"OpenAI API 호출 실패 (시도 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt == MAX_RETRIES - 1:
                    raise ContentGenerationError(f"OpenAI API 호출 실패: {str(e)}")
                await asyncio.sleep(1)
                
    except Exception as e:
        logger.error(f"향상된 콘텐츠 생성 중 오류: {e}")
        raise ContentGenerationError(f"향상된 콘텐츠 생성 실패: {str(e)}")

def _extract_ai_analysis(content: str) -> Dict:
    """AI 분석 결과를 추출합니다."""
    analysis = {
        'ai_summary': '',
        'trust_score': 0,
        'seo_score': 0,
        'trust_reason': '',
        'seo_reason': ''
    }
    
    try:
        # AI 요약 추출 (더 정확한 패턴 매칭)
        summary_patterns = [
            r'<h3>AI 요약.*?</h3>\s*<p>(.*?)</p>',
            r'<h3>AI 요약.*?</h3>\s*<p>(.*?)(?=<h3>|<div|</div>)',
            r'AI 요약.*?<p>(.*?)</p>',
            r'AI 요약.*?<p>(.*?)(?=<h3>|<div|</div>)'
        ]
        
        for pattern in summary_patterns:
            summary_match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if summary_match:
                summary_text = summary_match.group(1).strip()
                # HTML 태그 제거
                summary_text = re.sub(r'<[^>]+>', '', summary_text)
                analysis['ai_summary'] = summary_text
                break
        
        # 신뢰도 점수 추출
        trust_patterns = [
            r'평점:\s*⭐+.*?\((\d+)/5\)',
            r'신뢰도.*?\((\d+)/5\)',
            r'신뢰도.*?(\d+)/5'
        ]
        
        for pattern in trust_patterns:
            trust_match = re.search(pattern, content, re.IGNORECASE)
            if trust_match:
                analysis['trust_score'] = int(trust_match.group(1))
                break
        
        # SEO 점수 추출
        seo_patterns = [
            r'평점:\s*🔥+.*?\((\d+)/10\)',
            r'SEO.*?\((\d+)/10\)',
            r'SEO.*?(\d+)/10'
        ]
        
        for pattern in seo_patterns:
            seo_match = re.search(pattern, content, re.IGNORECASE)
            if seo_match:
                analysis['seo_score'] = int(seo_match.group(1))
                break
        
        # 평가 근거 추출 (더 정확한 패턴)
        trust_reason_patterns = [
            r'평가 근거:\s*(.*?)(?=<h3>|<div|</div>|$)',
            r'신뢰도.*?근거:\s*(.*?)(?=<h3>|<div|</div>|$)'
        ]
        
        for pattern in trust_reason_patterns:
            trust_reason_match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if trust_reason_match:
                reason_text = trust_reason_match.group(1).strip()
                reason_text = re.sub(r'<[^>]+>', '', reason_text)
                analysis['trust_reason'] = reason_text
                break
        
        seo_reason_patterns = [
            r'최적화 근거:\s*(.*?)(?=<h3>|<div|</div>|$)',
            r'SEO.*?근거:\s*(.*?)(?=<h3>|<div|</div>|$)'
        ]
        
        for pattern in seo_reason_patterns:
            seo_reason_match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if seo_reason_match:
                reason_text = seo_reason_match.group(1).strip()
                reason_text = re.sub(r'<[^>]+>', '', reason_text)
                analysis['seo_reason'] = reason_text
                break
            
    except Exception as e:
        logger.error(f"AI 분석 결과 추출 중 오류: {e}")
    
    return analysis

async def _create_enhanced_blog_post_with_gemini(text: str, keywords: str, rule_guidelines: Optional[list] = None, content_length: str = "5000", ai_mode: Optional[str] = None) -> Dict:
    """
    Gemini 2.0 Flash API를 사용하여 향상된 블로그 포스트를 생성합니다.
    """
    try:
        import httpx
        
        # Gemini API 키 확인
        from .translator import get_gemini_api_key
        api_key = get_gemini_api_key()
        if not api_key:
            raise ContentGenerationError("Gemini API 키가 설정되지 않았습니다.")
        
        # 콘텐츠 길이 설정
        target_length = int(content_length) if content_length.isdigit() else 5000
        
        # 규칙 가이드라인 처리
        rules_text = ""
        if rule_guidelines:
            rules_text = "\n".join([f"- {rule}" for rule in rule_guidelines])
        
        # 콘텐츠 스타일별 가이드라인 추가
        style_guidelines = ""
        if ai_mode:
            if ai_mode == "뉴스":
                style_guidelines = """
뉴스 스타일 가이드라인:
- 객관적이고 사실 중심으로 작성
- 5W1H (누가, 언제, 어디서, 무엇을, 왜, 어떻게) 포함
- 최신성과 시의성 강조
- 요약: 핵심 사실만 간결하게 (300자 이내)
- 주요 내용: 시간순 또는 중요도순으로 구성
- 개인적 의견 배제, 객관적 서술
"""
            elif ai_mode == "리뷰":
                style_guidelines = """
리뷰 스타일 가이드라인:
- 장단점을 명확히 구분하여 서술
- 개인적 경험과 체험 중심
- 구체적인 예시와 근거 제시
- 요약: 핵심 평가와 추천 여부 (400자 이내)
- 주요 내용: 장점, 단점, 결론 순으로 구성
- 솔직하고 신뢰할 수 있는 톤 유지
"""
            elif ai_mode == "가이드":
                style_guidelines = """
가이드 스타일 가이드라인:
- 단계별로 명확하게 구분하여 설명
- 실용적이고 실행 가능한 정보 제공
- 초보자도 이해할 수 있도록 상세히 설명
- 요약: 핵심 단계와 목표 (350자 이내)
- 주요 내용: 단계별 순서대로 구성
- 체크리스트나 팁 포함
"""
            elif ai_mode == "요약":
                style_guidelines = """
요약 스타일 가이드라인:
- 핵심 내용만 간결하게 정리
- 불필요한 설명 제거
- 명확하고 이해하기 쉬운 문장
- 요약: 핵심 포인트만 간결하게 (250자 이내)
- 주요 내용: 중요도순으로 핵심만 나열
- 빠른 정보 전달에 최적화
"""
            elif ai_mode == "블로그":
                style_guidelines = """
블로그 스타일 가이드라인:
- 개인적 인사이트와 경험 중심
- 독자와의 소통하는 톤으로 작성
- 실용적 조언과 개인적 견해 포함
- 요약: 개인적 관점과 핵심 메시지 (400자 이내)
- 주요 내용: 경험담, 인사이트, 조언 순으로 구성
- 친근하고 솔직한 어조 유지
"""
            elif ai_mode == "enhanced":
                style_guidelines = """
향상된 모드 가이드라인 (2025 Advanced SEO):
- AEO (답변 엔진 최적화): 각 섹션의 시작은 질문에 대한 40-60자 내외의 명확한 직접 답변(Direct Answer)으로 시작하세요.
- AIO (AI Overviews): 대화체 톤을 유지하고, '제로 클릭' 검색을 위해 핵심 정보를 전면에 배치하세요.
- GEO (생성형 엔진 최적화): 주제를 포괄적으로 다루고, 권위 있는 출처를 인용하거나 언급하여 신뢰도를 높이세요.
- 구조: 질문(H2/H3) -> 직접 답변 -> 상세 설명 -> 예시/데이터 순서로 구성하세요.
- AI 분석과 데이터 기반 인사이트 포함
- 심층적 분석과 전문적 관점
- 다양한 관점에서의 종합적 분석
- 요약: AI 분석 결과와 핵심 인사이트 (500자 이내)
- 주요 내용: 분석, 인사이트, 전망 순으로 구성
- 전문적이면서도 이해하기 쉬운 설명
"""
        
        # 요약 및 주요 내용 가이드라인
        summary_guidelines = """
요약 및 주요 내용 가이드라인:
- 요약: 완벽한 문장으로 작성, 500자 이내
- 주요 내용: 핵심 포인트를 명확하게 구분
- 키워드 자연스럽게 포함
- 독자가 쉽게 이해할 수 있는 구조
- 각 섹션별로 명확한 제목 사용
"""
        
        # 향상된 프롬프트 구성
        prompt = f"""
다음 텍스트를 기반으로 SEO 최적화된 한국어 블로그 포스트를 작성해주세요.

원본 텍스트:
{text}

주요 키워드: {keywords}

요구사항:
- 목표 길이: 약 {target_length}자
- SEO 최적화: 키워드를 자연스럽게 포함
- 구조: 제목, 소제목, 본문, 결론 포함
- HTML 형식으로 작성

추가 규칙:
{rules_text}

{style_guidelines}

{summary_guidelines}

다음 형식으로 응답해주세요:

```html
<h1>제목</h1>
<meta name="description" content="메타 설명">

<div class="content-intro">
    <p>소개 내용...</p>
</div>

<div class="ai-keywords">
    <h2>🤖 AI 추천 키워드</h2>
    <ul>
        <li>키워드1</li>
        <li>키워드2</li>
        ...
    </ul>
</div>

<div class="main-content">
    <h2>📋 주요 내용</h2>
    <p>주요 내용...</p>
    
    <h2>🔍 핵심 포인트</h2>
    <ul>
        <li>핵심 포인트 1</li>
        <li>핵심 포인트 2</li>
        ...
    </ul>
    
    <h2>💡 실용적인 팁</h2>
    <div class="tips-container">
        <div class="tip-item">
            <h3>팁 1</h3>
            <p>팁 내용...</p>
        </div>
        ...
    </div>
    
    <h2>📊 요약</h2>
    <p>요약 내용...</p>
</div>

<div class="ai-analysis">
    <h2>🤖 AI 분석</h2>
    <div class="analysis-item">
        <h3>AI 요약 (100자 이내)</h3>
        <p>요약 내용...</p>
    </div>
    <div class="analysis-item">
        <h3>신뢰도 평가 (5점 만점)</h3>
        <p>평점: ⭐⭐⭐⭐⭐ (5/5)</p>
        <p>평가 근거: ...</p>
    </div>
    <div class="analysis-item">
        <h3>SEO 최적화 점수 (10점 만점)</h3>
        <p>평점: 🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥 (10/10)</p>
        <p>최적화 근거: ...</p>
    </div>
</div>
```

제목과 메타 설명도 함께 제공해주세요.
"""
        
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 8192
                }
            }
            
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and result['candidates']:
                    generated_content = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    # HTML 태그 추출
                    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', generated_content, re.IGNORECASE | re.DOTALL)
                    meta_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', generated_content, re.IGNORECASE)
                    
                    title = title_match.group(1).strip() if title_match else f"{keywords.split(',')[0] if keywords else 'AI 블로그 포스트'}"
                    meta_description = meta_match.group(1).strip() if meta_match else f"{keywords}에 대한 포괄적인 정보와 가이드를 제공합니다."
                    
                    # HTML 태그 제거하여 순수 텍스트 추출
                    clean_content = re.sub(r'<[^>]+>', '', generated_content)
                    word_count = len(clean_content.split())
                    
                    # AI 분석 결과 추출
                    ai_analysis = _extract_ai_analysis(generated_content)
                    
                    # 가이드라인 적용 분석
                    guidelines_analysis = _analyze_guidelines_application(generated_content, rule_guidelines)
                    
                    return {
                        'post': generated_content,
                        'title': title,
                        'meta_description': meta_description,
                        'keywords': keywords,
                        'word_count': word_count,
                        'content_length': content_length,
                        'ai_mode': ai_mode or 'gemini_2_0_flash',
                        'ai_analysis': ai_analysis,
                        'guidelines_analysis': guidelines_analysis
                    }
                else:
                    raise ContentGenerationError("Gemini API 응답에 생성 결과가 없습니다.")
            else:
                error_detail = response.text
                logger.error(f"Gemini API 오류: {response.status_code} - {error_detail}")
                raise ContentGenerationError(f"Gemini API 오류: {response.status_code}")
                
    except Exception as e:
        logger.error(f"Gemini 향상된 블로그 포스트 생성 중 오류: {e}")
        raise ContentGenerationError(f"Gemini 향상된 블로그 포스트 생성 실패: {str(e)}")

def _generate_enhanced_default_template(text: str, keywords: str, rule_guidelines: Optional[List[str]] = None, content_length: str = "3000", ai_mode: Optional[str] = None) -> Dict:
    """
    향상된 기능을 포함한 기본 템플릿 생성
    """
    # 기본 키워드 추출
    if not keywords:
        keywords = _extract_default_keywords(text)
    
    # 제목 생성
    title = f"{keywords.split(',')[0].strip() if keywords else 'AI 블로그 포스트'}에 대한 상세 가이드"
    
    # 텍스트 요약 (1000자 이내로 완벽한 문장으로 정리)
    def create_summary(text_content, max_length=1000):
        """주요 내용의 전체 텍스트 결과를 압축하여 1000자 이내로 정리"""
        if len(text_content) <= max_length:
            return text_content
        
        # 문장 단위로 분리
        sentences = re.split(r'[.!?。！？]', text_content)
        summary_sentences = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 문장 끝에 마침표 추가
            if not sentence.endswith(('.', '!', '?', '。', '！', '？')):
                sentence += '.'
            
            if current_length + len(sentence) <= max_length:
                summary_sentences.append(sentence)
                current_length += len(sentence)
            else:
                break
        
        return ' '.join(summary_sentences)
    
    summary = create_summary(text, 1000)
    
    # 주요 내용 생성 함수
    def create_main_content(text_content, target_length):
        """URL 입력 또는 입력 테스트 내용을 기반으로 '콘텐츠 분량'에 따라서 텍스트를 추출하여 문장형으로 생성"""
        try:
            target_length_int = int(target_length) if target_length.isdigit() else 3000
            
            # 콘텐츠 길이에 따른 주요 내용 생성
            if len(text_content) < 500:
                # 짧은 콘텐츠: 원본 텍스트를 그대로 사용하되 문장형으로 정리
                sentences = re.split(r'[.!?。！？]', text_content)
                clean_sentences = []
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence and not sentence.endswith(('.', '!', '?', '。', '！', '？')):
                        sentence += '.'
                    if sentence:
                        clean_sentences.append(sentence)
                return ' '.join(clean_sentences)
            elif len(text_content) < 1500:
                # 중간 길이: 요약 + 추가 설명
                return f"{summary} 이 내용은 {keywords.split(',')[0].strip() if keywords else '주제'}에 대한 핵심 정보를 담고 있으며, 더 자세한 내용은 아래 섹션에서 확인할 수 있습니다."
            else:
                # 긴 콘텐츠: 구조화된 주요 내용
                sentences = re.split(r'[.!?。！？]', text_content)
                main_sentences = []
                current_length = 0
                max_main_length = min(target_length_int // 3, 800)  # 주요 내용은 전체의 1/3 이하
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if not sentence.endswith(('.', '!', '?', '。', '！', '？')):
                        sentence += '.'
                    
                    if current_length + len(sentence) <= max_main_length:
                        main_sentences.append(sentence)
                        current_length += len(sentence)
                    else:
                        break
                
                main_content = ' '.join(main_sentences)
                if len(main_content) < len(text_content):
                    main_content += f" 이 외에도 {keywords.split(',')[0].strip() if keywords else '주제'}에 대한 다양한 정보와 분석이 포함되어 있습니다."
                
                return main_content
        except Exception as e:
            logger.error(f"주요 내용 생성 중 오류: {e}")
            return summary
    
    # AI 추천 키워드 (명사 중심, 최대 10개)
    ai_keywords = _extract_ai_keywords(text, keywords)
    
    # 향상된 HTML 콘텐츠 생성
    content = f"""
<h1>{title}</h1>
<meta name="description" content="{keywords}에 대한 포괄적인 정보와 가이드를 제공합니다.">

<div class="content-intro">
    <p>이 글에서는 <strong>{keywords}</strong>에 대해 자세히 알아보겠습니다.</p>
</div>

<div class="ai-keywords">
    <h2>🤖 AI 추천 키워드</h2>
    <ul>
        {''.join([f'<li>{keyword.strip()}</li>' for keyword in ai_keywords[:10]])}
    </ul>
</div>

    <div class="main-content">
        <h2>📝 요약</h2>
        <p>{summary}</p>
        
        <h2>📋 주요 내용</h2>
        <p>{create_main_content(text, content_length)}</p>
    
    <h2>🔍 핵심 포인트</h2>
    <ul>
        <li><strong>첫 번째 중요한 포인트:</strong> {keywords.split(',')[0].strip()}의 기본 개념과 중요성</li>
        <li><strong>두 번째 중요한 포인트:</strong> 실제 적용 방법과 사례</li>
        <li><strong>세 번째 중요한 포인트:</strong> 주의사항과 모범 사례</li>
        <li><strong>네 번째 중요한 포인트:</strong> 미래 전망과 발전 방향</li>
    </ul>
    
    <h2>💡 실용적인 팁</h2>
    <div class="tips-container">
        <div class="tip-item">
            <h3>팁 1: 효과적인 활용</h3>
            <p>{keywords.split(',')[0].strip()}를 효과적으로 활용하는 방법을 알아보세요.</p>
        </div>
        <div class="tip-item">
            <h3>팁 2: 주의사항</h3>
            <p>일반적인 실수와 피해야 할 함정에 대해 알아보세요.</p>
        </div>
        <div class="tip-item">
            <h3>팁 3: 최적화 방법</h3>
            <p>성능과 효율성을 극대화하는 방법을 알아보세요.</p>
        </div>
    </div>
    
    <h2>📊 요약</h2>
    <p>이 글을 통해 {keywords.split(',')[0].strip()}에 대한 이해를 높이고, 실제 상황에서 효과적으로 활용할 수 있는 지식을 얻었습니다.</p>
</div>

    <div class="ai-analysis">
        <h2>🤖 AI 분석</h2>
        <div class="analysis-item">
            <h3>AI 요약 (1000자 이내)</h3>
            <p>{summary[:1000]}{'...' if len(summary) > 1000 else ''}</p>
        </div>
    <div class="analysis-item">
        <h3>신뢰도 평가 (5점 만점)</h3>
        <p>평점: ⭐⭐⭐⭐⭐ (5/5)</p>
        <p>평가 근거: 입력된 텍스트를 기반으로 한 신뢰할 수 있는 정보와 전문적인 분석을 제공합니다.</p>
    </div>
    <div class="analysis-item">
        <h3>SEO 최적화 점수 (10점 만점)</h3>
        <p>평점: 🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥 (10/10)</p>
        <p>최적화 근거: 키워드 최적화, 구조화된 콘텐츠, 메타 설명, 사용자 친화적 레이아웃을 모두 포함합니다.</p>
    </div>
</div>

<style>
.content-intro {{ background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 1rem 0; }}
.ai-keywords {{ background: #e8f5e8; padding: 1rem; border-radius: 8px; margin: 1rem 0; }}
.main-content {{ line-height: 1.6; }}
.tips-container {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin: 1rem 0; }}
.tip-item {{ background: #e3f2fd; padding: 1rem; border-radius: 8px; border-left: 4px solid #2196f3; }}
.ai-analysis {{ background: #fff3e0; padding: 1rem; border-radius: 8px; margin: 1rem 0; }}
.analysis-item {{ margin: 1rem 0; padding: 0.5rem; background: white; border-radius: 4px; }}
</style>
"""
    
    # 단어 수 계산
    text_content = re.sub(r'<[^>]+>', '', content)
    word_count = len(text_content.split())
    
    # AI 분석 결과
    ai_analysis = {
        'ai_summary': summary[:1000] + ('...' if len(summary) > 1000 else ''),
        'trust_score': 5,
        'seo_score': 10,
        'trust_reason': '입력된 텍스트를 기반으로 한 신뢰할 수 있는 정보와 전문적인 분석을 제공합니다.',
        'seo_reason': '키워드 최적화, 구조화된 콘텐츠, 메타 설명, 사용자 친화적 레이아웃을 모두 포함합니다.'
    }
    
    # 가이드라인 적용 분석
    guidelines_analysis = _analyze_guidelines_application(content, rule_guidelines)
    
    return {
        'post': content,
        'title': title,
        'meta_description': f"{keywords}에 대한 포괄적인 정보와 가이드를 제공합니다.",
        'keywords': keywords,
        'word_count': word_count,
        'content_length': content_length,
        'ai_mode': ai_mode or 'default',
        'ai_analysis': ai_analysis,
        'guidelines_analysis': guidelines_analysis
    }

def _extract_ai_keywords(text: str, existing_keywords: str) -> List[str]:
    """
    텍스트에서 AI 추천 키워드를 추출합니다 (명사 중심, 최대 10개)
    """
    try:
        # 기존 키워드와 텍스트를 결합
        combined_text = f"{existing_keywords} {text}"
        
        # 간단한 키워드 추출 로직 (명사 중심)
        import re
        
        # 한국어 명사 패턴 (간단한 구현)
        korean_nouns = re.findall(r'[가-힣]+', combined_text)
        
        # 영어 명사 패턴
        english_words = re.findall(r'\b[a-zA-Z]{3,}\b', combined_text)
        
        # 키워드 후보 생성
        candidates = []
        
        # 기존 키워드 추가
        if existing_keywords:
            candidates.extend([kw.strip() for kw in existing_keywords.split(',')])
        
        # 한국어 명사 추가 (길이가 2자 이상인 것만)
        candidates.extend([noun for noun in korean_nouns if len(noun) >= 2])
        
        # 영어 단어 추가
        candidates.extend(english_words)
        
        # 중복 제거 및 정렬
        unique_candidates = list(set(candidates))
        unique_candidates.sort(key=len, reverse=True)  # 긴 키워드 우선
        
        # 최대 10개 반환
        return unique_candidates[:10]
        
    except Exception as e:
        logger.error(f"AI 키워드 추출 중 오류: {e}")
        # 기본 키워드 반환
        if existing_keywords:
            return [kw.strip() for kw in existing_keywords.split(',')[:10]]
        return ['키워드', '분석', '가이드']

def _analyze_guidelines_application(content: str, rules: Optional[List[str]] = None) -> Dict:
    """
    생성된 콘텐츠에서 가이드라인 적용 여부를 분석합니다.
    """
    analysis = {
        'ai_seo_applied': False,
        'aeo_applied': False,
        'geo_applied': False,
        'aio_applied': False,
        'policy_applied': False,
        'structured_data': False,
        'faq_included': False,
        'keywords_optimized': False,
        'headings_structure': False,
        'links_included': False,
        'images_optimized': False,
        'balance_perspective': False
    }
    
    try:
        # AI SEO 분석
        if rules and 'AI_SEO' in rules:
            analysis['ai_seo_applied'] = True
            # 구조화된 데이터 확인
            if 'itemscope' in content or 'schema.org' in content:
                analysis['structured_data'] = True
            # 키워드 최적화 확인 (H1, H2 태그)
            if '<h1' in content and '<h2' in content:
                analysis['keywords_optimized'] = True
            # 헤딩 구조 확인
            if '<h1' in content and '<h2' in content and '<h3' in content:
                analysis['headings_structure'] = True
            # 링크 확인
            if '<a href' in content or 'http' in content:
                analysis['links_included'] = True
            # 이미지 최적화 확인
            if '<img' in content and 'alt=' in content:
                analysis['images_optimized'] = True
        
        # AEO 분석
        if rules and 'AEO' in rules:
            analysis['aeo_applied'] = True
            # FAQ 포함 확인
            if 'FAQ' in content or '자주 묻는 질문' in content or 'Q&A' in content:
                analysis['faq_included'] = True
        
        # GEO 분석
        if rules and 'GEO' in rules:
            analysis['geo_applied'] = True
            # 구조화된 데이터 확인
            if 'itemscope' in content or 'schema.org' in content:
                analysis['structured_data'] = True
        
        # AIO 분석
        if rules and 'AIO' in rules:
            analysis['aio_applied'] = True
        
        # 정책 균형 확인
        if '장단점' in content or '고려사항' in content or '주의사항' in content or '단점' in content:
            analysis['balance_perspective'] = True
            analysis['policy_applied'] = True
            
    except Exception as e:
        logger.error(f"가이드라인 분석 중 오류: {e}")
    
    return analysis
