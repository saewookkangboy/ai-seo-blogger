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
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
                ".Campaign__content", ".Column__content", ".Element__content", ".Row__content"
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
                ".loading", ".spinner", ".overlay", ".modal"
            ],
            "exclude_text_patterns": [
                r"^\s*$",  # 빈 텍스트
                r"^Advertisement$", r"^Ad$", r"^Sponsored$",
                r"^Click here$", r"^Read more$", r"^Continue reading$",
                r"^Share this$", r"^Follow us$", r"^Subscribe$",
                r"^Loading\.\.\.$", r"^Please wait$",
                r"^Enable JavaScript$", r"^JavaScript required$",
                r"^Cookie Policy$", r"^Privacy Policy$",
                r"^Terms of Service$", r"^Disclaimer$"
            ]
        }
    
    def crawl_url(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Google 스타일로 URL 크롤링"""
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] [GoogleStyleCrawler] 시도 {attempt+1}: {url}")
                response = self._make_request(url)
                if not response:
                    print(f"[DEBUG] [GoogleStyleCrawler] 응답 없음")
                    continue
                soup = BeautifulSoup(response.text, 'html.parser')
                content = self._extract_google_style_content(soup, url)
                print(f"[DEBUG] [GoogleStyleCrawler] 추출된 content 길이: {len(content) if content else 0}")
                if content and len(content.strip()) > 200:
                    print(f"[DEBUG] [GoogleStyleCrawler] 본문 추출 성공: {len(content)}자")
                    return content
                else:
                    print(f"[DEBUG] [GoogleStyleCrawler] 본문이 너무 짧거나 없음: {len(content) if content else 0}자")
            except Exception as e:
                print(f"[DEBUG] [GoogleStyleCrawler] 예외 발생: {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(1, 3))
        print(f"[DEBUG] [GoogleStyleCrawler] 모든 시도 실패: {url}")
        return None
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Google과 유사한 요청 생성"""
        try:
            # Google과 유사한 지연
            time.sleep(random.uniform(0.5, 2.0))
            
            # 요청 전송
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # 인코딩 처리
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"요청 오류: {e}")
            return None
    
    def _extract_google_style_content(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Google 스타일 콘텐츠 추출"""
        print(f"[DEBUG] [GoogleStyleCrawler] _extract_google_style_content 호출")
        self._remove_noise(soup)
        main_content = self._identify_main_content(soup)
        print(f"[DEBUG] [GoogleStyleCrawler] main_content: {type(main_content)}, {main_content.name if main_content else None}")
        if not main_content:
            print(f"[DEBUG] [GoogleStyleCrawler] 메인 콘텐츠 영역을 찾을 수 없음")
            return None
        content_blocks = self._analyze_content_blocks(main_content)
        print(f"[DEBUG] [GoogleStyleCrawler] content_blocks 개수: {len(content_blocks)}")
        best_content = self._select_best_content(content_blocks)
        print(f"[DEBUG] [GoogleStyleCrawler] best_content 길이: {len(best_content) if best_content else 0}")
        cleaned_content = self._clean_and_structure_text(best_content)
        print(f"[DEBUG] [GoogleStyleCrawler] cleaned_content 길이: {len(cleaned_content) if cleaned_content else 0}")
        return cleaned_content
    
    def _remove_noise(self, soup: BeautifulSoup):
        """노이즈 요소 제거"""
        # 제외할 요소들 제거
        for selector in self.noise_patterns["exclude_selectors"]:
            for element in soup.select(selector):
                element.decompose()
        
        # 스크립트와 스타일 태그 제거
        for element in soup(["script", "style", "noscript"]):
            element.decompose()
    
    def _identify_main_content(self, soup: BeautifulSoup) -> Optional[Any]:
        """메인 콘텐츠 영역 식별 (Google 방식)"""
        print(f"[DEBUG] [GoogleStyleCrawler] _identify_main_content 호출")
        candidates = []
        for selector in self.content_patterns["main_content"]:
            elements = soup.select(selector)
            print(f"[DEBUG] selector: {selector}, elements: {len(elements)}")
            for element in elements:
                if isinstance(element, Tag):
                    score = self._calculate_content_score(element)
                    candidates.append((element, score))
        print(f"[DEBUG] candidates 개수: {len(candidates)}")
        text_dense_elements = self._find_text_dense_elements(soup)
        print(f"[DEBUG] text_dense_elements 개수: {len(text_dense_elements)}")
        for element, density in text_dense_elements:
            score = density * 100
            if isinstance(element, Tag):
                candidates.append((element, score))
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            best_element = candidates[0][0]
            print(f"[DEBUG] best_element: {best_element.name}, 점수: {candidates[0][1]:.2f}, 길이: {len(best_element.get_text(strip=True))}")
            return best_element
        articles = soup.find_all('article')
        print(f"[DEBUG] article 태그 개수: {len(articles)}")
        if articles:
            best = max(articles, key=lambda el: len(el.get_text(strip=True)))
            print(f"[DEBUG] 강제 article 선택: {len(best.get_text(strip=True))}자")
            return best
        if soup.body:
            print(f"[DEBUG] body 전체 사용")
            return soup.body
        return None
    
    def _calculate_content_score(self, element: Tag) -> float:
        """콘텐츠 점수 계산 (Google 방식)"""
        score = 0.0
        
        # 1. 텍스트 길이
        text_length = len(element.get_text(strip=True))
        score += min(text_length / 100, 10)  # 최대 10점
        
        # 2. 링크 밀도 (낮을수록 좋음)
        links = element.find_all('a')
        link_density = len(links) / max(text_length / 100, 1)
        score += max(0, 5 - link_density)  # 링크 밀도가 낮을수록 높은 점수
        
        # 3. 구조적 요소
        structural_elements = element.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li'])
        score += min(len(structural_elements) / 10, 5)  # 최대 5점
        
        # 4. 클래스명 점수
        class_attr = element.get('class')
        if class_attr:
            class_name = ' '.join(class_attr) if isinstance(class_attr, list) else str(class_attr)
            if any(keyword in class_name.lower() for keyword in ['content', 'post', 'article', 'main', 'body']):
                score += 3
        
        # 5. ID 점수
        element_id = element.get('id', '')
        if element_id and any(keyword in element_id.lower() for keyword in ['content', 'post', 'article', 'main']):
            score += 2
        
        return score
    
    def _find_text_dense_elements(self, soup: BeautifulSoup) -> List[Tuple[Tag, float]]:
        """텍스트 밀도가 높은 요소 찾기"""
        dense_elements = []
        
        for element in soup.find_all(['div', 'article', 'section', 'main']):
            if isinstance(element, Tag):
                text_length = len(element.get_text(strip=True))
                total_length = len(str(element))
                
                if total_length > 0:
                    density = text_length / total_length
                    if density > 0.1 and text_length > 500:  # 최소 밀도와 길이
                        dense_elements.append((element, density))
        
        # 밀도 순으로 정렬
        dense_elements.sort(key=lambda x: x[1], reverse=True)
        return dense_elements[:5]  # 상위 5개만 반환
    
    def _analyze_content_blocks(self, main_content: Tag) -> List[ContentBlock]:
        """콘텐츠 블록 분석"""
        print(f"[DEBUG] [GoogleStyleCrawler] _analyze_content_blocks 호출")
        blocks = []
        position = 0
        
        for tag in main_content.find_all(self.content_patterns["text_blocks"]):
            if isinstance(tag, Tag):
                text = tag.get_text(strip=True)
                
                if len(text) > 50:  # 의미있는 텍스트 블록
                    # 텍스트 밀도 계산
                    total_length = len(str(tag))
                    density = len(text) / total_length if total_length > 0 else 0
                    
                    # 클래스명 처리
                    class_attr = tag.get('class')
                    if hasattr(class_attr, '__iter__') and not isinstance(class_attr, str):
                        class_name = ' '.join(class_attr)
                    elif class_attr:
                        class_name = str(class_attr)
                    else:
                        class_name = ''
                    
                    # ID 처리
                    id_attr = tag.get('id')
                    id_name = str(id_attr) if id_attr else ''
                    
                    block = ContentBlock(
                        text=text,
                        tag=tag.name,
                        class_name=class_name,
                        id_name=id_name,
                        length=len(text),
                        density=density,
                        position=position
                    )
                    blocks.append(block)
                    position += 1
        
        print(f"[DEBUG] [GoogleStyleCrawler] 분석된 블록 개수: {len(blocks)}")
        return blocks
    
    def _select_best_content(self, blocks: List[ContentBlock]) -> str:
        """최적 콘텐츠 선택"""
        print(f"[DEBUG] [GoogleStyleCrawler] _select_best_content 호출, 블록 개수: {len(blocks)}")
        if not blocks:
            print(f"[DEBUG] [GoogleStyleCrawler] 블록 없음")
            return ""
        
        # 1. 점수 계산
        scored_blocks = []
        for block in blocks:
            score = 0
            
            # 길이 점수
            score += min(block.length / 100, 10)
            
            # 밀도 점수
            score += block.density * 20
            
            # 태그 점수
            if block.tag in ['p', 'h1', 'h2', 'h3']:
                score += 2
            elif block.tag in ['article', 'section']:
                score += 3
            
            # 클래스명 점수
            try:
                if isinstance(block.class_name, str):
                    class_name_str = block.class_name
                elif block.class_name is not None and hasattr(block.class_name, '__iter__'):
                    class_name_str = ' '.join([str(x) for x in list(block.class_name) if x])
                elif block.class_name:
                    class_name_str = str(block.class_name)
                else:
                    class_name_str = ''
            except Exception:
                class_name_str = ''
            if any(keyword in class_name_str.lower() for keyword in ['content', 'post', 'article']):
                score += 2
            
            scored_blocks.append((block, score))
        
        # 2. 점수 순으로 정렬
        scored_blocks.sort(key=lambda x: x[1], reverse=True)
        
        # 3. 상위 블록들 선택 (연속된 블록 우선)
        selected_blocks = []
        selected_positions = set()
        
        for block, score in scored_blocks:
            if len(selected_blocks) >= 10:  # 최대 10개 블록
                break
            
            # 연속된 블록 우선 선택
            if not selected_positions or any(abs(block.position - pos) <= 2 for pos in selected_positions):
                selected_blocks.append(block)
                selected_positions.add(block.position)
        
        # 4. 위치 순으로 정렬하여 텍스트 구성
        selected_blocks.sort(key=lambda x: x.position)
        
        print(f"[DEBUG] [GoogleStyleCrawler] 선택된 블록 개수: {len(selected_blocks)}")
        return "\n\n".join([block.text for block in selected_blocks])
    
    def _clean_and_structure_text(self, text: str) -> str:
        """텍스트 정제 및 구조화"""
        if not text:
            return ""
        
        # 1. 기본 정제
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # 노이즈 패턴 필터링
            if any(re.match(pattern, line) for pattern in self.noise_patterns["exclude_text_patterns"]):
                continue
            
            # 너무 짧은 라인 제거
            if len(line) < 10:
                continue
            
            # 중복 라인 제거
            if line not in cleaned_lines:
                cleaned_lines.append(line)
        
        # 2. 텍스트 재구성
        cleaned_text = "\n\n".join(cleaned_lines)
        
        # 3. HTML 엔티티 디코딩
        cleaned_text = self._decode_html_entities(cleaned_text)
        
        # 4. 공백 정리
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
        
        return cleaned_text.strip()
    
    def _decode_html_entities(self, text: str) -> str:
        """HTML 엔티티 디코딩"""
        entities = {
            '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>',
            '&quot;': '"', '&apos;': "'", '&copy;': '©', '&reg;': '®',
            '&trade;': '™', '&hellip;': '...', '&mdash;': '—', '&ndash;': '–'
        }
        
        for entity, replacement in entities.items():
            text = text.replace(entity, replacement)
        
        return text

# 기존 인터페이스와의 호환성을 위한 래퍼
def crawl_url_google_style(url: str) -> Optional[str]:
    """Google 스타일로 URL 크롤링"""
    crawler = GoogleStyleCrawler()
    return crawler.crawl_url(url) 