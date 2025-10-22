#!/usr/bin/env python3
"""
OAuth URL 테스트 스크립트
"""

import urllib.parse

def generate_oauth_url():
    """OAuth URL을 생성합니다."""
    
    # OAuth 파라미터
    params = {
        'response_type': 'code',
        'client_id': '1050278621988-s7bg1k15tm114icvq2ad8aa49ohj2q5t.apps.googleusercontent.com',
        'redirect_uri': 'http://localhost:8080',
        'scope': 'https://www.googleapis.com/auth/drive.file',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    # URL 생성
    base_url = 'https://accounts.google.com/o/oauth2/auth'
    oauth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    return oauth_url

def main():
    """메인 함수"""
    print("🔗 OAuth URL 생성 중...\n")
    
    oauth_url = generate_oauth_url()
    
    print("📋 생성된 OAuth URL:")
    print("=" * 80)
    print(oauth_url)
    print("=" * 80)
    
    print("\n📝 사용 방법:")
    print("1. 위 URL을 브라우저에 복사하여 붙여넣기")
    print("2. Google 계정으로 로그인 (pakseri@gmail.com)")
    print("3. 권한 승인")
    print("4. 리디렉션된 URL에서 'code' 파라미터 확인")
    
    print("\n⚠️  주의사항:")
    print("- Google Cloud Console에서 OAuth 동의 화면 설정 완료 필요")
    print("- 테스트 사용자에 pakseri@gmail.com 추가 필요")
    print("- Google Drive API 활성화 필요")
    
    print("\n🔧 문제 해결:")
    print("- 403 오류: OAuth 동의 화면 설정 확인")
    print("- 401 오류: 클라이언트 ID/시크릿 확인")
    print("- 400 오류: 리디렉션 URI 확인")

if __name__ == "__main__":
    main() 