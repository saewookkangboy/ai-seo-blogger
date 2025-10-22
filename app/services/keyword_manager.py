#!/usr/bin/env python3
"""
키워드 중복 방지 및 관리 서비스
기존 키워드와의 중복을 방지하고 키워드 품질을 관리합니다.
"""

import re
import json
import sqlite3
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter
from difflib import SequenceMatcher
from ..utils.logger import setup_logger
from ..database import SessionLocal
from .. import models, crud

logger = setup_logger(__name__)

class KeywordManager:
    """키워드 중복 방지 및 관리 클래스"""
    
    def __init__(self):
        self.similarity_threshold = 0.8  # 유사도 임계값
        self.max_keywords_per_post = 7   # 포스트당 최대 키워드 수
        self.min_keyword_length = 2      # 최소 키워드 길이
        self.max_keyword_length = 20     # 최대 키워드 길이
        
        # 금지 키워드 목록
        self.blacklist_keywords = {
            'the', 'said', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through',
            'during', 'before', 'after', 'above', 'below', 'between',
            '이', '그', '저', '것', '수', '것', '때', '곳', '말', '일'
        }
    
    def get_existing_keywords(self, db_session) -> Set[str]:
        """데이터베이스에서 기존 키워드들을 가져옵니다."""
        try:
            posts = db_session.query(models.BlogPost).filter(
                models.BlogPost.keywords.isnot(None),
                models.BlogPost.keywords != ''
            ).all()
            
            existing_keywords = set()
            for post in posts:
                if post.keywords:
                    keywords = [kw.strip() for kw in post.keywords.split(',')]
                    existing_keywords.update(keywords)
            
            logger.info(f"기존 키워드 {len(existing_keywords)}개 로드 완료")
            return existing_keywords
            
        except Exception as e:
            logger.error(f"기존 키워드 로드 중 오류: {e}")
            return set()
    
    def check_keyword_similarity(self, new_keyword: str, existing_keywords: Set[str]) -> List[Tuple[str, float]]:
        """새로운 키워드와 기존 키워드 간의 유사도를 확인합니다."""
        similar_keywords = []
        
        for existing in existing_keywords:
            similarity = SequenceMatcher(None, new_keyword.lower(), existing.lower()).ratio()
            if similarity >= self.similarity_threshold:
                similar_keywords.append((existing, similarity))
        
        return sorted(similar_keywords, key=lambda x: x[1], reverse=True)
    
    def filter_keywords(self, keywords: List[str], existing_keywords: Set[str]) -> List[str]:
        """키워드를 필터링하고 중복을 제거합니다."""
        filtered_keywords = []
        
        for keyword in keywords:
            keyword = keyword.strip()
            
            # 기본 필터링
            if not self._is_valid_keyword(keyword):
                continue
            
            # 중복 확인
            if keyword in filtered_keywords:
                continue
            
            # 기존 키워드와 유사도 확인
            similar_keywords = self.check_keyword_similarity(keyword, existing_keywords)
            if similar_keywords:
                logger.warning(f"키워드 '{keyword}'가 기존 키워드와 유사합니다: {similar_keywords[0][0]} (유사도: {similar_keywords[0][1]:.2f})")
                # 유사도가 높으면 건너뛰기
                if similar_keywords[0][1] >= 0.9:
                    continue
            
            filtered_keywords.append(keyword)
            
            # 최대 키워드 수 제한
            if len(filtered_keywords) >= self.max_keywords_per_post:
                break
        
        return filtered_keywords
    
    def _is_valid_keyword(self, keyword: str) -> bool:
        """키워드가 유효한지 확인합니다."""
        if not keyword:
            return False
        
        # 길이 확인
        if len(keyword) < self.min_keyword_length or len(keyword) > self.max_keyword_length:
            return False
        
        # 금지 키워드 확인
        if keyword.lower() in self.blacklist_keywords:
            return False
        
        # 특수문자 확인 (한글, 영문, 숫자, 공백, 쉼표만 허용)
        if not re.match(r'^[가-힣a-zA-Z0-9\s,]+$', keyword):
            return False
        
        return True
    
    def extract_unique_keywords(self, text: str, existing_keywords: Set[str]) -> str:
        """텍스트에서 고유한 키워드를 추출합니다."""
        try:
            # HTML 태그 제거
            clean_text = re.sub(r'<[^>]+>', '', text)
            
            # 한국어 단어 추출
            korean_words = re.findall(r'[가-힣]+', clean_text)
            
            # 영문 단어 추출 (2글자 이상)
            english_words = re.findall(r'\b[a-zA-Z]{2,}\b', clean_text)
            
            # 단어 빈도 계산
            word_freq = Counter(korean_words + english_words)
            
            # 빈도순으로 정렬하여 상위 키워드 추출
            sorted_words = word_freq.most_common(20)
            
            # 키워드 필터링
            filtered_keywords = self.filter_keywords(
                [word for word, freq in sorted_words], 
                existing_keywords
            )
            
            # 최종 키워드 문자열 생성
            final_keywords = ', '.join(filtered_keywords[:self.max_keywords_per_post])
            
            logger.info(f"고유 키워드 추출 완료: {final_keywords}")
            return final_keywords
            
        except Exception as e:
            logger.error(f"키워드 추출 중 오류: {e}")
            return "AI, 기술, 분석"
    
    def suggest_alternative_keywords(self, keyword: str, existing_keywords: Set[str]) -> List[str]:
        """키워드 대안을 제안합니다."""
        alternatives = []
        
        # 유사한 키워드 찾기
        similar_keywords = self.check_keyword_similarity(keyword, existing_keywords)
        
        for similar, similarity in similar_keywords:
            if similarity >= 0.7 and similarity < 0.9:
                alternatives.append(similar)
        
        # 관련 키워드 생성
        if 'AI' in keyword or '인공지능' in keyword:
            alternatives.extend(['머신러닝', '딥러닝', '자연어처리', '컴퓨터비전'])
        elif '기술' in keyword:
            alternatives.extend(['혁신', '개발', '연구', '응용'])
        elif '분석' in keyword:
            alternatives.extend(['데이터', '통계', '인사이트', '결과'])
        
        return list(set(alternatives))[:5]
    
    def get_keyword_statistics(self, db_session) -> Dict:
        """키워드 통계를 반환합니다."""
        try:
            posts = db_session.query(models.BlogPost).filter(
                models.BlogPost.keywords.isnot(None),
                models.BlogPost.keywords != ''
            ).all()
            
            keyword_freq = Counter()
            total_posts = len(posts)
            
            for post in posts:
                if post.keywords:
                    keywords = [kw.strip() for kw in post.keywords.split(',')]
                    keyword_freq.update(keywords)
            
            # 가장 많이 사용된 키워드
            most_common = keyword_freq.most_common(10)
            
            # 중복 키워드 수
            duplicate_keywords = sum(1 for freq in keyword_freq.values() if freq > 1)
            
            return {
                'total_keywords': len(keyword_freq),
                'total_posts': total_posts,
                'duplicate_keywords': duplicate_keywords,
                'most_common_keywords': most_common,
                'average_keywords_per_post': len(keyword_freq) / total_posts if total_posts > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"키워드 통계 생성 중 오류: {e}")
            return {}

# 전역 인스턴스
keyword_manager = KeywordManager() 