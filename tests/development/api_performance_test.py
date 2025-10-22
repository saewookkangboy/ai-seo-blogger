#!/usr/bin/env python3
"""
API 성능 테스트 스크립트
OpenAI와 Google Gemini API의 성능을 테스트합니다.
"""

import asyncio
import time
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.content_generator import create_blog_post, extract_seo_keywords
from app.services.translator import translate_text
import logging

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIPerformanceTest:
    """API 성능 테스트 클래스"""
    
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
    
    async def test_openai_api(self) -> Dict[str, Any]:
        """OpenAI API 성능 테스트"""
        logger.info("OpenAI API 성능 테스트 시작...")
        
        test_text = "인공지능은 현대 사회에서 가장 혁신적인 기술 중 하나입니다."
        test_keywords = "인공지능, AI, 머신러닝, 딥러닝"
        
        start_time = time.time()
        try:
            response = await create_blog_post(
                text=test_text,
                keywords=test_keywords,
                content_length="1000"
            )
            end_time = time.time()
            
            result = {
                "api": "openai",
                "status": "success",
                "response_time": round(end_time - start_time, 2),
                "response_length": len(response),
                "error": None
            }
            
            logger.info(f"OpenAI API 테스트 성공: {result['response_time']}초")
            return result
            
        except Exception as e:
            end_time = time.time()
            result = {
                "api": "openai",
                "status": "error",
                "response_time": round(end_time - start_time, 2),
                "response_length": 0,
                "error": str(e)
            }
            
            logger.error(f"OpenAI API 테스트 실패: {e}")
            return result
    
    async def test_gemini_api(self) -> Dict[str, Any]:
        """Google Gemini API 성능 테스트"""
        logger.info("Google Gemini API 성능 테스트 시작...")
        
        test_text = "머신러닝은 다양한 분야에서 혁신적인 솔루션을 제공합니다."
        test_keywords = "머신러닝, ML, 인공지능, 데이터 분석"
        
        start_time = time.time()
        try:
            response = await create_blog_post(
                text=test_text,
                keywords=test_keywords,
                content_length="1000"
            )
            end_time = time.time()
            
            result = {
                "api": "gemini",
                "status": "success",
                "response_time": round(end_time - start_time, 2),
                "response_length": len(response),
                "error": None
            }
            
            logger.info(f"Gemini API 테스트 성공: {result['response_time']}초")
            return result
            
        except Exception as e:
            end_time = time.time()
            result = {
                "api": "gemini",
                "status": "error",
                "response_time": round(end_time - start_time, 2),
                "response_length": 0,
                "error": str(e)
            }
            
            logger.error(f"Gemini API 테스트 실패: {e}")
            return result
    
    async def test_translation_api(self) -> Dict[str, Any]:
        """번역 API 성능 테스트"""
        logger.info("번역 API 성능 테스트 시작...")
        
        test_text = "Artificial Intelligence is transforming the way we live and work."
        
        start_time = time.time()
        try:
            translated_text = await translate_text(
                text=test_text,
                target_lang="KO"
            )
            end_time = time.time()
            
            result = {
                "api": "translation",
                "status": "success",
                "response_time": round(end_time - start_time, 2),
                "response_length": len(translated_text),
                "error": None
            }
            
            logger.info(f"번역 API 테스트 성공: {result['response_time']}초")
            return result
            
        except Exception as e:
            end_time = time.time()
            result = {
                "api": "translation",
                "status": "error",
                "response_time": round(end_time - start_time, 2),
                "response_length": 0,
                "error": str(e)
            }
            
            logger.error(f"번역 API 테스트 실패: {e}")
            return result
    
    async def run_all_tests(self, iterations: int = 3) -> Dict[str, Any]:
        """모든 API 테스트 실행"""
        logger.info(f"API 성능 테스트 시작 (반복 횟수: {iterations})")
        
        all_results = []
        
        for i in range(iterations):
            logger.info(f"테스트 반복 {i+1}/{iterations}")
            
            # OpenAI 테스트
            openai_result = await self.test_openai_api()
            openai_result["iteration"] = i + 1
            all_results.append(openai_result)
            
            # Gemini 테스트
            gemini_result = await self.test_gemini_api()
            gemini_result["iteration"] = i + 1
            all_results.append(gemini_result)
            
            # 번역 테스트
            translation_result = await self.test_translation_api()
            translation_result["iteration"] = i + 1
            all_results.append(translation_result)
            
            # 테스트 간 간격
            if i < iterations - 1:
                await asyncio.sleep(2)
        
        self.test_results["tests"] = all_results
        return self.test_results
    
    def generate_report(self) -> str:
        """테스트 결과 리포트 생성"""
        if not self.test_results["tests"]:
            return "테스트 결과가 없습니다."
        
        report = []
        report.append("=" * 60)
        report.append("API 성능 테스트 리포트")
        report.append("=" * 60)
        report.append(f"테스트 시간: {self.test_results['timestamp']}")
        report.append("")
        
        # API별 통계
        api_stats = {}
        for test in self.test_results["tests"]:
            api = test["api"]
            if api not in api_stats:
                api_stats[api] = {
                    "success_count": 0,
                    "error_count": 0,
                    "response_times": [],
                    "response_lengths": []
                }
            
            if test["status"] == "success":
                api_stats[api]["success_count"] += 1
                api_stats[api]["response_times"].append(test["response_time"])
                api_stats[api]["response_lengths"].append(test["response_length"])
            else:
                api_stats[api]["error_count"] += 1
        
        for api, stats in api_stats.items():
            report.append(f"[{api.upper()} API]")
            report.append(f"  성공: {stats['success_count']}회")
            report.append(f"  실패: {stats['error_count']}회")
            
            if stats["response_times"]:
                avg_time = sum(stats["response_times"]) / len(stats["response_times"])
                min_time = min(stats["response_times"])
                max_time = max(stats["response_times"])
                
                report.append(f"  평균 응답시간: {avg_time:.2f}초")
                report.append(f"  최소 응답시간: {min_time:.2f}초")
                report.append(f"  최대 응답시간: {max_time:.2f}초")
            
            if stats["response_lengths"]:
                avg_length = sum(stats["response_lengths"]) / len(stats["response_lengths"])
                report.append(f"  평균 응답 길이: {avg_length:.0f}자")
            
            report.append("")
        
        # 상세 결과
        report.append("상세 테스트 결과:")
        report.append("-" * 40)
        
        for test in self.test_results["tests"]:
            status_icon = "✅" if test["status"] == "success" else "❌"
            report.append(f"{status_icon} {test['api']} (반복 {test['iteration']}): "
                         f"{test['response_time']}초, {test['response_length']}자")
            if test["error"]:
                report.append(f"    오류: {test['error']}")
        
        return "\n".join(report)
    
    def save_results(self, filename: str = None):
        """테스트 결과를 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_test_results_{timestamp}.json"
        
        filepath = os.path.join("logs", filename)
        os.makedirs("logs", exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"테스트 결과가 {filepath}에 저장되었습니다.")
        return filepath

async def main():
    """메인 함수"""
    print("API 성능 테스트를 시작합니다...")
    print("=" * 50)
    
    # 설정 검증
    errors = settings.validate_settings()
    if errors:
        print("❌ 설정 오류:")
        for error in errors:
            print(f"  - {error}")
        return
    
    print("✅ 환경 설정이 올바르게 구성되었습니다.")
    print(f"  - OpenAI API: {'설정됨' if settings.openai_api_key else '설정되지 않음'}")
    print(f"  - Gemini API: {'설정됨' if settings.gemini_api_key else '설정되지 않음'}")
    print()
    
    # 테스트 실행
    tester = APIPerformanceTest()
    results = await tester.run_all_tests(iterations=2)  # 2회 반복으로 테스트
    
    # 결과 출력
    report = tester.generate_report()
    print(report)
    
    # 결과 저장
    saved_file = tester.save_results()
    print(f"\n📁 상세 결과가 저장되었습니다: {saved_file}")

if __name__ == "__main__":
    asyncio.run(main()) 