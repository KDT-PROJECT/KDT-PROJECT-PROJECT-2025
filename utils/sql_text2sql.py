"""
Text-to-SQL 변환 모듈 (TASK1 스텁)
PRD TASK3에서 LlamaIndex 기반으로 완전 구현 예정
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def nl_to_sql(nl_query: str, schema_prompt: str = None, llm_cfg: Dict[str, Any] = None) -> str:
    """
    자연어 질의를 SQL로 변환하는 함수 (스텁)

    Args:
        nl_query: 자연어 질의
        schema_prompt: 스키마 프롬프트 (선택사항)
        llm_cfg: LLM 설정 (선택사항)

    Returns:
        생성된 SQL 쿼리
    """
    try:
        logger.info(f"NL→SQL 변환 요청: {nl_query}")

        # TASK1 스텁: 기본 SQL 템플릿 반환
        # TODO: TASK3에서 LlamaIndex + HuggingFace LLM으로 구현

        # 실제 commercial_analysis 테이블 스키마에 맞춘 SQL 생성
        nl_query_lower = nl_query.lower()

        # 상권별 매출 분석
        if "상권" in nl_query and "매출" in nl_query:
            return """
            SELECT 상권코드명, 서비스업종코드명,
                   SUM(당월매출금액) as 총매출금액,
                   COUNT(*) as 점포수
            FROM commercial_analysis
            WHERE 당월매출금액 > 0
            GROUP BY 상권코드명, 서비스업종코드명
            ORDER BY 총매출금액 DESC
            LIMIT 20
            """

        # 업종별 매출 분석
        elif "업종" in nl_query and "매출" in nl_query:
            return """
            SELECT 서비스업종코드명,
                   SUM(당월매출금액) as 총매출금액,
                   AVG(당월매출금액) as 평균매출금액,
                   COUNT(*) as 점포수
            FROM commercial_analysis
            WHERE 당월매출금액 > 0
            GROUP BY 서비스업종코드명
            ORDER BY 총매출금액 DESC
            LIMIT 15
            """

        # 시간대별 매출 분석
        elif "시간대" in nl_query or "시간" in nl_query:
            return """
            SELECT '00-06시' as 시간대, SUM(시간대00_06매출금액) as 매출금액, SUM(시간대00_06매출건수) as 매출건수
            FROM commercial_analysis WHERE 시간대00_06매출금액 > 0
            UNION ALL
            SELECT '06-11시' as 시간대, SUM(시간대06_11매출금액), SUM(시간대06_11매출건수)
            FROM commercial_analysis WHERE 시간대06_11매출금액 > 0
            UNION ALL
            SELECT '11-14시' as 시간대, SUM(시간대11_14매출금액), SUM(시간대11_14매출건수)
            FROM commercial_analysis WHERE 시간대11_14매출금액 > 0
            UNION ALL
            SELECT '14-17시' as 시간대, SUM(시간대14_17매출금액), SUM(시간대14_17매출건수)
            FROM commercial_analysis WHERE 시간대14_17매출금액 > 0
            UNION ALL
            SELECT '17-21시' as 시간대, SUM(시간대17_21매출금액), SUM(시간대17_21매출건수)
            FROM commercial_analysis WHERE 시간대17_21매출금액 > 0
            UNION ALL
            SELECT '21-24시' as 시간대, SUM(시간대21_24매출금액), SUM(시간대21_24매출건수)
            FROM commercial_analysis WHERE 시간대21_24매출금액 > 0
            ORDER BY 매출금액 DESC
            """

        # 요일별 매출 분석
        elif "요일" in nl_query:
            return """
            SELECT '월요일' as 요일, SUM(월요일매출금액) as 매출금액, SUM(월요일매출건수) as 매출건수
            FROM commercial_analysis WHERE 월요일매출금액 > 0
            UNION ALL
            SELECT '화요일', SUM(화요일매출금액), SUM(화요일매출건수)
            FROM commercial_analysis WHERE 화요일매출금액 > 0
            UNION ALL
            SELECT '수요일', SUM(수요일매출금액), SUM(수요일매출건수)
            FROM commercial_analysis WHERE 수요일매출금액 > 0
            UNION ALL
            SELECT '목요일', SUM(목요일매출금액), SUM(목요일매출건수)
            FROM commercial_analysis WHERE 목요일매출금액 > 0
            UNION ALL
            SELECT '금요일', SUM(금요일매출금액), SUM(금요일매출건수)
            FROM commercial_analysis WHERE 금요일매출금액 > 0
            UNION ALL
            SELECT '토요일', SUM(토요일매출금액), SUM(토요일매출건수)
            FROM commercial_analysis WHERE 토요일매출금액 > 0
            UNION ALL
            SELECT '일요일', SUM(일요일매출금액), SUM(일요일매출건수)
            FROM commercial_analysis WHERE 일요일매출금액 > 0
            ORDER BY 매출금액 DESC
            """

        # 연령대별 매출 분석
        elif "연령" in nl_query or "나이" in nl_query:
            return """
            SELECT '10대' as 연령대, SUM(연령대10매출금액) as 매출금액, SUM(연령대10매출건수) as 매출건수
            FROM commercial_analysis WHERE 연령대10매출금액 > 0
            UNION ALL
            SELECT '20대', SUM(연령대20매출금액), SUM(연령대20매출건수)
            FROM commercial_analysis WHERE 연령대20매출금액 > 0
            UNION ALL
            SELECT '30대', SUM(연령대30매출금액), SUM(연령대30매출건수)
            FROM commercial_analysis WHERE 연령대30매출금액 > 0
            UNION ALL
            SELECT '40대', SUM(연령대40매출금액), SUM(연령대40매출건수)
            FROM commercial_analysis WHERE 연령대40매출금액 > 0
            UNION ALL
            SELECT '50대', SUM(연령대50매출금액), SUM(연령대50매출건수)
            FROM commercial_analysis WHERE 연령대50매출금액 > 0
            UNION ALL
            SELECT '60대이상', SUM(연령대60이상매출금액), SUM(연령대60이상매출건수)
            FROM commercial_analysis WHERE 연령대60이상매출금액 > 0
            ORDER BY 매출금액 DESC
            """

        # 성별 매출 분석
        elif "성별" in nl_query or "남성" in nl_query or "여성" in nl_query:
            return """
            SELECT '남성' as 성별, SUM(남성매출금액) as 매출금액, SUM(남성매출건수) as 매출건수
            FROM commercial_analysis WHERE 남성매출금액 > 0
            UNION ALL
            SELECT '여성', SUM(여성매출금액), SUM(여성매출건수)
            FROM commercial_analysis WHERE 여성매출금액 > 0
            ORDER BY 매출금액 DESC
            """
        else:
            # 기본 쿼리 - 전체 데이터 요약
            sql = """
            SELECT
                r.gu as 구,
                i.industry_name as 업종명,
                SUM(s.monthly_sales_amount) as 총매출금액,
                SUM(s.monthly_sales_count) as 총매출건수,
                COUNT(*) as 데이터건수
            FROM sales_2024 s
            JOIN commercial_areas ca ON s.area_id = ca.area_id
            JOIN regions r ON ca.region_id = r.region_id
            JOIN industries i ON s.industry_id = i.industry_id
            GROUP BY r.gu, i.industry_name
            ORDER BY 총매출금액 DESC
            LIMIT 20
            """

        logger.info("NL→SQL 변환 완료 (스텁)")
        return sql.strip()

    except Exception as e:
        logger.error(f"NL→SQL 변환 실패: {str(e)}")
        return "SELECT 1 as error_fallback"

def validate_sql_query(sql: str) -> Dict[str, Any]:
    """
    SQL 쿼리 검증 함수 (스텁)

    Args:
        sql: SQL 쿼리

    Returns:
        검증 결과
    """
    try:
        # 기본 보안 검증
        sql_lower = sql.lower().strip()

        # SELECT만 허용
        if not sql_lower.startswith('select'):
            return {"valid": False, "message": "SELECT 쿼리만 허용됩니다."}

        # 금지된 키워드 검사
        forbidden_keywords = ['drop', 'delete', 'insert', 'update', 'create', 'alter', 'truncate']
        for keyword in forbidden_keywords:
            if keyword in sql_lower:
                return {"valid": False, "message": f"금지된 키워드가 포함되어 있습니다: {keyword}"}

        # LIMIT 체크
        if 'limit' not in sql_lower:
            return {"valid": False, "message": "LIMIT 절이 필요합니다."}

        return {"valid": True, "message": "SQL 쿼리가 유효합니다."}

    except Exception as e:
        logger.error(f"SQL 검증 실패: {str(e)}")
        return {"valid": False, "message": str(e)}