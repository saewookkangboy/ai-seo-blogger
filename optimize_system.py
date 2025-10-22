#!/usr/bin/env python3
"""
AI SEO Blogger 시스템 최적화 스크립트
불필요한 파일들을 정리하고 시스템 성능을 최적화합니다.
"""

import os
import shutil
import glob
import json
from pathlib import Path
from datetime import datetime, timedelta

def cleanup_pycache():
    """Python 캐시 파일 정리"""
    print("🧹 Python 캐시 파일 정리 중...")
    
    # __pycache__ 디렉토리 삭제
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                cache_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(cache_path)
                    print(f"  삭제됨: {cache_path}")
                except Exception as e:
                    print(f"  오류: {cache_path} - {e}")
    
    # .pyc 파일 삭제
    for pyc_file in glob.glob('**/*.pyc', recursive=True):
        try:
            os.remove(pyc_file)
            print(f"  삭제됨: {pyc_file}")
        except Exception as e:
            print(f"  오류: {pyc_file} - {e}")

def cleanup_test_files():
    """테스트 파일 정리"""
    print("🧪 테스트 파일 정리 중...")
    
    # 테스트 JSON 파일 패턴
    test_patterns = [
        '*test*.json',
        '*performance*.json',
        '*optimization*.json',
        '*stress*.json',
        '*complete*.json',
        '*gemini*.json',
        '*seo*.json',
        '*system*.json',
        '*crawler*.json',
        '*content*.json',
        '*enhanced*.json',
        '*geo*.json',
        '*report*.json',
        '*results*.json'
    ]
    
    for pattern in test_patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
                print(f"  삭제됨: {file_path}")
            except Exception as e:
                print(f"  오류: {file_path} - {e}")

def cleanup_debug_files():
    """디버그 파일 정리"""
    print("🐛 디버그 파일 정리 중...")
    
    debug_patterns = [
        'debug_*.html',
        'debug_*.json',
        'debug_*.txt',
        'test_*.html',
        'test_*.txt'
    ]
    
    for pattern in debug_patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
                print(f"  삭제됨: {file_path}")
            except Exception as e:
                print(f"  오류: {file_path} - {e}")

def cleanup_temp_files():
    """임시 파일 정리"""
    print("📁 임시 파일 정리 중...")
    
    temp_patterns = [
        '*.tmp',
        '*.bak',
        '*.backup',
        '*.swp',
        '*.swo',
        '*~',
        '.DS_Store'
    ]
    
    for pattern in temp_patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
                print(f"  삭제됨: {file_path}")
            except Exception as e:
                print(f"  오류: {file_path} - {e}")

def cleanup_old_logs():
    """오래된 로그 파일 정리"""
    print("📝 오래된 로그 파일 정리 중...")
    
    logs_dir = Path('logs')
    if logs_dir.exists():
        # 7일 이상 된 로그 파일 삭제
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for log_file in logs_dir.glob('*.log'):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                try:
                    log_file.unlink()
                    print(f"  삭제됨: {log_file}")
                except Exception as e:
                    print(f"  오류: {log_file} - {e}")

def optimize_database():
    """데이터베이스 최적화"""
    print("🗄️ 데이터베이스 최적화 중...")
    
    import sqlite3
    
    db_files = ['app/blog.db', 'app/news_archive.db']
    
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # VACUUM으로 데이터베이스 최적화
                cursor.execute("VACUUM")
                
                # 인덱스 재구성
                cursor.execute("REINDEX")
                
                conn.close()
                print(f"  최적화됨: {db_file}")
            except Exception as e:
                print(f"  오류: {db_file} - {e}")

def create_optimization_report():
    """최적화 리포트 생성"""
    print("📊 최적화 리포트 생성 중...")
    
    # 현재 디렉토리 크기 계산
    total_size = 0
    file_count = 0
    
    for root, dirs, files in os.walk('.'):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                total_size += os.path.getsize(file_path)
                file_count += 1
            except:
                pass
    
    report = {
        'optimization_date': datetime.now().isoformat(),
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'file_count': file_count,
        'optimization_actions': [
            'Python 캐시 파일 정리',
            '테스트 파일 정리',
            '디버그 파일 정리',
            '임시 파일 정리',
            '오래된 로그 파일 정리',
            '데이터베이스 최적화'
        ]
    }
    
    with open('system_optimization_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"  리포트 생성됨: system_optimization_report.json")
    print(f"  총 크기: {report['total_size_mb']}MB")
    print(f"  파일 개수: {report['file_count']}개")

def main():
    """메인 최적화 함수"""
    print("🚀 AI SEO Blogger 시스템 최적화 시작")
    print("=" * 50)
    
    # 최적화 전 상태
    print("📈 최적화 전 상태:")
    total_size_before = sum(
        os.path.getsize(os.path.join(root, file))
        for root, dirs, files in os.walk('.')
        for file in files
        if os.path.isfile(os.path.join(root, file))
    )
    print(f"  총 크기: {round(total_size_before / (1024 * 1024), 2)}MB")
    
    # 최적화 실행
    cleanup_pycache()
    cleanup_test_files()
    cleanup_debug_files()
    cleanup_temp_files()
    cleanup_old_logs()
    optimize_database()
    
    # 최적화 후 상태
    print("\n📉 최적화 후 상태:")
    total_size_after = sum(
        os.path.getsize(os.path.join(root, file))
        for root, dirs, files in os.walk('.')
        for file in files
        if os.path.isfile(os.path.join(root, file))
    )
    print(f"  총 크기: {round(total_size_after / (1024 * 1024), 2)}MB")
    
    # 절약된 공간 계산
    saved_space = total_size_before - total_size_after
    saved_percentage = (saved_space / total_size_before) * 100 if total_size_before > 0 else 0
    
    print(f"  절약된 공간: {round(saved_space / (1024 * 1024), 2)}MB ({saved_percentage:.1f}%)")
    
    # 리포트 생성
    create_optimization_report()
    
    print("\n✅ 시스템 최적화 완료!")

if __name__ == "__main__":
    main() 