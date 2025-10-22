#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal
from app.models import Base
from app.crud import initialize_default_keywords
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def init_database():
    """데이터베이스를 초기화합니다."""
    try:
        logger.info("데이터베이스 초기화를 시작합니다...")
        
        # 테이블 생성
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블이 생성되었습니다.")
        
        # 기본 키워드 초기화
        db = SessionLocal()
        try:
            initialize_default_keywords(db)
            logger.info("기본 키워드가 초기화되었습니다.")
        finally:
            db.close()
        
        logger.info("데이터베이스 초기화가 완료되었습니다.")
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    init_database() 