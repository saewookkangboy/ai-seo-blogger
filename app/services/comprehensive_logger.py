"""
포괄적인 로깅 시스템
모든 시스템 활동을 자동으로 기록하고 관리합니다.
"""

import os
import json
import logging
import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import queue
import sqlite3
from contextlib import contextmanager

class LogLevel(Enum):
    """로그 레벨 열거형"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """로그 카테고리 열거형"""
    SYSTEM = "SYSTEM"
    API = "API"
    DATABASE = "DATABASE"
    CRAWLING = "CRAWLING"
    CONTENT_GENERATION = "CONTENT_GENERATION"
    TRANSLATION = "TRANSLATION"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    USER_ACTION = "USER_ACTION"
    ERROR = "ERROR"

@dataclass
class LogEntry:
    """로그 엔트리 데이터 클래스"""
    timestamp: str
    level: str
    category: str
    message: str
    details: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    duration: Optional[float] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None

class ComprehensiveLogger:
    """포괄적인 로깅 시스템"""
    
    def __init__(self, 
                 log_dir: str = "logs",
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 max_files: int = 10,
                 enable_database_logging: bool = True,
                 enable_file_logging: bool = True,
                 enable_console_logging: bool = True):
        
        # Vercel 서버리스: 읽기 전용 파일시스템이므로 /tmp 사용
        if os.environ.get("VERCEL") == "1":
            self.log_dir = Path("/tmp/logs")
        else:
            self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.max_files = max_files
        self.enable_database_logging = enable_database_logging
        self.enable_file_logging = enable_file_logging
        self.enable_console_logging = enable_console_logging

        # 로그 디렉토리 생성. 읽기 전용 파일시스템(예: Vercel)이면 파일/DB 로깅 비활성화
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            self.log_dir = Path("/tmp/logs")
            try:
                self.log_dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                self.enable_file_logging = False
                self.enable_database_logging = False
                self.log_dir = Path(log_dir)  # 경로만 유지, 실제 쓰기 안 함
        
        # 로그 큐 (비동기 처리를 위한)
        self.log_queue = queue.Queue()
        self.log_worker_thread = None
        self.is_running = False
        
        # 로그 통계
        self.log_stats = {
            "total_logs": 0,
            "logs_by_level": {level.value: 0 for level in LogLevel},
            "logs_by_category": {category.value: 0 for category in LogCategory},
            "last_log_time": None,
            "errors_today": 0,
            "warnings_today": 0
        }
        
        # 로그 파일 핸들러
        self.file_handlers = {}
        
        # 데이터베이스 연결
        self.db_path = self.log_dir / "comprehensive_logs.db"
        self._init_database()
        
        # 시작
        self.start()
    
    def _init_database(self):
        """로그 데이터베이스 초기화"""
        if not self.enable_database_logging:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 로그 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    request_id TEXT,
                    duration REAL,
                    file_path TEXT,
                    line_number INTEGER,
                    function_name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 인덱스 생성
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_level ON logs(level)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON logs(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON logs(user_id)")
            
            # 통계 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS log_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    total_logs INTEGER DEFAULT 0,
                    debug_logs INTEGER DEFAULT 0,
                    info_logs INTEGER DEFAULT 0,
                    warning_logs INTEGER DEFAULT 0,
                    error_logs INTEGER DEFAULT 0,
                    critical_logs INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date)
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"로그 데이터베이스 초기화 실패: {e}")
    
    def start(self):
        """로깅 시스템 시작"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 로그 워커 스레드 시작
        self.log_worker_thread = threading.Thread(target=self._log_worker, daemon=True)
        self.log_worker_thread.start()
        
        # 통계 업데이트 스레드 시작
        self.stats_thread = threading.Thread(target=self._stats_worker, daemon=True)
        self.stats_thread.start()
        
        self.log(LogLevel.INFO, LogCategory.SYSTEM, "포괄적인 로깅 시스템이 시작되었습니다")
    
    def stop(self):
        """로깅 시스템 중지"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 큐에 남은 로그 처리
        while not self.log_queue.empty():
            time.sleep(0.1)
        
        self.log(LogLevel.INFO, LogCategory.SYSTEM, "포괄적인 로깅 시스템이 중지되었습니다")
    
    def _log_worker(self):
        """로그 워커 스레드"""
        while self.is_running:
            try:
                # 큐에서 로그 엔트리 가져오기
                log_entry = self.log_queue.get(timeout=1)
                
                # 로그 처리
                self._process_log_entry(log_entry)
                
                # 통계 업데이트
                self._update_stats(log_entry)
                
                self.log_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"로그 워커 오류: {e}")
    
    def _stats_worker(self):
        """통계 워커 스레드 (매시간 실행)"""
        while self.is_running:
            try:
                time.sleep(3600)  # 1시간 대기
                self._update_daily_stats()
            except Exception as e:
                print(f"통계 워커 오류: {e}")
    
    def _process_log_entry(self, log_entry: LogEntry):
        """로그 엔트리 처리"""
        try:
            # 파일 로깅
            if self.enable_file_logging:
                self._write_to_file(log_entry)
            
            # 데이터베이스 로깅
            if self.enable_database_logging:
                self._write_to_database(log_entry)
            
            # 콘솔 로깅
            if self.enable_console_logging:
                self._write_to_console(log_entry)
                
        except Exception as e:
            print(f"로그 엔트리 처리 실패: {e}")
    
    def _write_to_file(self, log_entry: LogEntry):
        """파일에 로그 쓰기"""
        try:
            # 카테고리별 파일 분리
            log_file = self.log_dir / f"{log_entry.category.lower()}.log"
            
            # 파일 핸들러 가져오기 또는 생성
            if log_file not in self.file_handlers:
                self.file_handlers[log_file] = open(log_file, 'a', encoding='utf-8')
            
            # 로그 포맷팅
            log_line = self._format_log_line(log_entry)
            
            # 파일에 쓰기
            self.file_handlers[log_file].write(log_line + '\n')
            self.file_handlers[log_file].flush()
            
            # 파일 크기 체크 및 로테이션
            self._rotate_log_file(log_file)
            
        except Exception as e:
            print(f"파일 로깅 실패: {e}")
    
    def _write_to_database(self, log_entry: LogEntry):
        """데이터베이스에 로그 쓰기"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO logs (
                    timestamp, level, category, message, details,
                    user_id, session_id, request_id, duration,
                    file_path, line_number, function_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_entry.timestamp,
                log_entry.level,
                log_entry.category,
                log_entry.message,
                json.dumps(log_entry.details) if log_entry.details else None,
                log_entry.user_id,
                log_entry.session_id,
                log_entry.request_id,
                log_entry.duration,
                log_entry.file_path,
                log_entry.line_number,
                log_entry.function_name
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"데이터베이스 로깅 실패: {e}")
    
    def _write_to_console(self, log_entry: LogEntry):
        """콘솔에 로그 쓰기"""
        try:
            log_line = self._format_log_line(log_entry)
            print(log_line)
        except Exception as e:
            print(f"콘솔 로깅 실패: {e}")
    
    def _format_log_line(self, log_entry: LogEntry) -> str:
        """로그 라인 포맷팅"""
        details_str = ""
        if log_entry.details:
            details_str = f" | Details: {json.dumps(log_entry.details, ensure_ascii=False)}"
        
        return (f"[{log_entry.timestamp}] "
                f"[{log_entry.level}] "
                f"[{log_entry.category}] "
                f"{log_entry.message}"
                f"{details_str}")
    
    def _rotate_log_file(self, log_file: Path):
        """로그 파일 로테이션"""
        try:
            if log_file.stat().st_size > self.max_file_size:
                # 기존 파일 백업
                backup_file = log_file.with_suffix(f'.log.{int(time.time())}')
                log_file.rename(backup_file)
                
                # 새 파일 생성
                self.file_handlers[log_file] = open(log_file, 'w', encoding='utf-8')
                
                # 오래된 백업 파일 삭제
                self._cleanup_old_logs(log_file)
                
        except Exception as e:
            print(f"로그 파일 로테이션 실패: {e}")
    
    def _cleanup_old_logs(self, log_file: Path):
        """오래된 로그 파일 정리"""
        try:
            pattern = f"{log_file.stem}.log.*"
            old_files = list(log_file.parent.glob(pattern))
            
            # 파일 수가 max_files를 초과하면 오래된 것부터 삭제
            if len(old_files) > self.max_files:
                old_files.sort(key=lambda x: x.stat().st_mtime)
                for old_file in old_files[:-self.max_files]:
                    old_file.unlink()
                    
        except Exception as e:
            print(f"오래된 로그 파일 정리 실패: {e}")
    
    def _update_stats(self, log_entry: LogEntry):
        """로그 통계 업데이트"""
        try:
            self.log_stats["total_logs"] += 1
            self.log_stats["logs_by_level"][log_entry.level] += 1
            self.log_stats["logs_by_category"][log_entry.category] += 1
            self.log_stats["last_log_time"] = log_entry.timestamp
            
            if log_entry.level == LogLevel.ERROR.value:
                self.log_stats["errors_today"] += 1
            elif log_entry.level == LogLevel.WARNING.value:
                self.log_stats["warnings_today"] += 1
                
        except Exception as e:
            print(f"통계 업데이트 실패: {e}")
    
    def _update_daily_stats(self):
        """일일 통계 업데이트"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 오늘의 통계 조회
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN level = 'DEBUG' THEN 1 ELSE 0 END) as debug,
                    SUM(CASE WHEN level = 'INFO' THEN 1 ELSE 0 END) as info,
                    SUM(CASE WHEN level = 'WARNING' THEN 1 ELSE 0 END) as warning,
                    SUM(CASE WHEN level = 'ERROR' THEN 1 ELSE 0 END) as error,
                    SUM(CASE WHEN level = 'CRITICAL' THEN 1 ELSE 0 END) as critical
                FROM logs 
                WHERE DATE(timestamp) = ?
            """, (today,))
            
            stats = cursor.fetchone()
            
            if stats:
                cursor.execute("""
                    INSERT OR REPLACE INTO log_stats 
                    (date, total_logs, debug_logs, info_logs, warning_logs, error_logs, critical_logs)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (today, *stats))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"일일 통계 업데이트 실패: {e}")
    
    def log(self, 
            level: LogLevel, 
            category: LogCategory, 
            message: str,
            details: Optional[Dict[str, Any]] = None,
            user_id: Optional[str] = None,
            session_id: Optional[str] = None,
            request_id: Optional[str] = None,
            duration: Optional[float] = None,
            file_path: Optional[str] = None,
            line_number: Optional[int] = None,
            function_name: Optional[str] = None):
        """로그 기록"""
        
        # 호출자 정보 가져오기
        if not file_path or not line_number or not function_name:
            import inspect
            frame = inspect.currentframe().f_back
            if not file_path:
                file_path = frame.f_code.co_filename
            if not line_number:
                line_number = frame.f_lineno
            if not function_name:
                function_name = frame.f_code.co_name
        
        # 로그 엔트리 생성
        log_entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.value,
            category=category.value,
            message=message,
            details=details,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            duration=duration,
            file_path=file_path,
            line_number=line_number,
            function_name=function_name
        )
        
        # 큐에 추가
        self.log_queue.put(log_entry)
    
    def get_logs(self, 
                 level: Optional[str] = None,
                 category: Optional[str] = None,
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None,
                 limit: int = 100,
                 offset: int = 0) -> List[Dict[str, Any]]:
        """로그 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 쿼리 조건 구성
            conditions = []
            params = []
            
            if level:
                conditions.append("level = ?")
                params.append(level)
            
            if category:
                conditions.append("category = ?")
                params.append(category)
            
            if start_date:
                conditions.append("timestamp >= ?")
                params.append(start_date)
            
            if end_date:
                conditions.append("timestamp <= ?")
                params.append(end_date)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # 쿼리 실행
            query = f"""
                SELECT * FROM logs 
                {where_clause}
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # 컬럼명 가져오기
            columns = [description[0] for description in cursor.description]
            
            # 결과 변환
            logs = []
            for row in rows:
                log_dict = dict(zip(columns, row))
                if log_dict.get('details'):
                    try:
                        log_dict['details'] = json.loads(log_dict['details'])
                    except:
                        pass
                logs.append(log_dict)
            
            conn.close()
            return logs
            
        except Exception as e:
            print(f"로그 조회 실패: {e}")
            return []
    
    def get_log_stats(self) -> Dict[str, Any]:
        """로그 통계 반환"""
        return self.log_stats.copy()
    
    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """일일 통계 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM log_stats 
                ORDER BY date DESC 
                LIMIT ?
            """, (days,))
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            stats = []
            for row in rows:
                stats.append(dict(zip(columns, row)))
            
            conn.close()
            return stats
            
        except Exception as e:
            print(f"일일 통계 조회 실패: {e}")
            return []
    
    def export_logs(self, 
                   output_file: str,
                   level: Optional[str] = None,
                   category: Optional[str] = None,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> bool:
        """로그 내보내기"""
        try:
            logs = self.get_logs(level, category, start_date, end_date, limit=10000)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"로그 내보내기 실패: {e}")
            return False
    
    def cleanup_old_logs(self, days: int = 30):
        """오래된 로그 정리"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff_date,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.log(LogLevel.INFO, LogCategory.SYSTEM, 
                    f"오래된 로그 정리 완료: {deleted_count}개 삭제")
            
            return deleted_count
            
        except Exception as e:
            print(f"오래된 로그 정리 실패: {e}")
            return 0

# 전역 로거 인스턴스
comprehensive_logger = ComprehensiveLogger()

# 편의 함수들
def log_system(message: str, details: Optional[Dict[str, Any]] = None):
    """시스템 로그"""
    comprehensive_logger.log(LogLevel.INFO, LogCategory.SYSTEM, message, details)

def log_api(message: str, details: Optional[Dict[str, Any]] = None, duration: Optional[float] = None):
    """API 로그"""
    comprehensive_logger.log(LogLevel.INFO, LogCategory.API, message, details, duration=duration)

def log_database(message: str, details: Optional[Dict[str, Any]] = None):
    """데이터베이스 로그"""
    comprehensive_logger.log(LogLevel.INFO, LogCategory.DATABASE, message, details)

def log_crawling(message: str, details: Optional[Dict[str, Any]] = None):
    """크롤링 로그"""
    comprehensive_logger.log(LogLevel.INFO, LogCategory.CRAWLING, message, details)

def log_content_generation(message: str, details: Optional[Dict[str, Any]] = None):
    """콘텐츠 생성 로그"""
    comprehensive_logger.log(LogLevel.INFO, LogCategory.CONTENT_GENERATION, message, details)

def log_translation(message: str, details: Optional[Dict[str, Any]] = None):
    """번역 로그"""
    comprehensive_logger.log(LogLevel.INFO, LogCategory.TRANSLATION, message, details)

def log_performance(message: str, details: Optional[Dict[str, Any]] = None):
    """성능 로그"""
    comprehensive_logger.log(LogLevel.INFO, LogCategory.PERFORMANCE, message, details)

def log_security(message: str, details: Optional[Dict[str, Any]] = None):
    """보안 로그"""
    comprehensive_logger.log(LogLevel.WARNING, LogCategory.SECURITY, message, details)

def log_user_action(message: str, user_id: str, details: Optional[Dict[str, Any]] = None):
    """사용자 액션 로그"""
    comprehensive_logger.log(LogLevel.INFO, LogCategory.USER_ACTION, message, details, user_id=user_id)

def log_error(message: str, details: Optional[Dict[str, Any]] = None):
    """에러 로그"""
    comprehensive_logger.log(LogLevel.ERROR, LogCategory.ERROR, message, details)

def log_critical(message: str, details: Optional[Dict[str, Any]] = None):
    """치명적 오류 로그"""
    comprehensive_logger.log(LogLevel.CRITICAL, LogCategory.ERROR, message, details)
