import time
from typing import Optional
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SeleniumCrawler:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.options = Options()
        if self.headless:
            self.options.add_argument('--headless')
            self.options.add_argument('--disable-gpu')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

    def get_rendered_html(self, url: str, timeout: int = 7) -> Optional[str]:
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=self.options)
            driver.get(url)
            wait_selectors = [
                (By.TAG_NAME, "article"),
                (By.TAG_NAME, "main"),
                (By.CSS_SELECTOR, ".content, .post-content, .entry-content, .article-content")
            ]
            for by, selector in wait_selectors:
                try:
                    WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    break
                except Exception:
                    continue
            html = driver.page_source
            driver.quit()
            return html
        except Exception as e:
            print(f"[SeleniumCrawler] 크롤링 실패: {e}")
            return None

    def extract_main_content(self, html: str) -> Optional[str]:
        soup = BeautifulSoup(html, 'html.parser')
        selectors = [
            'main', 'article', '[role="main"]', '[role="article"]',
            '.content', '.post-content', '.entry-content', '.article-content',
            '.main-content', '.body-content', '.text-content', '#content', '#main',
            '#article', '#post', '.post', '.entry', '.article', '.story',
            '.content-area', '.content-body', '.content-main', '.article-text',
            '.global-content-stream', '.lomita-c-content', '.Campaign__content',
            '.Column__content', '.Element__content', '.Row__content'
        ]
        for selector in selectors:
            elements = soup.select(selector)
            for el in elements:
                text = el.get_text(separator='\n', strip=True)
                if text and len(text) > 200:
                    return text
        # fallback: 텍스트가 가장 긴 div
        divs = soup.find_all('div')
        best = max(divs, key=lambda d: len(d.get_text(strip=True)), default=None)
        if best:
            text = best.get_text(separator='\n', strip=True)
            if text and len(text) > 200:
                return text
        return None 