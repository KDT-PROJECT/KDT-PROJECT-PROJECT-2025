"""
Text-to-SQL 변환 모듈
PRD TASK1: LlamaIndex Text-to-SQL 스텁
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def nl_to_sql(nl_query: str, schema_prompt: str, llm_cfg: Dict[str, Any]) -> str:
    """
    자연어 질의를 SQL로 변환하는 함수 (스텁)
    
    Args:
        nl_query: 자연어 질의
        schema_prompt: 스키마 프롬프트
        llm_cfg: LLM 설정
        
    Returns:
        생성된 SQL 쿼리
    """
    try:
        # 기본 SQL 가드
        if not nl_query or len(nl_query.strip()) == 0:
            return "SELECT 1 as error WHERE 1=0"
        
        # 금지 키워드 검사
        forbidden_keywords = [
            "INSERT", "UPDATE", "DELETE", "ALTER", "DROP", "TRUNCATE",
            "GRANT", "REVOKE", "CREATE", "EXEC", "EXECUTE"
        ]
        
        query_upper = nl_query.upper()
        for keyword in forbidden_keywords:
            if keyword in query_upper:
                logger.warning(f"금지된 키워드 감지: {keyword}")
                return "SELECT 1 as error WHERE 1=0"
        
        # 기본 SQL 생성 (스텁)
        if "매출" in nl_query or "sales" in nl_query.lower():
            if "월별" in nl_query or "monthly" in nl_query.lower():
                return """
                SELECT 
                    DATE_FORMAT(date, '%Y-%m') as month,
                    SUM(sales_amt) as total_sales,
                    AVG(sales_amt) as avg_sales
                FROM sales_2024 
                GROUP BY DATE_FORMAT(date, '%Y-%m')
                ORDER BY month
                LIMIT 1000
                """
            else:
                return """
                SELECT 
                    r.name as region,
                    i.name as industry,
                    SUM(s.sales_amt) as total_sales,
                    COUNT(*) as record_count
                FROM sales_2024 s
                JOIN regions r ON s.region_id = r.region_id
                JOIN industries i ON s.industry_id = i.industry_id
                GROUP BY r.name, i.name
                ORDER BY total_sales DESC
                LIMIT 1000
                """
        elif "지역" in nl_query or "region" in nl_query.lower():
            return """
            SELECT 
                r.name as region,
                r.gu,
                r.dong,
                COUNT(*) as sales_count
            FROM sales_2024 s
            JOIN regions r ON s.region_id = r.region_id
            GROUP BY r.name, r.gu, r.dong
            ORDER BY sales_count DESC
            LIMIT 1000
            """
        else:
            # 기본 쿼리
            return """
            SELECT 
                s.date,
                r.name as region,
                i.name as industry,
                s.sales_amt,
                s.sales_cnt,
                s.visitors
            FROM sales_2024 s
            JOIN regions r ON s.region_id = r.region_id
            JOIN industries i ON s.industry_id = i.industry_id
            ORDER BY s.date DESC
            LIMIT 1000
            """
            
    except Exception as e:
        logger.error(f"SQL 변환 실패: {str(e)}")
        return "SELECT 1 as error WHERE 1=0"

def validate_sql(sql: str) -> Dict[str, Any]:
    """
    SQL 쿼리 유효성 검사
    
    Args:
        sql: 검사할 SQL 쿼리
        
    Returns:
        검증 결과 딕셔너리
    """
    try:
        sql_upper = sql.upper().strip()
        
        # SELECT만 허용
        if not sql_upper.startswith("SELECT"):
            return {"valid": False, "message": "SELECT 쿼리만 허용됩니다."}
        
        # 금지 키워드 검사
        forbidden_keywords = [
            "INSERT", "UPDATE", "DELETE", "ALTER", "DROP", "TRUNCATE",
            "GRANT", "REVOKE", "CREATE", "EXEC", "EXECUTE"
        ]
        
        for keyword in forbidden_keywords:
            if keyword in sql_upper:
                return {"valid": False, "message": f"금지된 키워드: {keyword}"}
        
        # LIMIT 강제 추가 (없는 경우)
        if "LIMIT" not in sql_upper:
            sql = sql.rstrip(";") + " LIMIT 1000"
        
        return {"valid": True, "sql": sql}
        
    except Exception as e:
        logger.error(f"SQL 검증 실패: {str(e)}")
        return {"valid": False, "message": str(e)}