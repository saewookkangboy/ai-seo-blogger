#!/usr/bin/env python3
"""
스마트 크롤러 테스트 도구
고도화된 크롤러의 성능을 측정하고 최적화 전략을 분석합니다.
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

from app.services.smart_crawler import SmartCrawler, CrawlingStrategy
from app.services.advanced_selenium_crawler import AdvancedSeleniumCrawler
from app.services.crawler import EnhancedCrawler

class SmartCrawlerTester:
    """스마트 크롤러 테스터"""
    
    def __init__(self):
        self.smart_crawler = SmartCrawler()
        self.advanced_selenium_crawler = AdvancedSeleniumCrawler()
        self.enhanced_crawler = EnhancedCrawler()
        self.test_results = []
        
        # 테스트 사이트들 (다양한 유형)
        self.test_sites = [
            # 소셜 미디어
            "https://www.socialmediatoday.com",
            "https://www.facebook.com",
            "https://twitter.com",
            "https://www.linkedin.com",
            "https://www.youtube.com",
            "https://www.reddit.com",
            "https://www.medium.com",
            "https://www.quora.com",
            "https://www.tumblr.com",
            "https://www.pinterest.com",
            
            # 뉴스/블로그
            "https://techcrunch.com",
            "https://www.theverge.com",
            "https://www.wired.com",
            "https://www.engadget.com",
            "https://www.gizmodo.com",
            
            # 기술 사이트
            "https://www.stackoverflow.com",
            "https://github.com",
            "https://www.producthunt.com",
            "https://www.hackernews.com",
            
            # 일반 사이트
            "https://www.wikipedia.org",
            "https://www.amazon.com",
            "https://www.ebay.com",
            "https://www.craigslist.org"
        ]
    
    def test_smart_crawler(self, url: str) -> Dict[str, Any]:
        """스마트 크롤러 테스트"""
        start_time = time.time()
        success = False
        content_length = 0
        error = ""
        strategy_used = ""
        
        try:
            content = self.smart_crawler.crawl_url(url)
            if content:
                success = True
                content_length = len(content)
                # 사용된 전략은 로그에서 확인 (실제로는 SmartCrawler에서 반환해야 함)
                strategy_used = "smart_auto"
            else:
                error = "스마트 크롤러 실패"
        except Exception as e:
            error = str(e)
        
        response_time = time.time() - start_time
        
        return {
            "test_type": "Smart Crawler",
            "url": url,
            "success": success,
            "content_length": content_length,
            "response_time": response_time,
            "error": error,
            "strategy_used": strategy_used
        }
    
    def test_advanced_selenium(self, url: str) -> Dict[str, Any]:
        """고급 Selenium 크롤러 테스트"""
        start_time = time.time()
        success = False
        content_length = 0
        error = ""
        
        try:
            html = self.advanced_selenium_crawler.get_rendered_html(url, timeout=25)
            if html:
                content = self.advanced_selenium_crawler.extract_main_content(html, url)
                if content:
                    success = True
                    content_length = len(content)
                else:
                    error = "고급 Selenium 콘텐츠 추출 실패"
            else:
                error = "고급 Selenium HTML 가져오기 실패"
        except Exception as e:
            error = str(e)
        
        response_time = time.time() - start_time
        
        return {
            "test_type": "Advanced Selenium",
            "url": url,
            "success": success,
            "content_length": content_length,
            "response_time": response_time,
            "error": error
        }
    
    def test_enhanced_crawler(self, url: str) -> Dict[str, Any]:
        """강화된 크롤러 테스트"""
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
                error = "강화된 크롤러 실패"
        except Exception as e:
            error = str(e)
        
        response_time = time.time() - start_time
        
        return {
            "test_type": "Enhanced Crawler",
            "url": url,
            "success": success,
            "content_length": content_length,
            "response_time": response_time,
            "error": error
        }
    
    def test_strategy_comparison(self, url: str) -> List[Dict[str, Any]]:
        """전략별 비교 테스트"""
        results = []
        
        # 각 전략별 테스트
        strategies = [
            CrawlingStrategy.TRADITIONAL,
            CrawlingStrategy.GOOGLE_STYLE,
            CrawlingStrategy.ADVANCED_SELENIUM
        ]
        
        for strategy in strategies:
            start_time = time.time()
            success = False
            content_length = 0
            error = ""
            
            try:
                content = self.smart_crawler.crawl_url(url, force_strategy=strategy)
                if content:
                    success = True
                    content_length = len(content)
                else:
                    error = f"{strategy.value} 전략 실패"
            except Exception as e:
                error = str(e)
            
            response_time = time.time() - start_time
            
            results.append({
                "test_type": f"Strategy: {strategy.value}",
                "url": url,
                "success": success,
                "content_length": content_length,
                "response_time": response_time,
                "error": error,
                "strategy": strategy.value
            })
        
        return results
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """종합적인 스마트 크롤링 테스트 실행"""
        print("🚀 스마트 크롤러 테스트 시작...")
        print(f"📋 테스트 사이트 수: {len(self.test_sites)}")
        print("=" * 60)
        
        all_results = []
        
        for i, url in enumerate(self.test_sites, 1):
            print(f"\n🔍 테스트 {i}/{len(self.test_sites)}: {url}")
            
            # 1. 스마트 크롤러 테스트
            print("  📊 스마트 크롤러 테스트 중...")
            smart_result = self.test_smart_crawler(url)
            all_results.append(smart_result)
            
            # 2. 고급 Selenium 테스트
            print("  📊 고급 Selenium 테스트 중...")
            advanced_result = self.test_advanced_selenium(url)
            all_results.append(advanced_result)
            
            # 3. 강화된 크롤러 테스트
            print("  📊 강화된 크롤러 테스트 중...")
            enhanced_result = self.test_enhanced_crawler(url)
            all_results.append(enhanced_result)
            
            # 결과 출력
            print(f"    ✅ Smart: {'성공' if smart_result['success'] else '실패'} ({smart_result['content_length']}자, {smart_result['response_time']:.2f}초)")
            print(f"    ✅ Advanced: {'성공' if advanced_result['success'] else '실패'} ({advanced_result['content_length']}자, {advanced_result['response_time']:.2f}초)")
            print(f"    ✅ Enhanced: {'성공' if enhanced_result['success'] else '실패'} ({enhanced_result['content_length']}자, {enhanced_result['response_time']:.2f}초)")
            
            # 크롤링 간격
            time.sleep(3)
        
        # 결과 분석
        analysis = self.analyze_results(all_results)
        
        # 결과 저장
        self.save_results(all_results, analysis)
        
        return analysis
    
    def run_strategy_comparison_test(self) -> Dict[str, Any]:
        """전략별 비교 테스트 실행"""
        print("🔍 전략별 비교 테스트 시작...")
        print("=" * 60)
        
        # 상위 10개 사이트만 테스트 (시간 절약)
        test_sites = self.test_sites[:10]
        all_results = []
        
        for i, url in enumerate(test_sites, 1):
            print(f"\n🔍 전략 비교 {i}/{len(test_sites)}: {url}")
            
            strategy_results = self.test_strategy_comparison(url)
            all_results.extend(strategy_results)
            
            # 결과 출력
            for result in strategy_results:
                status = "성공" if result['success'] else "실패"
                print(f"    ✅ {result['strategy']}: {status} ({result['content_length']}자, {result['response_time']:.2f}초)")
            
            time.sleep(2)
        
        # 결과 분석
        analysis = self.analyze_strategy_results(all_results)
        
        # 결과 저장
        self.save_strategy_results(all_results, analysis)
        
        return analysis
    
    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """테스트 결과 분석"""
        analysis = {
            "total_tests": len(results),
            "method_comparison": {},
            "site_performance": {},
            "overall_stats": {},
            "smart_crawler_analysis": {}
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
        
        # 스마트 크롤러 특별 분석
        smart_results = [r for r in results if r["test_type"] == "Smart Crawler"]
        if smart_results:
            smart_success = sum(1 for r in smart_results if r["success"])
            smart_total = len(smart_results)
            analysis["smart_crawler_analysis"] = {
                "total_tests": smart_total,
                "success_rate": round(smart_success / smart_total, 4),
                "avg_response_time": round(sum(r["response_time"] for r in smart_results) / smart_total, 2),
                "avg_content_length": round(sum(r["content_length"] for r in smart_results if r["success"]) / smart_success, 2) if smart_success > 0 else 0
            }
        
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
    
    def analyze_strategy_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """전략별 결과 분석"""
        analysis = {
            "strategy_performance": {},
            "best_strategies_by_domain": {},
            "overall_strategy_ranking": []
        }
        
        # 전략별 성능 분석
        strategy_stats = {}
        for result in results:
            strategy = result.get("strategy", "unknown")
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    "total": 0,
                    "success": 0,
                    "total_content_length": 0,
                    "total_response_time": 0
                }
            
            stats = strategy_stats[strategy]
            stats["total"] += 1
            
            if result["success"]:
                stats["success"] += 1
                stats["total_content_length"] += result["content_length"]
            
            stats["total_response_time"] += result["response_time"]
        
        # 전략별 통계 계산
        for strategy, stats in strategy_stats.items():
            success_rate = stats["success"] / stats["total"] if stats["total"] > 0 else 0
            avg_content_length = stats["total_content_length"] / stats["success"] if stats["success"] > 0 else 0
            avg_response_time = stats["total_response_time"] / stats["total"] if stats["total"] > 0 else 0
            
            # 종합 점수 계산 (성공률 70%, 응답시간 30%)
            score = (success_rate * 0.7) + (1 / (1 + avg_response_time / 10) * 0.3)
            
            analysis["strategy_performance"][strategy] = {
                "success_rate": round(success_rate, 4),
                "avg_content_length": round(avg_content_length, 2),
                "avg_response_time": round(avg_response_time, 2),
                "total_tests": stats["total"],
                "successful_tests": stats["success"],
                "score": round(score, 4)
            }
        
        # 전략 순위
        strategy_ranking = sorted(
            analysis["strategy_performance"].items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )
        analysis["overall_strategy_ranking"] = [
            {"strategy": strategy, "score": data["score"]} 
            for strategy, data in strategy_ranking
        ]
        
        return analysis
    
    def save_results(self, results: List[Dict[str, Any]], analysis: Dict[str, Any]):
        """테스트 결과를 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"smart_crawler_test_{timestamp}.json"
        
        output = {
            "test_timestamp": datetime.now().isoformat(),
            "test_sites": self.test_sites,
            "detailed_results": results,
            "analysis": analysis
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 테스트 결과가 {filename}에 저장되었습니다.")
    
    def save_strategy_results(self, results: List[Dict[str, Any]], analysis: Dict[str, Any]):
        """전략별 결과를 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"strategy_comparison_test_{timestamp}.json"
        
        output = {
            "test_timestamp": datetime.now().isoformat(),
            "test_sites": self.test_sites[:10],
            "detailed_results": results,
            "analysis": analysis
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 전략별 결과가 {filename}에 저장되었습니다.")
    
    def print_summary(self, analysis: Dict[str, Any]):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("📊 스마트 크롤러 테스트 결과 요약")
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
        
        # 스마트 크롤러 특별 분석
        if "smart_crawler_analysis" in analysis:
            smart = analysis["smart_crawler_analysis"]
            print(f"\n🧠 스마트 크롤러 분석:")
            print(f"  • 성공률: {smart['success_rate']:.1%}")
            print(f"  • 평균 응답 시간: {smart['avg_response_time']:.2f}초")
            print(f"  • 평균 콘텐츠 길이: {smart['avg_content_length']:.0f}자")
        
        # 성능 개선 분석
        smart = analysis["method_comparison"].get("Smart Crawler", {})
        traditional = analysis["method_comparison"].get("Enhanced Crawler", {})
        
        if smart and traditional:
            success_improvement = smart["success_rate"] - traditional["success_rate"]
            print(f"\n🚀 스마트 크롤러 효과:")
            print(f"  • 성공률 개선: {success_improvement:+.1%}")
    
    def print_strategy_summary(self, analysis: Dict[str, Any]):
        """전략별 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("📊 전략별 비교 결과 요약")
        print("=" * 60)
        
        # 전략 순위
        print(f"\n🏆 전략 순위:")
        for i, ranking in enumerate(analysis["overall_strategy_ranking"], 1):
            print(f"  {i}. {ranking['strategy']}: {ranking['score']:.3f}")
        
        # 전략별 상세 성능
        print(f"\n📈 전략별 상세 성능:")
        for strategy, stats in analysis["strategy_performance"].items():
            print(f"  • {strategy}:")
            print(f"    - 성공률: {stats['success_rate']:.1%}")
            print(f"    - 평균 응답 시간: {stats['avg_response_time']:.2f}초")
            print(f"    - 평균 콘텐츠 길이: {stats['avg_content_length']:.0f}자")
            print(f"    - 종합 점수: {stats['score']:.3f}")

def main():
    """메인 함수"""
    print("🔧 스마트 크롤러 테스트 도구")
    print("고도화된 크롤러의 성능을 측정합니다.")
    
    tester = SmartCrawlerTester()
    
    try:
        # 1. 종합 테스트 실행
        print("\n1️⃣ 종합 테스트 실행 중...")
        analysis = tester.run_comprehensive_test()
        tester.print_summary(analysis)
        
        # 2. 전략별 비교 테스트
        print("\n2️⃣ 전략별 비교 테스트 실행 중...")
        strategy_analysis = tester.run_strategy_comparison_test()
        tester.print_strategy_summary(strategy_analysis)
        
        # 3. 크롤링 통계 출력
        print("\n3️⃣ 크롤링 통계:")
        stats = tester.smart_crawler.get_crawling_stats()
        print(f"  • 총 도메인 수: {stats['total_domains']}")
        print(f"  • 전체 성공률: {stats['overall_stats']['success_rate']:.1%}")
        
    except KeyboardInterrupt:
        print("\n⏹️  테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 크롤러 정리
        tester.smart_crawler.close()
        tester.advanced_selenium_crawler.close()

if __name__ == "__main__":
    main() 