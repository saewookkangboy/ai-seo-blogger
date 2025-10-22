#!/bin/bash

# AWS AI SEO Blogger 배포 스크립트
# 사용법: ./aws-deploy.sh [환경] [리전]
# 예시: ./aws-deploy.sh production us-east-1

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
ENVIRONMENT=${1:-production}
AWS_REGION=${2:-us-east-1}
PROJECT_NAME="ai-seo-blogger"
ECR_REPOSITORY="${PROJECT_NAME}-${ENVIRONMENT}"
ECS_CLUSTER="${PROJECT_NAME}-cluster-${ENVIRONMENT}"
ECS_SERVICE="${PROJECT_NAME}-service-${ENVIRONMENT}"
TASK_DEFINITION="${PROJECT_NAME}-task-${ENVIRONMENT}"

log_info "AWS AI SEO Blogger 배포 시작"
log_info "환경: $ENVIRONMENT"
log_info "리전: $AWS_REGION"
log_info "프로젝트명: $PROJECT_NAME"

# AWS CLI 설정 확인
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    log_error "AWS CLI가 설정되지 않았습니다. 'aws configure'를 실행하세요."
    exit 1
fi

# 현재 AWS 계정 정보 출력
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
log_info "AWS 계정 ID: $AWS_ACCOUNT_ID"

# ECR 리포지토리 생성
log_info "ECR 리포지토리 생성 중..."
if ! aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION > /dev/null 2>&1; then
    aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION
    log_success "ECR 리포지토리 생성 완료: $ECR_REPOSITORY"
else
    log_info "ECR 리포지토리가 이미 존재합니다: $ECR_REPOSITORY"
fi

# Docker 이미지 빌드 및 푸시
log_info "Docker 이미지 빌드 중..."
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

# ECR 로그인
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

# 이미지 빌드
docker build -t $PROJECT_NAME .

# 이미지 태깅
docker tag $PROJECT_NAME:latest $ECR_URI:latest
docker tag $PROJECT_NAME:latest $ECR_URI:$(date +%Y%m%d-%H%M%S)

# 이미지 푸시
log_info "Docker 이미지 푸시 중..."
docker push $ECR_URI:latest
docker push $ECR_URI:$(date +%Y%m%d-%H%M%S)

log_success "Docker 이미지 푸시 완료"

# ECS 클러스터 생성
log_info "ECS 클러스터 생성 중..."
if ! aws ecs describe-clusters --clusters $ECS_CLUSTER --region $AWS_REGION > /dev/null 2>&1; then
    aws ecs create-cluster --cluster-name $ECS_CLUSTER --region $AWS_REGION
    log_success "ECS 클러스터 생성 완료: $ECS_CLUSTER"
else
    log_info "ECS 클러스터가 이미 존재합니다: $ECS_CLUSTER"
fi

log_success "AWS 배포 준비 완료!"
log_info "다음 단계:"
log_info "1. RDS 데이터베이스 설정"
log_info "2. Application Load Balancer 설정"
log_info "3. ECS 서비스 배포"
log_info "4. 도메인 연결"

echo ""
log_info "ECR URI: $ECR_URI"
log_info "ECS 클러스터: $ECS_CLUSTER"
