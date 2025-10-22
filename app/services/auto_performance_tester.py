# app/services/auto_performance_tester.py

import asyncio
import time
import json
import threading
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import random
import subprocess
import sys
import os

from ..utils.logger import setup_logger

logger = setup_logger(__name__, "auto_performance_tester.log", level=logging.DEBUG)

class AutoPerformanceTester:
    """백그라운드 자동 성능 테스트 시스템"""
    
    def __init__(self):
        self.is_running = False
        self.test_thread = None
        self.base_url = "http://localhost:8000"
        self.test_interval = 600  # 10분마다 테스트
        self.test_results = []
        self.max_results = 144  # 24시간 (10분 간격)
        
        # 테스트 결과 파일
        self.results_file = Path("auto_performance_test_results.json")
        self.load_test_results()
    
    def start_auto_testing(self):
        """자동 성능 테스트 시작"""
        if self.is_running:
            logger.warning("자동 성능 테스트가 이미 실행 중입니다.")
            return
        
        self.is_running = True
        self.test_thread = threading.Thread(target=self._test_loop, daemon=True)
        self.test_thread.start()
        logger.info("백그라운드 자동 성능 테스트가 시작되었습니다.")
    
    def stop_auto_testing(self):
        """자동 성능 테스트 중지"""
        self.is_running = False
        if self.test_thread:
            self.test_thread.join(timeout=5)
        logger.info("백그라운드 자동 성능 테스트가 중지되었습니다.")
    
    def _test_loop(self):
        """테스트 루프 - 간단한 API 테스트만 실행"""
        while self.is_running:
            try:
                logger.info("자동 성능 테스트 사이클 시작")
                
                # 기본 API 테스트만 실행
                api_results = self._run_simple_api_tests()
                
                # 결과 저장
                test_record = {
                    "timestamp": datetime.now().isoformat(),
                    "api_tests": api_results,
                    "summary": self._generate_simple_summary(api_results)
                }
                
                self._add_test_result(test_record)
                self._save_test_results()
                
                # 테스트 결과 로깅
                self._log_test_summary(test_record)
                
                # 대기
                time.sleep(self.test_interval)
                
            except Exception as e:
                logger.error(f"자동 성능 테스트 중 오류 발생: {e}")
                time.sleep(60)  # 오류 시 1분 대기
    
    def _run_simple_api_tests(self) -> Dict[str, Any]:
        """간단한 API 성능 테스트 실행"""
        logger.info("API 성능 테스트 시작")
        
        endpoints = [
            "/api/v1/posts",
            "/api/v1/keywords", 
            "/api/v1/stats/dashboard"
        ]
        
        results = {
            "endpoints": {},
            "overall": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "average_response_time": 0
            }
        }
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                start_time = time.time()
                response = requests.get(url, timeout=30)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # ms로 변환
                
                endpoint_result = {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "success": response.status_code == 200
                }
                
                results["endpoints"][endpoint] = endpoint_result
                results["overall"]["total_requests"] += 1
                
                if response.status_code == 200:
                    results["overall"]["successful_requests"] += 1
                else:
                    results["overall"]["failed_requests"] += 1
                    
            except Exception as e:
                endpoint_result = {
                    "status_code": None,
                    "response_time": None,
                    "success": False,
                    "error": str(e)
                }
                results["endpoints"][endpoint] = endpoint_result
                results["overall"]["total_requests"] += 1
                results["overall"]["failed_requests"] += 1
                logger.warning(f"엔드포인트 {endpoint} 테스트 실패: {e}")
        
        # 평균 응답 시간 계산
        response_times = []
        for data in results["endpoints"].values():
            response_time = data.get("response_time")
            if response_time is not None:
                response_times.append(response_time)
        
        if response_times:
            results["overall"]["average_response_time"] = sum(response_times) / len(response_times)
        
        logger.info(f"API 테스트 완료: {results['overall']['successful_requests']}/{results['overall']['total_requests']} 성공")
        return results
    
    def _generate_simple_summary(self, api_results: Dict[str, Any]) -> Dict[str, Any]:
        """간단한 테스트 결과 요약 생성"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "tests_run": ["api"],
            "issues": []
        }
        
        if api_results:
            total_requests = api_results["overall"]["total_requests"]
            successful_requests = api_results["overall"]["successful_requests"]
            
            if total_requests > 0:
                success_rate = (successful_requests / total_requests) * 100
                if success_rate < 95:
                    summary["issues"].append("API 성공률이 95% 미만")
                    summary["overall_status"] = "warning"
                
                if success_rate < 80:
                    summary["overall_status"] = "error"
        
        return summary
    
    def _add_test_result(self, result: Dict[str, Any]):
        """테스트 결과 추가"""
        self.test_results.append(result)
        
        # 최대 개수 제한
        if len(self.test_results) > self.max_results:
            self.test_results = self.test_results[-self.max_results:]
    
    def _save_test_results(self):
        """테스트 결과 저장"""
        try:
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"테스트 결과 저장 실패: {e}")
    
    def load_test_results(self):
        """테스트 결과 로드"""
        try:
            if self.results_file.exists():
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    self.test_results = json.load(f)
                logger.info(f"테스트 결과 로드 완료: {len(self.test_results)}개 레코드")
            else:
                self.test_results = []
        except Exception as e:
            logger.error(f"테스트 결과 로드 실패: {e}")
            self.test_results = []
    
    def _log_test_summary(self, test_record: Dict[str, Any]):
        """테스트 결과 로깅"""
        summary = test_record.get("summary", {})
        status = summary.get("overall_status", "unknown")
        issues = summary.get("issues", [])
        
        logger.info(f"자동 성능 테스트 완료 - 상태: {status}")
        
        if issues:
            for issue in issues:
                logger.warning(f"성능 테스트 이슈: {issue}")
        
        # API 테스트 결과 로깅
        if test_record.get("api_tests"):
            api_overall = test_record["api_tests"]["overall"]
            total_requests = api_overall["total_requests"]
            successful_requests = api_overall["successful_requests"]
            
            if total_requests > 0:
                success_rate = (successful_requests / total_requests) * 100
                avg_time = api_overall["average_response_time"]
                logger.info(f"API 테스트 - 성공률: {success_rate:.1f}%, 평균 응답시간: {avg_time:.1f}ms")
    
    def get_test_summary(self, hours: int = 24) -> Dict[str, Any]:
        """테스트 결과 요약 반환"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_results = [
            result for result in self.test_results
            if datetime.fromisoformat(result["timestamp"]) > cutoff_time
        ]
        
        if not recent_results:
            return {"message": "최근 테스트 결과가 없습니다."}
        
        # 통계 계산
        total_tests = len(recent_results)
        healthy_tests = sum(1 for r in recent_results if r.get("summary", {}).get("overall_status") == "healthy")
        warning_tests = sum(1 for r in recent_results if r.get("summary", {}).get("overall_status") == "warning")
        error_tests = sum(1 for r in recent_results if r.get("summary", {}).get("overall_status") == "error")
        
        return {
            "period_hours": hours,
            "total_tests": total_tests,
            "healthy_tests": healthy_tests,
            "warning_tests": warning_tests,
            "error_tests": error_tests,
            "health_rate": (healthy_tests / total_tests) * 100 if total_tests > 0 else 0,
            "latest_result": recent_results[-1] if recent_results else None
        }

# 전역 인스턴스
auto_performance_tester = AutoPerformanceTester() 