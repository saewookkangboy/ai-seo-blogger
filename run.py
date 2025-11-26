#!/usr/bin/env python3
"""
AI SEO Blog Generator 실행 스크립트
"""

import os
import sys
import uvicorn
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """메인 실행 함수"""
    # 개발 환경 설정
    if not os.getenv('DEBUG'):
        os.environ['DEBUG'] = 'True'
        print("🔧 개발 모드로 설정되었습니다.")
    
    # 설정 모듈 임포트
    try:
        from app.config import settings
        
        # 설정 유효성 검사
        errors = settings.validate_settings()
        if errors:
            print("⚠️  설정 오류가 발견되었습니다:")
            for error in errors:
                print(f"   {error}")
            print("   .env 파일에 API 키를 설정해주세요.")
        else:
            print("✅ 모든 API 키가 올바르게 설정되었습니다.")
            
    except Exception as e:
        print(f"⚠️  설정 로드 중 오류: {e}")
        print("   .env 파일을 확인해주세요.")
    
    # 로그 디렉토리 생성
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 서버 실행
    print("🚀 AI SEO Blog Generator를 시작합니다...")
    print("📝 API 문서: http://localhost:8000/docs")
    print("🌐 웹 인터페이스: http://localhost:8000")
    print("💚 헬스체크: http://localhost:8000/health")
    print("=" * 50)
    
    reload_enabled = os.getenv("UVICORN_RELOAD", "true").lower() == "true"
    reload_dirs = [str(project_root / "app")] if reload_enabled else None
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload_enabled,
        reload_dirs=reload_dirs,
        log_level="info"
    )

if __name__ == "__main__":
    main() 