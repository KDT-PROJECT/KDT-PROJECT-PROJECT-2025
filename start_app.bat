@echo off
set ALLOWED_TABLES=sales_2024,regions,industries,features,docs,query_logs,v_sales_validation,v_region_sales_summary,v_industry_sales_summary,v_monthly_sales_trend,information_schema
set GEMINI_API_KEY=AIzaSyCBq39sdhXGZuBBdpZlB0mdjOdYxWP3oJQ
set DB_HOST=localhost
set DB_PORT=3306
set DB_USER=test
set DB_PASSWORD=test
set DB_NAME=test_db
set MAX_QUERY_LENGTH=5000
set MAX_EXECUTION_TIME=30
set MAX_RESULT_ROWS=10000

echo Starting Seoul Commercial Analysis App...
echo Environment variables set:
echo - ALLOWED_TABLES: %ALLOWED_TABLES%
echo - GEMINI_API_KEY: Configured
echo - Database: %DB_USER%@%DB_HOST%:%DB_PORT%/%DB_NAME%
echo.

python -m streamlit run app.py
