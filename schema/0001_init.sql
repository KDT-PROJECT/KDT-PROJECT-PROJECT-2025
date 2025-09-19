-- 서울 상권분석 LLM 시스템 초기 스키마
-- TASK2: MySQL 스키마 정의

-- 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS seoul_commercial 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE seoul_commercial;

-- 지역 테이블
CREATE TABLE regions (
    region_id INT PRIMARY KEY AUTO_INCREMENT,
    region_code VARCHAR(20) NOT NULL UNIQUE,
    region_name VARCHAR(100) NOT NULL,
    gu VARCHAR(50) NOT NULL,
    dong VARCHAR(80),
    lat DECIMAL(10,7),
    lon DECIMAL(10,7),
    adm_code VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_region_code (region_code),
    INDEX idx_gu_dong (gu, dong)
);

-- 업종 테이블
CREATE TABLE industries (
    industry_id INT PRIMARY KEY AUTO_INCREMENT,
    industry_code VARCHAR(20) NOT NULL UNIQUE,
    industry_name VARCHAR(100) NOT NULL,
    nace_kor VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_industry_code (industry_code)
);

-- 상권 테이블
CREATE TABLE commercial_areas (
    area_id INT PRIMARY KEY AUTO_INCREMENT,
    area_code VARCHAR(20) NOT NULL UNIQUE,
    area_name VARCHAR(100) NOT NULL,
    area_type_code VARCHAR(10) NOT NULL,
    area_type_name VARCHAR(50) NOT NULL,
    region_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(region_id),
    INDEX idx_area_code (area_code),
    INDEX idx_area_type (area_type_code)
);

-- 매출 데이터 테이블 (2024년)
CREATE TABLE sales_2024 (
    id INT PRIMARY KEY AUTO_INCREMENT,
    quarter_code VARCHAR(10) NOT NULL,
    area_id INT NOT NULL,
    industry_id INT NOT NULL,
    sales_date DATE NOT NULL,
    monthly_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    monthly_sales_count INT NOT NULL DEFAULT 0,
    weekday_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    weekend_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    male_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    female_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    teen_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    twenties_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    thirties_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    forties_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    fifties_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    sixties_plus_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    time_00_06_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    time_06_11_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    time_11_14_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    time_14_17_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    time_17_21_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    time_21_24_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    male_sales_count INT NOT NULL DEFAULT 0,
    female_sales_count INT NOT NULL DEFAULT 0,
    teen_sales_count INT NOT NULL DEFAULT 0,
    twenties_sales_count INT NOT NULL DEFAULT 0,
    thirties_sales_count INT NOT NULL DEFAULT 0,
    forties_sales_count INT NOT NULL DEFAULT 0,
    fifties_sales_count INT NOT NULL DEFAULT 0,
    sixties_plus_sales_count INT NOT NULL DEFAULT 0,
    time_00_06_sales_count INT NOT NULL DEFAULT 0,
    time_06_11_sales_count INT NOT NULL DEFAULT 0,
    time_11_14_sales_count INT NOT NULL DEFAULT 0,
    time_14_17_sales_count INT NOT NULL DEFAULT 0,
    time_17_21_sales_count INT NOT NULL DEFAULT 0,
    time_21_24_sales_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (area_id) REFERENCES commercial_areas(area_id),
    FOREIGN KEY (industry_id) REFERENCES industries(industry_id),
    INDEX idx_sales_date (sales_date),
    INDEX idx_area_industry (area_id, industry_id),
    INDEX idx_quarter (quarter_code),
    UNIQUE KEY uk_sales_unique (area_id, industry_id, sales_date)
);

-- 쿼리 로그 테이블
CREATE TABLE query_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    query_text TEXT NOT NULL,
    sql_query TEXT,
    execution_time_ms INT,
    result_rows INT,
    status ENUM('success', 'error', 'timeout') NOT NULL,
    error_message TEXT,
    user_ip VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at),
    INDEX idx_status (status)
);

-- 문서 테이블 (RAG용)
CREATE TABLE docs (
    doc_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    source VARCHAR(100) NOT NULL,
    url VARCHAR(500),
    published_date DATE,
    file_path VARCHAR(500),
    content_hash VARCHAR(64),
    meta_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_source (source),
    INDEX idx_published_date (published_date),
    INDEX idx_content_hash (content_hash)
);
