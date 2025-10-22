#!/usr/bin/env python3
"""
성능 스트레스 테스트 스크립트
시스템의 한계를 테스트하고 최적화 포인트를 찾습니다.
"""
import requests
import time
import threading
import concurrent.futures
import statistics
from datetime import datetime
import json

class PerformanceStressTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = {}
        
    def log(self, message):
        """로그 출력"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def test_single_endpoint_stress(self, endpoint, num_requests=100, max_workers=10):
        """단일 엔드포인트 스트레스 테스트"""
        self.log(f"🔥 {endpoint} 스트레스 테스트 시작 ({num_requests} 요청, {max_workers} 동시)")
        
        def make_request():
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                end_time = time.time()
                return {
                    "status_code": response.status_code,
                    "response_time": (end_time - start_time) * 1000,
                    "success": response.status_code == 200,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                return {
                    "status_code": 0,
                    "response_time": 0,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_list = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(future_list)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 결과 분석
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        response_times = [r["response_time"] for r in successful_requests]
        
        stats = {
            "total_requests": num_requests,
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": (len(successful_requests) / num_requests) * 100,
            "total_time": total_time,
            "requests_per_second": num_requests / total_time,
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "median_response_time": statistics.median(response_times) if response_times else 0,
            "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else 0,
            "p99_response_time": statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else 0
        }
        
        self.log(f"📊 {endpoint} 결과: {stats['success_rate']:.1f}% 성공, {stats['requests_per_second']:.1f} req/s, 평균 {stats['avg_response_time']:.2f}ms")
        
        return {
            "endpoint": endpoint,
            "stats": stats,
            "results": results
        }
    
    def test_mixed_endpoints_stress(self, duration=60):
        """혼합 엔드포인트 스트레스 테스트"""
        self.log(f"🔥 혼합 엔드포인트 스트레스 테스트 시작 ({duration}초)")
        
        endpoints = [
            "/",
            "/api/v1/posts",
            "/api/v1/keywords",
            "/api/v1/stats/dashboard",
            "/api/v1/system/uptime",
            "/api/v1/feature-updates/history"
        ]
        
        results = []
        start_time = time.time()
        
        def worker():
            while time.time() - start_time < duration:
                for endpoint in endpoints:
                    try:
                        request_start = time.time()
                        response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                        request_end = time.time()
                        
                        results.append({
                            "endpoint": endpoint,
                            "status_code": response.status_code,
                            "response_time": (request_end - request_start) * 1000,
                            "success": response.status_code == 200,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # 짧은 대기 시간
                        time.sleep(0.1)
                        
                    except Exception as e:
                        results.append({
                            "endpoint": endpoint,
                            "status_code": 0,
                            "response_time": 0,
                            "success": False,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        })
        
        # 여러 스레드로 동시 실행
        threads = []
        for _ in range(5):  # 5개 스레드
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        # 결과 분석
        total_requests = len(results)
        successful_requests = [r for r in results if r["success"]]
        
        # 엔드포인트별 통계
        endpoint_stats = {}
        for endpoint in endpoints:
            endpoint_results = [r for r in results if r["endpoint"] == endpoint]
            endpoint_successful = [r for r in endpoint_results if r["success"]]
            
            if endpoint_successful:
                response_times = [r["response_time"] for r in endpoint_successful]
                endpoint_stats[endpoint] = {
                    "total_requests": len(endpoint_results),
                    "successful_requests": len(endpoint_successful),
                    "success_rate": (len(endpoint_successful) / len(endpoint_results)) * 100,
                    "avg_response_time": statistics.mean(response_times),
                    "min_response_time": min(response_times),
                    "max_response_time": max(response_times),
                    "median_response_time": statistics.median(response_times)
                }
        
        overall_stats = {
            "duration": duration,
            "total_requests": total_requests,
            "successful_requests": len(successful_requests),
            "success_rate": (len(successful_requests) / total_requests) * 100,
            "requests_per_second": total_requests / duration,
            "endpoint_stats": endpoint_stats
        }
        
        self.log(f"📊 혼합 테스트 결과: {overall_stats['success_rate']:.1f}% 성공, {overall_stats['requests_per_second']:.1f} req/s")
        
        return {
            "test_type": "mixed_endpoints",
            "stats": overall_stats,
            "results": results
        }
    
    def test_memory_leak_detection(self, duration=120):
        """메모리 누수 감지 테스트"""
        self.log(f"🧠 메모리 누수 감지 테스트 시작 ({duration}초)")
        
        import psutil
        process = psutil.Process()
        
        memory_samples = []
        start_time = time.time()
        
        # 메모리 사용량 모니터링
        while time.time() - start_time < duration:
            memory_info = process.memory_info()
            memory_samples.append({
                "timestamp": datetime.now().isoformat(),
                "rss_mb": memory_info.rss / (1024 * 1024),
                "vms_mb": memory_info.vms / (1024 * 1024),
                "elapsed_time": time.time() - start_time
            })
            
            # API 요청 수행
            try:
                requests.get(f"{self.base_url}/api/v1/posts", timeout=5)
                requests.get(f"{self.base_url}/api/v1/keywords", timeout=5)
                requests.get(f"{self.base_url}/api/v1/stats/dashboard", timeout=5)
            except:
                pass
            
            time.sleep(5)  # 5초마다 샘플링
        
        # 메모리 사용량 분석
        rss_values = [sample["rss_mb"] for sample in memory_samples]
        vms_values = [sample["vms_mb"] for sample in memory_samples]
        
        memory_analysis = {
            "duration": duration,
            "samples_count": len(memory_samples),
            "rss_start_mb": rss_values[0] if rss_values else 0,
            "rss_end_mb": rss_values[-1] if rss_values else 0,
            "rss_increase_mb": rss_values[-1] - rss_values[0] if len(rss_values) > 1 else 0,
            "rss_increase_percent": ((rss_values[-1] - rss_values[0]) / rss_values[0] * 100) if len(rss_values) > 1 and rss_values[0] > 0 else 0,
            "vms_start_mb": vms_values[0] if vms_values else 0,
            "vms_end_mb": vms_values[-1] if vms_values else 0,
            "vms_increase_mb": vms_values[-1] - vms_values[0] if len(vms_values) > 1 else 0,
            "max_rss_mb": max(rss_values) if rss_values else 0,
            "min_rss_mb": min(rss_values) if rss_values else 0,
            "avg_rss_mb": statistics.mean(rss_values) if rss_values else 0
        }
        
        # 메모리 누수 판단
        memory_leak_detected = False
        if memory_analysis["rss_increase_percent"] > 20:  # 20% 이상 증가 시 누수 의심
            memory_leak_detected = True
        
        self.log(f"📊 메모리 분석: RSS {memory_analysis['rss_increase_mb']:.2f}MB 증가 ({memory_analysis['rss_increase_percent']:.1f}%)")
        
        if memory_leak_detected:
            self.log("⚠️ 메모리 누수가 감지되었습니다!")
        else:
            self.log("✅ 메모리 사용량이 안정적입니다.")
        
        return {
            "test_type": "memory_leak_detection",
            "memory_analysis": memory_analysis,
            "memory_leak_detected": memory_leak_detected,
            "samples": memory_samples
        }
    
    def test_database_performance_under_load(self, num_requests=500):
        """부하 하에서의 데이터베이스 성능 테스트"""
        self.log(f"🗄️ 데이터베이스 부하 테스트 시작 ({num_requests} 요청)")
        
        # 데이터베이스 집약적 엔드포인트들
        db_endpoints = [
            "/api/v1/posts",
            "/api/v1/keywords",
            "/api/v1/stats/dashboard",
            "/api/v1/feature-updates/history"
        ]
        
        results = []
        
        def make_db_request():
            endpoint = db_endpoints[hash(str(time.time())) % len(db_endpoints)]
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                end_time = time.time()
                return {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "response_time": (end_time - start_time) * 1000,
                    "success": response.status_code == 200,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                return {
                    "endpoint": endpoint,
                    "status_code": 0,
                    "response_time": 0,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_list = [executor.submit(make_db_request) for _ in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(future_list)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 결과 분석
        successful_requests = [r for r in results if r["success"]]
        response_times = [r["response_time"] for r in successful_requests]
        
        # 엔드포인트별 분석
        endpoint_analysis = {}
        for endpoint in db_endpoints:
            endpoint_results = [r for r in results if r["endpoint"] == endpoint]
            endpoint_successful = [r for r in endpoint_results if r["success"]]
            
            if endpoint_successful:
                endpoint_response_times = [r["response_time"] for r in endpoint_successful]
                endpoint_analysis[endpoint] = {
                    "total_requests": len(endpoint_results),
                    "successful_requests": len(endpoint_successful),
                    "success_rate": (len(endpoint_successful) / len(endpoint_results)) * 100,
                    "avg_response_time": statistics.mean(endpoint_response_times),
                    "min_response_time": min(endpoint_response_times),
                    "max_response_time": max(endpoint_response_times),
                    "median_response_time": statistics.median(endpoint_response_times),
                    "p95_response_time": statistics.quantiles(endpoint_response_times, n=20)[18] if len(endpoint_response_times) >= 20 else 0
                }
        
        db_performance = {
            "total_requests": num_requests,
            "successful_requests": len(successful_requests),
            "success_rate": (len(successful_requests) / num_requests) * 100,
            "total_time": total_time,
            "requests_per_second": num_requests / total_time,
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "median_response_time": statistics.median(response_times) if response_times else 0,
            "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else 0,
            "endpoint_analysis": endpoint_analysis
        }
        
        self.log(f"📊 DB 부하 테스트 결과: {db_performance['success_rate']:.1f}% 성공, {db_performance['requests_per_second']:.1f} req/s")
        
        return {
            "test_type": "database_performance_under_load",
            "performance": db_performance,
            "results": results
        }
    
    def run_comprehensive_stress_test(self):
        """종합 스트레스 테스트 실행"""
        self.log("🚀 종합 성능 스트레스 테스트 시작")
        print("=" * 60)
        
        try:
            # 1. 단일 엔드포인트 스트레스 테스트
            self.log("1단계: 단일 엔드포인트 스트레스 테스트")
            self.results["single_endpoint"] = self.test_single_endpoint_stress("/api/v1/posts", 200, 20)
            
            # 2. 혼합 엔드포인트 스트레스 테스트
            self.log("2단계: 혼합 엔드포인트 스트레스 테스트")
            self.results["mixed_endpoints"] = self.test_mixed_endpoints_stress(30)  # 30초
            
            # 3. 데이터베이스 부하 테스트
            self.log("3단계: 데이터베이스 부하 테스트")
            self.results["database_load"] = self.test_database_performance_under_load(300)
            
            # 4. 메모리 누수 감지 테스트
            self.log("4단계: 메모리 누수 감지 테스트")
            self.results["memory_leak"] = self.test_memory_leak_detection(60)  # 60초
            
            # 5. 결과 분석 및 리포트 생성
            self.generate_stress_test_report()
            
        except Exception as e:
            self.log(f"❌ 스트레스 테스트 중 오류 발생: {e}")
    
    def generate_stress_test_report(self):
        """스트레스 테스트 리포트 생성"""
        self.log("📋 스트레스 테스트 리포트 생성")
        
        # 성능 점수 계산
        single_score = min(100, self.results["single_endpoint"]["stats"]["success_rate"])
        mixed_score = min(100, self.results["mixed_endpoints"]["stats"]["success_rate"])
        db_score = min(100, self.results["database_load"]["performance"]["success_rate"])
        memory_score = 100 if not self.results["memory_leak"]["memory_leak_detected"] else 50
        
        overall_score = (single_score + mixed_score + db_score + memory_score) / 4
        
        report = {
            "test_summary": {
                "overall_score": overall_score,
                "test_timestamp": datetime.now().isoformat(),
                "performance_metrics": {
                    "single_endpoint_performance": single_score,
                    "mixed_endpoints_performance": mixed_score,
                    "database_performance": db_score,
                    "memory_stability": memory_score
                }
            },
            "detailed_results": self.results,
            "recommendations": self.generate_stress_test_recommendations()
        }
        
        # 리포트 저장
        with open("performance_stress_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.print_stress_test_summary(report)
        
        return report
    
    def generate_stress_test_recommendations(self):
        """스트레스 테스트 권장사항 생성"""
        recommendations = []
        
        # 단일 엔드포인트 성능 분석
        single_stats = self.results["single_endpoint"]["stats"]
        if single_stats["success_rate"] < 95:
            recommendations.append("단일 엔드포인트 성공률이 95% 미만입니다. 서버 리소스나 연결 풀을 확인하세요.")
        
        if single_stats["p95_response_time"] > 1000:
            recommendations.append("95% 응답시간이 1초를 초과합니다. 캐싱이나 데이터베이스 최적화를 고려하세요.")
        
        # 혼합 엔드포인트 성능 분석
        mixed_stats = self.results["mixed_endpoints"]["stats"]
        if mixed_stats["success_rate"] < 90:
            recommendations.append("혼합 엔드포인트 성공률이 90% 미만입니다. 동시 처리 능력을 개선하세요.")
        
        # 데이터베이스 성능 분석
        db_perf = self.results["database_load"]["performance"]
        if db_perf["success_rate"] < 95:
            recommendations.append("데이터베이스 부하 테스트 성공률이 95% 미만입니다. DB 연결 풀과 인덱스를 확인하세요.")
        
        # 메모리 분석
        memory_analysis = self.results["memory_leak"]["memory_analysis"]
        if memory_analysis["rss_increase_percent"] > 20:
            recommendations.append("메모리 사용량이 20% 이상 증가했습니다. 메모리 누수를 확인하고 최적화하세요.")
        
        if not recommendations:
            recommendations.append("시스템이 스트레스 테스트를 성공적으로 통과했습니다. 현재 설정을 유지하세요.")
        
        return recommendations
    
    def print_stress_test_summary(self, report):
        """스트레스 테스트 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("🔥 성능 스트레스 테스트 결과")
        print("=" * 60)
        
        summary = report["test_summary"]
        metrics = summary["performance_metrics"]
        
        print(f"📊 전체 점수: {summary['overall_score']:.1f}/100")
        print(f"📅 테스트 일시: {summary['test_timestamp']}")
        
        print("\n📈 성능 지표:")
        print(f"   단일 엔드포인트 성능: {metrics['single_endpoint_performance']:.1f}%")
        print(f"   혼합 엔드포인트 성능: {metrics['mixed_endpoints_performance']:.1f}%")
        print(f"   데이터베이스 성능: {metrics['database_performance']:.1f}%")
        print(f"   메모리 안정성: {metrics['memory_stability']:.1f}%")
        
        print("\n💡 최적화 권장사항:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"   {i}. {rec}")
        
        print(f"\n📄 상세 리포트: performance_stress_test_report.json")
        print("=" * 60)

def main():
    """메인 함수"""
    tester = PerformanceStressTest()
    tester.run_comprehensive_stress_test()

if __name__ == "__main__":
    main() 