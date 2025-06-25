import os
from typing import Optional, ClassVar
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # API Keys
    openai_api_key: Optional[str] = None
    deepl_api_key: Optional[str] = None
    
    # Database
    database_url: str = "sqlite:///./blog.db"
    
    # Application
    app_name: str = "AI SEO Blog Generator"
    debug: bool = False
    
    # API Settings
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.7
    
    # Translation
    default_target_language: str = "KO"
    
    # Crawler
    request_timeout: int = 10
    max_text_length: int = 8000
    
    # Admin
    admin_username: str = "admin"
    admin_password: str = "912712"
    
    # 네이버 검색광고 API 연동용 Client ID/Secret (직접 입력)
    NAVER_CLIENT_ID: ClassVar[str] = os.getenv('NAVER_CLIENT_ID', '')  # 네이버 애플리케이션 Client ID
    NAVER_CLIENT_SECRET: ClassVar[str] = os.getenv('NAVER_CLIENT_SECRET', '')  # 네이버 애플리케이션 Client Secret
    # .env 파일 또는 환경변수에 직접 입력하세요.
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def validate_settings(self) -> list[str]:
        """설정 유효성 검사"""
        errors = []
        
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY가 설정되지 않았습니다.")
        
        if not self.deepl_api_key:
            errors.append("DEEPL_API_KEY가 설정되지 않았습니다.")
        
        return errors

# 전역 설정 인스턴스
settings = Settings() 