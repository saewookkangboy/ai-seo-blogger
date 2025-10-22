#!/usr/bin/env python3
"""
Google Docs Archive 기능 테스트 스크립트
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.google_docs_service import google_docs_service
from app.config import settings

async def test_google_docs_archive():
    """Google Docs Archive 기능을 테스트합니다."""
    
    print("🔍 Google Docs Archive 기능 테스트 시작")
    print("=" * 50)
    
    # 1. 설정 확인
    print("1️⃣ 설정 확인")
    print(f"   - Archive 활성화: {settings.google_docs_archive_enabled}")
    print(f"   - Archive 폴더: {settings.google_docs_archive_folder}")
    print(f"   - 자동 Archive: {settings.google_docs_auto_archive}")
    print(f"   - 클라이언트 ID: {settings.google_drive_client_id[:20]}...")
    print()
    
    # 2. 인증 테스트
    print("2️⃣ Google Docs API 인증 테스트")
    try:
        auth_success = google_docs_service.authenticate()
        if auth_success:
            print("   ✅ Google Docs API 인증 성공")
        else:
            print("   ❌ Google Docs API 인증 실패")
            return False
    except Exception as e:
        print(f"   ❌ 인증 중 오류 발생: {e}")
        return False
    print()
    
    # 3. Archive 폴더 생성 테스트
    print("3️⃣ Archive 폴더 생성 테스트")
    try:
        folder_id = google_docs_service.create_archive_folder("AI_SEO_Blogger_Archive_Test")
        if folder_id:
            print(f"   ✅ Archive 폴더 생성 성공: {folder_id}")
        else:
            print("   ❌ Archive 폴더 생성 실패")
            return False
    except Exception as e:
        print(f"   ❌ 폴더 생성 중 오류 발생: {e}")
        return False
    print()
    
    # 4. 테스트 블로그 포스트 데이터 생성
    print("4️⃣ 테스트 블로그 포스트 생성")
    test_blog_post = {
        'title': f'테스트 블로그 포스트 - {datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'content': '''
        <h1>AI SEO Blogger 테스트 포스트</h1>
        
        <h2>소개</h2>
        <p>이 문서는 Google Docs Archive 기능을 테스트하기 위해 생성된 테스트 블로그 포스트입니다.</p>
        
        <h2>주요 기능</h2>
        <ul>
            <li>자동 블로그 포스트 생성</li>
            <li>SEO 최적화</li>
            <li>Google Docs Archive 저장</li>
            <li>키워드 분석</li>
        </ul>
        
        <h2>결론</h2>
        <p>AI SEO Blogger는 강력한 콘텐츠 생성 도구로, Google Docs와의 연동을 통해 효율적인 콘텐츠 관리가 가능합니다.</p>
        ''',
        'keywords': 'AI, SEO, 블로그, 콘텐츠 생성, Google Docs',
        'source_url': 'https://example.com/test',
        'ai_mode': 'test',
        'summary': 'Google Docs Archive 기능 테스트를 위한 샘플 블로그 포스트입니다.',
        'created_at': datetime.now().isoformat()
    }
    print("   ✅ 테스트 데이터 준비 완료")
    print()
    
    # 5. Google Docs 문서 생성 테스트
    print("5️⃣ Google Docs 문서 생성 테스트")
    try:
        doc_url = google_docs_service.create_blog_post_document(test_blog_post, folder_id)
        if doc_url:
            print(f"   ✅ Google Docs 문서 생성 성공")
            print(f"   📄 문서 URL: {doc_url}")
        else:
            print("   ❌ Google Docs 문서 생성 실패")
            return False
    except Exception as e:
        print(f"   ❌ 문서 생성 중 오류 발생: {e}")
        return False
    print()
    
    # 6. Archive 문서 목록 조회 테스트
    print("6️⃣ Archive 문서 목록 조회 테스트")
    try:
        documents = google_docs_service.get_archive_documents(folder_id, limit=5)
        print(f"   ✅ Archive 문서 목록 조회 성공: {len(documents)}개 문서")
        for i, doc in enumerate(documents, 1):
            print(f"   {i}. {doc['name']} (생성: {doc['created_time'][:10]})")
    except Exception as e:
        print(f"   ❌ 문서 목록 조회 중 오류 발생: {e}")
        return False
    print()
    
    print("🎉 Google Docs Archive 기능 테스트 완료!")
    print("=" * 50)
    return True

async def test_archive_api_endpoints():
    """Archive API 엔드포인트를 테스트합니다."""
    
    print("🔍 Archive API 엔드포인트 테스트")
    print("=" * 50)
    
    # FastAPI 앱을 임포트하여 테스트
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # 1. Archive 문서 목록 조회 테스트
        print("1️⃣ GET /api/v1/blog-generation/archive/documents 테스트")
        response = client.get("/api/v1/blog-generation/archive/documents?limit=5")
        print(f"   상태 코드: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 성공: {data.get('message', '')}")
            print(f"   📊 문서 수: {data.get('data', {}).get('total_count', 0)}")
        else:
            print(f"   ❌ 실패: {response.text}")
        print()
        
        # 2. Archive 설정 확인
        print("2️⃣ Archive 설정 확인")
        print(f"   - Archive 활성화: {settings.google_docs_archive_enabled}")
        print(f"   - 자동 Archive: {settings.google_docs_auto_archive}")
        print()
        
    except ImportError as e:
        print(f"   ⚠️ FastAPI 테스트 클라이언트를 사용할 수 없습니다: {e}")
        print("   pip install httpx 를 실행하여 설치하세요.")
    except Exception as e:
        print(f"   ❌ API 테스트 중 오류 발생: {e}")
    
    print("🎉 Archive API 테스트 완료!")
    print("=" * 50)

def main():
    """메인 함수"""
    print("🚀 Google Docs Archive 기능 종합 테스트")
    print("=" * 60)
    
    # 비동기 테스트 실행
    try:
        # 기본 기능 테스트
        success = asyncio.run(test_google_docs_archive())
        
        if success:
            print("\n✅ 모든 기본 테스트 통과!")
            
            # API 엔드포인트 테스트
            asyncio.run(test_archive_api_endpoints())
        else:
            print("\n❌ 일부 테스트 실패")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ 테스트가 사용자에 의해 중단되었습니다.")
        return 1
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        return 1
    
    print("\n🎉 모든 테스트 완료!")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
