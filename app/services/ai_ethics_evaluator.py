# app/services/ai_ethics_evaluator.py

"""
AI 윤리 및 Responsible AI 평가 서비스
생성된 콘텐츠의 윤리적 측면을 평가하고 측정합니다.
"""

import re
import json
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from ..utils.logger import setup_logger
from ..config import settings
import asyncio

logger = setup_logger(__name__)

class AIEthicsEvaluator:
    """
    AI 윤리 평가 클래스
    Responsible AI 원칙에 따라 콘텐츠를 평가합니다.
    """
    
    def __init__(self):
        # 해로운 콘텐츠 패턴 (한국어 및 영어)
        self.harmful_patterns = {
            'violence': [
                r'살인|폭력|학대|고문|살해',
                r'murder|violence|abuse|torture|kill',
                r'자해|자살|자살시도',
                r'suicide|self-harm|self-injury'
            ],
            'hate_speech': [
                r'혐오|차별|인종차별|성차별',
                r'hate|discrimination|racism|sexism',
                r'비하|모욕|욕설',
                r'insult|offensive|profanity'
            ],
            'misinformation': [
                r'확인되지 않은|근거 없는|거짓',
                r'unverified|unfounded|false',
                r'가짜 뉴스|허위 정보',
                r'fake news|misinformation'
            ],
            'privacy_violation': [
                r'개인정보|주민등록번호|전화번호|이메일',
                r'personal information|ssn|phone number|email',
                r'신용카드|계좌번호',
                r'credit card|account number'
            ]
        }
        
        # 편향성 관련 키워드
        self.bias_keywords = {
            'gender': ['남성', '여성', '남녀', '성별', 'male', 'female', 'gender'],
            'age': ['나이', '연령', '젊은', '늙은', 'age', 'young', 'old'],
            'ethnicity': ['인종', '민족', 'ethnicity', 'race'],
            'religion': ['종교', 'religion', 'religious'],
            'political': ['정치', '정당', 'political', 'party']
        }
        
        # AI 사용 명시 관련 키워드
        self.ai_disclosure_keywords = [
            'AI', '인공지능', '자동 생성', '기계 생성',
            'artificial intelligence', 'automated', 'machine generated',
            '생성형 AI', 'generative AI', 'AI 기반'
        ]
        
        # 출처 및 인용 관련 키워드
        self.citation_keywords = {
            'korean': ['출처', '참고', '참조', '인용', '원문', '링크', '사이트', '웹사이트', '홈페이지'],
            'english': ['source', 'reference', 'citation', 'cite', 'link', 'website', 'url', 'according to']
        }
        
        # 신뢰할 수 있는 도메인 패턴
        self.trusted_domains = {
            'high': [
                r'\.edu$', r'\.gov$', r'\.ac\.kr$', r'\.go\.kr$',
                r'wikipedia\.org', r'pubmed\.', r'ieee\.org', r'acm\.org',
                r'nature\.com', r'science\.org', r'nejm\.org', r'bmj\.com'
            ],
            'medium': [
                r'\.org$', r'\.net$', r'news\.', r'bbc\.', r'reuters\.',
                r'forbes\.', r'bloomberg\.', r'wsj\.', r'nytimes\.'
            ],
            'low': [
                r'blogspot\.', r'wordpress\.', r'tumblr\.', r'\.blog',
                r'\.xyz$', r'\.info$'
            ]
        }
        
        # 인용 형식 패턴
        self.citation_patterns = {
            'apa': [
                r'\([A-Z][a-z]+,\s*\d{4}\)',  # (Author, 2024)
                r'[A-Z][a-z]+\s+\([A-Z][a-z]+,\s*\d{4}\)',  # Author (Author, 2024)
            ],
            'mla': [
                r'\([A-Z][a-z]+\s+\d+\)',  # (Author 123)
                r'"[^"]+"\s+\([A-Z][a-z]+\)',  # "Title" (Author)
            ],
            'chicago': [
                r'\d+\.\s+[A-Z][a-z]+,\s+"[^"]+"',  # 1. Author, "Title"
                r'\([A-Z][a-z]+\s+\d{4}:\s*\d+\)',  # (Author 2024: 123)
            ],
            'url': [
                r'https?://[^\s<>"{}|\\^`\[\]]+',  # HTTP/HTTPS URL
                r'www\.[^\s<>"{}|\\^`\[\]]+',  # www URL
            ],
            'html_link': [
                r'<a\s+href=["\']([^"\']+)["\']',  # <a href="...">
                r'href=["\']([^"\']+)["\']',  # href="..."
            ]
        }
    
    async def evaluate_content(self, content: str, title: str = "", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        콘텐츠의 AI 윤리 측면을 종합적으로 평가합니다.
        
        Args:
            content: 평가할 콘텐츠 (HTML 포함 가능)
            title: 콘텐츠 제목
            metadata: 추가 메타데이터 (키워드, 생성 모드 등)
        
        Returns:
            평가 결과 딕셔너리
        """
        try:
            # HTML 태그 제거하여 텍스트만 추출
            text_content = self._extract_text_from_html(content)
            full_text = f"{title} {text_content}".strip()
            
            # 각 평가 항목 실행
            bias_score = await self._evaluate_bias(full_text)
            fairness_score = await self._evaluate_fairness(full_text)
            transparency_score = await self._evaluate_transparency(content, metadata)
            privacy_score = await self._evaluate_privacy(full_text)
            harmful_content_score = await self._evaluate_harmful_content(full_text)
            accuracy_score = await self._evaluate_accuracy(full_text, metadata)
            explainability_score = await self._evaluate_explainability(content, metadata)
            
            # 출처 및 인용 평가 (정확성 평가의 일부이지만 별도로 상세 분석)
            citation_analysis = await self._analyze_citations_and_sources(content, full_text)
            
            # 종합 점수 계산 (가중 평균)
            overall_score = self._calculate_overall_score({
                'bias': bias_score,
                'fairness': fairness_score,
                'transparency': transparency_score,
                'privacy': privacy_score,
                'harmful_content': harmful_content_score,
                'accuracy': accuracy_score,
                'explainability': explainability_score
            })
            
            # 평가 결과 구성
            evaluation_result = {
                'overall_score': overall_score,
                'scores': {
                    'bias': bias_score,
                    'fairness': fairness_score,
                    'transparency': transparency_score,
                    'privacy': privacy_score,
                    'harmful_content': harmful_content_score,
                    'accuracy': accuracy_score,
                    'explainability': explainability_score
                },
                'details': {
                    'bias': self._get_bias_details(full_text),
                    'fairness': self._get_fairness_details(full_text),
                    'transparency': self._get_transparency_details(content, metadata),
                    'privacy': self._get_privacy_details(full_text),
                    'harmful_content': self._get_harmful_content_details(full_text),
                    'accuracy': self._get_accuracy_details(full_text, metadata),
                    'explainability': self._get_explainability_details(content, metadata),
                    'citations': citation_analysis  # 출처 및 인용 상세 분석
                },
                'recommendations': self._generate_recommendations({
                    'bias': bias_score,
                    'fairness': fairness_score,
                    'transparency': transparency_score,
                    'privacy': privacy_score,
                    'harmful_content': harmful_content_score,
                    'accuracy': accuracy_score,
                    'explainability': explainability_score
                }),
                'evaluated_at': datetime.now().isoformat(),
                'content_length': len(text_content),
                'word_count': len(text_content.split())
            }
            
            logger.info(f"AI 윤리 평가 완료: 종합 점수 {overall_score:.2f}/100")
            return evaluation_result
            
        except Exception as e:
            logger.error(f"AI 윤리 평가 중 오류 발생: {e}")
            return self._get_default_evaluation_result()
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """HTML에서 순수 텍스트만 추출"""
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', ' ', html_content)
        # 여러 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    async def _evaluate_bias(self, text: str) -> float:
        """
        편향성 평가 (0-100, 높을수록 좋음)
        특정 그룹에 대한 부정적/긍정적 편향 검사
        """
        score = 100.0
        text_lower = text.lower()
        
        # 편향성 키워드 검사
        bias_indicators = 0
        for category, keywords in self.bias_keywords.items():
            found_keywords = [kw for kw in keywords if kw.lower() in text_lower]
            if found_keywords:
                # 부정적 맥락 검사
                context_window = 50  # 키워드 주변 50자
                for keyword in found_keywords:
                    idx = text_lower.find(keyword.lower())
                    if idx != -1:
                        context = text[max(0, idx-context_window):min(len(text), idx+len(keyword)+context_window)]
                        # 부정적 표현 검사
                        negative_words = ['차별', '혐오', '열등', '우월', 'discrimination', 'hate', 'inferior', 'superior']
                        if any(neg in context.lower() for neg in negative_words):
                            bias_indicators += 1
                            score -= 15
        
        # 균형 잡힌 표현 검사
        gender_balance = self._check_gender_balance(text)
        if not gender_balance:
            score -= 10
        
        return max(0.0, min(100.0, score))
    
    def _check_gender_balance(self, text: str) -> bool:
        """성별 표현의 균형 검사"""
        male_terms = ['남성', '남자', '그', 'he', 'him', 'his', 'male']
        female_terms = ['여성', '여자', '그녀', 'she', 'her', 'female']
        
        male_count = sum(1 for term in male_terms if term.lower() in text.lower())
        female_count = sum(1 for term in female_terms if term.lower() in text.lower())
        
        # 둘 다 없거나 비슷한 비율이면 균형 잡힌 것으로 간주
        if male_count == 0 and female_count == 0:
            return True
        if male_count > 0 and female_count > 0:
            ratio = min(male_count, female_count) / max(male_count, female_count)
            return ratio > 0.3  # 30% 이상 비율이면 균형 잡힌 것으로 간주
        
        return False
    
    async def _evaluate_fairness(self, text: str) -> float:
        """
        공정성 평가 (0-100, 높을수록 좋음)
        다양한 관점과 그룹에 대한 공정한 표현 검사
        """
        score = 100.0
        text_lower = text.lower()
        
        # 배제적 표현 검사
        exclusive_terms = ['오직', '만', 'only', 'exclusively']
        inclusive_terms = ['다양한', '포괄적', 'diverse', 'inclusive', 'various']
        
        exclusive_count = sum(1 for term in exclusive_terms if term in text_lower)
        inclusive_count = sum(1 for term in inclusive_terms if term in text_lower)
        
        if exclusive_count > inclusive_count * 2:
            score -= 20
        
        # 균형 잡힌 관점 표현
        opinion_indicators = ['하지만', '반면', '그러나', 'however', 'but', 'on the other hand']
        if len(opinion_indicators) > 0:
            balanced_views = sum(1 for term in opinion_indicators if term in text_lower)
            if balanced_views > 0:
                score += 5  # 다양한 관점 제시 보너스
        
        return max(0.0, min(100.0, score))
    
    async def _evaluate_transparency(self, content: str, metadata: Optional[Dict] = None) -> float:
        """
        투명성 평가 (0-100, 높을수록 좋음)
        AI 사용 여부 명시 및 생성 과정 투명성
        """
        score = 50.0  # 기본 점수 (AI 사용 명시 없으면 감점)
        content_lower = content.lower()
        
        # AI 사용 명시 검사
        ai_disclosure_found = any(keyword.lower() in content_lower for keyword in self.ai_disclosure_keywords)
        
        if ai_disclosure_found:
            score += 30  # AI 사용 명시 보너스
        
        # 메타데이터에서 AI 모드 확인
        if metadata and metadata.get('ai_mode'):
            score += 20  # AI 모드 정보 제공 보너스
        
        # 생성 일시 정보
        if metadata and metadata.get('created_at'):
            score += 10
        
        # 출처 명시
        source_indicators = ['출처', '참고', 'source', 'reference', '참조']
        if any(indicator in content_lower for indicator in source_indicators):
            score += 10
        
        return max(0.0, min(100.0, score))
    
    async def _evaluate_privacy(self, text: str) -> float:
        """
        프라이버시 평가 (0-100, 높을수록 좋음)
        개인정보 보호 및 민감 정보 노출 검사
        """
        score = 100.0
        text_lower = text.lower()
        
        # 개인정보 패턴 검사
        privacy_violations = 0
        for pattern in self.harmful_patterns['privacy_violation']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                privacy_violations += len(matches)
                score -= 20 * len(matches)
        
        # 이메일 패턴 검사
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            score -= 15 * len(emails)
        
        # 전화번호 패턴 검사
        phone_pattern = r'\b\d{2,3}-\d{3,4}-\d{4}\b|\b\d{10,11}\b'
        phones = re.findall(phone_pattern, text)
        if phones:
            score -= 10 * len(phones)
        
        return max(0.0, min(100.0, score))
    
    async def _evaluate_harmful_content(self, text: str) -> float:
        """
        해로운 콘텐츠 평가 (0-100, 높을수록 좋음)
        폭력, 혐오 표현, 허위 정보 등 검사
        """
        score = 100.0
        text_lower = text.lower()
        
        # 각 해로운 콘텐츠 카테고리 검사
        for category, patterns in self.harmful_patterns.items():
            if category == 'privacy_violation':
                continue  # 프라이버시는 별도 평가
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # 맥락 분석 (부정적 맥락인지 확인)
                    for match in matches:
                        idx = text_lower.find(match.lower())
                        if idx != -1:
                            context = text[max(0, idx-30):min(len(text), idx+len(match)+30)]
                            # 교육적/정보적 맥락인지 확인
                            educational_indicators = ['예방', '교육', '정보', 'prevention', 'education', 'information']
                            is_educational = any(ind in context.lower() for ind in educational_indicators)
                            
                            if not is_educational:
                                score -= 25  # 해로운 콘텐츠 감점
        
        return max(0.0, min(100.0, score))
    
    async def _evaluate_accuracy(self, text: str, metadata: Optional[Dict] = None) -> float:
        """
        정확성 평가 (0-100, 높을수록 좋음)
        사실 확인 가능성 및 출처 명시
        """
        score = 70.0  # 기본 점수
        text_lower = text.lower()
        
        # 출처 명시 검사
        source_indicators = ['출처', '참고', '참조', 'source', 'reference', 'citation']
        source_count = sum(1 for ind in source_indicators if ind in text_lower)
        if source_count > 0:
            score += 15
        
        # URL 존재 여부 (출처 검증 가능성)
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text, re.IGNORECASE)
        if urls:
            score += 10  # URL이 있으면 출처 확인 가능
        
        # 날짜/통계 정보 검사 (구체적 정보는 정확성 높음)
        date_pattern = r'\d{4}년|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}'
        dates = re.findall(date_pattern, text)
        if dates:
            score += 5
        
        # 숫자/통계 정보
        number_pattern = r'\d+%|\d+\.\d+%|\d+명|\d+개'
        numbers = re.findall(number_pattern, text)
        if len(numbers) > 2:
            score += 10
        
        # 불확실성 표현 (정확성 향상)
        uncertainty_indicators = ['추정', '약', '대략', 'approximately', 'estimated', 'about']
        uncertainty_count = sum(1 for ind in uncertainty_indicators if ind in text_lower)
        if uncertainty_count > 0:
            score += 5  # 불확실성 인정은 정확성 향상
        
        return max(0.0, min(100.0, score))
    
    async def _analyze_citations_and_sources(self, content: str, text: str) -> Dict[str, Any]:
        """
        출처 및 인용에 대한 상세 분석
        
        Returns:
            출처 분석 결과 딕셔너리
        """
        try:
            # URL 추출
            urls = self._extract_urls(content, text)
            
            # 인용 형식 검증
            citation_formats = self._detect_citation_formats(text)
            
            # 출처 키워드 검사
            citation_keywords_found = self._detect_citation_keywords(text)
            
            # URL 유효성 검사
            url_validation = await self._validate_urls(urls)
            
            # 출처 신뢰도 평가
            source_credibility = self._evaluate_source_credibility(urls)
            
            # 인용 링크 검증 (HTML 내)
            html_links = self._extract_html_links(content)
            
            # 출처 완전성 검사
            citation_completeness = self._check_citation_completeness(text, urls, citation_formats)
            
            # 종합 점수 계산
            citation_score = self._calculate_citation_score(
                len(urls),
                len(citation_formats),
                url_validation,
                source_credibility,
                citation_completeness
            )
            
            return {
                'citation_score': citation_score,
                'urls_found': urls,
                'url_count': len(urls),
                'url_validation': url_validation,
                'citation_formats': citation_formats,
                'citation_keywords': citation_keywords_found,
                'source_credibility': source_credibility,
                'html_links': html_links,
                'citation_completeness': citation_completeness,
                'recommendations': self._generate_citation_recommendations(
                    urls, citation_formats, url_validation, source_credibility, citation_completeness
                )
            }
            
        except Exception as e:
            logger.error(f"출처 분석 중 오류: {e}")
            return {
                'citation_score': 0,
                'error': str(e)
            }
    
    def _extract_urls(self, content: str, text: str) -> List[str]:
        """콘텐츠에서 URL 추출"""
        urls = []
        
        # HTTP/HTTPS URL 패턴
        http_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        http_urls = re.findall(http_pattern, content + text, re.IGNORECASE)
        urls.extend(http_urls)
        
        # www URL 패턴
        www_pattern = r'www\.[^\s<>"{}|\\^`\[\]]+'
        www_urls = re.findall(www_pattern, content + text, re.IGNORECASE)
        urls.extend([f'http://{url}' if not url.startswith('http') else url for url in www_urls])
        
        # HTML 링크에서 URL 추출
        html_link_pattern = r'<a\s+href=["\']([^"\']+)["\']'
        html_urls = re.findall(html_link_pattern, content, re.IGNORECASE)
        urls.extend(html_urls)
        
        # 중복 제거 및 정규화
        unique_urls = []
        seen = set()
        for url in urls:
            # URL 정규화
            normalized = url.strip().rstrip('.,;:!?)')
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_urls.append(normalized)
        
        return unique_urls
    
    def _detect_citation_formats(self, text: str) -> List[str]:
        """인용 형식 감지"""
        formats_found = []
        
        for format_name, patterns in self.citation_patterns.items():
            if format_name in ['url', 'html_link']:
                continue  # URL은 별도로 처리
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    if format_name not in formats_found:
                        formats_found.append(format_name)
                    break
        
        return formats_found
    
    def _detect_citation_keywords(self, text: str) -> Dict[str, int]:
        """출처 관련 키워드 감지"""
        text_lower = text.lower()
        keywords_found = {}
        
        for lang, keywords in self.citation_keywords.items():
            count = sum(1 for kw in keywords if kw.lower() in text_lower)
            if count > 0:
                keywords_found[lang] = count
        
        return keywords_found
    
    async def _validate_urls(self, urls: List[str]) -> Dict[str, Any]:
        """URL 유효성 검사"""
        validation_results = {
            'valid_count': 0,
            'invalid_count': 0,
            'valid_urls': [],
            'invalid_urls': [],
            'details': []
        }
        
        for url in urls:
            try:
                # URL 파싱 검증
                parsed = urllib.parse.urlparse(url)
                
                # 기본 유효성 검사
                is_valid = (
                    parsed.scheme in ['http', 'https'] and
                    parsed.netloc and
                    len(parsed.netloc) > 0 and
                    '.' in parsed.netloc
                )
                
                if is_valid:
                    validation_results['valid_count'] += 1
                    validation_results['valid_urls'].append(url)
                    validation_results['details'].append({
                        'url': url,
                        'valid': True,
                        'domain': parsed.netloc
                    })
                else:
                    validation_results['invalid_count'] += 1
                    validation_results['invalid_urls'].append(url)
                    validation_results['details'].append({
                        'url': url,
                        'valid': False,
                        'reason': 'Invalid URL format'
                    })
                    
            except Exception as e:
                validation_results['invalid_count'] += 1
                validation_results['invalid_urls'].append(url)
                validation_results['details'].append({
                    'url': url,
                    'valid': False,
                    'reason': str(e)
                })
        
        return validation_results
    
    def _evaluate_source_credibility(self, urls: List[str]) -> Dict[str, Any]:
        """출처 신뢰도 평가"""
        credibility_scores = {
            'high': [],
            'medium': [],
            'low': [],
            'unknown': []
        }
        
        total_score = 0
        max_score = 0
        
        for url in urls:
            try:
                parsed = urllib.parse.urlparse(url)
                domain = parsed.netloc.lower()
                
                # 도메인 신뢰도 평가
                score = 0
                level = 'unknown'
                
                # 높은 신뢰도 도메인
                for pattern in self.trusted_domains['high']:
                    if re.search(pattern, domain):
                        score = 3
                        level = 'high'
                        break
                
                # 중간 신뢰도 도메인
                if level == 'unknown':
                    for pattern in self.trusted_domains['medium']:
                        if re.search(pattern, domain):
                            score = 2
                            level = 'medium'
                            break
                
                # 낮은 신뢰도 도메인
                if level == 'unknown':
                    for pattern in self.trusted_domains['low']:
                        if re.search(pattern, domain):
                            score = 1
                            level = 'low'
                            break
                
                # 알 수 없는 도메인
                if level == 'unknown':
                    score = 1  # 기본 점수
                
                credibility_scores[level].append({
                    'url': url,
                    'domain': domain,
                    'score': score
                })
                
                total_score += score
                max_score += 3  # 최대 점수
                
            except Exception as e:
                logger.warning(f"도메인 신뢰도 평가 중 오류 ({url}): {e}")
                credibility_scores['unknown'].append({
                    'url': url,
                    'domain': 'unknown',
                    'score': 0
                })
        
        # 평균 신뢰도 점수 계산
        avg_credibility = (total_score / max_score * 100) if max_score > 0 else 0
        
        return {
            'distribution': {
                'high': len(credibility_scores['high']),
                'medium': len(credibility_scores['medium']),
                'low': len(credibility_scores['low']),
                'unknown': len(credibility_scores['unknown'])
            },
            'average_score': round(avg_credibility, 2),
            'details': credibility_scores
        }
    
    def _extract_html_links(self, content: str) -> List[Dict[str, str]]:
        """HTML에서 링크 추출"""
        links = []
        
        # <a> 태그에서 링크 추출
        link_pattern = r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
        matches = re.findall(link_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for href, text in matches:
            links.append({
                'url': href,
                'link_text': re.sub(r'<[^>]+>', '', text).strip(),  # HTML 태그 제거
                'has_text': bool(re.sub(r'<[^>]+>', '', text).strip())
            })
        
        return links
    
    def _check_citation_completeness(self, text: str, urls: List[str], citation_formats: List[str]) -> Dict[str, Any]:
        """출처 완전성 검사"""
        completeness_score = 0
        max_score = 0
        issues = []
        
        # URL이 있으면 출처 정보가 있는 것으로 간주
        max_score += 2
        if urls:
            completeness_score += 2
        else:
            issues.append('출처 URL이 없습니다.')
        
        # 인용 형식이 있으면 보너스
        max_score += 1
        if citation_formats:
            completeness_score += 1
        else:
            issues.append('표준 인용 형식이 없습니다.')
        
        # 출처 키워드가 있으면 보너스
        max_score += 1
        citation_keywords = self._detect_citation_keywords(text)
        if citation_keywords:
            completeness_score += 1
        else:
            issues.append('출처 관련 키워드가 없습니다.')
        
        # URL과 텍스트의 연관성 검사
        max_score += 1
        if urls and any(kw in text.lower() for kw in ['출처', '참고', 'source', 'reference']):
            completeness_score += 1
        else:
            if urls:
                issues.append('URL이 있지만 출처 명시가 불명확합니다.')
        
        completeness_percentage = (completeness_score / max_score * 100) if max_score > 0 else 0
        
        return {
            'score': round(completeness_percentage, 2),
            'issues': issues,
            'has_urls': len(urls) > 0,
            'has_citation_format': len(citation_formats) > 0,
            'has_citation_keywords': len(citation_keywords) > 0
        }
    
    def _calculate_citation_score(self, url_count: int, format_count: int, 
                                  url_validation: Dict, source_credibility: Dict,
                                  citation_completeness: Dict) -> float:
        """출처 및 인용 종합 점수 계산"""
        score = 0.0
        
        # URL 존재 (최대 30점)
        if url_count > 0:
            score += min(30, url_count * 10)
        
        # URL 유효성 (최대 20점)
        if url_validation['valid_count'] > 0:
            valid_ratio = url_validation['valid_count'] / max(1, url_validation['valid_count'] + url_validation['invalid_count'])
            score += valid_ratio * 20
        
        # 출처 신뢰도 (최대 25점)
        score += (source_credibility.get('average_score', 0) / 100) * 25
        
        # 인용 형식 (최대 10점)
        if format_count > 0:
            score += min(10, format_count * 5)
        
        # 출처 완전성 (최대 15점)
        score += (citation_completeness.get('score', 0) / 100) * 15
        
        return round(min(100.0, score), 2)
    
    def _generate_citation_recommendations(self, urls: List[str], citation_formats: List[str],
                                          url_validation: Dict, source_credibility: Dict,
                                          citation_completeness: Dict) -> List[str]:
        """출처 및 인용 개선 권장사항 생성"""
        recommendations = []
        
        # URL 관련 권장사항
        if len(urls) == 0:
            recommendations.append('출처 URL을 추가하세요.')
        elif url_validation['invalid_count'] > 0:
            recommendations.append(f"유효하지 않은 URL {url_validation['invalid_count']}개를 수정하세요.")
        
        # 신뢰도 관련 권장사항
        if source_credibility.get('average_score', 0) < 50:
            recommendations.append('신뢰할 수 있는 출처(교육기관, 정부기관, 학술지 등)를 사용하세요.')
        
        # 인용 형식 관련 권장사항
        if len(citation_formats) == 0:
            recommendations.append('표준 인용 형식(APA, MLA, Chicago 등)을 사용하세요.')
        
        # 완전성 관련 권장사항
        if citation_completeness.get('score', 0) < 70:
            for issue in citation_completeness.get('issues', []):
                recommendations.append(issue)
        
        if not recommendations:
            recommendations.append('출처 및 인용이 적절하게 표시되어 있습니다.')
        
        return recommendations
    
    async def _evaluate_explainability(self, content: str, metadata: Optional[Dict] = None) -> float:
        """
        설명 가능성 평가 (0-100, 높을수록 좋음)
        AI 결정 과정의 설명 가능성
        """
        score = 60.0  # 기본 점수
        content_lower = content.lower()
        
        # 구조화된 정보 (설명 가능성 향상)
        structured_indicators = [
            '<div class="faq', '<div class="comparison',
            '<h1>', '<h2>', '<h3>', '<ul>', '<ol>',
            '질문', '답변', 'FAQ', 'Q&A'
        ]
        structured_count = sum(1 for ind in structured_indicators if ind in content_lower)
        if structured_count > 3:
            score += 20
        
        # 메타데이터에서 생성 정보
        if metadata:
            if metadata.get('ai_mode'):
                score += 10
            if metadata.get('keywords'):
                score += 10
        
        # 키워드 명시 (SEO 관련이지만 설명 가능성에도 기여)
        keyword_indicators = ['키워드', '주제', 'keyword', 'topic']
        if any(ind in content_lower for ind in keyword_indicators):
            score += 10
        
        return max(0.0, min(100.0, score))
    
    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """종합 점수 계산 (가중 평균)"""
        weights = {
            'harmful_content': 0.25,  # 가장 중요
            'privacy': 0.20,
            'bias': 0.15,
            'fairness': 0.15,
            'transparency': 0.10,
            'accuracy': 0.10,
            'explainability': 0.05
        }
        
        weighted_sum = sum(scores.get(key, 0) * weight for key, weight in weights.items())
        return round(weighted_sum, 2)
    
    def _get_bias_details(self, text: str) -> Dict[str, Any]:
        """편향성 상세 정보"""
        detected_categories = []
        for category, keywords in self.bias_keywords.items():
            if any(kw.lower() in text.lower() for kw in keywords):
                detected_categories.append(category)
        
        return {
            'detected_categories': detected_categories,
            'gender_balance': self._check_gender_balance(text),
            'recommendation': '다양한 그룹에 대한 균형 잡힌 표현을 사용하세요.' if detected_categories else '편향성 문제 없음'
        }
    
    def _get_fairness_details(self, text: str) -> Dict[str, Any]:
        """공정성 상세 정보"""
        return {
            'balanced_views': '하지만' in text or 'however' in text.lower(),
            'inclusive_language': any(term in text.lower() for term in ['다양한', '포괄적', 'diverse', 'inclusive']),
            'recommendation': '다양한 관점을 포함하고 포괄적인 언어를 사용하세요.'
        }
    
    def _get_transparency_details(self, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """투명성 상세 정보"""
        ai_disclosed = any(kw.lower() in content.lower() for kw in self.ai_disclosure_keywords)
        return {
            'ai_disclosure': ai_disclosed,
            'ai_mode': metadata.get('ai_mode') if metadata else None,
            'has_metadata': metadata is not None,
            'recommendation': 'AI 사용 여부를 명시하고 생성 정보를 제공하세요.' if not ai_disclosed else 'AI 사용이 적절히 명시됨'
        }
    
    def _get_privacy_details(self, text: str) -> Dict[str, Any]:
        """프라이버시 상세 정보"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        phone_pattern = r'\b\d{2,3}-\d{3,4}-\d{4}\b'
        phones = re.findall(phone_pattern, text)
        
        return {
            'email_count': len(emails),
            'phone_count': len(phones),
            'privacy_risk': len(emails) > 0 or len(phones) > 0,
            'recommendation': '개인정보를 제거하거나 마스킹 처리하세요.' if (emails or phones) else '프라이버시 문제 없음'
        }
    
    def _get_harmful_content_details(self, text: str) -> Dict[str, Any]:
        """해로운 콘텐츠 상세 정보"""
        detected_categories = []
        for category, patterns in self.harmful_patterns.items():
            if category == 'privacy_violation':
                continue
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    detected_categories.append(category)
                    break
        
        return {
            'detected_categories': list(set(detected_categories)),
            'risk_level': 'high' if detected_categories else 'low',
            'recommendation': '해로운 콘텐츠를 제거하거나 교육적 맥락으로 재작성하세요.' if detected_categories else '해로운 콘텐츠 없음'
        }
    
    def _get_accuracy_details(self, text: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """정확성 상세 정보"""
        source_indicators = ['출처', '참고', '참조', 'source', 'reference']
        has_sources = any(ind in text.lower() for ind in source_indicators)
        
        # URL 추출
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text, re.IGNORECASE)
        
        return {
            'has_sources': has_sources,
            'has_urls': len(urls) > 0,
            'url_count': len(urls),
            'has_dates': bool(re.search(r'\d{4}', text)),
            'has_statistics': len(re.findall(r'\d+%', text)) > 0,
            'recommendation': '출처를 명시하고 사실을 확인 가능하게 하세요.' if not has_sources else '정확성 확보됨'
        }
    
    def _get_explainability_details(self, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """설명 가능성 상세 정보"""
        has_structure = any(ind in content.lower() for ind in ['<h1>', '<h2>', '<div class'])
        return {
            'has_structure': has_structure,
            'has_metadata': metadata is not None,
            'recommendation': '구조화된 형식과 메타데이터를 제공하세요.'
        }
    
    def _generate_recommendations(self, scores: Dict[str, float]) -> List[str]:
        """점수 기반 개선 권장사항 생성"""
        recommendations = []
        
        if scores['harmful_content'] < 80:
            recommendations.append('해로운 콘텐츠를 제거하거나 교육적 맥락으로 재작성하세요.')
        
        if scores['privacy'] < 80:
            recommendations.append('개인정보 및 민감 정보를 제거하거나 마스킹 처리하세요.')
        
        if scores['bias'] < 70:
            recommendations.append('다양한 그룹에 대한 균형 잡힌 표현을 사용하세요.')
        
        if scores['fairness'] < 70:
            recommendations.append('다양한 관점을 포함하고 포괄적인 언어를 사용하세요.')
        
        if scores['transparency'] < 60:
            recommendations.append('AI 사용 여부를 명시하고 생성 정보를 제공하세요.')
        
        if scores['accuracy'] < 70:
            recommendations.append('출처를 명시하고 사실을 확인 가능하게 하세요.')
        
        if scores['explainability'] < 60:
            recommendations.append('구조화된 형식과 메타데이터를 제공하세요.')
        
        if not recommendations:
            recommendations.append('모든 Responsible AI 원칙을 잘 준수하고 있습니다.')
        
        return recommendations
    
    def _get_default_evaluation_result(self) -> Dict[str, Any]:
        """기본 평가 결과 (오류 발생 시)"""
        return {
            'overall_score': 0.0,
            'scores': {
                'bias': 0.0,
                'fairness': 0.0,
                'transparency': 0.0,
                'privacy': 0.0,
                'harmful_content': 0.0,
                'accuracy': 0.0,
                'explainability': 0.0
            },
            'details': {},
            'recommendations': ['평가 중 오류가 발생했습니다.'],
            'evaluated_at': datetime.now().isoformat(),
            'error': True
        }


# 싱글톤 인스턴스
ai_ethics_evaluator = AIEthicsEvaluator()

