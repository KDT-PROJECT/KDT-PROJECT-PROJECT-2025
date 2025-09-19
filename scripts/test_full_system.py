#!/usr/bin/env python3
"""
Full System Test for Seoul Commercial Analysis LLM System
Tests all 4 tasks: Project Bootstrap, MySQL Schema, Text-to-SQL & RAG, Streamlit Frontend
"""

import sys
from pathlib import Path
import logging
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_task1_bootstrap():
    """Test TASK 1: Project Bootstrap"""
    logger.info("=== Testing TASK 1: Project Bootstrap ===")

    try:
        # Test module imports
        from utils.sql_text2sql import nl_to_sql, validate_sql_query
        from utils.rag_hybrid import index_pdfs, hybrid_search
        from utils.dao import run_sql, test_connection
        from utils.viz import create_line_chart, create_bar_chart
        from utils.data_loader import load_csv_to_mysql

        logger.info("✅ All utility modules imported successfully")

        # Test app module
        import app
        assert hasattr(app, 'main'), "App must have main function"
        assert hasattr(app, 'render_sql_tab'), "App must have render_sql_tab function"
        assert hasattr(app, 'render_rag_tab'), "App must have render_rag_tab function"
        assert hasattr(app, 'render_report_tab'), "App must have render_report_tab function"

        logger.info("✅ App module structure verified")
        return True

    except Exception as e:
        logger.error(f"❌ TASK 1 failed: {e}")
        return False

def test_task2_schema():
    """Test TASK 2: MySQL Schema Setup"""
    logger.info("=== Testing TASK 2: MySQL Schema Setup ===")

    try:
        from utils.dao import test_connection

        # Test database connection
        mysql_url = "mysql+pymysql://test:test@localhost:3306/test_db"
        result = test_connection(mysql_url)

        logger.info(f"Database connection test: {result['status']}")

        # Test SQL validation
        from utils.sql_text2sql import validate_sql_query

        valid_sql = "SELECT * FROM sales_2024 LIMIT 10"
        validation = validate_sql_query(valid_sql)
        assert validation['valid'], "Valid SQL should pass validation"

        invalid_sql = "DROP TABLE sales_2024"
        validation = validate_sql_query(invalid_sql)
        assert not validation['valid'], "Invalid SQL should fail validation"

        logger.info("✅ Schema and SQL validation working")
        return True

    except Exception as e:
        logger.error(f"❌ TASK 2 failed: {e}")
        return False

def test_task3_text2sql_rag():
    """Test TASK 3: Text-to-SQL & Hybrid RAG"""
    logger.info("=== Testing TASK 3: Text-to-SQL & Hybrid RAG ===")

    try:
        from utils.sql_text2sql import nl_to_sql
        from utils.dao import run_sql
        from utils.rag_hybrid import index_pdfs, hybrid_search

        # Test Text-to-SQL
        nl_query = "강남구 매출 조회"
        sql = nl_to_sql(nl_query)
        assert sql and len(sql) > 0, "NL-to-SQL should generate SQL"
        assert "SELECT" in sql.upper(), "Generated SQL should be SELECT query"
        assert "LIMIT" in sql.upper(), "Generated SQL should have LIMIT clause"

        logger.info("✅ Text-to-SQL generation working")

        # Test SQL execution
        mysql_url = "mysql+pymysql://test:test@localhost:3306/test_db"
        df = run_sql(sql, mysql_url)
        assert isinstance(df, pd.DataFrame), "SQL execution should return DataFrame"

        logger.info(f"✅ SQL execution working: {len(df)} rows returned")

        # Test Hybrid RAG
        test_pdfs = ["test.pdf", "example.pdf"]
        index_result = index_pdfs(test_pdfs)
        assert index_result['status'] == 'success', "PDF indexing should succeed"

        search_results = hybrid_search("강남구 창업 지원")
        assert isinstance(search_results, list), "Search should return list"
        assert len(search_results) > 0, "Search should return results"

        logger.info("✅ Hybrid RAG working")
        return True

    except Exception as e:
        logger.error(f"❌ TASK 3 failed: {e}")
        return False

def test_task4_frontend():
    """Test TASK 4: Streamlit Frontend"""
    logger.info("=== Testing TASK 4: Streamlit Frontend ===")

    try:
        import streamlit as st
        import app

        # Test app functions exist
        required_functions = [
            'render_sql_tab',
            'render_rag_tab',
            'render_report_tab',
            'render_data_loading_section'
        ]

        for func_name in required_functions:
            assert hasattr(app, func_name), f"App must have {func_name} function"
            assert callable(getattr(app, func_name)), f"{func_name} must be callable"

        logger.info("✅ All required UI functions available")

        # Test report composition using app function
        # Create sample data
        sample_df = pd.DataFrame({
            '구': ['강남구', '마포구'],
            '업종명': ['음식점', '카페'],
            '매출금액': [1000000, 500000]
        })

        sample_passages = [
            {'text': '강남구 창업 지원 정보', 'source': 'test.pdf', 'page': 1}
        ]

        # Test the compose_report function from app module
        report = app.compose_report(sample_df, sample_passages, {'p95': 2.5})
        assert isinstance(report, dict), "Report generation should return dict"
        assert 'markdown' in report, "Report should contain markdown"

        logger.info("✅ Report generation working")
        return True

    except Exception as e:
        logger.error(f"❌ TASK 4 failed: {e}")
        return False

def main():
    """Run all system tests"""
    logger.info("🚀 Starting Full System Test for Seoul Commercial Analysis LLM System")

    results = {
        'task1_bootstrap': test_task1_bootstrap(),
        'task2_schema': test_task2_schema(),
        'task3_text2sql_rag': test_task3_text2sql_rag(),
        'task4_frontend': test_task4_frontend()
    }

    # Summary
    logger.info("=" * 60)
    logger.info("📊 SYSTEM TEST RESULTS:")
    logger.info("=" * 60)

    total_tests = len(results)
    passed_tests = sum(results.values())

    for task, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{task.upper()}: {status}")

    logger.info(f"\nOVERALL: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED! System is ready for use.")
        return True
    else:
        logger.warning("⚠️ Some tests failed. Please check the logs above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)