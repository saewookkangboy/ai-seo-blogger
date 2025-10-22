import time
import logging
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import threading

logger = logging.getLogger(__name__)

class SeleniumCrawler:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.options = Options()
        self._setup_chrome_options()
        self.driver = None
        self.lock = threading.Lock()
        
    def _setup_chrome_options(self):
        """Chrome 옵션 설정"""
        if self.headless:
            self.options.add_argument('--headless')
            self.options.add_argument('--disable-gpu')
        
        # 기본 옵션
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_argument('--disable-extensions')
        self.options.add_argument('--disable-plugins')
        self.options.add_argument('--disable-images')
        self.options.add_argument('--disable-javascript')
        self.options.add_argument('--disable-css')
        self.options.add_argument('--disable-web-security')
        self.options.add_argument('--allow-running-insecure-content')
        self.options.add_argument('--disable-features=VizDisplayCompositor')
        
        # User Agent 설정
        self.options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
        
        # 성능 최적화
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "geolocation": 2,
                "media_stream": 2
            }
        }
        self.options.add_experimental_option("prefs", prefs)
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)

    def _create_driver(self) -> Optional[webdriver.Chrome]:
        """Chrome 드라이버 생성"""
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=self.options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            logger.error(f"Chrome 드라이버 생성 실패: {e}")
            return None

    def get_rendered_html(self, url: str, timeout: int = 15, site_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """URL에서 렌더링된 HTML을 가져옵니다."""
        driver = None
        try:
            logger.info(f"Selenium 크롤링 시작: {url}")
            start_time = time.time()
            
            # 드라이버 생성
            driver = self._create_driver()
            if not driver:
                return None
            
            # 페이지 로드
            driver.get(url)
            
            # 페이지 로딩 대기
            self._wait_for_page_load(driver, timeout, site_config)
            
            # 스크롤 처리
            self._handle_scroll(driver)
            
            # HTML 추출
            html = driver.page_source
            
            response_time = time.time() - start_time
            logger.info(f"Selenium 크롤링 완료: {url} ({response_time:.2f}초)")
            
            return html
            
        except TimeoutException:
            logger.warning(f"Selenium 타임아웃: {url}")
            if driver:
                return driver.page_source
        except WebDriverException as e:
            logger.error(f"Selenium WebDriver 오류: {url}, {e}")
        except Exception as e:
            logger.error(f"Selenium 크롤링 오류: {url}, {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logger.error(f"드라이버 종료 오류: {e}")
        
        return None

    def _wait_for_page_load(self, driver: webdriver.Chrome, timeout: int, site_config: Optional[Dict[str, Any]] = None):
        """페이지 로딩 대기"""
        try:
            # 기본 대기 조건
            wait_selectors = [
                (By.TAG_NAME, "body"),
                (By.TAG_NAME, "html")
            ]
            
            # 사이트별 특화 대기 조건 추가
            if site_config and 'selectors' in site_config:
                for selector in site_config['selectors'][:3]:  # 상위 3개만 사용
                    if selector.startswith('.'):
                        wait_selectors.append((By.CSS_SELECTOR, selector))
                    elif selector.startswith('#'):
                        wait_selectors.append((By.CSS_SELECTOR, selector))
                    else:
                        wait_selectors.append((By.TAG_NAME, selector))
            
            # 일반적인 콘텐츠 선택자들
            general_selectors = [
                (By.TAG_NAME, "article"),
                (By.TAG_NAME, "main"),
                (By.CSS_SELECTOR, ".content, .post-content, .entry-content, .article-content"),
                (By.CSS_SELECTOR, ".main-content, .body-content, .text-content")
            ]
            
            wait_selectors.extend(general_selectors)
            
            # 대기 시도
            for by, selector in wait_selectors:
                try:
                    WebDriverWait(driver, min(timeout, 5)).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    logger.debug(f"페이지 로딩 완료: {selector}")
                    break
                except TimeoutException:
                    continue
            
            # 추가 대기 (JavaScript 실행 완료)
            time.sleep(2)
            
        except Exception as e:
            logger.warning(f"페이지 로딩 대기 중 오류: {e}")

    def _handle_scroll(self, driver: webdriver.Chrome):
        """스크롤 처리 (동적 콘텐츠 로딩)"""
        try:
            # 페이지 끝까지 스크롤
            last_height = driver.execute_script("return document.body.scrollHeight")
            
            for _ in range(3):  # 최대 3번 스크롤
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # 맨 위로 스크롤
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
        except Exception as e:
            logger.warning(f"스크롤 처리 중 오류: {e}")

    def extract_main_content(self, html: str, site_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """HTML에서 메인 콘텐츠를 추출합니다."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 사이트별 특화 선택자 우선 시도
            if site_config and 'selectors' in site_config:
                for selector in site_config['selectors']:
                    content = self._extract_with_selector(soup, selector, site_config)
                    if content:
                        logger.info(f"사이트별 선택자로 콘텐츠 추출 성공: {selector}")
                        return content
            
            # 일반적인 선택자들
            general_selectors = [
                'main', 'article', '[role="main"]', '[role="article"]',
                '.content', '.post-content', '.entry-content', '.article-content',
                '.main-content', '.body-content', '.text-content', '#content', '#main',
                '#article', '#post', '.post', '.entry', '.article', '.story',
                '.content-area', '.content-body', '.content-main', '.article-text',
                '.global-content-stream', '.lomita-c-content', '.Campaign__content',
                '.Column__content', '.Element__content', '.Row__content'
            ]
            
            for selector in general_selectors:
                content = self._extract_with_selector(soup, selector, site_config)
                if content:
                    logger.info(f"일반 선택자로 콘텐츠 추출 성공: {selector}")
                    return content
            
            # 폴백: 가장 큰 텍스트 블록
            content = self._extract_fallback(soup)
            if content:
                logger.info("폴백 방법으로 콘텐츠 추출 성공")
                return content
            
            return None
            
        except Exception as e:
            logger.error(f"콘텐츠 추출 중 오류: {e}")
            return None

    def _extract_with_selector(self, soup: BeautifulSoup, selector: str, site_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """특정 선택자로 콘텐츠 추출"""
        try:
            elements = soup.select(selector)
            if not elements:
                return None
            
            # 가장 큰 요소 선택
            best_element = max(elements, key=lambda el: len(el.get_text(strip=True)))
            
            # 제외할 요소들 제거
            if site_config and 'exclude_selectors' in site_config:
                for exclude_selector in site_config['exclude_selectors']:
                    for element in best_element.select(exclude_selector):
                        element.decompose()
            
            # 텍스트 추출
            text = best_element.get_text(separator='\n', strip=True)
            
            # 최소 길이 확인
            if text and len(text) > 200:
                return self._clean_text(text, site_config)
            
            return None
            
        except Exception as e:
            logger.debug(f"선택자 {selector} 처리 중 오류: {e}")
            return None

    def _extract_fallback(self, soup: BeautifulSoup) -> Optional[str]:
        """폴백 방법으로 콘텐츠 추출"""
        try:
            # 모든 div 요소 중 텍스트가 가장 긴 것 선택
            divs = soup.find_all('div')
            if not divs:
                return None
            
            best_div = max(divs, key=lambda d: len(d.get_text(strip=True)))
            text = best_div.get_text(separator='\n', strip=True)
            
            if text and len(text) > 200:
                return self._clean_text(text)
            
            return None
            
        except Exception as e:
            logger.error(f"폴백 추출 중 오류: {e}")
            return None

    def _clean_text(self, text: str, site_config: Optional[Dict[str, Any]] = None) -> str:
        """텍스트 정리"""
        if not text:
            return ""
        
        # 기본 정리
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 10:  # 너무 짧은 라인 제거
                cleaned_lines.append(line)
        
        # 사이트별 텍스트 필터 적용
        if site_config and 'text_filters' in site_config:
            import re
            for pattern in site_config['text_filters']:
                cleaned_lines = [line for line in cleaned_lines if not re.match(pattern, line)]
        
        return '\n\n'.join(cleaned_lines)

    def close(self):
        """드라이버 종료"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"드라이버 종료 오류: {e}")
            finally:
                self.driver = None 