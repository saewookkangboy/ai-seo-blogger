"""
LRU (Least Recently Used) 캐시 구현
메모리 효율적인 캐시 전략 제공
"""

import time
import threading
from typing import Any, Optional, Dict, Tuple
from collections import OrderedDict
import hashlib
import json
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class LRUCache:
    """LRU 캐시 구현 클래스"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Args:
            max_size: 최대 캐시 항목 수
            default_ttl: 기본 TTL (초)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, Tuple[Any, float, float]] = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
    
    def _is_expired(self, timestamp: float, ttl: float) -> bool:
        """캐시 항목이 만료되었는지 확인"""
        return time.time() - timestamp > ttl
    
    def _cleanup_expired(self):
        """만료된 항목 제거"""
        current_time = time.time()
        expired_keys = []
        
        for key, (value, timestamp, ttl) in list(self.cache.items()):
            if current_time - timestamp > ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
    
    def _evict_lru(self):
        """LRU 항목 제거"""
        if len(self.cache) >= self.max_size:
            # 가장 오래된 항목 제거 (FIFO)
            self.cache.popitem(last=False)
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            value, timestamp, ttl = self.cache[key]
            
            # 만료 확인
            if self._is_expired(timestamp, ttl):
                del self.cache[key]
                self.misses += 1
                return None
            
            # 최근 사용된 항목으로 이동 (LRU)
            self.cache.move_to_end(key)
            self.hits += 1
            
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """캐시에 값 저장"""
        with self.lock:
            ttl = ttl or self.default_ttl
            timestamp = time.time()
            
            # 만료된 항목 정리
            if len(self.cache) >= self.max_size * 0.9:
                self._cleanup_expired()
            
            # 공간이 부족하면 LRU 항목 제거
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # 캐시에 저장
            self.cache[key] = (value, timestamp, ttl)
            self.cache.move_to_end(key)  # 최근 사용으로 표시
    
    def delete(self, key: str) -> bool:
        """캐시에서 항목 삭제"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self):
        """캐시 전체 삭제"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': round(hit_rate, 2),
                'total_requests': total
            }
    
    def _generate_cache_key(self, *args, **kwargs) -> str:
        """캐시 키 생성"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get_or_set(self, key: str, func, ttl: Optional[int] = None, *args, **kwargs) -> Any:
        """캐시에서 가져오거나 함수 실행 후 저장"""
        value = self.get(key)
        if value is not None:
            return value
        
        value = func(*args, **kwargs)
        self.set(key, value, ttl)
        return value


class CacheManager:
    """캐시 관리자 - 여러 캐시 인스턴스 관리"""
    
    def __init__(self):
        self.caches: Dict[str, LRUCache] = {}
        self.lock = threading.RLock()
    
    def get_cache(self, name: str, max_size: int = 1000, ttl: int = 3600) -> LRUCache:
        """캐시 인스턴스 가져오기 또는 생성"""
        with self.lock:
            if name not in self.caches:
                self.caches[name] = LRUCache(max_size=max_size, default_ttl=ttl)
            return self.caches[name]
    
    def clear_cache(self, name: Optional[str] = None):
        """캐시 삭제"""
        with self.lock:
            if name:
                if name in self.caches:
                    self.caches[name].clear()
            else:
                for cache in self.caches.values():
                    cache.clear()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """모든 캐시 통계 조회"""
        with self.lock:
            return {
                name: cache.get_stats() 
                for name, cache in self.caches.items()
            }


# 전역 캐시 관리자 인스턴스
cache_manager = CacheManager()

# 기본 캐시 인스턴스들
content_cache = cache_manager.get_cache('content', max_size=500, ttl=1800)  # 30분
translation_cache = cache_manager.get_cache('translation', max_size=1000, ttl=1800)  # 30분
crawling_cache = cache_manager.get_cache('crawling', max_size=200, ttl=3600)  # 1시간
api_cache = cache_manager.get_cache('api', max_size=200, ttl=300)  # 5분
