#!/usr/bin/env python3
"""
고급 SEO 분석 테스트 스크립트
"""

import sys
import os
import json
import requests
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SEOAnalysisTest:
    """SEO 분석 테스트 클래스"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {}
        }
    
    def test_seo_analysis(self):
        """SEO 분석 테스트"""
        print("🔍 고급 SEO 분석 테스트 시작...")
        
        # 테스트용 HTML 콘텐츠
        test_content = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <title>AI 기술의 미래와 발전 방향</title>
            <meta name="description" content="인공지능 기술의 현재와 미래 발전 방향에 대해 자세히 알아보세요. AI 기술의 혁신과 우리 삶에 미치는 영향을 분석합니다.">
        </head>
        <body>
            <h1>AI 기술의 미래와 발전 방향</h1>
            <p>인공지능(AI) 기술은 현재 우리 삶의 모든 영역에서 혁신을 가져오고 있습니다. 머신러닝과 딥러닝 기술의 발전으로 AI는 더욱 정교하고 유용한 도구로 발전하고 있습니다.</p>
            
            <h2>AI 기술의 현재 상황</h2>
            <p>현재 AI 기술은 자연어 처리, 컴퓨터 비전, 음성 인식 등 다양한 분야에서 놀라운 성과를 보여주고 있습니다. 특히 GPT와 같은 대규모 언어 모델의 등장으로 AI의 활용 범위가 크게 확장되었습니다.</p>
            
            <h2>AI 기술의 미래 전망</h2>
            <p>AI 기술의 미래는 더욱 밝습니다. 강화학습과 생성형 AI의 발전으로 AI는 창의적인 작업까지 수행할 수 있게 되었습니다. 또한 AI 윤리와 안전성에 대한 연구도 활발히 진행되고 있습니다.</p>
            
            <h3>AI 기술의 주요 응용 분야</h3>
            <ul>
                <li>의료 진단 및 치료</li>
                <li>자율주행 자동차</li>
                <li>스마트 홈 시스템</li>
                <li>교육 및 학습</li>
            </ul>
            
            <p>AI 기술은 계속해서 발전하고 있으며, 우리의 삶을 더욱 편리하고 효율적으로 만들어줄 것입니다. <a href="/ai-trends">AI 트렌드</a>와 <a href="/ai-applications">AI 응용사례</a>에 대해 더 자세히 알아보세요.</p>
            
            <img src="/images/ai-future.jpg" alt="AI 기술의 미래">
        </body>
        </html>
        """
        
        test_data = {
            "content": test_content,
            "url": "https://example.com/ai-future",
            "target_keywords": ["AI", "인공지능", "머신러닝", "기술", "미래"]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/seo-analysis",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('data', {})
                
                print(f"✅ SEO 분석 테스트 성공")
                print(f"   - 종합 점수: {result.get('overall_score', 0)}점")
                print(f"   - 콘텐츠 점수: {result.get('content_score', 0)}점")
                print(f"   - 기술 점수: {result.get('technical_score', 0)}점")
                print(f"   - 키워드 점수: {result.get('keyword_score', 0)}점")
                print(f"   - 가독성 점수: {result.get('readability_score', 0)}점")
                
                metrics = result.get('metrics', {})
                print(f"   - 제목 길이: {metrics.get('title_length', 0)}자")
                print(f"   - 메타 설명 길이: {metrics.get('meta_length', 0)}자")
                print(f"   - 콘텐츠 길이: {metrics.get('content_length', 0)}자")
                print(f"   - 내부 링크: {metrics.get('internal_links', 0)}개")
                print(f"   - 외부 링크: {metrics.get('external_links', 0)}개")
                
                recommendations = result.get('recommendations', [])
                issues = result.get('issues', [])
                
                if recommendations:
                    print(f"   - 권장사항: {len(recommendations)}개")
                    for i, rec in enumerate(recommendations[:3], 1):
                        print(f"     {i}. {rec}")
                
                if issues:
                    print(f"   - 개선사항: {len(issues)}개")
                    for i, issue in enumerate(issues[:3], 1):
                        print(f"     {i}. {issue}")
                
                test_result = {
                    "test": "seo_analysis",
                    "status": "success",
                    "overall_score": result.get('overall_score', 0),
                    "content_score": result.get('content_score', 0),
                    "technical_score": result.get('technical_score', 0),
                    "keyword_score": result.get('keyword_score', 0),
                    "readability_score": result.get('readability_score', 0),
                    "recommendations_count": len(recommendations),
                    "issues_count": len(issues),
                    "metrics": metrics
                }
                
            else:
                print(f"❌ SEO 분석 테스트 실패: {response.status_code}")
                print(f"   응답: {response.text}")
                test_result = {
                    "test": "seo_analysis",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
            
            self.test_results["tests"].append(test_result)
            return test_result["status"] == "success"
            
        except Exception as e:
            print(f"❌ SEO 분석 테스트 오류: {e}")
            test_result = {
                "test": "seo_analysis",
                "status": "error",
                "error": str(e)
            }
            self.test_results["tests"].append(test_result)
            return False
    
    def test_seo_analysis_with_poor_content(self):
        """SEO 분석 테스트 (낮은 품질 콘텐츠)"""
        print("\n🔍 SEO 분석 테스트 (낮은 품질 콘텐츠)...")
        
        # 낮은 품질의 HTML 콘텐츠
        poor_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI</title>
        </head>
        <body>
            <p>AI는 좋습니다.</p>
        </body>
        </html>
        """
        
        test_data = {
            "content": poor_content,
            "url": "https://example.com/poor-content",
            "target_keywords": ["AI", "인공지능"]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/seo-analysis",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('data', {})
                
                print(f"✅ 낮은 품질 콘텐츠 SEO 분석 성공")
                print(f"   - 종합 점수: {result.get('overall_score', 0)}점")
                print(f"   - 콘텐츠 점수: {result.get('content_score', 0)}점")
                print(f"   - 기술 점수: {result.get('technical_score', 0)}점")
                
                issues = result.get('issues', [])
                if issues:
                    print(f"   - 발견된 문제점: {len(issues)}개")
                    for i, issue in enumerate(issues[:5], 1):
                        print(f"     {i}. {issue}")
                
                test_result = {
                    "test": "seo_analysis_poor_content",
                    "status": "success",
                    "overall_score": result.get('overall_score', 0),
                    "issues_count": len(issues)
                }
                
            else:
                print(f"❌ 낮은 품질 콘텐츠 SEO 분석 실패: {response.status_code}")
                test_result = {
                    "test": "seo_analysis_poor_content",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}"
                }
            
            self.test_results["tests"].append(test_result)
            return test_result["status"] == "success"
            
        except Exception as e:
            print(f"❌ 낮은 품질 콘텐츠 SEO 분석 오류: {e}")
            test_result = {
                "test": "seo_analysis_poor_content",
                "status": "error",
                "error": str(e)
            }
            self.test_results["tests"].append(test_result)
            return False
    
    def save_results(self, filename: str = None):
        """테스트 결과를 파일로 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"seo_analysis_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 테스트 결과가 {filename}에 저장되었습니다.")
        except Exception as e:
            print(f"❌ 결과 저장 실패: {e}")
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "="*60)
        print("고급 SEO 분석 테스트 결과")
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
                if test.get('overall_score'):
                    print(f"   종합 점수: {test['overall_score']}점")
                if test.get('error'):
                    print(f"   오류: {test['error']}")
        
        print("\n✅ 고급 SEO 분석 테스트가 완료되었습니다!")

def main():
    """메인 함수"""
    print("🔍 고급 SEO 분석 테스트를 시작합니다...")
    
    tester = SEOAnalysisTest()
    
    # 테스트 실행
    test1_success = tester.test_seo_analysis()
    test2_success = tester.test_seo_analysis_with_poor_content()
    
    # 결과 저장 및 출력
    tester.save_results()
    tester.print_summary()

if __name__ == "__main__":
    main() 