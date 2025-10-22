#!/usr/bin/env python3
"""
최종 통계 표시 테스트 스크립트
업데이트 이력 통계가 프론트엔드에 제대로 표시되는지 확인
"""
import requests
import json
import time

def test_api_data():
    """API 데이터 테스트"""
    print("🚀 API 데이터 테스트")
    print("=" * 50)
    
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
            
            print("\n📊 카테고리별 통계:")
            for cat in ['UI/UX', 'API', 'AI']:
                count = categories.get(cat, 0)
                print(f"   {cat}: {count}개")
            
            expected_stats = {
                'total-updates': len(data),
                'uiux-updates': categories.get('UI/UX', 0),
                'api-updates': categories.get('API', 0),
                'ai-updates': categories.get('AI', 0)
            }
            
            print(f"\n🎯 예상 통계: {expected_stats}")
            return expected_stats
        else:
            print(f"❌ API 응답 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ API 요청 오류: {e}")
        return None

def test_admin_page():
    """관리자 페이지 테스트"""
    print("\n🌐 관리자 페이지 테스트")
    print("=" * 50)
    
    try:
        response = requests.get('http://localhost:8000/admin')
        if response.status_code == 200:
            html_content = response.text
            print("✅ 관리자 페이지 접근 성공")
            
            # 통계 요소 ID 확인
            stats_ids = ['total-updates', 'uiux-updates', 'api-updates', 'ai-updates']
            found_count = 0
            
            for stat_id in stats_ids:
                if stat_id in html_content:
                    found_count += 1
                    print(f"   ✅ {stat_id}: HTML에 존재")
                else:
                    print(f"   ❌ {stat_id}: HTML에 없음")
            
            print(f"\n📈 통계 요소 발견: {found_count}/{len(stats_ids)}")
            
            if found_count == len(stats_ids):
                print("🎉 모든 통계 요소가 HTML에 존재합니다!")
                return True
            else:
                print("⚠️  일부 통계 요소가 누락되었습니다.")
                return False
        else:
            print(f"❌ 관리자 페이지 접근 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 관리자 페이지 접근 오류: {e}")
        return False

def generate_instructions(expected_stats):
    """사용자 지침 생성"""
    print("\n📋 사용자 지침")
    print("=" * 50)
    
    if expected_stats:
        print("✅ 백엔드 시스템이 정상 작동하고 있습니다.")
        print(f"📊 예상 통계:")
        print(f"   - 총 업데이트: {expected_stats['total-updates']}개")
        print(f"   - UI/UX: {expected_stats['uiux-updates']}개")
        print(f"   - API: {expected_stats['api-updates']}개")
        print(f"   - AI: {expected_stats['ai-updates']}개")
    
    print("\n🔍 프론트엔드 확인 방법:")
    print("1. 브라우저에서 http://localhost:8000/admin 접속")
    print("2. 관리자 로그인 (비밀번호: 0000)")
    print("3. '업데이트 이력' 탭 클릭")
    print("4. 상단 통계 카드에서 수치 확인")
    print("5. 개발자 도구 콘솔 열기 (F12)")
    print("6. 콘솔에서 다음 로그 확인:")
    print("   - '=== forceUpdateStats 함수 시작 ==='")
    print("   - '계산된 통계: { total: 699, uiux: 72, api: 171, ai: 63 }'")
    print("   - '✅ 강제 업데이트: total-updates \"-\" → \"699\"'")
    
    print("\n🔧 문제 해결 방법:")
    print("- 브라우저 캐시 완전 삭제 (Ctrl+Shift+Delete)")
    print("- 하드 새로고침 (Ctrl+F5 또는 Cmd+Shift+R)")
    print("- 개발자 도구에서 'Disable cache' 체크")
    print("- '업데이트 이력 새로고침' 버튼 클릭")
    print("- 서버 재시작 후 다시 시도")

def main():
    """메인 함수"""
    print("🚀 업데이트 이력 통계 시스템 최종 테스트")
    print("=" * 60)
    
    try:
        # 1. API 데이터 테스트
        expected_stats = test_api_data()
        
        # 2. 관리자 페이지 테스트
        admin_ok = test_admin_page()
        
        # 3. 사용자 지침 생성
        generate_instructions(expected_stats)
        
        print("\n✅ 모든 테스트 완료!")
        print("\n💡 다음 단계:")
        print("브라우저에서 관리자 페이지에 접속하여 '업데이트 이력' 탭을 확인해주세요.")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    main() 