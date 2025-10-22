#!/usr/bin/env python3
"""
Selenium 크롤러 테스트 도구
Selenium 중심 크롤링의 성능을 측정하고 문제점을 진단합니다.
"""

import sys
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Any
import requests

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.selenium_crawler import SeleniumCrawler
from app.services.crawler import EnhancedCrawler

class SeleniumCrawlerTester:
    """Selenium 크롤러 테스터"""
    
    def __init__(self):
        self.selenium_crawler = SeleniumCrawler(headless=True)
        self.enhanced_crawler = EnhancedCrawler()
        self.test_results = []
        
        # Selenium이 효과적일 것으로 예상되는 사이트들
        self.test_sites = [
            "https://www.socialmediatoday.com",
            "https://www.facebook.com",
            "https://www.instagram.com",
            "https://twitter.com",
            "https://www.linkedin.com",
            "https://www.youtube.com",
            "https://www.reddit.com",
            "https://www.quora.com",
            "https://www.medium.com",
            "https://www.tumblr.com",
            "https://www.pinterest.com",
            "https://www.snapchat.com",
            "https://www.tiktok.com",
            "https://www.discord.com",
            "https://www.slack.com",
            "https://www.notion.so",
            "https://www.figma.com",
            "https://www.canva.com",
            "https://www.behance.net",
            "https://www.dribbble.com"
        ]
    
    def test_selenium_only(self, url: str) -> Dict[str, Any]:
        """Selenium만 사용하여 테스트"""
        start_time = time.time()
        success = False
        content_length = 0
        error = ""
        
        try:
            # Selenium으로 HTML 가져오기
            html = self.selenium_crawler.get_rendered_html(url, timeout=20)
            if html:
                # Selenium으로 콘텐츠 추출
                content = self.selenium_crawler.extract_main_content(html)
                if content:
                    success = True
                    content_length = len(content)
                else:
                    error = "Selenium 콘텐츠 추출 실패"
            else:
                error = "Selenium HTML 가져오기 실패"
        except Exception as e:
            error = str(e)
        
        response_time = time.time() - start_time
        
        return {
            "test_type": "Selenium Only",
            "url": url,
            "success": success,
            "content_length": content_length,
            "response_time": response_time,
            "error": error
        }
    
    def test_enhanced_with_selenium(self, url: str) -> Dict[str, Any]:
        """강화된 크롤러 (Selenium 우선)로 테스트"""
        start_time = time.time()
        success = False
        content_length = 0
        error = ""
        
        try:
            # 강화된 크롤러 사용 (Selenium 우선)
            content = self.enhanced_crawler.crawl_url(url, max_retries=2, use_google_style=False)
            if content:
                success = True
                content_length = len(content)
            else:
                error = "강화된 크롤러 실패"
        except Exception as e:
            error = str(e)
        
        response_time = time.time() - start_time
        
        return {
            "test_type": "Enhanced with Selenium",
            "url": url,
            "success": success,
            "content_length": content_length,
            "response_time": response_time,
            "error": error
        }
    
    def test_traditional_only(self, url: str) -> Dict[str, Any]:
        """기존 방식만 사용하여 테스트"""
        start_time = time.time()
        success = False
        content_length = 0
        error = ""
        
        try:
            # 기존 방식 (Selenium 없이)
            content = self.enhanced_crawler.crawl_url(url, max_retries=2, use_google_style=False)
            if content:
                success = True
                content_length = len(content)
            else:
                error = "기존 방식 실패"
        except Exception as e:
            error = str(e)
        
        response_time = time.time() - start_time
        
        return {
            "test_type": "Traditional Only",
            "url": url,
            "success": success,
            "content_length": content_length,
            "response_time": response_time,
            "error": error
        }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """종합적인 Selenium 크롤링 테스트 실행"""
        print("🚀 Selenium 크롤링 테스트 시작...")
        print(f"📋 테스트 사이트 수: {len(self.test_sites)}")
        print("=" * 60)
        
        all_results = []
        
        for i, url in enumerate(self.test_sites, 1):
            print(f"\n🔍 테스트 {i}/{len(self.test_sites)}: {url}")
            
            # 1. Selenium만 사용
            print("  📊 Selenium만 사용 테스트 중...")
            selenium_result = self.test_selenium_only(url)
            all_results.append(selenium_result)
            
            # 2. 강화된 크롤러 (Selenium 우선)
            print("  📊 강화된 크롤러 테스트 중...")
            enhanced_result = self.test_enhanced_with_selenium(url)
            all_results.append(enhanced_result)
            
            # 3. 기존 방식만
            print("  📊 기존 방식 테스트 중...")
            traditional_result = self.test_traditional_only(url)
            all_results.append(traditional_result)
            
            # 결과 출력
            print(f"    ✅ Selenium: {'성공' if selenium_result['success'] else '실패'} ({selenium_result['content_length']}자, {selenium_result['response_time']:.2f}초)")
            print(f"    ✅ Enhanced: {'성공' if enhanced_result['success'] else '실패'} ({enhanced_result['content_length']}자, {enhanced_result['response_time']:.2f}초)")
            print(f"    ✅ Traditional: {'성공' if traditional_result['success'] else '실패'} ({traditional_result['content_length']}자, {traditional_result['response_time']:.2f}초)")
            
            # 크롤링 간격
            time.sleep(2)
        
        # 결과 분석
        analysis = self.analyze_results(all_results)
        
        # 결과 저장
        self.save_results(all_results, analysis)
        
        return analysis
    
    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """테스트 결과 분석"""
        analysis = {
            "total_tests": len(results),
            "method_comparison": {},
            "site_performance": {},
            "overall_stats": {}
        }
        
        # 방법별 통계
        method_stats = {}
        for result in results:
            test_type = result["test_type"]
            if test_type not in method_stats:
                method_stats[test_type] = {
                    "total": 0,
                    "success": 0,
                    "total_content_length": 0,
                    "total_response_time": 0,
                    "errors": []
                }
            
            stats = method_stats[test_type]
            stats["total"] += 1
            
            if result["success"]:
                stats["success"] += 1
                stats["total_content_length"] += result["content_length"]
            
            stats["total_response_time"] += result["response_time"]
            
            if result["error"]:
                stats["errors"].append(result["error"])
        
        # 성공률 및 평균 계산
        for test_type, stats in method_stats.items():
            success_rate = stats["success"] / stats["total"] if stats["total"] > 0 else 0
            avg_content_length = stats["total_content_length"] / stats["success"] if stats["success"] > 0 else 0
            avg_response_time = stats["total_response_time"] / stats["total"] if stats["total"] > 0 else 0
            
            analysis["method_comparison"][test_type] = {
                "success_rate": round(success_rate, 4),
                "avg_content_length": round(avg_content_length, 2),
                "avg_response_time": round(avg_response_time, 2),
                "total_tests": stats["total"],
                "successful_tests": stats["success"],
                "common_errors": list(set(stats["errors"]))
            }
        
        # 사이트별 성능 분석
        site_stats = {}
        for i in range(0, len(results), 3):  # 3개 방법 결과씩 그룹화
            if i + 2 < len(results):
                url = results[i]["url"]
                selenium = results[i]
                enhanced = results[i + 1]
                traditional = results[i + 2]
                
                site_stats[url] = {
                    "selenium": {
                        "success": selenium["success"],
                        "content_length": selenium["content_length"],
                        "response_time": selenium["response_time"]
                    },
                    "enhanced": {
                        "success": enhanced["success"],
                        "content_length": enhanced["content_length"],
                        "response_time": enhanced["response_time"]
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
        filename = f"selenium_crawler_test_{timestamp}.json"
        
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
        print("📊 Selenium 크롤링 테스트 결과 요약")
        print("=" * 60)
        
        # 전체 통계
        overall = analysis["overall_stats"]
        print(f"\n📈 전체 통계:")
        print(f"  • 총 테스트: {overall['total_tests']}회")
        print(f"  • 성공: {overall['total_success']}회")
        print(f"  • 전체 성공률: {overall['overall_success_rate']:.1%}")
        print(f"  • 평균 콘텐츠 길이: {overall['avg_content_length']:.0f}자")
        print(f"  • 평균 응답 시간: {overall['avg_response_time']:.2f}초")
        
        # 방법별 비교
        print(f"\n🔍 방법별 성능 비교:")
        for test_type, stats in analysis["method_comparison"].items():
            print(f"  • {test_type}:")
            print(f"    - 성공률: {stats['success_rate']:.1%}")
            print(f"    - 평균 콘텐츠 길이: {stats['avg_content_length']:.0f}자")
            print(f"    - 평균 응답 시간: {stats['avg_response_time']:.2f}초")
            if stats['common_errors']:
                print(f"    - 주요 오류: {', '.join(stats['common_errors'][:3])}")
        
        # Selenium 효과 분석
        selenium = analysis["method_comparison"].get("Selenium Only", {})
        traditional = analysis["method_comparison"].get("Traditional Only", {})
        
        if selenium and traditional:
            success_improvement = selenium["success_rate"] - traditional["success_rate"]
            content_improvement = selenium["avg_content_length"] - traditional["avg_content_length"]
            
            print(f"\n🚀 Selenium 효과:")
            print(f"  • 성공률 개선: {success_improvement:+.1%}")
            print(f"  • 콘텐츠 길이 개선: {content_improvement:+.0f}자")
        
        # 성공한 사이트 분석
        successful_sites = []
        for url, stats in analysis["site_performance"].items():
            if any([stats["selenium"]["success"], stats["enhanced"]["success"], stats["traditional"]["success"]]):
                successful_sites.append(url)
        
        if successful_sites:
            print(f"\n✅ 성공한 사이트 ({len(successful_sites)}개):")
            for site in successful_sites[:10]:  # 상위 10개만 표시
                print(f"  • {site}")
            if len(successful_sites) > 10:
                print(f"  • ... 및 {len(successful_sites) - 10}개 더")
        else:
            print(f"\n⚠️  성공한 사이트가 없습니다.")
        
        # 실패한 사이트 분석
        failed_sites = []
        for url, stats in analysis["site_performance"].items():
            if not any([stats["selenium"]["success"], stats["enhanced"]["success"], stats["traditional"]["success"]]):
                failed_sites.append(url)
        
        if failed_sites:
            print(f"\n❌ 실패한 사이트 ({len(failed_sites)}개):")
            for site in failed_sites[:10]:  # 상위 10개만 표시
                print(f"  • {site}")
            if len(failed_sites) > 10:
                print(f"  • ... 및 {len(failed_sites) - 10}개 더")

def main():
    """메인 함수"""
    print("🔧 Selenium 크롤러 테스트 도구")
    print("Selenium 중심 크롤링의 성능을 측정합니다.")
    
    tester = SeleniumCrawlerTester()
    
    try:
        # 종합 테스트 실행
        analysis = tester.run_comprehensive_test()
        
        # 결과 요약 출력
        tester.print_summary(analysis)
        
    except KeyboardInterrupt:
        print("\n⏹️  테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Selenium 크롤러 정리
        tester.selenium_crawler.close()

if __name__ == "__main__":
    main() 