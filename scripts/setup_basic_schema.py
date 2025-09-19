#!/usr/bin/env python3
"""
Basic MySQL Schema Setup for Seoul Commercial Analysis LLM System
Works with test_db database and limited privileges
"""

import mysql.connector
import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_basic_schema():
    """Create basic schema in test_db database"""

    basic_schema = """
    -- Use existing test_db database
    USE test_db;

    -- Drop tables if they exist (for clean setup)
    DROP TABLE IF EXISTS sales_2024;
    DROP TABLE IF EXISTS query_logs;
    DROP TABLE IF EXISTS docs;
    DROP TABLE IF EXISTS commercial_areas;
    DROP TABLE IF EXISTS industries;
    DROP TABLE IF EXISTS regions;

    -- Create regions table
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
        INDEX idx_region_code (region_code),
        INDEX idx_gu_dong (gu, dong)
    );

    -- Create industries table
    CREATE TABLE industries (
        industry_id INT PRIMARY KEY AUTO_INCREMENT,
        industry_code VARCHAR(20) NOT NULL UNIQUE,
        industry_name VARCHAR(100) NOT NULL,
        nace_kor VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_industry_code (industry_code)
    );

    -- Create commercial_areas table
    CREATE TABLE commercial_areas (
        area_id INT PRIMARY KEY AUTO_INCREMENT,
        area_code VARCHAR(20) NOT NULL UNIQUE,
        area_name VARCHAR(100) NOT NULL,
        area_type_code VARCHAR(10) NOT NULL,
        area_type_name VARCHAR(50) NOT NULL,
        region_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (region_id) REFERENCES regions(region_id),
        INDEX idx_area_code (area_code),
        INDEX idx_area_type (area_type_code)
    );

    -- Create sales_2024 table (simplified structure)
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (area_id) REFERENCES commercial_areas(area_id),
        FOREIGN KEY (industry_id) REFERENCES industries(industry_id),
        INDEX idx_sales_date (sales_date),
        INDEX idx_area_industry (area_id, industry_id),
        INDEX idx_quarter (quarter_code),
        UNIQUE KEY uk_sales_unique (area_id, industry_id, sales_date)
    );

    -- Create docs table (for RAG)
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
        INDEX idx_source (source),
        INDEX idx_published_date (published_date),
        INDEX idx_content_hash (content_hash)
    );

    -- Create query_logs table
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

    -- Insert sample data for testing
    INSERT INTO regions (region_code, region_name, gu, dong, lat, lon, adm_code) VALUES
    ('R001', '강남구 역삼동', '강남구', '역삼동', 37.5006, 127.0366, '11680101'),
    ('R002', '강남구 신사동', '강남구', '신사동', 37.5206, 127.0276, '11680102'),
    ('R003', '마포구 홍대동', '마포구', '홍대동', 37.5563, 126.9236, '11440123'),
    ('R004', '종로구 인사동', '종로구', '인사동', 37.5729, 126.9857, '11110345'),
    ('R005', '강서구 화곡동', '강서구', '화곡동', 37.5415, 126.8406, '11500567');

    INSERT INTO industries (industry_code, industry_name, nace_kor) VALUES
    ('I001', '일반음식점', '음식점업'),
    ('I002', '커피전문점', '음료점업'),
    ('I003', '의류소매업', '의류 및 패션용품 소매업'),
    ('I004', '편의점', '종합 소매업'),
    ('I005', '미용업', '개인서비스업');

    INSERT INTO commercial_areas (area_code, area_name, area_type_code, area_type_name, region_id) VALUES
    ('A001', '강남역 상권', 'D', '발달상권', 1),
    ('A002', '신사역 상권', 'T', '전통시장', 2),
    ('A003', '홍대상권', 'D', '발달상권', 3),
    ('A004', '인사동 상권', 'T', '전통시장', 4),
    ('A005', '화곡동 상권', 'G', '골목상권', 5);

    -- Insert sample sales data for 2024
    INSERT INTO sales_2024 (quarter_code, area_id, industry_id, sales_date, monthly_sales_amount, monthly_sales_count, weekday_sales_amount, weekend_sales_amount) VALUES
    ('20241', 1, 1, '2024-01-15', 5000000, 150, 3500000, 1500000),
    ('20241', 1, 2, '2024-01-15', 2500000, 300, 1800000, 700000),
    ('20241', 2, 1, '2024-01-15', 3000000, 100, 2100000, 900000),
    ('20241', 3, 1, '2024-01-15', 4500000, 180, 3000000, 1500000),
    ('20242', 1, 1, '2024-04-15', 5500000, 160, 3800000, 1700000),
    ('20242', 1, 2, '2024-04-15', 2800000, 320, 2000000, 800000);
    """

    return basic_schema

def main():
    """Main function"""
    logger.info("=== Basic MySQL Schema Setup for Seoul Commercial Analysis ===")

    # Database configuration
    db_config = {
        'host': 'localhost',
        'user': 'test',
        'password': 'test',
        'port': 3306,
        'database': 'test_db',
        'charset': 'utf8mb4',
        'autocommit': True
    }

    try:
        # Create connection
        connection = mysql.connector.connect(**db_config)
        logger.info("Connected to MySQL successfully")

        # Execute schema
        cursor = connection.cursor()
        schema_sql = create_basic_schema()

        # Split into individual statements
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]

        success_count = 0
        for i, statement in enumerate(statements):
            try:
                logger.info(f"Executing statement {i+1}/{len(statements)}")
                cursor.execute(statement)
                success_count += 1
            except mysql.connector.Error as e:
                logger.warning(f"Statement {i+1} failed: {e}")
                logger.debug(f"Failed statement: {statement[:100]}...")

        logger.info(f"Schema setup: {success_count}/{len(statements)} statements successful")

        # Verify tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        logger.info(f"Created tables: {[table[0] for table in tables]}")

        # Check sample data
        cursor.execute("SELECT COUNT(*) FROM regions")
        regions_count = cursor.fetchone()[0]
        logger.info(f"Sample regions: {regions_count}")

        cursor.execute("SELECT COUNT(*) FROM sales_2024")
        sales_count = cursor.fetchone()[0]
        logger.info(f"Sample sales records: {sales_count}")

        cursor.close()
        connection.close()

        logger.info("✅ Basic schema setup completed successfully!")

    except Exception as e:
        logger.error(f"Schema setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()