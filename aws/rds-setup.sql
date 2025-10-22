-- AI SEO Blogger RDS PostgreSQL 설정
-- 이 스크립트는 RDS PostgreSQL 인스턴스에서 실행됩니다.

-- 데이터베이스 생성
CREATE DATABASE ai_seo_blogger;

-- 사용자 생성 및 권한 부여
CREATE USER ai_seo_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE ai_seo_blogger TO ai_seo_user;

-- 데이터베이스 연결
\c ai_seo_blogger;

-- 테이블 생성
CREATE TABLE IF NOT EXISTS blog_posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    keywords TEXT,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'draft',
    word_count INTEGER DEFAULT 0,
    reading_time INTEGER DEFAULT 0,
    seo_score INTEGER DEFAULT 0,
    meta_description TEXT,
    tags TEXT,
    category VARCHAR(100),
    author VARCHAR(100) DEFAULT 'AI SEO Blogger',
    slug VARCHAR(500) UNIQUE,
    featured_image_url TEXT,
    published_at TIMESTAMP,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS keyword_list (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    difficulty INTEGER DEFAULT 0,
    search_volume INTEGER DEFAULT 0,
    competition VARCHAR(50),
    cpc DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    category VARCHAR(100),
    language VARCHAR(10) DEFAULT 'ko',
    country VARCHAR(10) DEFAULT 'KR'
);

CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    service VARCHAR(50) NOT NULL,
    api_key TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    quota_limit INTEGER,
    quota_used INTEGER DEFAULT 0,
    quota_reset_date DATE
);

CREATE TABLE IF NOT EXISTS crawling_logs (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    response_time_ms INTEGER,
    content_length INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    referer TEXT,
    ip_address INET
);

CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    metric_unit VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags JSONB,
    service VARCHAR(50),
    environment VARCHAR(20) DEFAULT 'production'
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_blog_posts_created_at ON blog_posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_blog_posts_title ON blog_posts(title);
CREATE INDEX IF NOT EXISTS idx_blog_posts_keywords ON blog_posts(keywords);
CREATE INDEX IF NOT EXISTS idx_blog_posts_status ON blog_posts(status);
CREATE INDEX IF NOT EXISTS idx_blog_posts_slug ON blog_posts(slug);
CREATE INDEX IF NOT EXISTS idx_blog_posts_published_at ON blog_posts(published_at DESC);

CREATE INDEX IF NOT EXISTS idx_keyword_list_type ON keyword_list(type);
CREATE INDEX IF NOT EXISTS idx_keyword_list_keyword ON keyword_list(keyword);
CREATE INDEX IF NOT EXISTS idx_keyword_list_is_active ON keyword_list(is_active);
CREATE INDEX IF NOT EXISTS idx_keyword_list_category ON keyword_list(category);

CREATE INDEX IF NOT EXISTS idx_api_keys_service ON api_keys(service);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);

CREATE INDEX IF NOT EXISTS idx_crawling_logs_created_at ON crawling_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_crawling_logs_status ON crawling_logs(status);
CREATE INDEX IF NOT EXISTS idx_crawling_logs_url ON crawling_logs(url);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_service ON performance_metrics(service);

-- 트리거 함수 생성 (updated_at 자동 업데이트)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
CREATE TRIGGER update_blog_posts_updated_at BEFORE UPDATE ON blog_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_keyword_list_updated_at BEFORE UPDATE ON keyword_list
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 초기 데이터 삽입
INSERT INTO api_keys (service, api_key, is_active) VALUES 
('openai', 'your_openai_api_key_here', true),
('gemini', 'your_gemini_api_key_here', true),
('deepl', 'your_deepl_api_key_here', true)
ON CONFLICT DO NOTHING;

-- 권한 설정
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ai_seo_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ai_seo_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO ai_seo_user;

-- 연결 풀 설정을 위한 뷰 생성
CREATE VIEW IF NOT EXISTS active_blog_posts AS
SELECT * FROM blog_posts 
WHERE status = 'published' 
AND published_at IS NOT NULL 
ORDER BY published_at DESC;

CREATE VIEW IF NOT EXISTS keyword_statistics AS
SELECT 
    type,
    COUNT(*) as total_keywords,
    COUNT(CASE WHEN is_active = true THEN 1 END) as active_keywords,
    AVG(difficulty) as avg_difficulty,
    AVG(search_volume) as avg_search_volume
FROM keyword_list 
GROUP BY type;

-- 성능 최적화를 위한 통계 업데이트
ANALYZE blog_posts;
ANALYZE keyword_list;
ANALYZE api_keys;
ANALYZE crawling_logs;
ANALYZE performance_metrics;

-- 완료 메시지
SELECT 'AI SEO Blogger 데이터베이스 설정이 완료되었습니다.' as message;
