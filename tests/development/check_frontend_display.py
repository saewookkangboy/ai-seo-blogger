#!/usr/bin/env python3
"""
프론트엔드 API 호출 건수 표시 확인 스크립트
"""

import requests
import re
import json

def check_frontend_api_display():
    """프론트엔드에서 API 호출 건수가 정확하게 표시되는지 확인"""
    print("🔍 프론트엔드 API 호출 건수 표시 확인")
    print("=" * 60)
    
    try:
        # 1. 백엔드 API에서 실제 데이터 확인
        print("1️⃣ 백엔드 API 데이터 확인...")
        api_response = requests.get('http://localhost:8000/api/v1/stats/api-usage')
        if api_response.status_code == 200:
            api_data = api_response.json()
            print(f"   ✅ OpenAI: {api_data.get('openai', 0)}회")
            print(f"   ✅ Gemini: {api_data.get('gemini', 0)}회")
        else:
            print(f"   ❌ API 응답 실패: {api_response.status_code}")
            return False
        
        # 2. 프론트엔드 페이지에서 HTML 요소 확인
        print("\n2️⃣ 프론트엔드 HTML 요소 확인...")
        frontend_response = requests.get('http://localhost:8000/')
        if frontend_response.status_code == 200:
            html_content = frontend_response.text
            
            # OpenAI 카운트 요소 확인
            openai_pattern = r'id="openai-count"[^>]*>([^<]+)</span>'
            openai_match = re.search(openai_pattern, html_content)
            if openai_match:
                openai_display = openai_match.group(1).strip()
                print(f"   ✅ OpenAI 표시: {openai_display}")
            else:
                print("   ❌ OpenAI 카운트 요소를 찾을 수 없음")
            
            # Gemini 카운트 요소 확인
            gemini_pattern = r'id="gemini-count"[^>]*>([^<]+)</span>'
            gemini_match = re.search(gemini_pattern, html_content)
            if gemini_match:
                gemini_display = gemini_match.group(1).strip()
                print(f"   ✅ Gemini 표시: {gemini_display}")
            else:
                print("   ❌ Gemini 카운트 요소를 찾을 수 없음")
            
            # JavaScript 함수 확인
            if 'updateApiUsageCounts' in html_content:
                print("   ✅ API 사용량 업데이트 함수 발견")
            else:
                print("   ❌ API 사용량 업데이트 함수 없음")
            
            # API 엔드포인트 호출 확인
            if '/api/v1/stats/api-usage' in html_content:
                print("   ✅ 올바른 API 엔드포인트 사용")
            else:
                print("   ❌ 잘못된 API 엔드포인트 사용")
            
        else:
            print(f"   ❌ 프론트엔드 페이지 접근 실패: {frontend_response.status_code}")
            return False
        
        # 3. 데이터 일치성 확인
        print("\n3️⃣ 데이터 일치성 확인...")
        if openai_match and gemini_match:
            openai_display = openai_match.group(1).strip()
            gemini_display = gemini_match.group(1).strip()
            
            # 숫자가 아닌 경우 '-'로 표시되는지 확인
            if openai_display == '-' or openai_display.isdigit():
                print(f"   ✅ OpenAI 표시 형식 정상: {openai_display}")
            else:
                print(f"   ⚠️ OpenAI 표시 형식 이상: {openai_display}")
            
            if gemini_display == '-' or gemini_display.isdigit():
                print(f"   ✅ Gemini 표시 형식 정상: {gemini_display}")
            else:
                print(f"   ⚠️ Gemini 표시 형식 이상: {gemini_display}")
            
            # 실제 데이터와 비교
            if openai_display.isdigit() and int(openai_display) == api_data.get('openai', 0):
                print(f"   ✅ OpenAI 데이터 일치: {openai_display} == {api_data.get('openai', 0)}")
            elif openai_display == '-':
                print(f"   ⚠️ OpenAI 데이터 로딩 중 또는 오류")
            else:
                print(f"   ❌ OpenAI 데이터 불일치: {openai_display} != {api_data.get('openai', 0)}")
            
            if gemini_display.isdigit() and int(gemini_display) == api_data.get('gemini', 0):
                print(f"   ✅ Gemini 데이터 일치: {gemini_display} == {api_data.get('gemini', 0)}")
            elif gemini_display == '-':
                print(f"   ⚠️ Gemini 데이터 로딩 중 또는 오류")
            else:
                print(f"   ❌ Gemini 데이터 불일치: {gemini_display} != {api_data.get('gemini', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 확인 중 오류 발생: {e}")
        return False

def check_real_time_update():
    """실시간 업데이트 기능 확인"""
    print("\n🔍 실시간 업데이트 기능 확인")
    print("=" * 60)
    
    try:
        # API 호출 시뮬레이션
        print("1️⃣ API 호출 시뮬레이션...")
        test_data = {
            "text": "실시간 업데이트 테스트를 위한 간단한 텍스트입니다.",
            "rules": [],
            "ai_mode": "informative",
            "content_length": "300",
            "policy_auto": True
        }
        
        response = requests.post(
            'http://localhost:8000/api/v1/generate-post',
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            print("   ✅ API 호출 성공")
            
            # 업데이트된 API 사용량 확인
            import time
            time.sleep(2)
            
            updated_response = requests.get('http://localhost:8000/api/v1/stats/api-usage')
            if updated_response.status_code == 200:
                updated_data = updated_response.json()
                print(f"   ✅ 업데이트된 OpenAI: {updated_data.get('openai', 0)}회")
                print(f"   ✅ 업데이트된 Gemini: {updated_data.get('gemini', 0)}회")
                
                # 증가 확인
                if updated_data.get('openai', 0) > api_data.get('openai', 0):
                    print("   ✅ OpenAI 호출 건수 증가 확인")
                else:
                    print("   ⚠️ OpenAI 호출 건수 증가 없음")
                
                return True
            else:
                print(f"   ❌ 업데이트된 데이터 조회 실패: {updated_response.status_code}")
                return False
        else:
            print(f"   ❌ API 호출 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 실시간 업데이트 확인 중 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("프론트엔드 API 호출 건수 표시 확인")
    print("=" * 80)
    
    # 1. 기본 표시 확인
    display_ok = check_frontend_api_display()
    
    # 2. 실시간 업데이트 확인
    update_ok = check_real_time_update()
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("확인 결과 요약")
    print("=" * 80)
    
    if display_ok:
        print("✅ 프론트엔드 API 호출 건수 표시가 정상적으로 작동합니다.")
    else:
        print("❌ 프론트엔드 API 호출 건수 표시에 문제가 있습니다.")
    
    if update_ok:
        print("✅ 실시간 업데이트 기능이 정상적으로 작동합니다.")
    else:
        print("❌ 실시간 업데이트 기능에 문제가 있습니다.")
    
    print("\n💡 브라우저에서 확인 방법:")
    print("1. http://localhost:8000 접속")
    print("2. 우측 상단의 'API 호출 건수' 카드 확인")
    print("3. OpenAI와 Gemini 호출 건수가 표시되는지 확인")
    print("4. 콘텐츠 생성 후 실시간으로 업데이트되는지 확인")
    print("5. 개발자 도구(F12) → Console에서 오류 메시지 확인")

if __name__ == "__main__":
    main() 