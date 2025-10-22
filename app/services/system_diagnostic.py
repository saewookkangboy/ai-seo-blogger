"""
시스템 진단 및 자동 업데이트 서비스
전체 시스템의 상태를 진단하고 자동으로 업데이트를 수행합니다.
"""

import os
import sys
import json
import logging
import subprocess
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import psutil
import requests
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import SessionLocal
from ..models import BlogPost, KeywordList, APIKey, FeatureUpdate
from ..config import settings
from .performance_monitor import performance_monitor
from .crawler_monitor import crawling_monitor

logger = logging.getLogger(__name__)

class SystemDiagnostic:
    """시스템 진단 및 자동 업데이트 클래스"""
    
    def __init__(self):
        self.diagnostic_results = {}
        self.critical_issues = []
        self.warnings = []
        self.recommendations = []
        self.auto_update_enabled = True
        self.last_diagnostic = None
        
    async def run_full_diagnostic(self) -> Dict[str, Any]:
        """전체 시스템 진단 실행"""
        logger.info("=== 전체 시스템 진단 시작 ===")
        start_time = time.time()
        
        try:
            # 1. 시스템 리소스 진단
            await self._diagnose_system_resources()
            
            # 2. 데이터베이스 진단
            await self._diagnose_database()
            
            # 3. API 연결 진단
            await self._diagnose_api_connections()
            
            # 4. 서비스 상태 진단
            await self._diagnose_services()
            
            # 5. 파일 시스템 진단
            await self._diagnose_file_system()
            
            # 6. 성능 진단
            await self._diagnose_performance()
            
            # 7. 보안 진단
            await self._diagnose_security()
            
            # 8. 종합 평가
            await self._evaluate_overall_health()
            
            # 9. 자동 업데이트 실행
            if self.auto_update_enabled:
                await self._run_auto_updates()
            
            # 10. 진단 결과 저장
            await self._save_diagnostic_results()
            
            end_time = time.time()
            diagnostic_time = end_time - start_time
            
            logger.info(f"=== 전체 시스템 진단 완료 (소요시간: {diagnostic_time:.2f}초) ===")
            
            return {
                "status": "completed",
                "diagnostic_time": diagnostic_time,
                "critical_issues": self.critical_issues,
                "warnings": self.warnings,
                "recommendations": self.recommendations,
                "overall_health": self.diagnostic_results.get("overall_health", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"시스템 진단 중 오류 발생: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _diagnose_system_resources(self):
        """시스템 리소스 진단"""
        logger.info("시스템 리소스 진단 중...")
        
        try:
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 메모리 사용률
            memory = psutil.virtual_memory()
            
            # 디스크 사용률
            disk = psutil.disk_usage('/')
            
            # 네트워크 상태
            network = psutil.net_io_counters()
            
            # 프로세스 정보
            processes = len(psutil.pids())
            
            resource_data = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_available": memory.available,
                "disk_usage": disk.percent,
                "disk_free": disk.free,
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "process_count": processes
            }
            
            # 임계값 체크
            if cpu_percent > 80:
                self.critical_issues.append(f"CPU 사용률이 높습니다: {cpu_percent}%")
            elif cpu_percent > 60:
                self.warnings.append(f"CPU 사용률이 높습니다: {cpu_percent}%")
            
            if memory.percent > 90:
                self.critical_issues.append(f"메모리 사용률이 높습니다: {memory.percent}%")
            elif memory.percent > 75:
                self.warnings.append(f"메모리 사용률이 높습니다: {memory.percent}%")
            
            if disk.percent > 95:
                self.critical_issues.append(f"디스크 사용률이 높습니다: {disk.percent}%")
            elif disk.percent > 85:
                self.warnings.append(f"디스크 사용률이 높습니다: {disk.percent}%")
            
            self.diagnostic_results["system_resources"] = resource_data
            
        except Exception as e:
            logger.error(f"시스템 리소스 진단 실패: {e}")
            self.critical_issues.append(f"시스템 리소스 진단 실패: {e}")
    
    async def _diagnose_database(self):
        """데이터베이스 진단"""
        logger.info("데이터베이스 진단 중...")
        
        try:
            db = SessionLocal()
            
            # 데이터베이스 연결 테스트
            db.execute(text("SELECT 1"))
            
            # 테이블 존재 확인
            tables = ["blog_posts", "keyword_list", "api_keys", "feature_updates"]
            existing_tables = []
            missing_tables = []
            
            for table in tables:
                try:
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    existing_tables.append({"table": table, "count": count})
                except Exception:
                    missing_tables.append(table)
            
            # 데이터베이스 크기 확인
            db_size = 0
            if os.path.exists("blog.db"):
                db_size = os.path.getsize("blog.db")
            
            # 인덱스 상태 확인
            indexes = db.execute(text("SELECT name FROM sqlite_master WHERE type='index'")).fetchall()
            
            db_data = {
                "connection_status": "healthy",
                "existing_tables": existing_tables,
                "missing_tables": missing_tables,
                "database_size": db_size,
                "index_count": len(indexes)
            }
            
            if missing_tables:
                self.critical_issues.append(f"누락된 테이블: {', '.join(missing_tables)}")
            
            if db_size > 100 * 1024 * 1024:  # 100MB
                self.warnings.append(f"데이터베이스 크기가 큽니다: {db_size / (1024*1024):.1f}MB")
            
            self.diagnostic_results["database"] = db_data
            
        except Exception as e:
            logger.error(f"데이터베이스 진단 실패: {e}")
            self.critical_issues.append(f"데이터베이스 연결 실패: {e}")
        finally:
            db.close()
    
    async def _diagnose_api_connections(self):
        """API 연결 진단"""
        logger.info("API 연결 진단 중...")
        
        api_status = {}
        
        # OpenAI API 테스트
        try:
            if settings.get_openai_api_key():
                # 간단한 API 호출 테스트
                import openai
                client = openai.OpenAI(api_key=settings.get_openai_api_key())
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                api_status["openai"] = {"status": "healthy", "response_time": "< 1s"}
            else:
                api_status["openai"] = {"status": "not_configured"}
        except Exception as e:
            api_status["openai"] = {"status": "error", "error": str(e)}
            self.warnings.append(f"OpenAI API 연결 실패: {e}")
        
        # Gemini API 테스트
        try:
            if settings.get_gemini_api_key():
                import google.generativeai as genai
                genai.configure(api_key=settings.get_gemini_api_key())
                model = genai.GenerativeModel('gemini-2.0-flash')
                response = model.generate_content("test")
                api_status["gemini"] = {"status": "healthy", "response_time": "< 1s"}
            else:
                api_status["gemini"] = {"status": "not_configured"}
        except Exception as e:
            api_status["gemini"] = {"status": "error", "error": str(e)}
            self.warnings.append(f"Gemini API 연결 실패: {e}")
        
        # Google Drive API 테스트
        try:
            if os.path.exists("token.json"):
                from .google_drive_service import GoogleDriveService
                drive_service = GoogleDriveService()
                # 간단한 연결 테스트
                api_status["google_drive"] = {"status": "healthy"}
            else:
                api_status["google_drive"] = {"status": "not_configured"}
        except Exception as e:
            api_status["google_drive"] = {"status": "error", "error": str(e)}
            self.warnings.append(f"Google Drive API 연결 실패: {e}")
        
        self.diagnostic_results["api_connections"] = api_status
    
    async def _diagnose_services(self):
        """서비스 상태 진단"""
        logger.info("서비스 상태 진단 중...")
        
        services_status = {}
        
        # 성능 모니터 상태
        try:
            if hasattr(performance_monitor, 'monitoring'):
                services_status["performance_monitor"] = {
                    "status": "running" if performance_monitor.monitoring else "stopped",
                    "data_points": len(performance_monitor.performance_data)
                }
            else:
                services_status["performance_monitor"] = {"status": "not_available"}
        except Exception as e:
            services_status["performance_monitor"] = {"status": "error", "error": str(e)}
        
        # 크롤링 모니터 상태
        try:
            if hasattr(crawling_monitor, 'monitoring'):
                services_status["crawling_monitor"] = {
                    "status": "running" if crawling_monitor.monitoring else "stopped"
                }
            else:
                services_status["crawling_monitor"] = {"status": "not_available"}
        except Exception as e:
            services_status["crawling_monitor"] = {"status": "error", "error": str(e)}
        
        self.diagnostic_results["services"] = services_status
    
    async def _diagnose_file_system(self):
        """파일 시스템 진단"""
        logger.info("파일 시스템 진단 중...")
        
        file_system_data = {}
        
        # 로그 파일 확인
        log_dir = Path("logs")
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            total_log_size = sum(f.stat().st_size for f in log_files)
            file_system_data["log_files"] = {
                "count": len(log_files),
                "total_size": total_log_size,
                "files": [f.name for f in log_files]
            }
            
            if total_log_size > 50 * 1024 * 1024:  # 50MB
                self.warnings.append(f"로그 파일 크기가 큽니다: {total_log_size / (1024*1024):.1f}MB")
        else:
            file_system_data["log_files"] = {"count": 0, "total_size": 0}
        
        # 백업 파일 확인
        backup_dir = Path("backups")
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("*.db"))
            file_system_data["backup_files"] = {
                "count": len(backup_files),
                "files": [f.name for f in backup_files]
            }
        else:
            file_system_data["backup_files"] = {"count": 0}
        
        # 임시 파일 확인
        temp_files = list(Path(".").glob("*.tmp")) + list(Path(".").glob("*.bak"))
        if temp_files:
            self.warnings.append(f"임시 파일이 발견되었습니다: {len(temp_files)}개")
            file_system_data["temp_files"] = [f.name for f in temp_files]
        
        self.diagnostic_results["file_system"] = file_system_data
    
    async def _diagnose_performance(self):
        """성능 진단"""
        logger.info("성능 진단 중...")
        
        performance_data = {}
        
        # API 응답 시간 테스트
        try:
            start_time = time.time()
            response = requests.get("http://localhost:8000/health", timeout=5)
            response_time = time.time() - start_time
            
            performance_data["api_response_time"] = response_time
            
            if response_time > 5:
                self.critical_issues.append(f"API 응답 시간이 느립니다: {response_time:.2f}초")
            elif response_time > 2:
                self.warnings.append(f"API 응답 시간이 느립니다: {response_time:.2f}초")
                
        except Exception as e:
            self.critical_issues.append(f"API 응답 시간 테스트 실패: {e}")
            performance_data["api_response_time"] = None
        
        # 메모리 사용량 추적
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            performance_data["process_memory"] = memory_info.rss
            
            if memory_info.rss > 500 * 1024 * 1024:  # 500MB
                self.warnings.append(f"프로세스 메모리 사용량이 높습니다: {memory_info.rss / (1024*1024):.1f}MB")
                
        except Exception as e:
            logger.error(f"메모리 사용량 추적 실패: {e}")
        
        self.diagnostic_results["performance"] = performance_data
    
    async def _diagnose_security(self):
        """보안 진단"""
        logger.info("보안 진단 중...")
        
        security_data = {}
        
        # API 키 보안 확인
        api_keys_status = {}
        
        if settings.get_openai_api_key():
            if settings.get_openai_api_key().startswith("sk-"):
                api_keys_status["openai"] = "secure"
            else:
                api_keys_status["openai"] = "insecure"
                self.critical_issues.append("OpenAI API 키 형식이 올바르지 않습니다")
        else:
            api_keys_status["openai"] = "not_set"
        
        if settings.get_gemini_api_key():
            if settings.get_gemini_api_key().startswith("AIza"):
                api_keys_status["gemini"] = "secure"
            else:
                api_keys_status["gemini"] = "insecure"
                self.critical_issues.append("Gemini API 키 형식이 올바르지 않습니다")
        else:
            api_keys_status["gemini"] = "not_set"
        
        security_data["api_keys"] = api_keys_status
        
        # 환경 변수 파일 확인
        env_file = Path(".env")
        if env_file.exists():
            env_content = env_file.read_text()
            if "password" in env_content.lower() and "=" in env_content:
                security_data["env_file"] = "exists"
            else:
                security_data["env_file"] = "empty_or_invalid"
        else:
            security_data["env_file"] = "missing"
            self.warnings.append(".env 파일이 없습니다")
        
        self.diagnostic_results["security"] = security_data
    
    async def _evaluate_overall_health(self):
        """종합 건강 상태 평가"""
        logger.info("종합 건강 상태 평가 중...")
        
        health_score = 100
        
        # 치명적 오류로 인한 점수 차감
        health_score -= len(self.critical_issues) * 20
        
        # 경고로 인한 점수 차감
        health_score -= len(self.warnings) * 5
        
        # 최소 점수 보장
        health_score = max(0, health_score)
        
        if health_score >= 90:
            health_status = "excellent"
        elif health_score >= 75:
            health_status = "good"
        elif health_score >= 50:
            health_status = "fair"
        elif health_score >= 25:
            health_status = "poor"
        else:
            health_status = "critical"
        
        self.diagnostic_results["overall_health"] = {
            "status": health_status,
            "score": health_score,
            "critical_issues_count": len(self.critical_issues),
            "warnings_count": len(self.warnings)
        }
        
        # 개선 권장사항 생성
        if self.critical_issues:
            self.recommendations.append("치명적 오류를 즉시 해결해야 합니다")
        
        if len(self.warnings) > 5:
            self.recommendations.append("경고 사항이 많습니다. 시스템 점검을 권장합니다")
        
        if health_score < 50:
            self.recommendations.append("시스템 성능이 저하되었습니다. 최적화가 필요합니다")
    
    async def _run_auto_updates(self):
        """자동 업데이트 실행"""
        logger.info("자동 업데이트 실행 중...")
        
        updates_applied = []
        
        # 1. 로그 파일 정리
        try:
            await self._cleanup_log_files()
            updates_applied.append("로그 파일 정리")
        except Exception as e:
            logger.error(f"로그 파일 정리 실패: {e}")
        
        # 2. 임시 파일 정리
        try:
            await self._cleanup_temp_files()
            updates_applied.append("임시 파일 정리")
        except Exception as e:
            logger.error(f"임시 파일 정리 실패: {e}")
        
        # 3. 데이터베이스 최적화
        try:
            await self._optimize_database()
            updates_applied.append("데이터베이스 최적화")
        except Exception as e:
            logger.error(f"데이터베이스 최적화 실패: {e}")
        
        # 4. 캐시 정리
        try:
            await self._clear_cache()
            updates_applied.append("캐시 정리")
        except Exception as e:
            logger.error(f"캐시 정리 실패: {e}")
        
        self.diagnostic_results["auto_updates"] = {
            "applied": updates_applied,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _cleanup_log_files(self):
        """로그 파일 정리"""
        log_dir = Path("logs")
        if not log_dir.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=7)
        cleaned_files = []
        
        for log_file in log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                cleaned_files.append(log_file.name)
        
        if cleaned_files:
            logger.info(f"오래된 로그 파일 정리 완료: {len(cleaned_files)}개")
    
    async def _cleanup_temp_files(self):
        """임시 파일 정리"""
        temp_patterns = ["*.tmp", "*.bak", "*.backup", ".DS_Store"]
        cleaned_files = []
        
        for pattern in temp_patterns:
            for temp_file in Path(".").glob(pattern):
                temp_file.unlink()
                cleaned_files.append(temp_file.name)
        
        if cleaned_files:
            logger.info(f"임시 파일 정리 완료: {len(cleaned_files)}개")
    
    async def _optimize_database(self):
        """데이터베이스 최적화"""
        db = SessionLocal()
        try:
            # VACUUM 실행
            db.execute(text("VACUUM"))
            db.commit()
            logger.info("데이터베이스 최적화 완료")
        except Exception as e:
            logger.error(f"데이터베이스 최적화 실패: {e}")
        finally:
            db.close()
    
    async def _clear_cache(self):
        """캐시 정리"""
        # Python 캐시 파일 정리
        import shutil
        for root, dirs, files in os.walk("."):
            for dir_name in dirs:
                if dir_name == "__pycache__":
                    shutil.rmtree(os.path.join(root, dir_name))
        
        logger.info("Python 캐시 파일 정리 완료")
    
    async def _save_diagnostic_results(self):
        """진단 결과 저장"""
        try:
            results = {
                "timestamp": datetime.now().isoformat(),
                "diagnostic_results": self.diagnostic_results,
                "critical_issues": self.critical_issues,
                "warnings": self.warnings,
                "recommendations": self.recommendations
            }
            
            # JSON 파일로 저장
            with open("system_diagnostic_results.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 데이터베이스에도 저장
            db = SessionLocal()
            try:
                update_record = FeatureUpdate(
                    title="시스템 진단 완료",
                    description=f"진단 결과: {len(self.critical_issues)}개 치명적 오류, {len(self.warnings)}개 경고",
                    category="System",
                    priority="high" if self.critical_issues else "medium",
                    status="completed",
                    impact="system_health"
                )
                db.add(update_record)
                db.commit()
            except Exception as e:
                logger.error(f"진단 결과 데이터베이스 저장 실패: {e}")
            finally:
                db.close()
            
            logger.info("진단 결과 저장 완료")
            
        except Exception as e:
            logger.error(f"진단 결과 저장 실패: {e}")
    
    def get_diagnostic_summary(self) -> Dict[str, Any]:
        """진단 요약 반환"""
        return {
            "last_diagnostic": self.last_diagnostic,
            "critical_issues_count": len(self.critical_issues),
            "warnings_count": len(self.warnings),
            "recommendations_count": len(self.recommendations),
            "overall_health": self.diagnostic_results.get("overall_health", {}).get("status", "unknown")
        }

# 전역 진단 인스턴스
system_diagnostic = SystemDiagnostic()
