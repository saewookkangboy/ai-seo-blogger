from fastapi import HTTPException

class BlogGeneratorException(Exception):
    """블로그 생성기 기본 예외 클래스"""
    pass

class TranslationError(BlogGeneratorException):
    """번역 관련 오류"""
    pass

class ContentGenerationError(BlogGeneratorException):
    """콘텐츠 생성 관련 오류"""
    pass

class CrawlingError(BlogGeneratorException):
    """웹 크롤링 관련 오류"""
    pass

class APIKeyError(BlogGeneratorException):
    """API 키 관련 오류"""
    pass

def handle_blog_generator_exception(exc: BlogGeneratorException) -> HTTPException:
    """BlogGeneratorException을 HTTPException으로 변환"""
    if isinstance(exc, TranslationError):
        return HTTPException(status_code=500, detail=f"번역 오류: {str(exc)}")
    elif isinstance(exc, ContentGenerationError):
        return HTTPException(status_code=500, detail=f"콘텐츠 생성 오류: {str(exc)}")
    elif isinstance(exc, CrawlingError):
        return HTTPException(status_code=400, detail=f"크롤링 오류: {str(exc)}")
    elif isinstance(exc, APIKeyError):
        return HTTPException(status_code=500, detail=f"API 키 오류: {str(exc)}")
    else:
        return HTTPException(status_code=500, detail=f"알 수 없는 오류: {str(exc)}") 