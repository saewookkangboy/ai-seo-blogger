#!/bin/bash

# AWS Secrets Manager 설정 스크립트
# AI SEO Blogger API 키들을 안전하게 저장합니다.

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 변수 설정
AWS_REGION=${1:-us-east-1}
SECRET_NAME_PREFIX="ai-seo-blogger"

log_info "AWS Secrets Manager 설정 시작"
log_info "리전: $AWS_REGION"

# AWS CLI 설정 확인
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    log_error "AWS CLI가 설정되지 않았습니다. 'aws configure'를 실행하세요."
    exit 1
fi

# OpenAI API 키 설정
log_info "OpenAI API 키 설정 중..."
read -s -p "OpenAI API 키를 입력하세요: " OPENAI_API_KEY
echo

if [ -n "$OPENAI_API_KEY" ]; then
    aws secretsmanager create-secret \
        --name "$SECRET_NAME_PREFIX/openai-api-key" \
        --description "OpenAI API Key for AI SEO Blogger" \
        --secret-string "$OPENAI_API_KEY" \
        --region $AWS_REGION \
        --tags Key=Project,Value=AI-SEO-Blogger Key=Environment,Value=Production Key=Service,Value=OpenAI \
        2>/dev/null || \
    aws secretsmanager update-secret \
        --secret-id "$SECRET_NAME_PREFIX/openai-api-key" \
        --secret-string "$OPENAI_API_KEY" \
        --region $AWS_REGION
    log_success "OpenAI API 키가 설정되었습니다."
else
    log_warning "OpenAI API 키가 입력되지 않았습니다."
fi

# Gemini API 키 설정
log_info "Gemini API 키 설정 중..."
read -s -p "Gemini API 키를 입력하세요: " GEMINI_API_KEY
echo

if [ -n "$GEMINI_API_KEY" ]; then
    aws secretsmanager create-secret \
        --name "$SECRET_NAME_PREFIX/gemini-api-key" \
        --description "Gemini API Key for AI SEO Blogger" \
        --secret-string "$GEMINI_API_KEY" \
        --region $AWS_REGION \
        --tags Key=Project,Value=AI-SEO-Blogger Key=Environment,Value=Production Key=Service,Value=Gemini \
        2>/dev/null || \
    aws secretsmanager update-secret \
        --secret-id "$SECRET_NAME_PREFIX/gemini-api-key" \
        --secret-string "$GEMINI_API_KEY" \
        --region $AWS_REGION
    log_success "Gemini API 키가 설정되었습니다."
else
    log_warning "Gemini API 키가 입력되지 않았습니다."
fi

# DeepL API 키 설정
log_info "DeepL API 키 설정 중..."
read -s -p "DeepL API 키를 입력하세요: " DEEPL_API_KEY
echo

if [ -n "$DEEPL_API_KEY" ]; then
    aws secretsmanager create-secret \
        --name "$SECRET_NAME_PREFIX/deepl-api-key" \
        --description "DeepL API Key for AI SEO Blogger" \
        --secret-string "$DEEPL_API_KEY" \
        --region $AWS_REGION \
        --tags Key=Project,Value=AI-SEO-Blogger Key=Environment,Value=Production Key=Service,Value=DeepL \
        2>/dev/null || \
    aws secretsmanager update-secret \
        --secret-id "$SECRET_NAME_PREFIX/deepl-api-key" \
        --secret-string "$DEEPL_API_KEY" \
        --region $AWS_REGION
    log_success "DeepL API 키가 설정되었습니다."
else
    log_warning "DeepL API 키가 입력되지 않았습니다."
fi

# 데이터베이스 URL 설정
log_info "데이터베이스 URL 설정 중..."
read -p "RDS 엔드포인트를 입력하세요 (예: ai-seo-blogger-db-production.xxxxx.us-east-1.rds.amazonaws.com): " RDS_ENDPOINT
read -s -p "데이터베이스 비밀번호를 입력하세요: " DB_PASSWORD
echo

if [ -n "$RDS_ENDPOINT" ] && [ -n "$DB_PASSWORD" ]; then
    DATABASE_URL="postgresql://ai_seo_user:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/ai_seo_blogger"
    
    aws secretsmanager create-secret \
        --name "$SECRET_NAME_PREFIX/database-url" \
        --description "Database URL for AI SEO Blogger" \
        --secret-string "$DATABASE_URL" \
        --region $AWS_REGION \
        --tags Key=Project,Value=AI-SEO-Blogger Key=Environment,Value=Production Key=Service,Value=Database \
        2>/dev/null || \
    aws secretsmanager update-secret \
        --secret-id "$SECRET_NAME_PREFIX/database-url" \
        --secret-string "$DATABASE_URL" \
        --region $AWS_REGION
    log_success "데이터베이스 URL이 설정되었습니다."
else
    log_warning "데이터베이스 정보가 입력되지 않았습니다."
fi

# Google Drive API 설정 (선택사항)
log_info "Google Drive API 설정 중 (선택사항)..."
read -p "Google Drive Client ID를 입력하세요 (선택사항): " GOOGLE_DRIVE_CLIENT_ID
read -s -p "Google Drive Client Secret을 입력하세요 (선택사항): " GOOGLE_DRIVE_CLIENT_SECRET
echo

if [ -n "$GOOGLE_DRIVE_CLIENT_ID" ] && [ -n "$GOOGLE_DRIVE_CLIENT_SECRET" ]; then
    GOOGLE_DRIVE_CONFIG="{\"client_id\":\"$GOOGLE_DRIVE_CLIENT_ID\",\"client_secret\":\"$GOOGLE_DRIVE_CLIENT_SECRET\"}"
    
    aws secretsmanager create-secret \
        --name "$SECRET_NAME_PREFIX/google-drive-config" \
        --description "Google Drive API Configuration for AI SEO Blogger" \
        --secret-string "$GOOGLE_DRIVE_CONFIG" \
        --region $AWS_REGION \
        --tags Key=Project,Value=AI-SEO-Blogger Key=Environment,Value=Production Key=Service,Value=GoogleDrive \
        2>/dev/null || \
    aws secretsmanager update-secret \
        --secret-id "$SECRET_NAME_PREFIX/google-drive-config" \
        --secret-string "$GOOGLE_DRIVE_CONFIG" \
        --region $AWS_REGION
    log_success "Google Drive API 설정이 완료되었습니다."
else
    log_info "Google Drive API 설정을 건너뛰었습니다."
fi

# 시크릿 목록 출력
log_info "설정된 시크릿 목록:"
aws secretsmanager list-secrets \
    --region $AWS_REGION \
    --query "SecretList[?contains(Name, '$SECRET_NAME_PREFIX')].{Name:Name,Description:Description}" \
    --output table

log_success "AWS Secrets Manager 설정이 완료되었습니다!"
log_info "다음 단계:"
log_info "1. Terraform을 사용하여 인프라 배포"
log_info "2. ECS 서비스 배포"
log_info "3. 도메인 연결 및 SSL 인증서 설정"
