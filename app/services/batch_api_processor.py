"""
배치 API 호출 프로세서
여러 API 요청을 배치로 처리하여 비용 절감
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, Awaitable
from collections import deque
from dataclasses import dataclass
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class BatchRequest:
    """배치 요청 데이터 클래스"""
    request_data: Dict[str, Any]
    future: asyncio.Future
    timestamp: float


class BatchAPIProcessor:
    """배치 API 호출 프로세서"""
    
    def __init__(self, batch_size: int = 10, 
                 batch_interval: float = 0.5,
                 max_wait_time: float = 2.0):
        """
        Args:
            batch_size: 배치 크기 (최대 몇 개의 요청을 한 번에 처리)
            batch_interval: 배치 처리 간격 (초)
            max_wait_time: 최대 대기 시간 (초)
        """
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        self.max_wait_time = max_wait_time
        self.request_queue: deque = deque()
        self.processing = False
        self.lock = asyncio.Lock()
        self.processor_task: Optional[asyncio.Task] = None
    
    async def add_request(self, request_data: Dict[str, Any], 
                         processor_func: Callable[[List[Dict[str, Any]]], Awaitable[List[Any]]]) -> Any:
        """
        요청을 큐에 추가하고 결과를 반환
        
        Args:
            request_data: 요청 데이터
            processor_func: 배치 처리 함수
            
        Returns:
            처리 결과
        """
        future = asyncio.Future()
        
        async with self.lock:
            self.request_queue.append(BatchRequest(
                request_data=request_data,
                future=future,
                timestamp=time.time()
            ))
            
            # 프로세서가 실행 중이 아니면 시작
            if not self.processing:
                self.processing = True
                self.processor_task = asyncio.create_task(
                    self._process_batch(processor_func)
                )
        
        return await future
    
    async def _process_batch(self, processor_func: Callable[[List[Dict[str, Any]]], Awaitable[List[Any]]]):
        """배치 처리"""
        try:
            while True:
                await asyncio.sleep(self.batch_interval)
                
                async with self.lock:
                    if not self.request_queue:
                        break
                    
                    # 배치 수집
                    batch = []
                    current_time = time.time()
                    
                    # 최대 대기 시간 초과 요청 처리
                    while self.request_queue:
                        request = self.request_queue[0]
                        if current_time - request.timestamp >= self.max_wait_time:
                            batch.append(self.request_queue.popleft())
                        elif len(batch) >= self.batch_size:
                            break
                        else:
                            break
                    
                    # 배치 크기만큼 수집
                    while len(batch) < self.batch_size and self.request_queue:
                        batch.append(self.request_queue.popleft())
                    
                    if not batch:
                        continue
                    
                    # 배치 처리
                    try:
                        batch_requests = [req.request_data for req in batch]
                        results = await processor_func(batch_requests)
                        
                        # 결과 할당
                        for req, result in zip(batch, results):
                            if not req.future.done():
                                req.future.set_result(result)
                    except Exception as e:
                        logger.error(f"배치 처리 오류: {e}")
                        # 오류 발생 시 각 요청에 오류 전달
                        for req in batch:
                            if not req.future.done():
                                req.future.set_exception(e)
        
        except asyncio.CancelledError:
            logger.info("배치 프로세서 취소됨")
        except Exception as e:
            logger.error(f"배치 프로세서 오류: {e}")
        finally:
            async with self.lock:
                self.processing = False
                # 남은 요청 처리
                while self.request_queue:
                    req = self.request_queue.popleft()
                    if not req.future.done():
                        req.future.set_exception(Exception("배치 프로세서 종료"))
    
    async def flush(self, processor_func: Callable[[List[Dict[str, Any]]], Awaitable[List[Any]]]):
        """큐에 있는 모든 요청을 즉시 처리"""
        async with self.lock:
            if not self.request_queue:
                return
            
            batch = []
            while self.request_queue:
                batch.append(self.request_queue.popleft())
            
            if batch:
                try:
                    batch_requests = [req.request_data for req in batch]
                    results = await processor_func(batch_requests)
                    
                    for req, result in zip(batch, results):
                        if not req.future.done():
                            req.future.set_result(result)
                except Exception as e:
                    logger.error(f"배치 플러시 오류: {e}")
                    for req in batch:
                        if not req.future.done():
                            req.future.set_exception(e)
    
    def get_queue_size(self) -> int:
        """큐 크기 조회"""
        return len(self.request_queue)
    
    def stop(self):
        """프로세서 중지"""
        if self.processor_task:
            self.processor_task.cancel()


class OpenAIBatchProcessor:
    """OpenAI API 배치 처리"""
    
    def __init__(self, batch_size: int = 10, batch_interval: float = 0.5):
        self.processor = BatchAPIProcessor(
            batch_size=batch_size,
            batch_interval=batch_interval
        )
    
    async def generate_content_batch(self, requests: List[Dict[str, Any]]) -> List[Any]:
        """콘텐츠 생성 배치 처리"""
        import openai
        from app.config import settings
        
        # OpenAI 클라이언트 초기화
        client = openai.AsyncOpenAI(api_key=settings.get_openai_api_key())
        
        # 배치로 처리 (OpenAI는 배치 API를 지원하지 않으므로 병렬 처리)
        tasks = []
        for req in requests:
            task = client.chat.completions.create(
                model=req.get('model', 'gpt-4o-mini'),
                messages=req.get('messages', []),
                max_tokens=req.get('max_tokens', 2000),
                temperature=req.get('temperature', 0.7)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def add_generation_request(self, text: str, keywords: str, 
                                     content_length: str = "3000") -> Any:
        """콘텐츠 생성 요청 추가"""
        request_data = {
            'text': text,
            'keywords': keywords,
            'content_length': content_length,
            'model': 'gpt-4o-mini',
            'messages': [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Generate content for: {text}, Keywords: {keywords}"}
            ],
            'max_tokens': int(content_length) * 2,
            'temperature': 0.7
        }
        
        return await self.processor.add_request(request_data, self.generate_content_batch)


class GeminiBatchProcessor:
    """Gemini API 배치 처리"""
    
    def __init__(self, batch_size: int = 10, batch_interval: float = 0.5):
        self.processor = BatchAPIProcessor(
            batch_size=batch_size,
            batch_interval=batch_interval
        )
    
    async def generate_content_batch(self, requests: List[Dict[str, Any]]) -> List[Any]:
        """콘텐츠 생성 배치 처리"""
        import google.generativeai as genai
        from app.config import settings
        
        # Gemini 클라이언트 초기화
        genai.configure(api_key=settings.get_gemini_api_key())
        model = genai.GenerativeModel(settings.gemini_model)
        
        # 배치로 처리 (병렬 처리)
        tasks = []
        for req in requests:
            prompt = req.get('prompt', '')
            task = model.generate_content_async(prompt)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 응답 추출
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(result)
            else:
                try:
                    processed_results.append(result.text)
                except Exception as e:
                    processed_results.append(e)
        
        return processed_results
    
    async def add_generation_request(self, text: str, keywords: str, 
                                     content_length: str = "3000") -> Any:
        """콘텐츠 생성 요청 추가"""
        request_data = {
            'text': text,
            'keywords': keywords,
            'content_length': content_length,
            'prompt': f"Generate content for: {text}, Keywords: {keywords}"
        }
        
        return await self.processor.add_request(request_data, self.generate_content_batch)


# 전역 배치 프로세서 인스턴스
openai_batch_processor = OpenAIBatchProcessor(batch_size=10, batch_interval=0.5)
gemini_batch_processor = GeminiBatchProcessor(batch_size=10, batch_interval=0.5)
