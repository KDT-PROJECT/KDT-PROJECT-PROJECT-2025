#!/usr/bin/env python3
"""
MySQL Schema Setup Script for Seoul Commercial Analysis LLM System
PRD TASK2: 스키마 생성 및 초기화
"""

import mysql.connector
import os
import sys
from pathlib import Path
import logging
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_connection(config: Dict[str, Any]) -> mysql.connector.MySQLConnection:
    """Create MySQL connection"""
    try:
        connection = mysql.connector.connect(**config)
        logger.info(f"Connected to MySQL: {config['host']}:{config['port']}")
        return connection
    except mysql.connector.Error as e:
        logger.error(f"Failed to connect to MySQL: {e}")
        raise

def execute_sql_file(connection: mysql.connector.MySQLConnection, sql_file_path: Path) -> bool:
    """Execute SQL file"""
    try:
        logger.info(f"Executing SQL file: {sql_file_path}")

        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()

        cursor = connection.cursor()

        # Split SQL content into individual statements
        statements = []
        current_statement = ""
        in_delimiter_block = False

        for line in sql_content.split('\n'):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('--'):
                continue

            # Handle DELIMITER blocks
            if line.startswith('DELIMITER'):
                if '$$' in line:
                    in_delimiter_block = True
                else:
                    in_delimiter_block = False
                continue

            current_statement += line + "\n"

            # Check for statement end
            if not in_delimiter_block and line.endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
            elif in_delimiter_block and line.endswith('$$'):
                statements.append(current_statement.strip())
                current_statement = ""
                in_delimiter_block = False

        # Add any remaining statement
        if current_statement.strip():
            statements.append(current_statement.strip())

        # Execute statements
        success_count = 0
        for i, statement in enumerate(statements):
            statement = statement.strip()
            if not statement:
                continue

            try:
                logger.debug(f"Executing statement {i+1}/{len(statements)}")
                cursor.execute(statement)
                connection.commit()
                success_count += 1
            except mysql.connector.Error as e:
                logger.warning(f"Statement {i+1} failed (continuing): {e}")
                logger.debug(f"Failed statement: {statement[:100]}...")

        cursor.close()
        logger.info(f"SQL file executed: {success_count}/{len(statements)} statements successful")
        return True

    except Exception as e:
        logger.error(f"Error executing SQL file: {e}")
        return False

def verify_schema(connection: mysql.connector.MySQLConnection) -> bool:
    """Verify schema creation"""
    try:
        cursor = connection.cursor()

        # Check if database exists
        cursor.execute("SHOW DATABASES LIKE 'seoul_commercial'")
        if not cursor.fetchone():
            logger.error("Database 'seoul_commercial' not found")
            return False

        # Switch to the database
        cursor.execute("USE seoul_commercial")

        # Check required tables
        required_tables = [
            'regions', 'industries', 'commercial_areas',
            'sales_2024', 'docs', 'query_logs'
        ]

        cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in cursor.fetchall()]

        logger.info(f"Existing tables: {existing_tables}")

        # Verify all required tables exist
        missing_tables = [table for table in required_tables if table not in existing_tables]
        if missing_tables:
            logger.warning(f"Missing tables: {missing_tables}")
        else:
            logger.info("All required tables exist")

        # Check sales_2024 table structure
        try:
            cursor.execute("DESCRIBE sales_2024")
            columns = cursor.fetchall()
            logger.info(f"sales_2024 table has {len(columns)} columns")
        except mysql.connector.Error as e:
            logger.error(f"Error checking sales_2024 structure: {e}")

        # Check READ-ONLY user
        try:
            cursor.execute("SELECT User FROM mysql.user WHERE User='seoul_ro'")
            if cursor.fetchone():
                logger.info("READ-ONLY user 'seoul_ro' exists")
            else:
                logger.warning("READ-ONLY user 'seoul_ro' not found")
        except mysql.connector.Error as e:
            logger.warning(f"Could not check READ-ONLY user: {e}")

        cursor.close()
        return True

    except Exception as e:
        logger.error(f"Error verifying schema: {e}")
        return False

def main():
    """Main function"""
    logger.info("=== Seoul Commercial LLM System - MySQL Schema Setup ===")

    # Database configuration
    db_config = {
        'host': 'localhost',
        'user': 'test',
        'password': 'test',
        'port': 3306,
        'charset': 'utf8mb4',
        'autocommit': True
    }

    # SQL files to execute
    schema_dir = project_root / 'schema'
    sql_files = [
        schema_dir / '0001_init.sql',
        schema_dir / '0002_constraints.sql',
    ]

    # Check if SQL files exist
    for sql_file in sql_files:
        if not sql_file.exists():
            logger.error(f"SQL file not found: {sql_file}")
            sys.exit(1)

    try:
        # Create connection
        connection = create_connection(db_config)

        # Execute schema files
        for sql_file in sql_files:
            logger.info(f"Executing {sql_file.name}...")
            if not execute_sql_file(connection, sql_file):
                logger.error(f"Failed to execute {sql_file.name}")
                sys.exit(1)

        # Verify schema
        logger.info("Verifying schema...")
        if verify_schema(connection):
            logger.info("✅ Schema setup completed successfully!")
        else:
            logger.warning("⚠️ Schema verification found issues")

        connection.close()
        logger.info("Database connection closed")

    except Exception as e:
        logger.error(f"Schema setup failed: {e}")
        sys.exit(1)

    logger.info("=== Schema Setup Complete ===")

if __name__ == "__main__":
    main()