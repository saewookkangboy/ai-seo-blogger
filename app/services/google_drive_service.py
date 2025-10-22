import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
import io
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..models import BlogPost, APIKey, KeywordList, FeatureUpdate

logger = logging.getLogger(__name__)

class GoogleDriveService:
    """Google Drive API를 사용하여 데이터베이스 산출물을 관리하는 서비스"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, credentials_path: str = None, token_path: str = None):
        from ..config import settings
        
        self.credentials_path = credentials_path or settings.google_drive_credentials_path
        self.token_path = token_path or settings.google_drive_token_path
        self.client_id = settings.google_drive_client_id
        self.client_secret = settings.google_drive_client_secret
        self.service = None
        self.folder_id = None
        self.blog_generator_folder_id = None
        
    def authenticate(self) -> bool:
        """Google Drive API 인증을 수행합니다."""
        try:
            creds = None
            
            # 토큰이 있으면 로드
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
            
            # 유효한 인증 정보가 없거나 만료된 경우
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # 설정에서 클라이언트 정보를 사용하여 인증
                    if self.client_id and self.client_secret and self.client_secret != "YOUR_CLIENT_SECRET":
                        # 클라이언트 정보로 직접 인증
                        client_config = {
                            "installed": {
                                "client_id": self.client_id,
                                "client_secret": self.client_secret,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                                "redirect_uris": ["http://localhost"]
                            }
                        }
                        
                        flow = InstalledAppFlow.from_client_config(client_config, self.SCOPES)
                        creds = flow.run_local_server(port=0)
                    else:
                        # 기존 credentials.json 파일 사용
                        if not os.path.exists(self.credentials_path):
                            logger.error(f"credentials.json 파일을 찾을 수 없습니다: {self.credentials_path}")
                            return False
                        
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_path, self.SCOPES)
                        creds = flow.run_local_server(port=0)
                
                # 토큰 저장
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Google Drive API 인증 성공")
            return True
            
        except Exception as e:
            logger.error(f"Google Drive API 인증 실패: {e}")
            return False
    
    def create_folder(self, folder_name: str, parent_folder_id: str = None) -> Optional[str]:
        """Google Drive에 폴더를 생성합니다."""
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            file = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            folder_id = file.get('id')
            logger.info(f"폴더 생성 완료: {folder_name} (ID: {folder_id})")
            return folder_id
            
        except HttpError as e:
            logger.error(f"폴더 생성 실패: {e}")
            return None
    
    def get_or_create_blog_generator_folder(self) -> Optional[str]:
        """blog_generator 폴더를 가져오거나 생성합니다."""
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            
            # 기존 blog_generator 폴더 검색
            query = "name='blog_generator' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            files = results.get('files', [])
            
            if files:
                # 기존 폴더가 있으면 첫 번째 폴더 사용
                folder_id = files[0]['id']
                self.blog_generator_folder_id = folder_id
                logger.info(f"기존 blog_generator 폴더 사용: {folder_id}")
                return folder_id
            else:
                # 폴더가 없으면 새로 생성
                folder_id = self.create_folder("blog_generator")
                self.blog_generator_folder_id = folder_id
                logger.info(f"새로운 blog_generator 폴더 생성: {folder_id}")
                return folder_id
                
        except Exception as e:
            logger.error(f"blog_generator 폴더 관리 실패: {e}")
            return None
    
    def move_file_to_blog_generator(self, file_id: str) -> bool:
        """파일을 blog_generator 폴더로 이동합니다."""
        try:
            if not self.service:
                if not self.authenticate():
                    return False
            
            # blog_generator 폴더 ID 가져오기
            if not self.blog_generator_folder_id:
                self.get_or_create_blog_generator_folder()
            
            if not self.blog_generator_folder_id:
                logger.error("blog_generator 폴더를 찾을 수 없습니다.")
                return False
            
            # 파일을 blog_generator 폴더로 이동
            file = self.service.files().update(
                fileId=file_id,
                addParents=self.blog_generator_folder_id,
                removeParents='root',
                fields='id, parents'
            ).execute()
            
            logger.info(f"파일 이동 완료: {file_id} -> blog_generator 폴더")
            return True
            
        except Exception as e:
            logger.error(f"파일 이동 실패: {e}")
            return False
    
    def upload_file(self, file_path: str, folder_id: str = None, file_name: str = None) -> Optional[str]:
        """파일을 Google Drive에 업로드합니다."""
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            
            if not file_name:
                file_name = os.path.basename(file_path)
            
            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"파일 업로드 완료: {file_name} (ID: {file_id})")
            return file_id
            
        except HttpError as e:
            logger.error(f"파일 업로드 실패: {e}")
            return None
    
    def upload_dataframe(self, df: pd.DataFrame, file_name: str, folder_id: str = None) -> Optional[str]:
        """DataFrame을 CSV 파일로 변환하여 Google Drive에 업로드합니다."""
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            
            # DataFrame을 CSV로 변환
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_buffer.seek(0)
            
            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaIoBaseUpload(
                io.BytesIO(csv_buffer.getvalue().encode('utf-8-sig')),
                mimetype='text/csv',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"DataFrame 업로드 완료: {file_name} (ID: {file_id})")
            return file_id
            
        except Exception as e:
            logger.error(f"DataFrame 업로드 실패: {e}")
            return None
    
    def export_database_to_drive(self, db: Session, folder_name: str = None) -> Dict[str, Any]:
        """데이터베이스의 모든 테이블을 Google Drive에 내보냅니다."""
        try:
            if not folder_name:
                folder_name = f"AI_SEO_Blogger_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # blog_generator 폴더 가져오기 또는 생성
            blog_generator_folder_id = self.get_or_create_blog_generator_folder()
            if not blog_generator_folder_id:
                return {"success": False, "error": "blog_generator 폴더 생성 실패"}
            
            # 메인 폴더를 blog_generator 폴더 안에 생성
            main_folder_id = self.create_folder(folder_name, blog_generator_folder_id)
            if not main_folder_id:
                return {"success": False, "error": "메인 폴더 생성 실패"}
            
            results = {
                "success": True,
                "folder_id": main_folder_id,
                "folder_name": folder_name,
                "files": []
            }
            
            # 1. 블로그 포스트 데이터 내보내기
            blog_posts = db.query(BlogPost).all()
            if blog_posts:
                blog_data = []
                for post in blog_posts:
                    blog_data.append({
                        'id': post.id,
                        'title': post.title,
                        'original_url': post.original_url,
                        'keywords': post.keywords,
                        'meta_description': post.meta_description,
                        'word_count': post.word_count,
                        'content_length': post.content_length,
                        'category': post.category,
                        'status': post.status,
                        'description': post.description,
                        'created_at': post.created_at.isoformat() if post.created_at else None,
                        'updated_at': post.updated_at.isoformat() if post.updated_at else None
                    })
                
                df_blog = pd.DataFrame(blog_data)
                file_id = self.upload_dataframe(
                    df_blog, 
                    f"blog_posts_{datetime.now().strftime('%Y%m%d')}.csv",
                    main_folder_id
                )
                if file_id:
                    results["files"].append({
                        "name": "blog_posts.csv",
                        "id": file_id,
                        "count": len(blog_data)
                    })
            
            # 2. API 키 데이터 내보내기
            api_keys = db.query(APIKey).all()
            if api_keys:
                api_data = []
                for key in api_keys:
                    api_data.append({
                        'id': key.id,
                        'service': key.service,
                        'description': key.description,
                        'is_active': key.is_active,
                        'created_at': key.created_at.isoformat() if key.created_at else None,
                        'updated_at': key.updated_at.isoformat() if key.updated_at else None
                    })
                
                df_api = pd.DataFrame(api_data)
                file_id = self.upload_dataframe(
                    df_api,
                    f"api_keys_{datetime.now().strftime('%Y%m%d')}.csv",
                    main_folder_id
                )
                if file_id:
                    results["files"].append({
                        "name": "api_keys.csv",
                        "id": file_id,
                        "count": len(api_data)
                    })
            
            # 3. 키워드 리스트 데이터 내보내기
            keywords = db.query(KeywordList).all()
            if keywords:
                keyword_data = []
                for kw in keywords:
                    keyword_data.append({
                        'id': kw.id,
                        'type': kw.type,
                        'keyword': kw.keyword,
                        'created_at': kw.created_at.isoformat() if kw.created_at else None,
                        'updated_at': kw.updated_at.isoformat() if kw.updated_at else None
                    })
                
                df_keywords = pd.DataFrame(keyword_data)
                file_id = self.upload_dataframe(
                    df_keywords,
                    f"keyword_list_{datetime.now().strftime('%Y%m%d')}.csv",
                    main_folder_id
                )
                if file_id:
                    results["files"].append({
                        "name": "keyword_list.csv",
                        "id": file_id,
                        "count": len(keyword_data)
                    })
            
            # 4. 기능 업데이트 데이터 내보내기
            updates = db.query(FeatureUpdate).all()
            if updates:
                update_data = []
                for update in updates:
                    update_data.append({
                        'id': update.id,
                        'date': update.date.isoformat() if update.date else None,
                        'content': update.content,
                        'created_at': update.created_at.isoformat() if update.created_at else None
                    })
                
                df_updates = pd.DataFrame(update_data)
                file_id = self.upload_dataframe(
                    df_updates,
                    f"feature_updates_{datetime.now().strftime('%Y%m%d')}.csv",
                    main_folder_id
                )
                if file_id:
                    results["files"].append({
                        "name": "feature_updates.csv",
                        "id": file_id,
                        "count": len(update_data)
                    })
            
            # 5. 시스템 통계 리포트 생성
            stats = self._generate_system_stats(db)
            stats_json = json.dumps(stats, ensure_ascii=False, indent=2, default=str)
            
            file_metadata = {
                'name': f"system_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                'parents': [main_folder_id]
            }
            
            media = MediaIoBaseUpload(
                io.BytesIO(stats_json.encode('utf-8')),
                mimetype='application/json',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            results["files"].append({
                "name": "system_stats.json",
                "id": file.get('id'),
                "count": 1
            })
            
            logger.info(f"데이터베이스 내보내기 완료: {folder_name}")
            return results
            
        except Exception as e:
            logger.error(f"데이터베이스 내보내기 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_system_stats(self, db: Session) -> Dict[str, Any]:
        """시스템 통계를 생성합니다."""
        try:
            # 기본 통계
            total_posts = db.query(BlogPost).count()
            published_posts = db.query(BlogPost).filter(BlogPost.status == 'published').count()
            draft_posts = db.query(BlogPost).filter(BlogPost.status == 'draft').count()
            
            # 카테고리별 통계
            from sqlalchemy import func
            category_stats = db.query(
                BlogPost.category,
                func.count(BlogPost.id).label('count')
            ).group_by(BlogPost.category).all()
            
            # 월별 생성 통계
            from sqlalchemy import func
            monthly_stats = db.query(
                func.strftime('%Y-%m', BlogPost.created_at).label('month'),
                func.count(BlogPost.id).label('count')
            ).group_by('month').order_by('month').all()
            
            # 키워드 통계
            blacklist_count = db.query(KeywordList).filter(KeywordList.type == 'blacklist').count()
            whitelist_count = db.query(KeywordList).filter(KeywordList.type == 'whitelist').count()
            
            # API 키 통계
            active_api_keys = db.query(APIKey).filter(APIKey.is_active == True).count()
            total_api_keys = db.query(APIKey).count()
            
            stats = {
                "export_date": datetime.now().isoformat(),
                "total_posts": total_posts,
                "published_posts": published_posts,
                "draft_posts": draft_posts,
                "categories": [{"category": cat, "count": count} for cat, count in category_stats],
                "monthly_growth": [{"month": month, "count": count} for month, count in monthly_stats],
                "keywords": {
                    "blacklist_count": blacklist_count,
                    "whitelist_count": whitelist_count
                },
                "api_keys": {
                    "active": active_api_keys,
                    "total": total_api_keys
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"시스템 통계 생성 실패: {e}")
            return {"error": str(e)}
    
    def schedule_auto_backup(self, db: Session, schedule_type: str = "daily") -> Dict[str, Any]:
        """자동 백업을 스케줄링합니다."""
        try:
            folder_name = f"AutoBackup_{schedule_type}_{datetime.now().strftime('%Y%m%d')}"
            result = self.export_database_to_drive(db, folder_name)
            
            if result["success"]:
                logger.info(f"자동 백업 완료: {folder_name}")
                return {
                    "success": True,
                    "message": f"{schedule_type} 자동 백업이 완료되었습니다.",
                    "folder_id": result["folder_id"],
                    "files_count": len(result["files"])
                }
            else:
                return {
                    "success": False,
                    "message": "자동 백업에 실패했습니다.",
                    "error": result.get("error", "Unknown error")
                }
                
        except Exception as e:
            logger.error(f"자동 백업 실패: {e}")
            return {
                "success": False,
                "message": "자동 백업 중 오류가 발생했습니다.",
                "error": str(e)
            }
    
    def organize_existing_files(self) -> Dict[str, Any]:
        """기존 파일들을 blog_generator 폴더로 정리합니다."""
        try:
            if not self.service:
                if not self.authenticate():
                    return {"success": False, "error": "인증 실패"}
            
            # blog_generator 폴더 가져오기 또는 생성
            blog_generator_folder_id = self.get_or_create_blog_generator_folder()
            if not blog_generator_folder_id:
                return {"success": False, "error": "blog_generator 폴더 생성 실패"}
            
            # 루트에 있는 AI SEO Blogger 관련 파일들 검색
            query = "(name contains 'AI_SEO_Blogger' or name contains 'Test_Export' or name contains 'AutoBackup' or name contains 'test_dataframe' or name contains 'system_stats') and trashed=false"
            results = self.service.files().list(q=query, fields="files(id, name, parents)").execute()
            files = results.get('files', [])
            
            moved_count = 0
            for file in files:
                # 이미 blog_generator 폴더에 있으면 건너뛰기
                if blog_generator_folder_id in file.get('parents', []):
                    continue
                
                # 파일을 blog_generator 폴더로 이동
                try:
                    self.service.files().update(
                        fileId=file['id'],
                        addParents=blog_generator_folder_id,
                        removeParents='root',
                        fields='id, parents'
                    ).execute()
                    moved_count += 1
                    logger.info(f"파일 이동: {file['name']} -> blog_generator 폴더")
                except Exception as e:
                    logger.error(f"파일 이동 실패: {file['name']} - {e}")
            
            return {
                "success": True,
                "message": f"{moved_count}개 파일을 blog_generator 폴더로 이동했습니다.",
                "moved_count": moved_count,
                "blog_generator_folder_id": blog_generator_folder_id
            }
            
        except Exception as e:
            logger.error(f"파일 정리 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            } 