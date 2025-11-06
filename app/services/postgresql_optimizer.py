"""
PostgreSQL 최적화 서비스
PostgreSQL 전용 최적화 설정 및 기능
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.utils.logger import setup_logger
from app.config import settings

logger = setup_logger(__name__)


class PostgreSQLOptimizer:
    """PostgreSQL 최적화 클래스"""
    
    def __init__(self, database_url: str):
        """
        Args:
            database_url: PostgreSQL 데이터베이스 URL
        """
        self.database_url = database_url
        self.engine = None
    
    def initialize(self):
        """초기화"""
        if not self.database_url.startswith("postgresql"):
            raise ValueError("PostgreSQL URL이 아닙니다.")
        
        # PostgreSQL 최적화 설정
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=20,  # 연결 풀 크기
            max_overflow=30,  # 최대 오버플로우 연결 수
            pool_pre_ping=True,  # 연결 상태 확인
            pool_recycle=3600,  # 연결 재사용 시간 (1시간)
            pool_timeout=30,  # 연결 타임아웃
            echo=settings.debug
        )
        
        logger.info("PostgreSQL 최적화 엔진 초기화 완료")
    
    def optimize_connection_pool(self, pool_size: int = 20, max_overflow: int = 30):
        """연결 풀 최적화"""
        if not self.engine:
            self.initialize()
        
        # 연결 풀 크기 조정
        self.engine.pool.size = pool_size
        self.engine.pool._max_overflow = max_overflow
        
        logger.info(f"연결 풀 최적화: pool_size={pool_size}, max_overflow={max_overflow}")
    
    def create_read_replica_config(self, replica_url: str) -> Dict[str, Any]:
        """읽기 전용 복제본 설정"""
        return {
            'primary': self.database_url,
            'replica': replica_url,
            'read_preference': 'replica',
            'write_preference': 'primary'
        }
    
    def optimize_query_performance(self):
        """쿼리 성능 최적화"""
        if not self.engine:
            self.initialize()
        
        optimizations = []
        
        with self.engine.connect() as conn:
            # PostgreSQL 설정 최적화
            try:
                # 통계 수집 활성화
                conn.execute(text("ALTER SYSTEM SET track_activity_query_size = 2048"))
                conn.execute(text("ALTER SYSTEM SET shared_buffers = '256MB'"))
                conn.execute(text("ALTER SYSTEM SET effective_cache_size = '1GB'"))
                conn.execute(text("ALTER SYSTEM SET maintenance_work_mem = '64MB'"))
                conn.execute(text("ALTER SYSTEM SET checkpoint_completion_target = 0.9"))
                conn.execute(text("ALTER SYSTEM SET wal_buffers = '16MB'"))
                conn.execute(text("ALTER SYSTEM SET default_statistics_target = 100"))
                conn.execute(text("ALTER SYSTEM SET random_page_cost = 1.1"))
                conn.execute(text("ALTER SYSTEM SET effective_io_concurrency = 200"))
                conn.execute(text("ALTER SYSTEM SET work_mem = '4MB'"))
                conn.execute(text("ALTER SYSTEM SET min_wal_size = '1GB'"))
                conn.execute(text("ALTER SYSTEM SET max_wal_size = '4GB'"))
                
                conn.commit()
                optimizations.append("PostgreSQL 설정 최적화 완료")
                logger.info("PostgreSQL 쿼리 성능 최적화 완료")
            
            except Exception as e:
                logger.warning(f"PostgreSQL 최적화 중 오류: {e}")
                optimizations.append(f"최적화 실패: {e}")
        
        return optimizations
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 조회"""
        if not self.engine:
            self.initialize()
        
        stats = {}
        
        with self.engine.connect() as conn:
            try:
                # 연결 통계
                result = conn.execute(text("""
                    SELECT count(*) as connections,
                           count(*) FILTER (WHERE state = 'active') as active,
                           count(*) FILTER (WHERE state = 'idle') as idle
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """))
                row = result.fetchone()
                stats['connections'] = {
                    'total': row[0],
                    'active': row[1],
                    'idle': row[2]
                }
                
                # 데이터베이스 크기
                result = conn.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size
                """))
                row = result.fetchone()
                stats['database_size'] = row[0]
                
                # 캐시 히트율
                result = conn.execute(text("""
                    SELECT 
                        sum(heap_blks_read) as heap_read,
                        sum(heap_blks_hit) as heap_hit,
                        sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0) as hit_ratio
                    FROM pg_statio_user_tables
                """))
                row = result.fetchone()
                stats['cache_hit_ratio'] = row[2] if row[2] else 0
                
                # 인덱스 사용 통계
                result = conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan as index_scans,
                        idx_tup_read as tuples_read,
                        idx_tup_fetch as tuples_fetched
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan DESC
                    LIMIT 10
                """))
                stats['top_indexes'] = [
                    {
                        'schema': row[0],
                        'table': row[1],
                        'index': row[2],
                        'scans': row[3],
                        'tuples_read': row[4],
                        'tuples_fetched': row[5]
                    }
                    for row in result
                ]
                
            except Exception as e:
                logger.error(f"성능 통계 조회 오류: {e}")
                stats['error'] = str(e)
        
        return stats


def get_postgresql_optimizer(database_url: Optional[str] = None) -> PostgreSQLOptimizer:
    """PostgreSQL 최적화 인스턴스 가져오기"""
    if database_url is None:
        database_url = settings.database_url
    
    if not database_url.startswith("postgresql"):
        raise ValueError("PostgreSQL URL이 아닙니다.")
    
    optimizer = PostgreSQLOptimizer(database_url)
    optimizer.initialize()
    return optimizer
