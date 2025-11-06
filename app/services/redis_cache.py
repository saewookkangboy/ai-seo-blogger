"""
Redis 분산 캐시 구현
Redis가 없는 경우 메모리 캐시로 fallback
"""

import json
import hashlib
import time
from typing import Any, Optional, Dict
from app.utils.logger import setup_logger
from app.config import settings

logger = setup_logger(__name__)

# Redis 클라이언트 (선택적)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis가 설치되지 않았습니다. 메모리 캐시로 대체됩니다.")

# 메모리 캐시 fallback
from collections import OrderedDict
from threading import RLock

class MemoryCacheFallback:
    """Redis가 없을 때 사용할 메모리 캐시"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.cache: OrderedDict[str, tuple] = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.lock = RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        with self.lock:
            if key not in self.cache:
                return None
            
            value, timestamp, ttl = self.cache[key]
            
            if time.time() - timestamp > ttl:
                del self.cache[key]
                return None
            
            # LRU: 최근 사용된 항목으로 이동
            self.cache.move_to_end(key)
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """캐시에 값 저장"""
        with self.lock:
            ttl = ttl or self.default_ttl
            timestamp = time.time()
            
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
            
            self.cache[key] = (value, timestamp, ttl)
            self.cache.move_to_end(key)
    
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
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'type': 'memory'
            }


class RedisCache:
    """Redis 캐시 클래스"""
    
    def __init__(self, redis_url: Optional[str] = None, 
                 default_ttl: int = 3600,
                 fallback_to_memory: bool = True):
        """
        Args:
            redis_url: Redis URL (예: redis://localhost:6379/0)
            default_ttl: 기본 TTL (초)
            fallback_to_memory: Redis 실패 시 메모리 캐시로 대체
        """
        self.default_ttl = default_ttl
        self.fallback_to_memory = fallback_to_memory
        self.redis_client = None
        self.memory_cache = None
        self.use_memory = False
        
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.Redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # 연결 테스트
                self.redis_client.ping()
                logger.info("✅ Redis 연결 성공")
            except Exception as e:
                logger.warning(f"Redis 연결 실패: {e}")
                if fallback_to_memory:
                    logger.info("메모리 캐시로 대체합니다.")
                    self.use_memory = True
                    self.memory_cache = MemoryCacheFallback(default_ttl=default_ttl)
                else:
                    raise
        else:
            if fallback_to_memory:
                logger.info("Redis가 없어 메모리 캐시를 사용합니다.")
                self.use_memory = True
                self.memory_cache = MemoryCacheFallback(default_ttl=default_ttl)
            else:
                raise ValueError("Redis가 설정되지 않았습니다.")
    
    def _serialize(self, value: Any) -> str:
        """값을 JSON 문자열로 직렬화"""
        return json.dumps(value, ensure_ascii=False, default=str)
    
    def _deserialize(self, value: str) -> Any:
        """JSON 문자열을 값으로 역직렬화"""
        return json.loads(value)
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        if self.use_memory and self.memory_cache:
            return self.memory_cache.get(key)
        
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            return self._deserialize(value)
        except Exception as e:
            logger.warning(f"Redis get 오류: {e}")
            if self.fallback_to_memory:
                if not self.memory_cache:
                    self.memory_cache = MemoryCacheFallback(default_ttl=self.default_ttl)
                self.use_memory = True
                return self.memory_cache.get(key)
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """캐시에 값 저장"""
        ttl = ttl or self.default_ttl
        
        if self.use_memory and self.memory_cache:
            self.memory_cache.set(key, value, ttl)
            return
        
        if not self.redis_client:
            return
        
        try:
            serialized = self._serialize(value)
            self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.warning(f"Redis set 오류: {e}")
            if self.fallback_to_memory:
                if not self.memory_cache:
                    self.memory_cache = MemoryCacheFallback(default_ttl=self.default_ttl)
                self.use_memory = True
                self.memory_cache.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """캐시에서 항목 삭제"""
        if self.use_memory and self.memory_cache:
            return self.memory_cache.delete(key)
        
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.warning(f"Redis delete 오류: {e}")
            if self.fallback_to_memory and self.memory_cache:
                return self.memory_cache.delete(key)
            return False
    
    def clear(self):
        """캐시 전체 삭제"""
        if self.use_memory and self.memory_cache:
            self.memory_cache.clear()
            return
        
        if not self.redis_client:
            return
        
        try:
            self.redis_client.flushdb()
        except Exception as e:
            logger.warning(f"Redis clear 오류: {e}")
            if self.fallback_to_memory and self.memory_cache:
                self.memory_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        if self.use_memory and self.memory_cache:
            return self.memory_cache.get_stats()
        
        if not self.redis_client:
            return {'type': 'none', 'connected': False}
        
        try:
            info = self.redis_client.info('stats')
            return {
                'type': 'redis',
                'connected': True,
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': info.get('keyspace_hits', 0) / 
                           (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0) + 1)
            }
        except Exception as e:
            logger.warning(f"Redis stats 오류: {e}")
            return {'type': 'redis', 'connected': False, 'error': str(e)}


# 전역 Redis 캐시 인스턴스 (설정에서 가져오기)
redis_cache = None

def get_redis_cache() -> RedisCache:
    """Redis 캐시 인스턴스 가져오기"""
    global redis_cache
    
    if redis_cache is None:
        redis_url = getattr(settings, 'redis_url', None)
        default_ttl = getattr(settings, 'cache_default_ttl', 3600)
        redis_cache = RedisCache(
            redis_url=redis_url,
            default_ttl=default_ttl,
            fallback_to_memory=True
        )
    
    return redis_cache
