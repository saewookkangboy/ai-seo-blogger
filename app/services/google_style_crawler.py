"""
Google 스타일 크롤러
Google이 웹페이지를 크롤링하는 방식을 모방한 고급 크롤러
"""

import requests
from bs4 import BeautifulSoup, Tag
import logging
from typing import Optional, Dict, List, Any, Tuple
import re
import time
import random
from urllib.parse import urlparse, urljoin
import json
import os
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class ContentBlock:
    """콘텐츠 블록 정보"""
    text: str
    tag: str
    class_name: str
    id_name: str
    length: int
    density: float  # 텍스트 밀도
    position: int   # 페이지 내 위치

class GoogleStyleCrawler:
    """Google 스타일 크롤러"""
    
    def __init__(self):
        self.session = self._create_session()
        self.content_patterns = self._load_content_patterns()
        self.noise_patterns = self._load_noise_patterns()
        
    def _create_session(self) -> requests.Session:
        """Google과 유사한 세션 생성"""
        session = requests.Session()
        
        # Google Chrome과 유사한 헤더
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        
        return session
    
    def _load_content_patterns(self) -> Dict[str, List[str]]:
        """콘텐츠 패턴 로드"""
        return {
            "main_content": [
                "main", "article", "[role='main']", "[role='article']",
                ".content", ".post-content", ".entry-content", ".article-content",
                ".main-content", ".body-content", ".text-content",
                "#content", "#main", "#article", "#post",
                ".post", ".entry", ".article", ".story",
                ".content-area", ".content-body", ".content-main",
                # Search Engine Land 특화 선택자
                ".article-text", ".global-content-stream", ".lomita-c-content",
                ".Campaign__content", ".Column__content", ".Element__content", ".Row__content",
                # BBC 특화 선택자
                ".article-body", ".story-body", "[data-component='text-block']",
                ".gs-c-promo-body", ".gs-o-faux-block-link", ".gs-c-promo-summary",
                # Facebook 특화 선택자
                "[data-testid='post_message']", "[data-testid='story_message']",
                ".userContent", ".userContent p",
                # 일반적인 시맨틱 선택자
                "[itemprop='articleBody']", "[itemprop='text']", "[itemprop='description']",
                ".article-body", ".post-body", ".entry-body", ".story-body"
            ],
            "text_blocks": [
                "p", "div", "section", "article", "main",
                "h1", "h2", "h3", "h4", "h5", "h6",
                "li", "blockquote", "pre", "code"
            ],
            "semantic_content": [
                "[itemprop='articleBody']", "[itemprop='text']",
                "[itemprop='description']", "[itemprop='content']",
                ".article-body", ".post-body", ".entry-body",
                ".story-body", ".content-body", ".text-body"
            ]
        }
    
    def _load_noise_patterns(self) -> Dict[str, List[str]]:
        """노이즈 패턴 로드"""
        return {
            "exclude_selectors": [
                "script", "style", "noscript", "iframe", "embed",
                "nav", "header", "footer", "aside", "sidebar",
                ".advertisement", ".ads", ".ad", ".banner",
                ".sidebar", ".navigation", ".menu", ".breadcrumb",
                ".comments", ".comment", ".social-share", ".share",
                ".related", ".recommended", ".suggested",
                ".newsletter", ".subscribe", ".signup",
                ".cookie", ".privacy", ".terms", ".disclaimer",
                ".author-bio", ".author-info", ".author-meta",
                ".post-meta", ".entry-meta", ".article-meta",
                ".social-media", ".social-links", ".social-buttons",
                ".pagination", ".pager", ".page-nav",
                ".breadcrumbs", ".breadcrumb", ".crumb",
                ".search", ".search-box", ".search-form",
                ".newsletter-signup", ".email-signup", ".subscription",
                ".popup", ".modal", ".overlay", ".lightbox",
                ".cookie-banner", ".privacy-notice", ".gdpr-notice",
                ".right-rail-content", ".sel-new-articles", ".stream-article"
            ],
            "text_filters": [
                r'^\s*$',  # 빈 텍스트
                r'^Advertisement$', r'^Ad$', r'^Sponsored$',
                r'^Related.*$', r'^You might also like.*$',
                r'^Share.*$', r'^Follow.*$', r'^Subscribe.*$',
                r'^Sign up.*$', r'^Join.*$', r'^Get.*$',
                r'^Click here.*$', r'^Read more.*$', r'^Continue reading.*$',
                r'^Loading.*$', r'^Please wait.*$', r'^Error.*$',
                r'^404.*$', r'^Page not found.*$', r'^Not found.*$',
                r'^Access denied.*$', r'^Forbidden.*$', r'^Unauthorized.*$'
            ]
        }
    
    def crawl_url(self, url: str, max_retries: int = 3) -> Optional[str]:
        """URL을 Google 스타일로 크롤링합니다."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Google 스타일 크롤링 시도 {attempt + 1}/{max_retries}: {url}")
                
                # 요청 전송
                response = self._make_request(url)
                if not response:
                    continue
                
                # HTML 파싱
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 노이즈 제거
                self._remove_noise(soup)
                
                # 본문 추출
                content = self._extract_google_style_content(soup, url)
                
                if content and len(content.strip()) > 200:
                    logger.info(f"Google 스타일 크롤링 성공: {len(content)}자 추출")
                    return content
                else:
                    logger.warning(f"Google 스타일 크롤링 실패: 콘텐츠가 너무 짧음 ({len(content) if content else 0}자)")
                    
            except Exception as e:
                logger.error(f"Google 스타일 크롤링 오류 (시도 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
        
        logger.error(f"Google 스타일 크롤링 모든 시도 실패: {url}")
        return None
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """HTTP 요청을 전송합니다."""
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            
            # 인코딩 확인 및 수정
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP 요청 실패: {e}")
            return None
    
    def _extract_google_style_content(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Google 스타일로 본문을 추출합니다."""
        try:
            # 1. 메인 콘텐츠 영역 식별
            main_content = self._identify_main_content(soup)
            if not main_content:
                logger.warning("메인 콘텐츠 영역을 찾을 수 없음")
                return None
            
            # 2. 콘텐츠 블록 분석
            content_blocks = self._analyze_content_blocks(main_content)
            if not content_blocks:
                logger.warning("콘텐츠 블록을 찾을 수 없음")
                return None
            
            # 3. 최적의 콘텐츠 선택
            best_content = self._select_best_content(content_blocks)
            if not best_content:
                logger.warning("최적의 콘텐츠를 선택할 수 없음")
                return None
            
            # 4. 텍스트 정리 및 구조화
            cleaned_content = self._clean_and_structure_text(best_content)
            
            return cleaned_content
            
        except Exception as e:
            logger.error(f"Google 스타일 콘텐츠 추출 오류: {e}")
            return None
    
    def _remove_noise(self, soup: BeautifulSoup):
        """노이즈 요소들을 제거합니다."""
        # 제외할 선택자들 제거
        for selector in self.noise_patterns["exclude_selectors"]:
            for element in soup.select(selector):
                element.decompose()
    
    def _identify_main_content(self, soup: BeautifulSoup) -> Optional[Any]:
        """메인 콘텐츠 영역을 식별합니다."""
        # 1. 시맨틱 메인 콘텐츠 선택자들 시도
        for selector in self.content_patterns["main_content"]:
            elements = soup.select(selector)
            if elements:
                # 가장 큰 요소 선택
                largest_element = max(elements, key=lambda e: len(e.get_text(strip=True)))
                if len(largest_element.get_text(strip=True)) > 500:
                    return largest_element
        
        # 2. 텍스트 밀도가 높은 요소들 찾기
        dense_elements = self._find_text_dense_elements(soup)
        if dense_elements:
            best_element, score = max(dense_elements, key=lambda x: x[1])
            if score > 0.3:  # 텍스트 밀도 임계값
                return best_element
        
        return None
    
    def _calculate_content_score(self, element: Tag) -> float:
        """요소의 콘텐츠 점수를 계산합니다."""
        if not element:
            return 0.0
        
        text = element.get_text(strip=True)
        if not text:
            return 0.0
        
        # 텍스트 길이 점수
        length_score = min(len(text) / 1000, 1.0)
        
        # 텍스트 밀도 점수
        total_length = len(element.get_text())
        text_density = len(text) / total_length if total_length > 0 else 0
        
        # 링크 밀도 점수 (낮을수록 좋음)
        links = element.find_all('a')
        link_density = len(links) / len(text) if len(text) > 0 else 1.0
        link_score = max(0, 1 - link_density * 10)
        
        # 태그 점수
        tag_score = 1.0
        if element.name in ['article', 'main']:
            tag_score = 1.2
        elif element.name in ['div', 'section']:
            tag_score = 1.0
        else:
            tag_score = 0.8
        
        # 클래스명 점수
        class_score = 1.0
        class_name = element.get('class', [])
        if class_name:
            class_str = ' '.join(class_name).lower()
            if any(keyword in class_str for keyword in ['content', 'post', 'article', 'main', 'body']):
                class_score = 1.2
            elif any(keyword in class_str for keyword in ['sidebar', 'nav', 'menu', 'footer', 'header']):
                class_score = 0.5
        
        # 종합 점수
        total_score = (length_score * 0.3 + 
                      text_density * 0.3 + 
                      link_score * 0.2 + 
                      tag_score * 0.1 + 
                      class_score * 0.1)
        
        return total_score
    
    def _find_text_dense_elements(self, soup: BeautifulSoup) -> List[Tuple[Tag, float]]:
        """텍스트 밀도가 높은 요소들을 찾습니다."""
        dense_elements = []
        
        for element in soup.find_all(['div', 'article', 'section', 'main']):
            if isinstance(element, Tag):
                score = self._calculate_content_score(element)
                if score > 0.2:  # 최소 점수 임계값
                    dense_elements.append((element, score))
        
        return sorted(dense_elements, key=lambda x: x[1], reverse=True)[:10]
    
    def _analyze_content_blocks(self, main_content: Tag) -> List[ContentBlock]:
        """콘텐츠 블록들을 분석합니다."""
        blocks = []
        
        for i, element in enumerate(main_content.find_all(self.content_patterns["text_blocks"])):
            if isinstance(element, Tag):
                text = element.get_text(strip=True)
                if len(text) > 50:  # 최소 텍스트 길이
                    block = ContentBlock(
                        text=text,
                        tag=element.name,
                        class_name=' '.join(element.get('class', [])),
                        id_name=element.get('id', ''),
                        length=len(text),
                        density=len(text) / len(element.get_text()) if len(element.get_text()) > 0 else 0,
                        position=i
                    )
                    blocks.append(block)
        
        return blocks
    
    def _select_best_content(self, blocks: List[ContentBlock]) -> str:
        """최적의 콘텐츠를 선택합니다."""
        if not blocks:
            return ""
        
        # 점수 계산
        scored_blocks = []
        for block in blocks:
            score = 0
            
            # 길이 점수
            length_score = min(block.length / 1000, 1.0)
            score += length_score * 0.3
            
            # 밀도 점수
            density_score = min(block.density * 2, 1.0)
            score += density_score * 0.3
            
            # 태그 점수
            tag_score = 1.0
            if block.tag in ['p', 'div']:
                tag_score = 1.0
            elif block.tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                tag_score = 0.8
            elif block.tag in ['li', 'blockquote']:
                tag_score = 0.9
            else:
                tag_score = 0.7
            score += tag_score * 0.2
            
            # 위치 점수 (중간 부분이 좋음)
            position_score = 1.0
            if len(blocks) > 1:
                relative_position = block.position / len(blocks)
                if 0.2 <= relative_position <= 0.8:
                    position_score = 1.2
                elif relative_position < 0.1 or relative_position > 0.9:
                    position_score = 0.7
            score += position_score * 0.2
            
            scored_blocks.append((block, score))
        
        # 점수순으로 정렬
        scored_blocks.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 블록들 결합
        top_blocks = scored_blocks[:min(5, len(scored_blocks))]
        combined_text = " ".join([block.text for block, score in top_blocks])
        
        return combined_text
    
    def _clean_and_structure_text(self, text: str) -> str:
        """텍스트를 정리하고 구조화합니다."""
        if not text:
            return ""
        
        # HTML 엔티티 디코딩
        text = self._decode_html_entities(text)
        
        # 불필요한 공백 정리
        text = re.sub(r'\s+', ' ', text)
        
        # 노이즈 텍스트 필터링
        for pattern in self.noise_patterns["text_filters"]:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 문단 구분 정리
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def _decode_html_entities(self, text: str) -> str:
        """HTML 엔티티를 디코딩합니다."""
        entities = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&apos;': "'",
            '&hellip;': '...',
            '&mdash;': '—',
            '&ndash;': '–',
            '&copy;': '©',
            '&reg;': '®',
            '&trade;': '™',
            '&deg;': '°',
            '&plusmn;': '±',
            '&times;': '×',
            '&divide;': '÷',
            '&frac12;': '½',
            '&frac14;': '¼',
            '&frac34;': '¾',
            '&lsquo;': ''',
            '&rsquo;': ''',
            '&ldquo;': '"',
            '&rdquo;': '"',
            '&laquo;': '«',
            '&raquo;': '»',
            '&lsaquo;': '‹',
            '&rsaquo;': '›',
            '&sbquo;': '‚',
            '&dbquo;': '„',
            '&dagger;': '†',
            '&Dagger;': '‡',
            '&permil;': '‰',
            '&euro;': '€',
            '&pound;': '£',
            '&cent;': '¢',
            '&yen;': '¥',
            '&sect;': '§',
            '&para;': '¶',
            '&micro;': 'µ',
            '&alpha;': 'α',
            '&beta;': 'β',
            '&gamma;': 'γ',
            '&delta;': 'δ',
            '&epsilon;': 'ε',
            '&zeta;': 'ζ',
            '&eta;': 'η',
            '&theta;': 'θ',
            '&iota;': 'ι',
            '&kappa;': 'κ',
            '&lambda;': 'λ',
            '&mu;': 'μ',
            '&nu;': 'ν',
            '&xi;': 'ξ',
            '&omicron;': 'ο',
            '&pi;': 'π',
            '&rho;': 'ρ',
            '&sigma;': 'σ',
            '&tau;': 'τ',
            '&upsilon;': 'υ',
            '&phi;': 'φ',
            '&chi;': 'χ',
            '&psi;': 'ψ',
            '&omega;': 'ω'
        }
        
        for entity, char in entities.items():
            text = text.replace(entity, char)
            text = text.replace(entity.upper(), char)
        
        return text

def crawl_url_google_style(url: str) -> Optional[str]:
    """Google 스타일 크롤링을 위한 편의 함수"""
    crawler = GoogleStyleCrawler()
    return crawler.crawl_url(url) 