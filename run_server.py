#!/usr/bin/env python3
"""
서버 실행 스크립트 (포트 충돌 방지 버전)
"""
import os
import sys
import uvicorn
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def find_free_port(start_port=8000, max_attempts=10):
    """사용 가능한 포트 찾기"""
    import socket
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

def main():
    """메인 실행 함수"""
    # 개발 환경 설정
    if not os.getenv('DEBUG'):
        os.environ['DEBUG'] = 'True'
        print("🔧 개발 모드로 설정되었습니다.")
    
    # 설정 모듈 임포트
    try:
        from app.config import settings
        errors = settings.validate_settings()
        if errors:
            print("⚠️  설정 오류가 발견되었습니다:")
            for error in errors:
                print(f"   {error}")
        else:
            print("✅ 모든 API 키가 올바르게 설정되었습니다.")
    except Exception as e:
        print(f"⚠️  설정 로드 중 오류: {e}")
    
    # 로그 디렉토리 생성
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 사용 가능한 포트 찾기
    port = find_free_port(8000)
    if port != 8000:
        print(f"⚠️  포트 8000이 사용 중이므로 포트 {port}를 사용합니다.")
    
    # 서버 실행
    print("🚀 AI SEO Blog Generator를 시작합니다...")
    print(f"📝 API 문서: http://localhost:{port}/docs")
    print(f"🌐 웹 인터페이스: http://localhost:{port}")
    print(f"💚 헬스체크: http://localhost:{port}/health")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",  # localhost만 바인딩
            port=port,
            reload=False,  # reload 비활성화
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

