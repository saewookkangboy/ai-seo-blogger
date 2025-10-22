#!/usr/bin/env python3
"""
콘텐츠 길이 정확한 제어 서비스
사용자가 설정한 길이에 맞춰 콘텐츠를 정확하게 생성합니다.
"""

import re
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class ContentLengthController:
    """콘텐츠 길이 제어 클래스"""
    
    def __init__(self):
        # 길이별 목표 단어 수 (한국어 기준)
        self.length_targets = {
            "500": 250,    # 500자 = 약 250단어
            "1000": 500,   # 1000자 = 약 500단어
            "1500": 750,   # 1500자 = 약 750단어
            "2000": 1000,  # 2000자 = 약 1000단어
            "3000": 1500,  # 3000자 = 약 1500단어
            "4000": 2000,  # 4000자 = 약 2000단어
            "5000": 2500   # 5000자 = 약 2500단어
        }
        
        # 허용 오차 범위 (±10%)
        self.tolerance = 0.1
    
    def count_words(self, text: str) -> int:
        """텍스트의 단어 수를 계산합니다."""
        # HTML 태그 제거
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # 공백으로 분리하여 단어 수 계산
        words = clean_text.split()
        return len(words)
    
    def count_characters(self, text: str) -> int:
        """텍스트의 문자 수를 계산합니다 (공백 제외)."""
        # HTML 태그 제거
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # 공백 제거 후 문자 수 계산
        clean_text = re.sub(r'\s+', '', clean_text)
        return len(clean_text)
    
    def get_target_length(self, content_length: str) -> Tuple[int, int]:
        """목표 길이를 반환합니다 (단어 수, 문자 수)."""
        target_words = self.length_targets.get(content_length, 1500)
        target_chars = target_words * 2  # 한국어는 평균 2자/단어
        
        return target_words, target_chars
    
    def is_length_acceptable(self, content: str, target_length: str) -> bool:
        """콘텐츠 길이가 허용 범위 내인지 확인합니다."""
        target_words, target_chars = self.get_target_length(target_length)
        actual_words = self.count_words(content)
        actual_chars = self.count_characters(content)
        
        # 허용 오차 범위 계산
        min_words = int(target_words * (1 - self.tolerance))
        max_words = int(target_words * (1 + self.tolerance))
        
        return min_words <= actual_words <= max_words
    
    def adjust_content_length(self, content: str, target_length: str) -> str:
        """콘텐츠 길이를 조정합니다."""
        target_words, target_chars = self.get_target_length(target_length)
        current_words = self.count_words(content)
        
        if current_words < target_words:
            # 콘텐츠가 짧으면 확장
            return self._expand_content(content, target_words - current_words)
        elif current_words > target_words:
            # 콘텐츠가 길면 축소
            return self._shrink_content(content, current_words - target_words)
        
        return content
    
    def _expand_content(self, content: str, additional_words: int) -> str:
        """콘텐츠를 확장합니다."""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # 기존 콘텐츠 분석
            paragraphs = soup.find_all(['p', 'div'])
            
            if not paragraphs:
                # 단락이 없으면 새 단락 추가
                new_content = f"""
                <p>추가적인 정보를 제공하겠습니다. 이 주제에 대해 더 자세히 알아보면, 
                다양한 관점에서 접근할 수 있는 중요한 요소들이 있습니다. 
                특히 실무에서 활용할 수 있는 구체적인 방법론과 사례를 통해 
                더욱 실용적인 인사이트를 얻을 수 있을 것입니다.</p>
                """
                soup.append(BeautifulSoup(new_content, 'html.parser'))
            else:
                # 마지막 단락에 내용 추가
                last_paragraph = paragraphs[-1]
                additional_text = f"""
                또한, 이와 관련하여 추가적인 고려사항들이 있습니다. 
                실무에서 경험할 수 있는 다양한 시나리오와 그에 따른 
                대응 방안을 미리 준비해두는 것이 중요합니다. 
                특히 최신 트렌드와 기술 발전에 따른 변화를 
                지속적으로 모니터링하고 대응하는 것이 핵심입니다.
                """
                last_paragraph.append(BeautifulSoup(additional_text, 'html.parser'))
            
            return str(soup)
            
        except Exception as e:
            logger.error(f"콘텐츠 확장 중 오류: {e}")
            return content
    
    def _shrink_content(self, content: str, remove_words: int) -> str:
        """콘텐츠를 축소합니다."""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # 단락들을 찾아서 뒤에서부터 제거
            paragraphs = soup.find_all(['p', 'div'])
            
            if len(paragraphs) > 1:
                # 마지막 단락부터 제거
                for i in range(len(paragraphs) - 1, 0, -1):
                    if remove_words <= 0:
                        break
                    
                    paragraph_text = paragraphs[i].get_text()
                    paragraph_words = len(paragraph_text.split())
                    
                    if paragraph_words <= remove_words:
                        paragraphs[i].decompose()
                        remove_words -= paragraph_words
                    else:
                        # 단락의 일부만 제거
                        words = paragraph_text.split()
                        remaining_words = words[:-remove_words]
                        paragraphs[i].string = ' '.join(remaining_words)
                        break
            
            return str(soup)
            
        except Exception as e:
            logger.error(f"콘텐츠 축소 중 오류: {e}")
            return content
    
    def validate_content_structure(self, content: str) -> Dict[str, any]:
        """콘텐츠 구조를 검증합니다."""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # 기본 구조 확인
            has_title = bool(soup.find(['h1', 'h2']))
            has_paragraphs = bool(soup.find_all('p'))
            has_meta = bool(soup.find('meta'))
            
            # 길이 정보
            word_count = self.count_words(content)
            char_count = self.count_characters(content)
            
            return {
                'has_title': has_title,
                'has_paragraphs': has_paragraphs,
                'has_meta': has_meta,
                'word_count': word_count,
                'char_count': char_count,
                'is_well_structured': has_title and has_paragraphs
            }
            
        except Exception as e:
            logger.error(f"콘텐츠 구조 검증 중 오류: {e}")
            return {
                'has_title': False,
                'has_paragraphs': False,
                'has_meta': False,
                'word_count': 0,
                'char_count': 0,
                'is_well_structured': False
            }
    
    def generate_length_report(self, content: str, target_length: str) -> Dict[str, any]:
        """길이 관련 리포트를 생성합니다."""
        target_words, target_chars = self.get_target_length(target_length)
        actual_words = self.count_words(content)
        actual_chars = self.count_characters(content)
        
        word_diff = actual_words - target_words
        char_diff = actual_chars - target_chars
        
        word_percentage = (actual_words / target_words * 100) if target_words > 0 else 0
        char_percentage = (actual_chars / target_chars * 100) if target_chars > 0 else 0
        
        return {
            'target_length': target_length,
            'target_words': target_words,
            'target_chars': target_chars,
            'actual_words': actual_words,
            'actual_chars': actual_chars,
            'word_diff': word_diff,
            'char_diff': char_diff,
            'word_percentage': word_percentage,
            'char_percentage': char_percentage,
            'is_acceptable': self.is_length_acceptable(content, target_length),
            'recommendation': self._get_length_recommendation(word_diff, char_diff)
        }
    
    def _get_length_recommendation(self, word_diff: int, char_diff: int) -> str:
        """길이 조정 권장사항을 반환합니다."""
        if word_diff < -100:
            return "콘텐츠가 너무 짧습니다. 더 자세한 설명을 추가하세요."
        elif word_diff > 100:
            return "콘텐츠가 너무 깁니다. 불필요한 내용을 제거하세요."
        else:
            return "콘텐츠 길이가 적절합니다."

# 전역 인스턴스
content_length_controller = ContentLengthController() 