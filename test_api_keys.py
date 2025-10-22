#!/usr/bin/env python3
"""
API Key 정상작동 확인 스크립트
모든 API Key가 올바르게 설정되어 있고 실제로 작동하는지 테스트합니다.
"""

import os
import sys
import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, List, Tuple

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

class APIKeyTester:
    """API Key 테스터 클래스"""
    
    def __init__(self):
        self.results = {}
        self.test_text = "Hello, this is a test message for API validation."
        
    async def test_openai_api(self) -> Dict:
        """OpenAI API 테스트"""
        print("🔍 OpenAI API 테스트 중...")
        
        api_key = settings.get_openai_api_key()
        if not api_key:
            return {
                "status": "error",
                "message": "OpenAI API 키가 설정되지 않았습니다.",
                "details": "config.py 또는 .env 파일에서 OPENAI_API_KEY를 설정하세요."
            }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "user", "content": "Say 'OpenAI API is working' in Korean"}
                        ],
                        "max_tokens": 50
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    return {
                        "status": "success",
                        "message": "OpenAI API 정상 작동",
                        "response": content,
                        "model": "gpt-4o-mini"
                    }
                elif response.status_code == 401:
                    return {
                        "status": "error",
                        "message": "OpenAI API 키가 유효하지 않습니다.",
                        "details": "API 키를 확인하고 다시 시도하세요."
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"OpenAI API 오류: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "message": f"OpenAI API 테스트 실패: {str(e)}",
                "details": "네트워크 연결 또는 API 서버 상태를 확인하세요."
            }
    
    async def test_gemini_api(self) -> Dict:
        """Gemini API 테스트"""
        print("🔍 Gemini API 테스트 중...")
        
        api_key = settings.get_gemini_api_key()
        if not api_key:
            return {
                "status": "error",
                "message": "Gemini API 키가 설정되지 않았습니다.",
                "details": "config.py 또는 .env 파일에서 GEMINI_API_KEY를 설정하세요."
            }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{
                            "parts": [{
                                "text": "Say 'Gemini API is working' in Korean"
                            }]
                        }]
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if 'candidates' in result and result['candidates']:
                        content = result['candidates'][0]['content']['parts'][0]['text']
                        return {
                            "status": "success",
                            "message": "Gemini API 정상 작동",
                            "response": content,
                            "model": "gemini-2.0-flash"
                        }
                    else:
                        return {
                            "status": "error",
                            "message": "Gemini API 응답 형식 오류",
                            "details": "API 응답에 예상된 데이터가 없습니다."
                        }
                elif response.status_code == 400:
                    return {
                        "status": "error",
                        "message": "Gemini API 요청 형식 오류",
                        "details": response.text
                    }
                elif response.status_code == 403:
                    return {
                        "status": "error",
                        "message": "Gemini API 키가 유효하지 않습니다.",
                        "details": "API 키를 확인하고 다시 시도하세요."
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Gemini API 오류: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "message": f"Gemini API 테스트 실패: {str(e)}",
                "details": "네트워크 연결 또는 API 서버 상태를 확인하세요."
            }
    
    async def test_deepl_api(self) -> Dict:
        """DeepL API 테스트"""
        print("🔍 DeepL API 테스트 중...")
        
        api_key = settings.get_deepl_api_key()
        if not api_key:
            return {
                "status": "warning",
                "message": "DeepL API 키가 설정되지 않았습니다.",
                "details": "DeepL은 선택사항이며, Gemini API로 대체됩니다."
            }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api-free.deepl.com/v2/translate",
                    headers={
                        "Authorization": f"DeepL-Auth-Key {api_key}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={
                        "text": self.test_text,
                        "target_lang": "KO"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    translated_text = result['translations'][0]['text']
                    return {
                        "status": "success",
                        "message": "DeepL API 정상 작동",
                        "response": translated_text,
                        "model": "DeepL Free API"
                    }
                elif response.status_code == 403:
                    return {
                        "status": "error",
                        "message": "DeepL API 키가 유효하지 않습니다.",
                        "details": "API 키를 확인하고 다시 시도하세요."
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"DeepL API 오류: {response.status_code}",
                        "details": response.text
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "message": f"DeepL API 테스트 실패: {str(e)}",
                "details": "네트워크 연결 또는 API 서버 상태를 확인하세요."
            }
    
    def test_config_validation(self) -> Dict:
        """설정 유효성 검사"""
        print("🔍 설정 유효성 검사 중...")
        
        errors = settings.validate_settings()
        
        if errors:
            return {
                "status": "error",
                "message": "설정 유효성 검사 실패",
                "details": errors
            }
        else:
            return {
                "status": "success",
                "message": "모든 설정이 유효합니다.",
                "details": []
            }
    
    def check_env_file(self) -> Dict:
        """환경 변수 파일 확인"""
        print("🔍 환경 변수 파일 확인 중...")
        
        env_file = ".env"
        if not os.path.exists(env_file):
            return {
                "status": "warning",
                "message": ".env 파일이 존재하지 않습니다.",
                "details": "env.example을 .env로 복사하고 API 키를 설정하세요."
            }
        
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # API 키 설정 확인
        api_keys = {
            "OPENAI_API_KEY": "OPENAI_API_KEY" in content,
            "GEMINI_API_KEY": "GEMINI_API_KEY" in content,
            "DEEPL_API_KEY": "DEEPL_API_KEY" in content
        }
        
        missing_keys = [key for key, exists in api_keys.items() if not exists]
        
        if missing_keys:
            return {
                "status": "warning",
                "message": f"다음 API 키가 .env 파일에 설정되지 않았습니다: {', '.join(missing_keys)}",
                "details": "env.example을 참고하여 API 키를 설정하세요."
            }
        else:
            return {
                "status": "success",
                "message": ".env 파일에 모든 API 키가 설정되어 있습니다.",
                "details": list(api_keys.keys())
            }
    
    async def run_all_tests(self) -> Dict:
        """모든 테스트 실행"""
        print("🚀 API Key 테스트 시작")
        print("=" * 50)
        
        # 설정 검사
        self.results['config_validation'] = self.test_config_validation()
        self.results['env_file'] = self.check_env_file()
        
        # API 테스트
        self.results['openai'] = await self.test_openai_api()
        self.results['gemini'] = await self.test_gemini_api()
        self.results['deepl'] = await self.test_deepl_api()
        
        return self.results
    
    def print_results(self):
        """결과 출력"""
        print("\n📊 API Key 테스트 결과")
        print("=" * 50)
        
        status_colors = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️"
        }
        
        for api_name, result in self.results.items():
            color = status_colors.get(result['status'], "❓")
            print(f"\n{color} {api_name.upper()}: {result['message']}")
            
            if 'response' in result:
                print(f"   응답: {result['response']}")
            
            if 'details' in result and result['details']:
                if isinstance(result['details'], list):
                    for detail in result['details']:
                        print(f"   - {detail}")
                else:
                    print(f"   상세: {result['details']}")
        
        # 요약
        print("\n📋 요약")
        print("-" * 30)
        
        success_count = sum(1 for r in self.results.values() if r['status'] == 'success')
        error_count = sum(1 for r in self.results.values() if r['status'] == 'error')
        warning_count = sum(1 for r in self.results.values() if r['status'] == 'warning')
        
        print(f"✅ 성공: {success_count}개")
        print(f"❌ 오류: {error_count}개")
        print(f"⚠️ 경고: {warning_count}개")
        
        if error_count == 0:
            print("\n🎉 모든 API Key가 정상 작동합니다!")
        else:
            print(f"\n⚠️ {error_count}개의 API Key에 문제가 있습니다. 위의 상세 내용을 확인하세요.")

async def main():
    """메인 함수"""
    tester = APIKeyTester()
    results = await tester.run_all_tests()
    tester.print_results()
    
    # 결과를 JSON 파일로 저장
    with open('api_key_test_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 결과가 'api_key_test_results.json' 파일에 저장되었습니다.")

if __name__ == "__main__":
    asyncio.run(main())
