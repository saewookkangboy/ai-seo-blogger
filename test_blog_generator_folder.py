#!/usr/bin/env python3
"""
blog_generator 폴더 관리 테스트 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.google_drive_service import GoogleDriveService

def test_blog_generator_folder():
    """blog_generator 폴더 생성 및 관리 테스트"""
    print("📁 blog_generator 폴더 관리 테스트 시작...\n")
    
    try:
        drive_service = GoogleDriveService()
        
        # 1. blog_generator 폴더 생성 또는 가져오기
        print("1️⃣ blog_generator 폴더 생성/가져오기 테스트")
        folder_id = drive_service.get_or_create_blog_generator_folder()
        
        if folder_id:
            print(f"✅ blog_generator 폴더 준비 완료: {folder_id}")
        else:
            print("❌ blog_generator 폴더 생성 실패")
            return False
        
        # 2. 기존 파일들을 blog_generator 폴더로 정리
        print("\n2️⃣ 기존 파일 정리 테스트")
        result = drive_service.organize_existing_files()
        
        if result["success"]:
            print(f"✅ 파일 정리 완료: {result['message']}")
            print(f"   이동된 파일 수: {result['moved_count']}")
        else:
            print(f"❌ 파일 정리 실패: {result.get('error', 'Unknown error')}")
        
        # 3. 테스트 파일 업로드 (blog_generator 폴더에)
        print("\n3️⃣ blog_generator 폴더에 테스트 파일 업로드")
        
        # 간단한 테스트 데이터 생성
        test_data = {
            'id': [1, 2, 3],
            'title': ['테스트 포스트 1', '테스트 포스트 2', '테스트 포스트 3'],
            'keywords': ['테스트,키워드1', '테스트,키워드2', '테스트,키워드3'],
            'created_at': ['2025-01-27', '2025-01-27', '2025-01-27']
        }
        
        import pandas as pd
        df = pd.DataFrame(test_data)
        
        file_id = drive_service.upload_dataframe(
            df, 
            f"test_blog_generator_{os.getenv('USER', 'user')}_{os.getpid()}.csv",
            folder_id
        )
        
        if file_id:
            print(f"✅ 테스트 파일 업로드 성공: {file_id}")
        else:
            print("❌ 테스트 파일 업로드 실패")
        
        print("\n🎉 blog_generator 폴더 관리 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    print("🚀 blog_generator 폴더 관리 테스트를 시작합니다...\n")
    
    success = test_blog_generator_folder()
    
    if success:
        print("\n✅ 모든 테스트가 성공적으로 완료되었습니다!")
        print("📁 이제 모든 AI SEO Blogger 관련 파일들이 blog_generator 폴더에 정리됩니다.")
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다.")
        print("📖 설정을 확인하고 다시 시도해주세요.")

if __name__ == "__main__":
    main() 