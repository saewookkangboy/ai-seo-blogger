#!/usr/bin/env python3
"""
Google Drive API 간단 테스트 스크립트
"""

import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Drive API 스코프
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def test_google_drive_connection():
    """Google Drive API 연결을 테스트합니다."""
    print("🔐 Google Drive API 연결 테스트 시작...")
    
    try:
        creds = None
        
        # 1. credentials.json 파일 확인
        if os.path.exists('credentials.json'):
            print("✅ credentials.json 파일 발견")
            
            # 2. 기존 토큰 확인
            if os.path.exists('token.json'):
                print("✅ token.json 파일 발견")
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
            # 3. 토큰이 유효하지 않으면 새로 인증
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    print("🔄 토큰 갱신 중...")
                    creds.refresh(Request())
                else:
                    print("🔑 새로운 인증 시작...")
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # 4. 토큰 저장
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
                print("✅ 토큰 저장 완료")
            
            # 5. Google Drive API 서비스 생성
            service = build('drive', 'v3', credentials=creds)
            
            # 6. 간단한 API 호출 테스트
            print("📋 Google Drive 파일 목록 조회 중...")
            results = service.files().list(pageSize=10).execute()
            files = results.get('files', [])
            
            if not files:
                print("📁 Google Drive에 파일이 없습니다.")
            else:
                print(f"📁 Google Drive에서 {len(files)}개 파일 발견:")
                for file in files:
                    print(f"   - {file['name']} ({file['id']})")
            
            print("✅ Google Drive API 연결 성공!")
            return True
            
        else:
            print("❌ credentials.json 파일을 찾을 수 없습니다.")
            print("📝 Google Cloud Console에서 credentials.json 파일을 다운로드하세요.")
            return False
            
    except HttpError as error:
        print(f"❌ Google Drive API 오류: {error}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

def create_test_file():
    """테스트 파일을 Google Drive에 업로드합니다."""
    print("\n📤 테스트 파일 업로드 중...")
    
    try:
        # 1. 인증
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            print("❌ 유효한 인증 정보가 없습니다.")
            return False
        
        # 2. 서비스 생성
        service = build('drive', 'v3', credentials=creds)
        
        # 3. 테스트 파일 생성
        test_content = "AI SEO Blogger Google Drive API 테스트 파일입니다.\n생성일: 2025-01-27"
        
        from googleapiclient.http import MediaIoBaseUpload
        import io
        
        file_metadata = {
            'name': 'test_file.txt',
            'mimeType': 'text/plain'
        }
        
        media = MediaIoBaseUpload(
            io.BytesIO(test_content.encode('utf-8')),
            mimetype='text/plain',
            resumable=True
        )
        
        # 4. 파일 업로드
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        print(f"✅ 테스트 파일 업로드 성공: {file.get('id')}")
        return True
        
    except Exception as e:
        print(f"❌ 파일 업로드 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🚀 Google Drive API 간단 테스트를 시작합니다...\n")
    
    # 1. 연결 테스트
    if test_google_drive_connection():
        # 2. 파일 업로드 테스트
        create_test_file()
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
    else:
        print("\n⚠️ 테스트가 실패했습니다.")
        print("📖 GOOGLE_DRIVE_SETUP_GUIDE.md 파일을 참조하여 설정을 확인하세요.")

if __name__ == "__main__":
    main() 