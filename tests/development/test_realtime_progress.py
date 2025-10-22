#!/usr/bin/env python3
"""
실시간 진행 상황 표시 기능 테스트 스크립트
"""

import requests
import json
import time
from datetime import datetime

def test_realtime_progress():
    """실시간 진행 상황 테스트"""
    print("🚀 실시간 진행 상황 테스트를 시작합니다...")
    
    # 테스트 데이터
    test_data = {
        "url": "https://www.searchengineland.com/google-core-update-may-2024-447456",
        "text": "",
        "rules": ["AI_SEO", "AI_SEARCH"],
        "ai_mode": "gemini_2_0_flash",
        "content_length": "3000",
        "policy_auto": False
    }
    
    print(f"📋 테스트 데이터: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    try:
        # 1. 시스템 상태 확인
        print("\n🔍 시스템 상태 확인 중...")
        response = requests.get('http://localhost:8000/api/v1/system-status', timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ 시스템 상태: {status_data.get('overall_status', '알 수 없음')}")
            print(f"   - CPU: {status_data.get('system', {}).get('cpu_usage', '알 수 없음')}")
            print(f"   - 메모리: {status_data.get('system', {}).get('memory_usage', '알 수 없음')}")
        else:
            print(f"❌ 시스템 상태 확인 실패: {response.status_code}")
            return
        
        # 2. 실시간 진행 상황 테스트
        print("\n⚡ 실시간 진행 상황 테스트 시작...")
        
        # EventSource 시뮬레이션 (실제로는 브라우저에서 테스트)
        print("📡 EventSource 연결 시뮬레이션...")
        
        # 일반 API 호출로 진행 상황 확인
        start_time = time.time()
        
        response = requests.post(
            'http://localhost:8000/api/v1/generate-post-gemini-2-flash',
            json=test_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✅ 테스트 완료! (소요시간: {duration:.2f}초)")
            print(f"   - 성공: {result.get('success', False)}")
            print(f"   - 메시지: {result.get('message', 'N/A')}")
            
            if result.get('success'):
                data = result.get('data', {})
                print(f"   - 제목: {data.get('title', 'N/A')}")
                print(f"   - 콘텐츠 길이: {len(data.get('content', ''))}자")
                print(f"   - 키워드: {data.get('keywords', 'N/A')}")
                print(f"   - AI 모드: {data.get('ai_mode', 'N/A')}")
                print(f"   - 단어 수: {data.get('word_count', 'N/A')}")
                
                # 성능 평가
                if duration < 10:
                    performance = "매우 빠름"
                elif duration < 20:
                    performance = "빠름"
                elif duration < 30:
                    performance = "보통"
                else:
                    performance = "느림"
                
                print(f"   - 성능 평가: {performance}")
                
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"   오류: {response.text}")
        
        # 3. 프론트엔드 테스트 안내
        print("\n🌐 프론트엔드 테스트 안내:")
        print("   1. 브라우저에서 http://localhost:8000 접속")
        print("   2. URL 또는 텍스트 입력")
        print("   3. AI 모드를 'Gemini 2.0 Flash'로 선택")
        print("   4. '콘텐츠 생성' 버튼 클릭")
        print("   5. 실시간 진행 상황 확인:")
        print("      - 단계별 아이콘 상태 변화")
        print("      - 진행률 바 애니메이션")
        print("      - 단계별 상세 정보 표시")
        print("      - 시스템 상태 실시간 업데이트")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

def test_progress_endpoints():
    """진행 상황 관련 엔드포인트 테스트"""
    print("\n🔧 진행 상황 엔드포인트 테스트...")
    
    endpoints = [
        '/api/v1/system-status',
        '/api/v1/performance/status',
        '/api/v1/stats/api-usage'
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://localhost:8000{endpoint}', timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint}: 정상")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: 오류 - {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("실시간 진행 상황 표시 기능 테스트")
    print("=" * 60)
    
    test_progress_endpoints()
    test_realtime_progress()
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60) 