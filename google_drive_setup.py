#!/usr/bin/env python3
"""
Google Drive API 설정 스크립트

이 스크립트는 Google Drive API를 사용하기 위한 초기 설정을 도와줍니다.
"""

import os
import json
from pathlib import Path

def create_credentials_template():
    """Google Drive API credentials.json 템플릿을 생성합니다."""
    
    template = {
        "installed": {
            "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
            "project_id": "your-project-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    with open("credentials.json", "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print("✅ credentials.json 템플릿이 생성되었습니다.")
    print("📝 Google Cloud Console에서 실제 값으로 교체해주세요.")

def create_env_template():
    """환경 변수 템플릿을 생성합니다."""
    
    env_content = """# Google Drive API 설정
GOOGLE_DRIVE_CREDENTIALS_PATH=credentials.json
GOOGLE_DRIVE_TOKEN_PATH=token.json
GOOGLE_DRIVE_BACKUP_FOLDER=AI_SEO_Blogger_Backups

# 백업 설정
GOOGLE_DRIVE_AUTO_BACKUP=true
GOOGLE_DRIVE_BACKUP_SCHEDULE=daily  # daily, weekly, monthly
GOOGLE_DRIVE_BACKUP_RETENTION_DAYS=30
"""
    
    with open(".env.google_drive", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print("✅ .env.google_drive 템플릿이 생성되었습니다.")

def create_setup_guide():
    """Google Drive API 설정 가이드를 생성합니다."""
    
    guide = """# Google Drive API 설정 가이드

## 1. Google Cloud Console 설정

### 1.1 프로젝트 생성
1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택

### 1.2 Google Drive API 활성화
1. "API 및 서비스" > "라이브러리"로 이동
2. "Google Drive API" 검색 후 활성화

### 1.3 사용자 인증 정보 생성
1. "API 및 서비스" > "사용자 인증 정보"로 이동
2. "사용자 인증 정보 만들기" > "OAuth 2.0 클라이언트 ID" 선택
3. 애플리케이션 유형: "데스크톱 앱" 선택
4. 이름 입력 후 생성

### 1.4 credentials.json 다운로드
1. 생성된 OAuth 2.0 클라이언트 ID 클릭
2. "JSON 다운로드" 버튼 클릭
3. 다운로드된 파일을 `credentials.json`으로 이름 변경
4. 프로젝트 루트 디렉토리에 저장

## 2. 환경 설정

### 2.1 환경 변수 설정
```bash
# .env 파일에 추가
GOOGLE_DRIVE_CREDENTIALS_PATH=credentials.json
GOOGLE_DRIVE_TOKEN_PATH=token.json
GOOGLE_DRIVE_BACKUP_FOLDER=AI_SEO_Blogger_Backups
GOOGLE_DRIVE_AUTO_BACKUP=true
GOOGLE_DRIVE_BACKUP_SCHEDULE=daily
```

### 2.2 필요한 패키지 설치
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client pandas
```

## 3. 초기 인증

### 3.1 첫 번째 실행
애플리케이션을 처음 실행하면 브라우저가 열리며 Google 계정 인증을 요청합니다.

### 3.2 권한 부여
1. Google 계정으로 로그인
2. "Google Drive API" 권한 요청 승인
3. 인증 완료 후 `token.json` 파일이 자동 생성됨

## 4. API 엔드포인트

### 4.1 데이터베이스 내보내기
```bash
POST /api/v1/google-drive/export-database
{
    "folder_name": "AI_SEO_Blogger_Export_20241201",
    "include_content": true,
    "include_stats": true
}
```

### 4.2 자동 백업
```bash
POST /api/v1/google-drive/backup-database
{
    "schedule_type": "daily",
    "folder_name": "AutoBackup_Daily"
}
```

### 4.3 연결 테스트
```bash
GET /api/v1/google-drive/test-connection
```

## 5. 보안 주의사항

### 5.1 파일 보안
- `credentials.json`과 `token.json` 파일을 Git에 커밋하지 마세요
- `.gitignore`에 다음 항목 추가:
```
credentials.json
token.json
.env.google_drive
```

### 5.2 권한 관리
- Google Drive API는 최소한의 권한만 요청합니다
- 필요시 Google Cloud Console에서 권한을 조정할 수 있습니다

## 6. 문제 해결

### 6.1 인증 오류
- `token.json` 파일을 삭제하고 다시 인증
- Google Cloud Console에서 OAuth 동의 화면 설정 확인

### 6.2 권한 오류
- Google Drive API가 활성화되어 있는지 확인
- OAuth 2.0 클라이언트 ID가 올바른지 확인

### 6.3 파일 업로드 오류
- Google Drive 저장 공간 확인
- 파일 크기 제한 확인 (Google Drive 무료 계정: 15GB)
"""
    
    with open("GOOGLE_DRIVE_SETUP_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print("✅ GOOGLE_DRIVE_SETUP_GUIDE.md 가이드가 생성되었습니다.")

def update_gitignore():
    """Gitignore 파일에 Google Drive 관련 파일들을 추가합니다."""
    
    gitignore_content = """
# Google Drive API
credentials.json
token.json
.env.google_drive
*.token
"""
    
    gitignore_path = Path(".gitignore")
    
    if gitignore_path.exists():
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if "credentials.json" not in content:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write(gitignore_content)
            print("✅ .gitignore에 Google Drive 관련 파일들이 추가되었습니다.")
        else:
            print("ℹ️ .gitignore에 이미 Google Drive 관련 설정이 있습니다.")
    else:
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(gitignore_content)
        print("✅ .gitignore 파일이 생성되고 Google Drive 관련 파일들이 추가되었습니다.")

def main():
    """메인 함수"""
    print("🚀 Google Drive API 설정 스크립트를 시작합니다...\n")
    
    # 1. credentials.json 템플릿 생성
    create_credentials_template()
    
    # 2. 환경 변수 템플릿 생성
    create_env_template()
    
    # 3. 설정 가이드 생성
    create_setup_guide()
    
    # 4. Gitignore 업데이트
    update_gitignore()
    
    print("\n🎉 Google Drive API 설정이 완료되었습니다!")
    print("\n📋 다음 단계:")
    print("1. Google Cloud Console에서 Google Drive API 활성화")
    print("2. OAuth 2.0 클라이언트 ID 생성")
    print("3. credentials.json 파일을 실제 값으로 교체")
    print("4. 애플리케이션 실행하여 초기 인증 완료")
    print("\n📖 자세한 내용은 GOOGLE_DRIVE_SETUP_GUIDE.md 파일을 참조하세요.")

if __name__ == "__main__":
    main() 