# Terraform 변수 정의

variable "aws_region" {
  description = "AWS 리전"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "환경 (production, staging, development)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["production", "staging", "development"], var.environment)
    error_message = "환경은 production, staging, development 중 하나여야 합니다."
  }
}

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
  default     = "ai-seo-blogger"
}

variable "db_password" {
  description = "RDS 데이터베이스 비밀번호"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "도메인 이름 (선택사항)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "SSL 인증서 ARN (선택사항)"
  type        = string
  default     = ""
}

variable "min_capacity" {
  description = "ECS 서비스 최소 용량"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "ECS 서비스 최대 용량"
  type        = number
  default     = 10
}

variable "desired_count" {
  description = "ECS 서비스 원하는 태스크 수"
  type        = number
  default     = 2
}

variable "cpu" {
  description = "ECS 태스크 CPU (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 512
  
  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.cpu)
    error_message = "CPU는 256, 512, 1024, 2048, 4096 중 하나여야 합니다."
  }
}

variable "memory" {
  description = "ECS 태스크 메모리 (512, 1024, 2048, 4096, 8192, 16384)"
  type        = number
  default     = 1024
  
  validation {
    condition     = contains([512, 1024, 2048, 4096, 8192, 16384], var.memory)
    error_message = "메모리는 512, 1024, 2048, 4096, 8192, 16384 중 하나여야 합니다."
  }
}

variable "enable_auto_scaling" {
  description = "자동 스케일링 활성화"
  type        = bool
  default     = true
}

variable "enable_cloudfront" {
  description = "CloudFront CDN 활성화"
  type        = bool
  default     = false
}

variable "enable_waf" {
  description = "AWS WAF 활성화"
  type        = bool
  default     = false
}

variable "backup_retention_period" {
  description = "RDS 백업 보존 기간 (일)"
  type        = number
  default     = 7
  
  validation {
    condition     = var.backup_retention_period >= 0 && var.backup_retention_period <= 35
    error_message = "백업 보존 기간은 0-35일 사이여야 합니다."
  }
}

variable "instance_class" {
  description = "RDS 인스턴스 클래스"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "RDS 할당된 스토리지 (GB)"
  type        = number
  default     = 20
  
  validation {
    condition     = var.allocated_storage >= 20 && var.allocated_storage <= 1000
    error_message = "할당된 스토리지는 20-1000GB 사이여야 합니다."
  }
}

variable "max_allocated_storage" {
  description = "RDS 최대 할당된 스토리지 (GB)"
  type        = number
  default     = 100
  
  validation {
    condition     = var.max_allocated_storage >= var.allocated_storage
    error_message = "최대 할당된 스토리지는 할당된 스토리지보다 크거나 같아야 합니다."
  }
}

variable "log_retention_days" {
  description = "CloudWatch 로그 보존 기간 (일)"
  type        = number
  default     = 30
  
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653], var.log_retention_days)
    error_message = "로그 보존 기간은 유효한 값이어야 합니다."
  }
}

variable "tags" {
  description = "추가 태그"
  type        = map(string)
  default     = {}
}
