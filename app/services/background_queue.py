"""
백그라운드 작업 큐 구현
긴 작업을 백그라운드에서 처리하여 API 응답 시간 단축
"""

import asyncio
import threading
import uuid
import time
from typing import Dict, Any, Optional, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from queue import Queue, Empty
import json

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackgroundTask:
    """백그라운드 작업 데이터 클래스"""
    task_id: str
    task_type: str
    task_data: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress: float = 0.0
    progress_message: Optional[str] = None


class BackgroundTaskQueue:
    """백그라운드 작업 큐"""
    
    def __init__(self, max_workers: int = 4, max_queue_size: int = 100):
        """
        Args:
            max_workers: 최대 작업자 수
            max_queue_size: 최대 큐 크기
        """
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.task_queue: Queue = Queue(maxsize=max_queue_size)
        self.tasks: Dict[str, BackgroundTask] = {}
        self.workers: list = []
        self.running = False
        self.lock = threading.Lock()
        self.task_handlers: Dict[str, Callable] = {}
    
    def register_handler(self, task_type: str, handler: Callable):
        """작업 핸들러 등록"""
        self.task_handlers[task_type] = handler
        logger.info(f"작업 핸들러 등록: {task_type}")
    
    def start(self):
        """작업 큐 시작"""
        if self.running:
            return
        
        self.running = True
        
        # 작업자 스레드 시작
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"BackgroundWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"백그라운드 작업 큐 시작: {self.max_workers}개 작업자")
    
    def stop(self, timeout: float = 5.0):
        """작업 큐 중지"""
        if not self.running:
            return
        
        self.running = False
        
        # 작업자 스레드 종료 대기
        for worker in self.workers:
            worker.join(timeout=timeout)
        
        self.workers.clear()
        logger.info("백그라운드 작업 큐 중지")
    
    def add_task(self, task_type: str, task_data: Dict[str, Any]) -> str:
        """
        작업 추가
        
        Args:
            task_type: 작업 타입
            task_data: 작업 데이터
            
        Returns:
            작업 ID
        """
        task_id = str(uuid.uuid4())
        
        task = BackgroundTask(
            task_id=task_id,
            task_type=task_type,
            task_data=task_data
        )
        
        with self.lock:
            self.tasks[task_id] = task
            
            try:
                self.task_queue.put(task, block=False)
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = f"큐 추가 실패: {str(e)}"
                logger.error(f"작업 큐 추가 실패: {e}")
        
        logger.info(f"작업 추가: {task_id} ({task_type})")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """작업 조회"""
        with self.lock:
            return self.tasks.get(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        task = self.get_task(task_id)
        if not task:
            return None
        
        return {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'status': task.status.value,
            'progress': task.progress,
            'progress_message': task.progress_message,
            'created_at': task.created_at,
            'started_at': task.started_at,
            'completed_at': task.completed_at,
            'error': task.error
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """작업 취소"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            
            if task.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return False
            
            task.status = TaskStatus.CANCELLED
            task.completed_at = time.time()
            logger.info(f"작업 취소: {task_id}")
            return True
    
    def _worker_loop(self):
        """작업자 루프"""
        while self.running:
            try:
                # 큐에서 작업 가져오기 (타임아웃 1초)
                try:
                    task = self.task_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # 작업 실행
                self._execute_task(task)
                
                # 작업 완료 표시
                self.task_queue.task_done()
            
            except Exception as e:
                logger.error(f"작업자 루프 오류: {e}")
    
    def _execute_task(self, task: BackgroundTask):
        """작업 실행"""
        handler = self.task_handlers.get(task.task_type)
        if not handler:
            task.status = TaskStatus.FAILED
            task.error = f"작업 핸들러를 찾을 수 없습니다: {task.task_type}"
            task.completed_at = time.time()
            logger.error(f"작업 핸들러 없음: {task.task_type}")
            return
        
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        
        try:
            # 작업 실행
            if asyncio.iscoroutinefunction(handler):
                # 비동기 함수인 경우
                result = asyncio.run(handler(task))
            else:
                # 동기 함수인 경우
                result = handler(task)
            
            task.result = result
            task.status = TaskStatus.SUCCESS
            task.progress = 1.0
            task.progress_message = "완료"
            logger.info(f"작업 완료: {task.task_id}")
        
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"작업 실패: {task.task_id} - {e}")
        
        finally:
            task.completed_at = time.time()
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """큐 통계 조회"""
        with self.lock:
            status_counts = {}
            for task in self.tasks.values():
                status = task.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                'queue_size': self.task_queue.qsize(),
                'max_queue_size': self.max_queue_size,
                'max_workers': self.max_workers,
                'active_workers': len([w for w in self.workers if w.is_alive()]),
                'total_tasks': len(self.tasks),
                'status_counts': status_counts
            }


# 전역 백그라운드 작업 큐 인스턴스
background_queue = BackgroundTaskQueue(max_workers=4, max_queue_size=100)


# 작업 핸들러 등록
def register_task_handlers():
    """작업 핸들러 등록"""
    from app.services.google_docs_service import google_docs_service
    from app import crud, models
    from app.database import SessionLocal
    
    async def archive_blog_post_handler(task: BackgroundTask):
        """블로그 포스트 Archive 작업 핸들러"""
        task.progress_message = "Archive 작업 시작"
        
        post_id = task.task_data.get('post_id')
        if not post_id:
            raise ValueError("post_id가 필요합니다")
        
        db = SessionLocal()
        try:
            # 블로그 포스트 조회
            blog_post = crud.get_blog_post(db, post_id)
            if not blog_post:
                raise ValueError(f"블로그 포스트를 찾을 수 없습니다: {post_id}")
            
            task.progress_message = "Google Docs 인증 중"
            task.progress = 0.3
            
            # Google Docs 서비스 인증
            if not google_docs_service.authenticate():
                raise ValueError("Google Docs 서비스 인증 실패")
            
            task.progress_message = "Archive 폴더 확인 중"
            task.progress = 0.5
            
            # Archive 폴더 확인
            from app.config import settings
            folder_id = google_docs_service.create_archive_folder(settings.google_docs_archive_folder)
            if not folder_id:
                raise ValueError("Archive 폴더 생성 실패")
            
            task.progress_message = "문서 생성 중"
            task.progress = 0.7
            
            # Archive 데이터 준비
            archive_data = {
                'title': blog_post.title,
                'content': blog_post.content_html,
                'keywords': blog_post.keywords,
                'source_url': blog_post.original_url,
                'ai_mode': blog_post.ai_mode or "default",
                'summary': '',
                'created_at': blog_post.created_at.isoformat() if blog_post.created_at else datetime.now().isoformat()
            }
            
            # Google Docs 문서 생성
            doc_url = google_docs_service.create_blog_post_document(archive_data, folder_id)
            
            task.progress_message = "완료"
            task.progress = 1.0
            
            return {'doc_url': doc_url, 'post_id': post_id}
        
        finally:
            db.close()
    
    background_queue.register_handler('archive_blog_post', archive_blog_post_handler)
    logger.info("작업 핸들러 등록 완료")


# 애플리케이션 시작 시 작업 큐 시작 및 핸들러 등록
try:
    background_queue.start()
    register_task_handlers()
except Exception as e:
    logger.warning(f"백그라운드 작업 큐 초기화 실패: {e}")
