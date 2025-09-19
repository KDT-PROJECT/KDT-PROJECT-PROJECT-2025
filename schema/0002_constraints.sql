-- =====================================================
-- TASK-002: MySQL 스키마 제약조건 및 뷰 생성
-- 파일: schema/0002_constraints.sql
-- 설명: CHECK 제약조건, 뷰, 권한 설정
-- =====================================================

USE seoul_commercial;

-- =====================================================
-- 1. 데이터 검증을 위한 뷰 생성
-- =====================================================

-- 매출 데이터 검증 뷰 (음수값 체크)
CREATE OR REPLACE VIEW v_sales_validation AS
SELECT 
    region_id,
    industry_id,
    date,
    sales_amt,
    sales_cnt,
    visitors,
    CASE 
        WHEN sales_amt < 0 THEN 'INVALID_SALES_AMT'
        WHEN sales_cnt < 0 THEN 'INVALID_SALES_CNT'
        WHEN visitors < 0 THEN 'INVALID_VISITORS'
        WHEN date < '2024-01-01' OR date > '2024-12-31' THEN 'INVALID_DATE'
        ELSE 'VALID'
    END AS validation_status
FROM sales_2024;

-- 지역별 매출 요약 뷰
CREATE OR REPLACE VIEW v_region_sales_summary AS
SELECT 
    r.region_id,
    r.name AS region_name,
    r.gu,
    r.dong,
    COUNT(DISTINCT s.date) AS days_with_sales,
    SUM(s.sales_amt) AS total_sales_amt,
    SUM(s.sales_cnt) AS total_sales_cnt,
    SUM(s.visitors) AS total_visitors,
    AVG(s.sales_amt) AS avg_daily_sales_amt,
    AVG(s.sales_cnt) AS avg_daily_sales_cnt,
    AVG(s.visitors) AS avg_daily_visitors
FROM regions r
LEFT JOIN sales_2024 s ON r.region_id = s.region_id
GROUP BY r.region_id, r.name, r.gu, r.dong;

-- 업종별 매출 요약 뷰
CREATE OR REPLACE VIEW v_industry_sales_summary AS
SELECT 
    i.industry_id,
    i.name AS industry_name,
    i.nace_kor,
    COUNT(DISTINCT s.date) AS days_with_sales,
    SUM(s.sales_amt) AS total_sales_amt,
    SUM(s.sales_cnt) AS total_sales_cnt,
    SUM(s.visitors) AS total_visitors,
    AVG(s.sales_amt) AS avg_daily_sales_amt,
    AVG(s.sales_cnt) AS avg_daily_sales_cnt,
    AVG(s.visitors) AS avg_daily_visitors
FROM industries i
LEFT JOIN sales_2024 s ON i.industry_id = s.industry_id
GROUP BY i.industry_id, i.name, i.nace_kor;

-- 월별 매출 추이 뷰
CREATE OR REPLACE VIEW v_monthly_sales_trend AS
SELECT 
    YEAR(date) AS year,
    MONTH(date) AS month,
    COUNT(DISTINCT region_id) AS regions_count,
    COUNT(DISTINCT industry_id) AS industries_count,
    SUM(sales_amt) AS total_sales_amt,
    SUM(sales_cnt) AS total_sales_cnt,
    SUM(visitors) AS total_visitors,
    AVG(sales_amt) AS avg_sales_amt,
    AVG(sales_cnt) AS avg_sales_cnt,
    AVG(visitors) AS avg_visitors
FROM sales_2024
GROUP BY YEAR(date), MONTH(date)
ORDER BY year, month;

-- =====================================================
-- 2. 데이터 검증을 위한 트리거 생성
-- =====================================================

-- sales_2024 삽입 전 검증 트리거
DELIMITER $$

CREATE TRIGGER tr_sales_2024_before_insert
BEFORE INSERT ON sales_2024
FOR EACH ROW
BEGIN
    -- 음수값 검증
    IF NEW.sales_amt < 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'sales_amt must be non-negative';
    END IF;
    
    IF NEW.sales_cnt < 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'sales_cnt must be non-negative';
    END IF;
    
    IF NEW.visitors < 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'visitors must be non-negative';
    END IF;
    
    -- 날짜 범위 검증
    IF NEW.date < '2024-01-01' OR NEW.date > '2024-12-31' THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'date must be within 2024';
    END IF;
END$$

-- sales_2024 업데이트 전 검증 트리거
CREATE TRIGGER tr_sales_2024_before_update
BEFORE UPDATE ON sales_2024
FOR EACH ROW
BEGIN
    -- 음수값 검증
    IF NEW.sales_amt < 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'sales_amt must be non-negative';
    END IF;
    
    IF NEW.sales_cnt < 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'sales_cnt must be non-negative';
    END IF;
    
    IF NEW.visitors < 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'visitors must be non-negative';
    END IF;
    
    -- 날짜 범위 검증
    IF NEW.date < '2024-01-01' OR NEW.date > '2024-12-31' THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'date must be within 2024';
    END IF;
END$$

DELIMITER ;

-- =====================================================
-- 3. READ-ONLY 계정 생성
-- =====================================================

-- READ-ONLY 사용자 생성 (비밀번호는 환경변수에서 설정)
-- 실제 환경에서는 보안을 위해 강력한 비밀번호 사용
CREATE USER IF NOT EXISTS 'seoul_ro'@'%' IDENTIFIED BY 'seoul_ro_password_2024';

-- READ-ONLY 권한 부여
GRANT SELECT ON seoul_commercial.* TO 'seoul_ro'@'%';

-- 특정 테이블에 대한 SELECT 권한만 부여 (더 세밀한 제어)
GRANT SELECT ON seoul_commercial.regions TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.industries TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.sales_2024 TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.features TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.docs TO 'seoul_commercial'@'%';

-- 뷰에 대한 SELECT 권한
GRANT SELECT ON seoul_commercial.v_sales_validation TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.v_region_sales_summary TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.v_industry_sales_summary TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.v_monthly_sales_trend TO 'seoul_ro'@'%';

-- 권한 적용
FLUSH PRIVILEGES;

-- =====================================================
-- 4. 성능 최적화를 위한 추가 인덱스
-- =====================================================

-- 복합 쿼리를 위한 커버링 인덱스
CREATE INDEX idx_sales_region_industry_date_amt 
ON sales_2024(region_id, industry_id, date, sales_amt);

CREATE INDEX idx_sales_date_region_amt 
ON sales_2024(date, region_id, sales_amt);

-- 텍스트 검색을 위한 인덱스
CREATE FULLTEXT INDEX idx_regions_name_fulltext 
ON regions(name);

CREATE FULLTEXT INDEX idx_industries_name_fulltext 
ON industries(name);

-- =====================================================
-- 5. 통계 정보 업데이트
-- =====================================================

-- 테이블 통계 정보 업데이트 (성능 최적화)
ANALYZE TABLE regions;
ANALYZE TABLE industries;
ANALYZE TABLE sales_2024;
ANALYZE TABLE features;
ANALYZE TABLE docs;
ANALYZE TABLE query_logs;

-- =====================================================
-- 완료 메시지
-- =====================================================
SELECT 'Schema 0002_constraints.sql applied successfully' AS status;

