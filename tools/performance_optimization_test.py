#!/usr/bin/env python3
"""
전체 시스템 성능 최적화 테스트 스크립트
"""

import requests
import json
import time
import asyncio
import aiohttp
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import statistics

class PerformanceOptimizationTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
        
    def test_system_status(self):
        """시스템 상태 테스트"""
        print("🔍 시스템 상태 테스트...")
        try:
            response = requests.get(f"{self.base_url}/api/v1/system-status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 시스템 상태: {data.get('overall_status', '알 수 없음')}")
                print(f"   - CPU: {data.get('system', {}).get('cpu_usage', '알 수 없음')}")
                print(f"   - 메모리: {data.get('system', {}).get('memory_usage', '알 수 없음')}")
                return True
            else:
                print(f"❌ 시스템 상태 확인 실패: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 시스템 상태 테스트 오류: {e}")
            return False
    
    def test_database_performance(self):
        """데이터베이스 성능 테스트"""
        print("\n🗄️ 데이터베이스 성능 테스트...")
        try:
            response = requests.get(f"{self.base_url}/api/v1/stats/api-usage", timeout=10)
            if response.status_code == 200:
                print("✅ 데이터베이스 연결 성공")
                return True
            else:
                print(f"❌ 데이터베이스 연결 실패: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 데이터베이스 테스트 오류: {e}")
            return False
    
    def test_crawling_performance(self):
        """크롤링 성능 테스트"""
        print("\n🕷️ 크롤링 성능 테스트...")
        
        test_urls = [
            "https://www.searchengineland.com/google-core-update-may-2024-447456",
            "https://www.socialmediatoday.com/news/ai-content-generation-trends-2024/",
            "https://www.marketingland.com/seo-strategies-2024/"
        ]
        
        results = []
        for i, url in enumerate(test_urls, 1):
            print(f"   테스트 {i}/3: {url}")
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/generate-post-gemini-2-flash",
                    json={
                        "url": url,
                        "text": "",
                        "rules": ["AI_SEO", "AI_SEARCH"],
                        "ai_mode": "gemini_2_0_flash",
                        "content_length": "2000",
                        "policy_auto": False
                    },
                    timeout=60
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print(f"   ✅ 성공 ({duration:.2f}초)")
                        results.append(duration)
                    else:
                        print(f"   ❌ 실패: {result.get('message', '알 수 없음')}")
                else:
                    print(f"   ❌ HTTP 오류: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ 오류: {e}")
        
        if results:
            avg_time = statistics.mean(results)
            min_time = min(results)
            max_time = max(results)
            print(f"\n📊 크롤링 성능 결과:")
            print(f"   - 평균 시간: {avg_time:.2f}초")
            print(f"   - 최소 시간: {min_time:.2f}초")
            print(f"   - 최대 시간: {max_time:.2f}초")
            return results
        else:
            print("❌ 크롤링 테스트 실패")
            return []
    
    def test_translation_performance(self):
        """번역 성능 테스트"""
        print("\n🌐 번역 성능 테스트...")
        
        test_texts = [
            "Artificial Intelligence is transforming the way we work and live.",
            "Machine learning algorithms are becoming more sophisticated every day.",
            "The future of technology lies in the integration of AI and human creativity."
        ]
        
        results = []
        for i, text in enumerate(test_texts, 1):
            print(f"   테스트 {i}/3: {len(text)}자 텍스트")
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/generate-post-gemini-2-flash",
                    json={
                        "url": "",
                        "text": text,
                        "rules": ["AI_SEO"],
                        "ai_mode": "gemini_2_0_flash",
                        "content_length": "1500",
                        "policy_auto": False
                    },
                    timeout=60
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print(f"   ✅ 성공 ({duration:.2f}초)")
                        results.append(duration)
                    else:
                        print(f"   ❌ 실패: {result.get('message', '알 수 없음')}")
                else:
                    print(f"   ❌ HTTP 오류: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ 오류: {e}")
        
        if results:
            avg_time = statistics.mean(results)
            min_time = min(results)
            max_time = max(results)
            print(f"\n📊 번역 성능 결과:")
            print(f"   - 평균 시간: {avg_time:.2f}초")
            print(f"   - 최소 시간: {min_time:.2f}초")
            print(f"   - 최대 시간: {max_time:.2f}초")
            return results
        else:
            print("❌ 번역 테스트 실패")
            return []
    
    def test_content_generation_performance(self):
        """콘텐츠 생성 성능 테스트"""
        print("\n✍️ 콘텐츠 생성 성능 테스트...")
        
        test_data = {
            "url": "",
            "text": "인공지능과 머신러닝이 현대 사회에 미치는 영향에 대해 설명합니다.",
            "rules": ["AI_SEO", "AI_SEARCH", "TECH"],
            "ai_mode": "gemini_2_0_flash",
            "content_length": "3000",
            "policy_auto": True
        }
        
        results = []
        for i in range(3):
            print(f"   테스트 {i+1}/3")
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/generate-post-gemini-2-flash",
                    json=test_data,
                    timeout=90
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        data = result.get('data', {})
                        content_length = len(data.get('content', ''))
                        print(f"   ✅ 성공 ({duration:.2f}초, {content_length}자)")
                        results.append(duration)
                    else:
                        print(f"   ❌ 실패: {result.get('message', '알 수 없음')}")
                else:
                    print(f"   ❌ HTTP 오류: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ 오류: {e}")
        
        if results:
            avg_time = statistics.mean(results)
            min_time = min(results)
            max_time = max(results)
            print(f"\n📊 콘텐츠 생성 성능 결과:")
            print(f"   - 평균 시간: {avg_time:.2f}초")
            print(f"   - 최소 시간: {min_time:.2f}초")
            print(f"   - 최대 시간: {max_time:.2f}초")
            return results
        else:
            print("❌ 콘텐츠 생성 테스트 실패")
            return []
    
    def test_concurrent_performance(self):
        """동시 처리 성능 테스트"""
        print("\n⚡ 동시 처리 성능 테스트...")
        
        test_data = {
            "url": "",
            "text": "AI technology is rapidly evolving and changing our world.",
            "rules": ["AI_SEO"],
            "ai_mode": "gemini_2_0_flash",
            "content_length": "2000",
            "policy_auto": False
        }
        
        def make_request():
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/generate-post-gemini-2-flash",
                    json=test_data,
                    timeout=60
                )
                end_time = time.time()
                duration = end_time - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        return duration, True
                    else:
                        return duration, False
                else:
                    return duration, False
            except Exception as e:
                return 0, False
        
        # 3개 동시 요청
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request) for _ in range(3)]
            results = []
            
            for i, future in enumerate(futures, 1):
                duration, success = future.result()
                if success:
                    print(f"   요청 {i}: ✅ 성공 ({duration:.2f}초)")
                    results.append(duration)
                else:
                    print(f"   요청 {i}: ❌ 실패")
        
        if results:
            avg_time = statistics.mean(results)
            total_time = max(results)  # 동시 처리이므로 가장 긴 시간
            print(f"\n📊 동시 처리 성능 결과:")
            print(f"   - 평균 개별 시간: {avg_time:.2f}초")
            print(f"   - 총 처리 시간: {total_time:.2f}초")
            print(f"   - 처리량: {len(results)}개 요청")
            return results
        else:
            print("❌ 동시 처리 테스트 실패")
            return []
    
    def test_cache_performance(self):
        """캐시 성능 테스트"""
        print("\n💾 캐시 성능 테스트...")
        
        test_data = {
            "url": "",
            "text": "This is a test text for cache performance evaluation.",
            "rules": ["AI_SEO"],
            "ai_mode": "gemini_2_0_flash",
            "content_length": "1500",
            "policy_auto": False
        }
        
        # 첫 번째 요청 (캐시 미스)
        print("   첫 번째 요청 (캐시 미스)...")
        start_time = time.time()
        try:
            response1 = requests.post(
                f"{self.base_url}/api/v1/generate-post-gemini-2-flash",
                json=test_data,
                timeout=60
            )
            first_duration = time.time() - start_time
            
            if response1.status_code == 200:
                print(f"   ✅ 성공 ({first_duration:.2f}초)")
                
                # 잠시 대기
                time.sleep(2)
                
                # 두 번째 요청 (캐시 히트)
                print("   두 번째 요청 (캐시 히트)...")
                start_time = time.time()
                response2 = requests.post(
                    f"{self.base_url}/api/v1/generate-post-gemini-2-flash",
                    json=test_data,
                    timeout=60
                )
                second_duration = time.time() - start_time
                
                if response2.status_code == 200:
                    print(f"   ✅ 성공 ({second_duration:.2f}초)")
                    
                    speedup = first_duration / second_duration if second_duration > 0 else 0
                    print(f"\n📊 캐시 성능 결과:")
                    print(f"   - 첫 번째 요청: {first_duration:.2f}초")
                    print(f"   - 두 번째 요청: {second_duration:.2f}초")
                    print(f"   - 속도 향상: {speedup:.1f}배")
                    
                    return [first_duration, second_duration]
                else:
                    print(f"   ❌ 두 번째 요청 실패: {response2.status_code}")
            else:
                print(f"   ❌ 첫 번째 요청 실패: {response1.status_code}")
                
        except Exception as e:
            print(f"   ❌ 캐시 테스트 오류: {e}")
        
        return []
    
    def run_all_tests(self):
        """모든 성능 테스트 실행"""
        print("🚀 전체 시스템 성능 최적화 테스트 시작")
        print("=" * 60)
        
        # 시스템 상태 확인
        if not self.test_system_status():
            print("❌ 시스템이 실행되지 않고 있습니다.")
            return
        
        # 데이터베이스 성능 테스트
        if not self.test_database_performance():
            print("❌ 데이터베이스 연결에 문제가 있습니다.")
            return
        
        # 각 단계별 성능 테스트
        crawling_results = self.test_crawling_performance()
        translation_results = self.test_translation_performance()
        generation_results = self.test_content_generation_performance()
        concurrent_results = self.test_concurrent_performance()
        cache_results = self.test_cache_performance()
        
        # 종합 결과 분석
        print("\n" + "=" * 60)
        print("📊 종합 성능 분석 결과")
        print("=" * 60)
        
        if crawling_results:
            print(f"🕷️ 크롤링: 평균 {statistics.mean(crawling_results):.2f}초")
        
        if translation_results:
            print(f"🌐 번역: 평균 {statistics.mean(translation_results):.2f}초")
        
        if generation_results:
            print(f"✍️ 콘텐츠 생성: 평균 {statistics.mean(generation_results):.2f}초")
        
        if concurrent_results:
            print(f"⚡ 동시 처리: 평균 {statistics.mean(concurrent_results):.2f}초")
        
        if cache_results and len(cache_results) >= 2:
            speedup = cache_results[0] / cache_results[1] if cache_results[1] > 0 else 0
            print(f"💾 캐시 효과: {speedup:.1f}배 속도 향상")
        
        # 성능 등급 평가
        print("\n🏆 성능 등급 평가")
        print("-" * 30)
        
        all_times = []
        if crawling_results:
            all_times.extend(crawling_results)
        if translation_results:
            all_times.extend(translation_results)
        if generation_results:
            all_times.extend(generation_results)
        
        if all_times:
            avg_time = statistics.mean(all_times)
            if avg_time < 10:
                grade = "A+ (매우 우수)"
            elif avg_time < 15:
                grade = "A (우수)"
            elif avg_time < 20:
                grade = "B+ (양호)"
            elif avg_time < 25:
                grade = "B (보통)"
            else:
                grade = "C (개선 필요)"
            
            print(f"평균 응답 시간: {avg_time:.2f}초")
            print(f"성능 등급: {grade}")
        
        print("\n✅ 성능 최적화 테스트 완료!")

if __name__ == "__main__":
    tester = PerformanceOptimizationTest()
    tester.run_all_tests() 