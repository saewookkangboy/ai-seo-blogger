"""
데이터베이스 마이그레이션 서비스
SQLite에서 PostgreSQL로 마이그레이션 지원
"""

import os
import sqlite3
from typing import Dict, Any, Optional, List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import logging

# psycopg2는 선택적 의존성
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from app.utils.logger import setup_logger
from app.config import settings
from app.database import SessionLocal, engine

logger = setup_logger(__name__)


class DatabaseMigration:
    """데이터베이스 마이그레이션 클래스"""
    
    def __init__(self, source_db_url: str, target_db_url: str):
        """
        Args:
            source_db_url: 소스 데이터베이스 URL (SQLite)
            target_db_url: 대상 데이터베이스 URL (PostgreSQL)
        """
        self.source_db_url = source_db_url
        self.target_db_url = target_db_url
        self.source_engine = None
        self.target_engine = None
    
    def initialize(self):
        """초기화"""
        self.source_engine = create_engine(self.source_db_url)
        self.target_engine = create_engine(self.target_db_url)
        logger.info("마이그레이션 엔진 초기화 완료")
    
    def get_table_names(self, engine) -> List[str]:
        """테이블 목록 조회"""
        with engine.connect() as conn:
            if self.source_db_url.startswith("sqlite"):
                # SQLite
                result = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ))
            else:
                # PostgreSQL
                result = conn.execute(text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                ))
            return [row[0] for row in result]
    
    def get_table_schema(self, engine, table_name: str) -> List[Dict[str, Any]]:
        """테이블 스키마 조회"""
        with engine.connect() as conn:
            if self.source_db_url.startswith("sqlite"):
                # SQLite
                result = conn.execute(text(
                    f"PRAGMA table_info({table_name})"
                ))
                columns = []
                for row in result:
                    columns.append({
                        'name': row[1],
                        'type': row[2],
                        'notnull': row[3],
                        'default': row[4],
                        'pk': row[5]
                    })
            else:
                # PostgreSQL
                result = conn.execute(text(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """))
                columns = []
                for row in result:
                    columns.append({
                        'name': row[0],
                        'type': row[1],
                        'notnull': row[2] == 'NO',
                        'default': row[3]
                    })
            return columns
    
    def get_table_data(self, engine, table_name: str) -> List[Dict[str, Any]]:
        """테이블 데이터 조회"""
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name}"))
            columns = result.keys()
            rows = []
            for row in result:
                rows.append(dict(zip(columns, row)))
            return rows
    
    def migrate_table(self, table_name: str) -> Dict[str, Any]:
        """테이블 마이그레이션"""
        logger.info(f"테이블 마이그레이션 시작: {table_name}")
        
        try:
            # 소스 테이블 데이터 조회
            source_data = self.get_table_data(self.source_engine, table_name)
            row_count = len(source_data)
            
            if row_count == 0:
                logger.info(f"테이블 {table_name}에 데이터가 없습니다.")
                return {
                    'table': table_name,
                    'status': 'skipped',
                    'rows': 0
                }
            
            # 대상 테이블에 데이터 삽입
            with self.target_engine.connect() as conn:
                # 배치 삽입
                batch_size = 1000
                inserted = 0
                
                for i in range(0, row_count, batch_size):
                    batch = source_data[i:i + batch_size]
                    
                    if not batch:
                        break
                    
                    # 컬럼명 추출
                    columns = list(batch[0].keys())
                    
                    # 배치 삽입
                    for row in batch:
                        try:
                            # 컬럼명과 값 매핑
                            values = {col: row[col] for col in columns}
                            
                            # INSERT 문 생성
                            if self.target_db_url.startswith("postgresql"):
                                # PostgreSQL: ON CONFLICT DO NOTHING
                                column_names = ', '.join(columns)
                                placeholders = ', '.join([f':{col}' for col in columns])
                                insert_sql = f"""
                                    INSERT INTO {table_name} ({column_names})
                                    VALUES ({placeholders})
                                    ON CONFLICT DO NOTHING
                                """
                            else:
                                # SQLite: INSERT OR IGNORE
                                column_names = ', '.join(columns)
                                placeholders = ', '.join([f':{col}' for col in columns])
                                insert_sql = f"""
                                    INSERT OR IGNORE INTO {table_name} ({column_names})
                                    VALUES ({placeholders})
                                """
                            
                            conn.execute(text(insert_sql), values)
                            inserted += 1
                        except Exception as e:
                            logger.warning(f"행 삽입 실패: {e}")
                            continue
                    
                    conn.commit()
                    logger.info(f"테이블 {table_name}: {inserted}/{row_count} 행 삽입 완료")
            
            return {
                'table': table_name,
                'status': 'success',
                'rows': row_count,
                'inserted': inserted
            }
        
        except Exception as e:
            logger.error(f"테이블 {table_name} 마이그레이션 실패: {e}")
            return {
                'table': table_name,
                'status': 'failed',
                'error': str(e)
            }
    
    def migrate_all(self) -> Dict[str, Any]:
        """전체 데이터베이스 마이그레이션"""
        logger.info("전체 데이터베이스 마이그레이션 시작")
        
        results = {
            'tables': [],
            'total_tables': 0,
            'success_tables': 0,
            'failed_tables': 0,
            'total_rows': 0
        }
        
        try:
            # 테이블 목록 조회
            table_names = self.get_table_names(self.source_engine)
            results['total_tables'] = len(table_names)
            
            logger.info(f"마이그레이션할 테이블: {table_names}")
            
            # 각 테이블 마이그레이션
            for table_name in table_names:
                result = self.migrate_table(table_name)
                results['tables'].append(result)
                
                if result['status'] == 'success':
                    results['success_tables'] += 1
                    results['total_rows'] += result.get('rows', 0)
                elif result['status'] == 'failed':
                    results['failed_tables'] += 1
            
            logger.info(f"마이그레이션 완료: {results['success_tables']}/{results['total_tables']} 테이블 성공")
            
        except Exception as e:
            logger.error(f"마이그레이션 중 오류: {e}")
            results['error'] = str(e)
        
        return results
    
    def verify_migration(self) -> Dict[str, Any]:
        """마이그레이션 검증"""
        logger.info("마이그레이션 검증 시작")
        
        verification = {
            'tables': [],
            'all_match': True
        }
        
        try:
            source_tables = self.get_table_names(self.source_engine)
            target_tables = self.get_table_names(self.target_engine)
            
            for table_name in source_tables:
                if table_name not in target_tables:
                    verification['tables'].append({
                        'table': table_name,
                        'status': 'missing',
                        'match': False
                    })
                    verification['all_match'] = False
                    continue
                
                # 행 수 비교
                source_count = len(self.get_table_data(self.source_engine, table_name))
                target_count = len(self.get_table_data(self.target_engine, table_name))
                
                match = source_count == target_count
                verification['tables'].append({
                    'table': table_name,
                    'status': 'verified' if match else 'mismatch',
                    'source_rows': source_count,
                    'target_rows': target_count,
                    'match': match
                })
                
                if not match:
                    verification['all_match'] = False
            
            logger.info(f"검증 완료: {'성공' if verification['all_match'] else '실패'}")
            
        except Exception as e:
            logger.error(f"검증 중 오류: {e}")
            verification['error'] = str(e)
            verification['all_match'] = False
        
        return verification


def migrate_to_postgresql(source_db_url: str, target_db_url: str) -> Dict[str, Any]:
    """
    SQLite에서 PostgreSQL로 마이그레이션
    
    Args:
        source_db_url: SQLite 데이터베이스 URL
        target_db_url: PostgreSQL 데이터베이스 URL
        
    Returns:
        마이그레이션 결과
    """
    migration = DatabaseMigration(source_db_url, target_db_url)
    migration.initialize()
    
    # 마이그레이션 실행
    results = migration.migrate_all()
    
    # 검증
    verification = migration.verify_migration()
    results['verification'] = verification
    
    return results
