#!/usr/bin/env python3
"""
AI SEO Blogger 종합 성능 테스트 스크립트
"""

import requests
import time
import json
import concurrent.futures
from datetime import datetime
import statistics

def test_endpoint(url, method="GET", timeout=10, name=None):
    """단일 엔드포인트 테스트"""
    start_time = time.time()
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, timeout=timeout)
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        return {
            "name": name or url,
            "url": url,
            "method": method,
            "status_code": response.status_code,
            "response_time_ms": round(response_time, 2),
            "success": response.status_code == 200,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        return {
            "name": name or url,
            "url": url,
            "method": method,
            "status_code": None,
            "response_time_ms": round(response_time, 2),
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def load_test_endpoint(url, method="GET", num_requests=10, concurrent_requests=5, timeout=10, name=None):
    """부하 테스트"""
    print(f"🔥 {name or url} 부하 테스트 ({num_requests} 요청, {concurrent_requests} 동시)")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        futures = []
        for i in range(num_requests):
            future = executor.submit(test_endpoint, url, method, timeout, f"{name or url} #{i+1}")
            futures.append(future)
        
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    return results

def comprehensive_performance_test():
    """종합 성능 테스트"""
    base_url = "http://localhost:8000"
    
    print("🚀 AI SEO Blogger 종합 성능 테스트 시작")
    print("=" * 60)
    
    # 기본 엔드포인트 테스트
    basic_endpoints = [
        {"url": f"{base_url}/health", "name": "헬스체크"},
        {"url": f"{base_url}/", "name": "메인 페이지"},
        {"url": f"{base_url}/docs", "name": "API 문서"},
        {"url": f"{base_url}/admin", "name": "관리자 페이지"},
        {"url": f"{base_url}/api/v1/admin/test-integration", "name": "통합 테스트"},
        {"url": f"{base_url}/api/v1/admin/posts/stats", "name": "포스트 통계"},
        {"url": f"{base_url}/admin/session-status", "name": "세션 상태"},
        {"url": f"{base_url}/admin/test-session", "name": "테스트 세션"},
    ]
    
    print("📊 기본 엔드포인트 테스트 중...")
    basic_results = []
    for endpoint in basic_endpoints:
        result = test_endpoint(endpoint["url"], name=endpoint["name"])
        basic_results.append(result)
        
        status_icon = "✅" if result['success'] else "❌"
        print(f"   {status_icon} {result['name']}: {result['response_time_ms']:.2f}ms")
        time.sleep(0.2)
    
    # 부하 테스트
    print("\n🔥 부하 테스트 중...")
    load_test_endpoints = [
        {"url": f"{base_url}/health", "name": "헬스체크 부하테스트"},
        {"url": f"{base_url}/admin/session-status", "name": "세션 상태 부하테스트"},
    ]
    
    load_results = []
    for endpoint in load_test_endpoints:
        results = load_test_endpoint(
            endpoint["url"], 
            num_requests=20, 
            concurrent_requests=5, 
            name=endpoint["name"]
        )
        load_results.extend(results)
        
        # 부하 테스트 결과 분석
        successful_results = [r for r in results if r['success']]
        if successful_results:
            response_times = [r['response_time_ms'] for r in successful_results]
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
            
            print(f"   📊 {endpoint['name']}:")
            print(f"      평균: {avg_time:.2f}ms, 최소: {min_time:.2f}ms, 최대: {max_time:.2f}ms")
            print(f"      표준편차: {std_dev:.2f}ms, 성공률: {len(successful_results)}/{len(results)}")
    
    # 데이터베이스 성능 테스트
    print("\n🗄️ 데이터베이스 성능 테스트 중...")
    db_endpoints = [
        {"url": f"{base_url}/api/v1/admin/posts/stats", "name": "포스트 통계"},
        {"url": f"{base_url}/api/v1/admin/keywords", "name": "키워드 목록"},
    ]
    
    db_results = []
    for endpoint in db_endpoints:
        # 여러 번 테스트하여 평균 계산
        times = []
        for i in range(5):
            result = test_endpoint(endpoint["url"], name=f"{endpoint['name']} #{i+1}")
            if result['success']:
                times.append(result['response_time_ms'])
            time.sleep(0.5)
        
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            
            db_result = {
                "name": endpoint["name"],
                "avg_response_time_ms": round(avg_time, 2),
                "min_response_time_ms": round(min_time, 2),
                "max_response_time_ms": round(max_time, 2),
                "test_count": len(times)
            }
            db_results.append(db_result)
            
            print(f"   📊 {endpoint['name']}: 평균 {avg_time:.2f}ms (최소: {min_time:.2f}ms, 최대: {max_time:.2f}ms)")
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📈 종합 성능 테스트 결과 요약")
    print("=" * 60)
    
    all_results = basic_results + load_results
    
    successful_tests = [r for r in all_results if r['success']]
    failed_tests = [r for r in all_results if not r['success']]
    
    if successful_tests:
        response_times = [r['response_time_ms'] for r in successful_tests]
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        median_response_time = statistics.median(response_times)
        std_dev_response_time = statistics.stdev(response_times) if len(response_times) > 1 else 0
        
        print(f"✅ 성공한 테스트: {len(successful_tests)}/{len(all_results)} ({len(successful_tests)/len(all_results)*100:.1f}%)")
        print(f"📊 평균 응답 시간: {avg_response_time:.2f}ms")
        print(f"📊 중간값 응답 시간: {median_response_time:.2f}ms")
        print(f"⚡ 최소 응답 시간: {min_response_time:.2f}ms")
        print(f"🐌 최대 응답 시간: {max_response_time:.2f}ms")
        print(f"📊 표준편차: {std_dev_response_time:.2f}ms")
        
        # 성능 등급 평가
        if avg_response_time < 50:
            performance_grade = "🟢 우수"
        elif avg_response_time < 100:
            performance_grade = "🟡 양호"
        elif avg_response_time < 200:
            performance_grade = "🟠 보통"
        else:
            performance_grade = "🔴 개선 필요"
        
        print(f"🏆 성능 등급: {performance_grade}")
    
    if failed_tests:
        print(f"❌ 실패한 테스트: {len(failed_tests)}/{len(all_results)}")
        for test in failed_tests[:5]:  # 처음 5개만 표시
            print(f"   - {test['name']}: {test.get('error', f'HTTP {test.get('status_code', 'Unknown')}')}")
        if len(failed_tests) > 5:
            print(f"   ... 및 {len(failed_tests) - 5}개 더")
    
    # 상세 결과를 JSON 파일로 저장
    comprehensive_results = {
        "test_timestamp": datetime.now().isoformat(),
        "test_summary": {
            "total_tests": len(all_results),
            "successful_tests": len(successful_tests),
            "failed_tests": len(failed_tests),
            "success_rate": len(successful_tests)/len(all_results)*100 if all_results else 0
        },
        "performance_metrics": {
            "avg_response_time_ms": round(statistics.mean([r['response_time_ms'] for r in successful_tests]), 2) if successful_tests else 0,
            "min_response_time_ms": min([r['response_time_ms'] for r in successful_tests]) if successful_tests else 0,
            "max_response_time_ms": max([r['response_time_ms'] for r in successful_tests]) if successful_tests else 0,
            "median_response_time_ms": round(statistics.median([r['response_time_ms'] for r in successful_tests]), 2) if successful_tests else 0,
            "std_dev_response_time_ms": round(statistics.stdev([r['response_time_ms'] for r in successful_tests]), 2) if len(successful_tests) > 1 else 0
        },
        "database_performance": db_results,
        "detailed_results": all_results
    }
    
    with open('comprehensive_performance_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(comprehensive_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 상세 결과가 'comprehensive_performance_test_results.json'에 저장되었습니다.")
    
    return comprehensive_results

if __name__ == "__main__":
    comprehensive_performance_test()
