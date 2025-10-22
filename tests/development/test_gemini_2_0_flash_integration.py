#!/usr/bin/env python3
"""
Gemini 2.0 Flash 통합 테스트 스크립트
실제 API 엔드포인트를 테스트합니다.
"""

import asyncio
import sys
import os
import json
import requests
from datetime import datetime
import time

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

class Gemini2FlashIntegrationTest:
    """Gemini 2.0 Flash 통합 테스트 클래스"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {}
        }
    
    def test_system_status(self):
        """시스템 상태 테스트"""
        print("🔍 시스템 상태 확인 중...")
        try:
            response = requests.get(f"{self.base_url}/api/v1/system-status", timeout=30)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 시스템 상태: {data.get('overall_status', '알 수 없음')}")
                print(f"   - Gemini API: {'✅' if data.get('apis', {}).get('gemini') else '❌'}")
                return True
            else:
                print(f"❌ 시스템 상태 확인 실패: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 시스템 상태 확인 오류: {e}")
            return False
    
    def test_gemini_2_0_flash_endpoint(self):
        """Gemini 2.0 Flash 엔드포인트 테스트"""
        print("\n🚀 Gemini 2.0 Flash 엔드포인트 테스트...")
        
        test_data = {
            "text": """
            Artificial Intelligence (AI) is revolutionizing the way we live and work. 
            From virtual assistants to autonomous vehicles, AI technologies are becoming 
            increasingly integrated into our daily lives. Machine learning algorithms 
            can now process vast amounts of data to identify patterns and make predictions 
            with remarkable accuracy.
            
            The impact of AI on various industries is profound. In healthcare, AI is 
            helping doctors diagnose diseases more accurately and develop personalized 
            treatment plans. In finance, AI algorithms are detecting fraudulent transactions 
            and optimizing investment strategies. In education, AI-powered platforms are 
            providing personalized learning experiences for students.
            
            However, the rapid advancement of AI also raises important questions about 
            privacy, security, and the future of work. As AI systems become more capable, 
            we must ensure they are developed and deployed responsibly, with proper 
            safeguards to protect human rights and promote social good.
            """,
            "ai_mode": "gemini_2_0_flash",
            "content_length": "3000",
            "rules": ["AI_SEO", "AI_SEARCH"]
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/generate-post-gemini-2-flash",
                json=test_data,
                timeout=60
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Gemini 2.0 Flash 테스트 성공 ({duration:.2f}초)")
                print(f"   - 제목: {data.get('data', {}).get('title', 'N/A')[:50]}...")
                print(f"   - 콘텐츠 길이: {len(data.get('data', {}).get('content', ''))}자")
                print(f"   - 키워드: {data.get('data', {}).get('keywords', 'N/A')}")
                print(f"   - AI 모드: {data.get('data', {}).get('ai_mode', 'N/A')}")
                
                result = {
                    "test": "gemini_2_0_flash_endpoint",
                    "status": "success",
                    "duration": round(duration, 2),
                    "content_length": len(data.get('data', {}).get('content', '')),
                    "keywords": data.get('data', {}).get('keywords', ''),
                    "ai_mode": data.get('data', {}).get('ai_mode', '')
                }
            else:
                print(f"❌ Gemini 2.0 Flash 테스트 실패: {response.status_code}")
                print(f"   응답: {response.text}")
                result = {
                    "test": "gemini_2_0_flash_endpoint",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "duration": round(duration, 2)
                }
            
            self.test_results["tests"].append(result)
            return result["status"] == "success"
            
        except Exception as e:
            print(f"❌ Gemini 2.0 Flash 테스트 오류: {e}")
            result = {
                "test": "gemini_2_0_flash_endpoint",
                "status": "error",
                "error": str(e),
                "duration": 0
            }
            self.test_results["tests"].append(result)
            return False
    
    def test_regular_gemini_endpoint(self):
        """일반 Gemini 엔드포인트 테스트 (비교용)"""
        print("\n🔍 일반 Gemini 엔드포인트 테스트 (비교용)...")
        
        test_data = {
            "text": """
            Artificial Intelligence (AI) is transforming the way we live and work. 
            From virtual assistants to autonomous vehicles, AI technologies are becoming 
            increasingly integrated into our daily lives.
            """,
            "ai_mode": "informative",
            "content_length": "2000",
            "rules": ["AI_SEO"]
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/generate-post-gemini",
                json=test_data,
                timeout=60
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 일반 Gemini 테스트 성공 ({duration:.2f}초)")
                print(f"   - 제목: {data.get('data', {}).get('title', 'N/A')[:50]}...")
                print(f"   - 콘텐츠 길이: {len(data.get('data', {}).get('content', ''))}자")
                print(f"   - AI 모드: {data.get('data', {}).get('ai_mode', 'N/A')}")
                
                result = {
                    "test": "regular_gemini_endpoint",
                    "status": "success",
                    "duration": round(duration, 2),
                    "content_length": len(data.get('data', {}).get('content', '')),
                    "ai_mode": data.get('data', {}).get('ai_mode', '')
                }
            else:
                print(f"❌ 일반 Gemini 테스트 실패: {response.status_code}")
                result = {
                    "test": "regular_gemini_endpoint",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "duration": round(duration, 2)
                }
            
            self.test_results["tests"].append(result)
            return result["status"] == "success"
            
        except Exception as e:
            print(f"❌ 일반 Gemini 테스트 오류: {e}")
            result = {
                "test": "regular_gemini_endpoint",
                "status": "error",
                "error": str(e),
                "duration": 0
            }
            self.test_results["tests"].append(result)
            return False
    
    def test_frontend_options(self):
        """프론트엔드 옵션 테스트"""
        print("\n🌐 프론트엔드 옵션 확인...")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                html_content = response.text
                
                # Gemini 2.0 Flash 옵션이 있는지 확인
                if 'gemini_2_0_flash' in html_content:
                    print("✅ 프론트엔드에 Gemini 2.0 Flash 옵션이 포함되어 있습니다.")
                    result = {
                        "test": "frontend_options",
                        "status": "success",
                        "message": "Gemini 2.0 Flash 옵션 확인됨"
                    }
                else:
                    print("❌ 프론트엔드에 Gemini 2.0 Flash 옵션이 없습니다.")
                    result = {
                        "test": "frontend_options",
                        "status": "failed",
                        "error": "Gemini 2.0 Flash 옵션을 찾을 수 없음"
                    }
                
                self.test_results["tests"].append(result)
                return result["status"] == "success"
            else:
                print(f"❌ 프론트엔드 접근 실패: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 프론트엔드 테스트 오류: {e}")
            return False
    
    def save_results(self, filename: str = None):
        """테스트 결과를 파일로 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gemini_2_0_flash_integration_test_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 테스트 결과가 {filename}에 저장되었습니다.")
        except Exception as e:
            print(f"❌ 결과 저장 실패: {e}")
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "="*60)
        print("Gemini 2.0 Flash 통합 테스트 결과")
        print("="*60)
        
        total_tests = len(self.test_results["tests"])
        successful_tests = sum(1 for test in self.test_results["tests"] if test.get("status") == "success")
        failed_tests = total_tests - successful_tests
        
        print(f"총 테스트 수: {total_tests}")
        print(f"성공: {successful_tests}")
        print(f"실패: {failed_tests}")
        print(f"성공률: {(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        if self.test_results["tests"]:
            print("\n상세 결과:")
            for i, test in enumerate(self.test_results["tests"], 1):
                print(f"{i}. {test.get('test', 'unknown')}: {test.get('status', 'unknown')}")
                if test.get('duration'):
                    print(f"   소요시간: {test['duration']}초")
                if test.get('error'):
                    print(f"   오류: {test['error']}")
                if test.get('message'):
                    print(f"   메시지: {test['message']}")

def main():
    """메인 테스트 함수"""
    print("Gemini 2.0 Flash 통합 테스트를 시작합니다...")
    
    # API 키 확인 - Gemini API 숨김 처리됨
    # if not settings.get_gemini_api_key():
    #     print("❌ Gemini API 키가 설정되지 않았습니다.")
    #     print("환경변수 GEMINI_API_KEY를 설정해주세요.")
    #     return
    
    # print("✅ Gemini API 키가 설정되었습니다.")
    print("ℹ️ Gemini API 기능이 숨김 처리되었습니다.")
    
    # 테스트 인스턴스 생성
    tester = Gemini2FlashIntegrationTest()
    
    # 1. 시스템 상태 확인
    if not tester.test_system_status():
        print("❌ 시스템이 실행되지 않고 있습니다. 먼저 서버를 시작해주세요.")
        return
    
    # 2. 프론트엔드 옵션 확인
    tester.test_frontend_options()
    
    # 3. 일반 Gemini 엔드포인트 테스트
    tester.test_regular_gemini_endpoint()
    
    # 4. Gemini 2.0 Flash 엔드포인트 테스트
    tester.test_gemini_2_0_flash_endpoint()
    
    # 결과 저장 및 출력
    tester.save_results()
    tester.print_summary()
    
    print("\n✅ 통합 테스트가 완료되었습니다!")

if __name__ == "__main__":
    main() 