#!/usr/bin/env python3
"""
스마트 크롤러
사이트별 최적화된 크롤링 전략을 자동으로 선택하고 실행합니다.
"""

import time
import logging
import json
import os
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse
import hashlib
import threading
from dataclasses import dataclass
from enum import Enum

from .crawler import EnhancedCrawler
from .google_style_crawler import GoogleStyleCrawler
from .advanced_selenium_crawler import AdvancedSeleniumCrawler

logger = logging.getLogger(__name__)

class CrawlingStrategy(Enum):
    """크롤링 전략"""
    TRADITIONAL = "traditional"
    GOOGLE_STYLE = "google_style"
    SELENIUM = "selenium"
    ADVANCED_SELENIUM = "advanced_selenium"
    HYBRID = "hybrid"

@dataclass
class CrawlingResult:
    """크롤링 결과"""
    success: bool
    content: Optional[str]
    strategy: CrawlingStrategy
    response_time: float
    content_length: int
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SiteAnalyzer:
    """사이트 분석기"""
    
    def __init__(self):
        self.site_profiles = self._load_site_profiles()
        
    def _load_site_profiles(self) -> Dict[str, Dict[str, Any]]:
        """사이트 프로필 로드"""
        profiles = {
            "socialmediatoday.com": {
                "recommended_strategy": CrawlingStrategy.ADVANCED_SELENIUM,
                "fallback_strategies": [CrawlingStrategy.SELENIUM, CrawlingStrategy.GOOGLE_STYLE],
                "timeout": 25,
                "retry_count": 3,
                "requires_javascript": True,
                "dynamic_content": True,
                "anti_bot_protection": False
            },
            "facebook.com": {
                "recommended_strategy": CrawlingStrategy.ADVANCED_SELENIUM,
                "fallback_strategies": [CrawlingStrategy.SELENIUM],
                "timeout": 30,
                "retry_count": 2,
                "requires_javascript": True,
                "dynamic_content": True,
                "anti_bot_protection": True
            },
            "twitter.com": {
                "recommended_strategy": CrawlingStrategy.ADVANCED_SELENIUM,
                "fallback_strategies": [CrawlingStrategy.SELENIUM],
                "timeout": 25,
                "retry_count": 3,
                "requires_javascript": True,
                "dynamic_content": True,
                "anti_bot_protection": True
            },
            "linkedin.com": {
                "recommended_strategy": CrawlingStrategy.ADVANCED_SELENIUM,
                "fallback_strategies": [CrawlingStrategy.SELENIUM],
                "timeout": 20,
                "retry_count": 2,
                "requires_javascript": True,
                "dynamic_content": True,
                "anti_bot_protection": True
            },
            "youtube.com": {
                "recommended_strategy": CrawlingStrategy.ADVANCED_SELENIUM,
                "fallback_strategies": [CrawlingStrategy.SELENIUM, CrawlingStrategy.GOOGLE_STYLE],
                "timeout": 20,
                "retry_count": 2,
                "requires_javascript": True,
                "dynamic_content": True,
                "anti_bot_protection": False
            },
            "reddit.com": {
                "recommended_strategy": CrawlingStrategy.ADVANCED_SELENIUM,
                "fallback_strategies": [CrawlingStrategy.SELENIUM, CrawlingStrategy.GOOGLE_STYLE],
                "timeout": 25,
                "retry_count": 3,
                "requires_javascript": True,
                "dynamic_content": True,
                "anti_bot_protection": False
            },
            "medium.com": {
                "recommended_strategy": CrawlingStrategy.ADVANCED_SELENIUM,
                "fallback_strategies": [CrawlingStrategy.SELENIUM, CrawlingStrategy.GOOGLE_STYLE],
                "timeout": 20,
                "retry_count": 2,
                "requires_javascript": True,
                "dynamic_content": False,
                "anti_bot_protection": False
            },
            "quora.com": {
                "recommended_strategy": CrawlingStrategy.ADVANCED_SELENIUM,
                "fallback_strategies": [CrawlingStrategy.SELENIUM],
                "timeout": 25,
                "retry_count": 2,
                "requires_javascript": True,
                "dynamic_content": True,
                "anti_bot_protection": True
            },
            "tumblr.com": {
                "recommended_strategy": CrawlingStrategy.ADVANCED_SELENIUM,
                "fallback_strategies": [CrawlingStrategy.SELENIUM, CrawlingStrategy.GOOGLE_STYLE],
                "timeout": 20,
                "retry_count": 2,
                "requires_javascript": True,
                "dynamic_content": True,
                "anti_bot_protection": False
            },
            "pinterest.com": {
                "recommended_strategy": CrawlingStrategy.ADVANCED_SELENIUM,
                "fallback_strategies": [CrawlingStrategy.SELENIUM],
                "timeout": 25,
                "retry_count": 2,
                "requires_javascript": True,
                "dynamic_content": True,
                "anti_bot_protection": True
            }
        }
        return profiles
    
    def analyze_site(self, url: str) -> Dict[str, Any]:
        """사이트 분석"""
        domain = urlparse(url).netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # 기본 프로필
        default_profile = {
            "recommended_strategy": CrawlingStrategy.TRADITIONAL,
            "fallback_strategies": [CrawlingStrategy.GOOGLE_STYLE, CrawlingStrategy.SELENIUM],
            "timeout": 15,
            "retry_count": 2,
            "requires_javascript": False,
            "dynamic_content": False,
            "anti_bot_protection": False
        }
        
        return self.site_profiles.get(domain, default_profile)

class PerformanceMonitor:
    """성능 모니터"""
    
    def __init__(self):
        self.performance_data = {}
        self.lock = threading.Lock()
        
    def record_performance(self, url: str, strategy: CrawlingStrategy, 
                          success: bool, response_time: float, content_length: int):
        """성능 데이터 기록"""
        domain = urlparse(url).netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        
        with self.lock:
            if domain not in self.performance_data:
                self.performance_data[domain] = {}
            
            if strategy.value not in self.performance_data[domain]:
                self.performance_data[domain][strategy.value] = {
                    "total_attempts": 0,
                    "successful_attempts": 0,
                    "total_response_time": 0,
                    "total_content_length": 0,
                    "avg_response_time": 0,
                    "avg_content_length": 0,
                    "success_rate": 0
                }
            
            data = self.performance_data[domain][strategy.value]
            data["total_attempts"] += 1
            data["total_response_time"] += response_time
            data["total_content_length"] += content_length
            
            if success:
                data["successful_attempts"] += 1
            
            # 평균 계산
            data["avg_response_time"] = data["total_response_time"] / data["total_attempts"]
            data["avg_content_length"] = data["total_content_length"] / data["total_attempts"]
            data["success_rate"] = data["successful_attempts"] / data["total_attempts"]
    
    def get_best_strategy(self, domain: str) -> Optional[CrawlingStrategy]:
        """도메인별 최적 전략 반환"""
        if domain.startswith('www.'):
            domain = domain[4:]
        
        with self.lock:
            if domain not in self.performance_data:
                return None
            
            best_strategy = None
            best_score = 0
            
            for strategy_name, data in self.performance_data[domain].items():
                if data["total_attempts"] < 3:  # 최소 시도 횟수
                    continue
                
                # 성공률과 응답시간을 고려한 점수 계산
                score = (data["success_rate"] * 0.7) + (1 / (1 + data["avg_response_time"] / 10) * 0.3)
                
                if score > best_score:
                    best_score = score
                    best_strategy = CrawlingStrategy(strategy_name)
            
            return best_strategy
    
    def save_performance_data(self, filename: str = "crawler_performance.json"):
        """성능 데이터 저장"""
        with self.lock:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.performance_data, f, indent=2, ensure_ascii=False)

class SmartCrawler:
    """스마트 크롤러"""
    
    def __init__(self):
        self.site_analyzer = SiteAnalyzer()
        self.performance_monitor = PerformanceMonitor()
        self.enhanced_crawler = EnhancedCrawler()
        self.google_style_crawler = GoogleStyleCrawler()
        self.advanced_selenium_crawler = AdvancedSeleniumCrawler()
        self.session_cache = {}
        self.cache_lock = threading.Lock()
        
    def _get_cached_result(self, url: str) -> Optional[CrawlingResult]:
        """캐시된 결과 가져오기"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        with self.cache_lock:
            if cache_key in self.session_cache:
                cached_data, timestamp = self.session_cache[cache_key]
                if time.time() - timestamp < 3600:  # 1시간 캐시
                    logger.info(f"캐시된 결과 사용: {url}")
                    return cached_data
                else:
                    del self.session_cache[cache_key]
        return None
    
    def _cache_result(self, url: str, result: CrawlingResult):
        """결과 캐시"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        with self.cache_lock:
            self.session_cache[cache_key] = (result, time.time())
            
            # 캐시 크기 제한
            if len(self.session_cache) > 100:
                oldest_key = min(self.session_cache.keys(), 
                               key=lambda k: self.session_cache[k][1])
                del self.session_cache[oldest_key]
    
    def _execute_strategy(self, url: str, strategy: CrawlingStrategy, 
                         timeout: int = 20) -> CrawlingResult:
        """전략 실행"""
        start_time = time.time()
        
        try:
            if strategy == CrawlingStrategy.TRADITIONAL:
                content = self.enhanced_crawler.crawl_url(url, max_retries=2, use_google_style=False)
                
            elif strategy == CrawlingStrategy.GOOGLE_STYLE:
                content = self.google_style_crawler.crawl_url(url)
                
            elif strategy == CrawlingStrategy.SELENIUM:
                html = self.advanced_selenium_crawler.get_rendered_html(url, timeout)
                content = self.advanced_selenium_crawler.extract_main_content(html, url) if html else None
                
            elif strategy == CrawlingStrategy.ADVANCED_SELENIUM:
                html = self.advanced_selenium_crawler.get_rendered_html(url, timeout)
                content = self.advanced_selenium_crawler.extract_main_content(html, url) if html else None
                
            else:  # HYBRID
                content = self._execute_hybrid_strategy(url, timeout)
            
            response_time = time.time() - start_time
            success = content is not None and len(content) > 100
            content_length = len(content) if content else 0
            
            result = CrawlingResult(
                success=success,
                content=content,
                strategy=strategy,
                response_time=response_time,
                content_length=content_length
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            result = CrawlingResult(
                success=False,
                content=None,
                strategy=strategy,
                response_time=response_time,
                content_length=0,
                error=str(e)
            )
        
        # 성능 데이터 기록
        self.performance_monitor.record_performance(
            url, strategy, result.success, result.response_time, result.content_length
        )
        
        return result
    
    def _execute_hybrid_strategy(self, url: str, timeout: int = 20) -> Optional[str]:
        """하이브리드 전략 실행"""
        # 먼저 빠른 전략 시도
        try:
            content = self.enhanced_crawler.crawl_url(url, max_retries=1, use_google_style=False)
            if content and len(content) > 500:
                return content
        except:
            pass
        
        # 실패하면 Selenium 사용
        try:
            html = self.advanced_selenium_crawler.get_rendered_html(url, timeout)
            if html:
                return self.advanced_selenium_crawler.extract_main_content(html, url)
        except:
            pass
        
        return None
    
    def _select_optimal_strategy(self, url: str) -> List[CrawlingStrategy]:
        """최적 전략 선택"""
        domain = urlparse(url).netloc.lower()
        site_profile = self.site_analyzer.analyze_site(url)
        
        # 성능 데이터 기반 최적 전략 확인
        best_strategy = self.performance_monitor.get_best_strategy(domain)
        
        strategies = []
        
        # 1순위: 성능 데이터 기반 최적 전략
        if best_strategy:
            strategies.append(best_strategy)
        
        # 2순위: 사이트 프로필 기반 권장 전략
        recommended = site_profile["recommended_strategy"]
        if recommended not in strategies:
            strategies.append(recommended)
        
        # 3순위: 폴백 전략들
        fallbacks = site_profile["fallback_strategies"]
        for fallback in fallbacks:
            if fallback not in strategies:
                strategies.append(fallback)
        
        # 4순위: 기본 전략
        if CrawlingStrategy.TRADITIONAL not in strategies:
            strategies.append(CrawlingStrategy.TRADITIONAL)
        
        return strategies
    
    def crawl_url(self, url: str, force_strategy: Optional[CrawlingStrategy] = None) -> Optional[str]:
        """URL 크롤링"""
        logger.info(f"스마트 크롤링 시작: {url}")
        
        # 캐시 확인
        cached_result = self._get_cached_result(url)
        if cached_result and cached_result.success:
            return cached_result.content
        
        # 전략 선택
        if force_strategy:
            strategies = [force_strategy]
        else:
            strategies = self._select_optimal_strategy(url)
        
        site_profile = self.site_analyzer.analyze_site(url)
        max_retries = site_profile["retry_count"]
        
        # 전략별 시도
        for attempt in range(max_retries):
            for strategy in strategies:
                logger.info(f"전략 시도 {attempt + 1}/{max_retries}: {strategy.value}")
                
                result = self._execute_strategy(url, strategy, site_profile["timeout"])
                
                if result.success:
                    logger.info(f"크롤링 성공: {strategy.value} ({result.response_time:.2f}초)")
                    self._cache_result(url, result)
                    return result.content
                else:
                    logger.warning(f"전략 실패: {strategy.value} - {result.error}")
                
                # 전략 간 간격
                time.sleep(1)
        
        logger.error(f"모든 전략 실패: {url}")
        return None
    
    def get_crawling_stats(self) -> Dict[str, Any]:
        """크롤링 통계 반환"""
        with self.performance_monitor.lock:
            stats = {
                "total_domains": len(self.performance_monitor.performance_data),
                "performance_by_domain": {},
                "overall_stats": {
                    "total_attempts": 0,
                    "total_success": 0,
                    "avg_response_time": 0,
                    "avg_content_length": 0
                }
            }
            
            total_attempts = 0
            total_success = 0
            total_response_time = 0
            total_content_length = 0
            
            for domain, strategies in self.performance_monitor.performance_data.items():
                domain_stats = {
                    "strategies": {},
                    "best_strategy": None,
                    "total_attempts": 0,
                    "success_rate": 0
                }
                
                domain_attempts = 0
                domain_success = 0
                best_strategy = None
                best_score = 0
                
                for strategy_name, data in strategies.items():
                    domain_stats["strategies"][strategy_name] = data
                    domain_attempts += data["total_attempts"]
                    domain_success += data["successful_attempts"]
                    
                    if data["total_attempts"] >= 3:
                        score = data["success_rate"]
                        if score > best_score:
                            best_score = score
                            best_strategy = strategy_name
                
                domain_stats["best_strategy"] = best_strategy
                domain_stats["total_attempts"] = domain_attempts
                domain_stats["success_rate"] = domain_success / domain_attempts if domain_attempts > 0 else 0
                
                stats["performance_by_domain"][domain] = domain_stats
                
                total_attempts += domain_attempts
                total_success += domain_success
            
            if total_attempts > 0:
                stats["overall_stats"]["total_attempts"] = total_attempts
                stats["overall_stats"]["total_success"] = total_success
                stats["overall_stats"]["success_rate"] = total_success / total_attempts
            
            return stats
    
    def save_performance_data(self):
        """성능 데이터 저장"""
        self.performance_monitor.save_performance_data()
    
    def close(self):
        """크롤러 정리"""
        self.advanced_selenium_crawler.close()
        self.save_performance_data() 