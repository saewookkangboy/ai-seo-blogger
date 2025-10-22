#!/usr/bin/env python3
"""
전체 시스템 최적화 테스트 스크립트
성능, 안정성, 기능성을 종합적으로 테스트
"""
import requests
import json
import time
import psutil
import os
import sqlite3
from datetime import datetime, timedelta
import threading
import concurrent.futures

class SystemOptimizationTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = {}
        self.start_time = time.time()
        
    def log(self, message, level="INFO"):
        """로그 출력"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_api_endpoints(self):
        """API 엔드포인트 테스트"""
        self.log("🚀 API 엔드포인트 테스트 시작")
        
        endpoints = [
            "/",
            "/admin",
            "/api/v1/posts",
            "/api/v1/keywords", 
            "/api/v1/stats/dashboard",
            "/api/v1/system/uptime",
            "/api/v1/system/db-size",
            "/api/v1/system/api-response-time",
            "/api/v1/system/log-files",
            "/api/v1/feature-updates/history",
            "/api/v1/news-archive/"
        ]
        
        results = {}
        total_time = 0
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # ms
                total_time += response_time
                
                if response.status_code == 200:
                    results[endpoint] = {
                        "status": "success",
                        "response_time": response_time,
                        "status_code": response.status_code
                    }
                    self.log(f"✅ {endpoint}: {response_time:.2f}ms")
                else:
                    results[endpoint] = {
                        "status": "error",
                        "response_time": response_time,
                        "status_code": response.status_code
                    }
                    self.log(f"❌ {endpoint}: {response.status_code} ({response_time:.2f}ms)")
                    
            except Exception as e:
                results[endpoint] = {
                    "status": "error",
                    "response_time": 0,
                    "error": str(e)
                }
                self.log(f"❌ {endpoint}: {e}")
        
        avg_response_time = total_time / len(endpoints) if endpoints else 0
        success_count = sum(1 for r in results.values() if r["status"] == "success")
        
        self.test_results["api_endpoints"] = {
            "total_endpoints": len(endpoints),
            "success_count": success_count,
            "success_rate": (success_count / len(endpoints)) * 100,
            "average_response_time": avg_response_time,
            "details": results
        }
        
        self.log(f"📊 API 테스트 완료: {success_count}/{len(endpoints)} 성공, 평균 응답시간: {avg_response_time:.2f}ms")
    
    def test_database_performance(self):
        """데이터베이스 성능 테스트"""
        self.log("🗄️ 데이터베이스 성능 테스트 시작")
        
        try:
            # 데이터베이스 파일 크기 확인
            db_path = "news_archive.db"
            if os.path.exists(db_path):
                db_size = os.path.getsize(db_path) / 1024  # KB
            else:
                db_size = 0
            
            # 데이터베이스 연결 및 쿼리 테스트
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 테이블 목록 조회
            start_time = time.time()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            table_query_time = (time.time() - start_time) * 1000
            
            # 각 테이블의 레코드 수 조회
            table_stats = {}
            total_records = 0
            
            for table in tables:
                table_name = table[0]
                start_time = time.time()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                query_time = (time.time() - start_time) * 1000
                
                table_stats[table_name] = {
                    "record_count": count,
                    "query_time": query_time
                }
                total_records += count
            
            conn.close()
            
            self.test_results["database"] = {
                "db_size_kb": db_size,
                "table_count": len(tables),
                "total_records": total_records,
                "table_query_time": table_query_time,
                "table_stats": table_stats
            }
            
            self.log(f"📊 DB 테스트 완료: {len(tables)}개 테이블, {total_records}개 레코드, 크기: {db_size:.2f}KB")
            
        except Exception as e:
            self.log(f"❌ 데이터베이스 테스트 오류: {e}")
            self.test_results["database"] = {"error": str(e)}
    
    def test_memory_usage(self):
        """메모리 사용량 테스트"""
        self.log("🧠 메모리 사용량 테스트 시작")
        
        try:
            # 시스템 메모리 정보
            memory = psutil.virtual_memory()
            
            # 프로세스별 메모리 사용량
            process = psutil.Process()
            process_memory = process.memory_info()
            
            self.test_results["memory"] = {
                "total_memory_gb": memory.total / (1024**3),
                "available_memory_gb": memory.available / (1024**3),
                "used_memory_gb": memory.used / (1024**3),
                "memory_percent": memory.percent,
                "process_memory_mb": process_memory.rss / (1024**2)
            }
            
            self.log(f"📊 메모리 테스트 완료: 전체 {memory.total/(1024**3):.1f}GB, 사용률: {memory.percent:.1f}%")
            
        except Exception as e:
            self.log(f"❌ 메모리 테스트 오류: {e}")
            self.test_results["memory"] = {"error": str(e)}
    
    def test_cpu_usage(self):
        """CPU 사용량 테스트"""
        self.log("⚡ CPU 사용량 테스트 시작")
        
        try:
            # CPU 사용률 측정 (5초간)
            cpu_percentages = []
            for _ in range(5):
                cpu_percentages.append(psutil.cpu_percent(interval=1))
            
            avg_cpu = sum(cpu_percentages) / len(cpu_percentages)
            max_cpu = max(cpu_percentages)
            
            self.test_results["cpu"] = {
                "average_cpu_percent": avg_cpu,
                "max_cpu_percent": max_cpu,
                "cpu_cores": psutil.cpu_count(),
                "cpu_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else 0
            }
            
            self.log(f"📊 CPU 테스트 완료: 평균 {avg_cpu:.1f}%, 최대 {max_cpu:.1f}%")
            
        except Exception as e:
            self.log(f"❌ CPU 테스트 오류: {e}")
            self.test_results["cpu"] = {"error": str(e)}
    
    def test_concurrent_requests(self):
        """동시 요청 테스트"""
        self.log("🔄 동시 요청 테스트 시작")
        
        def make_request(url):
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                end_time = time.time()
                return {
                    "url": url,
                    "status_code": response.status_code,
                    "response_time": (end_time - start_time) * 1000,
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "url": url,
                    "error": str(e),
                    "success": False
                }
        
        # 동시 요청 테스트
        urls = [
            f"{self.base_url}/",
            f"{self.base_url}/api/v1/posts",
            f"{self.base_url}/api/v1/keywords",
            f"{self.base_url}/api/v1/stats/dashboard"
        ] * 3  # 각 URL을 3번씩
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, url) for url in urls]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        success_count = sum(1 for r in results if r["success"])
        avg_response_time = sum(r.get("response_time", 0) for r in results) / len(results) if results else 0
        
        self.test_results["concurrent_requests"] = {
            "total_requests": len(urls),
            "success_count": success_count,
            "success_rate": (success_count / len(urls)) * 100,
            "total_time": total_time,
            "requests_per_second": len(urls) / total_time,
            "average_response_time": avg_response_time,
            "details": results
        }
        
        self.log(f"📊 동시 요청 테스트 완료: {success_count}/{len(urls)} 성공, {len(urls)/total_time:.1f} req/s")
    
    def test_file_system(self):
        """파일 시스템 테스트"""
        self.log("📁 파일 시스템 테스트 시작")
        
        try:
            # 주요 파일 및 디렉토리 확인
            files_to_check = [
                "news_archive.db",
                "api_usage.json",
                "update_history.json",
                "crawling_stats.json",
                "site_crawler_configs.json",
                "synonyms.json"
            ]
            
            file_stats = {}
            total_size = 0
            
            for file_path in files_to_check:
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    file_stats[file_path] = {
                        "exists": True,
                        "size_bytes": size,
                        "size_kb": size / 1024,
                        "modified": modified_time.isoformat()
                    }
                    total_size += size
                else:
                    file_stats[file_path] = {"exists": False}
            
            # 로그 디렉토리 확인
            log_dir = "logs"
            log_files = []
            if os.path.exists(log_dir):
                for file in os.listdir(log_dir):
                    if file.endswith('.log'):
                        file_path = os.path.join(log_dir, file)
                        size = os.path.getsize(file_path)
                        log_files.append({
                            "name": file,
                            "size_bytes": size,
                            "size_kb": size / 1024
                        })
            
            self.test_results["file_system"] = {
                "total_files_checked": len(files_to_check),
                "existing_files": sum(1 for f in file_stats.values() if f.get("exists", False)),
                "total_size_bytes": total_size,
                "total_size_kb": total_size / 1024,
                "log_files_count": len(log_files),
                "file_stats": file_stats,
                "log_files": log_files
            }
            
            self.log(f"📊 파일 시스템 테스트 완료: {len(files_to_check)}개 파일, 총 크기: {total_size/1024:.2f}KB")
            
        except Exception as e:
            self.log(f"❌ 파일 시스템 테스트 오류: {e}")
            self.test_results["file_system"] = {"error": str(e)}
    
    def test_error_handling(self):
        """에러 처리 테스트"""
        self.log("⚠️ 에러 처리 테스트 시작")
        
        error_tests = [
            ("/api/v1/nonexistent", 404),
            ("/api/v1/posts?limit=invalid", 422),
            ("/api/v1/system/invalid", 404)
        ]
        
        results = []
        
        for url, expected_status in error_tests:
            try:
                response = requests.get(f"{self.base_url}{url}", timeout=5)
                results.append({
                    "url": url,
                    "expected_status": expected_status,
                    "actual_status": response.status_code,
                    "correct": response.status_code == expected_status
                })
            except Exception as e:
                results.append({
                    "url": url,
                    "expected_status": expected_status,
                    "error": str(e),
                    "correct": False
                })
        
        correct_count = sum(1 for r in results if r["correct"])
        
        self.test_results["error_handling"] = {
            "total_tests": len(error_tests),
            "correct_count": correct_count,
            "success_rate": (correct_count / len(error_tests)) * 100,
            "details": results
        }
        
        self.log(f"📊 에러 처리 테스트 완료: {correct_count}/{len(error_tests)} 성공")
    
    def generate_optimization_report(self):
        """최적화 리포트 생성"""
        self.log("📋 최적화 리포트 생성")
        
        total_time = time.time() - self.start_time
        
        # 성능 점수 계산
        api_score = self.test_results.get("api_endpoints", {}).get("success_rate", 0)
        db_score = 100 if self.test_results.get("database", {}).get("table_count", 0) > 0 else 0
        memory_score = 100 - self.test_results.get("memory", {}).get("memory_percent", 100)
        cpu_score = 100 - self.test_results.get("cpu", {}).get("average_cpu_percent", 100)
        concurrent_score = self.test_results.get("concurrent_requests", {}).get("success_rate", 0)
        error_score = self.test_results.get("error_handling", {}).get("success_rate", 0)
        
        overall_score = (api_score + db_score + memory_score + cpu_score + concurrent_score + error_score) / 6
        
        report = {
            "test_summary": {
                "total_test_time": total_time,
                "overall_score": overall_score,
                "test_timestamp": datetime.now().isoformat()
            },
            "performance_metrics": {
                "api_success_rate": api_score,
                "database_health": db_score,
                "memory_efficiency": memory_score,
                "cpu_efficiency": cpu_score,
                "concurrent_performance": concurrent_score,
                "error_handling": error_score
            },
            "detailed_results": self.test_results,
            "recommendations": self.generate_recommendations()
        }
        
        # 리포트 저장
        with open("system_optimization_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log(f"📊 최적화 리포트 생성 완료: 전체 점수 {overall_score:.1f}/100")
        
        return report
    
    def generate_recommendations(self):
        """최적화 권장사항 생성"""
        recommendations = []
        
        # API 성능 권장사항
        api_results = self.test_results.get("api_endpoints", {})
        if api_results.get("average_response_time", 0) > 500:
            recommendations.append("API 응답시간이 500ms를 초과합니다. 캐싱 전략을 검토하세요.")
        
        # 메모리 사용량 권장사항
        memory_results = self.test_results.get("memory", {})
        if memory_results.get("memory_percent", 0) > 80:
            recommendations.append("메모리 사용률이 80%를 초과합니다. 메모리 최적화가 필요합니다.")
        
        # CPU 사용량 권장사항
        cpu_results = self.test_results.get("cpu", {})
        if cpu_results.get("average_cpu_percent", 0) > 70:
            recommendations.append("CPU 사용률이 70%를 초과합니다. CPU 집약적 작업을 최적화하세요.")
        
        # 데이터베이스 권장사항
        db_results = self.test_results.get("database", {})
        if db_results.get("db_size_kb", 0) > 10240:  # 10MB
            recommendations.append("데이터베이스 크기가 10MB를 초과합니다. 정리 작업을 고려하세요.")
        
        # 동시 요청 권장사항
        concurrent_results = self.test_results.get("concurrent_requests", {})
        if concurrent_results.get("success_rate", 0) < 95:
            recommendations.append("동시 요청 성공률이 95% 미만입니다. 서버 리소스를 확인하세요.")
        
        if not recommendations:
            recommendations.append("시스템이 최적 상태입니다. 현재 설정을 유지하세요.")
        
        return recommendations
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        self.log("🚀 전체 시스템 최적화 테스트 시작")
        print("=" * 60)
        
        try:
            # 1. API 엔드포인트 테스트
            self.test_api_endpoints()
            
            # 2. 데이터베이스 성능 테스트
            self.test_database_performance()
            
            # 3. 메모리 사용량 테스트
            self.test_memory_usage()
            
            # 4. CPU 사용량 테스트
            self.test_cpu_usage()
            
            # 5. 동시 요청 테스트
            self.test_concurrent_requests()
            
            # 6. 파일 시스템 테스트
            self.test_file_system()
            
            # 7. 에러 처리 테스트
            self.test_error_handling()
            
            # 8. 최적화 리포트 생성
            report = self.generate_optimization_report()
            
            # 9. 결과 출력
            self.print_summary(report)
            
        except Exception as e:
            self.log(f"❌ 테스트 실행 중 오류 발생: {e}")
    
    def print_summary(self, report):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("🎯 전체 시스템 최적화 테스트 결과")
        print("=" * 60)
        
        summary = report["test_summary"]
        metrics = report["performance_metrics"]
        
        print(f"📊 전체 점수: {summary['overall_score']:.1f}/100")
        print(f"⏱️  테스트 시간: {summary['total_test_time']:.2f}초")
        print(f"📅 테스트 일시: {summary['test_timestamp']}")
        
        print("\n📈 성능 지표:")
        print(f"   API 성공률: {metrics['api_success_rate']:.1f}%")
        print(f"   데이터베이스 상태: {metrics['database_health']:.1f}%")
        print(f"   메모리 효율성: {metrics['memory_efficiency']:.1f}%")
        print(f"   CPU 효율성: {metrics['cpu_efficiency']:.1f}%")
        print(f"   동시 처리 성능: {metrics['concurrent_performance']:.1f}%")
        print(f"   에러 처리: {metrics['error_handling']:.1f}%")
        
        print("\n💡 최적화 권장사항:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"   {i}. {rec}")
        
        print(f"\n📄 상세 리포트: system_optimization_report.json")
        print("=" * 60)

def main():
    """메인 함수"""
    tester = SystemOptimizationTest()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 