#!/usr/bin/env python3
"""
프론트엔드 API 호출 건수 표시 테스트 스크립트
"""

import requests
import json
import time

def test_api_usage_endpoint():
    """API 사용량 엔드포인트 테스트"""
    print("🔍 API 사용량 엔드포인트 테스트")
    print("=" * 50)
    
    try:
        # API 사용량 조회
        response = requests.get('http://localhost:8000/api/v1/stats/api-usage')
        if response.status_code == 200:
            data = response.json()
            print("✅ API 사용량 조회 성공")
            print(f"   OpenAI: {data.get('openai', 0)}회")
            print(f"   Gemini: {data.get('gemini', 0)}회")
            return data
        else:
            print(f"❌ API 사용량 조회 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ API 사용량 조회 오류: {e}")
        return None

def test_daily_stats_endpoint():
    """일일 통계 엔드포인트 테스트"""
    print("\n🔍 일일 통계 엔드포인트 테스트")
    print("=" * 50)
    
    try:
        # 일일 통계 조회
        response = requests.get('http://localhost:8000/api/v1/stats/daily')
        if response.status_code == 200:
            data = response.json()
            print("✅ 일일 통계 조회 성공")
            print(f"   OpenAI: {data.get('openai', 0)}회")
            print(f"   Gemini: {data.get('gemini', 0)}회")
            return data
        else:
            print(f"❌ 일일 통계 조회 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 일일 통계 조회 오류: {e}")
        return None

def test_keywords_summary_endpoint():
    """키워드 요약 엔드포인트 테스트"""
    print("\n🔍 키워드 요약 엔드포인트 테스트")
    print("=" * 50)
    
    try:
        # 키워드 요약 조회
        response = requests.get('http://localhost:8000/api/v1/stats/keywords-summary')
        if response.status_code == 200:
            data = response.json()
            print("✅ 키워드 요약 조회 성공")
            print(f"   총 키워드: {data.get('total_keywords', 0)}개")
            print(f"   상위 키워드: {data.get('top_keywords', '없음')}")
            return data
        else:
            print(f"❌ 키워드 요약 조회 실패: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 키워드 요약 조회 오류: {e}")
        return None

def test_frontend_page():
    """프론트엔드 페이지 접근 테스트"""
    print("\n🔍 프론트엔드 페이지 접근 테스트")
    print("=" * 50)
    
    try:
        # 메인 페이지 접근
        response = requests.get('http://localhost:8000/')
        if response.status_code == 200:
            print("✅ 메인 페이지 접근 성공")
            
            # API 호출 건수 관련 HTML 요소 확인
            content = response.text
            if 'openai-count' in content:
                print("✅ OpenAI 카운트 요소 발견")
            else:
                print("❌ OpenAI 카운트 요소 없음")
                
            if 'gemini-count' in content:
                print("✅ Gemini 카운트 요소 발견")
            else:
                print("❌ Gemini 카운트 요소 없음")
                
            if 'updateApiUsageCounts' in content:
                print("✅ API 사용량 업데이트 함수 발견")
            else:
                print("❌ API 사용량 업데이트 함수 없음")
                
            return True
        else:
            print(f"❌ 메인 페이지 접근 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 메인 페이지 접근 오류: {e}")
        return False

def simulate_api_call():
    """API 호출 시뮬레이션"""
    print("\n🔍 API 호출 시뮬레이션")
    print("=" * 50)
    
    try:
        # 간단한 블로그 포스트 생성 요청
        test_data = {
            "text": "인공지능의 미래에 대한 간단한 테스트입니다.",
            "rules": [],
            "ai_mode": "informative",
            "content_length": "500",
            "policy_auto": True
        }
        
        print("📝 블로그 포스트 생성 요청 중...")
        response = requests.post(
            'http://localhost:8000/api/v1/generate-post',
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ 블로그 포스트 생성 성공")
            data = response.json()
            print(f"   생성된 콘텐츠 길이: {len(data.get('post', ''))}자")
            print(f"   키워드: {data.get('keywords', '없음')}")
            
            # API 사용량 재확인
            time.sleep(2)
            usage_response = requests.get('http://localhost:8000/api/v1/stats/api-usage')
            if usage_response.status_code == 200:
                usage_data = usage_response.json()
                print(f"   업데이트된 OpenAI 호출: {usage_data.get('openai', 0)}회")
                print(f"   업데이트된 Gemini 호출: {usage_data.get('gemini', 0)}회")
            
            return True
        else:
            print(f"❌ 블로그 포스트 생성 실패: {response.status_code}")
            print(f"   오류: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 블로그 포스트 생성 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("프론트엔드 API 호출 건수 표시 테스트")
    print("=" * 60)
    
    # 1. API 엔드포인트 테스트
    api_usage = test_api_usage_endpoint()
    daily_stats = test_daily_stats_endpoint()
    keywords_summary = test_keywords_summary_endpoint()
    
    # 2. 프론트엔드 페이지 테스트
    frontend_ok = test_frontend_page()
    
    # 3. API 호출 시뮬레이션
    api_call_ok = simulate_api_call()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    if api_usage and daily_stats and keywords_summary and frontend_ok:
        print("✅ 모든 백엔드 엔드포인트가 정상 작동합니다.")
    else:
        print("❌ 일부 백엔드 엔드포인트에 문제가 있습니다.")
    
    if frontend_ok:
        print("✅ 프론트엔드 페이지가 정상적으로 로드됩니다.")
    else:
        print("❌ 프론트엔드 페이지에 문제가 있습니다.")
    
    if api_call_ok:
        print("✅ API 호출이 정상적으로 작동합니다.")
    else:
        print("❌ API 호출에 문제가 있습니다.")
    
    print("\n💡 권장사항:")
    print("1. 브라우저에서 http://localhost:8000 접속")
    print("2. 개발자 도구(F12)에서 Console 탭 확인")
    print("3. Network 탭에서 API 호출 상태 확인")
    print("4. API 호출 건수가 실시간으로 업데이트되는지 확인")

if __name__ == "__main__":
    main() 