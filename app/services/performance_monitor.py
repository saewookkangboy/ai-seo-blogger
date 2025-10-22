# app/services/performance_monitor.py

import time
import json
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import psutil
import asyncio
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class PerformanceMonitor:
    """시스템 성능 모니터링 클래스"""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.performance_data = []
        self.max_data_points = 1000
        self.monitor_interval = 5  # 5초마다 체크
        
        # 성능 임계값
        self.cpu_threshold = 80.0  # CPU 사용률 80% 이상 시 경고
        self.memory_threshold = 85.0  # 메모리 사용률 85% 이상 시 경고
        self.disk_threshold = 90.0  # 디스크 사용률 90% 이상 시 경고
        
        # API 응답 시간 추적
        self.api_response_times = {}
        self.api_error_counts = {}
        
        # 콘텐츠 생성 성능 추적
        self.content_generation_times = []
        self.content_generation_errors = []
        
        # 시스템 상태
        self.system_status = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "network_io": {"bytes_sent": 0, "bytes_recv": 0},
            "last_update": None
        }
    
    def start_monitoring(self):
        """성능 모니터링 시작"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("성능 모니터링이 시작되었습니다.")
    
    def stop_monitoring(self):
        """성능 모니터링 중지"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("성능 모니터링이 중지되었습니다.")
    
    def _monitor_loop(self):
        """모니터링 루프"""
        while self.monitoring:
            try:
                self._collect_system_metrics()
                self._check_thresholds()
                self._save_performance_data()
                time.sleep(self.monitor_interval)
            except Exception as e:
                logger.error(f"성능 모니터링 중 오류 발생: {e}")
                time.sleep(self.monitor_interval)
    
    def _collect_system_metrics(self):
        """시스템 메트릭 수집"""
        try:
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 메모리 사용률
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 디스크 사용률
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # 네트워크 I/O
            network = psutil.net_io_counters()
            
            # 시스템 상태 업데이트
            self.system_status.update({
                "cpu_usage": cpu_percent,
                "memory_usage": memory_percent,
                "disk_usage": disk_percent,
                "network_io": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv
                },
                "last_update": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"시스템 메트릭 수집 중 오류: {e}")
    
    def _check_thresholds(self):
        """임계값 체크 및 경고"""
        warnings = []
        
        if self.system_status["cpu_usage"] > self.cpu_threshold:
            warnings.append(f"CPU 사용률이 높습니다: {self.system_status['cpu_usage']:.1f}%")
        
        if self.system_status["memory_usage"] > self.memory_threshold:
            warnings.append(f"메모리 사용률이 높습니다: {self.system_status['memory_usage']:.1f}%")
        
        if self.system_status["disk_usage"] > self.disk_threshold:
            warnings.append(f"디스크 사용률이 높습니다: {self.system_status['disk_usage']:.1f}%")
        
        if warnings:
            logger.warning(f"성능 경고: {'; '.join(warnings)}")
    
    def _save_performance_data(self):
        """성능 데이터 저장"""
        data_point = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": self.system_status["cpu_usage"],
            "memory_usage": self.system_status["memory_usage"],
            "disk_usage": self.system_status["disk_usage"],
            "network_io": self.system_status["network_io"]
        }
        
        self.performance_data.append(data_point)
        
        # 데이터 포인트 수 제한
        if len(self.performance_data) > self.max_data_points:
            self.performance_data = self.performance_data[-self.max_data_points:]
    
    def record_api_response_time(self, api_name: str, response_time: float):
        """API 응답 시간 기록"""
        if api_name not in self.api_response_times:
            self.api_response_times[api_name] = []
        
        self.api_response_times[api_name].append(response_time)
        
        # 최근 100개만 유지
        if len(self.api_response_times[api_name]) > 100:
            self.api_response_times[api_name] = self.api_response_times[api_name][-100:]
    
    def record_api_error(self, api_name: str):
        """API 오류 기록"""
        if api_name not in self.api_error_counts:
            self.api_error_counts[api_name] = 0
        
        self.api_error_counts[api_name] += 1
    
    def record_content_generation_time(self, generation_time: float):
        """콘텐츠 생성 시간 기록"""
        self.content_generation_times.append(generation_time)
        
        # 최근 100개만 유지
        if len(self.content_generation_times) > 100:
            self.content_generation_times = self.content_generation_times[-100:]
    
    def record_content_generation_error(self, error: str):
        """콘텐츠 생성 오류 기록"""
        self.content_generation_errors.append({
            "timestamp": datetime.now().isoformat(),
            "error": error
        })
        
        # 최근 50개만 유지
        if len(self.content_generation_errors) > 50:
            self.content_generation_errors = self.content_generation_errors[-50:]
    
    def get_system_status(self) -> Dict[str, Any]:
        """현재 시스템 상태 반환"""
        return self.system_status.copy()
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """성능 요약 정보 반환"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 최근 데이터 필터링
        recent_data = [
            data for data in self.performance_data
            if datetime.fromisoformat(data["timestamp"]) > cutoff_time
        ]
        
        if not recent_data:
            return {"error": "최근 데이터가 없습니다."}
        
        # 평균값 계산
        avg_cpu = sum(d["cpu_usage"] for d in recent_data) / len(recent_data)
        avg_memory = sum(d["memory_usage"] for d in recent_data) / len(recent_data)
        avg_disk = sum(d["disk_usage"] for d in recent_data) / len(recent_data)
        
        # 최대값 계산
        max_cpu = max(d["cpu_usage"] for d in recent_data)
        max_memory = max(d["memory_usage"] for d in recent_data)
        max_disk = max(d["disk_usage"] for d in recent_data)
        
        # API 응답 시간 통계
        api_stats = {}
        for api_name, times in self.api_response_times.items():
            if times:
                api_stats[api_name] = {
                    "avg_response_time": sum(times) / len(times),
                    "max_response_time": max(times),
                    "min_response_time": min(times),
                    "total_calls": len(times)
                }
        
        # 콘텐츠 생성 통계
        content_stats = {}
        if self.content_generation_times:
            content_stats = {
                "avg_generation_time": sum(self.content_generation_times) / len(self.content_generation_times),
                "max_generation_time": max(self.content_generation_times),
                "min_generation_time": min(self.content_generation_times),
                "total_generations": len(self.content_generation_times),
                "recent_errors": len([e for e in self.content_generation_errors 
                                    if datetime.fromisoformat(e["timestamp"]) > cutoff_time])
            }
        
        return {
            "period_hours": hours,
            "data_points": len(recent_data),
            "system_metrics": {
                "cpu": {"average": avg_cpu, "maximum": max_cpu},
                "memory": {"average": avg_memory, "maximum": max_memory},
                "disk": {"average": avg_disk, "maximum": max_disk}
            },
            "api_performance": api_stats,
            "content_generation": content_stats,
            "current_status": self.system_status
        }
    
    def get_recent_performance_data(self, limit: int = 100) -> List[Dict[str, Any]]:
        """최근 성능 데이터 반환"""
        return self.performance_data[-limit:] if self.performance_data else []
    
    def export_performance_data(self) -> str:
        """성능 데이터를 JSON 파일로 내보내기"""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "performance_data": self.performance_data,
            "api_response_times": self.api_response_times,
            "api_error_counts": self.api_error_counts,
            "content_generation_times": self.content_generation_times,
            "content_generation_errors": self.content_generation_errors,
            "system_status": self.system_status
        }
        
        filename = f"performance_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(os.getcwd(), filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            logger.info(f"성능 데이터가 {filename}에 저장되었습니다.")
            return filename
        except Exception as e:
            logger.error(f"성능 데이터 내보내기 실패: {e}")
            return None

# 전역 성능 모니터 인스턴스
performance_monitor = PerformanceMonitor()

# 자동 시작
performance_monitor.start_monitoring() 