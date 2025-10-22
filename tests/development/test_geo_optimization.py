#!/usr/bin/env python3
"""
GEO(Generative Engine Optimization) 최적화 테스트 스크립트
Search Engine Land의 GEO 가이드에 따른 생성형 AI 엔진 최적화 테스트
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.seo_analyzer import seo_analyzer
from app.services.content_generator import create_blog_post

class GEOTestSuite:
    """GEO 최적화 테스트 스위트"""
    
    def __init__(self):
        self.test_results = []
        self.test_content = {
            "good_geo": """
            <h1>AI 기반 콘텐츠 최적화 완전 가이드</h1>
            <p>생성형 AI 엔진 최적화(GEO)는 검색 엔진의 AI 시스템이 콘텐츠를 더 잘 이해하고 활용할 수 있도록 하는 전략입니다.</p>
            
            <h2>GEO란 무엇인가요?</h2>
            <p>Generative Engine Optimization(GEO)은 생성형 AI 엔진이 콘텐츠를 더 효과적으로 처리하고 사용자에게 제공할 수 있도록 최적화하는 방법입니다.</p>
            
            <h2>GEO 최적화 방법</h2>
            <h3>1단계: 구조화된 콘텐츠 작성</h3>
            <ul>
                <li>명확한 헤딩 구조 사용</li>
                <li>리스트와 테이블 활용</li>
                <li>FAQ 형식 포함</li>
            </ul>
            
            <h3>2단계: AI 친화적 요소 추가</h3>
            <ul>
                <li>구조화된 데이터 마크업</li>
                <li>시맨틱 HTML 사용</li>
                <li>명확한 답변 블록 생성</li>
            </ul>
            
            <h2>GEO 최적화 예시</h2>
            <table>
                <tr><th>요소</th><th>설명</th><th>중요도</th></tr>
                <tr><td>구조화된 데이터</td><td>Schema.org 마크업</td><td>높음</td></tr>
                <tr><td>명확한 답변</td><td>직접적인 답변 제공</td><td>높음</td></tr>
                <tr><td>출처 인용</td><td>검증 가능한 정보</td><td>중간</td></tr>
            </table>
            
            <h2>FAQ</h2>
            <details>
                <summary>GEO는 SEO와 어떻게 다른가요?</summary>
                <p>GEO는 생성형 AI 엔진에 특화된 최적화로, AI가 콘텐츠를 이해하고 활용하는 방식을 개선합니다.</p>
            </details>
            
            <details>
                <summary>GEO 최적화의 효과는 언제 나타나나요?</summary>
                <p>구조화된 콘텐츠와 AI 친화적 요소를 적용하면 즉시 AI 엔진의 이해도가 향상됩니다.</p>
            </details>
            """,
            
            "poor_geo": """
            <h1>콘텐츠 최적화</h1>
            <p>콘텐츠를 최적화하는 것은 중요합니다. 많은 사람들이 콘텐츠 최적화에 대해 이야기합니다. 
            콘텐츠 최적화는 웹사이트에서 중요한 역할을 합니다. 콘텐츠 최적화를 통해 더 나은 결과를 얻을 수 있습니다.</p>
            
            <p>콘텐츠 최적화에는 여러 가지 방법이 있습니다. 첫 번째로 키워드를 사용하는 것입니다. 
            키워드는 검색에서 중요한 역할을 합니다. 두 번째로 링크를 사용하는 것입니다. 
            링크는 웹사이트 간의 연결을 제공합니다.</p>
            
            <p>또한 콘텐츠 최적화에서는 구조가 중요합니다. 구조화된 콘텐츠는 사용자가 이해하기 쉽습니다. 
            구조화된 콘텐츠는 검색 엔진에서도 좋은 평가를 받습니다.</p>
            
            <p>마지막으로 콘텐츠 최적화에서는 품질이 중요합니다. 품질 좋은 콘텐츠는 사용자에게 가치를 제공합니다. 
            품질 좋은 콘텐츠는 검색 엔진에서도 높은 순위를 받습니다.</p>
            """
        }
    
    async def test_geo_analysis(self):
        """GEO 분석 기능 테스트"""
        print("🔍 GEO 분석 기능 테스트 시작...")
        
        try:
            # 좋은 GEO 콘텐츠 분석
            print("\n📊 좋은 GEO 콘텐츠 분석...")
            good_analysis = await seo_analyzer.analyze_content(
                self.test_content["good_geo"], 
                "AI 기반 콘텐츠 최적화, GEO, 생성형 AI"
            )
            
            # 나쁜 GEO 콘텐츠 분석
            print("📊 나쁜 GEO 콘텐츠 분석...")
            poor_analysis = await seo_analyzer.analyze_content(
                self.test_content["poor_geo"], 
                "콘텐츠 최적화, 키워드, 링크"
            )
            
            # 결과 비교
            comparison = {
                "good_geo": {
                    "overall_score": good_analysis.overall_score,
                    "geo_score": good_analysis.geo_optimization_score,
                    "structure_score": good_analysis.content_structure_score,
                    "eeat_score": good_analysis.eeat_score,
                    "technical_score": good_analysis.technical_optimization_score
                },
                "poor_geo": {
                    "overall_score": poor_analysis.overall_score,
                    "geo_score": poor_analysis.geo_optimization_score,
                    "structure_score": poor_analysis.content_structure_score,
                    "eeat_score": poor_analysis.eeat_score,
                    "technical_score": poor_analysis.technical_optimization_score
                }
            }
            
            self.test_results.append({
                "test_name": "GEO 분석 기능",
                "status": "PASS",
                "comparison": comparison,
                "timestamp": datetime.now().isoformat()
            })
            
            print("✅ GEO 분석 기능 테스트 완료")
            return comparison
            
        except Exception as e:
            print(f"❌ GEO 분석 기능 테스트 실패: {e}")
            self.test_results.append({
                "test_name": "GEO 분석 기능",
                "status": "FAIL",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return None
    
    async def test_geo_content_generation(self):
        """GEO 최적화 콘텐츠 생성 테스트"""
        print("\n🚀 GEO 최적화 콘텐츠 생성 테스트 시작...")
        
        try:
            # GEO 규칙을 적용한 콘텐츠 생성
            test_text = "AI 기반 콘텐츠 최적화에 대한 정보를 제공합니다."
            test_keywords = "AI 기반 콘텐츠 최적화, GEO, 생성형 AI, AI 엔진 최적화"
            
            print("📝 GEO 규칙 적용 콘텐츠 생성...")
            generation_result = await create_blog_post(
                text=test_text,
                keywords=test_keywords,
                rule_guidelines=["GEO"],
                content_length="2000",
                ai_mode="가이드"
            )
            
            if generation_result and 'content' in generation_result:
                content = generation_result['content']
                
                # 생성된 콘텐츠의 GEO 분석
                print("📊 생성된 콘텐츠 GEO 분석...")
                geo_analysis = await seo_analyzer.analyze_content(content, test_keywords)
                
                result = {
                    "content_length": len(content),
                    "word_count": generation_result.get('word_count', 0),
                    "geo_score": geo_analysis.geo_optimization_score,
                    "overall_score": geo_analysis.overall_score,
                    "geo_signals": len(geo_analysis.geo_analysis.get('geo_signals', [])),
                    "generative_patterns": len(geo_analysis.geo_analysis.get('generative_optimization', [])),
                    "ai_friendly_elements": sum(1 for v in geo_analysis.geo_analysis.get('ai_friendly_content', {}).values() if v > 0),
                    "structured_answers": len(geo_analysis.geo_analysis.get('structured_answers', []))
                }
                
                self.test_results.append({
                    "test_name": "GEO 콘텐츠 생성",
                    "status": "PASS",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
                
                print("✅ GEO 콘텐츠 생성 테스트 완료")
                return result
            else:
                raise Exception("콘텐츠 생성 실패")
                
        except Exception as e:
            print(f"❌ GEO 콘텐츠 생성 테스트 실패: {e}")
            self.test_results.append({
                "test_name": "GEO 콘텐츠 생성",
                "status": "FAIL",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return None
    
    def generate_geo_report(self):
        """GEO 테스트 리포트 생성"""
        print("\n📋 GEO 테스트 리포트 생성...")
        
        report = {
            "test_suite": "GEO(Generative Engine Optimization) 최적화 테스트",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for r in self.test_results if r["status"] == "PASS"),
                "failed_tests": sum(1 for r in self.test_results if r["status"] == "FAIL")
            },
            "test_results": self.test_results,
            "geo_guidelines": {
                "description": "Search Engine Land의 GEO 가이드에 따른 생성형 AI 엔진 최적화",
                "key_elements": [
                    "생성형 AI 엔진 친화적 콘텐츠 구조",
                    "Featured Snippet 및 AI 오버뷰 최적화",
                    "구조화된 답변 및 명확한 정보 계층",
                    "How-to, 정의, 비교, 단계별 가이드 패턴",
                    "AI가 이해하기 쉬운 시맨틱 HTML 구조",
                    "구조화된 데이터(Schema.org) 마크업",
                    "검증 가능한 출처 및 최신 정보"
                ],
                "scoring_criteria": {
                    "geo_signals": "생성형 AI 관련 키워드 및 신호 (25점)",
                    "generative_optimization": "생성형 엔진 친화적 패턴 (30점)",
                    "ai_friendly_content": "AI 친화적 콘텐츠 요소 (25점)",
                    "structured_answers": "구조화된 답변 요소 (20점)"
                }
            }
        }
        
        # 리포트 저장
        report_file = "geo_optimization_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 GEO 테스트 리포트 저장됨: {report_file}")
        return report
    
    def print_summary(self):
        """테스트 결과 요약 출력"""
        print("\n" + "="*60)
        print("🎯 GEO 최적화 테스트 결과 요약")
        print("="*60)
        
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        total = len(self.test_results)
        
        print(f"📊 총 테스트: {total}개")
        print(f"✅ 통과: {passed}개")
        print(f"❌ 실패: {failed}개")
        print(f"📈 성공률: {(passed/total*100):.1f}%" if total > 0 else "📈 성공률: 0%")
        
        print("\n🔍 상세 결과:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"  {status_icon} {result['test_name']}: {result['status']}")
            
            if result["status"] == "PASS" and "result" in result:
                if "geo_score" in result["result"]:
                    print(f"     GEO 점수: {result['result']['geo_score']}/100")
                if "overall_score" in result["result"]:
                    print(f"     종합 점수: {result['result']['overall_score']}/100")
            elif result["status"] == "FAIL" and "error" in result:
                print(f"     오류: {result['error']}")

async def main():
    """메인 테스트 실행 함수"""
    print("🚀 GEO(Generative Engine Optimization) 최적화 테스트 시작")
    print("="*60)
    
    test_suite = GEOTestSuite()
    
    # 1. GEO 분석 기능 테스트
    await test_suite.test_geo_analysis()
    
    # 2. GEO 콘텐츠 생성 테스트
    await test_suite.test_geo_content_generation()
    
    # 3. 리포트 생성
    test_suite.generate_geo_report()
    
    # 4. 결과 요약 출력
    test_suite.print_summary()
    
    print("\n🎉 GEO 최적화 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(main()) 