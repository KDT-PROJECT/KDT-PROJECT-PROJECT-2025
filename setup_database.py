#!/usr/bin/env python3
"""
Database Setup Script
데이터베이스 초기화 및 테이블 생성 스크립트
"""

import mysql.connector
import sys
from pathlib import Path
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_database_connection(host="localhost", user="root", password="", port=3306):
    """데이터베이스 연결 생성"""
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            charset='utf8mb4',
            autocommit=True
        )
        logger.info(f"MySQL 서버에 연결되었습니다: {host}:{port}")
        return connection
    except mysql.connector.Error as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        return None

def execute_sql_file(connection, sql_file_path):
    """SQL 파일 실행"""
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()

        # SQL 스크립트를 개별 명령문으로 분할
        commands = []
        current_command = ""
        in_delimiter_block = False

        for line in sql_script.split('\n'):
            line = line.strip()

            # 빈 줄이나 주석 제거
            if not line or line.startswith('--'):
                continue

            # DELIMITER 처리
            if line.startswith('DELIMITER'):
                in_delimiter_block = True
                continue

            current_command += line + " "

            # 명령문 종료 확인
            if not in_delimiter_block and line.endswith(';'):
                commands.append(current_command.strip())
                current_command = ""
            elif in_delimiter_block and line.endswith(' //'):
                commands.append(current_command.strip())
                current_command = ""
                in_delimiter_block = False

        # 마지막 명령문 추가
        if current_command.strip():
            commands.append(current_command.strip())

        cursor = connection.cursor()
        success_count = 0

        for i, command in enumerate(commands):
            command = command.strip()
            if not command:
                continue

            try:
                # DELIMITER 관련 명령은 건너뛰기
                if command.startswith('DELIMITER'):
                    continue

                logger.info(f"실행 중: 명령 {i+1}/{len(commands)}")
                logger.debug(f"SQL: {command[:100]}...")

                cursor.execute(command)
                success_count += 1

            except mysql.connector.Error as e:
                logger.warning(f"명령 실행 실패 (계속 진행): {e}")
                logger.debug(f"실패한 SQL: {command}")

        cursor.close()
        logger.info(f"SQL 파일 실행 완료: {success_count}/{len(commands)} 명령 성공")
        return True

    except Exception as e:
        logger.error(f"SQL 파일 실행 중 오류: {e}")
        return False

def verify_tables(connection, database_name):
    """테이블 생성 확인"""
    try:
        cursor = connection.cursor()
        cursor.execute(f"USE {database_name}")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        logger.info(f"생성된 테이블 목록 ({database_name}):")
        for table in tables:
            logger.info(f"  - {table[0]}")

        # sales_data 테이블 구체적 확인
        cursor.execute("DESCRIBE sales_data")
        columns = cursor.fetchall()
        logger.info("sales_data 테이블 구조:")
        for column in columns:
            logger.info(f"  - {column[0]}: {column[1]}")

        # 샘플 데이터 확인
        cursor.execute("SELECT COUNT(*) FROM sales_data")
        count = cursor.fetchone()[0]
        logger.info(f"sales_data 테이블 데이터 개수: {count}")

        cursor.close()
        return True

    except mysql.connector.Error as e:
        logger.error(f"테이블 확인 중 오류: {e}")
        return False

def main():
    """메인 함수"""
    logger.info("=== 데이터베이스 설정 스크립트 시작 ===")

    # 연결 정보 (.env 파일 기반)
    DB_CONFIG = {
        "host": "localhost",
        "user": "test",
        "password": "test",
        "port": 3306
    }

    # SQL 파일 경로
    sql_file = Path(__file__).parent / "database_setup.sql"

    if not sql_file.exists():
        logger.error(f"SQL 파일을 찾을 수 없습니다: {sql_file}")
        sys.exit(1)

    # 데이터베이스 연결
    connection = create_database_connection(**DB_CONFIG)
    if not connection:
        logger.error("데이터베이스 연결에 실패했습니다.")
        sys.exit(1)

    try:
        # SQL 스크립트 실행
        logger.info("데이터베이스 및 테이블 생성 중...")
        if execute_sql_file(connection, sql_file):
            logger.info("데이터베이스 설정이 완료되었습니다.")

            # 테이블 확인
            logger.info("테이블 생성 확인 중...")
            verify_tables(connection, "test_db")

        else:
            logger.error("데이터베이스 설정 중 오류가 발생했습니다.")
            sys.exit(1)

    finally:
        connection.close()
        logger.info("데이터베이스 연결이 종료되었습니다.")

    logger.info("=== 데이터베이스 설정 완료 ===")

if __name__ == "__main__":
    main()