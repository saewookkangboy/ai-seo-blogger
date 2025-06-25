# app/routers/blog_generator.py

from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import Request
from fastapi.responses import StreamingResponse
import io
import openpyxl

# 서비스 및 DB 관련 모듈 임포트
from app.services.crawler import get_text_from_url
from app.services.translator import translate_text, translate_text_gemini, increase_api_usage_count
from app.services.content_generator import create_blog_post as generate_ai_post
from app.services.content_generator import extract_seo_keywords
from app import crud, models, exceptions
from app.database import SessionLocal, engine
from app.schemas import PostRequest, PostResponse, BlogPostResponse, ErrorResponse
from app.utils.logger import setup_logger
from app.services.rules import AI_RULES

logger = setup_logger(__name__)

# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)

router = APIRouter(tags=["blog-generation"])

# 데이터베이스 세션을 얻기 위한 의존성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/generate-post", response_model=PostResponse)
async def generate_post_endpoint(req: PostRequest, db: Session = Depends(get_db)):
    """
    URL 또는 텍스트를 받아 AI 블로그 포스트를 생성하고 DB에 저장합니다.
    """
    try:
        original_text = ""
        db_source_url = ""

        # 1. 입력 데이터 처리
        if req.url:
            logger.info(f"URL 입력으로 포스트 생성 시작: {req.url}")
            db_source_url = req.url
            original_text = await get_text_from_url(req.url)
        elif req.text:
            logger.info("텍스트 입력으로 포스트 생성 시작")
            db_source_url = "텍스트 직접 입력"
            original_text = req.text
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="URL 또는 텍스트를 입력해야 합니다."
            )

        # 2. 번역 (입력된 텍스트가 외국어라고 가정)
        logger.info("번역 단계 시작")
        translated_text = await translate_text(original_text)
        logger.info(f"번역 완료 (번역된 텍스트 길이: {len(translated_text)}자)")

        # 3. AI로 SEO 키워드 추출
        logger.info("SEO 키워드 추출 시작")
        extracted_keywords = await extract_seo_keywords(translated_text)
        logger.info(f"키워드 추출 완료: {extracted_keywords}")

        # 3-1. 선택된 RULE/모드 확인 (없으면 기본값)
        selected_rules = req.rules or []
        selected_mode = req.ai_mode or None
        policy_auto = req.policy_auto or False
        logger.info(f"선택된 RULE: {selected_rules}, MODE: {selected_mode}, POLICY 자동: {policy_auto}")

        # 3-2. RULE/모드에 따른 가이드라인 텍스트 생성
        rule_guidelines = []
        for rule in selected_rules:
            if rule in AI_RULES:
                if isinstance(AI_RULES[rule], list):
                    rule_guidelines.extend(AI_RULES[rule])
        if selected_mode and selected_mode in AI_RULES.get("AI_MODE", {}):
            rule_guidelines.extend(AI_RULES["AI_MODE"][selected_mode])
        # POLICY 자동 적용
        if policy_auto and "POLICY" in AI_RULES:
            rule_guidelines.extend(AI_RULES["POLICY"])
        logger.info(f"적용할 가이드라인: {rule_guidelines}")

        # 4. 추출된 키워드를 사용하여 AI로 최종 블로그 포스트 생성 (가이드라인 추가)
        logger.info("블로그 포스트 생성 시작")
        final_post_html = await generate_ai_post(translated_text, extracted_keywords, rule_guidelines)
        logger.info(f"블로그 포스트 생성 완료 (생성된 콘텐츠 길이: {len(final_post_html)}자)")

        # 5. 메타데이터 추출
        title = crud.extract_title_from_html(final_post_html)
        meta_description = crud.extract_meta_description_from_html(final_post_html)
        word_count = crud._count_words(final_post_html)

        # 6. 생성된 콘텐츠에 원문 링크 추가 (URL 입력 시에만)
        final_post_with_source = final_post_html
        if req.url:
            source_link_html = f'<hr><p><br><strong>원문 링크 : </strong><a href="{req.url}" target="_blank" rel="noopener noreferrer">{req.url}</a></p>'
            final_post_with_source += source_link_html
        
        # 7. DB에 최종본 저장
        logger.info("데이터베이스에 포스트 저장 시작")
        saved_post = crud.create_blog_post(
            db=db,
            title=title,
            original_url=db_source_url,
            keywords=extracted_keywords,
            content_html=final_post_with_source,
            meta_description=meta_description,
            word_count=word_count
        )
        logger.info(f"데이터베이스 저장 완료 (ID: {saved_post.id})")
        
        return PostResponse(
            post=final_post_with_source,
            keywords=extracted_keywords,
            title=title,
            meta_description=meta_description,
            word_count=word_count
        )

    except exceptions.BlogGeneratorException as e:
        logger.error(f"블로그 생성 중 오류 발생: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except HTTPException:
        # 이미 HTTPException인 경우 그대로 재발생
        raise
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"서버 내부 오류가 발생했습니다: {str(e)}"
        )

@router.post("/generate-post-gemini", response_model=PostResponse)
async def generate_post_gemini(req: PostRequest, db: Session = Depends(get_db)):
    """
    URL+텍스트 복합 입력, Gemini 번역 API, 1000~2000자 제한
    KOR 콘텐츠 입력(한국어 입력)일 경우 번역 없이 요약/가이드라인만 적용
    """
    try:
        original_text = ""
        db_source_url = ""
        # 1. 입력 데이터 처리 (URL, 텍스트, URL+텍스트 모두 지원)
        url_input = req.url.strip() if req.url else ""
        text_input = req.text.strip() if req.text else ""
        if url_input and text_input:
            db_source_url = url_input
            url_text = await get_text_from_url(url_input)
            original_text = (url_text or "") + "\n" + text_input
        elif url_input:
            db_source_url = url_input
            original_text = await get_text_from_url(url_input)
        elif text_input:
            db_source_url = "텍스트 직접 입력"
            original_text = text_input
        else:
            raise HTTPException(status_code=400, detail="URL 또는 텍스트를 입력해야 합니다.")

        # 2. KOR 콘텐츠 입력(한국어 입력) 분기: 번역 없이 요약/가이드라인만 적용
        import re
        def is_korean(text):
            return bool(re.search(r"[가-힣]", text or ""))
        is_kor = is_korean(original_text)
        if is_kor:
            logger.info("KOR 콘텐츠 입력: 번역 없이 Gemini 요약 및 가이드라인 적용")
            translated_text = original_text
        else:
            # Gemini 번역 (임시: DeepL 대신, 실제 Gemini 연동 필요)
            translated_text = await translate_text_gemini(original_text)
            increase_api_usage_count('gemini')

        # 3. 키워드 추출 (기존 방식)
        extracted_keywords = await extract_seo_keywords(translated_text)
        # 4. AI로 최종 블로그 포스트 생성 (기존 방식)
        # RULE/가이드라인 적용
        selected_rules = req.rules or []
        selected_mode = req.ai_mode or None
        policy_auto = req.policy_auto or False
        rule_guidelines = []
        for rule in selected_rules:
            if rule in AI_RULES:
                if isinstance(AI_RULES[rule], list):
                    rule_guidelines.extend(AI_RULES[rule])
        if selected_mode and selected_mode in AI_RULES.get("AI_MODE", {}):
            rule_guidelines.extend(AI_RULES["AI_MODE"][selected_mode])
        if policy_auto and "POLICY" in AI_RULES:
            rule_guidelines.extend(AI_RULES["POLICY"])
        final_post_html = await generate_ai_post(translated_text, extracted_keywords, rule_guidelines)
        # 5. 1000~2000자 이내로 자르기
        if len(final_post_html) > 2000:
            final_post_html = final_post_html[:2000]
        elif len(final_post_html) < 1000:
            final_post_html = final_post_html  # 너무 짧으면 그대로 반환(프론트에서 안내)
        # 6. 메타데이터 추출
        title = crud.extract_title_from_html(final_post_html)
        meta_description = crud.extract_meta_description_from_html(final_post_html)
        word_count = crud._count_words(final_post_html)
        # 7. DB 저장
        saved_post = crud.create_blog_post(
            db=db,
            title=title,
            original_url=db_source_url,
            keywords=extracted_keywords,
            content_html=final_post_html,
            meta_description=meta_description,
            word_count=word_count
        )
        return PostResponse(
            post=final_post_html,
            keywords=extracted_keywords,
            title=title,
            meta_description=meta_description,
            word_count=word_count
        )
    except Exception as e:
        logger.error(f"Gemini 복합 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini 복합 생성 오류: {e}")

@router.get("/posts", response_model=list[BlogPostResponse])
async def get_posts(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    생성된 모든 블로그 포스트 목록을 가져옵니다.
    """
    try:
        posts = crud.get_blog_posts(db, skip=skip, limit=limit)
        return posts
    except Exception as e:
        logger.error(f"포스트 목록 조회 중 오류 발생: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="포스트 목록을 불러오는 중 오류가 발생했습니다."
        )

@router.get("/posts/{post_id}", response_model=BlogPostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """
    특정 블로그 포스트를 가져옵니다.
    """
    try:
        post = crud.get_blog_post_by_id(db, post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="포스트를 찾을 수 없습니다."
            )
        return post
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"포스트 조회 중 오류 발생 (ID: {post_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="포스트를 불러오는 중 오류가 발생했습니다."
        )

@router.delete("/posts/{post_id}")
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    """
    특정 블로그 포스트를 삭제합니다.
    """
    try:
        success = crud.delete_blog_post(db, post_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="삭제할 포스트를 찾을 수 없습니다."
            )
        return {"message": "포스트가 성공적으로 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"포스트 삭제 중 오류 발생 (ID: {post_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="포스트 삭제 중 오류가 발생했습니다."
        )

@router.get("/search", response_model=list[BlogPostResponse])
async def search_posts(
    keyword: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    키워드로 블로그 포스트를 검색합니다.
    """
    try:
        posts = crud.search_blog_posts(db, keyword, skip=skip, limit=limit)
        return posts
    except Exception as e:
        logger.error(f"포스트 검색 중 오류 발생 (키워드: {keyword}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="포스트 검색 중 오류가 발생했습니다."
        )

@router.post("/admin/posts/bulk-delete")
async def bulk_delete_posts(post_ids: dict, db: Session = Depends(get_db)):
    """
    선택한 포스트들을 일괄 삭제합니다.
    {"post_ids": [1,2,3]}
    """
    ids = post_ids.get("post_ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="삭제할 포스트 ID가 필요합니다.")
    crud.bulk_delete_posts(db, ids)
    return {"message": "삭제 완료"}

@router.get("/admin/posts/export", response_model=list[dict])
async def export_posts(ids: Optional[str] = None, db: Session = Depends(get_db)):
    """
    선택한 포스트(또는 전체) 내보내기 (JSON)
    ids=1,2,3
    """
    id_list = [int(i) for i in ids.split(",") if i.strip()] if ids else None
    posts = crud.export_posts(db, id_list)
    return posts

@router.get("/admin/posts/export-xlsx")
async def export_posts_xlsx(ids: Optional[str] = None, db: Session = Depends(get_db)):
    """
    선택한 포스트(또는 전체) 엑셀(xlsx)로 내보내기
    ids=1,2,3
    """
    id_list = [int(i) for i in ids.split(",") if i.strip()] if ids else None
    posts = crud.export_posts(db, id_list)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Posts"
    # 헤더
    ws.append(["ID", "제목", "원문URL", "키워드", "메타설명", "단어수", "생성일", "수정일"])
    for p in posts:
        ws.append([
            p["id"],
            p["title"],
            p["original_url"],
            p["keywords"],
            p["meta_description"],
            p["word_count"],
            p["created_at"],
            p["updated_at"]
        ])
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=posts.xlsx"})

@router.post("/admin/posts/import")
async def import_posts(posts: list[dict], db: Session = Depends(get_db)):
    """
    포스트 복원(가져오기) - JSON 리스트
    """
    if not posts:
        raise HTTPException(status_code=400, detail="가져올 포스트 데이터가 필요합니다.")
    crud.import_posts(db, posts)
    return {"message": "복원 완료"}