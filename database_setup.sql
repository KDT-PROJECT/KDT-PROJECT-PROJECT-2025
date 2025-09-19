-- 서울시 상권 분석 데이터베이스 완전 설정
-- 데이터베이스 생성 및 초기화 스크립트

-- 1. 데이터베이스 생성 (필요시)
CREATE DATABASE IF NOT EXISTS test_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS seoul_commercial CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- test_db 사용 (에러 메시지에서 참조된 데이터베이스)
USE test_db;

-- 2. 상권 구분(commercial_districts) 테이블
CREATE TABLE IF NOT EXISTS commercial_districts (
    district_code VARCHAR(10) PRIMARY KEY,
    district_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_district_name (district_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 상권(commercial_areas) 테이블
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

-- 4. 서비스 업종(service_industries) 테이블
CREATE TABLE IF NOT EXISTS service_industries (
    industry_code VARCHAR(20) PRIMARY KEY,
    industry_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_industry_name (industry_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 매출 데이터(sales_data) 테이블 - 메인 데이터 테이블
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

    INDEX idx_quarter (quarter_code),
    INDEX idx_area_industry (area_code, industry_code),
    INDEX idx_sales_amount (sales_amount),
    INDEX idx_created_at (created_at),
    UNIQUE KEY uk_quarter_area_industry (quarter_code, area_code, industry_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. 지역(regions) 테이블 (기존 스키마 호환용)
CREATE TABLE IF NOT EXISTS regions (
    region_id INT AUTO_INCREMENT PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL UNIQUE,
    region_code VARCHAR(20) NOT NULL UNIQUE,
    district VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_region_name (region_name),
    INDEX idx_district (district)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. 업종(industries) 테이블 (기존 스키마 호환용)
CREATE TABLE IF NOT EXISTS industries (
    industry_id INT AUTO_INCREMENT PRIMARY KEY,
    industry_name VARCHAR(100) NOT NULL UNIQUE,
    industry_code VARCHAR(20) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_industry_name (industry_name),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. 2024년 매출 데이터(sales_2024) 테이블 (기존 스키마 호환용)
CREATE TABLE IF NOT EXISTS sales_2024 (
    region_id INT NOT NULL,
    industry_id INT NOT NULL,
    date DATE NOT NULL,
    sales_amount DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    transaction_count INT NOT NULL DEFAULT 0,
    avg_transaction_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (region_id, industry_id, date),
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (industry_id) REFERENCES industries(industry_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_date (date),
    INDEX idx_region_date (region_id, date),
    INDEX idx_industry_date (industry_id, date),
    INDEX idx_sales_amount (sales_amount),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. PDF 문서(pdf_documents) 테이블 - RAG 시스템용
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

-- 10. 문서 청크(document_chunks) 테이블 - RAG 시스템용
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

-- 11. 쿼리 로그(query_logs) 테이블
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

-- 12. 초기 데이터 삽입
-- 상권 구분 데이터
INSERT IGNORE INTO commercial_districts (district_code, district_name) VALUES
('A', '골목상권'),
('B', '발달상권'),
('C', '전문상권'),
('D', '관광특구'),
('E', '대학가상권');

-- 지역 데이터 (기존 호환용)
INSERT IGNORE INTO regions (region_name, region_code, district) VALUES
('강남구', 'GN', '강남구'),
('서초구', 'SC', '서초구'),
('송파구', 'SP', '송파구'),
('강동구', 'GD', '강동구'),
('마포구', 'MP', '마포구'),
('용산구', 'YS', '용산구'),
('중구', 'JG', '중구'),
('종로구', 'JR', '종로구'),
('성동구', 'SD', '성동구'),
('광진구', 'GJ', '광진구');

-- 업종 데이터 (기존 호환용)
INSERT IGNORE INTO industries (industry_name, industry_code, category) VALUES
('음식점업', 'F001', '서비스업'),
('소매업', 'R001', '유통업'),
('숙박업', 'H001', '서비스업'),
('문화체험업', 'C001', '문화업'),
('의료업', 'M001', '의료업'),
('교육업', 'E001', '교육업'),
('운송업', 'T001', '운송업'),
('부동산업', 'RE001', '부동산업'),
('금융업', 'FI001', '금융업'),
('정보통신업', 'IT001', 'IT업');

-- 서비스 업종 데이터
INSERT IGNORE INTO service_industries (industry_code, industry_name) VALUES
('F001', '음식점업'),
('R001', '소매업'),
('H001', '숙박업'),
('C001', '문화체험업'),
('M001', '의료업'),
('E001', '교육업'),
('T001', '운송업'),
('RE001', '부동산업'),
('FI001', '금융업'),
('IT001', '정보통신업');

-- 샘플 매출 데이터 추가
INSERT IGNORE INTO sales_data (
    quarter_code, district_code, area_code, industry_code,
    sales_amount, transaction_count,
    weekday_sales, weekend_sales,
    male_sales, female_sales,
    age_20_sales, age_30_sales, age_40_sales
) VALUES
('2024Q1', 'A', 'A001', 'F001', 1500000, 120, 1000000, 500000, 800000, 700000, 300000, 600000, 600000),
('2024Q1', 'A', 'A001', 'R001', 2300000, 85, 1600000, 700000, 1100000, 1200000, 400000, 800000, 1100000),
('2024Q1', 'B', 'B001', 'F001', 3200000, 200, 2200000, 1000000, 1500000, 1700000, 600000, 1200000, 1400000),
('2024Q1', 'B', 'B001', 'H001', 850000, 45, 600000, 250000, 400000, 450000, 150000, 300000, 400000),
('2024Q1', 'C', 'C001', 'IT001', 5600000, 75, 4200000, 1400000, 3200000, 2400000, 800000, 2100000, 2700000);

-- 13. 뷰 생성
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
LEFT JOIN commercial_districts cd ON sd.district_code = cd.district_code
LEFT JOIN commercial_areas ca ON sd.area_code = ca.area_code
LEFT JOIN service_industries si ON sd.industry_code = si.industry_code
GROUP BY cd.district_name, ca.area_name, si.industry_name, sd.quarter_code
ORDER BY total_sales DESC;

-- 기존 호환용 뷰
CREATE OR REPLACE VIEW v_sales_validation AS
SELECT
    r.region_name,
    i.industry_name,
    i.category,
    DATE_FORMAT(s.date, '%Y-%m') as month,
    SUM(s.sales_amount) as total_sales,
    AVG(s.sales_amount) as avg_sales,
    COUNT(*) as data_points
FROM sales_2024 s
LEFT JOIN regions r ON s.region_id = r.region_id
LEFT JOIN industries i ON s.industry_id = i.industry_id
GROUP BY r.region_name, i.industry_name, i.category, DATE_FORMAT(s.date, '%Y-%m')
ORDER BY total_sales DESC;

-- 14. 저장 프로시저
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

    INSERT INTO query_logs (query_id, user_query, generated_sql, query_mode, success)
    VALUES (query_id, '', query_text, 'sql', TRUE);

    COMMIT;
END //

DELIMITER ;

-- 15. 인덱스 최적화
ANALYZE TABLE commercial_districts, commercial_areas, service_industries, sales_data, regions, industries, sales_2024, pdf_documents, document_chunks, query_logs;