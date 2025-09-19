-- MySQL READ-ONLY 사용자 생성 스크립트

-- READ-ONLY 사용자 생성
CREATE USER IF NOT EXISTS 'seoul_ro'@'%' IDENTIFIED BY 'seoul_ro_password_2024';
CREATE USER IF NOT EXISTS 'seoul_ro'@'localhost' IDENTIFIED BY 'seoul_ro_password_2024';

-- 데이터베이스 선택
USE seoul_commercial;

-- 기본 SELECT 권한 부여
GRANT SELECT ON seoul_commercial.* TO 'seoul_ro'@'%';
GRANT SELECT ON seoul_commercial.* TO 'seoul_ro'@'localhost';

-- 권한 변경사항 적용
FLUSH PRIVILEGES;

-- 사용자 확인
SELECT User, Host FROM mysql.user WHERE User = 'seoul_ro';

-- 권한 확인
SHOW GRANTS FOR 'seoul_ro'@'%';
SHOW GRANTS FOR 'seoul_ro'@'localhost';