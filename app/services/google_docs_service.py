import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from ..config import settings

logger = logging.getLogger(__name__)

class GoogleDocsService:
    """Google Docs API를 사용하여 문서를 생성하고 관리하는 서비스"""
    
    # Google Docs API와 Google Drive API 모두 필요
    SCOPES = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive.file'
    ]
    
    def __init__(self, credentials_path: Optional[str] = None, token_path: Optional[str] = None):
        """Google Docs 서비스 초기화"""
        self.credentials_path: str = credentials_path or settings.google_drive_credentials_path
        self.token_path: str = token_path or settings.google_drive_token_path
        self.client_id: str = settings.google_drive_client_id
        self.client_secret: str = settings.google_drive_client_secret
        self.docs_service: Any = None
        self.drive_service: Any = None
        self.archive_folder_id: Optional[str] = None
        
    def authenticate(self) -> bool:
        """Google Docs API 인증을 수행합니다."""
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
                        if os.path.exists(self.credentials_path):
                            flow = InstalledAppFlow.from_client_config(
                                self.credentials_path, self.SCOPES
                            )
                            creds = flow.run_local_server(port=0)
                        else:
                            logger.error("인증 정보 파일을 찾을 수 없습니다.")
                            return False
            
            # 토큰 저장
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
            
            # 서비스 빌드
            self.docs_service = build('docs', 'v1', credentials=creds)
            self.drive_service = build('drive', 'v3', credentials=creds)
            
            logger.info("Google Docs API 인증 성공")
            return True
            
        except Exception as e:
            logger.error(f"Google Docs API 인증 실패: {e}")
            return False
    
    def create_archive_folder(self, folder_name: str = "AI_SEO_Blogger_Archive") -> Optional[str]:
        """Archive 폴더를 생성하고 폴더 ID를 반환합니다."""
        try:
            if not self.drive_service:
                if not self.authenticate():
                    return None
            
            # 폴더가 이미 존재하는지 확인
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(q=query).execute()
            items = results.get('files', [])
            
            if items:
                self.archive_folder_id = items[0]['id']
                logger.info(f"기존 Archive 폴더 사용: {folder_name}")
                return self.archive_folder_id
            
            # 새 폴더 생성
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            self.archive_folder_id = folder.get('id')
            logger.info(f"Archive 폴더 생성 완료: {folder_name} (ID: {self.archive_folder_id})")
            return self.archive_folder_id
            
        except Exception as e:
            logger.error(f"Archive 폴더 생성 실패: {e}")
            return None
    
    def create_blog_post_document(self, blog_post: Dict[str, Any], folder_id: Optional[str] = None) -> Optional[str]:
        """블로그 포스트를 Google Docs 문서로 생성합니다."""
        try:
            if not self.docs_service or not self.drive_service:
                if not self.authenticate():
                    return None
            
            # Archive 폴더 설정
            if not folder_id:
                if not self.archive_folder_id:
                    self.create_archive_folder()
                folder_id = self.archive_folder_id
            
            if not folder_id:
                logger.error("Archive 폴더 ID를 가져올 수 없습니다.")
                return None
            
            # 문서 제목 생성
            title = blog_post.get('title', 'AI 생성 블로그 포스트')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            doc_title = f"{title}_{timestamp}"
            
            # Google Docs 문서 생성
            doc = self.docs_service.documents().create(
                body={'title': doc_title}
            ).execute()
            
            doc_id = doc.get('documentId')
            logger.info(f"Google Docs 문서 생성: {doc_title} (ID: {doc_id})")
            
            # 문서 내용 작성
            self._write_blog_content_to_doc(doc_id, blog_post)
            
            # Drive에서 폴더로 이동
            if folder_id:
                self._move_document_to_folder(doc_id, folder_id)
            
            # 문서 URL 생성
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            
            logger.info(f"블로그 포스트 Archive 완료: {doc_url}")
            return doc_url
            
        except Exception as e:
            logger.error(f"블로그 포스트 문서 생성 실패: {e}")
            return None
    
    def _write_blog_content_to_doc(self, doc_id: str, blog_post: Dict[str, Any]):
        """블로그 포스트 내용을 Google Docs에 작성합니다."""
        try:
            # 문서 구조 생성
            requests = []
            
            # 제목 추가
            title = blog_post.get('title', 'AI 생성 블로그 포스트')
            requests.append({
                'insertText': {
                    'location': {'index': 1},
                    'text': f"{title}\n\n"
                }
            })
            
            # 제목 스타일링
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': 1, 'endIndex': len(title) + 1},
                    'textStyle': {
                        'bold': True,
                        'fontSize': {'magnitude': 18, 'unit': 'PT'}
                    },
                    'fields': 'bold,fontSize'
                }
            })
            
            # 메타데이터 추가
            current_index = len(title) + 3
            
            # 키워드
            keywords = blog_post.get('keywords', '')
            if keywords:
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': f"키워드: {keywords}\n"
                    }
                })
                current_index += len(f"키워드: {keywords}\n")
            
            # 생성 날짜
            created_date = datetime.now().strftime('%Y년 %m월 %d일 %H:%M')
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': f"생성일: {created_date}\n\n"
                }
            })
            current_index += len(f"생성일: {created_date}\n\n")
            
            # 소스 URL
            source_url = blog_post.get('source_url', '')
            if source_url:
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': f"출처: {source_url}\n\n"
                    }
                })
                current_index += len(f"출처: {source_url}\n\n")
            
            # AI 모드
            ai_mode = blog_post.get('ai_mode', '')
            if ai_mode:
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': f"AI 모드: {ai_mode}\n\n"
                    }
                })
                current_index += len(f"AI 모드: {ai_mode}\n\n")
            
            # 구분선
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': "=" * 50 + "\n\n"
                }
            })
            current_index += len("=" * 50 + "\n\n")
            
            # 본문 내용
            content = blog_post.get('content', '')
            if content:
                # HTML 태그 제거 및 텍스트 정리
                import re
                clean_content = re.sub(r'<[^>]+>', '', content)
                clean_content = clean_content.replace('&nbsp;', ' ')
                clean_content = clean_content.replace('&amp;', '&')
                clean_content = clean_content.replace('&lt;', '<')
                clean_content = clean_content.replace('&gt;', '>')
                
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': clean_content + "\n\n"
                    }
                })
            
            # 요약 (있는 경우)
            summary = blog_post.get('summary', '')
            if summary:
                requests.append({
                    'insertText': {
                        'location': {'index': current_index + len(clean_content) + 2},
                        'text': f"\n\n요약:\n{summary}\n"
                    }
                })
            
            # 요청 실행
            if requests:
                self.docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()
            
            logger.info(f"문서 내용 작성 완료: {doc_id}")
            
        except Exception as e:
            logger.error(f"문서 내용 작성 실패: {e}")
    
    def _move_document_to_folder(self, doc_id: str, folder_id: str):
        """문서를 지정된 폴더로 이동합니다."""
        try:
            # 현재 파일의 부모 폴더 정보 가져오기
            file = self.drive_service.files().get(
                fileId=doc_id,
                fields='parents'
            ).execute()
            
            previous_parents = ",".join(file.get('parents'))
            
            # 파일을 새 폴더로 이동
            self.drive_service.files().update(
                fileId=doc_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            
            logger.info(f"문서를 폴더로 이동 완료: {doc_id} -> {folder_id}")
            
        except Exception as e:
            logger.error(f"문서 폴더 이동 실패: {e}")
    
    def get_archive_documents(self, folder_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Archive 폴더의 문서 목록을 가져옵니다."""
        try:
            if not self.drive_service:
                if not self.authenticate():
                    return []
            
            if not folder_id:
                if not self.archive_folder_id:
                    self.create_archive_folder()
                folder_id = self.archive_folder_id
            
            if not folder_id:
                logger.error("Archive 폴더 ID를 가져올 수 없습니다.")
                return []
            
            # 폴더 내 문서 검색
            query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document' and trashed=false"
            results = self.drive_service.files().list(
                q=query,
                orderBy='createdTime desc',
                pageSize=limit,
                fields='files(id, name, createdTime, modifiedTime, webViewLink)'
            ).execute()
            
            documents = []
            for file in results.get('files', []):
                documents.append({
                    'id': file['id'],
                    'name': file['name'],
                    'created_time': file['createdTime'],
                    'modified_time': file['modifiedTime'],
                    'url': file['webViewLink']
                })
            
            logger.info(f"Archive 문서 목록 조회 완료: {len(documents)}개")
            return documents
            
        except Exception as e:
            logger.error(f"Archive 문서 목록 조회 실패: {e}")
            return []
    
    def delete_archive_document(self, doc_id: str) -> bool:
        """Archive 문서를 삭제합니다."""
        try:
            if not self.drive_service:
                if not self.authenticate():
                    return False
            
            self.drive_service.files().delete(fileId=doc_id).execute()
            logger.info(f"Archive 문서 삭제 완료: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Archive 문서 삭제 실패: {e}")
            return False

# 전역 서비스 인스턴스
google_docs_service = GoogleDocsService()
