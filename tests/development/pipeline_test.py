#!/usr/bin/env python3
"""
파이프라인 테스트 도구
크롤링 → 번역 → 콘텐츠 생성까지의 전체 프로세스를 테스트합니다.
"""

import sys
import os
import time
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.content_pipeline import content_pipeline, ContentPipelineConfig
from app.services.crawler import EnhancedCrawler
from app.services.smart_crawler import SmartCrawler
from app.services.translator import translate_text, detect_language
from app.services.content_generator import create_blog_post

class PipelineTester:
    """파이프라인 테스터"""
    
    def __init__(self):
        self.enhanced_crawler = EnhancedCrawler()
        self.smart_crawler = SmartCrawler()
        self.test_results = []
        
        # 테스트 사이트들
        self.test_sites = [
            "https://www.socialmediatoday.com",
            "https://techcrunch.com",
            "https://www.theverge.com",
            "https://www.wired.com",
            "https://www.engadget.com"
        ]
        
        # 테스트 텍스트들
        self.test_texts = [
            "Artificial Intelligence is transforming the way we live and work. From autonomous vehicles to smart home devices, AI is becoming an integral part of our daily lives.",
            "The future of renewable energy looks promising as solar and wind power technologies continue to advance. These clean energy sources are becoming more efficient and cost-effective.",
            "Digital transformation is reshaping industries across the globe. Companies are adopting new technologies to improve efficiency and stay competitive in the digital age."
        ]
    
    async def test_individual_components(self):
        """개별 컴포넌트 테스트"""
        print("🔧 개별 컴포넌트 테스트 시작...")
        print("=" * 60)
        
        # 1. 크롤러 테스트
        print("\n1️⃣ 크롤러 테스트")
        for url in self.test_sites[:2]:  # 상위 2개만 테스트
            print(f"  📊 {url}")
            
            # Enhanced Crawler
            start_time = time.time()
            try:
                content = self.enhanced_crawler.crawl_url(url, max_retries=2, use_google_style=True)
                response_time = time.time() - start_time
                success = content is not None and len(content) > 100
                print(f"    ✅ Enhanced: {'성공' if success else '실패'} ({len(content) if content else 0}자, {response_time:.2f}초)")
            except Exception as e:
                print(f"    ❌ Enhanced: 실패 - {e}")
            
            # Smart Crawler
            start_time = time.time()
            try:
                content = self.smart_crawler.crawl_url(url)
                response_time = time.time() - start_time
                success = content is not None and len(content) > 100
                print(f"    ✅ Smart: {'성공' if success else '실패'} ({len(content) if content else 0}자, {response_time:.2f}초)")
            except Exception as e:
                print(f"    ❌ Smart: 실패 - {e}")
            
            time.sleep(2)
        
        # 2. 번역 테스트
        print("\n2️⃣ 번역 테스트")
        for i, text in enumerate(self.test_texts):
            print(f"  📊 텍스트 {i+1} ({len(text)}자)")
            
            # 언어 감지
            start_time = time.time()
            try:
                detected_lang = await detect_language(text)
                response_time = time.time() - start_time
                print(f"    ✅ 언어 감지: {detected_lang} ({response_time:.2f}초)")
            except Exception as e:
                print(f"    ❌ 언어 감지: 실패 - {e}")
            
            # 번역
            start_time = time.time()
            try:
                translated = await translate_text(text, "ko")
                response_time = time.time() - start_time
                success = translated is not None and len(translated) > 50
                print(f"    ✅ 번역: {'성공' if success else '실패'} ({len(translated) if translated else 0}자, {response_time:.2f}초)")
            except Exception as e:
                print(f"    ❌ 번역: 실패 - {e}")
            
            time.sleep(1)
        
        # 3. 콘텐츠 생성 테스트
        print("\n3️⃣ 콘텐츠 생성 테스트")
        for i, text in enumerate(self.test_texts[:2]):  # 상위 2개만 테스트
            print(f"  📊 텍스트 {i+1}")
            
            start_time = time.time()
            try:
                blog_post = await create_blog_post(
                    text=text,
                    keywords="AI, technology, innovation",
                    content_length="2000",
                    ai_mode="creative"
                )
                response_time = time.time() - start_time
                success = blog_post is not None and "content" in blog_post
                print(f"    ✅ 콘텐츠 생성: {'성공' if success else '실패'} ({response_time:.2f}초)")
                if success:
                    print(f"      📝 제목: {blog_post.get('title', 'N/A')}")
                    print(f"      📝 길이: {len(blog_post.get('content', ''))}자")
            except Exception as e:
                print(f"    ❌ 콘텐츠 생성: 실패 - {e}")
            
            time.sleep(2)
    
    async def test_full_pipeline(self):
        """전체 파이프라인 테스트"""
        print("\n🚀 전체 파이프라인 테스트 시작...")
        print("=" * 60)
        
        for i, url in enumerate(self.test_sites[:3], 1):  # 상위 3개만 테스트
            print(f"\n🔍 파이프라인 테스트 {i}/{3}: {url}")
            
            # 파이프라인 설정
            config = ContentPipelineConfig(
                use_smart_crawler=True,
                target_language="ko",
                content_length="2000",
                ai_mode="creative",
                enable_seo_analysis=True,
                enable_caching=True
            )
            
            # 파이프라인 실행
            start_time = time.time()
            try:
                result = await content_pipeline.execute_pipeline(url=url, config=config)
                response_time = time.time() - start_time
                
                if result["success"]:
                    print(f"    ✅ 파이프라인 성공 ({response_time:.2f}초)")
                    
                    # 결과 분석
                    results = result["results"]
                    print(f"      📊 크롤링: {len(results.get('crawling', {}).get('content', ''))}자")
                    print(f"      📊 언어 감지: {results.get('language_detection', {}).get('detected_language', 'N/A')}")
                    print(f"      📊 번역: {len(results.get('translation', {}).get('translated_content', ''))}자")
                    
                    blog_post = results.get('content_generation', {}).get('blog_post', {})
                    print(f"      📊 콘텐츠 생성: {blog_post.get('title', 'N/A')}")
                    print(f"      📊 최종 길이: {len(blog_post.get('content', ''))}자")
                    
                    if 'seo_analysis' in results:
                        seo_score = results['seo_analysis'].get('seo_score', 0)
                        print(f"      📊 SEO 점수: {seo_score:.2f}")
                    
                else:
                    print(f"    ❌ 파이프라인 실패: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                print(f"    ❌ 파이프라인 오류: {e}")
            
            time.sleep(3)
    
    async def test_pipeline_with_progress(self):
        """진행 상황 스트리밍 파이프라인 테스트"""
        print("\n📡 진행 상황 스트리밍 파이프라인 테스트...")
        print("=" * 60)
        
        # 테스트 텍스트 사용
        test_text = self.test_texts[0]
        
        config = ContentPipelineConfig(
            use_smart_crawler=False,  # 텍스트 입력이므로 크롤러 불필요
            target_language="ko",
            content_length="1500",
            ai_mode="informative",
            enable_seo_analysis=True,
            enable_caching=False
        )
        
        print(f"📝 테스트 텍스트: {test_text[:100]}...")
        print("\n🔄 파이프라인 진행 상황:")
        
        step_count = 0
        async for progress in content_pipeline.execute_pipeline_with_progress(
            text=test_text, config=config
        ):
            step_count += 1
            step = progress.get("step", 0)
            message = progress.get("message", "")
            progress_percent = progress.get("progress", 0)
            
            print(f"  📊 단계 {step}: {message} ({progress_percent}%)")
            
            if "error" in progress:
                print(f"    ❌ 오류: {progress['error']}")
                break
            
            if "result" in progress:
                result = progress["result"]
                blog_post = result.get("blog_post", {})
                print(f"    ✅ 완료!")
                print(f"      📝 제목: {blog_post.get('title', 'N/A')}")
                print(f"      📝 길이: {len(blog_post.get('content', ''))}자")
                print(f"      📝 키워드: {result.get('keywords', 'N/A')}")
                break
            
            time.sleep(0.5)
    
    async def test_error_handling(self):
        """에러 처리 테스트"""
        print("\n⚠️ 에러 처리 테스트...")
        print("=" * 60)
        
        # 1. 잘못된 URL 테스트
        print("\n1️⃣ 잘못된 URL 테스트")
        config = ContentPipelineConfig(
            use_smart_crawler=True,
            target_language="ko",
            content_length="1000"
        )
        
        try:
            result = await content_pipeline.execute_pipeline(
                url="https://invalid-url-that-does-not-exist.com",
                config=config
            )
            print(f"    📊 결과: {'성공' if result['success'] else '실패'}")
            if not result['success']:
                print(f"    📝 오류: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"    ❌ 예외: {e}")
        
        # 2. 빈 텍스트 테스트
        print("\n2️⃣ 빈 텍스트 테스트")
        try:
            result = await content_pipeline.execute_pipeline(
                text="",
                config=config
            )
            print(f"    📊 결과: {'성공' if result['success'] else '실패'}")
            if not result['success']:
                print(f"    📝 오류: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"    ❌ 예외: {e}")
        
        # 3. 너무 짧은 텍스트 테스트
        print("\n3️⃣ 너무 짧은 텍스트 테스트")
        try:
            result = await content_pipeline.execute_pipeline(
                text="Hello",
                config=config
            )
            print(f"    📊 결과: {'성공' if result['success'] else '실패'}")
            if not result['success']:
                print(f"    📝 오류: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"    ❌ 예외: {e}")
    
    async def test_performance(self):
        """성능 테스트"""
        print("\n⚡ 성능 테스트...")
        print("=" * 60)
        
        # 여러 텍스트로 동시 처리 테스트
        print("\n📊 동시 처리 테스트")
        
        config = ContentPipelineConfig(
            use_smart_crawler=False,
            target_language="ko",
            content_length="1000",
            enable_caching=True
        )
        
        start_time = time.time()
        
        # 동시에 여러 파이프라인 실행
        tasks = []
        for i, text in enumerate(self.test_texts):
            task = content_pipeline.execute_pipeline(
                text=text,
                config=config
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        print(f"    📊 총 실행 시간: {total_time:.2f}초")
        print(f"    📊 평균 시간: {total_time/len(tasks):.2f}초")
        
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
        print(f"    📊 성공률: {success_count}/{len(tasks)} ({success_count/len(tasks)*100:.1f}%)")
    
    def save_test_results(self, results: List[Dict[str, Any]]):
        """테스트 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pipeline_test_results_{timestamp}.json"
        
        output = {
            "test_timestamp": datetime.now().isoformat(),
            "test_results": results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 테스트 결과가 {filename}에 저장되었습니다.")
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("🔧 파이프라인 테스트 도구")
        print("크롤링 → 번역 → 콘텐츠 생성 파이프라인을 테스트합니다.")
        print("=" * 60)
        
        try:
            # 1. 개별 컴포넌트 테스트
            await self.test_individual_components()
            
            # 2. 전체 파이프라인 테스트
            await self.test_full_pipeline()
            
            # 3. 진행 상황 스트리밍 테스트
            await self.test_pipeline_with_progress()
            
            # 4. 에러 처리 테스트
            await self.test_error_handling()
            
            # 5. 성능 테스트
            await self.test_performance()
            
            print("\n✅ 모든 테스트가 완료되었습니다!")
            
        except KeyboardInterrupt:
            print("\n⏹️ 테스트가 중단되었습니다.")
        except Exception as e:
            print(f"\n❌ 테스트 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 리소스 정리
            self.enhanced_crawler = None
            self.smart_crawler.close()
            content_pipeline.cleanup()

def main():
    """메인 함수"""
    tester = PipelineTester()
    asyncio.run(tester.run_all_tests())

if __name__ == "__main__":
    main() 