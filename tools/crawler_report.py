#!/usr/bin/env python3
"""
크롤링 성공률 리포트 생성 도구
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def generate_crawling_report():
    """크롤링 성공률 리포트를 생성합니다."""
    try:
        from app.services.crawler_monitor import crawling_monitor
        
        print("=" * 60)
        print("📊 크롤링 성공률 리포트")
        print("=" * 60)
        
        report = crawling_monitor.generate_report()
        print(report)
        
        # 추가 통계
        print("\n📈 상세 통계:")
        overall = crawling_monitor.get_overall_stats()
        
        if overall['total_attempts'] > 0:
            print(f"   • 평균 성공률: {overall['success_rate']:.1%}")
            
            # 사이트별 성공률
            problem_sites = crawling_monitor.get_problem_sites()
            if problem_sites:
                print(f"\n🚨 문제 사이트 상세:")
                for site in problem_sites[:5]:
                    print(f"   • {site['domain']}")
                    print(f"     - 성공률: {site['success_rate']:.1%}")
                    print(f"     - 실패 원인: {', '.join(site['common_errors'].keys())}")
            
            # 최근 시도
            recent = crawling_monitor.get_recent_attempts(10)
            if recent:
                print(f"\n🕒 최근 시도 (최근 10개):")
                for attempt in recent:
                    status = "✅" if attempt['success'] else "❌"
                    print(f"   {status} {attempt['domain']} - {attempt['timestamp'][:19]}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 모니터링 모듈을 불러올 수 없습니다: {e}")
        return False
    except Exception as e:
        print(f"❌ 리포트 생성 중 오류: {e}")
        return False

def test_specific_site(url: str):
    """특정 사이트를 테스트합니다."""
    try:
        from app.services.crawler import EnhancedCrawler
        
        print(f"\n🧪 {url} 사이트 테스트")
        print("-" * 40)
        
        crawler = EnhancedCrawler()
        content = crawler.crawl_url(url)
        
        if content:
            print(f"✅ 크롤링 성공!")
            print(f"   • 추출된 텍스트 길이: {len(content)}자")
            print(f"   • 미리보기: {content[:200]}...")
        else:
            print("❌ 크롤링 실패")
            
        return content is not None
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python tools/crawler_report.py report     # 전체 리포트 생성")
        print("  python tools/crawler_report.py test <URL> # 특정 사이트 테스트")
        return
    
    command = sys.argv[1]
    
    if command == "report":
        generate_crawling_report()
    elif command == "test":
        if len(sys.argv) < 3:
            print("❌ 테스트할 URL을 입력하세요")
            return
        url = sys.argv[2]
        test_specific_site(url)
    else:
        print(f"❌ 알 수 없는 명령어: {command}")

if __name__ == "__main__":
    main() 