-- 서울시 상권 분석 데이터베이스 스키마 (업데이트)
-- 버전: 0002_csv_import.sql
-- 생성일: 2024-12-19
-- CSV 데이터 구조에 맞춘 스키마

-- 데이터베이스 생성 (필요시)
-- CREATE DATABASE IF NOT EXISTS seoul_commercial CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE seoul_commercial;

-- 1. 상권 구분(commercial_districts) 테이블
CREATE TABLE IF NOT EXISTS commercial_districts (
    district_code VARCHAR(10) PRIMARY KEY,
    district_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_district_name (district_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 상권(commercial_areas) 테이블
CREATE TABLE IF NOT EXISTS commercial_areas (
    area_code VARCHAR(20) PRIMARY KEY,
    area_name VARCHAR(200) NOT NULL,
    district_code VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (district_code) REFERENCES commercial_districts(district_code) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_area_name (area_name),
    INDEX idx_district_code (district_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 서비스 업종(service_industries) 테이블
CREATE TABLE IF NOT EXISTS service_industries (
    industry_code VARCHAR(20) PRIMARY KEY,
    industry_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_industry_name (industry_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 매출 데이터(sales_data) 테이블 - CSV 데이터 구조에 맞춤
CREATE TABLE IF NOT EXISTS sales_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    quarter_code VARCHAR(10) NOT NULL,
    district_code VARCHAR(10) NOT NULL,
    area_code VARCHAR(20) NOT NULL,
    industry_code VARCHAR(20) NOT NULL,
    sales_amount BIGINT NOT NULL DEFAULT 0,
    transaction_count INT NOT NULL DEFAULT 0,
    
    -- 요일별 매출 금액
    weekday_sales BIGINT DEFAULT 0,
    weekend_sales BIGINT DEFAULT 0,
    
    -- 시간대별 매출 금액
    time_00_06_sales BIGINT DEFAULT 0,
    time_06_11_sales BIGINT DEFAULT 0,
    time_11_14_sales BIGINT DEFAULT 0,
    time_14_17_sales BIGINT DEFAULT 0,
    time_17_21_sales BIGINT DEFAULT 0,
    time_21_24_sales BIGINT DEFAULT 0,
    
    -- 성별 매출 금액
    male_sales BIGINT DEFAULT 0,
    female_sales BIGINT DEFAULT 0,
    
    -- 연령대별 매출 금액
    age_10_sales BIGINT DEFAULT 0,
    age_20_sales BIGINT DEFAULT 0,
    age_30_sales BIGINT DEFAULT 0,
    age_40_sales BIGINT DEFAULT 0,
    age_50_sales BIGINT DEFAULT 0,
    age_60_plus_sales BIGINT DEFAULT 0,
    
    -- 요일별 매출 건수
    weekday_count INT DEFAULT 0,
    weekend_count INT DEFAULT 0,
    
    -- 시간대별 매출 건수
    time_00_06_count INT DEFAULT 0,
    time_06_11_count INT DEFAULT 0,
    time_11_14_count INT DEFAULT 0,
    time_14_17_count INT DEFAULT 0,
    time_17_21_count INT DEFAULT 0,
    time_21_24_count INT DEFAULT 0,
    
    -- 성별 매출 건수
    male_count INT DEFAULT 0,
    female_count INT DEFAULT 0,
    
    -- 연령대별 매출 건수
    age_10_count INT DEFAULT 0,
    age_20_count INT DEFAULT 0,
    age_30_count INT DEFAULT 0,
    age_40_count INT DEFAULT 0,
    age_50_count INT DEFAULT 0,
    age_60_plus_count INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (district_code) REFERENCES commercial_districts(district_code) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (area_code) REFERENCES commercial_areas(area_code) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (industry_code) REFERENCES service_industries(industry_code) ON DELETE CASCADE ON UPDATE CASCADE,
    
    INDEX idx_quarter (quarter_code),
    INDEX idx_area_industry (area_code, industry_code),
    INDEX idx_sales_amount (sales_amount),
    INDEX idx_created_at (created_at),
    UNIQUE KEY uk_quarter_area_industry (quarter_code, area_code, industry_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. PDF 문서(pdf_documents) 테이블 - RAG 시스템용
CREATE TABLE IF NOT EXISTS pdf_documents (
    doc_id VARCHAR(36) PRIMARY KEY,
    file_name VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    title VARCHAR(500),
    content_type ENUM('policy', 'announcement', 'report', 'guideline', 'other') NOT NULL DEFAULT 'other',
    file_size BIGINT,
    upload_date DATE,
    processed_at TIMESTAMP NULL,
    is_indexed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_file_name (file_name),
    INDEX idx_content_type (content_type),
    INDEX idx_processed_at (processed_at),
    INDEX idx_is_indexed (is_indexed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. 문서 청크(document_chunks) 테이블 - RAG 시스템용
CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id VARCHAR(36) PRIMARY KEY,
    doc_id VARCHAR(36) NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    metadata JSON,
    embedding_vector JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES pdf_documents(doc_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_doc_id (doc_id),
    INDEX idx_chunk_index (chunk_index)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. 쿼리 로그(query_logs) 테이블 (보안 및 모니터링용)
CREATE TABLE IF NOT EXISTS query_logs (
    query_id VARCHAR(36) PRIMARY KEY,
    user_query TEXT NOT NULL,
    generated_sql TEXT,
    execution_time_ms INT,
    result_rows INT,
    query_mode ENUM('sql', 'rag', 'mixed') NOT NULL,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at),
    INDEX idx_query_mode (query_mode),
    INDEX idx_success (success)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. 뷰 생성 (자주 사용되는 쿼리 최적화)
CREATE OR REPLACE VIEW v_sales_summary AS
SELECT 
    cd.district_name,
    ca.area_name,
    si.industry_name,
    sd.quarter_code,
    SUM(sd.sales_amount) as total_sales,
    AVG(sd.sales_amount) as avg_sales,
    SUM(sd.transaction_count) as total_transactions,
    AVG(sd.transaction_count) as avg_transactions,
    COUNT(*) as data_points
FROM sales_data sd
JOIN commercial_districts cd ON sd.district_code = cd.district_code
JOIN commercial_areas ca ON sd.area_code = ca.area_code
JOIN service_industries si ON sd.industry_code = si.industry_code
GROUP BY cd.district_name, ca.area_name, si.industry_name, sd.quarter_code
ORDER BY total_sales DESC;

-- 9. 초기 데이터 삽입 (상권 구분)
INSERT IGNORE INTO commercial_districts (district_code, district_name) VALUES
('A', '골목상권'),
('B', '발달상권'),
('C', '전문상권'),
('D', '관광특구'),
('E', '대학가상권');

-- 10. 저장 프로시저 (보안을 위한 SQL 실행)
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS ExecuteSafeQuery(
    IN query_text TEXT,
    IN query_id VARCHAR(36)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        INSERT INTO query_logs (query_id, user_query, generated_sql, success, error_message)
        VALUES (query_id, '', query_text, FALSE, 'SQL 실행 오류');
    END;
    
    START TRANSACTION;
    
    -- 쿼리 로그 기록
    INSERT INTO query_logs (query_id, user_query, generated_sql, query_mode, success)
    VALUES (query_id, '', query_text, 'sql', TRUE);
    
    -- 실제 쿼리 실행은 애플리케이션 레벨에서 처리
    COMMIT;
END //

DELIMITER ;

-- 11. 인덱스 최적화 힌트
-- ANALYZE TABLE commercial_districts, commercial_areas, service_industries, sales_data, pdf_documents, document_chunks, query_logs;
