#!/usr/bin/env python3
"""
성능 최적화 및 에러 처리 테스트 스크립트
크롤링 → 번역 → 키워드 추출 → 콘텐츠 생성 파이프라인의 성능을 테스트합니다.
"""

import asyncio
import sys
import os
import json
import requests
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import statistics

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

class PerformanceOptimizationTest:
    """성능 최적화 테스트 클래스"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "performance_stats": {},
            "error_stats": {}
        }
    
    def test_system_status(self):
        """시스템 상태 테스트"""
        print("🔍 시스템 상태 확인 중...")
        try:
            response = requests.get(f"{self.base_url}/api/v1/system-status", timeout=30)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 시스템 상태: {data.get('overall_status', '알 수 없음')}")
                print(f"   - CPU 사용률: {data.get('system', {}).get('cpu_usage', 'N/A')}")
                print(f"   - 메모리 사용률: {data.get('system', {}).get('memory_usage', 'N/A')}")
                print(f"   - OpenAI API: {'✅' if data.get('apis', {}).get('openai') else '❌'}")
                print(f"   - Gemini API: {'✅' if data.get('apis', {}).get('gemini') else '❌'}")
                
                # 성능 통계 출력
                if 'performance' in data and 'stats' in data['performance']:
                    print("\n📊 성능 통계:")
                    for operation, stats in data['performance']['stats'].items():
                        if isinstance(stats, dict) and 'avg_time' in stats:
                            print(f"   - {operation}: 평균 {stats['avg_time']:.2f}초")
                
                # 에러 통계 출력
                if 'errors' in data:
                    print("\n⚠️ 에러 통계:")
                    error_stats = data['errors']
                    if isinstance(error_stats, dict):
                        total_errors = error_stats.get('total_errors', 0)
                        print(f"   - 총 에러 수: {total_errors}")
                        if 'error_counts' in error_stats:
                            for error_type, count in error_stats['error_counts'].items():
                                print(f"   - {error_type}: {count}회")
                
                return True
            else:
                print(f"❌ 시스템 상태 확인 실패: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 시스템 상태 확인 오류: {e}")
            return False
    
    def test_single_pipeline_performance(self, test_name: str, test_data: dict, expected_duration: float = 30.0):
        """단일 파이프라인 성능 테스트"""
        print(f"\n⚡ {test_name} 성능 테스트...")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/generate-post-gemini-2-flash",
                json=test_data,
                timeout=expected_duration + 10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content_length = len(data.get('data', {}).get('content', ''))
                
                # 성능 평가
                performance_score = "좋음" if duration < expected_duration else "보통"
                if duration > expected_duration * 1.5:
                    performance_score = "느림"
                
                print(f"✅ {test_name} 성공 ({duration:.2f}초)")
                print(f"   - 콘텐츠 길이: {content_length}자")
                print(f"   - 성능 평가: {performance_score}")
                
                result = {
                    "test": test_name,
                    "status": "success",
                    "duration": round(duration, 2),
                    "content_length": content_length,
                    "performance_score": performance_score
                }
            else:
                print(f"❌ {test_name} 실패: {response.status_code}")
                result = {
                    "test": test_name,
                    "status": "failed",
                    "error": f"HTTP {response.status_code}",
                    "duration": round(duration, 2)
                }
            
            self.test_results["tests"].append(result)
            return result["status"] == "success"
            
        except Exception as e:
            print(f"❌ {test_name} 오류: {e}")
            result = {
                "test": test_name,
                "status": "error",
                "error": str(e),
                "duration": 0
            }
            self.test_results["tests"].append(result)
            return False
    
    def test_concurrent_pipelines(self, num_concurrent: int = 3):
        """동시 파이프라인 테스트"""
        print(f"\n🔄 동시 파이프라인 테스트 ({num_concurrent}개)...")
        
        test_data = {
            "text": "Artificial Intelligence is transforming the world.",
            "ai_mode": "gemini_2_0_flash",
            "content_length": "2000",
            "rules": ["AI_SEO"]
        }
        
        def run_single_test():
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/generate-post-gemini-2-flash",
                    json=test_data,
                    timeout=60
                )
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    return {"status": "success", "duration": duration}
                else:
                    return {"status": "failed", "duration": duration, "error": response.status_code}
            except Exception as e:
                return {"status": "error", "duration": 0, "error": str(e)}
        
        # 동시 실행
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(run_single_test) for _ in range(num_concurrent)]
            results = [future.result() for future in futures]
        
        # 결과 분석
        successful_results = [r for r in results if r["status"] == "success"]
        durations = [r["duration"] for r in successful_results]
        
        if durations:
            avg_duration = statistics.mean(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            
            print(f"✅ 동시 테스트 완료")
            print(f"   - 성공률: {len(successful_results)}/{num_concurrent} ({len(successful_results)/num_concurrent*100:.1f}%)")
            print(f"   - 평균 시간: {avg_duration:.2f}초")
            print(f"   - 최소 시간: {min_duration:.2f}초")
            print(f"   - 최대 시간: {max_duration:.2f}초")
            
            result = {
                "test": "concurrent_pipelines",
                "status": "success",
                "concurrent_count": num_concurrent,
                "success_rate": len(successful_results) / num_concurrent,
                "avg_duration": round(avg_duration, 2),
                "min_duration": round(min_duration, 2),
                "max_duration": round(max_duration, 2)
            }
        else:
            print(f"❌ 동시 테스트 실패")
            result = {
                "test": "concurrent_pipelines",
                "status": "failed",
                "concurrent_count": num_concurrent,
                "success_rate": 0
            }
        
        self.test_results["tests"].append(result)
        return result["status"] == "success"
    
    def test_error_handling(self):
        """에러 처리 테스트"""
        print(f"\n🛡️ 에러 처리 테스트...")
        
        test_cases = [
            {
                "name": "빈 텍스트",
                "data": {"text": "", "ai_mode": "gemini_2_0_flash"},
                "expected": "400"
            },
            {
                "name": "유효하지 않은 URL",
                "data": {"url": "invalid-url", "ai_mode": "gemini_2_0_flash"},
                "expected": "400"
            },
            {
                "name": "너무 긴 텍스트",
                "data": {"text": "A" * 100000, "ai_mode": "gemini_2_0_flash"},
                "expected": "400"
            }
        ]
        
        error_handling_results = []
        
        for test_case in test_cases:
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/generate-post-gemini-2-flash",
                    json=test_case["data"],
                    timeout=30
                )
                
                if response.status_code == int(test_case["expected"]):
                    print(f"✅ {test_case['name']}: 올바른 에러 처리")
                    error_handling_results.append({"test": test_case["name"], "status": "success"})
                else:
                    print(f"❌ {test_case['name']}: 예상과 다른 응답 ({response.status_code})")
                    error_handling_results.append({"test": test_case["name"], "status": "failed", "actual": response.status_code})
                    
            except Exception as e:
                print(f"❌ {test_case['name']}: 예외 발생 - {e}")
                error_handling_results.append({"test": test_case["name"], "status": "error", "error": str(e)})
        
        # 전체 에러 처리 평가
        success_count = sum(1 for r in error_handling_results if r["status"] == "success")
        success_rate = success_count / len(test_cases)
        
        result = {
            "test": "error_handling",
            "status": "success" if success_rate >= 0.8 else "partial",
            "success_rate": success_rate,
            "details": error_handling_results
        }
        
        self.test_results["tests"].append(result)
        return success_rate >= 0.8
    
    def test_cache_performance(self):
        """캐시 성능 테스트"""
        print(f"\n💾 캐시 성능 테스트...")
        
        test_data = {
            "text": "This is a test for cache performance.",
            "ai_mode": "gemini_2_0_flash",
            "content_length": "1000",
            "rules": ["AI_SEO"]
        }
        
        # 첫 번째 요청 (캐시 미스)
        start_time = time.time()
        response1 = requests.post(
            f"{self.base_url}/api/v1/generate-post-gemini-2-flash",
            json=test_data,
            timeout=60
        )
        first_duration = time.time() - start_time
        
        # 두 번째 요청 (캐시 히트)
        start_time = time.time()
        response2 = requests.post(
            f"{self.base_url}/api/v1/generate-post-gemini-2-flash",
            json=test_data,
            timeout=60
        )
        second_duration = time.time() - start_time
        
        if response1.status_code == 200 and response2.status_code == 200:
            speedup = first_duration / second_duration if second_duration > 0 else 0
            
            print(f"✅ 캐시 성능 테스트 완료")
            print(f"   - 첫 번째 요청: {first_duration:.2f}초")
            print(f"   - 두 번째 요청: {second_duration:.2f}초")
            print(f"   - 속도 향상: {speedup:.1f}배")
            
            result = {
                "test": "cache_performance",
                "status": "success",
                "first_request": round(first_duration, 2),
                "second_request": round(second_duration, 2),
                "speedup": round(speedup, 1)
            }
        else:
            print(f"❌ 캐시 성능 테스트 실패")
            result = {
                "test": "cache_performance",
                "status": "failed",
                "first_status": response1.status_code,
                "second_status": response2.status_code
            }
        
        self.test_results["tests"].append(result)
        return result["status"] == "success"
    
    def save_results(self, filename: str = None):
        """테스트 결과를 파일로 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_optimization_test_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 테스트 결과가 {filename}에 저장되었습니다.")
        except Exception as e:
            print(f"❌ 결과 저장 실패: {e}")
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "="*60)
        print("성능 최적화 테스트 결과")
        print("="*60)
        
        total_tests = len(self.test_results["tests"])
        successful_tests = sum(1 for test in self.test_results["tests"] if test.get("status") == "success")
        failed_tests = total_tests - successful_tests
        
        print(f"총 테스트 수: {total_tests}")
        print(f"성공: {successful_tests}")
        print(f"실패: {failed_tests}")
        print(f"성공률: {(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        if self.test_results["tests"]:
            print("\n상세 결과:")
            for i, test in enumerate(self.test_results["tests"], 1):
                print(f"{i}. {test.get('test', 'unknown')}: {test.get('status', 'unknown')}")
                if test.get('duration'):
                    print(f"   소요시간: {test['duration']}초")
                if test.get('performance_score'):
                    print(f"   성능 평가: {test['performance_score']}")
                if test.get('success_rate'):
                    print(f"   성공률: {test['success_rate']*100:.1f}%")
                if test.get('error'):
                    print(f"   오류: {test['error']}")
        
        # 성능 통계
        duration_tests = [test for test in self.test_results["tests"] if test.get("duration")]
        if duration_tests:
            durations = [test["duration"] for test in duration_tests]
            print(f"\n성능 통계:")
            print(f"   평균 시간: {statistics.mean(durations):.2f}초")
            print(f"   중간값: {statistics.median(durations):.2f}초")
            print(f"   최소 시간: {min(durations):.2f}초")
            print(f"   최대 시간: {max(durations):.2f}초")

def main():
    """메인 테스트 함수"""
    print("성능 최적화 테스트를 시작합니다...")
    print("크롤링 → 번역 → 키워드 추출 → 콘텐츠 생성 파이프라인")
    
    # API 키 확인 - Gemini API 숨김 처리됨
    # if not settings.get_gemini_api_key():
    #     print("❌ Gemini API 키가 설정되지 않았습니다.")
    #     print("환경변수 GEMINI_API_KEY를 설정해주세요.")
    #     return
    
    # print("✅ Gemini API 키가 설정되었습니다.")
    print("ℹ️ Gemini API 기능이 숨김 처리되었습니다.")
    
    # 테스트 인스턴스 생성
    tester = PerformanceOptimizationTest()
    
    # 1. 시스템 상태 확인
    if not tester.test_system_status():
        print("❌ 시스템이 실행되지 않고 있습니다. 먼저 서버를 시작해주세요.")
        return
    
    # 2. 단일 파이프라인 성능 테스트
    test_cases = [
        {
            "name": "짧은 텍스트",
            "data": {
                "text": "AI is transforming the world.",
                "ai_mode": "gemini_2_0_flash",
                "content_length": "1000",
                "rules": ["AI_SEO"]
            },
            "expected_duration": 20.0
        },
        {
            "name": "중간 텍스트",
            "data": {
                "text": "Artificial Intelligence is revolutionizing various industries including healthcare, finance, and education. The technology continues to evolve rapidly.",
                "ai_mode": "gemini_2_0_flash",
                "content_length": "3000",
                "rules": ["AI_SEO", "AI_SEARCH"]
            },
            "expected_duration": 30.0
        },
        {
            "name": "긴 텍스트",
            "data": {
                "text": "Artificial Intelligence (AI) is transforming the way we live and work. From virtual assistants to autonomous vehicles, AI technologies are becoming increasingly integrated into our daily lives. Machine learning algorithms can now process vast amounts of data to identify patterns and make predictions with remarkable accuracy. The impact of AI on various industries is profound. In healthcare, AI is helping doctors diagnose diseases more accurately and develop personalized treatment plans. In finance, AI algorithms are detecting fraudulent transactions and optimizing investment strategies. In education, AI-powered platforms are providing personalized learning experiences for students.",
                "ai_mode": "gemini_2_0_flash",
                "content_length": "5000",
                "rules": ["AI_SEO", "AI_SEARCH", "POLICY"]
            },
            "expected_duration": 40.0
        }
    ]
    
    for test_case in test_cases:
        tester.test_single_pipeline_performance(
            test_case["name"], 
            test_case["data"], 
            test_case["expected_duration"]
        )
    
    # 3. 동시 파이프라인 테스트
    tester.test_concurrent_pipelines(num_concurrent=3)
    
    # 4. 에러 처리 테스트
    tester.test_error_handling()
    
    # 5. 캐시 성능 테스트
    tester.test_cache_performance()
    
    # 결과 저장 및 출력
    tester.save_results()
    tester.print_summary()
    
    print("\n✅ 성능 최적화 테스트가 완료되었습니다!")

if __name__ == "__main__":
    main() 