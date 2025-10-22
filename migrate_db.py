#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.utils.logger import setup_logger
from sqlalchemy import text

logger = setup_logger(__name__)

def migrate_database():
    """데이터베이스를 마이그레이션합니다."""
    try:
        logger.info("데이터베이스 마이그레이션을 시작합니다...")
        
        db = SessionLocal()
        try:
            # 기존 테이블 구조 확인
            result = db.execute(text("PRAGMA table_info(blog_posts)"))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            
            logger.info(f"현재 blog_posts 테이블 컬럼: {column_names}")
            
            # 필요한 컬럼들 추가
            new_columns = [
                ("category", "VARCHAR(50) DEFAULT '기타'"),
                ("status", "VARCHAR(20) DEFAULT 'draft'"),
                ("description", "VARCHAR(500)")
            ]
            
            for col_name, col_type in new_columns:
                if col_name not in column_names:
                    logger.info(f"컬럼 {col_name} 추가 중...")
                    db.execute(text(f"ALTER TABLE blog_posts ADD COLUMN {col_name} {col_type}"))
                    logger.info(f"컬럼 {col_name} 추가 완료")
                else:
                    logger.info(f"컬럼 {col_name} 이미 존재함")
            
            # 변경사항 커밋
            db.commit()
            
            # 최종 테이블 구조 확인
            result = db.execute(text("PRAGMA table_info(blog_posts)"))
            columns = result.fetchall()
            logger.info("마이그레이션 후 blog_posts 테이블 컬럼:")
            for col in columns:
                logger.info(f"  - {col[1]} ({col[2]})")
            
            logger.info("데이터베이스 마이그레이션이 완료되었습니다.")
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"데이터베이스 마이그레이션 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    migrate_database() 