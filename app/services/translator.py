# app/services/translator.py

import deepl
from typing import Optional
from ..config import settings
from ..exceptions import TranslationError, APIKeyError
from ..utils.logger import setup_logger
import os
import json
import threading
from datetime import datetime
import httpx
import requests

logger = setup_logger(__name__)

# DeepL 번역기 인스턴스
translator = None

API_USAGE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'api_usage.json')
API_USAGE_FILE = os.path.abspath(API_USAGE_FILE)
API_USAGE_LOCK = threading.Lock()

GEMINI_API_KEY = "AIzaSyCgS6BXWZIpiFVQ3bYfCxbWCfrpDIACtfQ"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + GEMINI_API_KEY

NAVER_API_URL = "https://api.naver.com/keywordstool"

def _initialize_translator():
    """DeepL 번역기 초기화"""
    global translator
    
    if not settings.deepl_api_key:
        logger.warning("DEEPL_API_KEY가 설정되지 않았습니다. 번역 기능이 작동하지 않습니다.")
        return False
    
    try:
        translator = deepl.Translator(settings.deepl_api_key)
        logger.info("DeepL 번역기가 성공적으로 초기화되었습니다.")
        return True
    except Exception as e:
        logger.error(f"DeepL 번역기 초기화 중 오류 발생: {e}")
        return False

async def translate_text(text: str, target_lang: str = None) -> str:
    """
    주어진 텍스트를 DeepL API를 사용하여 번역합니다.
    target_lang: 'KO' for Korean, 'EN-US' for English (US), etc.
    """
    global translator
    
    # 번역기 초기화 확인
    if translator is None:
        if not _initialize_translator():
            raise APIKeyError("DeepL 번역기 초기화에 실패했습니다. API 키를 확인해주세요.")
    
    if not text or not text.strip():
        return ""

    target_lang = target_lang or settings.default_target_language
    
    try:
        logger.info(f"번역 시작: {target_lang} (텍스트 길이: {len(text)}자)")
        
        # DeepL API는 한 번에 여러 텍스트를 리스트로 받아 처리할 수 있습니다.
        # 긴 텍스트의 경우 단락별로 나누어 번역하면 품질과 안정성이 향상될 수 있습니다.
        result = translator.translate_text(text, target_lang=target_lang)
        
        # DeepL 호출 카운트 증가
        increase_api_usage_count('deepl')
        translated_text = result.text
        logger.info(f"번역 완료: {target_lang} (번역된 텍스트 길이: {len(translated_text)}자)")
        
        return translated_text
        
    except deepl.exceptions.QuotaExceededException:
        error_msg = "DeepL API 할당량이 초과되었습니다."
        logger.error(error_msg)
        raise TranslationError(error_msg)
    except deepl.exceptions.DeepLException as e:
        error_msg = f"DeepL API 오류: {e}"
        logger.error(error_msg)
        raise TranslationError(error_msg)
    except Exception as e:
        error_msg = f"번역 중 알 수 없는 오류 발생: {e}"
        logger.error(error_msg)
        raise TranslationError(error_msg)

async def detect_language(text: str) -> Optional[str]:
    """
    텍스트의 언어를 감지합니다.
    """
    global translator
    
    if translator is None:
        if not _initialize_translator():
            return None
    
    try:
        result = translator.translate_text(text, target_lang="EN-US")
        return result.detected_source_lang
    except Exception as e:
        logger.error(f"언어 감지 중 오류 발생: {e}")
        return None

def increase_api_usage_count(api_name: str):
    today = datetime.now().strftime('%Y-%m-%d')
    with API_USAGE_LOCK:
        try:
            if os.path.exists(API_USAGE_FILE):
                with open(API_USAGE_FILE, 'r', encoding='utf-8') as f:
                    usage = json.load(f)
            else:
                usage = {}
            if today not in usage:
                usage[today] = {}
            usage[today][api_name] = usage[today].get(api_name, 0) + 1
            with open(API_USAGE_FILE, 'w', encoding='utf-8') as f:
                json.dump(usage, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"API 호출 카운트 증가 실패: {e}")

async def translate_text_gemini(text: str, target_lang: str = "ko") -> str:
    """
    Google Gemini 번역 API를 사용하여 번역
    """
    if not text or not text.strip():
        return ""
    prompt = f"다음 영어 또는 기타 외국어 텍스트를 한국어로 자연스럽게 번역해 주세요.\n---\n{text[:4000]}\n---\n번역 결과만 출력하세요."
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(GEMINI_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            # Gemini 응답 구조에서 번역 결과 추출
            candidates = data.get("candidates")
            if candidates and len(candidates) > 0:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts and len(parts) > 0:
                    translated = parts[0].get("text", "").strip()
                    increase_api_usage_count('gemini')
                    return translated
            # 실패 시 원문 반환
            return text
    except Exception as e:
        logger.error(f"Gemini 번역 API 오류: {e}")
        return text

# 네이버 검색광고 API로 키워드별 월간 검색량 조회
# 최대 5개씩 batch 요청, 결과: {키워드: 검색량}
def get_naver_keyword_volumes(keywords: list[str]) -> dict:
    if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET:
        return {k: None for k in keywords}
    url = f"{NAVER_API_URL}/v1/keywords/search"
    headers = {
        "X-API-KEY": settings.NAVER_CLIENT_ID,
        "X-CUSTOMER": settings.NAVER_CLIENT_SECRET,
        "Content-Type": "application/json"
    }
    result = {}
    for i in range(0, len(keywords), 5):
        batch = keywords[i:i+5]
        payload = {"hintKeywords": ",".join(batch), "showDetail": 1}
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("keywordList", []):
                    kw = item.get("relKeyword")
                    vol = item.get("monthlyPcQcCnt", 0) + item.get("monthlyMobileQcCnt", 0)
                    result[kw] = vol
                # 누락된 키워드는 None 처리
                for k in batch:
                    if k not in result:
                        result[k] = None
            else:
                for k in batch:
                    result[k] = None
        except Exception:
            for k in batch:
                result[k] = None
    return result