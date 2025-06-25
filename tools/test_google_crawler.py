#!/usr/bin/env python3
"""
Google 스타일 크롤러 테스트 도구
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_google_style_crawler(url: str):
    """Google 스타일 크롤러 테스트"""
    try:
        from app.services.google_style_crawler import GoogleStyleCrawler
        
        print(f"🧪 Google 스타일 크롤러 테스트: {url}")
        print("=" * 60)
        
        crawler = GoogleStyleCrawler()
        content = crawler.crawl_url(url)
        
        if content:
            print(f"✅ Google 스타일 크롤링 성공!")
            print(f"   • 추출된 텍스트 길이: {len(content)}자")
            print(f"   • 미리보기:")
            print(f"     {content[:300]}...")
            
            # 텍스트 품질 분석
            analyze_text_quality(content)
            
        else:
            print("❌ Google 스타일 크롤링 실패")
            
        return content is not None
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        return False

def compare_crawlers(url: str):
    """기존 크롤러와 Google 스타일 크롤러 비교"""
    try:
        from app.services.crawler import EnhancedCrawler
        from app.services.google_style_crawler import GoogleStyleCrawler
        
        print(f"🔄 크롤러 비교 테스트: {url}")
        print("=" * 60)
        
        # 기존 크롤러
        print("📋 기존 크롤러 테스트...")
        traditional_crawler = EnhancedCrawler()
        traditional_content = traditional_crawler.crawl_url(url, use_google_style=False)
        
        # Google 스타일 크롤러
        print("🔍 Google 스타일 크롤러 테스트...")
        google_crawler = GoogleStyleCrawler()
        google_content = google_crawler.crawl_url(url)
        
        # 결과 비교
        print("\n📊 결과 비교:")
        print(f"   기존 크롤러: {len(traditional_content) if traditional_content else 0}자")
        print(f"   Google 스타일: {len(google_content) if google_content else 0}자")
        
        if traditional_content and google_content:
            # 텍스트 유사도 분석
            similarity = calculate_text_similarity(traditional_content, google_content)
            print(f"   텍스트 유사도: {similarity:.1%}")
            
            # 더 나은 결과 선택
            if len(google_content) > len(traditional_content):
                print("   🏆 Google 스타일이 더 많은 콘텐츠를 추출했습니다!")
            elif len(traditional_content) > len(google_content):
                print("   🏆 기존 크롤러가 더 많은 콘텐츠를 추출했습니다!")
            else:
                print("   🤝 두 크롤러가 비슷한 양의 콘텐츠를 추출했습니다.")
        
        return True
        
    except Exception as e:
        print(f"❌ 비교 테스트 중 오류: {e}")
        return False

def analyze_text_quality(text: str):
    """텍스트 품질 분석"""
    print(f"\n📈 텍스트 품질 분석:")
    
    # 기본 통계
    lines = text.split('\n')
    paragraphs = [line for line in lines if len(line.strip()) > 50]
    
    print(f"   • 총 문자 수: {len(text):,}자")
    print(f"   • 총 라인 수: {len(lines)}개")
    print(f"   • 의미있는 단락: {len(paragraphs)}개")
    
    # 평균 단락 길이
    if paragraphs:
        avg_length = sum(len(p) for p in paragraphs) / len(paragraphs)
        print(f"   • 평균 단락 길이: {avg_length:.0f}자")
    
    # 텍스트 밀도 (실제 텍스트 vs 공백)
    text_chars = len([c for c in text if c.isalnum() or c.isspace()])
    density = text_chars / len(text) if text else 0
    print(f"   • 텍스트 밀도: {density:.1%}")
    
    # 중복 라인 검사
    unique_lines = set(lines)
    duplicate_ratio = 1 - (len(unique_lines) / len(lines)) if lines else 0
    print(f"   • 중복 라인 비율: {duplicate_ratio:.1%}")

def calculate_text_similarity(text1: str, text2: str) -> float:
    """두 텍스트 간의 유사도 계산"""
    # 간단한 유사도 계산 (공통 단어 기반)
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)

def main():
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python tools/test_google_crawler.py test <URL>     # Google 스타일 크롤러 테스트")
        print("  python tools/test_google_crawler.py compare <URL>  # 크롤러 비교 테스트")
        return
    
    command = sys.argv[1]
    
    if command == "test":
        if len(sys.argv) < 3:
            print("❌ 테스트할 URL을 입력하세요")
            return
        url = sys.argv[2]
        test_google_style_crawler(url)
        
    elif command == "compare":
        if len(sys.argv) < 3:
            print("❌ 비교할 URL을 입력하세요")
            return
        url = sys.argv[2]
        compare_crawlers(url)
        
    else:
        print(f"❌ 알 수 없는 명령어: {command}")

if __name__ == "__main__":
    main() 