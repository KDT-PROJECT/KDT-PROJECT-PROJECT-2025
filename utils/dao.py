"""
Data Access Object (DAO) for SQL execution
TASK-003: SQL 가드 및 실행 DAO
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import mysql.connector
import pandas as pd
from mysql.connector import Error

from infrastructure.decorators import error_handler, performance_monitor, retry_on_error
from infrastructure.error_handler import ErrorType, StandardError
from infrastructure.logging_service import StructuredLogger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLDAO:
    """Data Access Object for SQL operations."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SQL DAO.

        Args:
            config: Database configuration dictionary
        """
        self.config = config
        self.logger = StructuredLogger("sql_dao")
        self.connection_pool = None
        self._initialize_connection_pool()

    def _initialize_connection_pool(self):
        """Initialize MySQL connection pool."""
        try:
            # For now, we'll use single connections
            # In production, consider using mysql.connector.pooling
            self.logger.info("SQL DAO initialized with single connection mode")
        except Exception as e:
            self.logger.error(f"Error initializing connection pool: {e}")
            raise

    @performance_monitor(operation_name="sql_execution")
    @error_handler(error_type=ErrorType.DATABASE_ERROR)
    @retry_on_error(max_attempts=3, base_delay=1.0)
    def execute_query(self, query: str, params: Optional[List] = None) -> Dict[str, Any]:
        """
        Execute SQL query with error handling and performance monitoring.

        Args:
            query: SQL query string
            params: Query parameters (optional)

        Returns:
            Dictionary containing query results and metadata
        """
        connection = None
        cursor = None
        
        try:
            # Create connection
            connection = mysql.connector.connect(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 3306),
                user=self.config.get("user", "seoul_ro"),
                password=self.config.get("password", "seoul_ro_password_2024"),
                database=self.config.get("database", "seoul_commercial"),
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci",
                autocommit=True
            )

            if not connection or not connection.is_connected():
                raise StandardError("Failed to connect to database")

            cursor = connection.cursor(dictionary=True)
            
            # Execute query
            start_time = time.time()
            cursor.execute(query, params or [])
            
            # Get results
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
            else:
                results = []
            
            execution_time = time.time() - start_time
            
            # Log successful execution
            self.logger.info(
                f"Query executed successfully",
                extra={
                    "query": query[:100] + "..." if len(query) > 100 else query,
                    "execution_time": execution_time,
                    "result_count": len(results) if isinstance(results, list) else 0
                }
            )

            return {
                "status": "success",
                "results": results,
                "execution_time": execution_time,
                "row_count": len(results) if isinstance(results, list) else 0,
                "timestamp": datetime.now().isoformat()
            }

        except Error as e:
            self.logger.error(f"MySQL error: {e}")
            return {
                "status": "error",
                "message": f"Database error: {str(e)}",
                "error_code": e.errno,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        finally:
            try:
                if cursor:
                    cursor.close()
            except Exception as e:
                self.logger.warning(f"Error closing cursor: {e}")
            
            try:
                if connection and connection.is_connected():
                    connection.close()
            except Exception as e:
                self.logger.warning(f"Error closing connection: {e}")

    def execute_batch(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Execute multiple queries in batch.

        Args:
            queries: List of SQL queries

        Returns:
            List of results for each query
        """
        results = []
        for query in queries:
            result = self.execute_query(query)
            results.append(result)
        return results

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get table information.

        Args:
            table_name: Name of the table

        Returns:
            Table information dictionary
        """
        query = f"DESCRIBE {table_name}"
        return self.execute_query(query)

    def get_table_count(self, table_name: str) -> Dict[str, Any]:
        """
        Get row count for a table.

        Args:
            table_name: Name of the table

        Returns:
            Row count result
        """
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        return self.execute_query(query)

    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validate SQL query without executing.

        Args:
            query: SQL query to validate

        Returns:
            Validation result
        """
        try:
            # Basic validation
            query_upper = query.strip().upper()
            
            # Check for dangerous operations
            dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 'TRUNCATE']
            for keyword in dangerous_keywords:
                if keyword in query_upper:
                    return {
                        "valid": False,
                        "message": f"Dangerous operation detected: {keyword}"
                    }
            
            # Check for SELECT statement
            if not query_upper.startswith('SELECT'):
                return {
                    "valid": False,
                    "message": "Only SELECT queries are allowed"
                }
            
            # Check for LIMIT clause
            if 'LIMIT' not in query_upper:
                return {
                    "valid": False,
                    "message": "LIMIT clause is required"
                }
            
            return {
                "valid": True,
                "message": "Query is valid"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "message": f"Validation error: {str(e)}"
            }


def run_sql(query: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute SQL query using SQLDAO.

    Args:
        query: SQL query string
        config: Database configuration

    Returns:
        Query execution result
    """
    try:
        dao = SQLDAO(config)
        return dao.execute_query(query)
    except Exception as e:
        logger.error(f"Error in run_sql: {e}")
        return {
            "status": "error",
            "message": f"Failed to execute query: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


def validate_sql(query: str) -> Dict[str, Any]:
    """
    Validate SQL query.

    Args:
        query: SQL query to validate

    Returns:
        Validation result
    """
    try:
        dao = SQLDAO({})  # Empty config for validation
        return dao.validate_query(query)
    except Exception as e:
        logger.error(f"Error in validate_sql: {e}")
        return {
            "valid": False,
            "message": f"Validation error: {str(e)}"
        }


if __name__ == "__main__":
    # Test the DAO
    test_config = {
        "host": "localhost",
        "port": 3306,
        "user": "seoul_ro",
        "password": "seoul_ro_password_2024",
        "database": "seoul_commercial"
    }
    
    dao = SQLDAO(test_config)
    print("SQL DAO initialized successfully")