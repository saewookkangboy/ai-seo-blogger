#!/usr/bin/env python3
"""
통계 표시 문제 테스트 스크립트
업데이트 이력 통계가 프론트엔드에 제대로 표시되는지 확인
"""
import requests
import json
import time

def test_api_response():
    """API 응답 테스트"""
    print("=== API 응답 테스트 ===")
    
    try:
        response = requests.get('http://localhost:8000/api/v1/feature-updates/history')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API 응답 성공: {len(data)}개 업데이트")
            
            # 카테고리별 통계 계산
            categories = {}
            for item in data:
                cat = item.get('category', '기타')
                categories[cat] = categories.get(cat, 0) + 1
            
            print("\n카테고리별 통계:")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"  {cat}: {count}개")
            
            return data
        else:
            print(f"❌ API 응답 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ API 요청 오류: {e}")
        return None

def test_statistics_endpoint():
    """통계 엔드포인트 테스트"""
    print("\n=== 통계 엔드포인트 테스트 ===")
    
    try:
        response = requests.get('http://localhost:8000/api/v1/feature-updates/statistics')
        if response.status_code == 200:
            data = response.json()
            print("✅ 통계 엔드포인트 응답 성공")
            
            print(f"총 업데이트: {data.get('total_updates', 0)}개")
            print("\n카테고리별 통계:")
            for cat, count in data.get('by_category', {}).items():
                print(f"  {cat}: {count}개")
            
            return data
        else:
            print(f"❌ 통계 엔드포인트 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 통계 엔드포인트 오류: {e}")
        return None

def test_admin_page():
    """관리자 페이지 접근 테스트"""
    print("\n=== 관리자 페이지 접근 테스트 ===")
    
    try:
        response = requests.get('http://localhost:8000/admin')
        if response.status_code == 200:
            print("✅ 관리자 페이지 접근 성공")
            
            # HTML에서 통계 요소 ID 확인
            html_content = response.text
            stats_ids = ['total-updates', 'uiux-updates', 'api-updates', 'ai-updates']
            
            print("\n통계 요소 ID 확인:")
            for stat_id in stats_ids:
                if stat_id in html_content:
                    print(f"  ✅ {stat_id}: HTML에 존재")
                else:
                    print(f"  ❌ {stat_id}: HTML에 없음")
            
            return True
        else:
            print(f"❌ 관리자 페이지 접근 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 관리자 페이지 접근 오류: {e}")
        return False

def generate_test_report():
    """테스트 리포트 생성"""
    print("\n=== 테스트 리포트 ===")
    
    # 1. API 응답 테스트
    api_data = test_api_response()
    
    # 2. 통계 엔드포인트 테스트
    stats_data = test_statistics_endpoint()
    
    # 3. 관리자 페이지 테스트
    admin_accessible = test_admin_page()
    
    # 4. 종합 리포트
    print("\n=== 종합 리포트 ===")
    
    if api_data and len(api_data) > 0:
        print("✅ 백엔드 API: 정상 작동")
        print(f"   - 총 업데이트: {len(api_data)}개")
        
        # 주요 카테고리 확인
        categories = {}
        for item in api_data:
            cat = item.get('category', '기타')
            categories[cat] = categories.get(cat, 0) + 1
        
        print("   - 주요 카테고리:")
        for cat in ['UI/UX', 'API', 'AI']:
            count = categories.get(cat, 0)
            print(f"     {cat}: {count}개")
    else:
        print("❌ 백엔드 API: 문제 발생")
    
    if stats_data:
        print("✅ 통계 엔드포인트: 정상 작동")
    else:
        print("❌ 통계 엔드포인트: 문제 발생")
    
    if admin_accessible:
        print("✅ 관리자 페이지: 접근 가능")
    else:
        print("❌ 관리자 페이지: 접근 불가")
    
    print("\n💡 다음 단계:")
    print("1. 브라우저에서 http://localhost:8000/admin 접속")
    print("2. '업데이트 이력' 탭 클릭")
    print("3. 통계 카드에서 수치 확인")
    print("4. 개발자 도구 콘솔에서 오류 메시지 확인")

def main():
    """메인 함수"""
    print("🚀 통계 표시 문제 테스트 시작")
    print("=" * 50)
    
    try:
        generate_test_report()
        print("\n✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    main() 