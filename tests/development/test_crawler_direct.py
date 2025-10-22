#!/usr/bin/env python3
"""
크롤러 직접 테스트 스크립트
"""

import sys
import os
import asyncio

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.crawler import get_text_from_url, crawl_url

async def test_crawler():
    """크롤러 직접 테스트"""
    print("🔍 크롤러 직접 테스트 시작...")
    
    test_urls = [
        "https://www.example.com/",
        "https://httpbin.org/html",
        "https://jsonplaceholder.typicode.com/posts/1"
    ]
    
    for url in test_urls:
        print(f"\n📄 테스트 URL: {url}")
        
        try:
            # 동기 크롤러 테스트 (비동기로 처리됨)
            print("   동기 크롤러 테스트...")
            content = await crawl_url(url, use_google_style=True)
            if content:
                print(f"   ✅ 동기 크롤러 성공: {len(content)}자")
                print(f"   📝 내용 미리보기: {content[:200]}...")
            else:
                print("   ❌ 동기 크롤러 실패")
            
            # 비동기 크롤러 테스트
            print("   비동기 크롤러 테스트...")
            content_async = await get_text_from_url(url)
            if content_async:
                print(f"   ✅ 비동기 크롤러 성공: {len(content_async)}자")
                print(f"   📝 내용 미리보기: {content_async[:200]}...")
            else:
                print("   ❌ 비동기 크롤러 실패")
                
        except Exception as e:
            print(f"   ❌ 크롤러 테스트 오류: {e}")

if __name__ == "__main__":
    asyncio.run(test_crawler()) 