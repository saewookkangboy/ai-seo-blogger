#!/usr/bin/env python3
"""
SQLite에서 PostgreSQL로 마이그레이션 스크립트
"""

import sys
import os
import argparse

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.database_migration import migrate_to_postgresql
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='SQLite에서 PostgreSQL로 마이그레이션')
    parser.add_argument('--source', type=str, default=settings.database_url,
                       help='소스 데이터베이스 URL (SQLite)')
    parser.add_argument('--target', type=str, required=True,
                       help='대상 데이터베이스 URL (PostgreSQL)')
    parser.add_argument('--verify', action='store_true',
                       help='마이그레이션 후 검증')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("SQLite에서 PostgreSQL로 마이그레이션")
    print("=" * 60)
    print(f"소스: {args.source}")
    print(f"대상: {args.target}")
    print()
    
    try:
        # 마이그레이션 실행
        print("마이그레이션 시작...")
        results = migrate_to_postgresql(args.source, args.target)
        
        print("\n마이그레이션 결과:")
        print(f"  - 총 테이블: {results['total_tables']}")
        print(f"  - 성공: {results['success_tables']}")
        print(f"  - 실패: {results['failed_tables']}")
        print(f"  - 총 행: {results['total_rows']}")
        
        if results.get('verification'):
            verification = results['verification']
            print(f"\n검증 결과: {'성공' if verification['all_match'] else '실패'}")
            for table_result in verification['tables']:
                status = table_result['status']
                match = table_result['match']
                print(f"  - {table_result['table']}: {status} ({'일치' if match else '불일치'})")
        
        print("\n✅ 마이그레이션 완료!")
        return 0
    
    except Exception as e:
        print(f"\n❌ 마이그레이션 실패: {e}")
        logger.error(f"마이그레이션 실패: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
