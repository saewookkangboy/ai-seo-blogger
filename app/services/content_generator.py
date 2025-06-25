# app/services/content_generator.py

import openai
from typing import Optional
from ..config import settings
from ..exceptions import ContentGenerationError, APIKeyError
from ..utils.logger import setup_logger
import os
import json
import threading
from datetime import datetime
import re

logger = setup_logger(__name__)

# OpenAI 클라이언트 인스턴스
client = None

API_USAGE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'api_usage.json')
API_USAGE_FILE = os.path.abspath(API_USAGE_FILE)
API_USAGE_LOCK = threading.Lock()

def _initialize_client():
    """OpenAI 클라이언트 초기화"""
    global client
    
    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY가 설정되지 않았습니다. AI 콘텐츠 생성 기능이 작동하지 않습니다.")
        return False
    
    try:
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        logger.info("OpenAI 클라이언트가 성공적으로 초기화되었습니다.")
        return True
    except Exception as e:
        logger.error(f"OpenAI 클라이언트 초기화 중 오류 발생: {e}")
        return False

async def create_blog_post(text: str, keywords: str, rule_guidelines: Optional[list] = None) -> str:
    """
    번역된 텍스트와 키워드, 추가 가이드라인을 기반으로 AI를 사용하여 블로그 게시물을 생성합니다.
    """
    global client
    
    # 클라이언트 초기화 확인
    if client is None:
        if not _initialize_client():
            raise APIKeyError("OpenAI 클라이언트 초기화에 실패했습니다. API 키를 확인해주세요.")

    # AI에게 보낼 상세 지시사항 (프롬프트)
    system_prompt = "당신은 SEO에 최적화된 블로그 게시물을 작성하는 전문 카피라이터입니다. 당신의 글은 유익하고, 매력적이며, 이해하기 쉬운 어조를 가집니다."
    
    # 추가 가이드라인 텍스트 생성
    guideline_text = ""
    if rule_guidelines:
        guideline_text = "\n**추가 SEO/AI 가이드라인:**\n" + "\n".join([f"- {g}" for g in rule_guidelines])

    # 입력 토큰 수를 관리하기 위해 원본 텍스트의 길이를 제한
    user_prompt = f"""
    아래 정보를 바탕으로 SEO에 최적화된 전문적인 블로그 포스트를 한국어로 작성해주세요.

    **핵심 키워드:**
    {keywords}

    **참고 원문 (한국어 번역본):**
    ---
    {text[:settings.max_text_length]}
    ---
    {guideline_text}
    **작성 지침:**
    1.  **제목:** 핵심 키워드 중 하나 이상을 포함하여, 시선을 끄는 SEO 친화적인 제목을 만드세요.
    2.  **메타 설명:** 게시물을 요약하고 키워드를 포함하는 150자 내외의 간결한 메타 설명을 작성하세요.
    3.  **본문:**
        -   참고 원문을 그대로 복사하지 말고, 내용을 자연스럽게 재구성하고 확장하여 블로그 게시물을 작성하세요.
        -   최소 500 단어 이상의 분량으로 작성해주세요.
        -   서론, 여러 개의 소제목(H3 태그), 그리고 결론으로 명확하게 구조화하세요.
        -   핵심 키워드({keywords})를 제목, 서론, 소제목 등에 자연스럽게 통합하세요.
    4.  **출력 형식:**
        -   전체 결과물을 단일 HTML 문자열로 반환하세요.
        -   메인 제목에는 `<h2>` 태그를 사용하세요.
        -   소제목에는 `<h3>` 태그를 사용하세요.
        -   단락에는 `<p>` 태그를 사용하세요.
        -   메타 설명은 `<p><strong>메타 설명:</strong> [설명 내용]</p>` 형식으로 감싸주세요.

    **결과물 예시:**
    <h2>[AI가 생성한 제목]</h2>
    <p><strong>메타 설명:</strong> [AI가 생성한 메타 설명]</p>
    <hr>
    <p>[서론 단락]</p>
    <h3>[소제목 1]</h3>
    <p>[소제목 1에 대한 내용]</p>
    <h3>[소제목 2]</h3>
    <p>[소제목 2에 대한 내용]</p>
    <p>[결론 단락]</p>
    """

    try:
        logger.info(f"블로그 포스트 생성 시작 (키워드: {keywords})")
        
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens
        )
        
        # OpenAI 호출 카운트 증가
        increase_api_usage_count('openai')
        generated_content = response.choices[0].message.content
        # 코드블록/```html/``` 등 제거
        cleaned = re.sub(r'```+\s*html', '', generated_content, flags=re.IGNORECASE)
        cleaned = re.sub(r'```+', '', cleaned)
        cleaned = cleaned.replace("'''html", '').replace("'''", '')
        cleaned = cleaned.strip()
        logger.info(f"블로그 포스트 생성 완료 (생성된 콘텐츠 길이: {len(cleaned)}자)")
        
        return cleaned
        
    except openai.RateLimitError:
        error_msg = "OpenAI API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
        logger.error(error_msg)
        raise ContentGenerationError(error_msg)
    except openai.APIError as e:
        error_msg = f"OpenAI API 오류: {e}"
        logger.error(error_msg)
        raise ContentGenerationError(error_msg)
    except Exception as e:
        error_msg = f"콘텐츠 생성 중 알 수 없는 오류 발생: {e}"
        logger.error(error_msg)
        raise ContentGenerationError(error_msg)

async def extract_seo_keywords(text: str) -> str:
    """
    AI를 사용하여 주어진 텍스트에서 SEO 키워드를 추출합니다.
    """
    global client
    
    if client is None:
        if not _initialize_client():
            raise APIKeyError("OpenAI 클라이언트 초기화에 실패했습니다.")

    system_prompt = "당신은 주어진 텍스트의 핵심 주제를 파악하여 가장 관련성 높은 SEO 키워드를 추출하는 SEO 전문가입니다."
    
    user_prompt = f"""
    아래 한국어 텍스트를 분석하여, 검색 엔진에 가장 효과적일 것으로 생각되는 SEO 키워드를 5개에서 7개 사이로 추출해주세요.
    키워드들은 텍스트의 주요 주제를 대표해야 합니다.
    결과는 다른 설명 없이, 쉼표로만 구분된 단일 문자열로 제공해주세요.

    예시:
    AI SEO, 구글 AI 오버뷰, 콘텐츠 자동화, 블로그 마케팅, 생성형 AI

    분석할 텍스트:
    ---
    {text[:4000]}
    ---
    """

    try:
        logger.info("SEO 키워드 추출 시작")
        
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        # OpenAI 호출 카운트 증가
        increase_api_usage_count('openai')
        keywords = response.choices[0].message.content.strip()
        
        # 가끔 키워드 앞에 "키워드:" 같은 불필요한 텍스트가 붙는 경우를 대비
        if ":" in keywords:
            keywords = keywords.split(":")[-1].strip()
        
        logger.info(f"SEO 키워드 추출 완료: {keywords}")
        return keywords
        
    except Exception as e:
        error_msg = f"키워드 추출 중 오류 발생: {e}"
        logger.error(error_msg)
        raise ContentGenerationError(error_msg)

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
