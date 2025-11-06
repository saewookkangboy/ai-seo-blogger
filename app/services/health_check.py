"""
헬스체크 서비스
로드 밸런서 및 모니터링을 위한 헬스체크 엔드포인트
"""

import time
import psutil
import os
from typing import Dict, Any
from datetime import datetime
from sqlalchemy import text

from app.utils.logger import setup_logger
from app.database import engine, get_db_pool_status
from app.services.memory_manager import memory_manager
from app.services.redis_cache import get_redis_cache
from app.services.background_queue import background_queue
from app.config import settings

logger = setup_logger(__name__)


class HealthCheck:
    """헬스체크 클래스"""
    
    def __init__(self):
        self.start_time = time.time()
        self.process = psutil.Process(os.getpid())
    
    def check_health(self) -> Dict[str, Any]:
        """전체 헬스체크"""
        health = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': time.time() - self.start_time,
            'checks': {}
        }
        
        # 데이터베이스 체크
        db_health = self.check_database()
        health['checks']['database'] = db_health
        if db_health['status'] != 'healthy':
            health['status'] = 'unhealthy'
        
        # 메모리 체크
        memory_health = self.check_memory()
        health['checks']['memory'] = memory_health
        if memory_health['status'] != 'healthy':
            health['status'] = 'unhealthy'
        
        # Redis 체크 (선택적)
        try:
            redis_health = self.check_redis()
            health['checks']['redis'] = redis_health
        except Exception as e:
            health['checks']['redis'] = {
                'status': 'unknown',
                'error': str(e)
            }
        
        # 백그라운드 작업 큐 체크
        queue_health = self.check_background_queue()
        health['checks']['background_queue'] = queue_health
        
        # 시스템 리소스 체크
        system_health = self.check_system_resources()
        health['checks']['system'] = system_health
        
        return health
    
    def check_database(self) -> Dict[str, Any]:
        """데이터베이스 헬스체크"""
        try:
            start_time = time.time()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            response_time = (time.time() - start_time) * 1000
            
            pool_status = get_db_pool_status()
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'pool_status': pool_status
            }
        except Exception as e:
            logger.error(f"데이터베이스 헬스체크 실패: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_memory(self) -> Dict[str, Any]:
        """메모리 헬스체크"""
        try:
            memory_stats = memory_manager.get_memory_stats()
            usage = memory_stats['current']
            
            # 메모리 사용률 체크
            if usage['percent'] > 90:
                status = 'unhealthy'
            elif usage['percent'] > 80:
                status = 'degraded'
            else:
                status = 'healthy'
            
            return {
                'status': status,
                'usage_mb': round(usage['rss_mb'], 2),
                'usage_percent': round(usage['percent'], 2),
                'available_mb': round(usage['available_mb'], 2)
            }
        except Exception as e:
            logger.error(f"메모리 헬스체크 실패: {e}")
            return {
                'status': 'unknown',
                'error': str(e)
            }
    
    def check_redis(self) -> Dict[str, Any]:
        """Redis 헬스체크"""
        try:
            redis_cache = get_redis_cache()
            stats = redis_cache.get_stats()
            
            if stats.get('connected', False):
                return {
                    'status': 'healthy',
                    'type': stats.get('type', 'unknown'),
                    'hit_rate': round(stats.get('hit_rate', 0) * 100, 2)
                }
            else:
                return {
                    'status': 'degraded',
                    'type': stats.get('type', 'unknown'),
                    'message': 'Redis 연결 실패, 메모리 캐시 사용 중'
                }
        except Exception as e:
            logger.warning(f"Redis 헬스체크 실패: {e}")
            return {
                'status': 'degraded',
                'error': str(e),
                'message': 'Redis 연결 실패, 메모리 캐시 사용 중'
            }
    
    def check_background_queue(self) -> Dict[str, Any]:
        """백그라운드 작업 큐 헬스체크"""
        try:
            stats = background_queue.get_queue_stats()
            
            queue_full = stats['queue_size'] >= stats['max_queue_size']
            
            return {
                'status': 'healthy' if not queue_full else 'degraded',
                'queue_size': stats['queue_size'],
                'max_queue_size': stats['max_queue_size'],
                'active_workers': stats['active_workers'],
                'max_workers': stats['max_workers']
            }
        except Exception as e:
            logger.error(f"백그라운드 작업 큐 헬스체크 실패: {e}")
            return {
                'status': 'unknown',
                'error': str(e)
            }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """시스템 리소스 체크"""
        try:
            cpu_percent = self.process.cpu_percent(interval=0.1)
            memory_info = self.process.memory_info()
            
            # 시스템 전체 리소스
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent(interval=0.1)
            
            return {
                'status': 'healthy',
                'cpu_percent': round(cpu_percent, 2),
                'memory_mb': round(memory_info.rss / 1024 / 1024, 2),
                'system_cpu_percent': round(system_cpu, 2),
                'system_memory_percent': round(system_memory.percent, 2),
                'system_memory_available_mb': round(system_memory.available / 1024 / 1024, 2)
            }
        except Exception as e:
            logger.error(f"시스템 리소스 체크 실패: {e}")
            return {
                'status': 'unknown',
                'error': str(e)
            }
    
    def check_readiness(self) -> Dict[str, Any]:
        """Readiness 체크 (서비스 준비 상태)"""
        readiness = {
            'ready': True,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        # 데이터베이스 준비 상태
        db_ready = self.check_database()
        readiness['checks']['database'] = db_ready
        if db_ready['status'] != 'healthy':
            readiness['ready'] = False
        
        # 메모리 준비 상태
        memory_ready = self.check_memory()
        readiness['checks']['memory'] = memory_ready
        if memory_ready['status'] == 'unhealthy':
            readiness['ready'] = False
        
        return readiness
    
    def check_liveness(self) -> Dict[str, Any]:
        """Liveness 체크 (서비스 생존 상태)"""
        return {
            'alive': True,
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': time.time() - self.start_time
        }


# 전역 헬스체크 인스턴스
health_check = HealthCheck()
