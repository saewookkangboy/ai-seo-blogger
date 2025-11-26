"""
Task Scheduler for AI SEO Blogger
Handles scheduled tasks including weekly SEO guidelines updates
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import asyncio
import json

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Create scheduler instance
scheduler = AsyncIOScheduler()

async def weekly_seo_update_task():
    """주간 SEO 가이드라인 업데이트 작업"""
    try:
        logger.info("=" * 60)
        logger.info("Starting scheduled SEO guidelines update")
        logger.info(f"Time: {datetime.now().isoformat()}")
        logger.info("=" * 60)
        
        from app.seo_updater import run_seo_update
        
        # SEO 업데이트 실행
        report = await run_seo_update()
        
        # 결과 로깅
        if "error" in report:
            logger.error(f"SEO update failed: {report['error']}")
        else:
            logger.info(f"SEO update completed: {report.get('recommendation', 'N/A')}")
            logger.info(f"New trends found: {report.get('changes_detected', {}).get('new_trends', 0)}")
            
            # DB에 이력 저장
            try:
                from app.database import SessionLocal
                from app.models import SEOGuidelineHistory
                
                db = SessionLocal()
                try:
                    history = SEOGuidelineHistory(
                        version=report.get("new_version", report.get("current_version", "unknown")),
                        changes_summary=json.dumps(report.get("changes_detected", {}), ensure_ascii=False),
                        report_path=report.get("report_path", "")
                    )
                    db.add(history)
                    db.commit()
                    logger.info("Update history saved to database")
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Failed to save history to DB: {e}")
        
        return report
        
    except Exception as e:
        logger.error(f"Scheduled SEO update failed: {e}")
        return {"error": str(e)}

def setup_scheduler():
    """스케줄러 설정"""
    try:
        # 매주 월요일 오전 2시에 실행
        scheduler.add_job(
            weekly_seo_update_task,
            trigger=CronTrigger(day_of_week='mon', hour=2, minute=0),
            id='weekly_seo_update',
            name='Weekly SEO Guidelines Update',
            replace_existing=True
        )
        
        logger.info("Scheduler configured: Weekly SEO update on Mondays at 02:00")
        
        # 테스트용: 매일 오전 3시에도 실행 (선택사항, 주석 처리)
        # scheduler.add_job(
        #     weekly_seo_update_task,
        #     trigger=CronTrigger(hour=3, minute=0),
        #     id='daily_seo_update_test',
        #     name='Daily SEO Update (Test)',
        #     replace_existing=True
        # )
        
    except Exception as e:
        logger.error(f"Failed to setup scheduler: {e}")

def start_scheduler():
    """스케줄러 시작"""
    try:
        if not scheduler.running:
            scheduler.start()
            logger.info("Scheduler started successfully")
        else:
            logger.info("Scheduler already running")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

def stop_scheduler():
    """스케줄러 중지"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler stopped")
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")

def get_next_run_time():
    """다음 실행 시간 조회"""
    try:
        job = scheduler.get_job('weekly_seo_update')
        if job:
            return job.next_run_time
        return None
    except Exception as e:
        logger.error(f"Failed to get next run time: {e}")
        return None

# 스케줄러 초기화
setup_scheduler()
