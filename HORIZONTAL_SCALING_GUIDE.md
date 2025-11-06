# 수평 확장 가이드

## 📋 개요

AI SEO Blogger 시스템을 수평 확장하여 여러 인스턴스에서 실행할 수 있도록 설정하는 가이드입니다.

## 🏗️ 스테이트리스 설계

### 현재 상태
- ✅ 헬스체크 엔드포인트 제공
- ✅ 외부 데이터베이스 사용 가능
- ✅ Redis 캐시 지원 (선택적)
- ⚠️ 메모리 세션 저장 (수평 확장 시 문제)

### 권장사항

#### 1. 세션 저장소
**현재**: 메모리 세션 저장
**권장**: Redis 세션 저장소

```python
# config.py
session_storage: str = "redis"  # memory → redis
```

#### 2. 캐시 저장소
**현재**: 메모리 캐시 (Redis fallback 지원)
**권장**: Redis 캐시 활성화

```bash
# .env
REDIS_URL=redis://localhost:6379/0
```

#### 3. 데이터베이스
**현재**: SQLite (단일 인스턴스)
**권장**: PostgreSQL (공유 데이터베이스)

```bash
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/ai_seo_blogger
```

## 🔧 로드 밸런서 설정

### 헬스체크 설정

#### 헬스체크 엔드포인트
- **Health Check**: `/health`
- **Readiness Check**: `/health/readiness`
- **Liveness Check**: `/health/liveness`

#### 권장 설정
```yaml
health_check:
  path: /health
  interval: 10  # 초
  timeout: 5    # 초
  healthy_threshold: 2
  unhealthy_threshold: 3
  grace_period: 60  # 초
```

### 로드 밸런서 설정 예시

#### Nginx 로드 밸런서
```nginx
upstream ai_seo_blogger {
    least_conn;
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name example.com;
    
    location / {
        proxy_pass http://ai_seo_blogger;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /health {
        proxy_pass http://ai_seo_blogger;
        access_log off;
    }
}
```

#### AWS Application Load Balancer
- **Health Check Path**: `/health`
- **Health Check Interval**: 10초
- **Healthy Threshold**: 2회
- **Unhealthy Threshold**: 3회
- **Timeout**: 5초

## 🚀 배포 방법

### Docker Compose (수평 확장)

```yaml
version: '3.8'

services:
  app1:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/ai_seo_blogger
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
  
  app2:
    build: .
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/ai_seo_blogger
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ai_seo_blogger
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes 배포

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-seo-blogger
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-seo-blogger
  template:
    metadata:
      labels:
        app: ai-seo-blogger
    spec:
      containers:
      - name: app
        image: ai-seo-blogger:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        livenessProbe:
          httpGet:
            path: /health/liveness
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/readiness
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ai-seo-blogger-service
spec:
  selector:
    app: ai-seo-blogger
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 📊 모니터링

### 인스턴스 정보 조회
```bash
GET /api/v1/scaling/info
```

응답:
```json
{
  "instance_info": {
    "instance_id": "hostname-12345",
    "hostname": "server-01",
    "pid": 12345,
    "start_time": "2025-12-XXT00:00:00",
    "uptime_seconds": 3600
  },
  "stateless_check": {
    "stateless": true,
    "checks": {
      "session_storage": {...},
      "cache_storage": {...},
      "database": {...}
    }
  },
  "load_balancer_config": {...},
  "recommendations": {...}
}
```

## 🔍 검증

### 스테이트리스 설계 확인
```python
from app.services.horizontal_scaling import horizontal_scaling

checks = horizontal_scaling.check_stateless()
print(checks)
```

### 수평 확장 권장사항
```python
recommendations = horizontal_scaling.get_scaling_recommendations()
print(recommendations)
```

## 📝 체크리스트

### 수평 확장 준비
- [ ] PostgreSQL 데이터베이스 설정
- [ ] Redis 캐시 설정
- [ ] Redis 세션 저장소 설정 (선택적)
- [ ] 헬스체크 엔드포인트 확인
- [ ] 로드 밸런서 설정
- [ ] 인스턴스 간 상태 공유 확인

### 배포 전 확인
- [ ] 모든 인스턴스가 동일한 데이터베이스 사용
- [ ] 모든 인스턴스가 동일한 Redis 사용
- [ ] 세션이 공유 저장소에 저장되는지 확인
- [ ] 캐시가 공유 저장소에 저장되는지 확인
- [ ] 헬스체크 엔드포인트 정상 작동 확인

## 🎯 예상 효과

- **처리 용량**: 5배 증가
- **가용성**: 99.9% 달성
- **장애 복구**: 자동 장애 복구
- **부하 분산**: 여러 인스턴스에 부하 분산

## ⚠️ 주의사항

1. **세션 공유**: 메모리 세션은 수평 확장에 적합하지 않습니다. Redis 세션 사용을 권장합니다.
2. **캐시 공유**: 메모리 캐시는 인스턴스 간 공유되지 않습니다. Redis 캐시 사용을 권장합니다.
3. **파일 업로드**: 로컬 파일 시스템은 인스턴스 간 공유되지 않습니다. 객체 스토리지(S3 등) 사용을 권장합니다.
4. **로그 집계**: 로그를 중앙 집중식으로 관리하는 것을 권장합니다.
