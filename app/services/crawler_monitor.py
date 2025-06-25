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

logger = logging.getLogger(__name__)

class CrawlingMonitor:
    """크롤링 성공률 모니터링"""
    
    def __init__(self, stats_file: str = "crawling_stats.json"):
        self.stats_file = Path(stats_file)
        self.stats = self._load_stats()
    
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
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_stats(self):
        """통계 데이터를 저장합니다."""
        try:
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
    
    def record_attempt(self, url: str, success: bool, content_length: int = 0, error: str = ""):
        """크롤링 시도를 기록합니다."""
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc.lower()
        timestamp = datetime.now().isoformat()
        
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
                "last_success": None,
                "last_failure": None,
                "common_errors": Counter()
            }
        
        site_stat = self.stats["site_stats"][domain]
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
                # Counter 객체가 아닌 경우 Counter로 변환
                if not isinstance(site_stat["common_errors"], Counter):
                    site_stat["common_errors"] = Counter(site_stat["common_errors"])
                site_stat["common_errors"][error] += 1
        
        # 최근 시도 기록 (최대 100개)
        recent_attempt = {
            "url": url,
            "domain": domain,
            "success": success,
            "content_length": content_length,
            "error": error,
            "timestamp": timestamp
        }
        
        self.stats["recent_attempts"].append(recent_attempt)
        if len(self.stats["recent_attempts"]) > 100:
            self.stats["recent_attempts"] = self.stats["recent_attempts"][-100:]
        
        # 문제 사이트 식별
        self._identify_problem_sites()
        
        # 통계 저장
        self._save_stats()
    
    def _identify_problem_sites(self):
        """문제가 있는 사이트를 식별합니다."""
        problem_sites = []
        
        for domain, stats in self.stats["site_stats"].items():
            if stats["total_attempts"] >= 3:  # 최소 3번 시도
                success_rate = stats["successful_crawls"] / stats["total_attempts"]
                
                if success_rate < 0.5:  # 50% 미만 성공률
                    # Counter 객체 안전하게 처리
                    common_errors = stats.get("common_errors", {})
                    if isinstance(common_errors, Counter):
                        error_dict = dict(common_errors.most_common(3))
                    else:
                        # 딕셔너리인 경우 상위 3개 선택
                        sorted_errors = sorted(common_errors.items(), key=lambda x: x[1], reverse=True)
                        error_dict = dict(sorted_errors[:3])
                    
                    problem_sites.append({
                        "domain": domain,
                        "success_rate": success_rate,
                        "total_attempts": stats["total_attempts"],
                        "failed_attempts": stats["failed_crawls"],
                        "last_failure": stats["last_failure"],
                        "common_errors": error_dict
                    })
        
        # 성공률 순으로 정렬
        problem_sites.sort(key=lambda x: x["success_rate"])
        self.stats["problem_sites"] = problem_sites
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """전체 통계를 반환합니다."""
        total = self.stats["total_attempts"]
        if total == 0:
            return {"success_rate": 0, "total_attempts": 0}
        
        success_rate = self.stats["successful_crawls"] / total
        return {
            "success_rate": success_rate,
            "total_attempts": total,
            "successful_crawls": self.stats["successful_crawls"],
            "failed_crawls": self.stats["failed_crawls"]
        }
    
    def get_site_stats(self, domain: str) -> Optional[Dict[str, Any]]:
        """특정 사이트의 통계를 반환합니다."""
        return self.stats["site_stats"].get(domain)
    
    def get_problem_sites(self) -> List[Dict[str, Any]]:
        """문제가 있는 사이트 목록을 반환합니다."""
        return self.stats["problem_sites"]
    
    def get_recent_attempts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """최근 크롤링 시도를 반환합니다."""
        return self.stats["recent_attempts"][-limit:]
    
    def generate_report(self) -> str:
        """크롤링 성공률 리포트를 생성합니다."""
        overall = self.get_overall_stats()
        problem_sites = self.get_problem_sites()
        
        report = f"""
📊 크롤링 성공률 리포트
{'='*50}

📈 전체 통계:
   • 총 시도: {overall['total_attempts']:,}회
   • 성공: {overall['successful_crawls']:,}회
   • 실패: {overall['failed_crawls']:,}회
   • 성공률: {overall['success_rate']:.1%}

🚨 문제 사이트 ({len(problem_sites)}개):
"""
        
        for site in problem_sites[:10]:  # 상위 10개만 표시
            report += f"""
   • {site['domain']}
     - 성공률: {site['success_rate']:.1%}
     - 총 시도: {site['total_attempts']}회
     - 실패: {site['failed_attempts']}회
     - 주요 오류: {', '.join(site['common_errors'].keys())}
"""
        
        if not problem_sites:
            report += "   ✅ 문제 사이트 없음\n"
        
        report += f"\n📅 마지막 업데이트: {self.stats['last_updated']}"
        
        return report
    
    def cleanup_old_data(self, days: int = 30):
        """오래된 데이터를 정리합니다."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 최근 시도에서 오래된 데이터 제거
        self.stats["recent_attempts"] = [
            attempt for attempt in self.stats["recent_attempts"]
            if datetime.fromisoformat(attempt["timestamp"]) > cutoff_date
        ]
        
        # 사이트별 통계에서 오래된 데이터 정리
        for domain in list(self.stats["site_stats"].keys()):
            stats = self.stats["site_stats"][domain]
            last_activity = None
            
            if stats["last_success"]:
                last_activity = datetime.fromisoformat(stats["last_success"])
            elif stats["last_failure"]:
                last_activity = datetime.fromisoformat(stats["last_failure"])
            
            if last_activity and last_activity < cutoff_date:
                del self.stats["site_stats"][domain]
        
        self._save_stats()
        logger.info(f"{days}일 이상 된 데이터를 정리했습니다.")

# 전역 모니터 인스턴스
crawling_monitor = CrawlingMonitor() 