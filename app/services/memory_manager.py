"""
메모리 관리 최적화 서비스
메모리 누수 방지, 가비지 컬렉션 최적화
"""

import gc
import weakref
import psutil
import os
import threading
import time
from typing import Dict, Any, Optional, List
from collections import defaultdict
from app.utils.logger import setup_logger
from app.config import settings

logger = setup_logger(__name__)

class MemoryManager:
    """메모리 관리 클래스"""
    
    def __init__(self, max_memory_mb: int = 1024, cleanup_interval: int = 300):
        """
        Args:
            max_memory_mb: 최대 메모리 사용량 (MB)
            cleanup_interval: 정리 주기 (초)
        """
        self.max_memory_mb = max_memory_mb
        self.cleanup_interval = cleanup_interval
        self.process = psutil.Process(os.getpid())
        self.weak_refs = weakref.WeakValueDictionary()
        self.memory_history: List[Dict[str, float]] = []
        self.cleanup_thread: Optional[threading.Thread] = None
        self.running = False
        self.lock = threading.RLock()
        
        # 메모리 사용 패턴 추적
        self.memory_patterns = defaultdict(list)
    
    def start_monitoring(self):
        """메모리 모니터링 시작"""
        if self.running:
            return
        
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        logger.info("메모리 모니터링 시작")
    
    def stop_monitoring(self):
        """메모리 모니터링 중지"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        logger.info("메모리 모니터링 중지")
    
    def _cleanup_loop(self):
        """정리 루프 (백그라운드 스레드)"""
        while self.running:
            try:
                time.sleep(self.cleanup_interval)
                self.cleanup_memory()
                self._log_memory_usage()
            except Exception as e:
                logger.error(f"메모리 정리 루프 오류: {e}")
    
    def get_memory_usage(self) -> Dict[str, float]:
        """메모리 사용량 조회"""
        try:
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,  # 물리 메모리
                'vms_mb': memory_info.vms / 1024 / 1024,  # 가상 메모리
                'percent': memory_percent,
                'available_mb': psutil.virtual_memory().available / 1024 / 1024,
                'total_mb': psutil.virtual_memory().total / 1024 / 1024
            }
        except Exception as e:
            logger.error(f"메모리 사용량 조회 오류: {e}")
            return {
                'rss_mb': 0,
                'vms_mb': 0,
                'percent': 0,
                'available_mb': 0,
                'total_mb': 0
            }
    
    def cleanup_memory(self) -> Dict[str, Any]:
        """메모리 정리"""
        with self.lock:
            before_usage = self.get_memory_usage()
            
            # 가비지 컬렉션 실행
            collected = gc.collect()
            
            # 약한 참조 정리
            self._cleanup_weak_refs()
            
            after_usage = self.get_memory_usage()
            
            freed_mb = before_usage['rss_mb'] - after_usage['rss_mb']
            
            result = {
                'collected_objects': collected,
                'freed_mb': freed_mb,
                'before_mb': before_usage['rss_mb'],
                'after_mb': after_usage['rss_mb'],
                'current_percent': after_usage['percent']
            }
            
            if freed_mb > 0:
                logger.info(f"메모리 정리 완료: {freed_mb:.2f}MB 해제, {collected}개 객체 수집")
            
            return result
    
    def _cleanup_weak_refs(self):
        """약한 참조 정리"""
        try:
            # 약한 참조 딕셔너리는 자동으로 정리됨
            # 수동으로 정리할 필요는 없지만, 로깅을 위해 확인
            initial_count = len(self.weak_refs)
            # 약한 참조는 자동으로 정리되므로 별도 작업 불필요
        except Exception as e:
            logger.error(f"약한 참조 정리 오류: {e}")
    
    def check_memory_threshold(self) -> bool:
        """메모리 임계값 확인"""
        usage = self.get_memory_usage()
        
        # 메모리 사용량이 임계값을 초과하는지 확인
        if usage['rss_mb'] > self.max_memory_mb:
            logger.warning(
                f"⚠️ 메모리 사용량이 임계값을 초과했습니다: "
                f"{usage['rss_mb']:.2f}MB / {self.max_memory_mb}MB "
                f"({usage['percent']:.2f}%)"
            )
            return True
        
        return False
    
    def optimize_memory(self) -> Dict[str, Any]:
        """메모리 최적화 실행"""
        with self.lock:
            # 메모리 정리
            cleanup_result = self.cleanup_memory()
            
            # 메모리 사용량 확인
            usage = self.get_memory_usage()
            
            # 임계값 초과 시 추가 정리
            if self.check_memory_threshold():
                # 추가 가비지 컬렉션
                gc.collect(2)  # 모든 세대 수집
                
                # 메모리 사용량 재확인
                usage = self.get_memory_usage()
            
            return {
                'cleanup': cleanup_result,
                'current_usage': usage,
                'threshold_exceeded': usage['rss_mb'] > self.max_memory_mb
            }
    
    def _log_memory_usage(self):
        """메모리 사용량 로깅"""
        usage = self.get_memory_usage()
        self.memory_history.append({
            'timestamp': time.time(),
            'rss_mb': usage['rss_mb'],
            'percent': usage['percent']
        })
        
        # 최근 100개만 유지
        if len(self.memory_history) > 100:
            self.memory_history = self.memory_history[-100:]
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """메모리 통계 조회"""
        usage = self.get_memory_usage()
        
        # 메모리 히스토리 분석
        if self.memory_history:
            recent = self.memory_history[-10:]  # 최근 10개
            avg_rss = sum(h['rss_mb'] for h in recent) / len(recent)
            max_rss = max(h['rss_mb'] for h in recent)
            min_rss = min(h['rss_mb'] for h in recent)
        else:
            avg_rss = usage['rss_mb']
            max_rss = usage['rss_mb']
            min_rss = usage['rss_mb']
        
        return {
            'current': usage,
            'history': {
                'count': len(self.memory_history),
                'avg_rss_mb': round(avg_rss, 2),
                'max_rss_mb': round(max_rss, 2),
                'min_rss_mb': round(min_rss, 2)
            },
            'threshold': {
                'max_mb': self.max_memory_mb,
                'exceeded': usage['rss_mb'] > self.max_memory_mb
            },
            'gc': {
                'counts': gc.get_count(),
                'thresholds': gc.get_threshold()
            }
    }
    
    def register_weak_ref(self, name: str, obj: Any):
        """약한 참조 등록"""
        with self.lock:
            self.weak_refs[name] = obj
    
    def configure_gc(self, generation: int = 0, threshold: int = 700):
        """가비지 컬렉션 설정 조정"""
        try:
            gc.set_threshold(threshold, threshold * 2, threshold * 3)
            logger.info(f"가비지 컬렉션 임계값 설정: {gc.get_threshold()}")
        except Exception as e:
            logger.error(f"가비지 컬렉션 설정 오류: {e}")


# 전역 메모리 관리자 인스턴스
memory_manager = MemoryManager(
    max_memory_mb=getattr(settings, 'max_memory_mb', 1024),
    cleanup_interval=getattr(settings, 'memory_cleanup_interval', 300)
)

# 애플리케이션 시작 시 모니터링 시작
try:
    memory_manager.start_monitoring()
except Exception as e:
    logger.warning(f"메모리 모니터링 시작 실패: {e}")
