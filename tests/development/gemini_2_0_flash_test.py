#!/usr/bin/env python3
"""
Gemini 2.0 Flash API 테스트 스크립트
크롤링, 번역, 키워드 추출 전체 파이프라인을 테스트합니다.
"""

import asyncio
import sys
import os
import json
from datetime import datetime
import time

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.crawler import crawl_url
from app.services.translator import translate_text_gemini
from app.services.content_generator import extract_seo_keywords
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class Gemini2FlashPipelineTest:
    """Gemini 2.0 Flash 파이프라인 테스트 클래스"""
    
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {}
        }
        
    async def test_crawling(self, test_url: str) -> dict:
        """크롤링 테스트"""
        logger.info(f"크롤링 테스트 시작: {test_url}")
        start_time = time.time()
        
        try:
            # 크롤링 수행
            content = crawl_url(test_url)
            
            if content:
                duration = time.time() - start_time
                result = {
                    "test": "crawling",
                    "url": test_url,
                    "status": "success",
                    "content_length": len(content),
                    "duration": round(duration, 2),
                    "content_preview": content[:200] + "..." if len(content) > 200 else content
                }
                logger.info(f"크롤링 성공: {len(content)}자, {duration:.2f}초")
                return result
            else:
                duration = time.time() - start_time
                result = {
                    "test": "crawling",
                    "url": test_url,
                    "status": "failed",
                    "error": "크롤링된 콘텐츠가 없습니다",
                    "duration": round(duration, 2)
                }
                logger.error("크롤링 실패: 콘텐츠가 없습니다")
                return result
                
        except Exception as e:
            duration = time.time() - start_time
            result = {
                "test": "crawling",
                "url": test_url,
                "status": "error",
                "error": str(e),
                "duration": round(duration, 2)
            }
            logger.error(f"크롤링 오류: {e}")
            return result
    
    async def test_translation(self, text: str) -> dict:
        """번역 테스트"""
        logger.info(f"번역 테스트 시작: {len(text)}자")
        start_time = time.time()
        
        try:
            # 번역 수행
            translated = await translate_text_gemini(text, "ko")
            
            if translated:
                duration = time.time() - start_time
                result = {
                    "test": "translation",
                    "original_length": len(text),
                    "translated_length": len(translated),
                    "status": "success",
                    "duration": round(duration, 2),
                    "translated_preview": translated[:200] + "..." if len(translated) > 200 else translated
                }
                logger.info(f"번역 성공: {len(translated)}자, {duration:.2f}초")
                return result
            else:
                duration = time.time() - start_time
                result = {
                    "test": "translation",
                    "status": "failed",
                    "error": "번역 결과가 없습니다",
                    "duration": round(duration, 2)
                }
                logger.error("번역 실패: 결과가 없습니다")
                return result
                
        except Exception as e:
            duration = time.time() - start_time
            result = {
                "test": "translation",
                "status": "error",
                "error": str(e),
                "duration": round(duration, 2)
            }
            logger.error(f"번역 오류: {e}")
            return result
    
    async def test_keyword_extraction(self, text: str) -> dict:
        """키워드 추출 테스트"""
        logger.info(f"키워드 추출 테스트 시작: {len(text)}자")
        start_time = time.time()
        
        try:
            # 키워드 추출 수행
            keywords = await extract_seo_keywords(text)
            
            if keywords:
                duration = time.time() - start_time
                result = {
                    "test": "keyword_extraction",
                    "text_length": len(text),
                    "keywords_count": len(keywords.split(",")),
                    "status": "success",
                    "duration": round(duration, 2),
                    "keywords": keywords
                }
                logger.info(f"키워드 추출 성공: {keywords}, {duration:.2f}초")
                return result
            else:
                duration = time.time() - start_time
                result = {
                    "test": "keyword_extraction",
                    "status": "failed",
                    "error": "키워드 추출 결과가 없습니다",
                    "duration": round(duration, 2)
                }
                logger.error("키워드 추출 실패: 결과가 없습니다")
                return result
                
        except Exception as e:
            duration = time.time() - start_time
            result = {
                "test": "keyword_extraction",
                "status": "error",
                "error": str(e),
                "duration": round(duration, 2)
            }
            logger.error(f"키워드 추출 오류: {e}")
            return result
    
    async def test_full_pipeline(self, test_url: str) -> dict:
        """전체 파이프라인 테스트"""
        logger.info(f"전체 파이프라인 테스트 시작: {test_url}")
        start_time = time.time()
        
        pipeline_results = {
            "test": "full_pipeline",
            "url": test_url,
            "steps": [],
            "status": "success",
            "total_duration": 0
        }
        
        try:
            # 1단계: 크롤링
            crawling_result = await self.test_crawling(test_url)
            pipeline_results["steps"].append(crawling_result)
            
            if crawling_result["status"] != "success":
                pipeline_results["status"] = "failed"
                pipeline_results["error"] = "크롤링 실패"
                return pipeline_results
            
            content = crawling_result["content_preview"]
            
            # 2단계: 번역
            translation_result = await self.test_translation(content)
            pipeline_results["steps"].append(translation_result)
            
            if translation_result["status"] != "success":
                pipeline_results["status"] = "failed"
                pipeline_results["error"] = "번역 실패"
                return pipeline_results
            
            translated_content = translation_result["translated_preview"]
            
            # 3단계: 키워드 추출
            keyword_result = await self.test_keyword_extraction(translated_content)
            pipeline_results["steps"].append(keyword_result)
            
            if keyword_result["status"] != "success":
                pipeline_results["status"] = "failed"
                pipeline_results["error"] = "키워드 추출 실패"
                return pipeline_results
            
            # 전체 결과
            total_duration = time.time() - start_time
            pipeline_results["total_duration"] = round(total_duration, 2)
            pipeline_results["final_keywords"] = keyword_result["keywords"]
            
            logger.info(f"전체 파이프라인 성공: {total_duration:.2f}초")
            return pipeline_results
            
        except Exception as e:
            total_duration = time.time() - start_time
            pipeline_results["status"] = "error"
            pipeline_results["error"] = str(e)
            pipeline_results["total_duration"] = round(total_duration, 2)
            logger.error(f"전체 파이프라인 오류: {e}")
            return pipeline_results
    
    def save_results(self, filename: str = None):
        """테스트 결과를 파일로 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gemini_2_0_flash_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            logger.info(f"테스트 결과가 {filename}에 저장되었습니다.")
        except Exception as e:
            logger.error(f"결과 저장 실패: {e}")
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "="*60)
        print("Gemini 2.0 Flash 파이프라인 테스트 결과")
        print("="*60)
        
        total_tests = len(self.test_results["tests"])
        successful_tests = sum(1 for test in self.test_results["tests"] if test.get("status") == "success")
        failed_tests = total_tests - successful_tests
        
        print(f"총 테스트 수: {total_tests}")
        print(f"성공: {successful_tests}")
        print(f"실패: {failed_tests}")
        print(f"성공률: {(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        if self.test_results["tests"]:
            print("\n상세 결과:")
            for i, test in enumerate(self.test_results["tests"], 1):
                print(f"{i}. {test.get('test', 'unknown')}: {test.get('status', 'unknown')}")
                if test.get('duration'):
                    print(f"   소요시간: {test['duration']}초")
                if test.get('error'):
                    print(f"   오류: {test['error']}")

async def main():
    """메인 테스트 함수"""
    print("Gemini 2.0 Flash 파이프라인 테스트를 시작합니다...")
    
    # API 키 확인 - Gemini API 숨김 처리됨
    # if not settings.get_gemini_api_key():
    #     print("❌ Gemini API 키가 설정되지 않았습니다.")
    #     print("환경변수 GEMINI_API_KEY를 설정해주세요.")
    #     return
    
    # print("✅ Gemini API 키가 설정되었습니다.")
    print("ℹ️ Gemini API 기능이 숨김 처리되었습니다.")
    
    # 테스트 인스턴스 생성
    tester = Gemini2FlashPipelineTest()
    
    # 테스트 URL들
    test_urls = [
        "https://www.searchengineland.com/google-core-update-may-2024-447123",
        "https://www.socialmediatoday.com/news/meta-announces-new-ai-features-for-instagram-and-facebook/",
        "https://techcrunch.com/2024/01/15/ai-trends-2024/"
    ]
    
    # 개별 테스트
    print("\n1. 개별 기능 테스트...")
    
    # 크롤링 테스트
    for url in test_urls[:1]:  # 첫 번째 URL만 테스트
        result = await tester.test_crawling(url)
        tester.test_results["tests"].append(result)
    
    # 번역 테스트 (샘플 텍스트)
    sample_text = """
    Artificial Intelligence (AI) is transforming the way we live and work. 
    From virtual assistants to autonomous vehicles, AI technologies are becoming 
    increasingly integrated into our daily lives. Machine learning algorithms 
    can now process vast amounts of data to identify patterns and make predictions 
    with remarkable accuracy.
    """
    result = await tester.test_translation(sample_text)
    tester.test_results["tests"].append(result)
    
    # 키워드 추출 테스트
    result = await tester.test_keyword_extraction(sample_text)
    tester.test_results["tests"].append(result)
    
    # 전체 파이프라인 테스트
    print("\n2. 전체 파이프라인 테스트...")
    for url in test_urls[:1]:  # 첫 번째 URL만 테스트
        result = await tester.test_full_pipeline(url)
        tester.test_results["tests"].append(result)
    
    # 결과 저장 및 출력
    tester.save_results()
    tester.print_summary()
    
    print("\n✅ 테스트가 완료되었습니다!")

if __name__ == "__main__":
    asyncio.run(main()) 