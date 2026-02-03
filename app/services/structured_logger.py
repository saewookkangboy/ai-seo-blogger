"""
구조화된 로깅 서비스
JSON 형식 로깅, 로그 압축, 로그 레벨 최적화
"""

import json
import logging
import gzip
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler
import threading

class StructuredFormatter(logging.Formatter):
    """구조화된 로그 포맷터 (JSON 형식)"""
    
    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON 형식으로 변환"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 예외 정보 추가
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # 추가 필드 추가
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class CompressedRotatingFileHandler(RotatingFileHandler):
    """압축된 로테이팅 파일 핸들러"""
    
    def __init__(self, filename: str, maxBytes: int = 10 * 1024 * 1024, 
                 backupCount: int = 5, encoding: str = 'utf-8'):
        """
        Args:
            filename: 로그 파일 경로
            maxBytes: 파일 최대 크기 (10MB 기본)
            backupCount: 보관할 백업 파일 수
            encoding: 인코딩
        """
        super().__init__(filename, maxBytes=maxBytes, 
                        backupCount=backupCount, encoding=encoding)
        self.lock = threading.Lock()
    
    def doRollover(self):
        """로그 파일 롤오버 시 압축"""
        with self.lock:
            super().doRollover()
            
            # 이전 로그 파일 압축
            if self.backupCount > 0:
                for i in range(self.backupCount - 1, 0, -1):
                    sfn = f"{self.baseFilename}.{i}"
                    if os.path.exists(sfn):
                        compressed_fn = f"{sfn}.gz"
                        if not os.path.exists(compressed_fn):
                            self._compress_file(sfn, compressed_fn)
    
    def _compress_file(self, source: str, dest: str):
        """파일 압축"""
        try:
            with open(source, 'rb') as f_in:
                with gzip.open(dest, 'wb') as f_out:
                    f_out.writelines(f_in)
            os.remove(source)
        except Exception as e:
            # 압축 실패 시 원본 유지
            pass


class StructuredLogger:
    """구조화된 로거 클래스"""
    
    def __init__(self, name: str, log_dir: str = "logs", 
                 enable_file_logging: bool = True,
                 enable_console_logging: bool = True,
                 log_level: int = logging.INFO):
        """
        Args:
            name: 로거 이름
            log_dir: 로그 디렉토리
            enable_file_logging: 파일 로깅 활성화
            enable_console_logging: 콘솔 로깅 활성화
            log_level: 로그 레벨
        """
        self.name = name
        _dir = Path("/tmp/logs") if os.environ.get("VERCEL") == "1" else Path(log_dir)
        try:
            _dir.mkdir(parents=True, exist_ok=True)
            self.log_dir = _dir
            _enable_file = enable_file_logging
        except OSError:
            self.log_dir = Path(log_dir)
            _enable_file = False
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # 기존 핸들러 제거
        self.logger.handlers.clear()
        
        # 구조화된 포맷터
        formatter = StructuredFormatter()
        
        # 파일 로깅 설정
        if _enable_file:
            log_file = self.log_dir / f"{name}.log"
            file_handler = CompressedRotatingFileHandler(
                str(log_file),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # 콘솔 로깅 설정
        if enable_console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            # 콘솔은 간단한 포맷 사용
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def _log_with_extra(self, level: int, message: str, **kwargs):
        """추가 필드와 함께 로깅"""
        extra = {'extra_fields': kwargs}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """DEBUG 레벨 로깅"""
        self._log_with_extra(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """INFO 레벨 로깅"""
        self._log_with_extra(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """WARNING 레벨 로깅"""
        self._log_with_extra(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """ERROR 레벨 로깅"""
        self._log_with_extra(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """CRITICAL 레벨 로깅"""
        self._log_with_extra(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """예외 정보와 함께 로깅"""
        self._log_with_extra(logging.ERROR, message, exc_info=True, **kwargs)


def setup_optimized_logging(log_dir: str = "logs", 
                           log_level: str = "INFO",
                           enable_file: bool = True,
                           enable_console: bool = True):
    """최적화된 로깅 설정"""
    
    # 로그 레벨 변환
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    log_level = level_map.get(log_level.upper(), logging.INFO)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 기존 핸들러 제거
    root_logger.handlers.clear()
    
    # 구조화된 포맷터
    formatter = StructuredFormatter()
    
    # 파일 로깅 (Vercel/읽기전용에서는 스킵)
    if enable_file:
        _log_dir = Path("/tmp/logs") if os.environ.get("VERCEL") == "1" else Path(log_dir)
        try:
            _log_dir.mkdir(parents=True, exist_ok=True)
            log_file = _log_dir / "app.log"
            file_handler = CompressedRotatingFileHandler(
                str(log_file),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except OSError:
            pass  # 읽기 전용 파일시스템
    
    # 콘솔 로깅
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return root_logger


def compress_old_logs(log_dir: str = "logs", days: int = 7):
    """오래된 로그 파일 압축"""
    log_path = Path(log_dir)
    if not log_path.exists():
        return
    
    import time
    current_time = time.time()
    cutoff_time = current_time - (days * 24 * 60 * 60)
    
    compressed_count = 0
    for log_file in log_path.glob("*.log"):
        if log_file.stat().st_mtime < cutoff_time:
            compressed_file = log_file.with_suffix('.log.gz')
            if not compressed_file.exists():
                try:
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            f_out.writelines(f_in)
                    os.remove(log_file)
                    compressed_count += 1
                except Exception as e:
                    pass
    
    return compressed_count
