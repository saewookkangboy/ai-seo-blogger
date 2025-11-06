"""
수평 확장 지원 서비스
로드 밸런싱, 스테이트리스 설계 지원
"""

import os
import socket
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.utils.logger import setup_logger
from app.config import settings

logger = setup_logger(__name__)


class HorizontalScalingSupport:
    """수평 확장 지원 클래스"""
    
    def __init__(self):
        self.instance_id = self._generate_instance_id()
        self.start_time = datetime.utcnow()
    
    def _generate_instance_id(self) -> str:
        """인스턴스 ID 생성"""
        hostname = socket.gethostname()
        pid = os.getpid()
        return f"{hostname}-{pid}"
    
    def get_instance_info(self) -> Dict[str, Any]:
        """인스턴스 정보 조회"""
        return {
            'instance_id': self.instance_id,
            'hostname': socket.gethostname(),
            'pid': os.getpid(),
            'start_time': self.start_time.isoformat(),
            'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds()
        }
    
    def check_stateless(self) -> Dict[str, Any]:
        """스테이트리스 설계 확인"""
        checks = {
            'stateless': True,
            'checks': {}
        }
        
        # 세션 저장 방식 확인
        session_storage = getattr(settings, 'session_storage', 'memory')
        if session_storage == 'memory':
            checks['checks']['session_storage'] = {
                'status': 'warning',
                'message': '메모리 세션 저장은 수평 확장에 적합하지 않습니다. Redis 세션 사용을 권장합니다.'
            }
            checks['stateless'] = False
        else:
            checks['checks']['session_storage'] = {
                'status': 'ok',
                'message': f'{session_storage} 세션 저장 사용'
            }
        
        # 캐시 저장 방식 확인
        cache_type = 'memory'
        try:
            from app.services.redis_cache import get_redis_cache
            redis_cache = get_redis_cache()
            stats = redis_cache.get_stats()
            if stats.get('type') == 'redis' and stats.get('connected'):
                cache_type = 'redis'
        except:
            pass
        
        if cache_type == 'memory':
            checks['checks']['cache_storage'] = {
                'status': 'warning',
                'message': '메모리 캐시는 수평 확장에 적합하지 않습니다. Redis 캐시 사용을 권장합니다.'
            }
        else:
            checks['checks']['cache_storage'] = {
                'status': 'ok',
                'message': f'{cache_type} 캐시 사용'
            }
        
        # 데이터베이스 연결 확인
        db_url = settings.database_url
        if db_url.startswith("sqlite"):
            checks['checks']['database'] = {
                'status': 'warning',
                'message': 'SQLite는 수평 확장에 적합하지 않습니다. PostgreSQL 사용을 권장합니다.'
            }
        else:
            checks['checks']['database'] = {
                'status': 'ok',
                'message': '공유 데이터베이스 사용'
            }
        
        return checks
    
    def get_load_balancer_config(self) -> Dict[str, Any]:
        """로드 밸런서 설정"""
        return {
            'health_check_path': '/health',
            'readiness_path': '/health/readiness',
            'liveness_path': '/health/liveness',
            'timeout': 30,
            'interval': 10,
            'healthy_threshold': 2,
            'unhealthy_threshold': 3,
            'recommendations': {
                'sticky_session': False,
                'session_affinity': False,
                'health_check_grace_period': 60,
                'deregistration_delay': 30
            }
        }
    
    def get_scaling_recommendations(self) -> Dict[str, Any]:
        """확장 권장사항"""
        recommendations = {
            'database': [],
            'cache': [],
            'session': [],
            'general': []
        }
        
        # 데이터베이스 권장사항
        if settings.database_url.startswith("sqlite"):
            recommendations['database'].append({
                'priority': 'high',
                'message': 'PostgreSQL로 마이그레이션하여 수평 확장 지원',
                'benefit': '여러 인스턴스에서 동일한 데이터베이스 공유 가능'
            })
        
        # 캐시 권장사항
        try:
            from app.services.redis_cache import get_redis_cache
            redis_cache = get_redis_cache()
            stats = redis_cache.get_stats()
            if stats.get('type') != 'redis' or not stats.get('connected'):
                recommendations['cache'].append({
                    'priority': 'high',
                    'message': 'Redis 캐시 사용으로 여러 인스턴스 간 캐시 공유',
                    'benefit': '캐시 히트율 향상 및 일관성 유지'
                })
        except:
            recommendations['cache'].append({
                'priority': 'high',
                'message': 'Redis 캐시 설정',
                'benefit': '분산 캐시 지원'
            })
        
        # 세션 권장사항
        session_storage = getattr(settings, 'session_storage', 'memory')
        if session_storage == 'memory':
            recommendations['session'].append({
                'priority': 'medium',
                'message': 'Redis 세션 저장소 사용',
                'benefit': '여러 인스턴스 간 세션 공유'
            })
        
        # 일반 권장사항
        recommendations['general'].append({
            'priority': 'medium',
            'message': '스테이트리스 설계 유지',
            'benefit': '인스턴스 간 상태 공유 불필요'
        })
        
        recommendations['general'].append({
            'priority': 'medium',
            'message': '헬스체크 엔드포인트 활용',
            'benefit': '로드 밸런서가 비정상 인스턴스 자동 제거'
        })
        
        return recommendations


# 전역 수평 확장 지원 인스턴스
horizontal_scaling = HorizontalScalingSupport()
