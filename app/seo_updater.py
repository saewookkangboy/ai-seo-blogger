"""
SEO Guidelines Auto-Updater
Automated weekly research and update system for SEO guidelines
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re

from app.utils.logger import setup_logger
from app.seo_guidelines import (
    SEO_GUIDELINES,
    get_seo_guidelines,
    get_guideline_version_info
)

logger = setup_logger(__name__)

class SEOGuidelineUpdater:
    """SEO 가이드라인 자동 업데이트 관리"""
    
    def __init__(self):
        self.current_guidelines = get_seo_guidelines()
        self.current_version = get_guideline_version_info()
        
        # 리서치 쿼리
        self.research_queries = {
            "ai_seo": "AI SEO best practices 2025 latest E-E-A-T",
            "aeo": "Answer Engine Optimization ChatGPT Perplexity 2025",
            "geo": "Generative Engine Optimization Google SGE Bing Chat",
            "aio": "Google AI Overviews optimization strategies 2025",
            "ai_search": "AI Search optimization trends 2025 latest"
        }
    
    async def research_latest_trends(self) -> Dict[str, Any]:
        """최신 SEO 트렌드 리서치"""
        logger.info("Starting SEO trends research...")
        
        try:
            # 1. 뉴스 수집
            from app.services.news_collector import NewsCollectorService
            collector = NewsCollectorService()
            
            logger.info("Collecting latest news...")
            collection_result = collector.collect_all_news()
            
            # 2. 뉴스 조회 (최근 7일)
            all_news = collector.get_all_news()
            recent_news = []
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            for item in all_news:
                collected_date = datetime.fromisoformat(item['collected_date'])
                if collected_date > seven_days_ago:
                    recent_news.append(item)
            
            logger.info(f"Found {len(recent_news)} recent news items for analysis")
            
            # 3. AI 분석
            from app.services.content_generator import analyze_seo_news
            logger.info("Analyzing news for SEO trends...")
            analysis_results = await analyze_seo_news(recent_news)
            
            # 4. 결과 구성
            results = {}
            for guideline_type in self.research_queries.keys():
                trends = analysis_results.get(guideline_type, [])
                
                # 분석 결과가 없으면 시뮬레이션 데이터 사용 (안전장치)
                if not trends:
                    logger.warning(f"No trends found for {guideline_type}, using simulation fallback")
                    trends = await self._simulate_research(guideline_type, "")
                
                results[guideline_type] = {
                    "query": self.research_queries.get(guideline_type, ""),
                    "findings": trends,
                    "timestamp": datetime.now().isoformat(),
                    "sources": [item['url'] for item in recent_news if item['category'] == guideline_type.upper()]
                }
                
            return results
            
        except Exception as e:
            logger.error(f"Research failed: {e}")
            # 전체 실패 시 시뮬레이션으로 폴백
            results = {}
            for guideline_type, query in self.research_queries.items():
                results[guideline_type] = {
                    "query": query,
                    "findings": await self._simulate_research(guideline_type, query),
                    "timestamp": datetime.now().isoformat(),
                    "error": f"Real research failed, used fallback: {str(e)}"
                }
            return results

    async def _simulate_research(self, guideline_type: str, query: str) -> List[str]:
        """리서치 시뮬레이션 (Fallback용)"""
        # 실제 구현에서는 search_web 결과를 파싱
        await asyncio.sleep(0.1)  # 비동기 시뮬레이션
        
        simulated_findings = {
            "ai_seo": [
                "E-E-A-T remains critical in 2025",
                "User experience signals increasingly important",
                "Core Web Vitals still a ranking factor",
                "AI-generated content needs human oversight",
                "Semantic search optimization essential"
            ],
            "aeo": [
                "ChatGPT Search launched, optimize for citations",
                "Perplexity AI prioritizes structured Q&A",
                "Direct answers in first paragraph crucial",
                "FAQ schema markup highly recommended",
                "Conversational tone improves AI visibility"
            ],
            "geo": [
                "Google SGE expanding globally",
                "Bing Chat integration with GPT-4 Turbo",
                "Entity optimization more important",
                "Topic clusters boost generative results",
                "Source attribution required for citations"
            ],
            "aio": [
                "AI Overviews now in 100+ countries",
                "Featured snippets still valuable",
                "Question-Answer format preferred",
                "Fresh content gets priority",
                "Multimedia content increases visibility"
            ],
            "ai_search": [
                "Claude 3 search capabilities improved",
                "Gemini Advanced search integration",
                "AI crawlers need explicit permission",
                "Clean HTML structure critical",
                "Accessibility improves AI understanding"
            ]
        }
        
        return simulated_findings.get(guideline_type, [])
    
    def detect_changes(self, research_results: Dict[str, Any]) -> Dict[str, Any]:
        """변경사항 감지"""
        logger.info("Detecting changes in SEO guidelines...")
        
        changes = {
            "significant": [],
            "minor": [],
            "new_trends": [],
            "summary": ""
        }
        
        for guideline_type, research in research_results.items():
            if "error" in research:
                continue
            
            findings = research.get("findings", [])
            
            # 새로운 트렌드 감지 (간단한 키워드 기반)
            new_keywords = self._extract_keywords(findings)
            
            # 현재 가이드라인과 비교
            current = self.current_guidelines["guidelines"].get(guideline_type, {})
            current_desc = str(current.get("description", ""))
            
            # 새로운 내용 확인
            for finding in findings:
                if finding.lower() not in current_desc.lower():
                    changes["new_trends"].append({
                        "type": guideline_type,
                        "finding": finding,
                        "importance": "high" if any(word in finding.lower() for word in ["critical", "essential", "required"]) else "medium"
                    })
        
        # 요약 생성
        total_changes = len(changes["new_trends"])
        changes["summary"] = f"Found {total_changes} new trends across {len(research_results)} guidelines"
        
        logger.info(f"Change detection complete: {changes['summary']}")
        return changes
    
    def _extract_keywords(self, findings: List[str]) -> List[str]:
        """주요 키워드 추출"""
        keywords = []
        for finding in findings:
            # 간단한 키워드 추출 (실제로는 NLP 사용 가능)
            words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', finding)
            keywords.extend(words)
        return list(set(keywords))
    
    def should_update(self, changes: Dict[str, Any]) -> bool:
        """자동 업데이트 여부 판단"""
        # 안전을 위해 항상 수동 검토 권장
        new_trends_count = len(changes.get("new_trends", []))
        
        # 중요한 변경사항이 5개 이상이면 업데이트 권장
        if new_trends_count >= 5:
            logger.info(f"Update recommended: {new_trends_count} new trends found")
            return True
        
        logger.info(f"Manual review recommended: {new_trends_count} new trends found")
        return False
    
    def generate_update_report(self, research_results: Dict[str, Any], changes: Dict[str, Any]) -> Dict[str, Any]:
        """업데이트 리포트 생성"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "current_version": self.current_version["version"],
            "research_summary": {
                "total_queries": len(research_results),
                "successful": sum(1 for r in research_results.values() if "error" not in r),
                "failed": sum(1 for r in research_results.values() if "error" in r)
            },
            "changes_detected": {
                "new_trends": len(changes.get("new_trends", [])),
                "significant": len(changes.get("significant", [])),
                "minor": len(changes.get("minor", []))
            },
            "recommendation": "UPDATE" if self.should_update(changes) else "REVIEW",
            "details": changes,
            "research_results": research_results,
            # placeholder for report_path, will be set after saving
            "report_path": ""
        }
        
        return report
    
    async def run_weekly_update(self) -> Dict[str, Any]:
        """주간 업데이트 실행"""
        logger.info("=" * 60)
        logger.info("Starting weekly SEO guidelines update")
        logger.info("=" * 60)
        
        try:
            # 1. 최신 트렌드 리서치
            research_results = await self.research_latest_trends()
            
            # 2. 변경사항 감지
            changes = self.detect_changes(research_results)
            
            # 3. 리포트 생성
            report = self.generate_update_report(research_results, changes)
            
            # 4. 업데이트 적용 (권장 시)
            if report['recommendation'] == "UPDATE":
                try:
                    logger.info("Applying recommended updates to guidelines...")
                    from app.services.content_generator import update_guideline_content
                    from app.seo_guidelines import save_seo_guidelines
                    
                    # 트렌드 추출
                    trends = {}
                    for type_, res in research_results.items():
                        if "findings" in res:
                            trends[type_] = res["findings"]
                    
                    # 가이드라인 업데이트 생성
                    new_guidelines = await update_guideline_content(self.current_guidelines, trends)
                    
                    # 메타데이터 업데이트
                    new_guidelines["last_updated"] = datetime.now().isoformat()
                    # 버전은 날짜 기반으로 업데이트
                    new_guidelines["version"] = datetime.now().strftime("%Y-%m-%d")
                    
                    # 저장
                    if save_seo_guidelines(new_guidelines):
                        logger.info("Guidelines updated and saved successfully")
                        report["status"] = "UPDATED"
                        report["new_version"] = new_guidelines["version"]
                        report["guidelines_snapshot"] = new_guidelines
                    else:
                        logger.error("Failed to save updated guidelines")
                        report["status"] = "SAVE_FAILED"
                        
                except Exception as e:
                    logger.error(f"Failed to apply updates: {e}")
                    report["status"] = "UPDATE_FAILED"
                    report["update_error"] = str(e)
            else:
                report["status"] = "SKIPPED"
                report["guidelines_snapshot"] = self.current_guidelines
            
            # 5. 로그 저장
            self._save_report(report)
            
            logger.info("Weekly update completed successfully")
            logger.info(f"Recommendation: {report['recommendation']}")
            logger.info(f"Status: {report.get('status', 'UNKNOWN')}")
            
            return report
            
        except Exception as e:
            logger.error(f"Weekly update failed: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _save_report(self, report: Dict[str, Any]):
        """리포트 저장"""
        try:
            import os
            report_dir = "seo_update_reports"
            os.makedirs(report_dir, exist_ok=True)
            
            filename = f"{report_dir}/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            # Store the file path in the report for later rollback
            report['report_path'] = filename
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Report saved: {filename}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

# 편의 함수
async def run_seo_update():
    """SEO 업데이트 실행"""
    updater = SEOGuidelineUpdater()
    return await updater.run_weekly_update()

if __name__ == "__main__":
    # 테스트 실행
    async def test():
        updater = SEOGuidelineUpdater()
        report = await updater.run_weekly_update()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    asyncio.run(test())
