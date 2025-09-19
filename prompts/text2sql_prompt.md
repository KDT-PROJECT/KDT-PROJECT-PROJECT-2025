# Text-to-SQL Schema Prompt for Seoul Commercial Analysis System

## Database Schema

### Tables and Relationships

#### 1. regions
```sql
CREATE TABLE regions (
    region_id INT PRIMARY KEY AUTO_INCREMENT,
    region_code VARCHAR(20) NOT NULL UNIQUE,
    region_name VARCHAR(100) NOT NULL,  -- 지역명 (예: "강남구 역삼동")
    gu VARCHAR(50) NOT NULL,             -- 구 (예: "강남구")
    dong VARCHAR(80),                    -- 동 (예: "역삼동")
    lat DECIMAL(10,7),                   -- 위도
    lon DECIMAL(10,7),                   -- 경도
    adm_code VARCHAR(20),                -- 행정구역코드
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. industries
```sql
CREATE TABLE industries (
    industry_id INT PRIMARY KEY AUTO_INCREMENT,
    industry_code VARCHAR(20) NOT NULL UNIQUE,
    industry_name VARCHAR(100) NOT NULL,  -- 업종명 (예: "일반음식점", "커피전문점")
    nace_kor VARCHAR(100),                 -- 한국표준산업분류
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. commercial_areas
```sql
CREATE TABLE commercial_areas (
    area_id INT PRIMARY KEY AUTO_INCREMENT,
    area_code VARCHAR(20) NOT NULL UNIQUE,
    area_name VARCHAR(100) NOT NULL,       -- 상권명 (예: "강남역 상권")
    area_type_code VARCHAR(10) NOT NULL,   -- 상권유형코드 (D: 발달상권, T: 전통시장, G: 골목상권)
    area_type_name VARCHAR(50) NOT NULL,   -- 상권유형명
    region_id INT,                         -- 지역 FK
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(region_id)
);
```

#### 4. sales_2024 (Main Sales Data)
```sql
CREATE TABLE sales_2024 (
    id INT PRIMARY KEY AUTO_INCREMENT,
    quarter_code VARCHAR(10) NOT NULL,     -- 분기코드 (20241, 20242, 20243, 20244)
    area_id INT NOT NULL,                  -- 상권 FK
    industry_id INT NOT NULL,              -- 업종 FK
    sales_date DATE NOT NULL,              -- 매출일자
    monthly_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,    -- 월 매출금액
    monthly_sales_count INT NOT NULL DEFAULT 0,               -- 월 매출건수
    weekday_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,    -- 주중 매출금액
    weekend_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,    -- 주말 매출금액
    male_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,       -- 남성 매출금액
    female_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,     -- 여성 매출금액
    teen_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,       -- 10대 매출금액
    twenties_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,   -- 20대 매출금액
    thirties_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,   -- 30대 매출금액
    forties_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,    -- 40대 매출금액
    fifties_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0,    -- 50대 매출금액
    sixties_plus_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0, -- 60대 이상 매출금액
    time_00_06_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0, -- 00~06시 매출금액
    time_06_11_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0, -- 06~11시 매출금액
    time_11_14_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0, -- 11~14시 매출금액
    time_14_17_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0, -- 14~17시 매출금액
    time_17_21_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0, -- 17~21시 매출금액
    time_21_24_sales_amount DECIMAL(18,2) NOT NULL DEFAULT 0, -- 21~24시 매출금액
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (area_id) REFERENCES commercial_areas(area_id),
    FOREIGN KEY (industry_id) REFERENCES industries(industry_id)
);
```

## Sample Data Context

### Regions (지역)
- 강남구 역삼동, 강남구 신사동
- 마포구 홍대동
- 종로구 인사동
- 강서구 화곡동

### Industries (업종)
- 일반음식점 (음식점업)
- 커피전문점 (음료점업)
- 의류소매업 (의류 및 패션용품 소매업)
- 편의점 (종합 소매업)
- 미용업 (개인서비스업)

### Commercial Areas (상권)
- 강남역 상권 (발달상권)
- 신사역 상권 (전통시장)
- 홍대상권 (발달상권)
- 인사동 상권 (전통시장)
- 화곡동 상권 (골목상권)

## 예시 SQL 쿼리

### 1. 기본 조회
```sql
-- 강남구의 모든 매출 데이터
SELECT r.region_name, i.industry_name, s.sales_amount, s.transaction_count
FROM sales_2024 s
JOIN regions r ON s.region_id = r.region_id
JOIN industries i ON s.industry_id = i.industry_id
WHERE r.region_name = '강남구'
ORDER BY s.sales_amount DESC
LIMIT 100;
```

### 2. 집계 쿼리
```sql
-- 지역별 총 매출액 상위 10개
SELECT r.region_name, SUM(s.sales_amount) as total_sales
FROM sales_2024 s
JOIN regions r ON s.region_id = r.region_id
GROUP BY r.region_id, r.region_name
ORDER BY total_sales DESC
LIMIT 10;
```

### 3. 월별 트렌드
```sql
-- 2024년 월별 매출 트렌드
SELECT s.month, SUM(s.sales_amount) as monthly_sales
FROM sales_2024 s
GROUP BY s.month
ORDER BY s.month;
```

### 4. 업종별 분석
```sql
-- 음식점업 업종의 지역별 매출
SELECT r.region_name, SUM(s.sales_amount) as total_sales
FROM sales_2024 s
JOIN regions r ON s.region_id = r.region_id
JOIN industries i ON s.industry_id = i.industry_id
WHERE i.category = '음식점업'
GROUP BY r.region_id, r.region_name
ORDER BY total_sales DESC
LIMIT 20;
```

### 5. 복합 조건
```sql
-- 강남구에서 매출이 높은 상위 5개 업종
SELECT i.industry_name, SUM(s.sales_amount) as total_sales
FROM sales_2024 s
JOIN regions r ON s.region_id = r.region_id
JOIN industries i ON s.industry_id = i.industry_id
WHERE r.region_name = '강남구'
GROUP BY i.industry_id, i.industry_name
ORDER BY total_sales DESC
LIMIT 5;
```

## SQL 생성 규칙

### 1. 필수 규칙
- **SELECT 문만 사용**: DML, DDL, DCL 문은 절대 사용 금지
- **LIMIT 절 필수**: 모든 쿼리에 LIMIT 절 포함 (기본값: 100, 최대: 1000)
- **적절한 JOIN 사용**: 테이블 간 관계를 명확히 표현
- **WHERE 절 활용**: 불필요한 데이터 조회 방지

### 2. 보안 규칙
- **화이트리스트 테이블만 사용**: regions, industries, sales_2024
- **금지된 키워드**: DROP, DELETE, INSERT, UPDATE, CREATE, ALTER, TRUNCATE, GRANT, REVOKE, EXECUTE, CALL
- **시스템 함수 금지**: USER(), DATABASE(), VERSION(), CONNECTION_ID() 등

### 3. 성능 최적화
- **인덱스 활용**: region_id, industry_id, year, month 컬럼 활용
- **적절한 GROUP BY**: 집계 시 필요한 컬럼만 그룹화
- **ORDER BY 사용**: 의미 있는 정렬 기준 적용

### 4. 데이터 타입 고려사항
- **날짜/시간**: year, month는 INT 타입
- **금액**: sales_amount는 BIGINT, avg_transaction_amount는 DECIMAL(15,2)
- **문자열**: region_name, industry_name은 VARCHAR

## 자연어 쿼리 패턴

### 지역 관련
- "강남구 매출" → WHERE r.region_name = '강남구'
- "서울시 전체" → 모든 지역 포함
- "강남구, 서초구" → WHERE r.region_name IN ('강남구', '서초구')

### 업종 관련
- "음식점업" → WHERE i.category = '음식점업'
- "한식음식점업" → WHERE i.industry_name = '한식음식점업'
- "IT 업종" → WHERE i.category LIKE '%IT%' OR i.industry_name LIKE '%IT%'

### 시간 관련
- "2024년" → WHERE s.year = 2024
- "1월" → WHERE s.month = 1
- "상반기" → WHERE s.month BETWEEN 1 AND 6
- "하반기" → WHERE s.month BETWEEN 7 AND 12

### 집계 관련
- "총 매출" → SUM(s.sales_amount)
- "평균 매출" → AVG(s.sales_amount)
- "거래 건수" → SUM(s.transaction_count)
- "상위 N개" → ORDER BY ... DESC LIMIT N

## 오류 처리

### 일반적인 오류 상황
1. **테이블명 오류**: 존재하지 않는 테이블 참조 시 올바른 테이블명 사용
2. **컬럼명 오류**: 존재하지 않는 컬럼 참조 시 스키마 확인
3. **JOIN 오류**: 잘못된 관계 설정 시 올바른 외래키 사용
4. **데이터 타입 오류**: 잘못된 타입 비교 시 적절한 변환

### 사용자 친화적 메시지
- "해당 지역의 데이터가 없습니다" → 빈 결과 반환
- "업종명을 확인해주세요" → 유사한 업종명 제안
- "기간을 좁혀서 검색해보세요" → LIMIT 절 추가 제안
