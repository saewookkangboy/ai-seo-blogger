#!/usr/bin/env python3
"""
Google Drive API 통합 테스트 스크립트

이 스크립트는 Google Drive API와의 통합을 테스트합니다.
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.google_drive_service import GoogleDriveService
from app.database import SessionLocal
from app.models import BlogPost, APIKey, KeywordList, FeatureUpdate

def test_google_drive_authentication():
    """Google Drive API 인증을 테스트합니다."""
    print("🔐 Google Drive API 인증 테스트 시작...")
    
    try:
        drive_service = GoogleDriveService()
        success = drive_service.authenticate()
        
        if success:
            print("✅ Google Drive API 인증 성공!")
            return True
        else:
            print("❌ Google Drive API 인증 실패!")
            print("📝 credentials.json 파일이 올바르게 설정되었는지 확인하세요.")
            return False
            
    except Exception as e:
        print(f"❌ 인증 테스트 중 오류 발생: {e}")
        return False

def test_folder_creation():
    """Google Drive 폴더 생성을 테스트합니다."""
    print("\n📁 Google Drive 폴더 생성 테스트 시작...")
    
    try:
        drive_service = GoogleDriveService()
        
        if not drive_service.authenticate():
            print("❌ 인증 실패로 폴더 생성 테스트를 건너뜁니다.")
            return False
        
        test_folder_name = f"Test_Folder_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        folder_id = drive_service.create_folder(test_folder_name)
        
        if folder_id:
            print(f"✅ 폴더 생성 성공: {test_folder_name} (ID: {folder_id})")
            return True
        else:
            print("❌ 폴더 생성 실패!")
            return False
            
    except Exception as e:
        print(f"❌ 폴더 생성 테스트 중 오류 발생: {e}")
        return False

def test_dataframe_upload():
    """DataFrame 업로드를 테스트합니다."""
    print("\n📊 DataFrame 업로드 테스트 시작...")
    
    try:
        drive_service = GoogleDriveService()
        
        if not drive_service.authenticate():
            print("❌ 인증 실패로 DataFrame 업로드 테스트를 건너뜁니다.")
            return False
        
        # 테스트 데이터 생성
        test_data = {
            'id': [1, 2, 3],
            'title': ['테스트 포스트 1', '테스트 포스트 2', '테스트 포스트 3'],
            'keywords': ['테스트,키워드1', '테스트,키워드2', '테스트,키워드3'],
            'created_at': [datetime.now().isoformat()] * 3
        }
        
        df = pd.DataFrame(test_data)
        test_file_name = f"test_dataframe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        file_id = drive_service.upload_dataframe(df, test_file_name)
        
        if file_id:
            print(f"✅ DataFrame 업로드 성공: {test_file_name} (ID: {file_id})")
            return True
        else:
            print("❌ DataFrame 업로드 실패!")
            return False
            
    except Exception as e:
        print(f"❌ DataFrame 업로드 테스트 중 오류 발생: {e}")
        return False

def test_database_export():
    """데이터베이스 내보내기를 테스트합니다."""
    print("\n💾 데이터베이스 내보내기 테스트 시작...")
    
    try:
        drive_service = GoogleDriveService()
        db = SessionLocal()
        
        if not drive_service.authenticate():
            print("❌ 인증 실패로 데이터베이스 내보내기 테스트를 건너뜁니다.")
            return False
        
        # 테스트 폴더명 생성
        test_folder_name = f"Test_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 데이터베이스 내보내기 실행
        result = drive_service.export_database_to_drive(db, test_folder_name)
        
        if result["success"]:
            print(f"✅ 데이터베이스 내보내기 성공!")
            print(f"   폴더: {result['folder_name']}")
            print(f"   폴더 ID: {result['folder_id']}")
            print(f"   파일 수: {len(result['files'])}")
            
            for file_info in result['files']:
                print(f"   - {file_info['name']}: {file_info['count']}개 레코드")
            
            return True
        else:
            print(f"❌ 데이터베이스 내보내기 실패: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 데이터베이스 내보내기 테스트 중 오류 발생: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def test_backup_functionality():
    """백업 기능을 테스트합니다."""
    print("\n🔄 백업 기능 테스트 시작...")
    
    try:
        drive_service = GoogleDriveService()
        db = SessionLocal()
        
        if not drive_service.authenticate():
            print("❌ 인증 실패로 백업 기능 테스트를 건너뜁니다.")
            return False
        
        # 백업 실행
        result = drive_service.schedule_auto_backup(db, "test")
        
        if result["success"]:
            print(f"✅ 백업 성공!")
            print(f"   메시지: {result['message']}")
            print(f"   폴더 ID: {result['folder_id']}")
            print(f"   파일 수: {result['files_count']}")
            return True
        else:
            print(f"❌ 백업 실패: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 백업 기능 테스트 중 오류 발생: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def test_system_stats():
    """시스템 통계 생성을 테스트합니다."""
    print("\n📈 시스템 통계 생성 테스트 시작...")
    
    try:
        drive_service = GoogleDriveService()
        db = SessionLocal()
        
        # 시스템 통계 생성
        stats = drive_service._generate_system_stats(db)
        
        if "error" not in stats:
            print("✅ 시스템 통계 생성 성공!")
            print(f"   총 포스트: {stats.get('total_posts', 0)}")
            print(f"   발행된 포스트: {stats.get('published_posts', 0)}")
            print(f"   임시 포스트: {stats.get('draft_posts', 0)}")
            print(f"   카테고리 수: {len(stats.get('categories', []))}")
            print(f"   월별 통계: {len(stats.get('monthly_growth', []))}개 월")
            return True
        else:
            print(f"❌ 시스템 통계 생성 실패: {stats['error']}")
            return False
            
    except Exception as e:
        print(f"❌ 시스템 통계 생성 테스트 중 오류 발생: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def main():
    """메인 테스트 함수"""
    print("🚀 Google Drive API 통합 테스트를 시작합니다...\n")
    
    tests = [
        ("인증 테스트", test_google_drive_authentication),
        ("폴더 생성 테스트", test_folder_creation),
        ("DataFrame 업로드 테스트", test_dataframe_upload),
        ("시스템 통계 생성 테스트", test_system_stats),
        ("데이터베이스 내보내기 테스트", test_database_export),
        ("백업 기능 테스트", test_backup_functionality),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 중 예상치 못한 오류 발생: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n" + "="*50)
    print("📋 테스트 결과 요약")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("Google Drive API가 정상적으로 작동합니다.")
    else:
        print(f"\n⚠️ {total-passed}개 테스트가 실패했습니다.")
        print("설정을 확인하고 다시 시도해주세요.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 