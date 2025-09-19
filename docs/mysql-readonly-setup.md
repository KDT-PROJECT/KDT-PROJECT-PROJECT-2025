# MySQL READ-ONLY 계정 설정 가이드

## 개요
TASK-002: MySQL 스키마 정의 및 초기 마이그레이션에 따라 Text-to-SQL 서비스에서 사용할 READ-ONLY 계정을 설정하는 방법을 설명합니다.

## 목적
- Text-to-SQL 서비스의 보안 강화
- 데이터베이스 무결성 보호
- 최소 권한 원칙 적용

## READ-ONLY 계정 정보

### 계정명
- **사용자명**: `seoul_ro`
- **비밀번호**: `seoul_ro_password_2024` (운영 환경에서는 변경 필요)
- **호스트**: `%` (모든 호스트에서 접근 가능)

### 권한 범위
- **데이터베이스**: `seoul_commercial`
- **권한**: `SELECT`만 허용
- **테이블**: 모든 테이블에 대한 SELECT 권한
- **뷰**: 모든 뷰에 대한 SELECT 권한

## 설정 방법

### 1. MySQL 서버 접속
```bash
mysql -u root -p
```

### 2. READ-ONLY 계정 생성
```sql
-- READ-ONLY 사용자 생성
CREATE USER IF NOT EXISTS 'seoul_ro'@'%' IDENTIFIED BY 'seoul_ro_password_2024';

-- 데이터베이스 선택
USE seoul_commercial;

-- 기본 SELECT 권한 부여
GRANT SELECT ON seoul_commercial.* TO 'seoul_ro'@'%';
```

### 3. 개별 테이블 권한 설정 (선택사항)
```sql
-- 특정 테이블에 대한 SELECT 권한만 부여
GRANT SELECT ON seoul_commercial.regions TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.industries TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.sales_2024 TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.features TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.docs TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.query_logs TO 'seoul_ro'@'%';
```

### 4. 뷰 권한 설정
```sql
-- 뷰에 대한 SELECT 권한 부여
GRANT SELECT ON seoul_commercial.v_sales_validation TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.v_region_sales_summary TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.v_industry_sales_summary TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.v_monthly_sales_trend TO 'seoul_ro'@'%';
```

### 5. 권한 적용
```sql
-- 권한 변경사항 적용
FLUSH PRIVILEGES;
```

## 환경 변수 설정

### .env 파일 설정
```ini
# MySQL READ-ONLY Account (for Text-to-SQL)
MYSQL_USER_RO=seoul_ro
MYSQL_PWD_RO=seoul_ro_password_2024
MYSQL_URL_RO=mysql+pymysql://seoul_ro:seoul_ro_password_2024@localhost:3306/seoul_commercial
```

### config.py에서 사용
```python
from config import get_database_config

# READ-ONLY 연결 설정
db_config = get_database_config()
readonly_url = db_config.MYSQL_URL_RO
```

## 보안 검증

### 1. 권한 확인
```sql
-- 사용자 권한 확인
SHOW GRANTS FOR 'seoul_ro'@'%';

-- 특정 테이블 권한 확인
SELECT * FROM information_schema.table_privileges 
WHERE grantee = 'seoul_ro' AND table_name = 'sales_2024';
```

### 2. 연결 테스트
```bash
# READ-ONLY 계정으로 연결 테스트
mysql -u seoul_ro -p seoul_commercial

# SELECT 쿼리 테스트
SELECT COUNT(*) FROM sales_2024;

# INSERT 시도 (실패해야 함)
INSERT INTO sales_2024 VALUES (1, 1, '2024-01-01', 1000, 10, 20);
-- ERROR 1142 (42000): INSERT command denied to user 'seoul_ro'@'%' for table 'sales_2024'
```

### 3. 애플리케이션 테스트
```python
# Python에서 READ-ONLY 연결 테스트
from data.database_manager import DatabaseManager
from config import get_database_config

# READ-ONLY 연결 설정
config = get_database_config()
config.MYSQL_URL = config.MYSQL_URL_RO

# 데이터베이스 매니저 초기화
db_manager = DatabaseManager()

# SELECT 쿼리 실행
result = db_manager.execute_query("SELECT COUNT(*) FROM sales_2024")
print(f"Total records: {result.fetchone()[0]}")

# INSERT 시도 (실패해야 함)
try:
    db_manager.execute_query("INSERT INTO sales_2024 VALUES (1, 1, '2024-01-01', 1000, 10, 20)")
except Exception as e:
    print(f"INSERT blocked: {e}")
```

## 운영 환경 보안 강화

### 1. 비밀번호 변경
```sql
-- 강력한 비밀번호로 변경
ALTER USER 'seoul_ro'@'%' IDENTIFIED BY 'StrongPassword123!@#';
```

### 2. 호스트 제한
```sql
-- 특정 IP에서만 접근 허용
DROP USER 'seoul_ro'@'%';
CREATE USER 'seoul_ro'@'192.168.1.100' IDENTIFIED BY 'StrongPassword123!@#';
GRANT SELECT ON seoul_commercial.* TO 'seoul_ro'@'192.168.1.100';
FLUSH PRIVILEGES;
```

### 3. SSL 연결 강제
```sql
-- SSL 연결만 허용
ALTER USER 'seoul_ro'@'%' REQUIRE SSL;
```

### 4. 연결 수 제한
```sql
-- 최대 연결 수 제한
ALTER USER 'seoul_ro'@'%' WITH MAX_CONNECTIONS_PER_HOUR 100;
```

## 모니터링

### 1. 연결 모니터링
```sql
-- 현재 연결 상태 확인
SELECT * FROM information_schema.processlist WHERE user = 'seoul_ro';

-- 연결 통계
SELECT * FROM performance_schema.accounts WHERE user = 'seoul_ro';
```

### 2. 쿼리 로깅
```sql
-- 일반 쿼리 로그 활성화
SET GLOBAL general_log = 'ON';
SET GLOBAL general_log_file = '/var/log/mysql/general.log';

-- 슬로우 쿼리 로그 활성화
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow.log';
SET GLOBAL long_query_time = 2;
```

## 문제 해결

### 1. 연결 실패
- 비밀번호 확인
- 호스트 권한 확인
- 방화벽 설정 확인

### 2. 권한 오류
- GRANT 문법 확인
- FLUSH PRIVILEGES 실행
- 사용자 존재 여부 확인

### 3. 성능 이슈
- 인덱스 사용 여부 확인
- 쿼리 최적화
- 연결 풀 설정

## 참고사항

- READ-ONLY 계정은 Text-to-SQL 서비스에서만 사용
- 정기적인 비밀번호 변경 권장
- 접근 로그 모니터링 필수
- 백업 시에는 별도 계정 사용

## 관련 파일

- `schema/0002_constraints.sql`: READ-ONLY 계정 생성 스크립트
- `env.example`: 환경 변수 예시
- `config.py`: 데이터베이스 설정 관리
- `data/database_manager.py`: 데이터베이스 연결 관리

