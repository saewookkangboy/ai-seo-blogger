#!/usr/bin/env python3
"""
크롤링만 테스트하는 스크립트
"""

import sys
import os
import requests
import json

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_crawling_only():
    """크롤링만 테스트"""
    print("🔍 크롤링 전용 테스트 시작...")
    
    test_urls = [
        "https://www.example.com/",
        "https://httpbin.org/html",
        "https://jsonplaceholder.typicode.com/posts/1"
    ]
    
    for url in test_urls:
        print(f"\n📝 테스트 URL: {url}")
        
        try:
            # 크롤링 API 호출 (AI 생성 없이)
            response = requests.post(
                "http://localhost:8000/api/v1/crawl-url",
                json={"url": url},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    content = data.get('content', '')
                    print(f"   ✅ 크롤링 성공: {len(content)}자")
                    print(f"   📝 내용 미리보기: {content[:100]}...")
                else:
                    print(f"   ❌ 크롤링 실패: {data.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP 오류: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 요청 오류: {e}")

if __name__ == "__main__":
    test_crawling_only() 