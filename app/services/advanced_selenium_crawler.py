#!/usr/bin/env python3
"""
고급 Selenium 크롤러
더 정교한 페이지 처리와 스마트 크롤링 기능을 제공합니다.
"""

import time
import logging
import random
import json
import os
from typing import Optional, Dict, Any, List, Tuple
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import threading
import hashlib
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class AdvancedSeleniumCrawler:
    """고급 Selenium 크롤러"""
    
    def __init__(self, headless: bool = True, enable_ai_extraction: bool = True):
        self.headless = headless
        self.enable_ai_extraction = enable_ai_extraction
        self.options = Options()
        self._setup_chrome_options()
        self.driver = None
        self.lock = threading.Lock()
        self.session_cache = {}
        self.site_patterns = self._load_site_patterns()
        
    def _setup_chrome_options(self):
        """고급 Chrome 옵션 설정"""
        if self.headless:
            self.options.add_argument('--headless')
            self.options.add_argument('--disable-gpu')
        
        # 기본 성능 옵션
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_argument('--disable-extensions')
        self.options.add_argument('--disable-plugins')
        
        # 고급 성능 최적화
        self.options.add_argument('--disable-background-timer-throttling')
        self.options.add_argument('--disable-backgrounding-occluded-windows')
        self.options.add_argument('--disable-renderer-backgrounding')
        self.options.add_argument('--disable-features=TranslateUI')
        self.options.add_argument('--disable-ipc-flooding-protection')
        
        # 메모리 최적화
        self.options.add_argument('--memory-pressure-off')
        self.options.add_argument('--max_old_space_size=4096')
        
        # 네트워크 최적화
        self.options.add_argument('--disable-web-security')
        self.options.add_argument('--allow-running-insecure-content')
        self.options.add_argument('--disable-features=VizDisplayCompositor')
        
        # 이미지 및 미디어 처리
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "geolocation": 2,
                "media_stream": 2,
                "images": 1,  # 이미지 로드 허용 (콘텐츠 품질 향상)
                "plugins": 2,
                "popups": 2,
                "automatic_downloads": 2
            },
            "profile.managed_default_content_settings": {
                "images": 1
            }
        }
        self.options.add_experimental_option("prefs", prefs)
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        
        # User Agent 랜덤화
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        ]
        self.options.add_argument(f'user-agent={random.choice(user_agents)}')

    def _load_site_patterns(self) -> Dict[str, Dict[str, Any]]:
        """사이트별 패턴 설정 로드"""
        patterns = {
            "socialmediatoday.com": {
                "wait_selectors": [".article-content", ".post-content", "article"],
                "content_selectors": [".article-content", ".post-content", "article .content"],
                "exclude_selectors": [".advertisement", ".sidebar", ".comments"],
                "scroll_behavior": "smooth",
                "wait_time": 3,
                "max_scrolls": 3
            },
            "facebook.com": {
                "wait_selectors": ["[data-testid='post_message']", ".userContent"],
                "content_selectors": ["[data-testid='post_message']", ".userContent"],
                "exclude_selectors": [".ad", ".sponsored", ".sidebar"],
                "scroll_behavior": "aggressive",
                "wait_time": 5,
                "max_scrolls": 5
            },
            "twitter.com": {
                "wait_selectors": ["[data-testid='tweetText']", ".tweet-text"],
                "content_selectors": ["[data-testid='tweetText']", ".tweet-text"],
                "exclude_selectors": [".promoted-tweet", ".ad"],
                "scroll_behavior": "smooth",
                "wait_time": 4,
                "max_scrolls": 4
            },
            "linkedin.com": {
                "wait_selectors": [".feed-shared-text", ".post-content"],
                "content_selectors": [".feed-shared-text", ".post-content"],
                "exclude_selectors": [".ad", ".sponsored", ".sidebar"],
                "scroll_behavior": "smooth",
                "wait_time": 3,
                "max_scrolls": 3
            },
            "youtube.com": {
                "wait_selectors": ["#description", ".ytd-video-secondary-info-renderer"],
                "content_selectors": ["#description", ".ytd-video-secondary-info-renderer"],
                "exclude_selectors": [".ad", ".sponsored", ".sidebar"],
                "scroll_behavior": "minimal",
                "wait_time": 2,
                "max_scrolls": 2
            },
            "reddit.com": {
                "wait_selectors": [".RichTextJSON-root", ".usertext-body"],
                "content_selectors": [".RichTextJSON-root", ".usertext-body"],
                "exclude_selectors": [".ad", ".sponsored", ".sidebar"],
                "scroll_behavior": "smooth",
                "wait_time": 3,
                "max_scrolls": 4
            },
            "medium.com": {
                "wait_selectors": [".story-body", ".postArticle-content"],
                "content_selectors": [".story-body", ".postArticle-content"],
                "exclude_selectors": [".ad", ".sponsored", ".sidebar"],
                "scroll_behavior": "smooth",
                "wait_time": 3,
                "max_scrolls": 3
            }
        }
        return patterns

    def _get_site_config(self, url: str) -> Dict[str, Any]:
        """URL에 해당하는 사이트 설정 반환"""
        domain = urlparse(url).netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return self.site_patterns.get(domain, {
            "wait_selectors": ["article", ".content", ".post", ".entry"],
            "content_selectors": ["article", ".content", ".post", ".entry", "main"],
            "exclude_selectors": [".ad", ".advertisement", ".sidebar", ".comments"],
            "scroll_behavior": "smooth",
            "wait_time": 2,
            "max_scrolls": 2
        })

    def _create_driver(self) -> Optional[webdriver.Chrome]:
        """Chrome 드라이버 생성"""
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=self.options)
            
            # 웹드라이버 감지 방지
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko', 'en-US', 'en']})")
            
            # 뷰포트 설정
            driver.set_window_size(1920, 1080)
            
            return driver
        except Exception as e:
            logger.error(f"Chrome 드라이버 생성 실패: {e}")
            return None

    def _smart_wait(self, driver: webdriver.Chrome, url: str, timeout: int = 15) -> bool:
        """스마트 대기 - 사이트별 최적화된 대기 전략"""
        site_config = self._get_site_config(url)
        wait_selectors = site_config.get("wait_selectors", [])
        
        try:
            # 기본 페이지 로드 대기
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # 사이트별 특화 대기
            for selector in wait_selectors:
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"요소 발견: {selector}")
                    break
                except TimeoutException:
                    continue
            
            # 추가 대기 시간
            time.sleep(site_config.get("wait_time", 2))
            
            return True
            
        except TimeoutException:
            logger.warning(f"페이지 로드 타임아웃: {url}")
            return False

    def _smart_scroll(self, driver: webdriver.Chrome, url: str):
        """스마트 스크롤 - 사이트별 최적화된 스크롤 전략"""
        site_config = self._get_site_config(url)
        scroll_behavior = site_config.get("scroll_behavior", "smooth")
        max_scrolls = site_config.get("max_scrolls", 2)
        
        try:
            if scroll_behavior == "aggressive":
                # 적극적 스크롤 (소셜 미디어용)
                for i in range(max_scrolls):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(0.5)
                    
            elif scroll_behavior == "smooth":
                # 부드러운 스크롤 (일반 사이트용)
                for i in range(max_scrolls):
                    driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(0.5)
                    
            elif scroll_behavior == "minimal":
                # 최소 스크롤 (단순 페이지용)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(0.5)
                
        except Exception as e:
            logger.warning(f"스크롤 중 오류: {e}")

    def _handle_dynamic_content(self, driver: webdriver.Chrome, url: str):
        """동적 콘텐츠 처리"""
        site_config = self._get_site_config(url)
        
        try:
            # 무한 스크롤 처리
            if "infinite" in url or "feed" in url:
                for _ in range(3):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
            
            # 모달/팝업 처리
            modal_selectors = [".modal", ".popup", ".overlay", "[role='dialog']"]
            for selector in modal_selectors:
                try:
                    modal = driver.find_element(By.CSS_SELECTOR, selector)
                    if modal.is_displayed():
                        # ESC 키로 닫기 시도
                        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                        time.sleep(0.5)
                except NoSuchElementException:
                    continue
            
            # 쿠키/개인정보 처리
            cookie_selectors = [
                "[data-testid='cookie-accept']",
                ".cookie-accept",
                ".privacy-accept",
                "[aria-label*='Accept']",
                "[aria-label*='Accept']"
            ]
            
            for selector in cookie_selectors:
                try:
                    button = driver.find_element(By.CSS_SELECTOR, selector)
                    if button.is_displayed():
                        button.click()
                        time.sleep(0.5)
                        break
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            logger.warning(f"동적 콘텐츠 처리 중 오류: {e}")

    def _ai_enhanced_extraction(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """AI 기반 콘텐츠 추출"""
        if not self.enable_ai_extraction:
            return None
            
        try:
            # 콘텐츠 품질 점수 계산
            content_candidates = []
            
            # 주요 콘텐츠 영역 후보들
            selectors = [
                "article", "main", ".content", ".post", ".entry",
                ".article-content", ".post-content", ".story-content",
                "[role='main']", ".main-content", ".primary-content"
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    score = self._calculate_content_score(element)
                    if score > 0.3:  # 임계값
                        content_candidates.append((element, score))
            
            # 점수순 정렬
            content_candidates.sort(key=lambda x: x[1], reverse=True)
            
            if content_candidates:
                best_candidate = content_candidates[0][0]
                return self._extract_text_from_element(best_candidate)
                
        except Exception as e:
            logger.warning(f"AI 추출 중 오류: {e}")
            
        return None

    def _calculate_content_score(self, element) -> float:
        """콘텐츠 품질 점수 계산"""
        try:
            text = element.get_text(strip=True)
            if not text:
                return 0.0
            
            score = 0.0
            
            # 텍스트 길이 점수
            text_length = len(text)
            if 100 <= text_length <= 10000:
                score += 0.3
            elif text_length > 10000:
                score += 0.2
            
            # 문단 수 점수
            paragraphs = element.find_all(['p', 'div'])
            if 2 <= len(paragraphs) <= 50:
                score += 0.2
            
            # 제목 존재 점수
            headings = element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if headings:
                score += 0.1
            
            # 링크 밀도 점수 (너무 많은 링크는 제외)
            links = element.find_all('a')
            link_density = len(links) / max(len(text.split()), 1)
            if link_density < 0.1:
                score += 0.1
            
            # 불필요한 요소 제거
            unwanted = element.find_all(['script', 'style', 'nav', 'footer', 'header'])
            if not unwanted:
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception:
            return 0.0

    def _extract_text_from_element(self, element) -> str:
        """요소에서 텍스트 추출 및 정리"""
        try:
            # 불필요한 요소 제거
            for unwanted in element.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                unwanted.decompose()
            
            # 텍스트 추출
            text = element.get_text(separator='\n', strip=True)
            
            # 텍스트 정리
            lines = text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if line and len(line) > 10:  # 너무 짧은 줄 제외
                    cleaned_lines.append(line)
            
            return '\n\n'.join(cleaned_lines)
            
        except Exception as e:
            logger.warning(f"텍스트 추출 중 오류: {e}")
            return ""

    def get_rendered_html(self, url: str, timeout: int = 20) -> Optional[str]:
        """URL에서 렌더링된 HTML을 가져옵니다."""
        driver = None
        try:
            logger.info(f"고급 Selenium 크롤링 시작: {url}")
            start_time = time.time()
            
            # 캐시 확인
            cache_key = hashlib.md5(url.encode()).hexdigest()
            if cache_key in self.session_cache:
                logger.info("세션 캐시 사용")
                return self.session_cache[cache_key]
            
            # 드라이버 생성
            driver = self._create_driver()
            if not driver:
                return None
            
            # 페이지 로드
            driver.get(url)
            
            # 스마트 대기
            if not self._smart_wait(driver, url, timeout):
                return None
            
            # 동적 콘텐츠 처리
            self._handle_dynamic_content(driver, url)
            
            # 스마트 스크롤
            self._smart_scroll(driver, url)
            
            # HTML 추출
            html = driver.page_source
            
            # 캐시 저장
            self.session_cache[cache_key] = html
            
            response_time = time.time() - start_time
            logger.info(f"고급 Selenium 크롤링 완료: {url} ({response_time:.2f}초)")
            
            return html
            
        except Exception as e:
            logger.error(f"고급 Selenium 크롤링 실패: {url} - {e}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def extract_main_content(self, html: str, url: str) -> Optional[str]:
        """HTML에서 주요 콘텐츠를 추출합니다."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            site_config = self._get_site_config(url)
            
            # 1. AI 기반 추출 시도
            ai_content = self._ai_enhanced_extraction(soup, url)
            if ai_content and len(ai_content) > 500:
                return ai_content
            
            # 2. 사이트별 설정 기반 추출
            content_selectors = site_config.get("content_selectors", [])
            exclude_selectors = site_config.get("exclude_selectors", [])
            
            for selector in content_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        # 제외할 요소들 제거
                        for exclude_selector in exclude_selectors:
                            for unwanted in element.select(exclude_selector):
                                unwanted.decompose()
                        
                        content = self._extract_text_from_element(element)
                        if content and len(content) > 200:
                            return content
                except Exception as e:
                    logger.warning(f"선택자 {selector} 추출 실패: {e}")
                    continue
            
            # 3. 일반적인 추출 방법
            return self._extract_fallback(soup)
            
        except Exception as e:
            logger.error(f"콘텐츠 추출 실패: {e}")
            return None

    def _extract_fallback(self, soup: BeautifulSoup) -> Optional[str]:
        """폴백 콘텐츠 추출"""
        try:
            # 가장 큰 텍스트 블록 찾기
            text_blocks = []
            
            for element in soup.find_all(['article', 'main', 'div', 'section']):
                text = element.get_text(strip=True)
                if len(text) > 200:
                    text_blocks.append((element, len(text)))
            
            if text_blocks:
                # 가장 큰 블록 선택
                largest_block = max(text_blocks, key=lambda x: x[1])[0]
                return self._extract_text_from_element(largest_block)
            
            return None
            
        except Exception as e:
            logger.warning(f"폴백 추출 실패: {e}")
            return None

    def close(self):
        """크롤러 정리"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass
        self.session_cache.clear() 