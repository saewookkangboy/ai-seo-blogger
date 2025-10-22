#!/usr/bin/env python3
"""
에러 처리 및 디버깅 서비스
시스템 전반의 에러를 체계적으로 처리하고 디버깅 정보를 제공합니다.
"""

import traceback
import sys
import json
import time
import asyncio
from typing import Dict, Any, Optional, List
from functools import wraps
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ErrorHandler:
    """에러 처리 클래스"""
    
    def __init__(self):
        self.error_log = []
        self.error_counts = {}
        self.max_error_log_size = 1000
        
    def log_error(self, error: Exception, context: Dict[str, Any] = None, severity: str = "ERROR"):
        """에러 로깅"""
        error_info = {
            'timestamp': time.time(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'severity': severity
        }
        
        # 에러 카운트 증가
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # 에러 로그에 추가
        self.error_log.append(error_info)
        
        # 로그 크기 제한
        if len(self.error_log) > self.max_error_log_size:
            self.error_log = self.error_log[-self.max_error_log_size:]
        
        # 로그 출력
        logger.error(f"에러 발생: {error_type} - {error}")
        if context:
            logger.error(f"컨텍스트: {context}")
        
        return error_info
    
    def get_error_stats(self) -> Dict[str, Any]:
        """에러 통계 반환"""
        return {
            'total_errors': len(self.error_log),
            'error_counts': self.error_counts,
            'recent_errors': self.error_log[-10:] if self.error_log else []
        }
    
    def clear_error_log(self):
        """에러 로그 정리"""
        self.error_log.clear()
        self.error_counts.clear()
        logger.info("에러 로그가 정리되었습니다.")
    
    def error_handler(self, fallback_value=None, log_error=True):
        """에러 처리 데코레이터"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if log_error:
                        self.log_error(e, {
                            'function': func.__name__,
                            'args': str(args),
                            'kwargs': str(kwargs)
                        })
                    return fallback_value
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if log_error:
                        self.log_error(e, {
                            'function': func.__name__,
                            'args': str(args),
                            'kwargs': str(kwargs)
                        })
                    return fallback_value
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        return decorator
    
    def retry_on_error(self, max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
        """재시도 데코레이터"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_error = None
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        if attempt < max_retries:
                            wait_time = delay * (backoff_factor ** attempt)
                            logger.warning(f"{func.__name__} 재시도 {attempt + 1}/{max_retries + 1} ({wait_time:.1f}초 후)")
                            await asyncio.sleep(wait_time)
                        else:
                            self.log_error(e, {
                                'function': func.__name__,
                                'attempts': max_retries + 1,
                                'args': str(args),
                                'kwargs': str(kwargs)
                            })
                            raise last_error
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_error = None
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        if attempt < max_retries:
                            wait_time = delay * (backoff_factor ** attempt)
                            logger.warning(f"{func.__name__} 재시도 {attempt + 1}/{max_retries + 1} ({wait_time:.1f}초 후)")
                            time.sleep(wait_time)
                        else:
                            self.log_error(e, {
                                'function': func.__name__,
                                'attempts': max_retries + 1,
                                'args': str(args),
                                'kwargs': str(kwargs)
                            })
                            raise last_error
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        return decorator

class DebugHelper:
    """디버깅 헬퍼 클래스"""
    
    @staticmethod
    def debug_info(func_name: str, **kwargs) -> Dict[str, Any]:
        """디버깅 정보 생성"""
        return {
            'function': func_name,
            'timestamp': time.time(),
            'parameters': kwargs,
            'memory_usage': sys.getsizeof(kwargs)
        }
    
    @staticmethod
    def log_debug_info(info: Dict[str, Any]):
        """디버깅 정보 로깅"""
        logger.debug(f"디버깅 정보: {json.dumps(info, default=str, indent=2)}")
    
    @staticmethod
    def validate_input(data: Any, expected_type: type, field_name: str = "data"):
        """입력 데이터 검증"""
        if not isinstance(data, expected_type):
            raise ValueError(f"{field_name}는 {expected_type.__name__} 타입이어야 합니다. 현재: {type(data).__name__}")
        return data
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """URL 유효성 검사"""
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// 또는 https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # 도메인
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP 주소
            r'(?::\d+)?'  # 포트 (선택사항)
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(url))

# 전역 인스턴스
error_handler = ErrorHandler()
debug_helper = DebugHelper()

# 유틸리티 함수들
def handle_errors(fallback_value=None, log_error=True):
    """에러 처리 데코레이터"""
    return error_handler.error_handler(fallback_value, log_error)

def retry_on_error(max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
    """재시도 데코레이터"""
    return error_handler.retry_on_error(max_retries, delay, backoff_factor)

def debug_info(func_name: str, **kwargs):
    """디버깅 정보 생성"""
    return debug_helper.debug_info(func_name, **kwargs)

def validate_input(data: Any, expected_type: type, field_name: str = "data"):
    """입력 데이터 검증"""
    return debug_helper.validate_input(data, expected_type, field_name)

def validate_url(url: str) -> bool:
    """URL 유효성 검사"""
    return debug_helper.validate_url(url) 