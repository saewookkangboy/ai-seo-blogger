#!/usr/bin/env python3
"""
데이터베이스 테이블 생성 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal
from app.models import Base, BlogPost, APIKey, KeywordList, FeatureUpdate
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def create_tables():
    """데이터베이스 테이블을 생성합니다."""
    try:
        logger.info("데이터베이스 테이블 생성을 시작합니다...")
        
        # 테이블 생성
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블이 생성되었습니다.")
        
        # 테이블 생성 확인
        db = SessionLocal()
        try:
            # BlogPost 테이블 확인
            from sqlalchemy import text
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='blog_posts'"))
            if result.fetchone():
                logger.info("blog_posts 테이블이 성공적으로 생성되었습니다.")
                
                # 테이블 구조 확인
                result = db.execute(text("PRAGMA table_info(blog_posts)"))
                columns = result.fetchall()
                logger.info("blog_posts 테이블 컬럼:")
                for col in columns:
                    logger.info(f"  - {col[1]} ({col[2]})")
            else:
                logger.error("blog_posts 테이블이 생성되지 않았습니다.")
                
        finally:
            db.close()
        
        logger.info("데이터베이스 테이블 생성이 완료되었습니다.")
        
    except Exception as e:
        logger.error(f"데이터베이스 테이블 생성 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    create_tables() 