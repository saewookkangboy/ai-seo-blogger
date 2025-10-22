"""
크롤링 모니터링 시스템
크롤링 성공률을 추적하고 문제 사이트를 식별합니다.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
from collections import defaultdict, Counter
import threading

logger = logging.getLogger(__name__)

class CrawlingMonitor:
    """크롤링 성공률 모니터링"""
    
    def __init__(self, stats_file: str = "crawling_stats.json"):
        self.stats_file = Path(stats_file)
        self.stats = self._load_stats()
        self.lock = threading.Lock()
        self.monitoring = False
        self.monitor_thread = None
    
    def _load_stats(self) -> Dict[str, Any]:
        """통계 데이터를 로드합니다."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Counter 객체 복원
                    for domain, stats in data.get("site_stats", {}).items():
                        if "common_errors" in stats and isinstance(stats["common_errors"], dict):
                            stats["common_errors"] = Counter(stats["common_errors"])
                    
                    return data
            except Exception as e:
                logger.error(f"통계 파일 로드 실패: {e}")
        
        return {
            "total_attempts": 0,
            "successful_crawls": 0,
            "failed_crawls": 0,
            "site_stats": {},
            "recent_attempts": [],
            "problem_sites": [],
            "performance_metrics": {
                "avg_response_time": 0,
                "success_rate_trend": [],
                "top_performing_sites": [],
                "worst_performing_sites": []
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_stats(self):
        """통계 데이터를 저장합니다."""
        try:
            with self.lock:
                # Counter 객체를 딕셔너리로 변환
                save_data = self.stats.copy()
                for domain, stats in save_data.get("site_stats", {}).items():
                    if "common_errors" in stats and isinstance(stats["common_errors"], Counter):
                        stats["common_errors"] = dict(stats["common_errors"])
                
                save_data["last_updated"] = datetime.now().isoformat()
                with open(self.stats_file, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"통계 파일 저장 실패: {e}")
    
    def record_attempt(self, url: str, success: bool, content_length: int = 0, error: str = "", response_time: float = 0):
        """크롤링 시도를 기록합니다."""
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc.lower()
        timestamp = datetime.now().isoformat()
        
        with self.lock:
            # 전체 통계 업데이트
            self.stats["total_attempts"] += 1
            if success:
                self.stats["successful_crawls"] += 1
            else:
                self.stats["failed_crawls"] += 1
            
            # 사이트별 통계 업데이트
            if domain not in self.stats["site_stats"]:
                self.stats["site_stats"][domain] = {
                    "total_attempts": 0,
                    "successful_crawls": 0,
                    "failed_crawls": 0,
                    "avg_content_length": 0,
                    "avg_response_time": 0,
                    "last_success": None,
                    "last_failure": None,
                    "common_errors": Counter(),
                    "response_times": [],
                    "success_rate": 0.0
                }
            
            site_stat = self.stats["site_stats"][domain]
            
            # 기존 데이터에 response_times 필드가 없는 경우 추가
            if "response_times" not in site_stat:
                site_stat["response_times"] = []
            if "success_rate" not in site_stat:
                site_stat["success_rate"] = 0.0
            
            site_stat["total_attempts"] += 1
            
            if success:
                site_stat["successful_crawls"] += 1
                site_stat["last_success"] = timestamp
                if content_length > 0:
                    # 평균 콘텐츠 길이 업데이트
                    total_length = site_stat["avg_content_length"] * (site_stat["successful_crawls"] - 1) + content_length
                    site_stat["avg_content_length"] = total_length / site_stat["successful_crawls"]
            else:
                site_stat["failed_crawls"] += 1
                site_stat["last_failure"] = timestamp
                if error:
                    site_stat["common_errors"][error] += 1
            
            # 응답 시간 기록
            if response_time > 0:
                site_stat["response_times"].append(response_time)
                if len(site_stat["response_times"]) > 100:  # 최근 100개만 유지
                    site_stat["response_times"] = site_stat["response_times"][-100:]
                site_stat["avg_response_time"] = sum(site_stat["response_times"]) / len(site_stat["response_times"])
            
            # 성공률 계산
            site_stat["success_rate"] = site_stat["successful_crawls"] / site_stat["total_attempts"]
            
            # 최근 시도 기록
            attempt_record = {
                "url": url,
                "domain": domain,
                "success": success,
                "content_length": content_length,
                "error": error,
                "response_time": response_time,
                "timestamp": timestamp
            }
            
            self.stats["recent_attempts"].append(attempt_record)
            
            # 최근 시도는 최대 1000개만 유지
            if len(self.stats["recent_attempts"]) > 1000:
                self.stats["recent_attempts"] = self.stats["recent_attempts"][-1000:]
            
            # 성능 지표 업데이트
            try:
                self._update_performance_metrics()
            except Exception as e:
                logger.error(f"성능 지표 업데이트 오류: {e}")
            
            # 문제 사이트 식별
            try:
                self._identify_problem_sites()
            except Exception as e:
                logger.error(f"문제 사이트 식별 오류: {e}")
            
            # 주기적으로 저장
            if self.stats["total_attempts"] % 10 == 0:  # 10번마다 저장
                self._save_stats()
    
    def _update_performance_metrics(self):
        """성능 지표를 업데이트합니다."""
        if not self.stats["site_stats"]:
            return
        
        # 전체 평균 응답 시간
        all_response_times = []
        for site_stat in self.stats["site_stats"].values():
            if "response_times" in site_stat and site_stat["response_times"]:
                all_response_times.extend(site_stat["response_times"])
        
        if all_response_times:
            self.stats["performance_metrics"]["avg_response_time"] = sum(all_response_times) / len(all_response_times)
        
        # 성공률 기준으로 사이트 정렬
        sites_with_stats = []
        for domain, stats in self.stats["site_stats"].items():
            if stats["total_attempts"] >= 3:  # 최소 3번 시도한 사이트만
                sites_with_stats.append({
                    "domain": domain,
                    "success_rate": stats.get("success_rate", 0.0),
                    "total_attempts": stats["total_attempts"],
                    "avg_response_time": stats.get("avg_response_time", 0.0)
                })
        
        # 성공률 순으로 정렬
        sites_with_stats.sort(key=lambda x: x["success_rate"], reverse=True)
        
        # 상위/하위 성능 사이트
        self.stats["performance_metrics"]["top_performing_sites"] = sites_with_stats[:5]
        self.stats["performance_metrics"]["worst_performing_sites"] = sites_with_stats[-5:] if len(sites_with_stats) >= 5 else sites_with_stats
        
        # 성공률 트렌드 (최근 10번 시도 기준)
        recent_attempts = self.stats["recent_attempts"][-10:]
        if recent_attempts:
            recent_success = sum(1 for attempt in recent_attempts if attempt["success"])
            recent_success_rate = recent_success / len(recent_attempts)
            self.stats["performance_metrics"]["success_rate_trend"].append({
                "timestamp": datetime.now().isoformat(),
                "success_rate": recent_success_rate,
                "attempts": len(recent_attempts)
            })
            
            # 트렌드는 최근 50개만 유지
            if len(self.stats["performance_metrics"]["success_rate_trend"]) > 50:
                self.stats["performance_metrics"]["success_rate_trend"] = self.stats["performance_metrics"]["success_rate_trend"][-50:]
    
    def _identify_problem_sites(self):
        """문제 사이트를 식별합니다."""
        problem_sites = []
        
        for domain, stats in self.stats["site_stats"].items():
            if stats["total_attempts"] >= 3:  # 최소 3번 시도한 사이트만
                success_rate = stats.get("success_rate", 0.0)
                
                # 성공률이 50% 미만이거나 최근 실패가 많은 사이트
                if success_rate < 0.5 or (stats["failed_crawls"] >= 3 and success_rate < 0.7):
                    problem_sites.append({
                        "domain": domain,
                        "success_rate": success_rate,
                        "total_attempts": stats["total_attempts"],
                        "failed_attempts": stats["failed_crawls"],
                        "last_failure": stats["last_failure"],
                        "common_errors": dict(stats["common_errors"].most_common(3))
                    })
        
        # 실패 횟수 순으로 정렬
        problem_sites.sort(key=lambda x: x["failed_attempts"], reverse=True)
        self.stats["problem_sites"] = problem_sites
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """전체 통계를 반환합니다."""
        with self.lock:
            total_attempts = self.stats["total_attempts"]
            successful_crawls = self.stats["successful_crawls"]
            failed_crawls = self.stats["failed_crawls"]
            
            success_rate = successful_crawls / total_attempts if total_attempts > 0 else 0
            
            return {
                "success_rate": round(success_rate, 4),
                "total_attempts": total_attempts,
                "successful_crawls": successful_crawls,
                "failed_crawls": failed_crawls,
                "avg_response_time": self.stats["performance_metrics"]["avg_response_time"],
                "last_updated": self.stats["last_updated"]
            }
    
    def get_site_stats(self, domain: str) -> Optional[Dict[str, Any]]:
        """특정 사이트의 통계를 반환합니다."""
        with self.lock:
            return self.stats["site_stats"].get(domain)
    
    def get_problem_sites(self) -> List[Dict[str, Any]]:
        """문제 사이트 목록을 반환합니다."""
        with self.lock:
            return self.stats["problem_sites"]
    
    def get_recent_attempts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """최근 시도 목록을 반환합니다."""
        with self.lock:
            return self.stats["recent_attempts"][-limit:]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 지표를 반환합니다."""
        with self.lock:
            return self.stats["performance_metrics"]
    
    def generate_report(self) -> str:
        """크롤링 리포트를 생성합니다."""
        with self.lock:
            overall_stats = self.get_overall_stats()
            problem_sites = self.get_problem_sites()
            performance_metrics = self.get_performance_metrics()
            
            report = f"""
📊 크롤링 성공률 리포트
==================================================

📈 전체 통계:
  • 총 시도: {overall_stats['total_attempts']}회
  • 성공: {overall_stats['successful_crawls']}회
  • 실패: {overall_stats['failed_crawls']}회
  • 성공률: {overall_stats['success_rate']:.1%}
  • 평균 응답 시간: {overall_stats['avg_response_time']:.2f}초

🚨 문제 사이트 ({len(problem_sites)}개):
"""
            
            for site in problem_sites:
                report += f"""
  • {site['domain']}
    - 성공률: {site['success_rate']:.1%}
    - 총 시도: {site['total_attempts']}회
    - 실패: {site['failed_attempts']}회
    - 주요 오류: {', '.join(site['common_errors'].keys())}
"""
            
            if performance_metrics["top_performing_sites"]:
                report += f"""
🏆 상위 성능 사이트:
"""
                for site in performance_metrics["top_performing_sites"]:
                    report += f"  • {site['domain']}: {site['success_rate']:.1%} 성공률\n"
            
            report += f"""
📅 마지막 업데이트: {self.stats['last_updated']}
"""
            
            return report
    
    def cleanup_old_data(self, days: int = 30):
        """오래된 데이터를 정리합니다."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.lock:
            # 최근 시도에서 오래된 데이터 제거
            self.stats["recent_attempts"] = [
                attempt for attempt in self.stats["recent_attempts"]
                if datetime.fromisoformat(attempt["timestamp"]) > cutoff_date
            ]
            
            # 성능 지표 트렌드에서 오래된 데이터 제거
            self.stats["performance_metrics"]["success_rate_trend"] = [
                trend for trend in self.stats["performance_metrics"]["success_rate_trend"]
                if datetime.fromisoformat(trend["timestamp"]) > cutoff_date
            ]
            
            # 응답 시간 데이터 정리 (최근 100개만 유지)
            for site_stat in self.stats["site_stats"].values():
                if "response_times" in site_stat and len(site_stat["response_times"]) > 100:
                    site_stat["response_times"] = site_stat["response_times"][-100:]
            
            self._save_stats()
    
    def start_monitoring(self):
        """모니터링을 시작합니다."""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("크롤링 모니터링 시작")
    
    def stop_monitoring(self):
        """모니터링을 중지합니다."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("크롤링 모니터링 중지")
    
    def _monitor_loop(self):
        """모니터링 루프"""
        while self.monitoring:
            try:
                # 주기적으로 데이터 정리
                self.cleanup_old_data()
                
                # 성능 지표 업데이트
                self._update_performance_metrics()
                
                # 통계 저장
                self._save_stats()
                
                time.sleep(300)  # 5분마다 실행
            except Exception as e:
                logger.error(f"모니터링 루프 오류: {e}")
                time.sleep(60)  # 오류 시 1분 대기

# 전역 인스턴스
crawling_monitor = CrawlingMonitor() 