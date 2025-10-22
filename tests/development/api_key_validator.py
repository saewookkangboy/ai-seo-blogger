#!/usr/bin/env python3
"""
API 키 유효성 검사 스크립트
OpenAI와 Google Gemini API 키의 유효성을 검사합니다.
"""

import asyncio
import sys
import os
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
import openai
import httpx

async def test_openai_api_key():
    """OpenAI API 키 유효성 검사"""
    print("🔍 OpenAI API 키 검증 중...")
    
    if not settings.openai_api_key:
        print("❌ OpenAI API 키가 설정되지 않았습니다.")
        return False
    
    try:
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print("✅ OpenAI API 키가 유효합니다.")
        print(f"   모델: {response.model}")
        print(f"   사용량: {response.usage.total_tokens} 토큰")
        return True
    except Exception as e:
        print(f"❌ OpenAI API 키 검증 실패: {e}")
        return False

async def test_gemini_api_key():
    """Google Gemini API 키 유효성 검사"""
    print("🔍 Google Gemini API 키 검증 중...")
    
    if not settings.gemini_api_key:
        print("❌ Gemini API 키가 설정되지 않았습니다.")
        return False
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.gemini_api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": "Hello"
                }]
            }]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            
            if response.status_code == 200:
                print("✅ Google Gemini API 키가 유효합니다.")
                return True
            else:
                print(f"❌ Google Gemini API 키 검증 실패: HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Google Gemini API 키 검증 실패: {e}")
        return False

async def main():
    """메인 함수"""
    print("=" * 50)
    print("API 키 유효성 검사")
    print("=" * 50)
    print(f"검사 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 설정 검증
    errors = settings.validate_settings()
    if errors:
        print("⚠️  설정 경고:")
        for error in errors:
            print(f"  - {error}")
        print()
    
    # API 키 검증
    openai_valid = await test_openai_api_key()
    print()
    gemini_valid = await test_gemini_api_key()
    print()
    
    # 결과 요약
    print("=" * 50)
    print("검사 결과 요약")
    print("=" * 50)
    print(f"OpenAI API: {'✅ 유효' if openai_valid else '❌ 무효'}")
    print(f"Gemini API: {'✅ 유효' if gemini_valid else '❌ 무효'}")
    
    if openai_valid and gemini_valid:
        print("\n🎉 모든 API 키가 유효합니다!")
    else:
        print("\n⚠️  일부 API 키에 문제가 있습니다. .env 파일을 확인해주세요.")

if __name__ == "__main__":
    asyncio.run(main()) 