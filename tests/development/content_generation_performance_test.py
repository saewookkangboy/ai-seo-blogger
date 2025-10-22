#!/usr/bin/env python3
"""
콘텐츠 생성 성능 종합 테스트
- API 응답 시간 측정
- 각 단계별 처리 시간 분석
- 병목 지점 식별
- 시스템 리소스 모니터링
"""

import asyncio
import time
import psutil
import requests
import json
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_system_info() -> Dict[str, Any]:
    """시스템 정보 수집"""
    return {
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "memory_available": psutil.virtual_memory().available,
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent
    }

def test_api_endpoints() -> Dict[str, Any]:
    """API 엔드포인트 응답 시간 테스트"""
    base_url = "http://localhost:8017"
    endpoints = {
        "stats": "/api/v1/stats/api-usage",
        "keywords": "/api/v1/stats/keywords-summary",
        "posts": "/api/v1/posts",
        "news": "/api/v1/news"
    }
    
    results = {}
    
    for name, endpoint in endpoints.items():
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            end_time = time.time()
            
            results[name] = {
                "status_code": response.status_code,
                "response_time": round((end_time - start_time) * 1000, 2),  # ms
                "success": response.status_code == 200
            }
        except Exception as e:
            results[name] = {
                "status_code": None,
                "response_time": None,
                "success": False,
                "error": str(e)
            }
    
    return results

def test_content_generation_performance() -> Dict[str, Any]:
    """콘텐츠 생성 성능 테스트"""
    base_url = "http://localhost:8017"
    
    # 테스트용 간단한 요청 데이터
    test_data = {
        "url": "https://example.com",
        "ai_mode": "",
        "content_length": "1000",
        "rules": ["SEO", "AEO"],
        "policy_auto": True
    }
    
    results = {
        "total_time": 0,
        "steps": {},
        "success": False,
        "error": None
    }
    
    try:
        print("🔄 콘텐츠 생성 테스트 시작...")
        
        # 전체 시작 시간
        total_start = time.time()
        
        # 1. 요청 전송
        step_start = time.time()
        response = requests.post(
            f"{base_url}/api/v1/generate-post",  # 올바른 엔드포인트
            json=test_data,
            timeout=120  # 2분 타임아웃
        )
        step_end = time.time()
        
        results["steps"]["request_send"] = {
            "time": round((step_end - step_start) * 1000, 2),
            "status_code": response.status_code
        }
        
        if response.status_code == 200:
            # 2. 응답 처리
            step_start = time.time()
            response_data = response.json()
            step_end = time.time()
            
            results["steps"]["response_processing"] = {
                "time": round((step_end - step_start) * 1000, 2),
                "data_size": len(str(response_data))
            }
            
            # 3. 전체 시간 계산
            total_end = time.time()
            results["total_time"] = round((total_end - total_start) * 1000, 2)
            results["success"] = True
            
            # 4. 응답 데이터 분석
            if "post" in response_data:
                post = response_data["post"]
                results["content_info"] = {
                    "word_count": len(post.get("content", "").split()),
                    "has_seo_analysis": "seo_analysis" in response_data,
                    "has_keywords": "keywords" in response_data
                }
        
        else:
            results["error"] = f"HTTP {response.status_code}: {response.text}"
            
    except requests.exceptions.Timeout:
        results["error"] = "요청 타임아웃 (120초 초과)"
    except Exception as e:
        results["error"] = str(e)
    
    return results

def test_concurrent_requests() -> Dict[str, Any]:
    """동시 요청 테스트"""
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    base_url = "http://localhost:8017"
    test_data = {
        "url": "https://example.com",
        "ai_mode": "",
        "content_length": "1000",
        "rules": ["SEO"],
        "policy_auto": False
    }
    
    results = {
        "concurrent_requests": 3,
        "successful_requests": 0,
        "failed_requests": 0,
        "average_time": 0,
        "max_time": 0,
        "min_time": float('inf'),
        "times": []
    }
    
    def make_request():
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/api/v1/generate-post",  # 올바른 엔드포인트
                json=test_data,
                timeout=60
            )
            end_time = time.time()
            
            return {
                "success": response.status_code == 200,
                "time": (end_time - start_time) * 1000,
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "time": 0,
                "error": str(e)
            }
    
    print(f"🔄 {results['concurrent_requests']}개 동시 요청 테스트...")
    
    with ThreadPoolExecutor(max_workers=results['concurrent_requests']) as executor:
        futures = [executor.submit(make_request) for _ in range(results['concurrent_requests'])]
        
        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                results["successful_requests"] += 1
                results["times"].append(result["time"])
                results["max_time"] = max(results["max_time"], result["time"])
                results["min_time"] = min(results["min_time"], result["time"])
            else:
                results["failed_requests"] += 1
    
    if results["times"]:
        results["average_time"] = round(sum(results["times"]) / len(results["times"]), 2)
        results["max_time"] = round(results["max_time"], 2)
        results["min_time"] = round(results["min_time"], 2)
    
    return results

def test_simple_text_generation() -> Dict[str, Any]:
    """간단한 텍스트 기반 콘텐츠 생성 테스트"""
    base_url = "http://localhost:8017"
    
    # 간단한 텍스트로 테스트
    test_data = {
        "text": "인공지능과 머신러닝의 차이점에 대해 설명해주세요.",
        "ai_mode": "",
        "content_length": "1000",
        "rules": ["SEO"],
        "policy_auto": False
    }
    
    results = {
        "total_time": 0,
        "success": False,
        "error": None
    }
    
    try:
        print("🔄 간단한 텍스트 기반 콘텐츠 생성 테스트...")
        
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/v1/generate-post",
            json=test_data,
            timeout=60
        )
        end_time = time.time()
        
        results["total_time"] = round((end_time - start_time) * 1000, 2)
        results["status_code"] = response.status_code
        
        if response.status_code == 200:
            results["success"] = True
            response_data = response.json()
            if "post" in response_data:
                results["word_count"] = len(response_data["post"].get("content", "").split())
        else:
            results["error"] = f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        results["error"] = str(e)
    
    return results

def analyze_performance_issues(results: Dict[str, Any]) -> List[str]:
    """성능 문제점 분석"""
    issues = []
    
    # API 응답 시간 분석
    api_results = results.get("api_test", {})
    for endpoint, data in api_results.items():
        if data.get("success") and data.get("response_time", 0) > 1000:
            issues.append(f"⚠️ {endpoint} API 응답 시간이 느림: {data['response_time']}ms")
    
    # 콘텐츠 생성 시간 분석
    content_test = results.get("content_test", {})
    if content_test.get("total_time", 0) > 30000:  # 30초 이상
        issues.append(f"⚠️ 콘텐츠 생성 시간이 너무 김: {content_test['total_time']}ms")
    
    # 간단한 텍스트 생성 테스트 분석
    simple_test = results.get("simple_test", {})
    if simple_test.get("total_time", 0) > 30000:
        issues.append(f"⚠️ 간단한 텍스트 생성 시간이 너무 김: {simple_test['total_time']}ms")
    
    # 동시 요청 분석
    concurrent_test = results.get("concurrent_test", {})
    if concurrent_test.get("failed_requests", 0) > 0:
        issues.append(f"⚠️ 동시 요청 실패: {concurrent_test['failed_requests']}개")
    
    if concurrent_test.get("average_time", 0) > 30000:
        issues.append(f"⚠️ 동시 요청 평균 시간이 느림: {concurrent_test['average_time']}ms")
    
    # 시스템 리소스 분석
    system_info = results.get("system_info", {})
    if system_info.get("memory_percent", 0) > 80:
        issues.append(f"⚠️ 메모리 사용률이 높음: {system_info['memory_percent']}%")
    
    if system_info.get("disk_usage", 0) > 90:
        issues.append(f"⚠️ 디스크 사용률이 높음: {system_info['disk_usage']}%")
    
    return issues

def generate_recommendations(issues: List[str]) -> List[str]:
    """개선 권장사항 생성"""
    recommendations = []
    
    for issue in issues:
        if "API 응답 시간" in issue:
            recommendations.append("🔧 API 캐싱 구현 및 데이터베이스 쿼리 최적화")
        elif "콘텐츠 생성 시간" in issue:
            recommendations.append("🔧 AI API 호출 최적화 및 비동기 처리 개선")
        elif "동시 요청 실패" in issue:
            recommendations.append("🔧 동시 요청 처리 로직 개선 및 큐 시스템 도입")
        elif "메모리 사용률" in issue:
            recommendations.append("🔧 메모리 누수 점검 및 가비지 컬렉션 최적화")
        elif "디스크 사용률" in issue:
            recommendations.append("🔧 로그 파일 정리 및 불필요한 파일 제거")
    
    # 일반적인 권장사항
    recommendations.extend([
        "🔧 비동기 처리 방식으로 전환",
        "🔧 API 응답 캐싱 시스템 도입",
        "🔧 데이터베이스 인덱스 최적화",
        "🔧 로깅 레벨 조정으로 I/O 부하 감소",
        "🔧 AI API 호출 타임아웃 설정",
        "🔧 병렬 처리로 성능 향상"
    ])
    
    return list(set(recommendations))  # 중복 제거

def main():
    """메인 테스트 실행"""
    print("🚀 콘텐츠 생성 성능 종합 테스트 시작")
    print("=" * 60)
    
    results = {}
    
    # 1. 시스템 정보 수집
    print("📊 시스템 정보 수집 중...")
    results["system_info"] = get_system_info()
    
    # 2. API 엔드포인트 테스트
    print("🔗 API 엔드포인트 테스트 중...")
    results["api_test"] = test_api_endpoints()
    
    # 3. 간단한 텍스트 기반 콘텐츠 생성 테스트
    print("📝 간단한 텍스트 기반 콘텐츠 생성 테스트 중...")
    results["simple_test"] = test_simple_text_generation()
    
    # 4. URL 기반 콘텐츠 생성 성능 테스트
    print("📝 URL 기반 콘텐츠 생성 성능 테스트 중...")
    results["content_test"] = test_content_generation_performance()
    
    # 5. 동시 요청 테스트
    print("⚡ 동시 요청 테스트 중...")
    results["concurrent_test"] = test_concurrent_requests()
    
    # 6. 문제점 분석
    print("🔍 성능 문제점 분석 중...")
    issues = analyze_performance_issues(results)
    
    # 7. 권장사항 생성
    print("💡 개선 권장사항 생성 중...")
    recommendations = generate_recommendations(issues)
    
    # 8. 결과 출력
    print("\n" + "=" * 60)
    print("📋 테스트 결과 요약")
    print("=" * 60)
    
    # 시스템 정보
    print(f"\n🖥️ 시스템 정보:")
    print(f"  CPU 코어: {results['system_info']['cpu_count']}")
    print(f"  메모리 사용률: {results['system_info']['memory_percent']}%")
    print(f"  디스크 사용률: {results['system_info']['disk_usage']}%")
    
    # API 테스트 결과
    print(f"\n🔗 API 응답 시간:")
    for endpoint, data in results["api_test"].items():
        if data["success"]:
            print(f"  {endpoint}: {data['response_time']}ms")
        else:
            print(f"  {endpoint}: 실패 - {data.get('error', 'Unknown error')}")
    
    # 간단한 텍스트 생성 결과
    simple_test = results["simple_test"]
    print(f"\n📝 간단한 텍스트 생성 성능:")
    if simple_test["success"]:
        print(f"  총 소요 시간: {simple_test['total_time']}ms")
        print(f"  단어 수: {simple_test.get('word_count', 'N/A')}")
    else:
        print(f"  실패: {simple_test['error']}")
    
    # URL 기반 콘텐츠 생성 결과
    content_test = results["content_test"]
    print(f"\n📝 URL 기반 콘텐츠 생성 성능:")
    if content_test["success"]:
        print(f"  총 소요 시간: {content_test['total_time']}ms")
        for step, data in content_test["steps"].items():
            print(f"  {step}: {data['time']}ms")
        if "content_info" in content_test:
            info = content_test["content_info"]
            print(f"  단어 수: {info['word_count']}")
            print(f"  SEO 분석 포함: {info['has_seo_analysis']}")
    else:
        print(f"  실패: {content_test['error']}")
    
    # 동시 요청 결과
    concurrent_test = results["concurrent_test"]
    print(f"\n⚡ 동시 요청 결과:")
    print(f"  성공: {concurrent_test['successful_requests']}개")
    print(f"  실패: {concurrent_test['failed_requests']}개")
    if concurrent_test["times"]:
        print(f"  평균 시간: {concurrent_test['average_time']}ms")
        print(f"  최소 시간: {concurrent_test['min_time']}ms")
        print(f"  최대 시간: {concurrent_test['max_time']}ms")
    
    # 문제점 및 권장사항
    if issues:
        print(f"\n⚠️ 발견된 문제점:")
        for issue in issues:
            print(f"  {issue}")
    
    if recommendations:
        print(f"\n💡 개선 권장사항:")
        for rec in recommendations:
            print(f"  {rec}")
    
    # 결과 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"content_performance_test_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "results": results,
            "issues": issues,
            "recommendations": recommendations
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 테스트 결과가 {filename}에 저장되었습니다.")
    print("\n" + "=" * 60)
    print("✅ 테스트 완료!")

if __name__ == "__main__":
    main() 