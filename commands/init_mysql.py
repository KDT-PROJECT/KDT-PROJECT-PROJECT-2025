from sqlalchemy import create_engine, text
from utils.config import MYSQL_URI

DDL_SQL = """
-- DB가 URI에 포함돼 있더라도 안전하게 존재 보장
CREATE DATABASE IF NOT EXISTS mydb CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE mydb;

CREATE TABLE IF NOT EXISTS sales_daily (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  region_id    VARCHAR(64)   NOT NULL,
  industry_id  VARCHAR(64)   NOT NULL,
  sales_date   DATE          NOT NULL,
  sales_amt    DECIMAL(18,2) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_region_industry_date (region_id, industry_id, sales_date),
  KEY idx_sales_date (sales_date),
  KEY idx_region_date (region_id, sales_date),
  KEY idx_industry_date (industry_id, sales_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS regions (
  region_id VARCHAR(64) PRIMARY KEY,
  name      VARCHAR(128),
  gu        VARCHAR(64),
  dong      VARCHAR(64),
  lat       DECIMAL(10,7),
  lon       DECIMAL(10,7)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS industries (
  industry_id VARCHAR(64) PRIMARY KEY,
  name        VARCHAR(128)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 비정형 문서 저장 (PDF 등)
CREATE TABLE IF NOT EXISTS docs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  doc_hash   CHAR(64) NOT NULL,      -- 파일 내용 해시(SHA256)로 중복 방지
  title      VARCHAR(255) NOT NULL,
  source     VARCHAR(1024) NULL,     -- 로컬 경로/URL 등
  published_date DATE NULL,
  content    LONGTEXT NULL,          -- 추출 텍스트
  meta_json  JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_docs_hash (doc_hash),
  KEY idx_title (title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE OR REPLACE VIEW sales_monthly AS
SELECT
  region_id,
  industry_id,
  DATE_FORMAT(sales_date, '%Y-%m-01') AS month_first_day,
  SUM(sales_amt) AS sales_amt_sum
FROM sales_daily
GROUP BY region_id, industry_id, month_first_day;
"""

def main():
    if not MYSQL_URI:
        raise RuntimeError("MYSQL_URI가 utils/config.py에 설정되어야 합니다.")
    engine = create_engine(MYSQL_URI, pool_pre_ping=True)
    with engine.begin() as conn:
        for stmt in [s.strip() for s in DDL_SQL.split(";") if s.strip()]:
            conn.execute(text(stmt))
    print("✅ MySQL 초기화 완료 (스키마/테이블/뷰 생성).")

if __name__ == "__main__":
    main()