#!/usr/bin/env python3
"""
크롤링 파이프라인 직접 테스트 스크립트
"""

import sys
import os
import time
import requests
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_crawler_direct():
    """크롤러를 직접 테스트"""
    print("🔍 크롤링 파이프라인 직접 테스트 시작...")
    
    try:
        from app.services.crawler import crawl_url, get_text_from_url
        import asyncio
        
        # 테스트 URL들
        test_urls = [
            "https://www.example.com/",
            "https://httpbin.org/html",
            "https://jsonplaceholder.typicode.com/posts/1"
        ]
        
        print("\n1. 동기 크롤러 테스트:")
        for url in test_urls:
            print(f"\n   테스트 URL: {url}")
            start_time = time.time()
            
            try:
                content = crawl_url(url, use_google_style=True)
                end_time = time.time()
                
                if content:
                    print(f"   ✅ 성공: {len(content)}자 추출")
                    print(f"   ⏱️  소요시간: {end_time - start_time:.2f}초")
                    print(f"   📝 내용 미리보기: {content[:100]}...")
                else:
                    print(f"   ❌ 실패: 콘텐츠 추출 실패")
                    
            except Exception as e:
                print(f"   ❌ 오류: {e}")
        
        print("\n2. 비동기 크롤러 테스트:")
        async def test_async_crawler():
            for url in test_urls:
                print(f"\n   테스트 URL: {url}")
                start_time = time.time()
                
                try:
                    content = await get_text_from_url(url)
                    end_time = time.time()
                    
                    if content:
                        print(f"   ✅ 성공: {len(content)}자 추출")
                        print(f"   ⏱️  소요시간: {end_time - start_time:.2f}초")
                        print(f"   📝 내용 미리보기: {content[:100]}...")
                    else:
                        print(f"   ❌ 실패: 콘텐츠 추출 실패")
                        
                except Exception as e:
                    print(f"   ❌ 오류: {e}")
        
        # 비동기 테스트 실행
        asyncio.run(test_async_crawler())
        
        return True
        
    except Exception as e:
        print(f"❌ 크롤러 테스트 오류: {e}")
        return False

def test_crawler_with_requests():
    """requests를 사용한 기본 크롤링 테스트"""
    print("\n🔍 기본 requests 크롤링 테스트...")
    
    test_urls = [
        "https://www.example.com/",
        "https://httpbin.org/html",
        "https://jsonplaceholder.typicode.com/posts/1"
    ]
    
    for url in test_urls:
        print(f"\n   테스트 URL: {url}")
        start_time = time.time()
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # 간단한 텍스트 추출
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # body 텍스트 추출
            if soup.body:
                content = soup.body.get_text(strip=True)
                end_time = time.time()
                
                print(f"   ✅ 성공: {len(content)}자 추출")
                print(f"   ⏱️  소요시간: {end_time - start_time:.2f}초")
                print(f"   📝 내용 미리보기: {content[:100]}...")
            else:
                print(f"   ❌ 실패: body 태그 없음")
                
        except Exception as e:
            print(f"   ❌ 오류: {e}")
    
    return True

def test_api_endpoint():
    """API 엔드포인트 테스트"""
    print("\n🔍 API 엔드포인트 테스트...")
    
    test_data = {
        "url": "https://www.example.com/",
        "ai_mode": "gemini_2_0_flash",
        "content_length": "1000"
    }
    
    try:
        print(f"   테스트 URL: {test_data['url']}")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/api/v1/generate-post-gemini-2-flash",
            json=test_data,
            timeout=60
        )
        
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ API 호출 성공")
                print(f"   ⏱️  소요시간: {end_time - start_time:.2f}초")
                
                # 크롤링 결과 확인
                if 'crawled_content' in data:
                    content = data['crawled_content']
                    print(f"   📝 크롤링 결과: {len(content)}자")
                    print(f"   📝 내용 미리보기: {content[:100]}...")
                else:
                    print(f"   ⚠️  크롤링 결과 없음")
                    
            else:
                print(f"   ❌ API 응답 실패: {data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ HTTP 오류: {response.status_code}")
            print(f"   응답: {response.text}")
            
    except Exception as e:
        print(f"   ❌ API 테스트 오류: {e}")
    
    return True

def main():
    """메인 함수"""
    print("🔍 크롤링 파이프라인 종합 테스트를 시작합니다...")
    print("="*60)
    
    # 1. 기본 requests 테스트
    test_crawler_with_requests()
    
    # 2. 직접 크롤러 테스트
    test_crawler_direct()
    
    # 3. API 엔드포인트 테스트
    test_api_endpoint()
    
    print("\n" + "="*60)
    print("✅ 크롤링 파이프라인 테스트가 완료되었습니다!")
    print("="*60)

if __name__ == "__main__":
    main() 