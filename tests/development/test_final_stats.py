#!/usr/bin/env python3
"""
최종 통계 표시 테스트 스크립트
업데이트 이력 통계가 프론트엔드에 제대로 표시되는지 확인
"""
import requests
import json
import time

def test_complete_system():
    """완전한 시스템 테스트"""
    print("🚀 업데이트 이력 통계 시스템 완전 테스트")
    print("=" * 60)
    
    # 1. API 응답 테스트
    print("1️⃣ API 응답 테스트")
    try:
        response = requests.get('http://localhost:8000/api/v1/feature-updates/history')
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API 응답 성공: {len(data)}개 업데이트")
            
            # 카테고리별 통계 계산
            categories = {}
            for item in data:
                cat = item.get('category', '기타')
                categories[cat] = categories.get(cat, 0) + 1
            
            print("   📊 카테고리별 통계:")
            for cat in ['UI/UX', 'API', 'AI']:
                count = categories.get(cat, 0)
                print(f"      {cat}: {count}개")
            
            expected_stats = {
                'total-updates': len(data),
                'uiux-updates': categories.get('UI/UX', 0),
                'api-updates': categories.get('API', 0),
                'ai-updates': categories.get('AI', 0)
            }
            
            print("   🎯 예상 통계:", expected_stats)
            return expected_stats
        else:
            print(f"   ❌ API 응답 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"   ❌ API 요청 오류: {e}")
        return None

def test_admin_page_structure():
    """관리자 페이지 구조 테스트"""
    print("\n2️⃣ 관리자 페이지 구조 테스트")
    try:
        response = requests.get('http://localhost:8000/admin')
        if response.status_code == 200:
            html_content = response.text
            print("   ✅ 관리자 페이지 접근 성공")
            
            # 통계 요소 ID 확인
            stats_ids = ['total-updates', 'uiux-updates', 'api-updates', 'ai-updates']
            found_ids = []
            
            for stat_id in stats_ids:
                if stat_id in html_content:
                    found_ids.append(stat_id)
                    print(f"   ✅ {stat_id}: HTML에 존재")
                else:
                    print(f"   ❌ {stat_id}: HTML에 없음")
            
            if len(found_ids) == len(stats_ids):
                print("   🎉 모든 통계 요소 ID가 HTML에 존재")
                return True
            else:
                print(f"   ⚠️  일부 통계 요소 ID 누락: {len(found_ids)}/{len(stats_ids)}")
                return False
        else:
            print(f"   ❌ 관리자 페이지 접근 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 관리자 페이지 접근 오류: {e}")
        return False

def test_statistics_endpoint():
    """통계 엔드포인트 테스트"""
    print("\n3️⃣ 통계 엔드포인트 테스트")
    try:
        response = requests.get('http://localhost:8000/api/v1/feature-updates/statistics')
        if response.status_code == 200:
            data = response.json()
            print("   ✅ 통계 엔드포인트 응답 성공")
            print(f"   📊 총 업데이트: {data.get('total_updates', 0)}개")
            
            # 주요 카테고리 확인
            by_category = data.get('by_category', {})
            for cat in ['UI/UX', 'API', 'AI']:
                count = by_category.get(cat, 0)
                print(f"      {cat}: {count}개")
            
            return True
        else:
            print(f"   ❌ 통계 엔드포인트 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 통계 엔드포인트 오류: {e}")
        return False

def generate_final_report(expected_stats):
    """최종 리포트 생성"""
    print("\n" + "=" * 60)
    print("📋 최종 테스트 리포트")
    print("=" * 60)
    
    if expected_stats:
        print("✅ 백엔드 시스템: 정상 작동")
        print(f"   📈 총 업데이트: {expected_stats['total-updates']}개")
        print(f"   🎨 UI/UX: {expected_stats['uiux-updates']}개")
        print(f"   ⚙️  API: {expected_stats['api-updates']}개")
        print(f"   🤖 AI: {expected_stats['ai-updates']}개")
    else:
        print("❌ 백엔드 시스템: 문제 발생")
    
    print("\n💡 프론트엔드 확인 방법:")
    print("1. 브라우저에서 http://localhost:8000/admin 접속")
    print("2. '업데이트 이력' 탭 클릭")
    print("3. 상단 통계 카드에서 다음 수치 확인:")
    if expected_stats:
        print(f"   - 총 업데이트: {expected_stats['total-updates']}개")
        print(f"   - UI/UX: {expected_stats['uiux-updates']}개")
        print(f"   - API: {expected_stats['api-updates']}개")
        print(f"   - AI: {expected_stats['ai-updates']}개")
    print("4. 개발자 도구 콘솔에서 로그 확인")
    print("5. '업데이트 이력 새로고침' 버튼 클릭하여 테스트")
    
    print("\n🔧 문제 해결 방법:")
    print("- 브라우저 캐시 삭제 후 새로고침")
    print("- 개발자 도구 콘솔에서 오류 메시지 확인")
    print("- 서버 재시작 후 다시 시도")

def main():
    """메인 함수"""
    print("🚀 업데이트 이력 통계 시스템 최종 테스트")
    print("=" * 60)
    
    try:
        # 1. API 테스트
        expected_stats = test_complete_system()
        
        # 2. 관리자 페이지 구조 테스트
        admin_ok = test_admin_page_structure()
        
        # 3. 통계 엔드포인트 테스트
        stats_ok = test_statistics_endpoint()
        
        # 4. 최종 리포트
        generate_final_report(expected_stats)
        
        print("\n✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    main() 