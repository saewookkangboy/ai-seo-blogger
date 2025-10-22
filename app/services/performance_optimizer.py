#!/usr/bin/env python3
"""
성능 최적화 서비스
캐싱, 연결 풀링, 비동기 처리 등을 통해 성능을 최적화합니다.
"""

import asyncio
import time
import json
import hashlib
from typing import Dict, Any, Optional, List
from functools import wraps
import httpx
from app.utils.logger import setup_logger
from app.config import settings

logger = setup_logger(__name__)

class PerformanceOptimizer:
    """성능 최적화 클래스"""
    
    def __init__(self):
        self.cache = {}
        self.request_times = {}
        self.error_counts = {}
        self.connection_pool = None
        self.max_cache_size = 1000
        self.cache_ttl = 3600  # 1시간
        
    async def initialize(self):
        """초기화"""
        # HTTP 클라이언트 연결 풀 설정
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0
        )
        
        self.connection_pool = httpx.AsyncClient(
            limits=limits,
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True
        )
        
        logger.info("성능 최적화 서비스가 초기화되었습니다.")
    
    def cache_key(self, *args, **kwargs) -> str:
        """캐시 키 생성"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get_cache(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 가져오기"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return data
            else:
                del self.cache[key]
        return None
    
    def set_cache(self, key: str, data: Any):
        """캐시에 데이터 저장"""
        # 캐시 크기 제한
        if len(self.cache) >= self.max_cache_size:
            # 가장 오래된 항목 제거
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[key] = (data, time.time())
    
    def clear_cache(self):
        """캐시 정리"""
        self.cache.clear()
        logger.info("캐시가 정리되었습니다.")
    
    def cache_decorator(self, ttl: int = None):
        """캐싱 데코레이터"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = self.cache_key(func.__name__, *args, **kwargs)
                cached_result = self.get_cache(cache_key)
                
                if cached_result is not None:
                    logger.debug(f"캐시 히트: {func.__name__}")
                    return cached_result
                
                result = await func(*args, **kwargs)
                self.set_cache(cache_key, result)
                return result
            return wrapper
        return decorator
    
    async def batch_process(self, items: List[Any], processor_func, batch_size: int = 10):
        """배치 처리"""
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[processor_func(item) for item in batch],
                return_exceptions=True
            )
            results.extend(batch_results)
        return results
    
    def track_performance(self, operation: str):
        """성능 추적 데코레이터"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    if operation not in self.request_times:
                        self.request_times[operation] = []
                    self.request_times[operation].append(duration)
                    
                    # 최근 100개만 유지
                    if len(self.request_times[operation]) > 100:
                        self.request_times[operation] = self.request_times[operation][-100:]
                    
                    logger.debug(f"{operation} 완료: {duration:.2f}초")
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    if operation not in self.error_counts:
                        self.error_counts[operation] = 0
                    self.error_counts[operation] += 1
                    
                    logger.error(f"{operation} 실패 ({duration:.2f}초): {e}")
                    raise
            return wrapper
        return decorator
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        stats = {}
        
        for operation, times in self.request_times.items():
            if times:
                stats[operation] = {
                    'count': len(times),
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'error_count': self.error_counts.get(operation, 0)
                }
        
        return stats
    
    async def optimize_request(self, url: str, method: str = "GET", **kwargs) -> httpx.Response:
        """최적화된 HTTP 요청"""
        if not self.connection_pool:
            await self.initialize()
        
        try:
            response = await self.connection_pool.request(method, url, **kwargs)
            return response
        except Exception as e:
            logger.error(f"HTTP 요청 실패: {url} - {e}")
            raise
    
    async def cleanup(self):
        """정리"""
        if self.connection_pool:
            await self.connection_pool.aclose()
        self.clear_cache()

# 전역 인스턴스
performance_optimizer = PerformanceOptimizer()

# 유틸리티 함수들
async def get_optimized_client() -> httpx.AsyncClient:
    """최적화된 HTTP 클라이언트 반환"""
    if not performance_optimizer.connection_pool:
        await performance_optimizer.initialize()
    return performance_optimizer.connection_pool

def cache_result(ttl: int = 3600):
    """결과 캐싱 데코레이터"""
    return performance_optimizer.cache_decorator(ttl)

def track_performance(operation: str):
    """성능 추적 데코레이터"""
    return performance_optimizer.track_performance(operation) 