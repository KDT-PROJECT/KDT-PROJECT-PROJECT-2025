<<<<<<< HEAD
-- 서울시 상권 분석 데이터베이스 스키마
-- 버전: 0001_init.sql
-- 생성일: 2024-12-19

-- 데이터베이스 생성 (필요시)
-- CREATE DATABASE IF NOT EXISTS seoul_commercial CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE seoul_commercial;

-- 1. 지역(regions) 테이블
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

-- 2. 업종(industries) 테이블
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

-- 3. 2024년 매출 데이터(sales_2024) 테이블
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

-- 4. 상권 특성(features) 테이블 (추가 분석용)
CREATE TABLE IF NOT EXISTS features (
    feature_id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_value DECIMAL(10,4) NOT NULL,
    feature_type ENUM('demographic', 'economic', 'infrastructure', 'competition') NOT NULL,
    measurement_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_region_feature (region_id, feature_name),
    INDEX idx_feature_type (feature_type),
    INDEX idx_measurement_date (measurement_date),
    UNIQUE KEY uk_region_feature_date (region_id, feature_name, measurement_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 쿼리 로그(query_logs) 테이블 (보안 및 모니터링용)
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

-- 6. 초기 데이터 삽입 (샘플 데이터)
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

-- 7. 뷰 생성 (자주 사용되는 쿼리 최적화)
CREATE OR REPLACE VIEW v_sales_summary AS
SELECT 
    r.region_name,
    i.industry_name,
    i.category,
    DATE_FORMAT(s.date, '%Y-%m') as month,
    SUM(s.sales_amount) as total_sales,
    AVG(s.sales_amount) as avg_sales,
    COUNT(*) as data_points
FROM sales_2024 s
JOIN regions r ON s.region_id = r.region_id
JOIN industries i ON s.industry_id = i.industry_id
GROUP BY r.region_name, i.industry_name, i.category, DATE_FORMAT(s.date, '%Y-%m')
ORDER BY total_sales DESC;

-- 8. 저장 프로시저 (보안을 위한 SQL 실행)
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

-- 9. 권한 설정 (보안)
-- GRANT SELECT ON seoul_commercial.* TO 'readonly_user'@'%';
-- GRANT EXECUTE ON PROCEDURE seoul_commercial.ExecuteSafeQuery TO 'app_user'@'%';

-- 10. 인덱스 최적화 힌트
=======
-- 서울시 상권 분석 데이터베이스 스키마
-- 버전: 0001_init.sql
-- 생성일: 2024-12-19

-- 데이터베이스 생성 (필요시)
-- CREATE DATABASE IF NOT EXISTS seoul_commercial CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE seoul_commercial;

-- 1. 지역(regions) 테이블
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

-- 2. 업종(industries) 테이블
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

-- 3. 2024년 매출 데이터(sales_2024) 테이블
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

-- 4. 상권 특성(features) 테이블 (추가 분석용)
CREATE TABLE IF NOT EXISTS features (
    feature_id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_value DECIMAL(10,4) NOT NULL,
    feature_type ENUM('demographic', 'economic', 'infrastructure', 'competition') NOT NULL,
    measurement_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_region_feature (region_id, feature_name),
    INDEX idx_feature_type (feature_type),
    INDEX idx_measurement_date (measurement_date),
    UNIQUE KEY uk_region_feature_date (region_id, feature_name, measurement_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 쿼리 로그(query_logs) 테이블 (보안 및 모니터링용)
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

-- 6. 초기 데이터 삽입 (샘플 데이터)
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

-- 7. 뷰 생성 (자주 사용되는 쿼리 최적화)
CREATE OR REPLACE VIEW v_sales_summary AS
SELECT 
    r.region_name,
    i.industry_name,
    i.category,
    DATE_FORMAT(s.date, '%Y-%m') as month,
    SUM(s.sales_amount) as total_sales,
    AVG(s.sales_amount) as avg_sales,
    COUNT(*) as data_points
FROM sales_2024 s
JOIN regions r ON s.region_id = r.region_id
JOIN industries i ON s.industry_id = i.industry_id
GROUP BY r.region_name, i.industry_name, i.category, DATE_FORMAT(s.date, '%Y-%m')
ORDER BY total_sales DESC;

-- 8. 저장 프로시저 (보안을 위한 SQL 실행)
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

-- 9. 권한 설정 (보안)
-- GRANT SELECT ON seoul_commercial.* TO 'readonly_user'@'%';
-- GRANT EXECUTE ON PROCEDURE seoul_commercial.ExecuteSafeQuery TO 'app_user'@'%';

-- 10. 인덱스 최적화 힌트
>>>>>>> b15a617 (first commit)
-- ANALYZE TABLE regions, industries, sales_2024, features, query_logs;