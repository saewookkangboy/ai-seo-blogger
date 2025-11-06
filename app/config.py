import os
import sys
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Python 바이트코드 캐시 비활성화 (시스템 최적화)
sys.dont_write_bytecode = True

load_dotenv()

class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # API Keys
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = "AIzaSyDsBBgP9R8NrLaseWWFDcdYFGrrUNbIX9A"
    deepl_api_key: Optional[str] = None
    
    # Database
    database_url: str = "sqlite:///./blog.db"
    
    # Application
    app_name: str = "AI SEO Blogger"
    debug: bool = True  # 개발 환경에서 테스트 세션 사용을 위해 True로 설정
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_prefix = ""
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 환경 변수에서 DEBUG 값을 직접 확인
        import os
        env_debug = os.getenv('DEBUG', 'False').lower() == 'true'
        if env_debug:
            self.debug = True
    
    # API Settings
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.7
    
    # Gemini API Settings (2.0 Flash 지원)
    gemini_model: str = "gemini-2.0-flash"  # Gemini 2.0 Flash 모델
    gemini_max_tokens: int = 8192  # Gemini 2.0 Flash는 더 큰 토큰 제한
    gemini_temperature: float = 0.7
    
    # Translation
    default_target_language: str = "KO"
    
    # Crawler
    request_timeout: int = 10
    max_text_length: int = 8000
    
    # Admin
    admin_username: str = "admin"
    admin_password: str = "admin123"
    
    # 네이버 검색광고 API 연동용
    naver_client_id: Optional[str] = None
    naver_client_secret: Optional[str] = None
    
    # Google Drive API 설정
    google_drive_client_id: str = "1050278621988-s7bg1k15tm114icvq2ad8aa49ohj2q5t.apps.googleusercontent.com"
    google_drive_client_secret: str = "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"
    google_drive_credentials_path: str = "credentials.json"
    google_drive_token_path: str = "token.json"
    google_drive_backup_folder: str = "AI_SEO_Blogger_Backups"
    google_drive_auto_backup: bool = True
    google_drive_backup_schedule: str = "daily"
    google_drive_backup_retention_days: int = 30
    
    # Google Docs Archive 설정
    google_docs_archive_enabled: bool = True
    google_docs_archive_folder: str = "AI_SEO_Blogger_Archive"
    google_docs_auto_archive: bool = True
    
    # 성능 최적화 설정
    max_memory_mb: int = 1024  # 최대 메모리 사용량 (MB)
    memory_cleanup_interval: int = 300  # 메모리 정리 주기 (초)
    cache_max_size: int = 1000  # 캐시 최대 크기
    cache_default_ttl: int = 3600  # 캐시 기본 TTL (초)
    log_level: str = "INFO"  # 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    log_enable_file: bool = True  # 파일 로깅 활성화
    log_enable_console: bool = True  # 콘솔 로깅 활성화
    log_compress_after_days: int = 7  # 로그 압축 주기 (일)
    
    # 중간 우선순위 최적화 설정
    redis_url: Optional[str] = None  # Redis URL (예: redis://localhost:6379/0)
    batch_api_size: int = 10  # 배치 API 크기
    batch_api_interval: float = 0.5  # 배치 API 간격 (초)
    background_queue_workers: int = 4  # 백그라운드 작업 큐 작업자 수
    background_queue_size: int = 100  # 백그라운드 작업 큐 크기
    crawler_max_concurrent: int = 10  # 크롤러 최대 동시 처리 수
    crawler_queue_size: int = 100  # 크롤러 큐 크기
    
    # 낮은 우선순위 최적화 설정
    enable_postgresql_optimization: bool = True  # PostgreSQL 최적화 활성화
    session_storage: str = "memory"  # 세션 저장소 (memory, redis)
    enable_horizontal_scaling: bool = True  # 수평 확장 지원 활성화
    
    def validate_settings(self) -> list[str]:
        """설정 유효성 검사 (개선된 버전)"""
        errors = []
        
        # API 키가 설정되지 않았거나 기본값인 경우
        if not self.openai_api_key or not self.is_api_key_valid(self.openai_api_key):
            errors.append("OPENAI_API_KEY가 설정되지 않았거나 유효하지 않습니다.")
        
        if not self.gemini_api_key or not self.is_api_key_valid(self.gemini_api_key):
            errors.append("GEMINI_API_KEY가 설정되지 않았거나 유효하지 않습니다.")
        
        # 데이터베이스 URL 검증
        if not self.database_url:
            errors.append("DATABASE_URL가 설정되지 않았습니다.")
        
        return errors

    def is_api_key_valid(self, api_key: Optional[str]) -> bool:
        """API 키가 유효한지 확인 (개선된 버전)"""
        if not api_key:
            return False
        
        # 기본값이나 더미 값인지 확인
        invalid_patterns = [
            "your_", "dummy_", "test_", "placeholder", "example", 
            "sk-0000000000000000000000000000000000000000000000000000000000000000",
            "2f05c78b-516f-406a-a555-81c9667c193d:fx"  # DeepL API 키
        ]
        
        # 길이 검증
        if len(api_key) < 10:
            return False
            
        return not any(pattern in api_key.lower() for pattern in invalid_patterns)

    def get_openai_api_key(self) -> Optional[str]:
        """OpenAI API 키를 안전하게 반환"""
        if self.is_api_key_valid(self.openai_api_key):
            return self.openai_api_key
        return None

    def get_gemini_api_key(self) -> Optional[str]:
        """Gemini API 키를 안전하게 반환"""
        if self.is_api_key_valid(self.gemini_api_key):
            return self.gemini_api_key
        return None

    def get_deepl_api_key(self) -> Optional[str]:
        """DeepL API 키를 안전하게 반환"""
        if self.is_api_key_valid(self.deepl_api_key):
            return self.deepl_api_key
        return None

    def get_naver_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """네이버 API 자격증명을 안전하게 반환"""
        client_id = self.naver_client_id if self.is_api_key_valid(self.naver_client_id) else None
        client_secret = self.naver_client_secret if self.is_api_key_valid(self.naver_client_secret) else None
        return client_id, client_secret

# 전역 설정 인스턴스
def get_settings():
    """환경 변수를 고려한 설정 인스턴스를 반환합니다."""
    import os
    env_debug = os.getenv('DEBUG', 'False').lower() == 'true'
    settings = Settings()
    if env_debug:
        settings.debug = True
    return settings

settings = get_settings() 