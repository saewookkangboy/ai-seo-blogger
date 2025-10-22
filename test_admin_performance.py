#!/usr/bin/env python3
"""
Admin 페이지 성능 테스트 스크립트
"""

import requests
import time
import json
from datetime import datetime

def test_admin_performance():
    """Admin 페이지 성능 테스트"""
    base_url = "http://localhost:8000"
    
    print("🚀 Admin 페이지 성능 테스트 시작")
    print("=" * 50)
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "통합 테스트",
            "url": f"{base_url}/api/v1/admin/test-integration",
            "method": "GET"
        },
        {
            "name": "포스트 통계",
            "url": f"{base_url}/api/v1/admin/posts/stats",
            "method": "GET"
        },
        {
            "name": "세션 상태",
            "url": f"{base_url}/admin/session-status",
            "method": "GET"
        },
        {
            "name": "테스트 세션 생성",
            "url": f"{base_url}/admin/test-session",
            "method": "GET"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"📊 {test_case['name']} 테스트 중...")
        
        start_time = time.time()
        try:
            response = requests.get(test_case['url'], timeout=10)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # ms로 변환
            
            result = {
                "name": test_case['name'],
                "status_code": response.status_code,
                "response_time_ms": round(response_time, 2),
                "success": response.status_code == 200,
                "timestamp": datetime.now().isoformat()
            }
            
            if response.status_code == 200:
                print(f"   ✅ 성공 - {response_time:.2f}ms")
            else:
                print(f"   ❌ 실패 - HTTP {response.status_code}")
                
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            result = {
                "name": test_case['name'],
                "status_code": None,
                "response_time_ms": round(response_time, 2),
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"   ❌ 오류 - {e}")
        
        results.append(result)
        time.sleep(0.5)  # 요청 간 간격
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📈 성능 테스트 결과 요약")
    print("=" * 50)
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    if successful_tests:
        avg_response_time = sum(r['response_time_ms'] for r in successful_tests) / len(successful_tests)
        min_response_time = min(r['response_time_ms'] for r in successful_tests)
        max_response_time = max(r['response_time_ms'] for r in successful_tests)
        
        print(f"✅ 성공한 테스트: {len(successful_tests)}/{len(results)}")
        print(f"📊 평균 응답 시간: {avg_response_time:.2f}ms")
        print(f"⚡ 최소 응답 시간: {min_response_time:.2f}ms")
        print(f"🐌 최대 응답 시간: {max_response_time:.2f}ms")
    
    if failed_tests:
        print(f"❌ 실패한 테스트: {len(failed_tests)}/{len(results)}")
        for test in failed_tests:
            print(f"   - {test['name']}: {test.get('error', f'HTTP {test.get('status_code', 'Unknown')}')}")
    
    # 상세 결과
    print("\n📋 상세 결과:")
    for result in results:
        status_icon = "✅" if result['success'] else "❌"
        print(f"   {status_icon} {result['name']}: {result['response_time_ms']:.2f}ms")
    
    # 결과를 JSON 파일로 저장
    with open('admin_performance_test_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            "test_timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "successful_tests": len(successful_tests),
            "failed_tests": len(failed_tests),
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 결과가 'admin_performance_test_results.json'에 저장되었습니다.")
    
    return results

if __name__ == "__main__":
    test_admin_performance()
