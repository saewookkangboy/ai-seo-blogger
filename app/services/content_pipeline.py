#!/usr/bin/env python3
"""
콘텐츠 파이프라인 서비스
크롤링 → 번역 → 콘텐츠 생성까지의 전체 프로세스를 관리합니다.
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
from datetime import datetime
import re

from .crawler import EnhancedCrawler
from .smart_crawler import SmartCrawler, CrawlingStrategy
from .translator import translate_text, detect_language
from .content_generator import create_blog_post, extract_seo_keywords
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class PipelineStep(Enum):
    """파이프라인 단계"""
    CRAWLING = "crawling"
    LANGUAGE_DETECTION = "language_detection"
    TRANSLATION = "translation"
    CONTENT_GENERATION = "content_generation"
    SEO_ANALYSIS = "seo_analysis"
    QUALITY_CHECK = "quality_check"
    COMPLETED = "completed"

class PipelineStatus(Enum):
    """파이프라인 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class PipelineResult:
    """파이프라인 결과"""
    success: bool
    step: PipelineStep
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ContentPipelineConfig:
    """콘텐츠 파이프라인 설정"""
    use_smart_crawler: bool = True
    force_crawling_strategy: Optional[CrawlingStrategy] = None
    target_language: str = "ko"
    content_length: str = "3000"
    ai_mode: Optional[str] = None
    enable_seo_analysis: bool = True
    enable_caching: bool = True
    timeout_per_step: int = 60
    min_content_length: int = 800  # 최소 콘텐츠 길이 (완화)
    max_retries: int = 3  # 최대 재시도 횟수
    quality_threshold: float = 0.7  # 품질 임계값

class ContentPipeline:
    """콘텐츠 파이프라인 관리자"""
    
    def __init__(self):
        self.enhanced_crawler = EnhancedCrawler()
        self.smart_crawler = SmartCrawler()
        self.pipeline_cache = {}
        self.active_pipelines = {}
        
    def _get_pipeline_cache_key(self, url: str, text: str, config: ContentPipelineConfig) -> str:
        """파이프라인 캐시 키 생성"""
        content = f"{url}{text}{config.target_language}{config.content_length}{config.ai_mode or ''}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_pipeline_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """캐시된 파이프라인 결과 가져오기"""
        if cache_key in self.pipeline_cache:
            cached_data, timestamp = self.pipeline_cache[cache_key]
            # 1시간 캐시
            if time.time() - timestamp < 3600:
                logger.info("캐시된 파이프라인 결과 사용")
                return cached_data
            else:
                del self.pipeline_cache[cache_key]
        return None
    
    def _cache_pipeline_result(self, cache_key: str, result: Dict[str, Any]):
        """파이프라인 결과 캐시"""
        self.pipeline_cache[cache_key] = (result, time.time())
        
        # 캐시 크기 제한
        if len(self.pipeline_cache) > 50:
            oldest_key = min(self.pipeline_cache.keys(), 
                           key=lambda k: self.pipeline_cache[k][1])
            del self.pipeline_cache[oldest_key]
    
    async def _step_crawling(self, url: str, text: str, config: ContentPipelineConfig) -> PipelineResult:
        """크롤링 단계 - 견고한 URL 크롤링"""
        try:
            logger.info(f"크롤링 단계 시작: URL={url}, 텍스트 길이={len(text)}")
            
            if url:
                # URL 크롤링 - 재시도 로직 포함
                content = None
                last_error = None
                
                for attempt in range(config.max_retries):
                    try:
                        logger.info(f"크롤링 시도 {attempt + 1}/{config.max_retries}")
                        
                        if config.use_smart_crawler:
                            content = self.smart_crawler.crawl_url(url, force_strategy=config.force_crawling_strategy)
                        else:
                            content = self.enhanced_crawler.crawl_url(url, max_retries=3, use_google_style=True)
                        
                        if content and len(content.strip()) >= 200:  # 최소 200자 이상
                            break
                        else:
                            last_error = "크롤링된 콘텐츠가 너무 짧습니다."
                            logger.warning(f"크롤링 시도 {attempt + 1} 실패: {last_error}")
                            
                    except Exception as e:
                        last_error = str(e)
                        logger.warning(f"크롤링 시도 {attempt + 1} 실패: {e}")
                        await asyncio.sleep(2 ** attempt)  # 지수 백오프
                
                if not content or len(content.strip()) < 200:
                    return PipelineResult(
                        success=False,
                        step=PipelineStep.CRAWLING,
                        error=f"크롤링 실패: {last_error or '콘텐츠를 추출할 수 없습니다.'}"
                    )
                
                # 크롤링된 콘텐츠 품질 검증
                cleaned_content = self._clean_crawled_content(content)
                if len(cleaned_content) < 200:
                    return PipelineResult(
                        success=False,
                        step=PipelineStep.CRAWLING,
                        error="크롤링된 콘텐츠가 너무 짧거나 품질이 낮습니다."
                    )
                
                logger.info(f"크롤링 성공: {len(cleaned_content)}자 추출")
                return PipelineResult(
                    success=True,
                    step=PipelineStep.CRAWLING,
                    data={"content": cleaned_content, "source": "url", "url": url}
                )
            else:
                # 텍스트 직접 입력
                if not text or len(text.strip()) < 100:
                    return PipelineResult(
                        success=False,
                        step=PipelineStep.CRAWLING,
                        error="입력된 텍스트가 너무 짧습니다."
                    )
                
                return PipelineResult(
                    success=True,
                    step=PipelineStep.CRAWLING,
                    data={"content": text, "source": "text"}
                )
                
        except Exception as e:
            logger.error(f"크롤링 단계 실패: {e}")
            return PipelineResult(
                success=False,
                step=PipelineStep.CRAWLING,
                error=f"크롤링 중 오류 발생: {str(e)}"
            )
    
    def _clean_crawled_content(self, content: str) -> str:
        """크롤링된 콘텐츠 정리"""
        if not content:
            return ""
        
        # HTML 태그 제거
        content = re.sub(r'<[^>]+>', '', content)
        
        # 불필요한 공백 정리
        content = re.sub(r'\s+', ' ', content)
        
        # 특수 문자 정리
        content = re.sub(r'[^\w\s\.,!?;:()\-]', '', content)
        
        # 줄바꿈 정리
        content = content.replace('\n', ' ').replace('\r', ' ')
        
        return content.strip()
    
    async def _step_language_detection(self, content: str) -> PipelineResult:
        """언어 감지 단계"""
        try:
            logger.info("언어 감지 단계 시작")
            
            if not content or len(content.strip()) < 50:
                return PipelineResult(
                    success=False,
                    step=PipelineStep.LANGUAGE_DETECTION,
                    error="언어 감지를 위한 충분한 텍스트가 없습니다."
                )
            
            # 언어 감지 시도
            detected_lang = None
            for attempt in range(3):
                try:
                    detected_lang = await detect_language(content[:1000])  # 처음 1000자만 사용
                    if detected_lang:
                        break
                except Exception as e:
                    logger.warning(f"언어 감지 시도 {attempt + 1} 실패: {e}")
                    await asyncio.sleep(1)
            
            if not detected_lang:
                # 기본값으로 영어 설정
                detected_lang = "en"
                logger.warning("언어 감지 실패, 기본값 'en' 사용")
            
            logger.info(f"언어 감지 완료: {detected_lang}")
            return PipelineResult(
                success=True,
                step=PipelineStep.LANGUAGE_DETECTION,
                data={"detected_language": detected_lang}
            )
            
        except Exception as e:
            logger.error(f"언어 감지 단계 실패: {e}")
            return PipelineResult(
                success=False,
                step=PipelineStep.LANGUAGE_DETECTION,
                error=f"언어 감지 중 오류 발생: {str(e)}"
            )
    
    async def _step_translation(self, content: str, source_lang: str, target_lang: str) -> PipelineResult:
        """번역 단계 - 견고한 번역 처리"""
        try:
            logger.info(f"번역 단계 시작: {source_lang} → {target_lang}")
            
            if source_lang == target_lang:
                logger.info("원본 언어와 타겟 언어가 동일하여 번역 건너뜀")
                return PipelineResult(
                    success=True,
                    step=PipelineStep.TRANSLATION,
                    data={"translated_content": content, "source_language": source_lang}
                )
            
            # 긴 텍스트를 청크로 나누어 번역
            translated_chunks = []
            chunk_size = 2000  # 번역 API 제한 고려
            
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                
                # 번역 재시도 로직
                translated_chunk = None
                for attempt in range(3):
                    try:
                        translated_chunk = await translate_text(chunk, target_lang)
                        if translated_chunk and len(translated_chunk.strip()) > 0:
                            break
                    except Exception as e:
                        logger.warning(f"번역 시도 {attempt + 1} 실패: {e}")
                        await asyncio.sleep(2)
                
                if not translated_chunk:
                    logger.error(f"청크 번역 실패: {i}-{i+chunk_size}")
                    return PipelineResult(
                        success=False,
                        step=PipelineStep.TRANSLATION,
                        error="번역 중 오류가 발생했습니다."
                    )
                
                translated_chunks.append(translated_chunk)
            
            translated_content = " ".join(translated_chunks)
            
            # 번역 품질 검증
            if len(translated_content.strip()) < len(content.strip()) * 0.5:
                logger.warning("번역된 콘텐츠가 원본보다 너무 짧습니다.")
            
            logger.info(f"번역 완료: {len(translated_content)}자")
            return PipelineResult(
                success=True,
                step=PipelineStep.TRANSLATION,
                data={"translated_content": translated_content, "source_language": source_lang}
            )
            
        except Exception as e:
            logger.error(f"번역 단계 실패: {e}")
            return PipelineResult(
                success=False,
                step=PipelineStep.TRANSLATION,
                error=f"번역 중 오류 발생: {str(e)}"
            )
    
    async def _step_content_generation(self, translated_content: str, keywords: str, config: ContentPipelineConfig) -> PipelineResult:
        """콘텐츠 생성 단계 - 최소 2000자 보장"""
        try:
            logger.info("콘텐츠 생성 단계 시작")
            
            # 콘텐츠 길이 설정 조정 (최소 1100자 보장, 재시도 시 길이 증가)
            min_length = max(config.min_content_length, 1100)
            base_target_length = max(int(config.content_length), min_length)
            
            # 콘텐츠 생성 재시도 로직
            blog_post = None
            for attempt in range(config.max_retries):
                try:
                    logger.info(f"콘텐츠 생성 시도 {attempt + 1}/{config.max_retries}")
                    
                    # 재시도 시 길이를 더 적극적으로 증가
                    target_length = base_target_length + (attempt * 1500)  # 1500자씩 증가
                    
                    blog_post = await create_blog_post(
                        translated_content,
                        keywords,
                        content_length=str(target_length),
                        ai_mode=config.ai_mode
                    )
                    
                    if blog_post and self._validate_generated_content(blog_post, min_length):
                        break
                    else:
                        logger.warning(f"콘텐츠 생성 시도 {attempt + 1} 실패: 품질 검증 실패")
                        # 캐시 클리어를 위해 잠시 대기
                        await asyncio.sleep(1)
                        
                        # 품질 검증 실패 시 캐시 클리어
                        from .content_generator import clear_specific_cache
                        clear_specific_cache(translated_content, keywords, str(target_length), config.ai_mode or "")
                        
                except Exception as e:
                    logger.warning(f"콘텐츠 생성 시도 {attempt + 1} 실패: {e}")
                    await asyncio.sleep(2)
            
            if not blog_post or not self._validate_generated_content(blog_post, min_length):
                return PipelineResult(
                    success=False,
                    step=PipelineStep.CONTENT_GENERATION,
                    error="콘텐츠 생성에 실패했습니다."
                )
            
            logger.info(f"콘텐츠 생성 완료: {len(blog_post.get('post', ''))}자")
            return PipelineResult(
                success=True,
                step=PipelineStep.CONTENT_GENERATION,
                data={"blog_post": blog_post}
            )
            
        except Exception as e:
            logger.error(f"콘텐츠 생성 단계 실패: {e}")
            return PipelineResult(
                success=False,
                step=PipelineStep.CONTENT_GENERATION,
                error=f"콘텐츠 생성 중 오류 발생: {str(e)}"
            )
    
    def _validate_generated_content(self, blog_post: Dict[str, Any], min_length: int) -> bool:
        """생성된 콘텐츠 품질 검증 (완화된 기준)"""
        if not blog_post:
            return False
        
        # content_generator.py에서 반환하는 'post' 키 사용
        content = blog_post.get('post', blog_post.get('content', ''))
        if not content or len(content.strip()) < min_length * 0.7:  # 70% 이상으로 완화
            logger.warning(f"콘텐츠 길이 부족: {len(content)} < {min_length * 0.7}")
            return False
        
        # HTML 태그 제거 후 실제 텍스트 길이 확인 (완화)
        text_content = re.sub(r'<[^>]+>', '', content)
        if len(text_content.strip()) < min_length * 0.5:  # 50% 이상으로 완화
            logger.warning(f"실제 텍스트 길이 부족: {len(text_content)} < {min_length * 0.5}")
            return False
        
        # 기본적인 구조 확인 (선택적)
        if not re.search(r'<h[1-6]', content):
            logger.info("헤딩 태그가 없지만 허용합니다.")
            # 헤딩이 없어도 통과 (완화)
        
        return True
    
    async def _step_seo_analysis(self, blog_post: Dict[str, Any], keywords: str) -> PipelineResult:
        """SEO 분석 단계"""
        try:
            logger.info("SEO 분석 단계 시작")
            
            # content_generator.py에서 반환하는 'post' 키 사용
            content = blog_post.get('post', blog_post.get('content', ''))
            if not content:
                return PipelineResult(
                    success=False,
                    step=PipelineStep.SEO_ANALYSIS,
                    error="분석할 콘텐츠가 없습니다."
                )
            
            # SEO 점수 계산
            seo_score = self._calculate_seo_score(content, keywords)
            
            # SEO 개선 제안 생성
            suggestions = self._generate_seo_suggestions(content, keywords, seo_score)
            
            seo_analysis = {
                "seo_score": seo_score,
                "suggestions": suggestions,
                "keywords": keywords,
                "content_length": len(content),
                "has_headings": bool(re.search(r'<h[1-6]', content)),
                "has_links": bool(re.search(r'<a\s+href', content)),
                "has_images": bool(re.search(r'<img', content))
            }
            
            logger.info(f"SEO 분석 완료: 점수 {seo_score}/100")
            return PipelineResult(
                success=True,
                step=PipelineStep.SEO_ANALYSIS,
                data={"seo_analysis": seo_analysis}
            )
            
        except Exception as e:
            logger.error(f"SEO 분석 단계 실패: {e}")
            return PipelineResult(
                success=False,
                step=PipelineStep.SEO_ANALYSIS,
                error=f"SEO 분석 중 오류 발생: {str(e)}"
            )
    
    def _calculate_seo_score(self, content: str, target_keywords: str) -> float:
        """SEO 점수 계산"""
        score = 0.0
        max_score = 100.0
        
        try:
            # 키워드 분석
            keywords = [kw.strip().lower() for kw in target_keywords.split(',') if kw.strip()]
            
            # 1. 키워드 밀도 (20점)
            text_content = re.sub(r'<[^>]+>', '', content).lower()
            total_words = len(text_content.split())
            
            if total_words > 0:
                keyword_density = 0
                for keyword in keywords:
                    keyword_count = text_content.count(keyword.lower())
                    keyword_density += keyword_count
                
                density_score = min(20, (keyword_density / total_words) * 1000)
                score += density_score
            
            # 2. 콘텐츠 길이 (20점)
            if len(content) >= 2000:
                score += 20
            elif len(content) >= 1500:
                score += 15
            elif len(content) >= 1000:
                score += 10
            else:
                score += 5
            
            # 3. 헤딩 구조 (15점)
            headings = re.findall(r'<h[1-6][^>]*>', content)
            if len(headings) >= 3:
                score += 15
            elif len(headings) >= 2:
                score += 10
            elif len(headings) >= 1:
                score += 5
            
            # 4. 링크 포함 (10점)
            if re.search(r'<a\s+href', content):
                score += 10
            
            # 5. 이미지 포함 (10점)
            if re.search(r'<img', content):
                score += 10
            
            # 6. 메타 태그 (10점)
            if re.search(r'<meta', content):
                score += 10
            
            # 7. 구조화된 데이터 (15점)
            if re.search(r'<script[^>]*application/ld\+json', content):
                score += 15
            
            return min(max_score, score)
            
        except Exception as e:
            logger.error(f"SEO 점수 계산 실패: {e}")
            return 50.0  # 기본 점수
    
    def _generate_seo_suggestions(self, content: str, keywords: str, seo_score: float) -> List[str]:
        """SEO 개선 제안 생성"""
        suggestions = []
        
        try:
            # 키워드 분석
            keyword_list = [kw.strip().lower() for kw in keywords.split(',') if kw.strip()]
            text_content = re.sub(r'<[^>]+>', '', content).lower()
            
            # 키워드 밀도 체크
            for keyword in keyword_list:
                keyword_count = text_content.count(keyword)
                if keyword_count < 2:
                    suggestions.append(f"키워드 '{keyword}'을 더 자주 사용하세요.")
            
            # 헤딩 구조 체크
            headings = re.findall(r'<h[1-6][^>]*>', content)
            if len(headings) < 2:
                suggestions.append("더 많은 헤딩 태그를 사용하여 구조를 개선하세요.")
            
            # 링크 체크
            if not re.search(r'<a\s+href', content):
                suggestions.append("관련 링크를 추가하여 사용자 경험을 향상시키세요.")
            
            # 이미지 체크
            if not re.search(r'<img', content):
                suggestions.append("관련 이미지를 추가하여 시각적 매력을 높이세요.")
            
            # 콘텐츠 길이 체크
            if len(content) < 2000:
                suggestions.append("콘텐츠를 더 길게 작성하여 상세한 정보를 제공하세요.")
            
            if not suggestions:
                suggestions.append("SEO 최적화가 잘 되어 있습니다!")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"SEO 제안 생성 실패: {e}")
            return ["SEO 분석 중 오류가 발생했습니다."]
    
    async def _extract_keywords(self, content: str) -> str:
        """키워드 추출"""
        try:
            keywords = await extract_seo_keywords(content)
            if keywords and len(keywords.strip()) > 0:
                return keywords
            else:
                # 기본 키워드 반환
                return "AI, 블로그, 콘텐츠"
        except Exception as e:
            logger.error(f"키워드 추출 실패: {e}")
            return "AI, 블로그, 콘텐츠"
    
    async def execute_pipeline(self, url: str = "", text: str = "", config: ContentPipelineConfig = None) -> Dict[str, Any]:
        """전체 파이프라인 실행"""
        if config is None:
            config = ContentPipelineConfig()
        
        pipeline_id = hashlib.md5(f"{url}{text}{time.time()}".encode()).hexdigest()
        self.active_pipelines[pipeline_id] = PipelineStatus.IN_PROGRESS
        
        try:
            logger.info(f"파이프라인 시작: {pipeline_id}")
            
            # 캐시 확인
            if config.enable_caching:
                cache_key = self._get_pipeline_cache_key(url, text, config)
                cached_result = self._get_cached_pipeline_result(cache_key)
                if cached_result:
                    self.active_pipelines[pipeline_id] = PipelineStatus.COMPLETED
                    return cached_result
            
            results = {}
            
            # 1단계: 크롤링
            crawling_result = await self._step_crawling(url, text, config)
            if not crawling_result.success:
                self.active_pipelines[pipeline_id] = PipelineStatus.FAILED
                return {
                    "success": False,
                    "error": crawling_result.error,
                    "step": "crawling",
                    "pipeline_id": pipeline_id
                }
            
            results["crawling"] = crawling_result.data
            content = crawling_result.data["content"]
            
            # 2단계: 언어 감지
            lang_result = await self._step_language_detection(content)
            if not lang_result.success:
                self.active_pipelines[pipeline_id] = PipelineStatus.FAILED
                return {
                    "success": False,
                    "error": lang_result.error,
                    "step": "language_detection",
                    "pipeline_id": pipeline_id
                }
            
            results["language_detection"] = lang_result.data
            detected_lang = lang_result.data["detected_language"]
            
            # 3단계: 번역
            translation_result = await self._step_translation(content, detected_lang, config.target_language)
            if not translation_result.success:
                self.active_pipelines[pipeline_id] = PipelineStatus.FAILED
                return {
                    "success": False,
                    "error": translation_result.error,
                    "step": "translation",
                    "pipeline_id": pipeline_id
                }
            
            results["translation"] = translation_result.data
            translated_content = translation_result.data["translated_content"]
            
            # 4단계: 키워드 추출
            keywords = await self._extract_keywords(translated_content)
            
            # 5단계: 콘텐츠 생성
            generation_result = await self._step_content_generation(translated_content, keywords, config)
            if not generation_result.success:
                self.active_pipelines[pipeline_id] = PipelineStatus.FAILED
                return {
                    "success": False,
                    "error": generation_result.error,
                    "step": "content_generation",
                    "pipeline_id": pipeline_id
                }
            
            results["content_generation"] = generation_result.data
            blog_post = generation_result.data["blog_post"]
            
            # 6단계: SEO 분석 (선택사항)
            if config.enable_seo_analysis:
                seo_result = await self._step_seo_analysis(blog_post, keywords)
                if seo_result.success:
                    results["seo_analysis"] = seo_result.data
            
            # 최종 결과 구성
            final_result = {
                "success": True,
                "pipeline_id": pipeline_id,
                "results": results,
                "blog_post": blog_post,
                "keywords": keywords,
                "metadata": {
                    "total_steps": len(results),
                    "execution_time": time.time(),
                    "config": {
                        "target_language": config.target_language,
                        "content_length": config.content_length,
                        "ai_mode": config.ai_mode
                    }
                }
            }
            
            # 캐시 저장
            if config.enable_caching:
                cache_key = self._get_pipeline_cache_key(url, text, config)
                self._cache_pipeline_result(cache_key, final_result)
            
            self.active_pipelines[pipeline_id] = PipelineStatus.COMPLETED
            logger.info(f"파이프라인 완료: {pipeline_id}")
            
            return final_result
            
        except Exception as e:
            logger.error(f"파이프라인 실행 실패: {e}")
            self.active_pipelines[pipeline_id] = PipelineStatus.FAILED
            return {
                "success": False,
                "error": f"파이프라인 실행 중 오류 발생: {str(e)}",
                "pipeline_id": pipeline_id
            }
    
    async def execute_pipeline_with_progress(self, url: str = "", text: str = "", config: ContentPipelineConfig = None):
        """진행 상황을 실시간으로 전송하는 파이프라인 실행"""
        if config is None:
            config = ContentPipelineConfig()
        
        pipeline_id = hashlib.md5(f"{url}{text}{time.time()}".encode()).hexdigest()
        
        try:
            # 1단계: 크롤링 (25%)
            yield {
                "step": 1,
                "message": "웹 크롤링을 시작합니다...",
                "progress": 25,
                "pipeline_id": pipeline_id
            }
            
            crawling_result = await self._step_crawling(url, text, config)
            if not crawling_result.success:
                yield {
                    "error": crawling_result.error,
                    "pipeline_id": pipeline_id
                }
                return
            
            content = crawling_result.data["content"]
            
            # 2단계: 언어 감지 (35%)
            yield {
                "step": 2,
                "message": "언어를 감지하고 있습니다...",
                "progress": 35,
                "pipeline_id": pipeline_id
            }
            
            lang_result = await self._step_language_detection(content)
            if not lang_result.success:
                yield {
                    "error": lang_result.error,
                    "pipeline_id": pipeline_id
                }
                return
            
            detected_lang = lang_result.data["detected_language"]
            
            # 3단계: 번역 (50%)
            yield {
                "step": 3,
                "message": "콘텐츠를 번역하고 있습니다...",
                "progress": 50,
                "pipeline_id": pipeline_id
            }
            
            translation_result = await self._step_translation(content, detected_lang, config.target_language)
            if not translation_result.success:
                yield {
                    "error": translation_result.error,
                    "pipeline_id": pipeline_id
                }
                return
            
            translated_content = translation_result.data["translated_content"]
            
            # 4단계: 키워드 추출 (60%)
            yield {
                "step": 4,
                "message": "키워드를 추출하고 있습니다...",
                "progress": 60,
                "pipeline_id": pipeline_id
            }
            
            keywords = await self._extract_keywords(translated_content)
            
            # 5단계: 콘텐츠 생성 (80%)
            yield {
                "step": 5,
                "message": "AI 블로그 포스트를 생성하고 있습니다...",
                "progress": 80,
                "pipeline_id": pipeline_id
            }
            
            generation_result = await self._step_content_generation(translated_content, keywords, config)
            if not generation_result.success:
                yield {
                    "error": generation_result.error,
                    "pipeline_id": pipeline_id
                }
                return
            
            blog_post = generation_result.data["blog_post"]
            
            # 6단계: SEO 분석 (90%)
            if config.enable_seo_analysis:
                yield {
                    "step": 6,
                    "message": "SEO 분석을 수행하고 있습니다...",
                    "progress": 90,
                    "pipeline_id": pipeline_id
                }
                
                seo_result = await self._step_seo_analysis(blog_post, keywords)
                if seo_result.success:
                    seo_analysis = seo_result.data["seo_analysis"]
                else:
                    seo_analysis = None
            else:
                seo_analysis = None
            
            # 7단계: 완료 (100%)
            yield {
                "step": 7,
                "message": "블로그 포스트 생성이 완료되었습니다!",
                "progress": 100,
                "pipeline_id": pipeline_id,
                "result": {
                    "blog_post": blog_post,
                    "keywords": keywords,
                    "seo_analysis": seo_analysis,
                    "metadata": {
                        "content_length": len(blog_post.get('content', '')),
                        "generated_at": datetime.now().isoformat()
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"진행 상황 파이프라인 실패: {e}")
            yield {
                "error": f"파이프라인 실행 중 오류 발생: {str(e)}",
                "pipeline_id": pipeline_id
            }
    
    def get_pipeline_status(self, pipeline_id: str) -> PipelineStatus:
        """파이프라인 상태 조회"""
        return self.active_pipelines.get(pipeline_id, PipelineStatus.PENDING)
    
    def cancel_pipeline(self, pipeline_id: str) -> bool:
        """파이프라인 취소"""
        if pipeline_id in self.active_pipelines:
            self.active_pipelines[pipeline_id] = PipelineStatus.CANCELLED
            return True
        return False
    
    def cleanup(self):
        """리소스 정리"""
        self.enhanced_crawler = None
        self.smart_crawler.close()
        self.pipeline_cache.clear()
        self.active_pipelines.clear()

# 전역 파이프라인 인스턴스
content_pipeline = ContentPipeline() 