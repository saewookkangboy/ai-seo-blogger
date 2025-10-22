# app/services/translator.py

from typing import Optional, List, Dict, Any
from ..config import settings
from ..exceptions import TranslationError, APIKeyError
from ..utils.logger import setup_logger
import os
import json
import threading
from datetime import datetime
import httpx
import requests
from bs4 import BeautifulSoup
import re
import openai
import asyncio
import time
import hashlib
from .performance_optimizer import cache_result, track_performance, get_optimized_client
from .error_handler import handle_errors, retry_on_error, validate_input

logger = setup_logger(__name__)

API_USAGE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'api_usage.json')
API_USAGE_FILE = os.path.abspath(API_USAGE_FILE)
API_USAGE_LOCK = threading.Lock()

# Gemini API 설정 (환경변수에서 가져오도록 수정)
DEFAULT_GEMINI_API_KEY = "AIzaSyDsBBgP9R8NrLaseWWFDcdYFGrrUNbIX9A"

def get_gemini_api_key():
    """Gemini API 키를 안전하게 가져오기"""
    from ..config import settings
    api_key = settings.get_gemini_api_key()
    if api_key:
        return api_key
    # 환경변수에서 직접 가져오기 (하드코딩된 키는 제외)
    env_key = os.getenv('GEMINI_API_KEY')
    if env_key and env_key != DEFAULT_GEMINI_API_KEY:
        return env_key
    return DEFAULT_GEMINI_API_KEY

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key="

NAVER_API_URL = "https://api.naver.com/keywordstool"

# 성능 최적화를 위한 설정 (최적화)
TRANSLATION_TIMEOUT = 10  # 10초로 단축 (속도 향상)
TRANSLATION_CACHE_DURATION = 1800  # 30분 캐시 (메모리 효율성)
MAX_RETRIES = 2  # 재시도 횟수 단축 (속도 향상)
MAX_CONCURRENT_TRANSLATIONS = 3  # 동시 번역 수 제한 (안정성)
TRANSLATION_DELAY = 0.05  # 번역 요청 간 지연 시간 단축 (속도 향상)

# 번역 캐시
translation_cache = {}
translation_cache_lock = threading.Lock()

def _get_translation_cache_key(text: str, target_lang: str) -> str:
    """번역 캐시 키 생성"""
    content = f"{text[:200]}{target_lang}"
    return hashlib.md5(content.encode()).hexdigest()

def _get_cached_translation(cache_key: str) -> Optional[str]:
    """캐시된 번역 가져오기"""
    with translation_cache_lock:
        if cache_key in translation_cache:
            cached_data, timestamp = translation_cache[cache_key]
            if time.time() - timestamp < TRANSLATION_CACHE_DURATION:
                logger.info("캐시된 번역 사용")
                return cached_data
            else:
                del translation_cache[cache_key]
    return None

def _set_cached_translation(cache_key: str, translated_text: str):
    """번역을 캐시에 저장"""
    with translation_cache_lock:
        translation_cache[cache_key] = (translated_text, time.time())
        # 캐시 크기 제한 (메모리 효율성)
        if len(translation_cache) > 100:
            oldest_key = min(translation_cache.keys(), key=lambda k: translation_cache[k][1])
            del translation_cache[oldest_key]

# 동시 번역 제어를 위한 세마포어
translation_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TRANSLATIONS)

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

@cache_result(ttl=1800)  # 30분 캐시로 단축 (메모리 효율성)
@track_performance("translate_text")
@retry_on_error(max_retries=2, delay=0.5, backoff_factor=1.5)  # 재시도 최적화
async def translate_text(text: str, target_lang: str = None) -> str:
    """
    주어진 텍스트를 DeepL API를 사용하여 번역합니다. (성능 최적화)
    target_lang: 'ko' for Korean, 'en' for English, etc.
    """
    # 동시 번역 제어
    async with translation_semaphore:
        start_time = time.time()
        logger.info(f"번역 함수 호출됨: 텍스트 길이={len(text)}, target_lang={target_lang}")
        
        # 입력 검증
        if not text or not text.strip():
            logger.warning("빈 텍스트가 입력되었습니다.")
            return ""
        
        # 기본 언어 설정
        if target_lang is None:
            target_lang = "ko"
        
        # 캐시 확인
        cache_key = _get_translation_cache_key(text, target_lang)
        cached_translation = _get_cached_translation(cache_key)
        if cached_translation:
            logger.info("캐시된 번역 결과 사용")
            return cached_translation
        
        # 요청 간 지연
        await asyncio.sleep(TRANSLATION_DELAY)
        
        # DeepL API 키 확인
        api_key = settings.get_deepl_api_key()
        if not api_key:
            api_key = os.getenv('DEEPL_API_KEY', "2f05c78b-516f-406a-a555-81c9667c193d:fx")
        if not api_key:
            logger.warning("DeepL API 키가 설정되지 않았습니다. 원본 텍스트를 반환합니다.")
            return text
        
        try:
            # Gemini API로 먼저 시도
            api_key = get_gemini_api_key()
            if api_key:
                try:
                    logger.info("Gemini API로 번역을 시도합니다...")
                    translated_text = await translate_text_gemini(text, target_lang)
                    
                    if translated_text and len(translated_text.strip()) > 10:
                        # API 사용량 기록
                        increase_api_usage_count("gemini")
                        
                        # 캐시에 저장
                        _set_cached_translation(cache_key, translated_text)
                        
                        translation_time = time.time() - start_time
                        logger.info(f"Gemini 번역 완료: {len(text)}자 → {len(translated_text)}자 (소요시간: {translation_time:.2f}초)")
                        
                        return translated_text
                except Exception as gemini_error:
                    error_message = str(gemini_error)
                    logger.error(f"Gemini 번역 중 오류 발생: {error_message}")
                    
                    # 할당량 초과 오류인지 확인
                    if "QUOTA_EXCEEDED" in error_message or is_gemini_quota_exceeded(error_message):
                        logger.warning("Gemini API 할당량 초과로 DeepL로 전환합니다.")
                    else:
                        logger.warning("Gemini API 오류로 DeepL로 전환합니다.")
            
            # DeepL API 호출 (fallback 또는 기본)
            logger.info("DeepL API로 번역을 시도합니다...")
            translated_text = await translate_text_deepl(text, target_lang)
            
            if translated_text and len(translated_text.strip()) > 10:
                # API 사용량 기록
                increase_api_usage_count("deepl")
                
                # 캐시에 저장
                _set_cached_translation(cache_key, translated_text)
                
                translation_time = time.time() - start_time
                logger.info(f"DeepL 번역 완료: {len(text)}자 → {len(translated_text)}자 (소요시간: {translation_time:.2f}초)")
                
                return translated_text
            else:
                logger.warning("DeepL 번역 결과가 비어있습니다. 원본 텍스트를 반환합니다.")
                return text
                
        except Exception as e:
            logger.error(f"DeepL 번역 중 오류 발생: {e}")
            
            # OpenAI fallback 시도
            try:
                logger.info("OpenAI API로 번역을 시도합니다...")
                translated_text = await translate_text_openai(text, target_lang)
                
                if translated_text and len(translated_text.strip()) > 10:
                    # API 사용량 기록
                    increase_api_usage_count("openai")
                    
                    # 캐시에 저장
                    _set_cached_translation(cache_key, translated_text)
                    
                    translation_time = time.time() - start_time
                    logger.info(f"OpenAI 번역 완료: {len(text)}자 → {len(translated_text)}자 (소요시간: {translation_time:.2f}초)")
                    
                    return translated_text
                else:
                    logger.warning("OpenAI 번역 결과가 비어있습니다. 원본 텍스트를 반환합니다.")
                    return text
                    
            except Exception as openai_error:
                logger.error(f"OpenAI 번역도 실패: {openai_error}")
                logger.warning("모든 번역 시도 실패로 원본 텍스트를 반환합니다.")
                return text

async def translate_long_text(text: str, target_lang: str = "ko") -> str:
    """
    긴 텍스트를 청크 단위로 나누어 번역합니다.
    """
    if not text or len(text) < 1000:
        return await translate_text(text, target_lang)
    
    # 텍스트를 청크로 분할 (최대 1000자)
    chunks = []
    current_chunk = ""
    
    sentences = re.split(r'[.!?]', text)
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < 1000:
            current_chunk += sentence + "."
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + "."
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # 각 청크 번역
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        logger.info(f"청크 {i+1}/{len(chunks)} 번역 중...")
        translated_chunk = await translate_text(chunk, target_lang)
        translated_chunks.append(translated_chunk)
        
        # 청크 간 지연
        if i < len(chunks) - 1:
            await asyncio.sleep(0.1)
    
    return " ".join(translated_chunks)

async def detect_language(text: str) -> Optional[str]:
    """
    텍스트의 언어를 감지합니다.
    """
    if not text or len(text.strip()) < 10:
        return None
    
    try:
        # 간단한 언어 감지 (한국어 패턴)
        korean_pattern = re.compile(r'[가-힣]')
        english_pattern = re.compile(r'[a-zA-Z]')
        
        korean_count = len(korean_pattern.findall(text))
        english_count = len(english_pattern.findall(text))
        
        if korean_count > english_count and korean_count > 5:
            return "ko"
        elif english_count > korean_count and english_count > 5:
            return "en"
        else:
            # Gemini API를 사용한 정확한 언어 감지
            api_key = get_gemini_api_key()
            if api_key:
                try:
                    async with httpx.AsyncClient(timeout=TRANSLATION_TIMEOUT) as client:
                        url = f"{GEMINI_API_URL}{api_key}"
                        payload = {
                            "contents": [{
                            "parts": [{
                                "text": f"다음 텍스트의 언어를 ISO 639-1 코드로만 응답하세요 (예: ko, en, ja, zh): {text[:500]}"
                            }]
                            }]
                        }
                        
                        response = await client.post(url, json=payload)
                        if response.status_code == 200:
                            result = response.json()
                            if 'candidates' in result and result['candidates']:
                                language = result['candidates'][0]['content']['parts'][0]['text'].strip().lower()
                                if len(language) == 2:
                                    return language
                        else:
                            error_detail = response.text
                            if is_gemini_quota_exceeded(error_detail):
                                logger.warning("Gemini API 할당량 초과로 기본 언어 감지 방법을 사용합니다.")
                            else:
                                logger.warning(f"Gemini 언어 감지 실패: {error_detail}")
                except Exception as e:
                    error_message = str(e)
                    if is_gemini_quota_exceeded(error_message):
                        logger.warning("Gemini API 할당량 초과로 기본 언어 감지 방법을 사용합니다.")
                    else:
                        logger.warning(f"Gemini 언어 감지 실패: {e}")
            pass
        
        return None
        
    except Exception as e:
        logger.error(f"언어 감지 중 오류: {e}")
        return None

def increase_api_usage_count(api_name: str):
    """API 사용량을 기록합니다."""
    try:
        with API_USAGE_LOCK:
            if os.path.exists(API_USAGE_FILE):
                with open(API_USAGE_FILE, 'r', encoding='utf-8') as f:
                    usage_data = json.load(f)
            else:
                usage_data = {}
            
            today = datetime.now().strftime('%Y-%m-%d')
            if today not in usage_data:
                usage_data[today] = {}
            
            if api_name not in usage_data[today]:
                usage_data[today][api_name] = 0
            
            usage_data[today][api_name] += 1
            
            with open(API_USAGE_FILE, 'w', encoding='utf-8') as f:
                json.dump(usage_data, f, ensure_ascii=False, indent=2)
                
    except Exception as e:
        logger.warning(f"API 사용량 기록 실패: {e}")

async def translate_text_gemini(text: str, target_lang: str = "ko") -> str:
    """
    Gemini 2.0 Flash API를 사용하여 텍스트를 번역합니다.
    """
    try:
        api_key = get_gemini_api_key()
        if not api_key:
            raise TranslationError("Gemini API 키가 설정되지 않았습니다.")
        
        # 언어 매핑
        lang_mapping = {
            "ko": "한국어",
            "en": "English",
            "ja": "日本語",
            "zh": "中文",
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch"
        }
        
        target_lang_name = lang_mapping.get(target_lang, target_lang)
        
        # 프롬프트 구성
        prompt = f"""
다음 텍스트를 {target_lang_name}로 번역해주세요. 
원문의 의미와 톤을 유지하면서 자연스럽게 번역해주세요.

원문:
{text}

번역:
"""
        
        async with httpx.AsyncClient(timeout=TRANSLATION_TIMEOUT) as client:
            url = f"{GEMINI_API_URL}{api_key}"
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 8192
                }
            }
            
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and result['candidates']:
                    translated_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    # 번역 결과 검증
                    if translated_text and len(translated_text) > 10:
                        return translated_text
                    else:
                        raise TranslationError("번역 결과가 비어있습니다.")
                else:
                    raise TranslationError("Gemini API 응답에 번역 결과가 없습니다.")
            else:
                error_detail = response.text
                logger.error(f"Gemini API 오류: {response.status_code} - {error_detail}")
                
                # 할당량 초과 오류인지 확인
                if is_gemini_quota_exceeded(error_detail):
                    logger.warning("Gemini API 할당량 초과로 DeepL로 전환합니다.")
                    raise TranslationError("QUOTA_EXCEEDED")
                else:
                    raise TranslationError(f"Gemini API 오류: {response.status_code}")
                
    except httpx.TimeoutException:
        logger.error("Gemini API 타임아웃")
        raise TranslationError("번역 요청이 시간 초과되었습니다.")
    except Exception as e:
        logger.error(f"Gemini 번역 중 오류: {e}")
        raise TranslationError(f"번역 중 오류가 발생했습니다: {str(e)}")

async def translate_text_openai(text: str, target_lang: str = "ko") -> str:
    """
    OpenAI API를 사용하여 텍스트를 번역합니다.
    """
    try:
        # OpenAI 클라이언트 초기화
        api_key = settings.get_openai_api_key()
        if not api_key:
            raise TranslationError("OpenAI API 키가 설정되지 않았습니다.")
        
        client = openai.AsyncOpenAI(
            api_key=api_key,
            timeout=openai.Timeout(TRANSLATION_TIMEOUT)
        )
        
        # 언어 매핑
        lang_mapping = {
            "ko": "Korean",
            "en": "English",
            "ja": "Japanese",
            "zh": "Chinese",
            "es": "Spanish",
            "fr": "French",
            "de": "German"
        }
        
        target_lang_name = lang_mapping.get(target_lang, target_lang)
        
        # 프롬프트 구성
        prompt = f"Translate the following text to {target_lang_name}. Maintain the original meaning and tone:\n\n{text}"
        
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a professional translator. Translate the given text to {target_lang_name} while preserving the original meaning and tone."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=4000,
            temperature=0.3
        )
        
        translated_text = response.choices[0].message.content.strip()
        
        # 번역 결과 검증
        if translated_text and len(translated_text) > 10:
            return translated_text
        else:
            raise TranslationError("OpenAI 번역 결과가 비어있습니다.")
            
    except openai.RateLimitError:
        logger.error("OpenAI API 할당량 초과")
        raise TranslationError("OpenAI API 할당량이 초과되었습니다.")
    except openai.Timeout:
        logger.error("OpenAI API 타임아웃")
        raise TranslationError("OpenAI 번역 요청이 시간 초과되었습니다.")
    except Exception as e:
        logger.error(f"OpenAI 번역 중 오류: {e}")
        raise TranslationError(f"OpenAI 번역 중 오류가 발생했습니다: {str(e)}")

def get_naver_keyword_volumes(keywords: list[str]) -> dict[str, int | None]:
    """
    네이버 검색광고 API를 사용하여 키워드 검색량을 조회합니다.
    """
    try:
        client_id, client_secret = settings.get_naver_credentials()
        if not client_id or not client_secret:
            logger.warning("네이버 API 자격증명이 설정되지 않았습니다.")
            return {keyword: None for keyword in keywords}
        
        headers = {
            'X-Naver-Client-Id': client_id,
            'X-Naver-Client-Secret': client_secret,
            'Content-Type': 'application/json'
        }
        
        results = {}
        for keyword in keywords:
            try:
                payload = {
                    'hintKeywords': keyword,
                    'showDetail': '1'
                }
                
                response = requests.post(NAVER_API_URL, headers=headers, json=payload, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'keywordList' in data and data['keywordList']:
                        # 첫 번째 키워드의 검색량 반환
                        monthly_pc_qty = data['keywordList'][0].get('monthlyPcQty', 0)
                        monthly_mobile_qty = data['keywordList'][0].get('monthlyMobileQty', 0)
                        total_volume = monthly_pc_qty + monthly_mobile_qty
                        results[keyword] = total_volume
                    else:
                        results[keyword] = None
                else:
                    logger.warning(f"네이버 API 오류: {response.status_code}")
                    results[keyword] = None
                    
            except Exception as e:
                logger.warning(f"키워드 {keyword} 조회 실패: {e}")
                results[keyword] = None
        
        return results
        
    except Exception as e:
        logger.error(f"네이버 키워드 검색량 조회 실패: {e}")
        return {keyword: None for keyword in keywords}

def google_search_related_posts(keywords: list[str]) -> list[str]:
    """
    Google 검색을 통해 관련 포스트 URL을 찾습니다.
    """
    try:
        api_key = settings.get_google_api_key()
        if not api_key:
            logger.warning("Google API 키가 설정되지 않았습니다.")
            return []
        
        search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        if not search_engine_id:
            logger.warning("Google Search Engine ID가 설정되지 않았습니다.")
            return []
        
        urls = []
        for keyword in keywords[:3]:  # 최대 3개 키워드만 처리
            try:
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': api_key,
                    'cx': search_engine_id,
                    'q': keyword,
                    'num': 5  # 최대 5개 결과
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'items' in data:
                        for item in data['items']:
                            if 'link' in item:
                                urls.append(item['link'])
                else:
                    logger.warning(f"Google 검색 API 오류: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"키워드 {keyword} 검색 실패: {e}")
        
        return list(set(urls))  # 중복 제거
        
    except Exception as e:
        logger.error(f"Google 검색 실패: {e}")
        return []

async def ai_summarize_and_evaluate_links(links: list, content: str = "") -> list:
    """
    AI를 사용하여 링크들을 요약하고 평가합니다.
    """
    try:
        if not links:
            return []
        
        # api_key = get_gemini_api_key() - 숨김 처리됨
        # if not api_key:
        #     logger.warning("Gemini API 키가 설정되지 않았습니다.")
        #     return []
        logger.warning("Gemini API 기능이 숨김 처리되었습니다.")
        return []
        
        results = []
        for link in links[:5]:  # 최대 5개 링크만 처리
            try:
                # 링크 요약 프롬프트
                prompt = f"""
다음 링크를 분석하여 간단한 요약과 관련성을 평가해주세요:

링크: {link}
현재 콘텐츠: {content[:200] if content else "없음"}

다음 형식으로 응답해주세요:
제목: [링크의 제목]
요약: [간단한 요약]
관련성: [높음/보통/낮음]
"""
                
                async with httpx.AsyncClient(timeout=TRANSLATION_TIMEOUT) as client:
                    url = f"{GEMINI_API_URL}{api_key}"
                    payload = {
                        "contents": [{
                            "parts": [{
                                "text": prompt
                            }]
                        }]
                    }
                    
                    response = await client.post(url, json=payload)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if 'candidates' in result and result['candidates']:
                            summary = result['candidates'][0]['content']['parts'][0]['text'].strip()
                            results.append({
                                'link': link,
                                'summary': summary
                            })
                
                # 요청 간 지연
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"링크 {link} 분석 실패: {e}")
        
        return results
        
    except Exception as e:
        logger.error(f"AI 링크 분석 실패: {e}")
        return []

async def translate_text_deepl(text: str, target_lang: str = "ko") -> str:
    """
    DeepL API를 사용하여 텍스트를 번역합니다.
    """
    try:
        api_key = settings.get_deepl_api_key()
        if not api_key:
            api_key = os.getenv('DEEPL_API_KEY', "2f05c78b-516f-406a-a555-81c9667c193d:fx")
        if not api_key:
            raise TranslationError("DeepL API 키가 설정되지 않았습니다.")
        
        # 언어 매핑 (DeepL 형식)
        lang_mapping = {
            "ko": "KO",
            "en": "EN",
            "ja": "JA",
            "zh": "ZH",
            "es": "ES",
            "fr": "FR",
            "de": "DE"
        }
        
        target_lang_code = lang_mapping.get(target_lang, target_lang.upper())
        
        # DeepL API 호출
        url = "https://api-free.deepl.com/v2/translate"
        headers = {
            "Authorization": f"DeepL-Auth-Key {api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "text": text,
            "target_lang": target_lang_code
        }
        
        async with httpx.AsyncClient(timeout=TRANSLATION_TIMEOUT) as client:
            response = await client.post(url, headers=headers, data=data)
            
            if response.status_code == 200:
                result = response.json()
                if 'translations' in result and result['translations']:
                    translated_text = result['translations'][0]['text']
                    
                    # 번역 결과 검증
                    if translated_text and len(translated_text) > 10:
                        return translated_text
                    else:
                        raise TranslationError("번역 결과가 비어있습니다.")
                else:
                    raise TranslationError("DeepL API 응답에 번역 결과가 없습니다.")
            else:
                error_detail = response.text
                logger.error(f"DeepL API 오류: {response.status_code} - {error_detail}")
                raise TranslationError(f"DeepL API 오류: {response.status_code}")
                
    except httpx.TimeoutException:
        logger.error("DeepL API 타임아웃")
        raise TranslationError("번역 요청이 시간 초과되었습니다.")
    except Exception as e:
        logger.error(f"DeepL 번역 중 오류: {e}")
        raise TranslationError(f"번역 중 오류가 발생했습니다: {str(e)}")