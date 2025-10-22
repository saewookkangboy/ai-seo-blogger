# 🚀 AWS 실서버 배포 가이드

AI SEO Blogger 서비스를 AWS에 배포하는 완전한 가이드입니다.

## 📋 목차

1. [사전 준비](#사전-준비)
2. [AWS 인프라 설정](#aws-인프라-설정)
3. [데이터베이스 설정](#데이터베이스-설정)
4. [시크릿 관리](#시크릿-관리)
5. [애플리케이션 배포](#애플리케이션-배포)
6. [모니터링 설정](#모니터링-설정)
7. [도메인 연결](#도메인-연결)
8. [비용 최적화](#비용-최적화)

## 🔧 사전 준비

### 1. AWS 계정 설정

```bash
# AWS CLI 설치 (macOS)
brew install awscli

# AWS CLI 설정
aws configure
```

### 2. 필요한 정보

- AWS Access Key ID
- AWS Secret Access Key
- 선호하는 AWS 리전 (예: us-east-1)
- 도메인 이름 (선택사항)

## 🏗️ AWS 인프라 설정

### 1. Terraform 설치

```bash
# macOS
brew install terraform

# 또는 직접 다운로드
# https://www.terraform.io/downloads.html
```

### 2. 인프라 배포

```bash
# Terraform 디렉토리로 이동
cd aws/terraform

# 변수 파일 생성
cp terraform.tfvars.example terraform.tfvars

# terraform.tfvars 파일 편집
nano terraform.tfvars
```

**terraform.tfvars 예시:**
```hcl
aws_region = "us-east-1"
environment = "production"
project_name = "ai-seo-blogger"
db_password = "your_secure_password_here"
domain_name = "your-domain.com"
```

### 3. Terraform 실행

```bash
# 초기화
terraform init

# 계획 확인
terraform plan

# 배포 실행
terraform apply
```

## 🗄️ 데이터베이스 설정

### 1. RDS PostgreSQL 설정

Terraform이 자동으로 RDS 인스턴스를 생성합니다:

- **엔진**: PostgreSQL 15.4
- **인스턴스 클래스**: db.t3.micro
- **스토리지**: 20GB (최대 100GB 자동 확장)
- **백업**: 7일 보존
- **암호화**: 활성화

### 2. 데이터베이스 초기화

```bash
# RDS 엔드포인트 확인
terraform output rds_endpoint

# 데이터베이스 스키마 실행
psql -h <RDS_ENDPOINT> -U ai_seo_user -d ai_seo_blogger -f aws/rds-setup.sql
```

## 🔐 시크릿 관리

### 1. AWS Secrets Manager 설정

```bash
# 시크릿 설정 스크립트 실행
./aws/secrets-setup.sh us-east-1
```

### 2. 저장되는 시크릿

- `ai-seo-blogger/openai-api-key`
- `ai-seo-blogger/gemini-api-key`
- `ai-seo-blogger/deepl-api-key`
- `ai-seo-blogger/database-url`
- `ai-seo-blogger/google-drive-config` (선택사항)

## 🚀 애플리케이션 배포

### 1. ECR 리포지토리 설정

```bash
# 배포 스크립트 실행
./aws-deploy.sh production us-east-1
```

### 2. ECS 서비스 배포

```bash
# ECS 클러스터 확인
aws ecs describe-clusters --clusters ai-seo-blogger-cluster-production

# 서비스 배포
aws ecs create-service \
  --cluster ai-seo-blogger-cluster-production \
  --service-name ai-seo-blogger-service-production \
  --task-definition ai-seo-blogger-task-production \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=DISABLED}"
```

## 📊 모니터링 설정

### 1. CloudWatch 대시보드

```bash
# CloudWatch 대시보드 생성
aws cloudwatch put-dashboard \
  --dashboard-name "AI-SEO-Blogger-Production" \
  --dashboard-body file://aws/cloudwatch-dashboard.json
```

### 2. 알람 설정

```bash
# CPU 사용률 알람
aws cloudwatch put-metric-alarm \
  --alarm-name "AI-SEO-Blogger-High-CPU" \
  --alarm-description "High CPU utilization" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

## 🌐 도메인 연결

### 1. Route 53 설정

```bash
# 호스팅 영역 생성
aws route53 create-hosted-zone \
  --name your-domain.com \
  --caller-reference $(date +%s)
```

### 2. SSL 인증서 생성

```bash
# ACM 인증서 요청
aws acm request-certificate \
  --domain-name your-domain.com \
  --subject-alternative-names www.your-domain.com \
  --validation-method DNS
```

### 3. CloudFront 설정 (선택사항)

```bash
# CloudFront 배포 생성
aws cloudfront create-distribution \
  --distribution-config file://aws/cloudfront-config.json
```

## 💰 비용 최적화

### 1. 예상 월 비용

| 서비스 | 인스턴스 | 월 비용 (USD) |
|--------|----------|---------------|
| **ECS Fargate** | 2 vCPU, 4GB RAM | ~$60 |
| **RDS PostgreSQL** | db.t3.micro | ~$15 |
| **Application Load Balancer** | - | ~$20 |
| **CloudWatch** | 로그 + 메트릭 | ~$10 |
| **ECR** | 이미지 저장 | ~$5 |
| **Route 53** | 호스팅 영역 | ~$0.50 |
| **ACM** | SSL 인증서 | 무료 |
| **총 예상 비용** | - | **~$110/월** |

### 2. 비용 절약 팁

- **개발 환경**: ECS 태스크 수를 1개로 줄이기
- **RDS**: db.t3.micro 사용 (프리티어 가능)
- **스토리지**: 불필요한 로그 정리
- **자동 스케일링**: 트래픽에 따른 자동 조정

## 🔄 CI/CD 파이프라인

### 1. GitHub Actions 설정

```yaml
# .github/workflows/deploy.yml 파일이 자동으로 생성됩니다
```

### 2. 필요한 GitHub Secrets

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `DEEPL_API_KEY`

## 🛠️ 유지보수

### 1. 로그 확인

```bash
# CloudWatch 로그 확인
aws logs describe-log-groups --log-group-name-prefix "/ecs/ai-seo-blogger"

# 실시간 로그 스트리밍
aws logs tail /ecs/ai-seo-blogger --follow
```

### 2. 서비스 상태 확인

```bash
# ECS 서비스 상태
aws ecs describe-services \
  --cluster ai-seo-blogger-cluster-production \
  --services ai-seo-blogger-service-production

# 헬스체크
curl -f http://your-alb-dns-name/health
```

### 3. 백업 및 복구

```bash
# RDS 스냅샷 생성
aws rds create-db-snapshot \
  --db-instance-identifier ai-seo-blogger-db-production \
  --db-snapshot-identifier ai-seo-blogger-backup-$(date +%Y%m%d)
```

## 🚨 문제 해결

### 1. 일반적인 문제

**ECS 태스크가 시작되지 않는 경우:**
```bash
# 태스크 정의 확인
aws ecs describe-task-definition --task-definition ai-seo-blogger-task-production

# 이벤트 로그 확인
aws ecs describe-services --cluster ai-seo-blogger-cluster-production --services ai-seo-blogger-service-production
```

**데이터베이스 연결 오류:**
```bash
# 보안 그룹 확인
aws ec2 describe-security-groups --group-ids sg-xxx

# RDS 상태 확인
aws rds describe-db-instances --db-instance-identifier ai-seo-blogger-db-production
```

### 2. 로그 분석

```bash
# 애플리케이션 로그
aws logs filter-log-events \
  --log-group-name "/ecs/ai-seo-blogger" \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern "ERROR"
```

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. **CloudWatch 로그**: 애플리케이션 오류 메시지
2. **ECS 이벤트**: 태스크 시작/중지 이벤트
3. **ALB 타겟 그룹**: 헬스체크 상태
4. **RDS 상태**: 데이터베이스 연결 상태

## 🎯 다음 단계

1. **성능 모니터링**: CloudWatch 대시보드 설정
2. **자동 스케일링**: 트래픽 증가에 따른 자동 확장
3. **백업 전략**: 정기적인 데이터베이스 백업
4. **보안 강화**: WAF, Shield Advanced 설정
5. **CDN 설정**: CloudFront로 전역 가속화

---

**배포 완료 후 서비스 URL**: `http://your-alb-dns-name`

**관리자 페이지**: `http://your-alb-dns-name/admin`

**API 문서**: `http://your-alb-dns-name/docs`
