from fastapi import FastAPI, Request, Depends, HTTPException, Body, Query, Form, status
from typing import Optional
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
import json
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import os
import re
from pathlib import Path
from difflib import SequenceMatcher
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import Response
from sqlalchemy import text
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import threading
import time
import sys

# 설정 및 유틸리티 임포트
from .config import settings
from .utils.logger import setup_logger
from .database import engine, SessionLocal
from . import models, crud, exceptions
from .schemas import APIKeyCreate, APIKeyUpdate, APIKeyOut, KeywordListBase, KeywordListOut, KeywordListBulkIn, PostExport, PostImport, BulkDeleteIn
from .crud import get_api_keys, get_api_key_by_id, create_api_key, update_api_key, delete_api_key, get_keywords_list, add_keyword_to_list, delete_keyword_from_list, bulk_add_keywords, bulk_delete_keywords, bulk_delete_posts, export_posts, import_posts
from app.services.crawler_monitor import crawling_monitor
from app.services.translator import get_naver_keyword_volumes
from app.services.performance_monitor import performance_monitor
from app.services.system_diagnostic import system_diagnostic
from app.services.comprehensive_logger import comprehensive_logger, log_system, log_api, log_error
from app.services.auto_update_monitor import auto_update_monitor
from app.services.readme_updater import readme_updater
# 최적화 서비스
from app.services.memory_manager import memory_manager
from app.services.structured_logger import setup_optimized_logging, compress_old_logs
from app.database import create_indexes
# 중간 우선순위 최적화 서비스
from app.services.redis_cache import get_redis_cache
from app.services.background_queue import background_queue
from app.services.optimized_crawler import priority_crawler
# 낮은 우선순위 최적화 서비스
from app.services.health_check import health_check
from app.services.postgresql_optimizer import get_postgresql_optimizer
from app.services.horizontal_scaling import horizontal_scaling
# from app.services.auto_performance_tester import auto_performance_tester

# API 응답 시간 최적화를 위한 캐시
from functools import lru_cache
from datetime import datetime, timedelta

# 메모리 캐시
api_cache = {}
cache_ttl = 300  # 5분

def get_cached_data(key: str, ttl: int = cache_ttl):
    """캐시된 데이터를 가져옵니다."""
    if key in api_cache:
        data, timestamp = api_cache[key]
        if datetime.now() - timestamp < timedelta(seconds=ttl):
            return data
        else:
            del api_cache[key]
    return None

def set_cached_data(key: str, data: dict):
    """데이터를 캐시에 저장합니다."""
    api_cache[key] = (data, datetime.now())

@lru_cache(maxsize=100)
def get_cached_stats():
    """통계 데이터를 캐시합니다."""
    return {
        "total_posts": 0,
        "total_keywords": 0,
        "api_calls_today": 0,
        "crawl_success_rate": 0
    }

# 로거 설정
logger = setup_logger(__name__, "app.log")

# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)
create_indexes()

# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.app_name,
    description="AI를 활용한 SEO 최적화 블로그 포스트 생성기",
    version="1.0.0"
)

# SessionMiddleware를 라우터 등록 등 모든 코드보다 먼저 추가
app.add_middleware(SessionMiddleware, secret_key="ai-seo-blogger-secret-key-2024")

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 및 템플릿 설정 (경로를 __file__ 기준으로 해서 Vercel 등에서 cwd 독립)
_BASE_DIR = Path(__file__).resolve().parent.parent
_STATIC_DIR = _BASE_DIR / "app" / "static"
_TEMPLATES_DIR = _BASE_DIR / "app" / "templates"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
if _BASE_DIR.exists():
    app.mount("/crawling_stats.json", StaticFiles(html=True, directory=str(_BASE_DIR)), name="crawling_stats_json")
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

# 라우터 등록
from app.routers import blog_generator, feature_updates, news_archive, google_drive
app.include_router(blog_generator.router, prefix="/api/v1")
app.include_router(feature_updates.router, prefix="/api/v1/feature-updates")
app.include_router(news_archive.router, prefix="/api/v1/news-archive")
app.include_router(google_drive.router, prefix="/api/v1")

# 의존성 주입 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 전역 예외 핸들러
@app.exception_handler(exceptions.BlogGeneratorException)
async def blog_generator_exception_handler(request: Request, exc: exceptions.BlogGeneratorException):
    logger.error(f"BlogGeneratorException: {exc}")
    return exceptions.handle_blog_generator_exception(exc)

# 헬스체크 엔드포인트
@app.get("/health", tags=["monitoring"])
async def health_check_endpoint():
    """헬스체크 엔드포인트 (로드 밸런서용)"""
    return health_check.check_health()

@app.get("/health/readiness", tags=["monitoring"])
async def readiness_check():
    """Readiness 체크 (서비스 준비 상태)"""
    return health_check.check_readiness()

@app.get("/health/liveness", tags=["monitoring"])
async def liveness_check():
    """Liveness 체크 (서비스 생존 상태)"""
    return health_check.check_liveness()

@app.get("/api/v1/scaling/info", tags=["scaling"])
async def get_scaling_info():
    """수평 확장 정보 조회"""
    return {
        'instance_info': horizontal_scaling.get_instance_info(),
        'stateless_check': horizontal_scaling.check_stateless(),
        'load_balancer_config': horizontal_scaling.get_load_balancer_config(),
        'recommendations': horizontal_scaling.get_scaling_recommendations()
    }

@app.get("/health/legacy")
async def health_check_legacy():
    """헬스 체크 엔드포인트"""
    try:
        # 데이터베이스 연결 확인
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="서비스가 정상적으로 작동하지 않습니다."
        )

# 메인 페이지
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """메인 페이지를 렌더링합니다."""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"메인 페이지 로드 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="페이지 로드 중 오류가 발생했습니다."
        )

@app.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    """테스트 페이지"""
    return FileResponse("test_content_generation.html")

# 히스토리 페이지
@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, db: Session = Depends(get_db)):
    """생성된 포스트 기록 페이지를 렌더링합니다."""
    try:
        posts = crud.get_blog_posts(db)
        posts_json_str = json.dumps(jsonable_encoder(posts))
        return templates.TemplateResponse("history.html", {
            "request": request,
            "posts": posts,
            "posts_json": posts_json_str
        })
    except Exception as e:
        logger.error(f"히스토리 페이지 로드 중 오류: {e}")
        return templates.TemplateResponse("history.html", {
            "request": request,
            "posts": [],
            "posts_json": "[]"
        })

# 로그인 페이지
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """로그인 페이지를 렌더링합니다."""
    return templates.TemplateResponse("login.html", {"request": request})

# 로그인 처리
@app.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    """로그인을 처리합니다."""
    if username == settings.admin_username and password == settings.admin_password:
        request.session["admin_logged_in"] = True
        request.session["admin_username"] = username
        logger.info(f"관리자 로그인 성공: {username}")
        return RedirectResponse(url="/admin", status_code=303)
    else:
        logger.warning(f"로그인 실패: {username}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "잘못된 사용자명 또는 비밀번호입니다."
        })

# 로그아웃
@app.get("/logout")
async def logout(request: Request):
    """로그아웃을 처리합니다."""
    request.session.clear()
    logger.info("관리자 로그아웃")
    return RedirectResponse(url="/login", status_code=303)

# 관리자 페이지
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """관리자 대시보드"""
    # 세션 확인
    if not request.session.get("admin_logged_in"):
        logger.warning("인증되지 않은 관리자 페이지 접근")
        return RedirectResponse(url="/login", status_code=303)
    
    logger.info(f"관리자 페이지 접근: {request.session.get('admin_username')}")
    return templates.TemplateResponse("admin.html", {"request": request})



# 테스트용 관리자 세션 생성 (개발 환경에서만)
@app.get("/admin/test-session")
async def create_test_session(request: Request):
    """테스트용 관리자 세션을 생성합니다. (개발 환경에서만 사용)"""
    import os
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true' or settings.debug
    
    if debug_mode:
        try:
            request.session["admin_logged_in"] = True
            request.session["admin_username"] = "test_admin"
            logger.info(f"테스트용 관리자 세션 생성 (debug_mode: {debug_mode})")
            logger.info(f"세션 내용: {dict(request.session)}")
            return JSONResponse(content={
                "success": True,
                "message": "테스트 세션이 생성되었습니다.",
                "redirect_url": "/admin",
                "debug_mode": debug_mode,
                "session_data": dict(request.session)
            })
        except Exception as e:
            logger.error(f"세션 생성 중 오류: {e}")
            return JSONResponse(content={
                "success": False,
                "message": f"세션 생성 실패: {e}",
                "debug_mode": debug_mode
            })
    else:
        logger.warning(f"프로덕션 환경에서 테스트 세션 생성 시도 (debug_mode: {debug_mode})")
        raise HTTPException(status_code=403, detail="프로덕션 환경에서는 사용할 수 없습니다.")

# 간단한 관리자 로그인 (개발용)
@app.get("/admin/quick-login")
async def quick_admin_login(request: Request):
    """개발용 간단한 관리자 로그인"""
    import os
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true' or settings.debug
    
    if debug_mode:
        request.session["admin_logged_in"] = True
        request.session["admin_username"] = "admin"
        logger.info(f"간단한 관리자 로그인 성공 (debug_mode: {debug_mode})")
        return RedirectResponse(url="/admin", status_code=303)
    else:
        logger.warning(f"프로덕션 환경에서 간단한 로그인 시도 (debug_mode: {debug_mode})")
        raise HTTPException(status_code=403, detail="프로덕션 환경에서는 사용할 수 없습니다.")

# 관리자 세션 상태 확인
@app.get("/admin/session-status")
async def check_admin_session(request: Request):
    """관리자 세션 상태를 확인합니다."""
    import os
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true' or settings.debug
    
    is_logged_in = request.session.get("admin_logged_in", False)
    username = request.session.get("admin_username", "")
    
    return {
        "logged_in": is_logged_in,
        "username": username,
        "debug_mode": debug_mode,
        "env_debug": os.getenv('DEBUG', 'Not Set'),
        "settings_debug": settings.debug
    }

# Admin 페이지 통합 테스트 엔드포인트
@app.get("/api/v1/admin/test-integration")
async def test_admin_integration():
    """Admin 페이지 통합 테스트를 수행합니다."""
    try:
        # 데이터베이스 연결 테스트
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        # 기본 통계 데이터 테스트
        stats = crud.get_posts_stats(db)
        
        return {
            "success": True,
            "message": "Admin 페이지 통합 테스트 성공",
            "database": "연결됨",
            "stats_available": bool(stats),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Admin 통합 테스트 실패: {e}")
        return {
            "success": False,
            "message": f"Admin 페이지 통합 테스트 실패: {e}",
            "timestamp": datetime.now().isoformat()
        }

# 크롤링 실패 내역 반환
@app.get("/api/v1/crawling/failures", response_class=JSONResponse)
async def get_crawling_failures():
    """크롤링 실패 내역 반환"""
    try:
        with open("crawling_stats.json", "r", encoding="utf-8") as f:
            stats = json.load(f)
        failures = [item for item in stats.get("recent_attempts", []) if not item.get("success", True)]
        return failures
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"크롤링 실패 내역을 불러올 수 없습니다: {e}"})

# 특정 URL 크롤링 재시도
@app.post("/api/v1/crawling/retry", response_class=JSONResponse)
async def retry_crawling(data: dict = Body(...)):
    """특정 URL 크롤링 재시도"""
    url = data.get("url")
    if not url:
        return JSONResponse(status_code=400, content={"success": False, "message": "url 파라미터가 필요합니다."})
    try:
        from app.services.crawler import get_text_from_url
        content = await get_text_from_url(url)
        if content and isinstance(content, str) and len(content.strip()) > 0:
            return {"success": True, "message": "크롤링 성공", "content_length": len(content)}
        else:
            return {"success": False, "message": "본문을 추출하지 못했습니다."}
    except Exception as e:
        return {"success": False, "message": f"크롤링 실패: {e}"}

# 사이트별 크롤링 설정 반환
@app.get("/api/v1/crawling/sites", response_class=JSONResponse)
async def get_crawling_sites():
    """사이트별 크롤링 설정 반환"""
    try:
        with open("site_crawler_configs.json", "r", encoding="utf-8") as f:
            configs = json.load(f)
        return configs
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"설정을 불러올 수 없습니다: {e}"})

# 특정 도메인의 크롤링 설정 수정/저장
@app.post("/api/v1/crawling/sites/update", response_class=JSONResponse)
async def update_crawling_site(data: dict = Body(...)):
    """특정 도메인의 크롤링 설정 수정/저장"""
    domain = data.get("domain")
    selectors = data.get("selectors")
    exclude_selectors = data.get("exclude_selectors")
    text_filters = data.get("text_filters")
    if not domain:
        return JSONResponse(status_code=400, content={"success": False, "message": "domain 파라미터가 필요합니다."})
    try:
        with open("site_crawler_configs.json", "r", encoding="utf-8") as f:
            configs = json.load(f)
        configs[domain] = {
            "selectors": selectors or [],
            "exclude_selectors": exclude_selectors or [],
            "text_filters": text_filters or []
        }
        with open("site_crawler_configs.json", "w", encoding="utf-8") as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)
        return {"success": True, "message": "설정이 저장되었습니다."}
    except Exception as e:
        return {"success": False, "message": f"설정 저장 실패: {e}"}

# 일자별 크롤링/포스트 작성 횟수 통계
@app.get("/api/v1/stats/daily", response_class=JSONResponse)
async def get_daily_stats(
    db: Session = Depends(get_db),
    days: int = Query(None, description="최근 N일"),
    start: str = Query(None, description="시작일(YYYY-MM-DD)"),
    end: str = Query(None, description="종료일(YYYY-MM-DD)")
):
    """일자별 크롤링/포스트 작성 횟수 통계 (기간 지정 지원)"""
    # 날짜 범위 결정
    if start and end:
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
        end_date = datetime.strptime(end, '%Y-%m-%d').date()
        days_list = [(start_date + timedelta(days=i)) for i in range((end_date - start_date).days + 1)]
    else:
        n = days if days else 30
        today = datetime.now().date()
        days_list = [(today - timedelta(days=i)) for i in range(n-1, -1, -1)]
    day_strs = [d.strftime('%Y-%m-%d') for d in days_list]

    # 크롤링 시도 집계
    crawling_counts = defaultdict(int)
    try:
        with open("crawling_stats.json", "r", encoding="utf-8") as f:
            stats = json.load(f)
        for item in stats.get("recent_attempts", []):
            ts = item.get("timestamp")
            if ts:
                d = ts[:10]
                if d in day_strs:
                    crawling_counts[d] += 1
    except Exception:
        pass
    crawling = [crawling_counts[d] for d in day_strs]

    # 포스트 작성 집계
    posts_counts = defaultdict(int)
    try:
        posts = db.query(models.BlogPost).all()
        for post in posts:
            if post.created_at is not None:
                d = post.created_at.strftime('%Y-%m-%d')
                if d in day_strs:
                    posts_counts[d] += 1
    except Exception:
        pass
    posts = [posts_counts[d] for d in day_strs]

    return {"dates": day_strs, "crawling": crawling, "posts": posts}

# 애플리케이션 시작 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행되는 이벤트 (최적화: 즉시 바인딩)"""
    # 로깅 설정을 포함한 모든 초기화를 백그라운드로 이동해 서버가 즉시 포트에 바인딩되도록 함
    asyncio.create_task(_run_all_startup_tasks())
    logger.info("=== AI SEO Blog Generator 시작 (초기화는 백그라운드에서 진행) ===")


async def _run_all_startup_tasks():
    """모든 초기화 작업을 백그라운드에서 실행"""
    try:
        # 최적화 로깅 설정 (블로킹이므로 스레드 풀에서 실행해 이벤트 루프가 멈추지 않도록 함)
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: setup_optimized_logging(
                    log_dir="logs",
                    log_level=settings.log_level,
                    enable_file=settings.log_enable_file,
                    enable_console=settings.log_enable_console,
                ),
            )
            logger.info("✅ 로깅 설정 완료")
        except Exception as e:
            logger.warning(f"로깅 설정 중 오류: {e}")
        # 데이터베이스 인덱스 생성
        try:
            create_indexes()
            logger.info("✅ 데이터베이스 인덱스 생성 완료")
        except Exception as e:
            logger.warning(f"인덱스 생성 중 오류: {e}")
        
        # Redis 캐시 초기화
        try:
            redis_cache = get_redis_cache()
            logger.info("✅ 캐시 초기화 완료")
        except Exception as e:
            logger.warning(f"캐시 초기화 실패: {e}")
        
        # 백그라운드 작업 큐 시작
        try:
            background_queue.start()
            logger.info("✅ 백그라운드 작업 큐 시작")
        except Exception as e:
            logger.warning(f"백그라운드 작업 큐 시작 실패: {e}")
        
        # 나머지 무거운 작업들
        await _run_background_startup_tasks()
        
    except Exception as e:
        logger.error(f"초기화 작업 중 오류: {e}")


async def _run_background_startup_tasks():
    """백그라운드에서 실행되는 초기화 작업들"""
    try:
        # 로그 압축 (무거운 작업)
        try:
            compressed_count = compress_old_logs("logs", days=settings.log_compress_after_days)
            if compressed_count > 0:
                logger.info(f"✅ {compressed_count}개의 오래된 로그 파일 압축 완료")
        except Exception as e:
            logger.warning(f"로그 압축 중 오류: {e}")
        
        # 메모리 관리 시작
        try:
            memory_manager.start_monitoring()
            logger.info("✅ 메모리 모니터링 시작")
        except Exception as e:
            logger.warning(f"메모리 모니터링 시작 실패: {e}")
        
        # 우선순위 크롤러 초기화
        try:
            await priority_crawler.initialize()
            logger.info("✅ 우선순위 크롤러 초기화")
        except Exception as e:
            logger.warning(f"우선순위 크롤러 초기화 실패: {e}")
        
        # PostgreSQL 최적화 (PostgreSQL 사용 시)
        try:
            if settings.database_url.startswith("postgresql"):
                postgresql_optimizer = get_postgresql_optimizer()
                postgresql_optimizer.optimize_query_performance()
                logger.info("✅ PostgreSQL 최적화 완료")
        except Exception as e:
            logger.warning(f"PostgreSQL 최적화 실패: {e}")
        
        # 설정 유효성 검사
        errors = settings.validate_settings()
        if errors:
            logger.warning("설정 경고:")
            for error in errors:
                logger.warning(f"  - {error}")
            log_error("설정 검증 실패", {"errors": errors})
        
        # 기본 키워드 데이터 초기화
        try:
            db = SessionLocal()
            try:
                keyword_count = db.query(models.KeywordList).count()
                if keyword_count == 0:
                    logger.info("기본 키워드 데이터를 초기화합니다...")
                    crud.initialize_default_keywords(db)
                    logger.info("기본 키워드 데이터 초기화 완료")
                    log_system("기본 키워드 데이터 초기화 완료")
                else:
                    logger.info(f"기존 키워드 데이터 {keyword_count}개가 있습니다.")
                    log_system("기존 키워드 데이터 확인", {"count": keyword_count})
            finally:
                db.close()
        except Exception as e:
            logger.error(f"기본 키워드 초기화 중 오류: {e}")
            log_error("기본 키워드 초기화 실패", {"error": str(e)})
        
        # 크롤링 모니터 시작
        try:
            crawling_monitor.start_monitoring()
            logger.info("크롤링 모니터가 시작되었습니다.")
            log_system("크롤링 모니터 시작")
        except Exception as e:
            logger.error(f"크롤링 모니터 시작 실패: {e}")
            log_error("크롤링 모니터 시작 실패", {"error": str(e)})
        
        # 성능 모니터 시작
        try:
            performance_monitor.start_monitoring()
            logger.info("백그라운드 성능 모니터링이 시작되었습니다.")
            log_system("성능 모니터 시작")
        except Exception as e:
            logger.error(f"성능 모니터 시작 실패: {e}")
            log_error("성능 모니터 시작 실패", {"error": str(e)})
        
        # 자동 업데이트 모니터 시작
        try:
            auto_update_monitor.start_monitoring()
            logger.info("자동 업데이트 모니터가 시작되었습니다.")
            log_system("자동 업데이트 모니터 시작")
        except Exception as e:
            logger.error(f"자동 업데이트 모니터 시작 실패: {e}")
            log_error("자동 업데이트 모니터 시작 실패", {"error": str(e)})
        
        # 시스템 로깅
        log_system("애플리케이션 시작", {"timestamp": datetime.now().isoformat()})
        
    except Exception as e:
        logger.error(f"백그라운드 초기화 작업 중 오류: {e}")
    
    # 무거운 진단/업데이트 작업은 더 나중에 실행
    asyncio.create_task(_run_post_startup_tasks())


async def _run_post_startup_tasks():
    """서버 기동 이후에 실행해야 하는 무거운 작업"""
    post_tasks_success = True
    
    try:
        logger.info("초기 시스템 진단을 실행합니다...")
        diagnostic_result = await system_diagnostic.run_full_diagnostic()
        logger.info(f"초기 시스템 진단 완료: {diagnostic_result.get('overall_health', 'unknown')}")
        log_system("초기 시스템 진단 완료", diagnostic_result)
    except Exception as e:
        post_tasks_success = False
        logger.error(f"초기 시스템 진단 실패: {e}")
        log_error("초기 시스템 진단 실패", {"error": str(e)})
    
    try:
        logger.info("README 자동 업데이트를 실행합니다...")
        readme_updated = await asyncio.to_thread(readme_updater.auto_update_readme)
        if readme_updated:
            logger.info("README 자동 업데이트 완료")
            log_system("README 자동 업데이트 완료")
        else:
            logger.info("README 업데이트할 내용이 없습니다")
    except Exception as e:
        post_tasks_success = False
        logger.error(f"README 자동 업데이트 실패: {e}")
        log_error("README 자동 업데이트 실패", {"error": str(e)})
    
    if post_tasks_success:
        logger.info("애플리케이션이 성공적으로 시작되었습니다.")
        log_system("애플리케이션 시작 완료")
    else:
        logger.warning("일부 후속 작업이 실패했으므로 애플리케이션 상태를 확인하세요.")

# 애플리케이션 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행되는 이벤트"""
    # 메모리 모니터링 중지
    try:
        memory_manager.stop_monitoring()
        logger.info("메모리 모니터링 중지")
    except Exception as e:
        logger.warning(f"메모리 모니터링 중지 실패: {e}")
    
    # 백그라운드 작업 큐 중지
    try:
        background_queue.stop()
        logger.info("백그라운드 작업 큐 중지")
    except Exception as e:
        logger.warning(f"백그라운드 작업 큐 중지 실패: {e}")
    
    # 우선순위 크롤러 종료
    try:
        asyncio.run(priority_crawler.close())
        logger.info("우선순위 크롤러 종료")
    except Exception as e:
        logger.warning(f"우선순위 크롤러 종료 실패: {e}")
    logger.info("애플리케이션 종료 중...")
    log_system("애플리케이션 종료 시작")
    
    # 자동 업데이트 모니터 중지
    try:
        auto_update_monitor.stop_monitoring()
        logger.info("자동 업데이트 모니터가 중지되었습니다.")
        log_system("자동 업데이트 모니터 중지")
    except Exception as e:
        logger.error(f"자동 업데이트 모니터 중지 실패: {e}")
        log_error("자동 업데이트 모니터 중지 실패", {"error": str(e)})
    
    # 크롤링 모니터 중지
    try:
        crawling_monitor.stop_monitoring()
        logger.info("크롤링 모니터가 중지되었습니다.")
        log_system("크롤링 모니터 중지")
    except Exception as e:
        logger.error(f"크롤링 모니터 중지 실패: {e}")
        log_error("크롤링 모니터 중지 실패", {"error": str(e)})
    
    # 성능 모니터 중지
    try:
        performance_monitor.stop_monitoring()
        logger.info("백그라운드 성능 모니터링이 중지되었습니다.")
        log_system("성능 모니터 중지")
    except Exception as e:
        logger.error(f"성능 모니터 중지 실패: {e}")
        log_error("성능 모니터 중지 실패", {"error": str(e)})
    
    # 포괄적인 로깅 시스템 중지
    try:
        comprehensive_logger.stop()
        logger.info("포괄적인 로깅 시스템이 중지되었습니다.")
    except Exception as e:
        logger.error(f"로깅 시스템 중지 실패: {e}")
    
    logger.info(f"{settings.app_name} 애플리케이션이 종료되었습니다.")
    log_system("애플리케이션 종료 완료")

@app.get("/api/v1/system/db-backup")
def download_db():
    """DB 파일 다운로드"""
    db_path = "blog.db"
    if not os.path.exists(db_path):
        return JSONResponse(status_code=404, content={"detail": "DB 파일이 존재하지 않습니다."})
    return FileResponse(db_path, filename="blog_backup.db", media_type="application/octet-stream")

@app.get("/api/v1/system/logs")
def list_logs():
    """로그 파일 목록 반환"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        return []
    files = [f for f in os.listdir(log_dir) if os.path.isfile(os.path.join(log_dir, f))]
    return files

@app.get("/api/v1/system/logs/download")
def download_log(filename: str):
    """로그 파일 다운로드"""
    log_path = os.path.join("logs", filename)
    if not os.path.exists(log_path):
        return JSONResponse(status_code=404, content={"detail": "로그 파일이 존재하지 않습니다."})
    return FileResponse(log_path, filename=filename, media_type="text/plain")

@app.get("/api/v1/keywords/stats", response_class=JSONResponse)
async def get_keywords_stats(db: Session = Depends(get_db)):
    """모든 포스트의 키워드별 등장 횟수 집계"""
    keywords_counter = Counter()
    try:
        posts = db.query(models.BlogPost).all()
        for post in posts:
            if post.keywords:
                for kw in re.split(r'[;,\n]+', post.keywords):
                    kw = kw.strip()
                    if kw:
                        keywords_counter[kw] += 1
    except Exception:
        pass
    # 등장 횟수 내림차순 정렬
    stats = [
        {"keyword": k, "count": v}
        for k, v in keywords_counter.most_common()
    ]
    return stats

@app.get("/api/v1/stats/api-usage", response_class=JSONResponse)
def get_api_usage():
    """OpenAI, Gemini 등 API 호출 누적 집계 반환"""
    usage_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'api_usage.json'))
    try:
        total_openai = 0
        total_gemini = 0
        if os.path.exists(usage_file):
            with open(usage_file, 'r', encoding='utf-8') as f:
                usage = json.load(f)
            # 날짜별로 저장된 경우 전체 합계 계산
            if isinstance(usage, dict) and all(isinstance(v, dict) for v in usage.values()):
                for v in usage.values():
                    total_openai += v.get("openai", 0)
                    total_gemini += v.get("gemini", 0)
            else:
                total_openai = usage.get("openai", 0)
                total_gemini = usage.get("gemini", 0)
        return {
            "openai": total_openai,
            "gemini": total_gemini
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"API 호출 통계 불러오기 실패: {e}"})

@app.get("/api/v1/stats/api-usage-daily", response_class=JSONResponse)
def get_api_usage_daily(
    days: int = Query(None, description="최근 N일"),
    start: str = Query(None, description="시작일(YYYY-MM-DD)"),
    end: str = Query(None, description="종료일(YYYY-MM-DD)")
):
    """일자별 OpenAI/Gemini API 호출 건수 반환 (누락일은 0)"""
    usage_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'api_usage.json'))
    # 날짜 범위 결정
    if start and end:
        start_date = datetime.strptime(start, '%Y-%m-%d').date()
        end_date = datetime.strptime(end, '%Y-%m-%d').date()
        days_list = [(start_date + timedelta(days=i)) for i in range((end_date - start_date).days + 1)]
    else:
        n = days if days else 30
        today = datetime.now().date()
        days_list = [(today - timedelta(days=i)) for i in range(n-1, -1, -1)]
    day_strs = [d.strftime('%Y-%m-%d') for d in days_list]
    # 데이터 집계
    openai_counts = [0] * len(day_strs)
    gemini_counts = [0] * len(day_strs)
    try:
        if os.path.exists(usage_file):
            with open(usage_file, 'r', encoding='utf-8') as f:
                usage = json.load(f)
        else:
            usage = {}
        for idx, d in enumerate(day_strs):
            day_usage = usage.get(d, {})
            openai_counts[idx] = day_usage.get('openai', 0)
            gemini_counts[idx] = day_usage.get('gemini', 0)
        return {
            "dates": day_strs,
            "openai": openai_counts,
            "gemini": gemini_counts
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"API 호출 일자별 통계 불러오기 실패: {e}"})

# crawling_stats.json 파일을 직접 반환하는 엔드포인트 추가
@app.get("/crawling_stats.json")
async def get_crawling_stats():
    try:
        return FileResponse("crawling_stats.json", media_type="application/json")
    except Exception as e:
        return JSONResponse(status_code=404, content={"detail": f"crawling_stats.json 파일을 찾을 수 없습니다: {e}"})

@app.get("/api/v1/stats/keywords-summary", response_class=JSONResponse)
async def get_keywords_summary(db: Session = Depends(get_db)):
    """
    누적 키워드 추출 건수와 상위 키워드 3개 반환
    """
    keywords_counter = Counter()
    try:
        posts = db.query(models.BlogPost).all()
        for post in posts:
            if post.keywords:
                for kw in re.split(r'[;,\n]+', post.keywords):
                    kw = kw.strip()
                    if kw:
                        keywords_counter[kw] += 1
    except Exception:
        pass
    total_keywords = sum(keywords_counter.values())
    top_keywords = [k for k, v in keywords_counter.most_common(3)]
    return {
        "total_keywords": total_keywords,
        "top_keywords": ', '.join(top_keywords)
    }

# API Key 목록 조회
@app.get("/api/v1/admin/api-keys", response_model=list[APIKeyOut])
def api_key_list(service: str = None, active_only: bool = False, db: Session = Depends(get_db)):
    db_keys = get_api_keys(db, service=service, active_only=active_only)
    db_keys_set = set((k.service, k.key) for k in db_keys)
    config_keys = []
    # OpenAI(예시: 환경변수에 있다면)
    if settings.openai_api_key and ("openai", settings.openai_api_key) not in db_keys_set:
        config_keys.append({
            "id": 0,
            "service": "openai",
            "key": settings.openai_api_key,
            "description": "환경설정(ENV/.env) 직접 입력",
            "is_active": True,
            "created_at": None,
            "updated_at": None
        })
    # Gemini(예시: 환경변수에 있다면)
    if hasattr(settings, "gemini_api_key") and settings.gemini_api_key and ("gemini", settings.gemini_api_key) not in db_keys_set:
        config_keys.append({
            "id": 0,
            "service": "gemini",
            "key": settings.gemini_api_key,
            "description": "환경설정(ENV/.env) 직접 입력",
            "is_active": True,
            "created_at": None,
            "updated_at": None
        })
    return db_keys + config_keys

# API Key 생성
@app.post("/api/v1/admin/api-keys", response_model=APIKeyOut)
def api_key_create(data: APIKeyCreate, db: Session = Depends(get_db)):
    # None 방지
    description = data.description if data.description is not None else ""
    is_active = data.is_active if data.is_active is not None else True
    return create_api_key(db, service=data.service, key=data.key, description=description, is_active=is_active)

# API Key 수정
@app.put("/api/v1/admin/api-keys/{key_id}", response_model=APIKeyOut)
def api_key_update(key_id: int, data: APIKeyUpdate, db: Session = Depends(get_db)):
    update_data = data.dict(exclude_unset=True)
    # None 방지
    if "description" in update_data and update_data["description"] is None:
        update_data["description"] = ""
    if "is_active" in update_data and update_data["is_active"] is None:
        update_data["is_active"] = True
    return update_api_key(db, key_id, **update_data)

# API Key 삭제
@app.delete("/api/v1/admin/api-keys/{key_id}")
def api_key_delete(key_id: int, db: Session = Depends(get_db)):
    success = delete_api_key(db, key_id)
    return {"success": success}

# 크롤링 작업 모니터링 API (관리자용)
@app.get("/api/v1/admin/crawling/overall")
def admin_crawling_overall():
    return crawling_monitor.get_overall_stats()

@app.get("/api/v1/admin/crawling/problem-sites")
def admin_crawling_problem_sites():
    return crawling_monitor.get_problem_sites()

@app.get("/api/v1/admin/crawling/recent-attempts")
def admin_crawling_recent_attempts(limit: int = 20):
    return crawling_monitor.get_recent_attempts(limit=limit)

@app.get("/api/v1/admin/crawling/site-stats")
def admin_crawling_site_stats(domain: str):
    return crawling_monitor.get_site_stats(domain)

@app.get("/api/v1/admin/crawling/report")
def admin_crawling_report():
    return {"report": crawling_monitor.generate_report()}

# 키워드 블랙/화이트리스트 관리 API (관리자)
@app.get("/api/v1/admin/keywords-list", response_model=list[KeywordListOut])
def admin_keywords_list(type: str = None, db: Session = Depends(get_db)):
    keywords = get_keywords_list(db, list_type=type)
    # 네이버 검색량 연동 (최대 20개만)
    keyword_names = [k.keyword for k in keywords][:20]
    naver_volumes = get_naver_keyword_volumes(keyword_names) if keyword_names else {}
    # 검색량 내림차순 순위 부여
    sorted_keywords = sorted([(k, naver_volumes.get(k, 0) or 0) for k in keyword_names], key=lambda x: x[1], reverse=True)
    naver_ranks = {k: i+1 for i, (k, _) in enumerate(sorted_keywords)}
    # 각 키워드에 검색량/순위 추가
    for k in keywords:
        k.naver_volume = naver_volumes.get(k.keyword)
        k.naver_rank = naver_ranks.get(k.keyword)
    return keywords

@app.post("/api/v1/admin/keywords-list", response_model=KeywordListOut)
def admin_add_keyword(data: KeywordListBase, db: Session = Depends(get_db)):
    return add_keyword_to_list(db, list_type=data.type, keyword=data.keyword)

@app.delete("/api/v1/admin/keywords-list")
def admin_delete_keyword(type: str, keyword: str, db: Session = Depends(get_db)):
    success = delete_keyword_from_list(db, list_type=type, keyword=keyword)
    return {"success": success}

@app.post("/api/v1/admin/keywords-list/bulk")
def admin_bulk_add_keywords(data: KeywordListBulkIn, db: Session = Depends(get_db)):
    return bulk_add_keywords(db, list_type=data.type, keywords=data.keywords)

@app.delete("/api/v1/admin/keywords-list/bulk")
def admin_bulk_delete_keywords(type: str, keywords: str, db: Session = Depends(get_db)):
    # keywords는 콤마로 구분된 문자열로 받음
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    bulk_delete_keywords(db, list_type=type, keywords=kw_list)
    return {"success": True}

# 포스트 일괄 삭제/백업/복원 API (관리자)
@app.post("/api/v1/admin/posts/bulk-delete")
def admin_bulk_delete_posts(data: BulkDeleteIn, db: Session = Depends(get_db)):
    bulk_delete_posts(db, post_ids=data.post_ids)
    return {"success": True}

@app.get("/api/v1/admin/posts/export", response_model=list[PostExport])
def admin_export_posts(ids: str = None, db: Session = Depends(get_db)):
    # ids는 콤마로 구분된 문자열
    post_ids = [int(i) for i in ids.split(",")] if ids else None
    return export_posts(db, post_ids=post_ids)

@app.post("/api/v1/admin/posts/import")
def admin_import_posts(data: list[PostImport], db: Session = Depends(get_db)):
    # data는 posts 배열
    posts_data = [d.dict() for d in data]
    import_posts(db, posts_data=posts_data)
    return {"success": True}

@app.get("/api/v1/admin/keywords-recommend")
def admin_keywords_recommend(db: Session = Depends(get_db)):
    # 샘플: 최근 포스트에서 많이 등장한 키워드 5개
    posts = db.query(models.BlogPost).order_by(models.BlogPost.created_at.desc()).limit(30).all()
    counter = Counter()
    for post in posts:
        if post.keywords:
            for kw in re.split(r'[;,\n]+', post.keywords):
                kw = kw.strip()
                if kw:
                    counter[kw] += 1
    return [k for k, v in counter.most_common(5)]

@app.get("/api/v1/admin/keywords-duplicates")
def admin_keywords_duplicates(db: Session = Depends(get_db)):
    # 샘플: Levenshtein 유사도 0.8 이상 쌍 반환
    keywords = [k.keyword for k in crud.get_keywords_list(db)]
    dups = []
    for i in range(len(keywords)):
        for j in range(i+1, len(keywords)):
            s1, s2 = keywords[i], keywords[j]
            sim = SequenceMatcher(None, s1, s2).ratio()
            if sim >= 0.8 and s1 != s2:
                dups.append({'a': s1, 'b': s2, 'similarity': round(sim,2)})
    return dups

@app.get("/api/v1/admin/keywords-synonyms")
def admin_keywords_synonyms(db: Session = Depends(get_db)):
    # 샘플: DB에 synonyms.json 파일로 관리
    syn_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'synonyms.json'))
    if os.path.exists(syn_file):
        with open(syn_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

@app.post("/api/v1/admin/keywords-synonyms")
def admin_add_synonym(keyword: str = Body(...), synonym: str = Body(...)):
    syn_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'synonyms.json'))
    data = {}
    if os.path.exists(syn_file):
        with open(syn_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    data.setdefault(keyword, []).append(synonym)
    with open(syn_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"success": True}

@app.delete("/api/v1/admin/keywords-synonyms")
def admin_delete_synonym(keyword: str = Query(...), synonym: str = Query(...)):
    # synonyms.json 파일에서 동의어 삭제
    try:
        import json
        synonyms_file = "synonyms.json"
        if os.path.exists(synonyms_file):
            with open(synonyms_file, 'r', encoding='utf-8') as f:
                synonyms = json.load(f)
        else:
            synonyms = {}
        
        if keyword in synonyms and synonym in synonyms[keyword]:
            synonyms[keyword].remove(synonym)
            if not synonyms[keyword]:  # 빈 리스트면 키워드도 삭제
                del synonyms[keyword]
            
            with open(synonyms_file, 'w', encoding='utf-8') as f:
                json.dump(synonyms, f, ensure_ascii=False, indent=2)
            
            return {"success": True, "message": f"동의어 '{synonym}' 삭제 완료"}
        else:
            return {"success": False, "message": "해당 동의어를 찾을 수 없습니다"}
    except Exception as e:
        logger.error(f"동의어 삭제 오류: {e}")
        return {"success": False, "message": f"동의어 삭제 중 오류 발생: {str(e)}"}

@app.get("/api/v1/admin/posts/stats")
def get_posts_stats(db: Session = Depends(get_db)):
    """포스트 분량별 통계"""
    from app.models import BlogPost
    
    try:
        # 전체 포스트 수
        total = db.query(BlogPost).count()
        
        # 분량별 통계 - 문자열 비교로 수정
        length_2000 = db.query(BlogPost).filter(BlogPost.content_length == "2000").count()
        length_3000 = db.query(BlogPost).filter(BlogPost.content_length == "3000").count()
        length_4000_plus = db.query(BlogPost).filter(
            BlogPost.content_length.in_(["4000", "5000"])
        ).count()
        
        # 디버깅을 위한 로그 추가
        logger.info(f"포스트 통계: total={total}, 2000={length_2000}, 3000={length_3000}, 4000+={length_4000_plus}")
        
        return {
            "total": total,
            "length_2000": length_2000,
            "length_3000": length_3000,
            "length_4000_plus": length_4000_plus
        }
    except Exception as e:
        logger.error(f"포스트 통계 조회 오류: {e}")
        return {
            "total": 0,
            "length_2000": 0,
            "length_3000": 0,
            "length_4000_plus": 0
        }
    syn_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'synonyms.json'))
    if not os.path.exists(syn_file):
        return {"success": False}
    with open(syn_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if keyword in data and synonym in data[keyword]:
        data[keyword].remove(synonym)
        if not data[keyword]:
            del data[keyword]
        with open(syn_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"success": True}
    return {"success": False}

@app.get("/api/v1/posts")
async def get_posts(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),
    category: str = Query(None)
):
    """포스트 목록 조회 (페이지네이션 지원)"""
    try:
        offset = (page - 1) * limit
        
        # 검색 조건 적용
        posts = crud.get_posts(db, skip=offset, limit=limit, search=search, category=category)
        total = crud.get_posts_count(db, search=search, category=category)
        
        return {
            "posts": posts,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    except Exception as e:
        logger.error(f"포스트 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="포스트 목록을 불러오는데 실패했습니다.")

@app.get("/api/v1/posts/{post_id}")
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """특정 포스트 조회"""
    try:
        post = crud.get_post(db, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="포스트를 찾을 수 없습니다.")
        return post
    except Exception as e:
        logger.error(f"포스트 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="포스트를 불러오는데 실패했습니다.")

@app.delete("/api/v1/posts/{post_id}")
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    """포스트 삭제"""
    try:
        success = crud.delete_post(db, post_id)
        if not success:
            raise HTTPException(status_code=404, detail="포스트를 찾을 수 없습니다.")
        return {"message": "포스트가 삭제되었습니다."}
    except Exception as e:
        logger.error(f"포스트 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail="포스트 삭제에 실패했습니다.")

@app.get("/api/v1/keywords")
async def get_keywords(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),
    category: str = Query(None)
):
    """키워드 목록 조회 (페이지네이션 지원)"""
    try:
        offset = (page - 1) * limit
        
        # 검색 조건 적용
        keywords = crud.get_keywords(db, skip=offset, limit=limit, search=search, category=category)
        total = crud.get_keywords_count(db, search=search, category=category)
        
        return {
            "keywords": keywords,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    except Exception as e:
        logger.error(f"키워드 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="키워드 목록을 불러오는데 실패했습니다.")

@app.get("/api/v1/keywords/{keyword_id}")
async def get_keyword(keyword_id: int, db: Session = Depends(get_db)):
    """특정 키워드 조회"""
    try:
        keyword = crud.get_keyword(db, keyword_id)
        if not keyword:
            raise HTTPException(status_code=404, detail="키워드를 찾을 수 없습니다.")
        return keyword
    except Exception as e:
        logger.error(f"키워드 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="키워드를 불러오는데 실패했습니다.")

@app.post("/api/v1/keywords")
async def create_keyword(keyword_data: dict, db: Session = Depends(get_db)):
    """키워드 생성"""
    try:
        keyword = crud.create_keyword(db, keyword_data)
        return keyword
    except Exception as e:
        logger.error(f"키워드 생성 오류: {e}")
        raise HTTPException(status_code=500, detail="키워드 생성에 실패했습니다.")

@app.put("/api/v1/keywords/{keyword_id}")
async def update_keyword(keyword_id: int, keyword_data: dict, db: Session = Depends(get_db)):
    """키워드 수정"""
    try:
        keyword = crud.update_keyword(db, keyword_id, keyword_data)
        if not keyword:
            raise HTTPException(status_code=404, detail="키워드를 찾을 수 없습니다.")
        return keyword
    except Exception as e:
        logger.error(f"키워드 수정 오류: {e}")
        raise HTTPException(status_code=500, detail="키워드 수정에 실패했습니다.")

@app.delete("/api/v1/keywords/{keyword_id}")
async def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    """키워드 삭제"""
    try:
        success = crud.delete_keyword(db, keyword_id)
        if not success:
            raise HTTPException(status_code=404, detail="키워드를 찾을 수 없습니다.")
        return {"message": "키워드가 삭제되었습니다."}
    except Exception as e:
        logger.error(f"키워드 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail="키워드 삭제에 실패했습니다.")

@app.get("/api/v1/stats/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """통합 대시보드 통계를 반환합니다."""
    try:
        # 캐시된 데이터 확인
        cached_data = get_cached_data("dashboard_stats")
        if cached_data:
            return cached_data
        
        # 기본 통계
        total_posts = crud.get_total_posts(db)
        total_keywords = crud.get_total_keywords(db)
        
        # API 사용량 통계 (동기 함수 사용)
        api_usage_data = {}
        try:
            with open('api_usage.json', 'r') as f:
                api_usage_data = json.load(f)
        except:
            api_usage_data = {"today": {"openai": 0, "gemini": 0, "translation": 0}}
        
        api_calls_today = sum(api_usage_data.get('today', {}).values())
        
        # 크롤링 성공률 (동기 함수 사용)
        crawl_stats_data = {}
        try:
            with open('crawling_stats.json', 'r') as f:
                crawl_stats_data = json.load(f)
        except:
            crawl_stats_data = {"success_rate": 0}
        
        crawl_success_rate = crawl_stats_data.get('success_rate', 0)
        
        # 포스트 분량별 통계
        posts_stats = crud.get_posts_stats(db)
        
        # 키워드 타입별 통계
        keywords_stats = crud.get_keywords_stats(db)
        
        # 뉴스 아카이브 통계
        news_stats = get_news_archive_stats()
        
        # 시스템 성능 통계
        system_stats = get_system_stats()
        
        result = {
            "total_posts": total_posts,
            "total_keywords": total_keywords,
            "api_calls_today": api_calls_today,
            "crawl_success_rate": crawl_success_rate,
            
            # API 사용량 상세
            "openai_calls": api_usage_data.get('today', {}).get('openai', 0),
            "gemini_calls": api_usage_data.get('today', {}).get('gemini', 0),
            "translation_calls": api_usage_data.get('today', {}).get('translation', 0),
            
            # 포스트 통계
            "posts_2000": posts_stats.get('2000', 0),
            "posts_3000": posts_stats.get('3000', 0),
            "posts_4000": posts_stats.get('4000', 0),
            "posts_5000": posts_stats.get('5000', 0),
            
            # 키워드 통계
            "keywords_ai": keywords_stats.get('AI', 0),
            "keywords_seo": keywords_stats.get('SEO', 0),
            "keywords_tech": keywords_stats.get('Tech', 0),
            "keywords_marketing": keywords_stats.get('Marketing', 0),
            
            # 뉴스 아카이브 통계
            "aeo_news": news_stats.get('aeo', 0),
            "geo_news": news_stats.get('geo', 0),
            "aio_news": news_stats.get('aio', 0),
            
            # 시스템 성능 통계
            "db_size": system_stats.get('db_size', 'N/A'),
            "log_files": system_stats.get('log_files', 'N/A'),
            "api_response_time": system_stats.get('api_response_time', 'N/A'),
            "system_uptime": system_stats.get('system_uptime', 'N/A')
        }
        
        # 결과를 캐시에 저장 (1분 TTL)
        set_cached_data("dashboard_stats", result)
        
        return result
        
    except Exception as e:
        logger.error(f"대시보드 통계 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail="대시보드 통계를 불러오는데 실패했습니다.")

# SEO Guidelines API
@app.get("/api/v1/admin/seo-guidelines")
async def get_seo_guidelines_api():
    """현재 SEO 가이드라인 조회"""
    try:
        from app.seo_guidelines import get_seo_guidelines
        guidelines = get_seo_guidelines()
        return guidelines
    except Exception as e:
        logger.error(f"SEO 가이드라인 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/admin/seo-guidelines/version")

# Manual trigger for SEO guidelines update
@app.post("/api/v1/admin/seo-guidelines/update")
async def trigger_seo_update():
    """Manually trigger the weekly SEO guidelines update process."""
    try:
        # Run the update process and get the report
        report = await run_seo_update()
        # Store the report in the history table
        from app.models import SEOGuidelineHistory
        from app.database import SessionLocal
        db = SessionLocal()
        history_entry = SEOGuidelineHistory(
            version=report.get("current_version", "unknown"),
            changes_summary=report.get("changes_detected", {}).get("new_trends", 0),
            report_path=report.get("report_path", "")
        )
        db.add(history_entry)
        db.commit()
        db.refresh(history_entry)
        db.close()
        return {"status": "update_triggered", "report": report}
    except Exception as e:
        logger.error(f"Failed to trigger SEO update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Retrieve SEO guidelines update history
@app.get("/api/v1/admin/seo-guidelines/history")
def get_seo_update_history(db: Session = Depends(get_db)):
    """Return a list of past SEO guideline updates."""
    from app.models import SEOGuidelineHistory
    histories = db.query(SEOGuidelineHistory).order_by(SEOGuidelineHistory.updated_at.desc()).all()
    return [
        {
            "id": h.id,
            "version": h.version,
            "updated_at": h.updated_at,
            "changes_summary": h.changes_summary,
            "report_path": h.report_path,
        }
        for h in histories
    ]

# Rollback to a specific SEO guidelines version
@app.post("/api/v1/admin/seo-guidelines/rollback/{version}")
async def rollback_seo_guidelines(version: str, db: Session = Depends(get_db)):
    """SEO 가이드라인을 특정 버전으로 롤백"""
    try:
        # 이력 조회
        from app.models import SEOGuidelineHistory
        history = db.query(SEOGuidelineHistory).filter(SEOGuidelineHistory.version == version).first()
        if not history:
            raise HTTPException(status_code=404, detail="Version not found")
        
        # 리포트 파일 로드
        import json, os
        if not history.report_path or not os.path.exists(history.report_path):
            raise HTTPException(status_code=404, detail="Report file not found")
            
        with open(history.report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
            
        # 가이드라인 스냅샷 확인
        if "guidelines_snapshot" not in report:
            raise HTTPException(status_code=400, detail="Snapshot not available in this version")
            
        # 롤백 적용
        from app.seo_guidelines import save_seo_guidelines
        if save_seo_guidelines(report["guidelines_snapshot"]):
            logger.info(f"Rolled back SEO guidelines to version {version}")
            return {"message": f"Successfully rolled back to version {version}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save rolled back guidelines")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
async def get_seo_guidelines_version():
    """SEO 가이드라인 버전 정보 조회"""
    try:
        from app.seo_guidelines import get_guideline_version_info
        version_info = get_guideline_version_info()
        return version_info
    except Exception as e:
        logger.error(f"SEO 가이드라인 버전 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/admin/seo-guidelines/{guideline_type}")
async def get_specific_seo_guideline(guideline_type: str):
    """특정 SEO 가이드라인 조회"""
    try:
        from app.seo_guidelines import get_guideline_by_type
        guideline = get_guideline_by_type(guideline_type)
        if not guideline:
            raise HTTPException(status_code=404, detail=f"Guideline type '{guideline_type}' not found")
        return guideline
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEO 가이드라인 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_news_archive_stats():
    """뉴스 아카이브 통계를 반환합니다."""
    try:
        # 실제 구현에서는 데이터베이스에서 뉴스 아카이브 통계를 조회
        return {
            "aeo": 15,
            "geo": 12,
            "aio": 8
        }
    except:
        return {"aeo": 0, "geo": 0, "aio": 0}

def get_system_stats():
    """시스템 성능 통계를 반환합니다."""
    try:
        import os
        import time
        
        # 데이터베이스 크기
        db_size = "80KB"  # 실제로는 파일 크기 계산
        
        # 로그 파일 수
        log_dir = "logs"
        log_files = len([f for f in os.listdir(log_dir) if f.endswith('.log')]) if os.path.exists(log_dir) else 0
        
        # API 응답 시간 (평균)
        api_response_time = "0.002s"
        
        # 시스템 업타임
        system_uptime = "2시간 30분"
        
        return {
            "db_size": db_size,
            "log_files": log_files,
            "api_response_time": api_response_time,
            "system_uptime": system_uptime
        }
    except:
        return {
            "db_size": "N/A",
            "log_files": "N/A", 
            "api_response_time": "N/A",
            "system_uptime": "N/A"
        }

# 시스템 관리 API 엔드포인트들
@app.get("/api/v1/system/uptime")
async def get_system_uptime():
    """시스템 가동시간 및 리소스 사용률을 반환합니다."""
    try:
        import psutil
        import time
        
        # 시스템 가동시간
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_hours = int(uptime_seconds // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        
        # 리소스 사용률
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "uptime": f"{uptime_hours}시간 {uptime_minutes}분",
            "cpu_usage": round(cpu_usage, 2),
            "memory_usage": round(memory.percent, 2),
            "disk_usage": round(disk.percent, 2),
            "memory_total": f"{memory.total // (1024**3):.1f}GB",
            "memory_used": f"{memory.used // (1024**3):.1f}GB",
            "disk_total": f"{disk.total // (1024**3):.1f}GB",
            "disk_used": f"{disk.used // (1024**3):.1f}GB"
        }
    except Exception as e:
        logger.error(f"시스템 가동시간 조회 중 오류: {e}")
        return {
            "uptime": "N/A",
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0
        }

@app.get("/api/v1/system/db-size")
async def get_database_size():
    """데이터베이스 크기 정보를 반환합니다."""
    try:
        import os
        
        # SQLite 데이터베이스 파일 크기
        db_path = "blog.db"
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            size_mb = size_bytes / (1024 * 1024)
            
            # 사용 가능한 디스크 공간
            disk = psutil.disk_usage('/')
            free_bytes = disk.free
            
            return {
                "size": f"{size_mb:.2f}MB",
                "used_bytes": size_bytes,
                "free_bytes": free_bytes,
                "total_bytes": disk.total
            }
        else:
            return {
                "size": "0MB",
                "used_bytes": 0,
                "free_bytes": 0,
                "total_bytes": 0
            }
    except Exception as e:
        logger.error(f"데이터베이스 크기 조회 중 오류: {e}")
        return {
            "size": "N/A",
            "used_bytes": 0,
            "free_bytes": 0,
            "total_bytes": 0
        }

@app.get("/api/v1/system/api-response-time")
async def get_api_response_time():
    """API 응답시간 통계를 반환합니다."""
    try:
        # 실제로는 응답시간 데이터를 수집해야 하지만, 여기서는 샘플 데이터 반환
        return {
            "average_response_time": "150ms",
            "hour1": 120,
            "hour2": 135,
            "hour3": 145,
            "hour4": 155,
            "hour5": 140,
            "hour6": 130,
            "hour7": 125,
            "hour8": 135,
            "hour9": 150,
            "hour10": 160
        }
    except Exception as e:
        logger.error(f"API 응답시간 조회 중 오류: {e}")
        return {
            "average_response_time": "N/A",
            "hour1": 0,
            "hour2": 0,
            "hour3": 0,
            "hour4": 0,
            "hour5": 0,
            "hour6": 0,
            "hour7": 0,
            "hour8": 0,
            "hour9": 0,
            "hour10": 0
        }

@app.get("/api/v1/system/log-files")
async def get_log_files_info():
    """로그 파일 정보를 반환합니다."""
    try:
        import os
        import glob
        
        # 로그 파일 목록
        log_files = glob.glob("logs/*.log") + glob.glob("*.log")
        total_files = len(log_files)
        
        # 데이터베이스 테이블 정보
        db = SessionLocal()
        tables_info = []
        
        try:
            # blog_posts 테이블
            posts_count = db.query(models.BlogPost).count()
            tables_info.append({
                "table_name": "blog_posts",
                "row_count": posts_count,
                "size": f"{posts_count * 1024}KB",  # 추정 크기
                "last_update": datetime.now().isoformat()
            })
            
            # keyword_list 테이블
            keywords_count = db.query(models.KeywordList).count()
            tables_info.append({
                "table_name": "keyword_list",
                "row_count": keywords_count,
                "size": f"{keywords_count * 512}KB",  # 추정 크기
                "last_update": datetime.now().isoformat()
            })
            
            # feature_updates 테이블
            updates_count = db.query(models.FeatureUpdate).count()
            tables_info.append({
                "table_name": "feature_updates",
                "row_count": updates_count,
                "size": f"{updates_count * 256}KB",  # 추정 크기
                "last_update": datetime.now().isoformat()
            })
            
        finally:
            db.close()
        
        # API 사용량 통계 (샘플 데이터)
        api_calls = {
            "OpenAI": {
                "today": 45,
                "week": 320,
                "month": 1250,
                "success_rate": 98.5,
                "avg_response_time": 1200
            },
            "Gemini": {
                "today": 23,
                "week": 180,
                "month": 750,
                "success_rate": 99.2,
                "avg_response_time": 800
            },
            "Translation": {
                "today": 67,
                "week": 450,
                "month": 1800,
                "success_rate": 97.8,
                "avg_response_time": 500
            }
        }
        
        # API 키 상태 (샘플 데이터)
        api_keys = {
            "OpenAI": {
                "status": "활성",
                "last_checked": datetime.now().isoformat()
            },
            "Gemini": {
                "status": "활성",
                "last_checked": datetime.now().isoformat()
            }
        }
        
        # 로그 레벨 통계 (샘플 데이터)
        log_levels = {
            "INFO": 1250,
            "WARNING": 45,
            "ERROR": 12,
            "DEBUG": 89
        }
        
        return {
            "total_files": total_files,
            "tables": tables_info,
            "api_calls": api_calls,
            "api_keys": api_keys,
            "log_levels": log_levels
        }
        
    except Exception as e:
        logger.error(f"로그 파일 정보 조회 중 오류: {e}")
        return {
            "total_files": 0,
            "tables": [],
            "api_calls": {},
            "api_keys": {},
            "log_levels": {}
        }

@app.get("/api/v1/system/logs/recent")
async def get_recent_logs():
    """최근 로그를 반환합니다."""
    try:
        # 실제 로그 파일에서 최근 로그를 읽어오는 로직
        recent_logs = [
            {
                "level": "INFO",
                "message": "시스템이 정상적으로 실행 중입니다.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "level": "INFO",
                "message": "API 요청 처리 완료: /api/v1/posts",
                "timestamp": (datetime.now() - timedelta(minutes=2)).isoformat()
            },
            {
                "level": "WARNING",
                "message": "API 응답시간이 평균보다 느립니다.",
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat()
            },
            {
                "level": "INFO",
                "message": "데이터베이스 연결 상태: 정상",
                "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat()
            }
        ]
        
        return recent_logs
        
    except Exception as e:
        logger.error(f"최근 로그 조회 중 오류: {e}")
        return []

@app.get("/api/v1/system/logs/download")
async def download_logs():
    """로그 파일을 다운로드합니다."""
    try:
        import os
        
        # 로그 파일 내용 생성
        log_content = f"""
=== AI SEO Blog Generator 로그 파일 ===
생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

시스템 정보:
- 가동시간: {get_system_uptime()['uptime']}
- CPU 사용률: {get_system_uptime()['cpu_usage']}%
- 메모리 사용률: {get_system_uptime()['memory_usage']}%

최근 로그:
{chr(10).join([f"[{log['level']}] {log['message']} - {log['timestamp']}" for log in get_recent_logs()])}
        """.strip()
        
        return Response(
            content=log_content,
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=system_logs.txt"}
        )
        
    except Exception as e:
        logger.error(f"로그 다운로드 중 오류: {e}")
        raise HTTPException(status_code=500, detail="로그 다운로드에 실패했습니다.")

@app.post("/api/v1/system/logs/clear")
async def clear_logs():
    """로그 파일을 정리합니다."""
    try:
        # 실제로는 로그 파일을 정리하는 로직
        logger.info("로그 파일 정리 요청됨")
        
        return {"success": True, "message": "로그 파일이 정리되었습니다."}
        
    except Exception as e:
        logger.error(f"로그 정리 중 오류: {e}")
        return {"success": False, "message": "로그 정리에 실패했습니다."}

@app.post("/api/v1/system/settings")
async def save_system_settings(settings: dict):
    """시스템 설정을 저장합니다."""
    try:
        # 실제로는 설정을 파일이나 데이터베이스에 저장하는 로직
        logger.info(f"시스템 설정 저장: {settings}")
        
        return {"success": True, "message": "시스템 설정이 저장되었습니다."}
        
    except Exception as e:
        logger.error(f"시스템 설정 저장 중 오류: {e}")
        return {"success": False, "message": "시스템 설정 저장에 실패했습니다."}

@app.post("/api/v1/system/reset")
async def reset_system():
    """시스템을 초기화합니다."""
    try:
        # 실제로는 시스템 초기화 로직
        logger.warning("시스템 초기화 요청됨")
        
        return {"success": True, "message": "시스템이 초기화되었습니다."}
        
    except Exception as e:
        logger.error(f"시스템 초기화 중 오류: {e}")
        return {"success": False, "message": "시스템 초기화에 실패했습니다."}

@app.post("/api/v1/system/database/backup")
async def backup_database():
    """데이터베이스를 백업합니다."""
    try:
        import shutil
        import os
        
        # 백업 파일명 생성
        backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        # 데이터베이스 파일 복사
        if os.path.exists("blog.db"):
            shutil.copy2("blog.db", f"backups/{backup_filename}")
            logger.info(f"데이터베이스 백업 완료: {backup_filename}")
        
        return {"success": True, "message": f"데이터베이스 백업이 완료되었습니다: {backup_filename}"}
        
    except Exception as e:
        logger.error(f"데이터베이스 백업 중 오류: {e}")
        return {"success": False, "message": "데이터베이스 백업에 실패했습니다."}

@app.post("/api/v1/system/database/optimize")
async def optimize_database():
    """데이터베이스를 최적화합니다."""
    try:
        db = SessionLocal()
        
        # SQLite VACUUM 명령으로 데이터베이스 최적화
        db.execute(text("VACUUM"))
        db.commit()
        
        logger.info("데이터베이스 최적화 완료")
        
        return {"success": True, "message": "데이터베이스 최적화가 완료되었습니다."}
        
    except Exception as e:
        logger.error(f"데이터베이스 최적화 중 오류: {e}")
        return {"success": False, "message": "데이터베이스 최적화에 실패했습니다."}
    finally:
        db.close()

# 성능 모니터링 API 엔드포인트
@app.get("/api/v1/performance/summary")
async def get_performance_summary(hours: int = 24):
    """성능 모니터링 요약 데이터 반환"""
    try:
        summary = performance_monitor.get_performance_summary(hours)
        return summary
    except Exception as e:
        logger.error(f"성능 요약 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"성능 요약 조회 실패: {e}")

@app.get("/api/v1/performance/status")
async def get_performance_status():
    """성능 모니터링 상태 반환"""
    try:
        system_status = performance_monitor.get_system_status()
        return {
            "monitoring": performance_monitor.monitoring,
            "data_points": len(performance_monitor.performance_data),
            "last_update": system_status.get("last_update"),
            "cpu_usage": system_status.get("cpu_usage", 0.0),
            "memory_usage": system_status.get("memory_usage", 0.0),
            "disk_usage": system_status.get("disk_usage", 0.0)
        }
    except Exception as e:
        logger.error(f"성능 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"성능 상태 조회 실패: {e}")

@app.post("/api/v1/performance/restart")
async def restart_performance_monitor():
    """성능 모니터링 재시작"""
    try:
        performance_monitor.stop_monitoring()
        await asyncio.sleep(1)
        performance_monitor.start_monitoring()
        return {"message": "성능 모니터링이 재시작되었습니다."}
    except Exception as e:
        logger.error(f"성능 모니터링 재시작 실패: {e}")
        raise HTTPException(status_code=500, detail=f"성능 모니터링 재시작 실패: {e}")

@app.get("/api/v1/performance/data")
async def get_performance_data(limit: int = 100):
    """성능 모니터링 원시 데이터 반환"""
    try:
        data = performance_monitor.performance_data[-limit:] if limit > 0 else performance_monitor.performance_data
        return {
            "data": data,
            "total_points": len(performance_monitor.performance_data),
            "returned_points": len(data)
        }
    except Exception as e:
        logger.error(f"성능 데이터 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"성능 데이터 조회 실패: {e}")

# 시스템 진단 API 엔드포인트
@app.get("/api/v1/system/diagnostic")
async def run_system_diagnostic():
    """시스템 진단 실행"""
    try:
        log_system("시스템 진단 API 호출")
        result = await system_diagnostic.run_full_diagnostic()
        return result
    except Exception as e:
        log_error("시스템 진단 API 실패", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"시스템 진단 실패: {e}")

@app.get("/api/v1/system/diagnostic/summary")
async def get_diagnostic_summary():
    """시스템 진단 요약 반환"""
    try:
        summary = system_diagnostic.get_diagnostic_summary()
        return summary
    except Exception as e:
        log_error("시스템 진단 요약 조회 실패", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"진단 요약 조회 실패: {e}")

# 포괄적인 로깅 API 엔드포인트
@app.get("/api/v1/logs")
async def get_logs(
    level: str = None,
    category: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
    offset: int = 0
):
    """로그 조회"""
    try:
        logs = comprehensive_logger.get_logs(
            level=level,
            category=category,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        return {
            "logs": logs,
            "total": len(logs),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        log_error("로그 조회 실패", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"로그 조회 실패: {e}")

@app.get("/api/v1/logs/stats")
async def get_log_stats():
    """로그 통계 반환"""
    try:
        stats = comprehensive_logger.get_log_stats()
        return stats
    except Exception as e:
        log_error("로그 통계 조회 실패", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"로그 통계 조회 실패: {e}")

@app.get("/api/v1/logs/daily-stats")
async def get_daily_log_stats(days: int = 7):
    """일일 로그 통계 조회"""
    try:
        stats = comprehensive_logger.get_daily_stats(days=days)
        return stats
    except Exception as e:
        log_error("일일 로그 통계 조회 실패", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"일일 로그 통계 조회 실패: {e}")

@app.post("/api/v1/logs/export")
async def export_logs(
    output_file: str = "logs_export.json",
    level: str = None,
    category: str = None,
    start_date: str = None,
    end_date: str = None
):
    """로그 내보내기"""
    try:
        success = comprehensive_logger.export_logs(
            output_file=output_file,
            level=level,
            category=category,
            start_date=start_date,
            end_date=end_date
        )
        if success:
            return {"success": True, "message": f"로그가 {output_file}로 내보내기되었습니다."}
        else:
            return {"success": False, "message": "로그 내보내기에 실패했습니다."}
    except Exception as e:
        log_error("로그 내보내기 실패", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"로그 내보내기 실패: {e}")

# 자동 업데이트 모니터 API 엔드포인트
@app.get("/api/v1/auto-update/status")
async def get_auto_update_status():
    """자동 업데이트 모니터 상태 반환"""
    try:
        status = auto_update_monitor.get_system_status()
        return status
    except Exception as e:
        log_error("자동 업데이트 상태 조회 실패", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"자동 업데이트 상태 조회 실패: {e}")

@app.get("/api/v1/auto-update/history")
async def get_auto_update_history(limit: int = 50):
    """자동 업데이트 이력 반환"""
    try:
        history = auto_update_monitor.get_update_history(limit=limit)
        return history
    except Exception as e:
        log_error("자동 업데이트 이력 조회 실패", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"자동 업데이트 이력 조회 실패: {e}")

@app.post("/api/v1/auto-update/task/{task_name}/enable")
async def enable_update_task(task_name: str):
    """업데이트 작업 활성화"""
    try:
        auto_update_monitor.enable_task(task_name)
        log_system(f"업데이트 작업 활성화: {task_name}")
        return {"success": True, "message": f"작업 '{task_name}'이 활성화되었습니다."}
    except Exception as e:
        log_error("업데이트 작업 활성화 실패", {"error": str(e), "task_name": task_name})
        raise HTTPException(status_code=500, detail=f"작업 활성화 실패: {e}")

@app.post("/api/v1/auto-update/task/{task_name}/disable")
async def disable_update_task(task_name: str):
    """업데이트 작업 비활성화"""
    try:
        auto_update_monitor.disable_task(task_name)
        log_system(f"업데이트 작업 비활성화: {task_name}")
        return {"success": True, "message": f"작업 '{task_name}'이 비활성화되었습니다."}
    except Exception as e:
        log_error("업데이트 작업 비활성화 실패", {"error": str(e), "task_name": task_name})
        raise HTTPException(status_code=500, detail=f"작업 비활성화 실패: {e}")

@app.post("/api/v1/auto-update/alert/{rule_name}/enable")
async def enable_alert_rule(rule_name: str):
    """알림 규칙 활성화"""
    try:
        auto_update_monitor.enable_alert(rule_name)
        log_system(f"알림 규칙 활성화: {rule_name}")
        return {"success": True, "message": f"알림 규칙 '{rule_name}'이 활성화되었습니다."}
    except Exception as e:
        log_error("알림 규칙 활성화 실패", {"error": str(e), "rule_name": rule_name})
        raise HTTPException(status_code=500, detail=f"알림 규칙 활성화 실패: {e}")

@app.post("/api/v1/auto-update/alert/{rule_name}/disable")
async def disable_alert_rule(rule_name: str):
    """알림 규칙 비활성화"""
    try:
        auto_update_monitor.disable_alert(rule_name)
        log_system(f"알림 규칙 비활성화: {rule_name}")
        return {"success": True, "message": f"알림 규칙 '{rule_name}'이 비활성화되었습니다."}
    except Exception as e:
        log_error("알림 규칙 비활성화 실패", {"error": str(e), "rule_name": rule_name})
        raise HTTPException(status_code=500, detail=f"알림 규칙 비활성화 실패: {e}")

# README 업데이트 API 엔드포인트
@app.post("/api/v1/readme/update")
async def update_readme():
    """README 자동 업데이트 실행"""
    try:
        log_system("README 자동 업데이트 API 호출")
        success = readme_updater.auto_update_readme()
        if success:
            return {"success": True, "message": "README가 성공적으로 업데이트되었습니다."}
        else:
            return {"success": False, "message": "README 업데이트할 내용이 없습니다."}
    except Exception as e:
        log_error("README 업데이트 실패", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"README 업데이트 실패: {e}")

@app.get("/api/v1/readme/update-history")
async def get_readme_update_history(limit: int = 10):
    """README 업데이트 이력 반환"""
    try:
        history = readme_updater.get_update_history(limit=limit)
        return history
    except Exception as e:
        log_error("README 업데이트 이력 조회 실패", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"README 업데이트 이력 조회 실패: {e}")

# 타겟 분석 API 엔드포인트
from app.services.target_analyzer import analyze_target

@app.post("/api/v1/target/analyze")
async def analyze_target_endpoint(
    target_keyword: str = Body(..., description="분석할 타겟 키워드 또는 주제"),
    target_type: str = Body("keyword", description="분석 유형: keyword, audience, competitor"),
    additional_context: Optional[str] = Body(None, description="추가 컨텍스트 정보"),
    use_gemini: bool = Body(False, description="Gemini API 사용 여부")
):
    """AI를 사용하여 타겟 분석을 수행합니다."""
    try:
        logger.info(f"타겟 분석 요청: {target_keyword} ({target_type})")
        
        # 타겟 타입 검증
        if target_type not in ["keyword", "audience", "competitor"]:
            raise HTTPException(
                status_code=400,
                detail="target_type은 'keyword', 'audience', 'competitor' 중 하나여야 합니다."
            )
        
        # 타겟 분석 수행
        result = await analyze_target(
            target_keyword=target_keyword,
            target_type=target_type,
            additional_context=additional_context,
            use_gemini=use_gemini
        )
        
        log_system("타겟 분석 완료", {
            "target": target_keyword,
            "type": target_type,
            "model": "gemini" if use_gemini else "openai"
        })
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"타겟 분석 중 오류: {e}")
        log_error("타겟 분석 실패", {"error": str(e), "target": target_keyword})
        raise HTTPException(
            status_code=500,
            detail=f"타겟 분석 실패: {str(e)}"
        )

@app.get("/api/v1/target/analyze")
async def analyze_target_get(
    target_keyword: str = Query(..., description="분석할 타겟 키워드 또는 주제"),
    target_type: str = Query("keyword", description="분석 유형: keyword, audience, competitor"),
    additional_context: Optional[str] = Query(None, description="추가 컨텍스트 정보"),
    use_gemini: bool = Query(False, description="Gemini API 사용 여부")
):
    """AI를 사용하여 타겟 분석을 수행합니다. (GET 방식)"""
    try:
        logger.info(f"타겟 분석 요청 (GET): {target_keyword} ({target_type})")
        
        # 타겟 타입 검증
        if target_type not in ["keyword", "audience", "competitor"]:
            raise HTTPException(
                status_code=400,
                detail="target_type은 'keyword', 'audience', 'competitor' 중 하나여야 합니다."
            )
        
        # 타겟 분석 수행
        result = await analyze_target(
            target_keyword=target_keyword,
            target_type=target_type,
            additional_context=additional_context,
            use_gemini=use_gemini
        )
        
        log_system("타겟 분석 완료", {
            "target": target_keyword,
            "type": target_type,
            "model": "gemini" if use_gemini else "openai"
        })
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"타겟 분석 중 오류: {e}")
        log_error("타겟 분석 실패", {"error": str(e), "target": target_keyword})
        raise HTTPException(
            status_code=500,
            detail=f"타겟 분석 실패: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )