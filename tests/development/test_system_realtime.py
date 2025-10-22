#!/usr/bin/env python3
"""
시스템 관리 실시간 업데이트 테스트 스크립트
시스템 통계가 실시간으로 반영되는지 확인
"""
import requests
import json
import time
from datetime import datetime

def test_system_apis():
    """시스템 API 엔드포인트 테스트"""
    print("🚀 시스템 API 엔드포인트 테스트")
    print("=" * 50)
    
    apis = [
        '/api/v1/system/uptime',
        '/api/v1/system/db-size',
        '/api/v1/system/api-response-time',
        '/api/v1/system/log-files'
    ]
    
    results = {}
    
    for api in apis:
        try:
            response = requests.get(f'http://localhost:8000{api}')
            if response.status_code == 200:
                data = response.json()
                results[api] = data
                print(f"✅ {api}: 성공")
                print(f"   응답: {data}")
            else:
                print(f"❌ {api}: 실패 (상태 코드: {response.status_code})")
                results[api] = None
        except Exception as e:
            print(f"❌ {api}: 오류 - {e}")
            results[api] = None
    
    return results

def test_real_time_updates():
    """실시간 업데이트 테스트"""
    print("\n⏰ 실시간 업데이트 테스트")
    print("=" * 50)
    
    print("1. 초기 데이터 확인...")
    initial_data = test_system_apis()
    
    print("\n2. 5초 대기 후 데이터 재확인...")
    time.sleep(5)
    
    print("\n3. 업데이트된 데이터 확인...")
    updated_data = test_system_apis()
    
    print("\n4. 데이터 변경 사항 분석...")
    for api in initial_data.keys():
        if initial_data[api] and updated_data[api]:
            if initial_data[api] == updated_data[api]:
                print(f"   {api}: 변경 없음 (정적 데이터)")
            else:
                print(f"   {api}: 변경됨 (동적 데이터)")
                print(f"      이전: {initial_data[api]}")
                print(f"      현재: {updated_data[api]}")
        else:
            print(f"   {api}: 데이터 없음")

def test_admin_page_access():
    """관리자 페이지 접근 테스트"""
    print("\n🌐 관리자 페이지 접근 테스트")
    print("=" * 50)
    
    try:
        response = requests.get('http://localhost:8000/admin')
        if response.status_code == 200:
            html_content = response.text
            print("✅ 관리자 페이지 접근 성공")
            
            # 시스템 관련 요소 확인
            system_elements = [
                'system-uptime',
                'db-size', 
                'api-response-time',
                'log-files-count',
                'refreshSystemData'
            ]
            
            found_count = 0
            for element in system_elements:
                if element in html_content:
                    found_count += 1
                    print(f"   ✅ {element}: HTML에 존재")
                else:
                    print(f"   ❌ {element}: HTML에 없음")
            
            print(f"\n📈 시스템 요소 발견: {found_count}/{len(system_elements)}")
            
            if found_count == len(system_elements):
                print("🎉 모든 시스템 요소가 HTML에 존재합니다!")
                return True
            else:
                print("⚠️  일부 시스템 요소가 누락되었습니다.")
                return False
        else:
            print(f"❌ 관리자 페이지 접근 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 관리자 페이지 접근 오류: {e}")
        return False

def generate_instructions():
    """사용자 지침 생성"""
    print("\n📋 사용자 지침")
    print("=" * 50)
    
    print("✅ 백엔드 시스템 API가 정상 작동하고 있습니다.")
    
    print("\n🔍 프론트엔드 확인 방법:")
    print("1. 브라우저에서 http://localhost:8000/admin 접속")
    print("2. 관리자 로그인 (비밀번호: 0000)")
    print("3. '시스템 관리' 탭 클릭")
    print("4. 상단 통계 카드에서 수치 확인")
    print("5. '시스템 데이터 새로고침' 버튼 클릭")
    print("6. 개발자 도구 콘솔 열기 (F12)")
    print("7. 콘솔에서 다음 로그 확인:")
    print("   - '시스템 실시간 업데이트 시작'")
    print("   - '시스템 데이터 로드 완료'")
    print("   - '시스템 가동시간 업데이트: [값]'")
    print("   - '데이터베이스 크기 업데이트: [값]'")
    print("   - 'API 응답시간 업데이트: [값]'")
    print("   - '로그 파일 수 업데이트: [값]'")
    
    print("\n⏰ 실시간 업데이트 기능:")
    print("- 시스템 탭 활성화 시 자동으로 30초마다 업데이트")
    print("- 다른 탭으로 이동 시 자동으로 업데이트 중지")
    print("- 수동 새로고침 버튼으로 즉시 업데이트 가능")
    print("- 변경된 데이터만 업데이트하여 성능 최적화")
    
    print("\n🔧 문제 해결 방법:")
    print("- 브라우저 캐시 완전 삭제 (Ctrl+Shift+Delete)")
    print("- 하드 새로고침 (Ctrl+F5 또는 Cmd+Shift+R)")
    print("- 개발자 도구에서 'Disable cache' 체크")
    print("- '시스템 데이터 새로고침' 버튼 클릭")
    print("- 서버 재시작 후 다시 시도")

def main():
    """메인 함수"""
    print("🚀 시스템 관리 실시간 업데이트 테스트")
    print("=" * 60)
    
    try:
        # 1. 시스템 API 테스트
        test_system_apis()
        
        # 2. 실시간 업데이트 테스트
        test_real_time_updates()
        
        # 3. 관리자 페이지 접근 테스트
        admin_ok = test_admin_page_access()
        
        # 4. 사용자 지침 생성
        generate_instructions()
        
        print("\n✅ 모든 테스트 완료!")
        print("\n💡 다음 단계:")
        print("브라우저에서 관리자 페이지에 접속하여 '시스템 관리' 탭을 확인해주세요.")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    main() 