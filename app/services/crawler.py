# app/services/crawler.py

import requests
from bs4 import BeautifulSoup, Tag
import logging
from typing import Optional, Dict, List, Any
import re
import time
from urllib.parse import urlparse
import json
import os
from ..config import settings
from ..exceptions import CrawlingError
from ..utils.logger import setup_logger

logger = setup_logger(__name__, "app.log")

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
                logger.warning(f"사이트 설정 로드 실패: {e}")
        
        return {
            "searchengineland.com": {
                "selectors": [
                    ".entry-content",
                    ".post-content", 
                    ".article-content",
                    ".content-area",
                    "article .entry-content",
                    ".entry-body",
                    ".post-body"
                ],
                "exclude_selectors": [
                    ".advertisement",
                    ".sidebar",
                    ".comments",
                    ".related-posts"
                ],
                "text_filters": [
                    r"^\s*$",  # 빈 줄
                    r"^Advertisement$",
                    r"^Related.*$"
                ]
            },
            "moz.com": {
                "selectors": [
                    ".post-content",
                    ".entry-content",
                    ".article-content",
                    ".content-body"
                ],
                "exclude_selectors": [
                    ".sidebar",
                    ".comments",
                    ".related"
                ]
            },
            "ahrefs.com": {
                "selectors": [
                    ".post-content",
                    ".entry-content",
                    ".article-body"
                ],
                "exclude_selectors": [
                    ".sidebar",
                    ".comments"
                ]
            }
        }
    
    def get_site_config(self, url: str) -> Optional[Dict[str, Any]]:
        """URL에 해당하는 사이트 설정을 반환합니다."""
        domain = urlparse(url).netloc.lower()
        
        # 정확한 도메인 매칭
        if domain in self.site_configs:
            return self.site_configs[domain]
        
        # 서브도메인 매칭
        for config_domain in self.site_configs.keys():
            if domain.endswith(config_domain):
                return self.site_configs[config_domain]
        
        return None

class EnhancedCrawler:
    """강화된 크롤러 (Google 스타일 통합)"""
    
    def __init__(self):
        self.site_crawler = SiteSpecificCrawler()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Google 스타일 크롤러 초기화
        self.google_crawler = GoogleStyleCrawler() if GoogleStyleCrawler is not None else None
        self.selenium_crawler = SeleniumCrawler() if selenium_available and SeleniumCrawler is not None else None
    
    def crawl_url(self, url: str, max_retries: int = 3, use_google_style: bool = True) -> Optional[str]:
        print(f"[DEBUG] crawl_url 호출: {url}, use_google_style={use_google_style}")
        error_message = ""
        
        # Google 스타일 크롤러 우선 시도
        if use_google_style and self.google_crawler:
            try:
                print(f"[DEBUG] Google 스타일 크롤러 시도: {url}")
                logger.info(f"Google 스타일 크롤러로 시도: {url}")
                content = self.google_crawler.crawl_url(url, max_retries)
                print(f"[DEBUG] Google 스타일 크롤러 결과: {type(content)}, 길이: {len(content) if content else 0}")
                if content and len(content.strip()) > 200:
                    logger.info(f"Google 스타일 크롤링 성공: {len(content)}자 추출")
                    print(f"[DEBUG] Google 스타일 크롤링 성공: {len(content)}자 추출")
                    if crawling_monitor:
                        crawling_monitor.record_attempt(url, True, len(content), "Google Style")
                    return content
                else:
                    logger.info("Google 스타일 크롤러 실패, 기존 방식으로 시도")
                    print(f"[DEBUG] Google 스타일 크롤러 실패, 기존 방식으로 시도")
            except Exception as e:
                logger.warning(f"Google 스타일 크롤러 오류: {e}")
                print(f"[DEBUG] Google 스타일 크롤러 오류: {e}")
        
        # 기존 방식으로 시도
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] 기존 크롤링 시도 {attempt + 1}/{max_retries}: {url}")
                logger.info(f"기존 크롤링 시도 {attempt + 1}/{max_retries}: {url}")
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                # 인코딩 확인
                if response.encoding == 'ISO-8859-1':
                    response.encoding = response.apparent_encoding
                
                # HTML 파싱
                soup = BeautifulSoup(response.text, 'html.parser')

                # 본문 추출
                content = self._extract_content(soup, url)
                print(f"[DEBUG] 기존 방식 본문 추출 결과: {type(content)}, 길이: {len(content) if content else 0}")
                
                if content and len(content.strip()) > 100:
                    logger.info(f"기존 크롤링 성공: {len(content)}자 추출")
                    print(f"[DEBUG] 기존 크롤링 성공: {len(content)}자 추출")
                    if crawling_monitor:
                        crawling_monitor.record_attempt(url, True, len(content), "Traditional")
                    return content
                else:
                    error_message = f"본문이 너무 짧거나 없음: {len(content) if content else 0}자"
                    logger.warning(error_message)
                    print(f"[DEBUG] {error_message}")
                    
            except requests.exceptions.RequestException as e:
                error_message = f"네트워크 오류: {e}"
                logger.error(f"네트워크 오류 (시도 {attempt + 1}): {e}")
                print(f"[DEBUG] 네트워크 오류 (시도 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
            except Exception as e:
                error_message = f"크롤링 오류: {e}"
                logger.error(f"크롤링 오류 (시도 {attempt + 1}): {e}")
                print(f"[DEBUG] 크롤링 오류 (시도 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        logger.error(f"모든 시도 실패: {url}")
        print(f"[DEBUG] 모든 시도 실패: {url}")
        
        # 모니터링 기록
        if crawling_monitor:
            crawling_monitor.record_attempt(url, False, 0, error_message)
        
        # 2차: Selenium 폴백
        if self.selenium_crawler:
            print(f"[DEBUG] Selenium 폴백 크롤링 시도: {url}")
            html = self.selenium_crawler.get_rendered_html(url)
            if html:
                content = self.selenium_crawler.extract_main_content(html)
                if content and len(content) > 200:
                    print(f"[DEBUG] Selenium 크롤링 성공: {len(content)}자")
                    return content
                else:
                    print(f"[DEBUG] Selenium 본문 추출 실패 또는 너무 짧음")
            else:
                print(f"[DEBUG] Selenium으로 HTML을 가져오지 못함")
        else:
            print("[DEBUG] Selenium이 설치되어 있지 않음. 동적 렌더링 사이트는 크롤링 불가.")
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        print(f"[DEBUG] _extract_content 호출: {url}")
        # 1. 사이트별 특화 처리
        site_config = self.site_crawler.get_site_config(url)
        if site_config:
            content = self._extract_with_site_config(soup, site_config)
            print(f"[DEBUG] 사이트별 특화 추출 결과: {type(content)}, 길이: {len(content) if content else 0}")
            if content:
                return content
        
        # 2. 일반적인 선택자들로 시도
        content = self._extract_with_general_selectors(soup)
        print(f"[DEBUG] 일반 선택자 추출 결과: {type(content)}, 길이: {len(content) if content else 0}")
        if content:
            return content
        
        # 3. 폴백: 전체 body에서 텍스트 추출
        content = self._extract_fallback(soup)
        print(f"[DEBUG] 폴백 추출 결과: {type(content)}, 길이: {len(content) if content else 0}")
        return content
    
    def _extract_with_site_config(self, soup: BeautifulSoup, config: Dict[str, Any]) -> Optional[str]:
        print(f"[DEBUG] _extract_with_site_config 호출")
        selectors = config.get('selectors', [])
        exclude_selectors = config.get('exclude_selectors', [])
        text_filters = config.get('text_filters', [])
        
        for selector in selectors:
            try:
                main_content = soup.select_one(selector)
                if main_content and isinstance(main_content, Tag):
                    # 제외할 요소들 제거
                    for exclude_selector in exclude_selectors:
                        for element in main_content.select(exclude_selector):
                            element.decompose()

                    # 텍스트 추출 및 필터링
                    content = self._clean_text(main_content.get_text(), text_filters)
                    print(f"[DEBUG] selector: {selector}, 추출 길이: {len(content)}")
                    
                    if len(content.strip()) > 500:
                        logger.info(f"사이트별 설정으로 본문 추출 성공: {selector}")
                        print(f"[DEBUG] 사이트별 설정으로 본문 추출 성공: {selector}")
                        return content
                        
            except Exception as e:
                logger.debug(f"선택자 {selector} 처리 중 오류: {e}")
                print(f"[DEBUG] 선택자 {selector} 처리 중 오류: {e}")
                continue
        
        return None
    
    def _extract_with_general_selectors(self, soup: BeautifulSoup) -> Optional[str]:
        print(f"[DEBUG] _extract_with_general_selectors 호출")
        general_selectors = [
            'article',
            'main',
            '[role="main"]',
            '.content',
            '.post-content',
            '.entry-content',
            '.article-content',
            '.main-content',
            '#content',
            '#main',
            '.post',
            '.entry',
            '.article'
        ]
        
        for selector in general_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    # 가장 큰 텍스트 블록 찾기
                    best_content = None
                    max_length = 0
                    
                    for element in elements:
                        if isinstance(element, Tag):
                            text = element.get_text(strip=True)
                            if len(text) > max_length:
                                max_length = len(text)
                                best_content = text
                    
                    print(f"[DEBUG] 일반 selector: {selector}, 최대 길이: {max_length}")
                    if best_content and len(best_content) > 500:
                        logger.info(f"일반 선택자로 본문 추출 성공: {selector}")
                        print(f"[DEBUG] 일반 선택자로 본문 추출 성공: {selector}")
                        return self._clean_text(best_content)
                        
            except Exception as e:
                logger.debug(f"일반 선택자 {selector} 처리 중 오류: {e}")
                print(f"[DEBUG] 일반 선택자 {selector} 처리 중 오류: {e}")
                continue
        
        return None
    
    def _extract_fallback(self, soup: BeautifulSoup) -> Optional[str]:
        print(f"[DEBUG] _extract_fallback 호출")
        try:
            # 모든 텍스트 블록 수집
            text_blocks = []
            
            for tag in soup.find_all(['p', 'div', 'article', 'section']):
                if isinstance(tag, Tag):
                    text = tag.get_text(strip=True)
                    if len(text) > 100:  # 의미있는 텍스트 블록
                        text_blocks.append((len(text), text))
            
            # 크기순으로 정렬
            text_blocks.sort(key=lambda x: x[0], reverse=True)
            
            # 상위 3개 블록 결합
            if text_blocks:
                combined_text = " ".join([block[1] for block in text_blocks[:3]])
                print(f"[DEBUG] 폴백 상위 3개 블록 결합 길이: {len(combined_text)}")
                if len(combined_text) > 300:
                    logger.info("폴백 방법으로 본문 추출 성공")
                    print(f"[DEBUG] 폴백 방법으로 본문 추출 성공")
                    return self._clean_text(combined_text)
            
            # 최후의 수단: body 전체
            if soup.body:
                body_text = soup.body.get_text(strip=True)
                print(f"[DEBUG] body 전체 길이: {len(body_text)}")
                if len(body_text) > 200:
                    logger.info("body 전체에서 본문 추출")
                    print(f"[DEBUG] body 전체에서 본문 추출")
                    return self._clean_text(body_text)
                    
        except Exception as e:
            logger.error(f"폴백 추출 중 오류: {e}")
            print(f"[DEBUG] 폴백 추출 중 오류: {e}")
        
        return None
    
    def _clean_text(self, text: str, filters: Optional[List[str]] = None) -> str:
        """텍스트를 정리하고 필터링합니다."""
        if not text:
            return ""
        
        # 기본 필터
        default_filters = [
            r'\s+',  # 연속된 공백
            r'^\s+|\s+$',  # 앞뒤 공백
            r'\[.*?\]',  # 대괄호 내용
            r'\(.*?\)',  # 괄호 내용 (선택적)
        ]
        
        all_filters = default_filters + (filters or [])
        
        # 필터 적용
        for pattern in all_filters:
            text = re.sub(pattern, ' ', text)
        
        # HTML 엔티티 디코딩
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        # 연속된 공백 정리
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

# 기존 함수들과의 호환성을 위한 래퍼
def crawl_url(url: str, use_google_style: bool = True) -> Optional[str]:
    """기존 인터페이스를 유지하는 래퍼 함수"""
    crawler = EnhancedCrawler()
    return crawler.crawl_url(url, use_google_style=use_google_style)

async def get_text_from_url(url: str) -> str:
    """URL에서 텍스트를 가져오는 비동기 함수"""
    try:
        content = crawl_url(url, use_google_style=True)
        if content:
            return content
        else:
            raise CrawlingError(f"URL에서 텍스트를 추출할 수 없습니다: {url}")
    except Exception as e:
        logger.error(f"URL 크롤링 실패: {url}, 오류: {e}")
        raise CrawlingError(f"URL 크롤링 중 오류가 발생했습니다: {e}")