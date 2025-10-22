#!/usr/bin/env python3
"""
관리 대시보드 네비게이션 테스트 스크립트
통계 대시보드 메뉴 클릭 문제를 진단하고 해결합니다.
"""
import requests
import time
from datetime import datetime

def test_admin_page_access():
    """관리자 페이지 접근 테스트"""
    print("🌐 관리자 페이지 접근 테스트")
    print("=" * 50)
    
    try:
        response = requests.get('http://localhost:8000/admin')
        if response.status_code == 200:
            html_content = response.text
            print("✅ 관리자 페이지 접근 성공")
            
            # 대시보드 관련 요소 확인
            dashboard_elements = [
                'showContent(\'dashboard\')',
                'dashboard-content',
                'total-posts',
                'total-keywords',
                'api-calls-today',
                'crawl-success-rate'
            ]
            
            found_count = 0
            for element in dashboard_elements:
                if element in html_content:
                    found_count += 1
                    print(f"   ✅ {element}: HTML에 존재")
                else:
                    print(f"   ❌ {element}: HTML에 없음")
            
            print(f"\n📈 대시보드 요소 발견: {found_count}/{len(dashboard_elements)}")
            
            if found_count == len(dashboard_elements):
                print("🎉 모든 대시보드 요소가 HTML에 존재합니다!")
                return True
            else:
                print("⚠️ 일부 대시보드 요소가 누락되었습니다.")
                return False
        else:
            print(f"❌ 관리자 페이지 접근 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 관리자 페이지 접근 오류: {e}")
        return False

def test_api_endpoints():
    """대시보드 관련 API 엔드포인트 테스트"""
    print("\n🚀 대시보드 API 엔드포인트 테스트")
    print("=" * 50)
    
    endpoints = [
        '/api/v1/posts',
        '/api/v1/keywords',
        '/api/v1/stats/dashboard'
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://localhost:8000{endpoint}')
            if response.status_code == 200:
                data = response.json()
                results[endpoint] = {
                    "status": "success",
                    "data_length": len(data) if isinstance(data, list) else "object",
                    "status_code": response.status_code
                }
                print(f"✅ {endpoint}: 성공 (데이터: {results[endpoint]['data_length']})")
            else:
                results[endpoint] = {
                    "status": "error",
                    "status_code": response.status_code
                }
                print(f"❌ {endpoint}: 실패 (상태 코드: {response.status_code})")
        except Exception as e:
            results[endpoint] = {
                "status": "error",
                "error": str(e)
            }
            print(f"❌ {endpoint}: 오류 - {e}")
    
    success_count = sum(1 for r in results.values() if r["status"] == "success")
    print(f"\n📊 API 테스트 결과: {success_count}/{len(endpoints)} 성공")
    
    return results

def test_dashboard_data_flow():
    """대시보드 데이터 흐름 테스트"""
    print("\n📊 대시보드 데이터 흐름 테스트")
    print("=" * 50)
    
    try:
        # 1. 포스트 데이터 로드
        print("1. 포스트 데이터 로드...")
        posts_response = requests.get('http://localhost:8000/api/v1/posts')
        posts_data = posts_response.json()
        print(f"   ✅ 포스트 데이터: {len(posts_data)}개")
        
        # 2. 키워드 데이터 로드
        print("2. 키워드 데이터 로드...")
        keywords_response = requests.get('http://localhost:8000/api/v1/keywords')
        keywords_data = keywords_response.json()
        print(f"   ✅ 키워드 데이터: {len(keywords_data)}개")
        
        # 3. 통계 데이터 로드
        print("3. 통계 데이터 로드...")
        stats_response = requests.get('http://localhost:8000/api/v1/stats/dashboard')
        stats_data = stats_response.json()
        print(f"   ✅ 통계 데이터: {stats_data}")
        
        # 4. 데이터 일관성 확인
        print("4. 데이터 일관성 확인...")
        expected_posts = stats_data.get('total_posts', 0)
        expected_keywords = stats_data.get('total_keywords', 0)
        
        if len(posts_data) == expected_posts:
            print(f"   ✅ 포스트 수 일치: {len(posts_data)}")
        else:
            print(f"   ⚠️ 포스트 수 불일치: 실제 {len(posts_data)}, 통계 {expected_posts}")
        
        if len(keywords_data) == expected_keywords:
            print(f"   ✅ 키워드 수 일치: {len(keywords_data)}")
        else:
            print(f"   ⚠️ 키워드 수 불일치: 실제 {len(keywords_data)}, 통계 {expected_keywords}")
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터 흐름 테스트 오류: {e}")
        return False

def generate_diagnosis_report():
    """진단 리포트 생성"""
    print("\n📋 대시보드 네비게이션 진단 리포트")
    print("=" * 50)
    
    # 1. 페이지 접근 테스트
    page_ok = test_admin_page_access()
    
    # 2. API 엔드포인트 테스트
    api_results = test_api_endpoints()
    
    # 3. 데이터 흐름 테스트
    data_flow_ok = test_dashboard_data_flow()
    
    # 종합 진단
    print("\n🔍 종합 진단 결과")
    print("=" * 50)
    
    if page_ok and all(r["status"] == "success" for r in api_results.values()) and data_flow_ok:
        print("✅ 모든 테스트 통과 - 대시보드가 정상적으로 작동해야 합니다.")
        print("\n💡 문제 해결 방법:")
        print("1. 브라우저 캐시를 완전히 삭제하세요 (Ctrl+Shift+Delete)")
        print("2. 하드 새로고침을 하세요 (Ctrl+F5 또는 Cmd+Shift+R)")
        print("3. 개발자 도구에서 'Disable cache'를 체크하세요")
        print("4. 브라우저를 완전히 종료하고 다시 시작하세요")
    else:
        print("❌ 일부 테스트 실패 - 문제가 발견되었습니다.")
        
        if not page_ok:
            print("   - 관리자 페이지 접근에 문제가 있습니다.")
        
        failed_apis = [k for k, v in api_results.items() if v["status"] != "success"]
        if failed_apis:
            print(f"   - 실패한 API: {', '.join(failed_apis)}")
        
        if not data_flow_ok:
            print("   - 데이터 흐름에 문제가 있습니다.")
        
        print("\n🔧 해결 방법:")
        print("1. 서버가 실행 중인지 확인하세요")
        print("2. API 엔드포인트가 정상 작동하는지 확인하세요")
        print("3. 데이터베이스 연결을 확인하세요")
        print("4. 서버 로그를 확인하세요")

def main():
    """메인 함수"""
    print("🚀 관리 대시보드 네비게이션 테스트")
    print("=" * 60)
    
    try:
        generate_diagnosis_report()
        
        print("\n✅ 테스트 완료!")
        print("\n💡 다음 단계:")
        print("브라우저에서 http://localhost:8000/admin 에 접속하여")
        print("'통계 대시보드' 메뉴를 클릭해보세요.")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    main() 