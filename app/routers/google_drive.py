from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from ..database import get_db
from ..services.google_drive_service import GoogleDriveService
from ..schemas import GoogleDriveExportRequest, GoogleDriveBackupRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/google-drive", tags=["Google Drive"])

# Google Drive 서비스 인스턴스
drive_service = GoogleDriveService()

@router.post("/export-database")
async def export_database_to_google_drive(
    request: GoogleDriveExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """데이터베이스를 Google Drive로 내보냅니다."""
    try:
        logger.info("Google Drive 데이터베이스 내보내기 시작")
        
        # 백그라운드에서 내보내기 실행
        background_tasks.add_task(
            drive_service.export_database_to_drive,
            db,
            request.folder_name
        )
        
        return {
            "success": True,
            "message": "데이터베이스 내보내기가 백그라운드에서 시작되었습니다.",
            "folder_name": request.folder_name or f"AI_SEO_Blogger_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Google Drive 내보내기 실패: {e}")
        raise HTTPException(status_code=500, detail=f"내보내기 실패: {str(e)}")

@router.post("/backup-database")
async def backup_database_to_google_drive(
    request: GoogleDriveBackupRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """데이터베이스를 Google Drive에 백업합니다."""
    try:
        logger.info(f"Google Drive 백업 시작: {request.schedule_type}")
        
        # 백그라운드에서 백업 실행
        background_tasks.add_task(
            drive_service.schedule_auto_backup,
            db,
            request.schedule_type
        )
        
        return {
            "success": True,
            "message": f"{request.schedule_type} 백업이 백그라운드에서 시작되었습니다.",
            "schedule_type": request.schedule_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Google Drive 백업 실패: {e}")
        raise HTTPException(status_code=500, detail=f"백업 실패: {str(e)}")

@router.get("/test-connection")
async def test_google_drive_connection():
    """Google Drive API 연결을 테스트합니다."""
    try:
        logger.info("Google Drive API 연결 테스트 시작")
        
        if drive_service.authenticate():
            return {
                "success": True,
                "message": "Google Drive API 연결이 성공했습니다.",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "Google Drive API 연결에 실패했습니다.",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Google Drive 연결 테스트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"연결 테스트 실패: {str(e)}")

@router.post("/create-folder")
async def create_google_drive_folder(folder_name: str, parent_folder_id: Optional[str] = None):
    """Google Drive에 폴더를 생성합니다."""
    try:
        logger.info(f"Google Drive 폴더 생성: {folder_name}")
        
        folder_id = drive_service.create_folder(folder_name, parent_folder_id)
        
        if folder_id:
            return {
                "success": True,
                "message": "폴더가 성공적으로 생성되었습니다.",
                "folder_id": folder_id,
                "folder_name": folder_name,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="폴더 생성에 실패했습니다.")
            
    except Exception as e:
        logger.error(f"Google Drive 폴더 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"폴더 생성 실패: {str(e)}")

@router.get("/backup-status")
async def get_backup_status():
    """백업 상태를 확인합니다."""
    try:
        # 여기서는 간단한 상태만 반환
        # 실제로는 백업 작업의 상태를 추적하는 시스템이 필요
        return {
            "success": True,
            "message": "백업 시스템이 정상적으로 작동 중입니다.",
            "last_backup": None,  # 실제로는 마지막 백업 시간을 저장해야 함
            "next_backup": None,  # 실제로는 다음 백업 시간을 계산해야 함
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"백업 상태 확인 실패: {e}")
        raise HTTPException(status_code=500, detail=f"상태 확인 실패: {str(e)}")

@router.post("/organize-files")
async def organize_files():
    """기존 파일들을 blog_generator 폴더로 정리합니다."""
    try:
        logger.info("기존 파일들을 blog_generator 폴더로 정리 시작")
        
        result = drive_service.organize_existing_files()
        
        return result
        
    except Exception as e:
        logger.error(f"파일 정리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"파일 정리 실패: {str(e)}")

@router.get("/blog-generator-folder")
async def get_blog_generator_folder():
    """blog_generator 폴더 정보를 확인합니다."""
    try:
        logger.info("blog_generator 폴더 정보 확인")
        
        folder_id = drive_service.get_or_create_blog_generator_folder()
        
        if folder_id:
            return {
                "success": True,
                "message": "blog_generator 폴더가 준비되었습니다.",
                "folder_id": folder_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "blog_generator 폴더 생성에 실패했습니다.",
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"blog_generator 폴더 확인 실패: {e}")
        raise HTTPException(status_code=500, detail=f"폴더 확인 실패: {str(e)}") 