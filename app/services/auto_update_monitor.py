"""
자동 업데이트 및 모니터링 시스템
시스템의 자동 업데이트와 실시간 모니터링을 담당합니다.
"""

import os
import sys
import json
import logging
import asyncio
import threading
import time
import subprocess
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import schedule
import psutil
from dataclasses import dataclass, asdict

from .system_diagnostic import system_diagnostic
from .comprehensive_logger import comprehensive_logger, LogLevel, LogCategory

@dataclass
class UpdateTask:
    """업데이트 작업 데이터 클래스"""
    name: str
    description: str
    function: Callable
    schedule: str  # cron 형식 또는 간격
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0
    last_error: Optional[str] = None

@dataclass
class AlertRule:
    """알림 규칙 데이터 클래스"""
    name: str
    condition: Callable
    threshold: Any
    severity: str  # info, warning, error, critical
    enabled: bool = True
    last_triggered: Optional[str] = None
    cooldown_minutes: int = 60

class AutoUpdateMonitor:
    """자동 업데이트 및 모니터링 시스템"""
    
    def __init__(self):
        self.update_tasks: Dict[str, UpdateTask] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.monitoring_active = False
        self.monitor_thread = None
        self.alert_callbacks: List[Callable] = []
        
        # 모니터링 설정
        self.check_interval = 60  # 1분마다 체크
        self.alert_cooldown = {}  # 알림 쿨다운 관리
        
        # 시스템 상태
        self.system_metrics = {
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0,
            "api_response_time": 0,
            "database_size": 0,
            "log_file_count": 0,
            "error_count_today": 0,
            "warning_count_today": 0
        }
        
        # 업데이트 이력
        self.update_history = []
        
        # 초기화
        self._setup_default_tasks()
        self._setup_default_alerts()
    
    def _setup_default_tasks(self):
        """기본 업데이트 작업 설정"""
        
        # 1. 시스템 진단 (매시간)
        self.add_update_task(
            name="system_diagnostic",
            description="전체 시스템 진단 실행",
            function=self._run_system_diagnostic,
            schedule="0 * * * *"  # 매시간 정각
        )
        
        # 2. 로그 정리 (매일 새벽 2시)
        self.add_update_task(
            name="log_cleanup",
            description="오래된 로그 파일 정리",
            function=self._cleanup_logs,
            schedule="0 2 * * *"  # 매일 새벽 2시
        )
        
        # 3. 데이터베이스 최적화 (매주 일요일 새벽 3시)
        self.add_update_task(
            name="database_optimization",
            description="데이터베이스 최적화",
            function=self._optimize_database,
            schedule="0 3 * * 0"  # 매주 일요일 새벽 3시
        )
        
        # 4. 임시 파일 정리 (매일 새벽 1시)
        self.add_update_task(
            name="temp_file_cleanup",
            description="임시 파일 정리",
            function=self._cleanup_temp_files,
            schedule="0 1 * * *"  # 매일 새벽 1시
        )
        
        # 5. 백업 생성 (매일 새벽 4시)
        self.add_update_task(
            name="backup_creation",
            description="시스템 백업 생성",
            function=self._create_backup,
            schedule="0 4 * * *"  # 매일 새벽 4시
        )
        
        # 6. 성능 모니터링 (5분마다)
        self.add_update_task(
            name="performance_monitoring",
            description="성능 지표 수집",
            function=self._collect_performance_metrics,
            schedule="*/5 * * * *"  # 5분마다
        )
        
        # 7. API 상태 확인 (10분마다)
        self.add_update_task(
            name="api_health_check",
            description="API 상태 확인",
            function=self._check_api_health,
            schedule="*/10 * * * *"  # 10분마다
        )
    
    def _setup_default_alerts(self):
        """기본 알림 규칙 설정"""
        
        # 1. CPU 사용률 알림
        self.add_alert_rule(
            name="high_cpu_usage",
            condition=lambda: self.system_metrics["cpu_usage"],
            threshold=80,
            severity="warning",
            cooldown_minutes=30
        )
        
        # 2. 메모리 사용률 알림
        self.add_alert_rule(
            name="high_memory_usage",
            condition=lambda: self.system_metrics["memory_usage"],
            threshold=85,
            severity="warning",
            cooldown_minutes=30
        )
        
        # 3. 디스크 사용률 알림
        self.add_alert_rule(
            name="high_disk_usage",
            condition=lambda: self.system_metrics["disk_usage"],
            threshold=90,
            severity="error",
            cooldown_minutes=60
        )
        
        # 4. API 응답 시간 알림
        self.add_alert_rule(
            name="slow_api_response",
            condition=lambda: self.system_metrics["api_response_time"],
            threshold=5.0,  # 5초
            severity="warning",
            cooldown_minutes=15
        )
        
        # 5. 에러 발생 알림
        self.add_alert_rule(
            name="error_count_high",
            condition=lambda: self.system_metrics["error_count_today"],
            threshold=10,
            severity="error",
            cooldown_minutes=60
        )
        
        # 6. 데이터베이스 크기 알림
        self.add_alert_rule(
            name="large_database",
            condition=lambda: self.system_metrics["database_size"],
            threshold=100 * 1024 * 1024,  # 100MB
            severity="warning",
            cooldown_minutes=120
        )
    
    def add_update_task(self, 
                       name: str, 
                       description: str, 
                       function: Callable, 
                       schedule: str, 
                       enabled: bool = True):
        """업데이트 작업 추가"""
        task = UpdateTask(
            name=name,
            description=description,
            function=function,
            schedule=schedule,
            enabled=enabled
        )
        self.update_tasks[name] = task
        
        # 스케줄 등록
        if enabled:
            self._schedule_task(task)
        
        comprehensive_logger.log(
            LogLevel.INFO, 
            LogCategory.SYSTEM, 
            f"업데이트 작업 추가: {name}",
            {"schedule": schedule, "enabled": enabled}
        )
    
    def add_alert_rule(self, 
                      name: str, 
                      condition: Callable, 
                      threshold: Any, 
                      severity: str, 
                      enabled: bool = True,
                      cooldown_minutes: int = 60):
        """알림 규칙 추가"""
        rule = AlertRule(
            name=name,
            condition=condition,
            threshold=threshold,
            severity=severity,
            enabled=enabled,
            cooldown_minutes=cooldown_minutes
        )
        self.alert_rules[name] = rule
        
        comprehensive_logger.log(
            LogLevel.INFO, 
            LogCategory.SYSTEM, 
            f"알림 규칙 추가: {name}",
            {"threshold": threshold, "severity": severity, "enabled": enabled}
        )
    
    def _schedule_task(self, task: UpdateTask):
        """작업 스케줄링"""
        try:
            if task.schedule.startswith("*/"):
                interval = int(task.schedule.split("*/")[1].split()[0])
                schedule.every(interval).minutes.do(self._execute_task, task.name)
                return
            
            parts = task.schedule.split()
            if len(parts) < 5:
                raise ValueError("지원하지 않는 스케줄 형식")
            
            minute, hour, day, month, weekday = parts[:5]
            
            day_constraint = int(day) if day != "*" else None
            month_constraint = int(month) if month != "*" else None
            weekday_constraint = weekday if weekday != "*" else None
            
            # 시간 필드 와일드카드 처리
            if hour == "*" and minute.isdigit():
                minute_marker = f":{int(minute):02d}"
                
                if not day_constraint and not month_constraint and not weekday_constraint:
                    schedule.every().hour.at(minute_marker).do(self._execute_task, task.name)
                else:
                    schedule.every().hour.at(minute_marker).do(
                        self._execute_with_constraints,
                        task.name,
                        day_constraint,
                        weekday_constraint,
                        month_constraint
                    )
                return
            
            time_str = self._format_time(hour, minute)
            
            if day_constraint is None and weekday_constraint is None and month_constraint is None:
                schedule.every().day.at(time_str).do(self._execute_task, task.name)
            else:
                schedule.every().day.at(time_str).do(
                    self._execute_with_constraints,
                    task.name,
                    day_constraint,
                    weekday_constraint,
                    month_constraint
                )
        except Exception as e:
            comprehensive_logger.log(
                LogLevel.ERROR, 
                LogCategory.SYSTEM, 
                f"작업 스케줄링 실패: {task.name}",
                {"error": str(e)}
            )

    def _format_time(self, hour: str, minute: str) -> str:
        """cron 시간 필드를 Schedule 형식으로 변환"""
        if hour == "*" or minute == "*":
            raise ValueError("시간 필드는 반드시 숫자여야 합니다")
        return f"{int(hour):02d}:{int(minute):02d}"
    
    def _execute_if_day_matches(self, task_name: str, day_of_month: int, month: Optional[int]):
        """월별/일자 기반 작업을 실행 조건에 맞게 처리"""
        today = datetime.now()
        if today.day == day_of_month and (month is None or today.month == month):
            self._execute_task(task_name)
    
    def _execute_if_weekday_matches(self, task_name: str, weekday: str, month: Optional[int]):
        """요일 및 월 조건을 만족할 때 작업 실행"""
        today = datetime.now()
        cron_weekday = today.strftime("%w")  # 0=일요일, 6=토요일
        if cron_weekday == weekday and (month is None or today.month == month):
            self._execute_task(task_name)
    
    def _execute_if_month_matches(self, task_name: str, month: int):
        """특정 월에만 작업 실행"""
        if datetime.now().month == month:
            self._execute_task(task_name)
    
    def _execute_with_constraints(
        self,
        task_name: str,
        day_of_month: Optional[int] = None,
        weekday: Optional[str] = None,
        month: Optional[int] = None
    ):
        """여러 cron 제약 조건을 동시에 확인해 작업 실행"""
        today = datetime.now()
        
        if month is not None and today.month != month:
            return
        
        if day_of_month is not None and today.day != day_of_month:
            return
        
        if weekday is not None:
            cron_weekday = int(today.strftime("%w"))
            if not self._weekday_matches(weekday, cron_weekday):
                return
        
        self._execute_task(task_name)
    
    def _weekday_matches(self, constraint: str, current_weekday: int) -> bool:
        """cron 요일 제약을 확인 (단일 값, 범위, 리스트 지원)"""
        try:
            parts = [p.strip() for p in constraint.split(",")]
            for part in parts:
                if "-" in part:
                    start_str, end_str = part.split("-", 1)
                    start = int(start_str)
                    end = int(end_str)
                    if start <= current_weekday <= end:
                        return True
                else:
                    if current_weekday == int(part):
                        return True
        except ValueError:
            return constraint == str(current_weekday)
        return False
    
    def start_monitoring(self):
        """모니터링 시작"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # 모니터링 스레드 시작
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        comprehensive_logger.log(
            LogLevel.INFO, 
            LogCategory.SYSTEM, 
            "자동 업데이트 및 모니터링 시스템이 시작되었습니다"
        )
    
    def stop_monitoring(self):
        """모니터링 중지"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        
        # 스케줄 정리
        schedule.clear()
        
        comprehensive_logger.log(
            LogLevel.INFO, 
            LogCategory.SYSTEM, 
            "자동 업데이트 및 모니터링 시스템이 중지되었습니다"
        )
    
    def _monitoring_loop(self):
        """모니터링 루프"""
        while self.monitoring_active:
            try:
                # 스케줄된 작업 실행
                schedule.run_pending()
                
                # 시스템 메트릭 수집
                self._collect_system_metrics()
                
                # 알림 규칙 체크
                self._check_alert_rules()
                
                # 잠시 대기
                time.sleep(self.check_interval)
                
            except Exception as e:
                comprehensive_logger.log(
                    LogLevel.ERROR, 
                    LogCategory.SYSTEM, 
                    "모니터링 루프 오류",
                    {"error": str(e)}
                )
                time.sleep(60)  # 오류 시 1분 대기
    
    def _execute_task(self, task_name: str):
        """작업 실행"""
        if task_name not in self.update_tasks:
            return
        
        task = self.update_tasks[task_name]
        if not task.enabled:
            return
        
        start_time = time.time()
        
        try:
            comprehensive_logger.log(
                LogLevel.INFO, 
                LogCategory.SYSTEM, 
                f"업데이트 작업 시작: {task.name}",
                {"description": task.description}
            )
            
            # 작업 실행
            if asyncio.iscoroutinefunction(task.function):
                asyncio.run(task.function())
            else:
                task.function()
            
            # 성공 기록
            task.success_count += 1
            task.last_run = datetime.now().isoformat()
            
            duration = time.time() - start_time
            
            comprehensive_logger.log(
                LogLevel.INFO, 
                LogCategory.SYSTEM, 
                f"업데이트 작업 완료: {task.name}",
                {"duration": duration, "success_count": task.success_count}
            )
            
            # 업데이트 이력 기록
            self.update_history.append({
                "task_name": task.name,
                "status": "success",
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            # 실패 기록
            task.failure_count += 1
            task.last_error = str(e)
            task.last_run = datetime.now().isoformat()
            
            comprehensive_logger.log(
                LogLevel.ERROR, 
                LogCategory.SYSTEM, 
                f"업데이트 작업 실패: {task.name}",
                {"error": str(e), "failure_count": task.failure_count}
            )
            
            # 업데이트 이력 기록
            self.update_history.append({
                "task_name": task.name,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    def _collect_system_metrics(self):
        """시스템 메트릭 수집"""
        try:
            # CPU 사용률
            self.system_metrics["cpu_usage"] = psutil.cpu_percent(interval=1)
            
            # 메모리 사용률
            memory = psutil.virtual_memory()
            self.system_metrics["memory_usage"] = memory.percent
            
            # 디스크 사용률
            disk = psutil.disk_usage('/')
            self.system_metrics["disk_usage"] = disk.percent
            
            # API 응답 시간
            try:
                start_time = time.time()
                response = requests.get("http://localhost:8000/health", timeout=5)
                self.system_metrics["api_response_time"] = time.time() - start_time
            except:
                self.system_metrics["api_response_time"] = 999  # 연결 실패 시 큰 값
            
            # 데이터베이스 크기
            if os.path.exists("blog.db"):
                self.system_metrics["database_size"] = os.path.getsize("blog.db")
            
            # 로그 파일 수
            log_dir = Path("logs")
            if log_dir.exists():
                self.system_metrics["log_file_count"] = len(list(log_dir.glob("*.log")))
            
            # 오늘의 에러/경고 수
            today = datetime.now().strftime("%Y-%m-%d")
            stats = comprehensive_logger.get_log_stats()
            self.system_metrics["error_count_today"] = stats.get("errors_today", 0)
            self.system_metrics["warning_count_today"] = stats.get("warnings_today", 0)
            
        except Exception as e:
            comprehensive_logger.log(
                LogLevel.ERROR, 
                LogCategory.SYSTEM, 
                "시스템 메트릭 수집 실패",
                {"error": str(e)}
            )
    
    def _check_alert_rules(self):
        """알림 규칙 체크"""
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            try:
                # 쿨다운 체크
                if rule_name in self.alert_cooldown:
                    last_triggered = datetime.fromisoformat(self.alert_cooldown[rule_name])
                    if datetime.now() - last_triggered < timedelta(minutes=rule.cooldown_minutes):
                        continue
                
                # 조건 체크
                current_value = rule.condition()
                
                if current_value > rule.threshold:
                    # 알림 트리거
                    self._trigger_alert(rule, current_value)
                    
                    # 쿨다운 설정
                    self.alert_cooldown[rule_name] = datetime.now().isoformat()
                    rule.last_triggered = datetime.now().isoformat()
                    
            except Exception as e:
                comprehensive_logger.log(
                    LogLevel.ERROR, 
                    LogCategory.SYSTEM, 
                    f"알림 규칙 체크 실패: {rule_name}",
                    {"error": str(e)}
                )
    
    def _trigger_alert(self, rule: AlertRule, current_value: Any):
        """알림 트리거"""
        alert_data = {
            "rule_name": rule.name,
            "severity": rule.severity,
            "threshold": rule.threshold,
            "current_value": current_value,
            "timestamp": datetime.now().isoformat()
        }
        
        # 로그 기록
        log_level = LogLevel.WARNING if rule.severity == "warning" else LogLevel.ERROR
        comprehensive_logger.log(
            log_level, 
            LogCategory.SYSTEM, 
            f"알림 트리거: {rule.name}",
            alert_data
        )
        
        # 콜백 실행
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                comprehensive_logger.log(
                    LogLevel.ERROR, 
                    LogCategory.SYSTEM, 
                    "알림 콜백 실행 실패",
                    {"error": str(e)}
                )
    
    def add_alert_callback(self, callback: Callable):
        """알림 콜백 추가"""
        self.alert_callbacks.append(callback)
    
    # 업데이트 작업 함수들
    async def _run_system_diagnostic(self):
        """시스템 진단 실행"""
        await system_diagnostic.run_full_diagnostic()
    
    def _cleanup_logs(self):
        """로그 정리"""
        comprehensive_logger.cleanup_old_logs(days=7)
    
    def _optimize_database(self):
        """데이터베이스 최적화"""
        from ..database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        try:
            db.execute(text("VACUUM"))
            db.commit()
        finally:
            db.close()
    
    def _cleanup_temp_files(self):
        """임시 파일 정리"""
        temp_patterns = ["*.tmp", "*.bak", "*.backup", ".DS_Store"]
        cleaned_count = 0
        
        for pattern in temp_patterns:
            for temp_file in Path(".").glob(pattern):
                temp_file.unlink()
                cleaned_count += 1
        
        comprehensive_logger.log(
            LogLevel.INFO, 
            LogCategory.SYSTEM, 
            f"임시 파일 정리 완료: {cleaned_count}개 삭제"
        )
    
    def _create_backup(self):
        """백업 생성"""
        try:
            import shutil
            from datetime import datetime
            
            # 백업 디렉토리 생성
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            # 데이터베이스 백업
            if os.path.exists("blog.db"):
                backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2("blog.db", backup_dir / backup_filename)
            
            # 로그 백업
            log_dir = Path("logs")
            if log_dir.exists():
                log_backup_dir = backup_dir / f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copytree(log_dir, log_backup_dir)
            
            comprehensive_logger.log(
                LogLevel.INFO, 
                LogCategory.SYSTEM, 
                "시스템 백업 생성 완료"
            )
            
        except Exception as e:
            comprehensive_logger.log(
                LogLevel.ERROR, 
                LogCategory.SYSTEM, 
                "백업 생성 실패",
                {"error": str(e)}
            )
    
    def _collect_performance_metrics(self):
        """성능 지표 수집"""
        # 이미 _collect_system_metrics에서 수집하므로 여기서는 추가 처리만
        pass
    
    def _check_api_health(self):
        """API 상태 확인"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                comprehensive_logger.log(
                    LogLevel.INFO, 
                    LogCategory.API, 
                    "API 상태 정상"
                )
            else:
                comprehensive_logger.log(
                    LogLevel.WARNING, 
                    LogCategory.API, 
                    f"API 상태 비정상: {response.status_code}"
                )
        except Exception as e:
            comprehensive_logger.log(
                LogLevel.ERROR, 
                LogCategory.API, 
                "API 상태 확인 실패",
                {"error": str(e)}
            )
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 반환"""
        return {
            "monitoring_active": self.monitoring_active,
            "system_metrics": self.system_metrics.copy(),
            "update_tasks": {
                name: {
                    "description": task.description,
                    "enabled": task.enabled,
                    "last_run": task.last_run,
                    "success_count": task.success_count,
                    "failure_count": task.failure_count,
                    "last_error": task.last_error
                }
                for name, task in self.update_tasks.items()
            },
            "alert_rules": {
                name: {
                    "severity": rule.severity,
                    "enabled": rule.enabled,
                    "last_triggered": rule.last_triggered,
                    "cooldown_minutes": rule.cooldown_minutes
                }
                for name, rule in self.alert_rules.items()
            },
            "recent_updates": self.update_history[-10:]  # 최근 10개
        }
    
    def get_update_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """업데이트 이력 반환"""
        return self.update_history[-limit:]
    
    def enable_task(self, task_name: str):
        """작업 활성화"""
        if task_name in self.update_tasks:
            self.update_tasks[task_name].enabled = True
            self._schedule_task(self.update_tasks[task_name])
    
    def disable_task(self, task_name: str):
        """작업 비활성화"""
        if task_name in self.update_tasks:
            self.update_tasks[task_name].enabled = False
    
    def enable_alert(self, rule_name: str):
        """알림 활성화"""
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name].enabled = True
    
    def disable_alert(self, rule_name: str):
        """알림 비활성화"""
        if rule_name in self.alert_rules:
            self.alert_rules[rule_name].enabled = False

# 전역 모니터 인스턴스
auto_update_monitor = AutoUpdateMonitor()
