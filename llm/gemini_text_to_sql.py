"""
Gemini 기반 Text-to-SQL 서비스
자연어를 SQL로 변환하는 Gemini API 기반 서비스
"""

import logging
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from config import get_gemini_config

logger = logging.getLogger(__name__)

class GeminiTextToSQLService:
    """Gemini API를 사용한 Text-to-SQL 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.config = get_gemini_config()
        self.model = None
        self.is_available = False
        
        # Gemini API 초기화
        if genai and self.config.GEMINI_API_KEY:
            try:
                genai.configure(api_key=self.config.GEMINI_API_KEY)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
                self.is_available = True
                logger.info("Gemini Text-to-SQL service initialized successfully")
            except Exception as e:
                logger.error(f"Gemini Text-to-SQL service initialization failed: {e}")
                self.is_available = False
        else:
            logger.warning("Gemini API not available")
            self.is_available = False
    
    def convert_to_sql(self, natural_language: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        자연어를 SQL로 변환
        
        Args:
            natural_language: 자연어 질의
            context: 추가 컨텍스트 정보
            
        Returns:
            Dict[str, Any]: 변환 결과
        """
        try:
            if not self.is_available:
                return self._create_fallback_response(natural_language, "Gemini API가 사용할 수 없습니다.")
            
            # 프롬프트 생성
            prompt = self._create_sql_prompt(natural_language, context)
            
            # Gemini API 호출
            response = self.model.generate_content(prompt)
            
            # SQL 추출
            sql_query = self._extract_sql_from_response(response.text)
            
            if sql_query:
                return {
                    "success": True,
                    "sql": sql_query,
                    "natural_language": natural_language,
                    "context": context,
                    "generated_at": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "SQL 쿼리를 생성할 수 없습니다.",
                    "natural_language": natural_language,
                    "context": context,
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Text-to-SQL conversion failed: {e}")
            return {
                "success": False,
                "error": f"SQL 변환 중 오류가 발생했습니다: {str(e)}",
                "natural_language": natural_language,
                "context": context,
                "generated_at": datetime.now().isoformat()
            }
    
    def _create_sql_prompt(self, natural_language: str, context: Dict[str, Any] = None) -> str:
        """SQL 생성 프롬프트 생성"""
        
        # 기본 데이터베이스 스키마 정보
        schema_info = """
        사용 가능한 테이블:
        1. regions - 지역 정보 테이블
           - region_id (INT): 지역 ID
           - region_name (VARCHAR): 지역명
           - region_code (VARCHAR): 지역 코드
           - district (VARCHAR): 구/군
        
        2. industries - 업종 정보 테이블
           - industry_id (INT): 업종 ID
           - industry_name (VARCHAR): 업종명
           - industry_code (VARCHAR): 업종 코드
           - category (VARCHAR): 업종 카테고리
        
        3. sales_2024 - 2024년 매출 데이터 테이블
           - region_id (INT): 지역 ID
           - industry_id (INT): 업종 ID
           - date (DATE): 날짜
           - sales_amount (DECIMAL): 매출액
           - transaction_count (INT): 거래건수
           - avg_transaction_amount (DECIMAL): 평균 거래액
        """
        
        # 컨텍스트 정보 추가
        context_str = ""
        if context:
            context_parts = []
            if context.get("available_tables"):
                context_parts.append(f"사용 가능한 테이블: {', '.join(context['available_tables'])}")
            if context.get("data_sources"):
                context_parts.append(f"데이터 소스: {context['data_sources']}")
            if context.get("query_context"):
                context_parts.append(f"쿼리 컨텍스트: {context['query_context']}")
            context_str = "\n".join(context_parts)
        
        prompt = f"""
당신은 전문적인 SQL 쿼리 생성자입니다. 자연어 질의를 정확한 MySQL SQL 쿼리로 변환해주세요.

**데이터베이스 스키마:**
{schema_info}

**추가 컨텍스트:**
{context_str if context_str else "없음"}

**자연어 질의:**
{natural_language}

**요구사항:**
1. MySQL 문법을 사용하세요
2. SELECT 문만 생성하세요 (INSERT, UPDATE, DELETE 금지)
3. 적절한 JOIN을 사용하여 테이블을 연결하세요
4. 한글 컬럼명과 값은 백틱(`)으로 감싸세요
5. 날짜 필터링이 필요한 경우 적절한 WHERE 조건을 추가하세요
6. 결과는 깔끔하고 실행 가능한 SQL만 반환하세요

**응답 형식:**
생성된 SQL 쿼리만 반환하세요. 설명이나 다른 텍스트는 포함하지 마세요.

예시:
질의: "강남구 음식점업 매출을 조회해주세요"
응답: 
```sql
SELECT s.sales_amount, s.transaction_count, s.avg_transaction_amount
FROM sales_2024 s
JOIN regions r ON s.region_id = r.region_id
JOIN industries i ON s.industry_id = i.industry_id
WHERE r.district = '강남구' AND i.industry_name = '음식점업'
ORDER BY s.sales_amount DESC;
```
"""
        return prompt
    
    def _extract_sql_from_response(self, response_text: str) -> Optional[str]:
        """응답에서 SQL 쿼리 추출"""
        try:
            # 코드 블록에서 SQL 추출
            sql_pattern = r'```(?:sql)?\s*(.*?)\s*```'
            matches = re.findall(sql_pattern, response_text, re.DOTALL | re.IGNORECASE)
            
            if matches:
                return matches[0].strip()
            
            # 코드 블록이 없는 경우 전체 응답에서 SQL 키워드가 있는지 확인
            if any(keyword in response_text.upper() for keyword in ['SELECT', 'FROM', 'WHERE']):
                # SQL 문장만 추출
                lines = response_text.split('\n')
                sql_lines = []
                in_sql = False
                
                for line in lines:
                    line = line.strip()
                    if any(keyword in line.upper() for keyword in ['SELECT', 'FROM', 'WHERE', 'JOIN', 'ORDER BY', 'GROUP BY']):
                        in_sql = True
                    
                    if in_sql:
                        if line.endswith(';') or line == '':
                            sql_lines.append(line)
                            break
                        else:
                            sql_lines.append(line)
                
                if sql_lines:
                    return ' '.join(sql_lines).strip()
            
            return None
            
        except Exception as e:
            logger.error(f"SQL extraction failed: {e}")
            return None
    
    def _create_fallback_response(self, natural_language: str, error_message: str) -> Dict[str, Any]:
        """폴백 응답 생성"""
        return {
            "success": False,
            "error": error_message,
            "natural_language": natural_language,
            "fallback": True,
            "generated_at": datetime.now().isoformat()
        }
    
    def test_connection(self) -> bool:
        """연결 테스트"""
        if not self.is_available:
            return False
        
        try:
            response = self.model.generate_content("SELECT 1")
            return response.text is not None
        except Exception as e:
            logger.error(f"Gemini Text-to-SQL connection test failed: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """서비스 상태 반환"""
        return {
            "available": self.is_available,
            "api_key_configured": bool(self.config.GEMINI_API_KEY),
            "model_name": "gemini-1.5-flash" if self.is_available else None,
            "last_check": datetime.now().isoformat()
        }

# 전역 서비스 인스턴스
_gemini_text_to_sql_service = None

def get_gemini_text_to_sql_service() -> GeminiTextToSQLService:
    """Gemini Text-to-SQL 서비스 인스턴스 반환"""
    global _gemini_text_to_sql_service
    if _gemini_text_to_sql_service is None:
        _gemini_text_to_sql_service = GeminiTextToSQLService()
    return _gemini_text_to_sql_service
