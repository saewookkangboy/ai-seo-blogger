# app/services/crawler.py

import requests
from bs4 import BeautifulSoup, Tag
import logging
from typing import Optional, Dict, List, Any
import re
import time
import asyncio
from urllib.parse import urlparse
import json
import os
import hashlib
import threading
import aiohttp
from ..config import settings
from ..exceptions import CrawlingError
from ..utils.logger import setup_logger
from .performance_optimizer import cache_result, track_performance, get_optimized_client
from .error_handler import handle_errors, retry_on_error, validate_url

logger = setup_logger(__name__, "app.log")

# 성능 최적화를 위한 설정 (최적화)
CRAWLING_TIMEOUT = 10  # 10초로 단축 (속도 향상)
CRAWLING_CACHE_DURATION = 3600  # 1시간 캐시 (메모리 효율성)
MAX_RETRIES = 2  # 재시도 횟수 단축 (속도 향상)
MAX_CONCURRENT_REQUESTS = 5  # 동시 요청 수 제한 (안정성)
REQUEST_DELAY = 0.05  # 요청 간 지연 시간 단축 (속도 향상)

# 크롤링 캐시
crawling_cache = {}
crawling_cache_lock = threading.Lock()

# 모니터링 시스템 import
try:
    from .crawler_monitor import crawling_monitor
except ImportError:
    crawling_monitor = None

# Google 스타일 크롤러 import
try:
    from .google_style_crawler import GoogleStyleCrawler
except ImportError:
    GoogleStyleCrawler = None

try:
    from .selenium_crawler import SeleniumCrawler
    selenium_available = True
except ImportError:
    selenium_available = False
    SeleniumCrawler = None

# 고급 크롤러 import
try:
    from .advanced_selenium_crawler import AdvancedSeleniumCrawler
    advanced_selenium_available = True
except ImportError:
    advanced_selenium_available = False
    AdvancedSeleniumCrawler = None

def _get_crawling_cache_key(url: str) -> str:
    """크롤링 캐시 키 생성"""
    return hashlib.md5(url.encode()).hexdigest()

def _get_cached_content(cache_key: str) -> Optional[str]:
    """캐시된 콘텐츠 가져오기"""
    with crawling_cache_lock:
        if cache_key in crawling_cache:
            cached_data, timestamp = crawling_cache[cache_key]
            if time.time() - timestamp < CRAWLING_CACHE_DURATION:
                logger.info("캐시된 크롤링 결과 사용")
                return cached_data
            else:
                del crawling_cache[cache_key]
    return None

def _set_cached_content(cache_key: str, content: str):
    """콘텐츠를 캐시에 저장"""
    with crawling_cache_lock:
        crawling_cache[cache_key] = (content, time.time())
        # 캐시 크기 제한 (메모리 효율성)
        if len(crawling_cache) > 100:
            oldest_key = min(crawling_cache.keys(), key=lambda k: crawling_cache[k][1])
            del crawling_cache[oldest_key]

# 동시 요청 제어를 위한 세마포어
crawling_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

class SiteSpecificCrawler:
    """사이트별 특화 크롤러"""
    
    def __init__(self):
        self.site_configs = self._load_site_configs()
    
    def _load_site_configs(self) -> Dict[str, Dict[str, Any]]:
        """사이트별 설정을 로드합니다."""
        config_file = "site_crawler_configs.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"사이트 설정 파일 로드 실패: {e}")
        return {}
    
    def get_site_config(self, url: str) -> Optional[Dict[str, Any]]:
        """URL에 해당하는 사이트 설정을 반환합니다."""
        try:
            domain = urlparse(url).netloc.lower()
            for site_pattern, config in self.site_configs.items():
                if site_pattern in domain:
                    return config
        except Exception as e:
            logger.warning(f"사이트 설정 조회 실패: {e}")
        return None

class EnhancedCrawler:
    """향상된 크롤러 클래스"""
    
    def __init__(self):
        self.site_crawler = SiteSpecificCrawler()
        self.session = None
    
    async def _get_session(self):
        """aiohttp 세션 생성"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=CRAWLING_TIMEOUT)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def crawl_url_async(self, url: str, max_retries: int = 2) -> Optional[str]:
        """비동기 URL 크롤링"""
        try:
            # 동시 요청 제어
            async with crawling_semaphore:
                # URL 유효성 검사
                if not validate_url(url):
                    logger.error(f"유효하지 않은 URL: {url}")
                    return None
                
                # 캐시 확인
                cache_key = _get_crawling_cache_key(url)
                cached_content = _get_cached_content(cache_key)
                if cached_content:
                    logger.info(f"캐시된 크롤링 결과 사용: {url}")
                    return cached_content
                
                # 요청 간 지연
                await asyncio.sleep(REQUEST_DELAY)
                
                # 사이트별 설정 확인
                site_config = self.site_crawler.get_site_config(url)
                
                # aiohttp를 사용한 비동기 크롤링
                session = await self._get_session()
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                for attempt in range(max_retries):
                    try:
                        logger.info(f"크롤링 시도 {attempt + 1}/{max_retries}: {url}")
                        
                        async with session.get(url, headers=headers, allow_redirects=True) as response:
                            if response.status == 200:
                                content_type = response.headers.get('content-type', '').lower()
                                
                                if 'text/html' in content_type:
                                    html_content = await response.text()
                                    extracted_text = await self._extract_content_async(html_content, url, site_config)
                                    
                                    if extracted_text and len(extracted_text.strip()) > 30:
                                        _set_cached_content(cache_key, extracted_text)
                                        logger.info(f"크롤링 성공: {url} ({len(extracted_text)}자)")
                                        return extracted_text
                                    else:
                                        logger.warning(f"텍스트 추출 실패: {url}")
                                elif 'application/json' in content_type:
                                    json_content = await response.json()
                                    extracted_text = self._json_to_text(json_content)
                                    
                                    if extracted_text and len(extracted_text.strip()) > 30:
                                        _set_cached_content(cache_key, extracted_text)
                                        logger.info(f"JSON 크롤링 성공: {url} ({len(extracted_text)}자)")
                                        return extracted_text
                                else:
                                    logger.warning(f"지원하지 않는 콘텐츠 타입: {content_type}")
                            else:
                                logger.warning(f"HTTP {response.status}: {url}")
                                
                    except asyncio.TimeoutError:
                        logger.warning(f"크롤링 타임아웃 (시도 {attempt + 1}): {url}")
                    except Exception as e:
                        logger.warning(f"크롤링 오류 (시도 {attempt + 1}): {url}, 오류: {e}")
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.5 * (attempt + 1))  # 지수 백오프
                
                logger.error(f"모든 크롤링 시도 실패: {url}")
                return None
                
        except Exception as e:
            logger.error(f"크롤링 중 예상치 못한 오류: {url}, 오류: {e}")
            return None
    
    async def _extract_content_async(self, html_content: str, url: str, site_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """HTML에서 콘텐츠 추출 (비동기)"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 사이트별 설정이 있으면 우선 사용
            if site_config:
                extracted = self._extract_with_site_config(soup, site_config)
                if extracted:
                    return extracted
            
            # 일반적인 선택자로 추출
            extracted = self._extract_with_general_selectors(soup)
            if extracted:
                return extracted
            
            # 폴백 추출
            return self._extract_fallback(soup)
            
        except Exception as e:
            logger.error(f"콘텐츠 추출 중 오류: {e}")
            return None

    def _extract_with_site_config(self, soup: BeautifulSoup, config: Dict[str, Any]) -> Optional[str]:
        """사이트별 설정을 사용한 콘텐츠 추출"""
        try:
            selectors = config.get('selectors', [])
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    text_parts = []
                    for element in elements:
                        text = element.get_text(strip=True)
                        if text and len(text) > 10:
                            text_parts.append(text)
                    
                    if text_parts:
                        return ' '.join(text_parts)
        except Exception as e:
            logger.warning(f"사이트별 설정 추출 실패: {e}")
        return None

    def _extract_with_general_selectors(self, soup: BeautifulSoup) -> Optional[str]:
        """일반적인 선택자로 콘텐츠 추출"""
        # 메타 태그에서 제목 추출
        title = ""
        meta_title = soup.find('meta', property='og:title')
        if meta_title and isinstance(meta_title, Tag):
            content = meta_title.get('content')
            if content:
                title = str(content)
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
        
        # 본문 콘텐츠 추출
        content_selectors = [
            'article',
            '[role="main"]',
            '.content',
            '.post-content',
            '.entry-content',
            '.article-content',
            'main',
            '.main-content'
        ]
        
        content_text = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                text_parts = []
                for element in elements:
                    # 불필요한 요소 제거
                    for unwanted in element.select('script, style, nav, header, footer, .ad, .advertisement'):
                        unwanted.decompose()
                    
                    text = element.get_text(strip=True)
                    if text and len(text) > 50:
                        text_parts.append(text)
                
                if text_parts:
                    content_text = ' '.join(text_parts)
                    break
        
        # 제목과 본문 결합
        if title and content_text:
            return f"{title}\n\n{content_text}"
        elif content_text:
            return content_text
        elif title:
            return title
        
        return None

    def _extract_fallback(self, soup: BeautifulSoup) -> Optional[str]:
        """폴백 콘텐츠 추출"""
        try:
            # 모든 텍스트 추출
            text = soup.get_text(strip=True)
            
            # 불필요한 공백 정리
            text = re.sub(r'\s+', ' ', text)
            
            # 최소 길이 확인
            if len(text) > 100:
                return text
            
        except Exception as e:
            logger.warning(f"폴백 추출 실패: {e}")
        
        return None

    def _json_to_text(self, json_data: Dict[str, Any]) -> str:
        """JSON 데이터를 텍스트로 변환"""
        try:
            if isinstance(json_data, dict):
                # 주요 필드들 추출
                text_parts = []
                
                # 제목 관련 필드
                for field in ['title', 'name', 'subject', 'headline']:
                    if field in json_data and json_data[field]:
                        text_parts.append(str(json_data[field]))
                
                # 본문 관련 필드
                for field in ['body', 'content', 'text', 'description', 'summary']:
                    if field in json_data and json_data[field]:
                        text_parts.append(str(json_data[field]))
                
                # 기타 유용한 필드들
                for field in ['message', 'comment', 'note', 'details']:
                    if field in json_data and json_data[field]:
                        text_parts.append(str(json_data[field]))
                
                # 중첩된 객체 처리
                for key, value in json_data.items():
                    if isinstance(value, dict):
                        nested_text = self._json_to_text(value)
                        if nested_text:
                            text_parts.append(nested_text)
                    elif isinstance(value, list) and value:
                        # 리스트의 첫 번째 항목만 처리
                        if isinstance(value[0], dict):
                            nested_text = self._json_to_text(value[0])
                            if nested_text:
                                text_parts.append(nested_text)
                        else:
                            text_parts.append(str(value[0]))
                
                return ' '.join(text_parts)
            
            elif isinstance(json_data, list) and json_data:
                # 리스트의 경우 첫 번째 항목 처리
                return self._json_to_text(json_data[0])
            
            else:
                return str(json_data)
                
        except Exception as e:
            logger.warning(f"JSON을 텍스트로 변환 중 오류: {e}")
            return str(json_data)

# 기존 함수들과의 호환성을 위한 래퍼
def crawl_url(url: str, use_google_style: bool = True) -> Optional[str]:
    """기존 인터페이스를 유지하는 래퍼 함수"""
    # URL 유효성 검사
    if not validate_url(url):
        raise ValueError(f"유효하지 않은 URL: {url}")
    
    logger.info(f"crawl_url 함수 시작: {url}")
    crawler = EnhancedCrawler()
    
    # 동기 실행을 위한 이벤트 루프 처리
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 이미 실행 중인 루프가 있으면 새 스레드에서 실행
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, crawler.crawl_url_async(url))
                result = future.result(timeout=CRAWLING_TIMEOUT + 5)
        else:
            result = loop.run_until_complete(crawler.crawl_url_async(url))
    except Exception as e:
        logger.error(f"크롤링 실행 중 오류: {e}")
        result = None
    
    logger.info(f"crawl_url 함수 결과: {len(result) if result else 0}자")
    return result

async def get_text_from_url(url: str) -> str:
    """URL에서 텍스트를 가져오는 비동기 함수 (성능 최적화)"""
    try:
        # URL 유효성 검사
        if not validate_url(url):
            logger.error(f"유효하지 않은 URL: {url}")
            return ""
        
        # 캐시 확인
        cache_key = _get_crawling_cache_key(url)
        cached_content = _get_cached_content(cache_key)
        if cached_content:
            logger.info(f"캐시된 크롤링 결과 사용: {url}")
            return cached_content
        
        # 향상된 크롤러 사용
        crawler = EnhancedCrawler()
        content = await crawler.crawl_url_async(url)
        
        if content and len(content.strip()) > 30:  # 최소 길이를 30자로 낮춤
            logger.info(f"크롤링 성공: {url} ({len(content)}자)")
            return content
        else:
            # 더 자세한 오류 메시지
            error_msg = f"URL에서 텍스트를 추출할 수 없습니다: {url}"
            if content:
                error_msg += f" (추출된 텍스트 길이: {len(content)}자, 최소 요구 길이: 30자)"
                logger.warning(f"크롤링 결과 (처음 200자): {content[:200]}...")
            else:
                error_msg += " (텍스트 추출 실패)"
            logger.warning(error_msg)
            return ""
            
    except Exception as e:
        logger.error(f"URL 크롤링 실패: {url}, 오류: {e}")
        return ""