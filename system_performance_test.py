#!/usr/bin/env python3
"""
시스템 리소스 성능 테스트 스크립트
"""

import psutil
import time
import json
import requests
from datetime import datetime
import threading

def monitor_system_resources(duration=60, interval=5):
    """시스템 리소스 모니터링"""
    print(f"🔍 시스템 리소스 모니터링 시작 ({duration}초, {interval}초 간격)")
    
    monitoring_data = []
    start_time = time.time()
    
    while time.time() - start_time < duration:
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 메모리 사용률
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_gb = memory.used / (1024**3)
        memory_total_gb = memory.total / (1024**3)
        
        # 디스크 사용률
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        
        # 네트워크 I/O
        network = psutil.net_io_counters()
        
        # 프로세스 정보
        processes = len(psutil.pids())
        
        # Python 프로세스 찾기
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if 'python' in proc.info['name'].lower():
                    python_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # 현재 시간
        timestamp = datetime.now().isoformat()
        
        data_point = {
            "timestamp": timestamp,
            "cpu_percent": cpu_percent,
            "memory": {
                "percent": memory_percent,
                "used_gb": round(memory_used_gb, 2),
                "total_gb": round(memory_total_gb, 2)
            },
            "disk": {
                "percent": disk_percent,
                "used_gb": round(disk_used_gb, 2),
                "total_gb": round(disk_total_gb, 2)
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv
            },
            "processes": {
                "total": processes,
                "python_count": len(python_processes),
                "python_processes": python_processes
            }
        }
        
        monitoring_data.append(data_point)
        
        # 실시간 출력
        print(f"⏰ {timestamp.split('T')[1][:8]} | "
              f"CPU: {cpu_percent:5.1f}% | "
              f"RAM: {memory_percent:5.1f}% ({memory_used_gb:5.1f}GB) | "
              f"Disk: {disk_percent:5.1f}% | "
              f"Processes: {processes}")
        
        time.sleep(interval)
    
    return monitoring_data

def stress_test_api(base_url="http://localhost:8000", duration=30):
    """API 스트레스 테스트"""
    print(f"🔥 API 스트레스 테스트 시작 ({duration}초)")
    
    stress_data = []
    start_time = time.time()
    
    def make_request():
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            return {
                "success": response.status_code == 200,
                "response_time": response.elapsed.total_seconds() * 1000,
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response_time": 0
            }
    
    while time.time() - start_time < duration:
        # 동시 요청 생성
        threads = []
        results = []
        
        for i in range(10):  # 10개 동시 요청
            thread = threading.Thread(target=lambda: results.append(make_request()))
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        # 결과 분석
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        if successful_requests:
            avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests)
            max_response_time = max(r['response_time'] for r in successful_requests)
            min_response_time = min(r['response_time'] for r in successful_requests)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        stress_point = {
            "timestamp": datetime.now().isoformat(),
            "total_requests": len(results),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": len(successful_requests) / len(results) * 100 if results else 0,
            "avg_response_time_ms": round(avg_response_time, 2),
            "min_response_time_ms": round(min_response_time, 2),
            "max_response_time_ms": round(max_response_time, 2)
        }
        
        stress_data.append(stress_point)
        
        print(f"📊 요청: {len(results)} | 성공: {len(successful_requests)} | "
              f"평균 응답: {avg_response_time:.2f}ms | "
              f"성공률: {stress_point['success_rate']:.1f}%")
        
        time.sleep(2)
    
    return stress_data

def analyze_performance(monitoring_data, stress_data):
    """성능 데이터 분석"""
    print("\n📈 성능 분석 결과")
    print("=" * 50)
    
    if monitoring_data:
        # CPU 분석
        cpu_values = [d['cpu_percent'] for d in monitoring_data]
        avg_cpu = sum(cpu_values) / len(cpu_values)
        max_cpu = max(cpu_values)
        min_cpu = min(cpu_values)
        
        print(f"🖥️  CPU 사용률:")
        print(f"   평균: {avg_cpu:.1f}%")
        print(f"   최대: {max_cpu:.1f}%")
        print(f"   최소: {min_cpu:.1f}%")
        
        # 메모리 분석
        memory_values = [d['memory']['percent'] for d in monitoring_data]
        avg_memory = sum(memory_values) / len(memory_values)
        max_memory = max(memory_values)
        
        print(f"💾 메모리 사용률:")
        print(f"   평균: {avg_memory:.1f}%")
        print(f"   최대: {max_memory:.1f}%")
        
        # 디스크 분석
        disk_values = [d['disk']['percent'] for d in monitoring_data]
        avg_disk = sum(disk_values) / len(disk_values)
        
        print(f"💿 디스크 사용률: {avg_disk:.1f}%")
    
    if stress_data:
        # API 성능 분석
        success_rates = [d['success_rate'] for d in stress_data]
        response_times = [d['avg_response_time_ms'] for d in stress_data if d['avg_response_time_ms'] > 0]
        
        if success_rates:
            avg_success_rate = sum(success_rates) / len(success_rates)
            print(f"🌐 API 성능:")
            print(f"   평균 성공률: {avg_success_rate:.1f}%")
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            print(f"   평균 응답 시간: {avg_response_time:.2f}ms")
            print(f"   최대 응답 시간: {max_response_time:.2f}ms")
            print(f"   최소 응답 시간: {min_response_time:.2f}ms")
    
    # 성능 등급 평가
    performance_score = 0
    
    if monitoring_data:
        avg_cpu = sum([d['cpu_percent'] for d in monitoring_data]) / len(monitoring_data)
        avg_memory = sum([d['memory']['percent'] for d in monitoring_data]) / len(monitoring_data)
        
        if avg_cpu < 50 and avg_memory < 70:
            performance_score += 40
        elif avg_cpu < 70 and avg_memory < 85:
            performance_score += 30
        else:
            performance_score += 10
    
    if stress_data:
        avg_success_rate = sum([d['success_rate'] for d in stress_data]) / len(stress_data)
        if avg_success_rate > 95:
            performance_score += 40
        elif avg_success_rate > 80:
            performance_score += 30
        else:
            performance_score += 10
    
    if performance_score >= 70:
        grade = "🟢 우수"
    elif performance_score >= 50:
        grade = "🟡 양호"
    elif performance_score >= 30:
        grade = "🟠 보통"
    else:
        grade = "🔴 개선 필요"
    
    print(f"\n🏆 전체 성능 등급: {grade} ({performance_score}/80점)")

def main():
    """메인 함수"""
    print("🚀 시스템 성능 테스트 시작")
    print("=" * 50)
    
    # 시스템 리소스 모니터링 (백그라운드)
    print("1️⃣ 시스템 리소스 모니터링 시작...")
    monitoring_thread = threading.Thread(
        target=lambda: monitor_system_resources(duration=60, interval=5)
    )
    monitoring_thread.start()
    
    # API 스트레스 테스트
    print("2️⃣ API 스트레스 테스트 시작...")
    stress_data = stress_test_api(duration=30)
    
    # 모니터링 완료 대기
    monitoring_thread.join()
    
    # 결과 분석
    analyze_performance([], stress_data)
    
    # 결과 저장
    results = {
        "test_timestamp": datetime.now().isoformat(),
        "stress_test_results": stress_data,
        "summary": {
            "total_stress_requests": sum(d['total_requests'] for d in stress_data),
            "total_successful_requests": sum(d['successful_requests'] for d in stress_data),
            "overall_success_rate": sum(d['success_rate'] for d in stress_data) / len(stress_data) if stress_data else 0
        }
    }
    
    with open('system_performance_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 결과가 'system_performance_test_results.json'에 저장되었습니다.")

if __name__ == "__main__":
    main()
