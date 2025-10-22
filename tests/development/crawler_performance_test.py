#!/usr/bin/env python3
"""
크롤링 성능 테스트 도구
개선된 크롤러의 성능을 측정하고 문제 사이트들의 개선 상황을 확인합니다.
"""

import sys
import os
import time
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import requests

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.crawler import EnhancedCrawler
from app.services.google_style_crawler import GoogleStyleCrawler
from app.services.crawler_monitor import crawling_monitor

class CrawlerPerformanceTester:
    """크롤링 성능 테스터"""
    
    def __init__(self):
        self.enhanced_crawler = EnhancedCrawler()
        self.google_crawler = GoogleStyleCrawler()
        self.test_results = []
        
        # 테스트할 사이트 목록 (문제가 있던 사이트들 포함)
        self.test_sites = [
            "https://www.example.com",
            "https://searchengineland.com",
            "https://www.socialmediatoday.com",
            "https://www.facebook.com",
            "https://www.bbc.com",
            "https://moz.com",
            "https://ahrefs.com",
            "https://backlinko.com",
            "https://neilpatel.com",
            "https://www.searchengineland.com/google-core-update-may-2024-447123",
            "https://www.socialmediatoday.com/news/5-ways-to-improve-your-social-media-strategy-in-2024/",
            "https://www.bbc.com/news/technology-12345678",
            "https://moz.com/blog/seo-guide",
            "https://ahrefs.com/blog/seo-tools",
            "https://backlinko.com/seo-techniques",
            "https://neilpatel.com/blog/digital-marketing-strategies/"
        ]
    
    def test_enhanced_crawler(self, url: str) -> Dict[str, Any]:
        """강화된 크롤러로 테스트"""
        start_time = time.time()
        success = False
        content_length = 0
        error = ""
        
        try:
            content = self.enhanced_crawler.crawl_url(url, max_retries=3, use_google_style=True)
            if content:
                success = True
                content_length = len(content)
            else:
                error = "콘텐츠 추출 실패"
        except Exception as e:
            error = str(e)
        
        response_time = time.time() - start_time
        
        return {
            "crawler_type": "Enhanced",
            "url": url,
            "success": success,
            "content_length": content_length,
            "response_time": response_time,
            "error": error
        }
    
    def test_google_style_crawler(self, url: str) -> Dict[str, Any]:
        """Google 스타일 크롤러로 테스트"""
        start_time = time.time()
        success = False
        content_length = 0
        error = ""
        
        try:
            content = self.google_crawler.crawl_url(url, max_retries=3)
            if content:
                success = True
                content_length = len(content)
            else:
                error = "콘텐츠 추출 실패"
        except Exception as e:
            error = str(e)
        
        response_time = time.time() - start_time
        
        return {
            "crawler_type": "Google Style",
            "url": url,
            "success": success,
            "content_length": content_length,
            "response_time": response_time,
            "error": error
        }
    
    def test_traditional_crawler(self, url: str) -> Dict[str, Any]:
        """기존 크롤러로 테스트"""
        start_time = time.time()
        success = False
        content_length = 0
        error = ""
        
        try:
            content = self.enhanced_crawler.crawl_url(url, max_retries=3, use_google_style=False)
            if content:
                success = True
                content_length = len(content)
            else:
                error = "콘텐츠 추출 실패"
        except Exception as e:
            error = str(e)
        
        response_time = time.time() - start_time
        
        return {
            "crawler_type": "Traditional",
            "url": url,
            "success": success,
            "content_length": content_length,
            "response_time": response_time,
            "error": error
        }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """종합적인 크롤링 성능 테스트 실행"""
        print("🚀 크롤링 성능 테스트 시작...")
        print(f"📋 테스트 사이트 수: {len(self.test_sites)}")
        print("=" * 60)
        
        all_results = []
        
        for i, url in enumerate(self.test_sites, 1):
            print(f"\n🔍 테스트 {i}/{len(self.test_sites)}: {url}")
            
            # 1. 강화된 크롤러 테스트
            print("  📊 강화된 크롤러 테스트 중...")
            enhanced_result = self.test_enhanced_crawler(url)
            all_results.append(enhanced_result)
            
            # 2. Google 스타일 크롤러 테스트
            print("  📊 Google 스타일 크롤러 테스트 중...")
            google_result = self.test_google_style_crawler(url)
            all_results.append(google_result)
            
            # 3. 기존 크롤러 테스트
            print("  📊 기존 크롤러 테스트 중...")
            traditional_result = self.test_traditional_crawler(url)
            all_results.append(traditional_result)
            
            # 결과 출력
            print(f"    ✅ 강화된: {'성공' if enhanced_result['success'] else '실패'} ({enhanced_result['content_length']}자, {enhanced_result['response_time']:.2f}초)")
            print(f"    ✅ Google: {'성공' if google_result['success'] else '실패'} ({google_result['content_length']}자, {google_result['response_time']:.2f}초)")
            print(f"    ✅ 기존: {'성공' if traditional_result['success'] else '실패'} ({traditional_result['content_length']}자, {traditional_result['response_time']:.2f}초)")
            
            # 크롤링 간격
            time.sleep(1)
        
        # 결과 분석
        analysis = self.analyze_results(all_results)
        
        # 결과 저장
        self.save_results(all_results, analysis)
        
        return analysis
    
    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """테스트 결과 분석"""
        analysis = {
            "total_tests": len(results),
            "crawler_comparison": {},
            "site_performance": {},
            "overall_stats": {}
        }
        
        # 크롤러별 통계
        crawler_stats = {}
        for result in results:
            crawler_type = result["crawler_type"]
            if crawler_type not in crawler_stats:
                crawler_stats[crawler_type] = {
                    "total": 0,
                    "success": 0,
                    "total_content_length": 0,
                    "total_response_time": 0,
                    "errors": []
                }
            
            stats = crawler_stats[crawler_type]
            stats["total"] += 1
            
            if result["success"]:
                stats["success"] += 1
                stats["total_content_length"] += result["content_length"]
            
            stats["total_response_time"] += result["response_time"]
            
            if result["error"]:
                stats["errors"].append(result["error"])
        
        # 성공률 및 평균 계산
        for crawler_type, stats in crawler_stats.items():
            success_rate = stats["success"] / stats["total"] if stats["total"] > 0 else 0
            avg_content_length = stats["total_content_length"] / stats["success"] if stats["success"] > 0 else 0
            avg_response_time = stats["total_response_time"] / stats["total"] if stats["total"] > 0 else 0
            
            analysis["crawler_comparison"][crawler_type] = {
                "success_rate": round(success_rate, 4),
                "avg_content_length": round(avg_content_length, 2),
                "avg_response_time": round(avg_response_time, 2),
                "total_tests": stats["total"],
                "successful_tests": stats["success"],
                "common_errors": list(set(stats["errors"]))
            }
        
        # 사이트별 성능 분석
        site_stats = {}
        for i in range(0, len(results), 3):  # 3개 크롤러 결과씩 그룹화
            if i + 2 < len(results):
                url = results[i]["url"]
                enhanced = results[i]
                google = results[i + 1]
                traditional = results[i + 2]
                
                site_stats[url] = {
                    "enhanced": {
                        "success": enhanced["success"],
                        "content_length": enhanced["content_length"],
                        "response_time": enhanced["response_time"]
                    },
                    "google": {
                        "success": google["success"],
                        "content_length": google["content_length"],
                        "response_time": google["response_time"]
                    },
                    "traditional": {
                        "success": traditional["success"],
                        "content_length": traditional["content_length"],
                        "response_time": traditional["response_time"]
                    }
                }
        
        analysis["site_performance"] = site_stats
        
        # 전체 통계
        total_success = sum(1 for r in results if r["success"])
        total_content_length = sum(r["content_length"] for r in results if r["success"])
        total_response_time = sum(r["response_time"] for r in results)
        
        analysis["overall_stats"] = {
            "total_tests": len(results),
            "total_success": total_success,
            "overall_success_rate": round(total_success / len(results), 4),
            "avg_content_length": round(total_content_length / total_success, 2) if total_success > 0 else 0,
            "avg_response_time": round(total_response_time / len(results), 2)
        }
        
        return analysis
    
    def save_results(self, results: List[Dict[str, Any]], analysis: Dict[str, Any]):
        """테스트 결과를 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crawler_performance_test_{timestamp}.json"
        
        output = {
            "test_timestamp": datetime.now().isoformat(),
            "test_sites": self.test_sites,
            "detailed_results": results,
            "analysis": analysis
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 테스트 결과가 {filename}에 저장되었습니다.")
    
    def print_summary(self, analysis: Dict[str, Any]):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("📊 크롤링 성능 테스트 결과 요약")
        print("=" * 60)
        
        # 전체 통계
        overall = analysis["overall_stats"]
        print(f"\n📈 전체 통계:")
        print(f"  • 총 테스트: {overall['total_tests']}회")
        print(f"  • 성공: {overall['total_success']}회")
        print(f"  • 전체 성공률: {overall['overall_success_rate']:.1%}")
        print(f"  • 평균 콘텐츠 길이: {overall['avg_content_length']:.0f}자")
        print(f"  • 평균 응답 시간: {overall['avg_response_time']:.2f}초")
        
        # 크롤러별 비교
        print(f"\n🔍 크롤러별 성능 비교:")
        for crawler_type, stats in analysis["crawler_comparison"].items():
            print(f"  • {crawler_type}:")
            print(f"    - 성공률: {stats['success_rate']:.1%}")
            print(f"    - 평균 콘텐츠 길이: {stats['avg_content_length']:.0f}자")
            print(f"    - 평균 응답 시간: {stats['avg_response_time']:.2f}초")
            if stats['common_errors']:
                print(f"    - 주요 오류: {', '.join(stats['common_errors'][:3])}")
        
        # 개선 효과 분석
        enhanced = analysis["crawler_comparison"].get("Enhanced", {})
        traditional = analysis["crawler_comparison"].get("Traditional", {})
        
        if enhanced and traditional:
            success_improvement = enhanced["success_rate"] - traditional["success_rate"]
            content_improvement = enhanced["avg_content_length"] - traditional["avg_content_length"]
            
            print(f"\n🚀 개선 효과:")
            print(f"  • 성공률 개선: {success_improvement:+.1%}")
            print(f"  • 콘텐츠 길이 개선: {content_improvement:+.0f}자")
        
        # 문제 사이트 분석
        problem_sites = []
        for url, stats in analysis["site_performance"].items():
            if not any([stats["enhanced"]["success"], stats["google"]["success"], stats["traditional"]["success"]]):
                problem_sites.append(url)
        
        if problem_sites:
            print(f"\n⚠️  여전히 문제가 있는 사이트:")
            for site in problem_sites:
                print(f"  • {site}")
        else:
            print(f"\n✅ 모든 테스트 사이트에서 최소 하나의 크롤러가 성공했습니다!")

def main():
    """메인 함수"""
    print("🔧 크롤링 성능 테스트 도구")
    print("개선된 크롤러의 성능을 측정합니다.")
    
    tester = CrawlerPerformanceTester()
    
    try:
        # 종합 테스트 실행
        analysis = tester.run_comprehensive_test()
        
        # 결과 요약 출력
        tester.print_summary(analysis)
        
        # 기존 통계와 비교
        print(f"\n📊 기존 크롤링 통계와 비교:")
        try:
            overall_stats = crawling_monitor.get_overall_stats()
            print(f"  • 기존 성공률: {overall_stats['success_rate']:.1%}")
            print(f"  • 테스트 성공률: {analysis['overall_stats']['overall_success_rate']:.1%}")
            
            improvement = analysis['overall_stats']['overall_success_rate'] - overall_stats['success_rate']
            print(f"  • 개선 효과: {improvement:+.1%}")
        except Exception as e:
            print(f"  • 기존 통계 조회 실패: {e}")
        
    except KeyboardInterrupt:
        print("\n⏹️  테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 