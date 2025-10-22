#!/usr/bin/env python3
"""
간단한 Gemini-2.0-flash 번역 테스트
"""

import sys
import os
import asyncio
import httpx
import json

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

async def test_gemini_2_translation():
    """Gemini-2.0-flash 번역 테스트"""
    
    # API 키 가져오기
    api_key = settings.get_gemini_api_key()
    if not api_key:
        print("❌ Gemini API 키가 설정되지 않았습니다.")
        return
    
    print("🔧 Gemini-2.0-flash 번역 테스트")
    print("=" * 50)
    
    # 테스트 텍스트
    test_text = "Hello, how are you today?"
    target_language = "ko"
    
    print(f"📝 테스트 텍스트: {test_text}")
    print(f"🌐 대상 언어: {target_language}")
    
    # API URL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    # 요청 페이로드
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"다음 텍스트를 {target_language}로 번역해주세요. 원문의 의미와 톤을 유지하면서 자연스럽게 번역해주세요:\n\n{test_text}"
                    }
                ]
            }
        ]
    }
    
    try:
        print("\n🔄 번역 요청 중...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
        
        print(f"📊 응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API 호출 성공!")
            
            if 'candidates' in data and len(data['candidates']) > 0:
                translated_text = data['candidates'][0]['content']['parts'][0]['text']
                print(f"📝 번역 결과: {translated_text}")
            else:
                print("❌ 응답에 번역 결과가 없습니다.")
                print(f"📄 응답 내용: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ API 오류: {response.status_code}")
            print(f"📄 오류 내용: {response.text}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

async def test_gemini_2_generation():
    """Gemini-2.0-flash 기본 생성 테스트"""
    
    # API 키 가져오기
    api_key = settings.get_gemini_api_key()
    if not api_key:
        print("❌ Gemini API 키가 설정되지 않았습니다.")
        return
    
    print("\n🔧 Gemini-2.0-flash 기본 생성 테스트")
    print("=" * 50)
    
    # 테스트 프롬프트
    prompt = "Explain how AI works in a few words"
    
    print(f"📝 프롬프트: {prompt}")
    
    # API URL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    # 요청 페이로드
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    try:
        print("\n🔄 생성 요청 중...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
        
        print(f"📊 응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API 호출 성공!")
            
            if 'candidates' in data and len(data['candidates']) > 0:
                generated_text = data['candidates'][0]['content']['parts'][0]['text']
                print(f"📝 생성 결과: {generated_text}")
            else:
                print("❌ 응답에 생성 결과가 없습니다.")
                print(f"📄 응답 내용: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ API 오류: {response.status_code}")
            print(f"📄 오류 내용: {response.text}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

async def main():
    """메인 함수"""
    print("🚀 Gemini-2.0-flash 모델 테스트 시작")
    print("=" * 60)
    
    # 1. 기본 생성 테스트
    await test_gemini_2_generation()
    
    # 2. 번역 테스트
    await test_gemini_2_translation()
    
    print("\n✅ 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main()) 