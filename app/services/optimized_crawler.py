"""
크롤링 최적화 서비스
병렬 처리, 우선순위 큐, 스마트 캐싱
"""

import asyncio
import aiohttp
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import threading
from bs4 import BeautifulSoup
import re

from app.utils.logger import setup_logger
from app.services.lru_cache import crawling_cache

logger = setup_logger(__name__)


class CrawlPriority(Enum):
    """크롤링 우선순위"""
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class CrawlTask:
    """크롤링 작업 데이터 클래스"""
    url: str
    priority: CrawlPriority = CrawlPriority.MEDIUM
    timeout: int = 10
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)


class PriorityCrawler:
    """우선순위 기반 크롤러"""
    
    def __init__(self, max_concurrent: int = 10, 
                 max_queue_size: int = 100,
                 default_timeout: int = 10):
        """
        Args:
            max_concurrent: 최대 동시 크롤링 수
            max_queue_size: 최대 큐 크기
            default_timeout: 기본 타임아웃 (초)
        """
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.default_timeout = default_timeout
        self.priority_queue: Dict[CrawlPriority, deque] = {
            CrawlPriority.HIGH: deque(),
            CrawlPriority.MEDIUM: deque(),
            CrawlPriority.LOW: deque()
        }
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.lock = asyncio.Lock()
        self.session: Optional[aiohttp.ClientSession] = None
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'cached': 0
        }
    
    async def initialize(self):
        """초기화"""
        timeout = aiohttp.ClientTimeout(total=self.default_timeout)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=aiohttp.TCPConnector(limit=self.max_concurrent)
        )
        logger.info(f"우선순위 크롤러 초기화: 최대 동시 {self.max_concurrent}개")
    
    async def close(self):
        """종료"""
        if self.session:
            await self.session.close()
    
    async def add_url(self, url: str, priority: CrawlPriority = CrawlPriority.MEDIUM) -> str:
        """URL 추가"""
        async with self.lock:
            # 캐시 확인
            cache_key = hashlib.md5(url.encode()).hexdigest()
            cached_content = crawling_cache.get(cache_key)
            if cached_content:
                self.stats['cached'] += 1
                logger.info(f"캐시된 결과 사용: {url}")
                return cached_content
            
            # 큐 크기 확인
            total_queue_size = sum(len(q) for q in self.priority_queue.values())
            if total_queue_size >= self.max_queue_size:
                logger.warning(f"큐가 가득 찼습니다: {total_queue_size}/{self.max_queue_size}")
                return None
            
            # 작업 추가
            task = CrawlTask(url=url, priority=priority)
            self.priority_queue[priority].append(task)
            self.stats['total'] += 1
            
            logger.debug(f"URL 추가: {url} (우선순위: {priority.name})")
            return cache_key
    
    async def crawl_url(self, url: str, timeout: int = 10) -> Optional[str]:
        """단일 URL 크롤링"""
        async with self.semaphore:
            try:
                if not self.session:
                    await self.initialize()
                
                async with self.session.get(url, allow_redirects=True) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # 텍스트 추출
                        text = self._extract_text(content)
                        
                        # 캐시 저장
                        cache_key = hashlib.md5(url.encode()).hexdigest()
                        crawling_cache.set(cache_key, text, ttl=3600)
                        
                        self.stats['success'] += 1
                        logger.debug(f"크롤링 성공: {url}")
                        return text
                    else:
                        self.stats['failed'] += 1
                        logger.warning(f"크롤링 실패: {url} (상태: {response.status})")
                        return None
            
            except asyncio.TimeoutError:
                self.stats['failed'] += 1
                logger.warning(f"크롤링 타임아웃: {url}")
                return None
            except Exception as e:
                self.stats['failed'] += 1
                logger.error(f"크롤링 오류: {url} - {e}")
                return None
    
    async def crawl_batch(self, urls: List[str], 
                         priority: CrawlPriority = CrawlPriority.MEDIUM) -> Dict[str, Optional[str]]:
        """배치 크롤링"""
        results = {}
        
        # URL 추가
        for url in urls:
            await self.add_url(url, priority)
        
        # 우선순위에 따라 크롤링
        tasks = []
        for priority_level in [CrawlPriority.HIGH, CrawlPriority.MEDIUM, CrawlPriority.LOW]:
            async with self.lock:
                queue = self.priority_queue[priority_level]
                while queue:
                    task = queue.popleft()
                    tasks.append(self._crawl_task(task))
        
        # 병렬 처리
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 수집
        for i, url in enumerate(urls):
            if i < len(task_results):
                result = task_results[i]
                if isinstance(result, Exception):
                    results[url] = None
                else:
                    results[url] = result
            else:
                results[url] = None
        
        return results
    
    async def _crawl_task(self, task: CrawlTask) -> Optional[str]:
        """크롤링 작업 실행"""
        for attempt in range(task.max_retries):
            try:
                result = await self.crawl_url(task.url, task.timeout)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"크롤링 재시도 {attempt + 1}/{task.max_retries}: {task.url} - {e}")
                if attempt < task.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 지수 백오프
        
        return None
    
    def _extract_text(self, html: str) -> str:
        """HTML에서 텍스트 추출"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 스크립트, 스타일 제거
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 텍스트 추출
            text = soup.get_text()
            
            # 공백 정리
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            logger.error(f"텍스트 추출 오류: {e}")
            return ""
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""
        queue_sizes = {
            priority.name: len(queue) 
            for priority, queue in self.priority_queue.items()
        }
        
        return {
            'stats': self.stats.copy(),
            'queue_sizes': queue_sizes,
            'cache_stats': crawling_cache.get_stats(),
            'success_rate': (
                self.stats['success'] / self.stats['total'] * 100 
                if self.stats['total'] > 0 else 0
            ),
            'cache_hit_rate': (
                self.stats['cached'] / self.stats['total'] * 100 
                if self.stats['total'] > 0 else 0
            )
        }


# 전역 우선순위 크롤러 인스턴스
priority_crawler = PriorityCrawler(
    max_concurrent=10,
    max_queue_size=100,
    default_timeout=10
)
