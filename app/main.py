from fastapi import FastAPI, Request, Depends, HTTPException, Body, Query, Form
from fastapi import FastAPI, Request, Depends, HTTPException
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
from difflib import SequenceMatcher
from starlette.middleware.sessions import SessionMiddleware

# 설정 및 유틸리티 임포트
from .config import settings
from .utils.logger import setup_logger
from .database import engine, SessionLocal
from . import models, crud, exceptions
from .schemas import APIKeyCreate, APIKeyUpdate, APIKeyOut, KeywordListBase, KeywordListOut, KeywordListBulkIn, PostExport, PostImport, BulkDeleteIn
from .crud import get_api_keys, get_api_key_by_id, create_api_key, update_api_key, delete_api_key, get_keywords_list, add_keyword_to_list, delete_keyword_from_list, bulk_add_keywords, bulk_delete_keywords, bulk_delete_posts, export_posts, import_posts
from app.services.crawler_monitor import crawling_monitor
from app.services.translator import get_naver_keyword_volumes

# 로거 설정
logger = setup_logger(__name__, "app.log")

# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.app_name,
    description="AI를 활용한 SEO 최적화 블로그 포스트 생성기",
    version="1.0.0"
)

# SessionMiddleware를 라우터 등록 등 모든 코드보다 먼저 추가
app.add_middleware(SessionMiddleware, secret_key=settings.admin_password+"_session")

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/crawling_stats.json", StaticFiles(html=True, directory="."), name="crawling_stats_json")
templates = Jinja2Templates(directory="app/templates")

# 라우터 등록
from app.routers import blog_generator, feature_updates
app.include_router(blog_generator.router, prefix="/api/v1")
app.include_router(feature_updates.router)

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
@app.get("/health")
async def health_check():
    """애플리케이션 상태 확인"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": "1.0.0"
    }

# 메인 페이지
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """메인 페이지를 렌더링합니다."""
    return templates.TemplateResponse("index.html", {"request": request})

# 히스토리 페이지
@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, db: Session = Depends(get_db)):
    """생성된 포스트 기록 페이지를 렌더링합니다."""
    try:
        posts = crud.get_blog_posts(db)
        posts_json_str = json.dumps(jsonable_encoder(posts))
        return templates.TemplateResponse(
            "history.html", 
            {"request": request, "posts": posts, "posts_json": posts_json_str}
        )
    except Exception as e:
        logger.error(f"히스토리 페이지 로드 중 오류: {e}")
        raise HTTPException(status_code=500, detail="히스토리를 불러오는 중 오류가 발생했습니다.")

# 관리 페이지
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == settings.admin_username and password == settings.admin_password:
        request.session["admin_authenticated"] = True
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "아이디 또는 비밀번호가 올바르지 않습니다."})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

# 기존 /admin 라우트 보호
@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    if not request.session.get("admin_authenticated"):
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("admin.html", {"request": request})

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
    """애플리케이션 시작 시 실행되는 이벤트"""
    logger.info(f"{settings.app_name} 애플리케이션이 시작되었습니다.")
    
    # 설정 유효성 검사
    errors = settings.validate_settings()
    if errors:
        logger.error("설정 오류가 발견되었습니다:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.warning("일부 기능이 제한될 수 있습니다.")

# 애플리케이션 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행되는 이벤트"""
    logger.info(f"{settings.app_name} 애플리케이션이 종료되었습니다.")

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
    """OpenAI, DeepL, Gemini 등 API 호출 누적 집계 반환"""
    usage_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'api_usage.json'))
    try:
        total_openai = 0
        total_deepl = 0
        total_gemini = 0
        if os.path.exists(usage_file):
            with open(usage_file, 'r', encoding='utf-8') as f:
                usage = json.load(f)
            # 날짜별로 저장된 경우 전체 합계 계산
            if isinstance(usage, dict) and all(isinstance(v, dict) for v in usage.values()):
                for v in usage.values():
                    total_openai += v.get("openai", 0)
                    total_deepl += v.get("deepl", 0)
                    total_gemini += v.get("gemini", 0)
            else:
                total_openai = usage.get("openai", 0)
                total_deepl = usage.get("deepl", 0)
                total_gemini = usage.get("gemini", 0)
        return {
            "openai": total_openai,
            "deepl": total_deepl,
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
    """일자별 OpenAI/DeepL/Gemini API 호출 건수 반환 (누락일은 0)"""
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
    deepl_counts = [0] * len(day_strs)
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
            deepl_counts[idx] = day_usage.get('deepl', 0)
            gemini_counts[idx] = day_usage.get('gemini', 0)
        return {
            "dates": day_strs,
            "openai": openai_counts,
            "deepl": deepl_counts,
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
    # OpenAI
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
    # DeepL
    if settings.deepl_api_key and ("deepl", settings.deepl_api_key) not in db_keys_set:
        config_keys.append({
            "id": 0,
            "service": "deepl",
            "key": settings.deepl_api_key,
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