"""
지능형 검색 서비스
MySQL DB를 먼저 검색하고, 데이터가 없으면 웹에서 검색하는 통합 서비스
"""

import os
import pandas as pd
import mysql.connector
from mysql.connector import Error
import google.generativeai as genai
import requests
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntelligentSearchServiceComplete:
    """지능형 검색 서비스 클래스"""

    def __init__(self):
        """서비스 초기화"""
        self.setup_apis()
        self.setup_database()

    def setup_apis(self):
        """API 설정"""
        try:
            # Gemini API 설정
            gemini_api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyCBq39sdhXGZuBBdpZlB0mdjOdYxWP3oJQ')
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')

            # 웹 검색 API 키
            self.serper_api_key = os.getenv('SERPER_API_KEY', '8d3f4ba5afc9a6b61fdb653d642f7446eba2ce55')
            self.tavily_api_key = os.getenv('TAVILY_API_KEY', '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')

            logger.info("API 설정 완료")
        except Exception as e:
            logger.error(f"API 설정 오류: {e}")

    def setup_database(self):
        """데이터베이스 연결 설정"""
        try:
            self.db_config = {
                'host': 'localhost',
                'database': 'seoul_commercial',
                'user': os.getenv('DB_USER', 'seoul_ro'),
                'password': os.getenv('DB_PASSWORD', 'seoul_ro_password_2024'),
                'port': int(os.getenv('DB_PORT', 3306)),
                'charset': 'utf8mb4'
            }
            logger.info("데이터베이스 설정 완료")
        except Exception as e:
            logger.error(f"데이터베이스 설정 오류: {e}")

    def search_mysql_data(self, query: str) -> Dict[str, Any]:
        """MySQL에서 데이터 검색"""
        connection = None
        cursor = None
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()

            # 검색어 기반으로 SQL 쿼리 생성
            sql_query = self.generate_sql_from_query(query)

            if sql_query:
                cursor.execute(sql_query)
                results = cursor.fetchall()
                column_names = [desc[0] for desc in cursor.description]

                if results:
                    # 결과를 DataFrame으로 변환
                    df = pd.DataFrame(results, columns=column_names)

                    return {
                        'success': True,
                        'data': df,
                        'source': 'mysql',
                        'sql_query': sql_query,
                        'row_count': len(results)
                    }

            return {
                'success': False,
                'data': None,
                'source': 'mysql',
                'message': 'MySQL에서 관련 데이터를 찾을 수 없습니다.'
            }

        except Error as e:
            logger.error(f"MySQL 검색 오류: {e}")
            return {
                'success': False,
                'data': None,
                'source': 'mysql',
                'error': str(e)
            }
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    def generate_sql_from_query(self, query: str) -> Optional[str]:
        """자연어 쿼리를 SQL로 변환"""
        try:
            # 테이블 스키마 정보
            schema_info = """
            상권분석 테이블 스키마:
            - 상권명 (VARCHAR): 상권 이름
            - 업종 (VARCHAR): 업종 분류
            - 년도 (INT): 연도
            - 분기 (INT): 분기
            - 매출금액 (DECIMAL): 매출 금액
            - 거래건수 (INT): 거래 건수
            """

            prompt = f"""
            다음 자연어 질의를 MySQL SQL 쿼리로 변환해주세요.

            테이블 정보:
            {schema_info}

            사용자 질의: {query}

            규칙:
            1. 테이블명은 '상권분석'을 사용하세요
            2. 존재하는 컬럼명만 사용하세요
            3. 한글 키워드는 LIKE 검색을 사용하세요
            4. 결과는 SQL 쿼리만 반환하세요
            5. LIMIT을 추가해서 최대 100개 결과만 반환하세요

            SQL 쿼리:
            """

            response = self.gemini_model.generate_content(prompt)
            sql_query = response.text.strip()

            # SQL 인젝션 방지를 위한 기본 검증
            if self.is_safe_sql(sql_query):
                return sql_query
            else:
                logger.warning(f"안전하지 않은 SQL 쿼리: {sql_query}")
                return None

        except Exception as e:
            logger.error(f"SQL 생성 오류: {e}")
            return None

    def is_safe_sql(self, sql: str) -> bool:
        """SQL 안전성 검증"""
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        sql_upper = sql.upper()

        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False
        return True

    def search_web_data(self, query: str) -> Dict[str, Any]:
        """웹에서 데이터 검색"""
        try:
            # Serper를 사용한 검색
            serper_results = self.search_with_serper(query)

            if serper_results['success']:
                return serper_results

            # Serper가 실패하면 Tavily 시도
            tavily_results = self.search_with_tavily(query)
            return tavily_results

        except Exception as e:
            logger.error(f"웹 검색 오류: {e}")
            return {
                'success': False,
                'data': None,
                'source': 'web',
                'error': str(e)
            }

    def search_with_serper(self, query: str) -> Dict[str, Any]:
        """Serper API를 사용한 검색"""
        try:
            # 상권/창업 관련 검색어로 확장
            enhanced_query = f"{query} 상권 창업 데이터 CSV"

            url = "https://google.serper.dev/search"
            payload = json.dumps({
                "q": enhanced_query,
                "num": 10
            })
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }

            response = requests.post(url, headers=headers, data=payload)

            if response.status_code == 200:
                results = response.json()

                # 결과 처리
                processed_results = self.process_serper_results(results)

                return {
                    'success': True,
                    'data': processed_results,
                    'source': 'serper',
                    'raw_results': results
                }
            else:
                return {
                    'success': False,
                    'data': None,
                    'source': 'serper',
                    'error': f"API 요청 실패: {response.status_code}"
                }

        except Exception as e:
            logger.error(f"Serper 검색 오류: {e}")
            return {
                'success': False,
                'data': None,
                'source': 'serper',
                'error': str(e)
            }

    def search_with_tavily(self, query: str) -> Dict[str, Any]:
        """Tavily API를 사용한 검색"""
        try:
            # 상권/창업 관련 검색어로 확장
            enhanced_query = f"{query} 상권 분석 창업 지원 데이터"

            url = "https://api.tavily.com/search"
            payload = {
                "api_key": self.tavily_api_key,
                "query": enhanced_query,
                "search_depth": "basic",
                "include_answer": True,
                "include_images": False,
                "include_raw_content": True,
                "max_results": 10
            }

            response = requests.post(url, json=payload)

            if response.status_code == 200:
                results = response.json()

                # 결과 처리
                processed_results = self.process_tavily_results(results)

                return {
                    'success': True,
                    'data': processed_results,
                    'source': 'tavily',
                    'raw_results': results
                }
            else:
                return {
                    'success': False,
                    'data': None,
                    'source': 'tavily',
                    'error': f"API 요청 실패: {response.status_code}"
                }

        except Exception as e:
            logger.error(f"Tavily 검색 오류: {e}")
            return {
                'success': False,
                'data': None,
                'source': 'tavily',
                'error': str(e)
            }

    def process_serper_results(self, results: Dict) -> List[Dict]:
        """Serper 검색 결과 처리"""
        processed = []

        if 'organic' in results:
            for item in results['organic']:
                processed.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'source': 'serper'
                })

        return processed

    def process_tavily_results(self, results: Dict) -> List[Dict]:
        """Tavily 검색 결과 처리"""
        processed = []

        if 'results' in results:
            for item in results['results']:
                processed.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'snippet': item.get('content', ''),
                    'source': 'tavily'
                })

        return processed

    def intelligent_search(self, query: str) -> Dict[str, Any]:
        """지능형 검색 - MySQL 우선, 웹 백업"""
        logger.info(f"지능형 검색 시작: {query}")

        # 1단계: MySQL에서 검색
        mysql_result = self.search_mysql_data(query)

        if mysql_result['success'] and mysql_result['data'] is not None:
            # MySQL에서 데이터를 찾았으면 LLM으로 분석
            analysis = self.analyze_data_with_llm(mysql_result['data'], query)

            return {
                'success': True,
                'primary_source': 'mysql',
                'mysql_data': mysql_result,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }

        # 2단계: MySQL에서 찾지 못했으면 웹 검색
        logger.info("MySQL에서 데이터를 찾을 수 없어 웹 검색을 시작합니다.")
        web_result = self.search_web_data(query)

        if web_result['success']:
            # 웹 검색 결과를 LLM으로 분석
            analysis = self.analyze_web_results_with_llm(web_result['data'], query)

            return {
                'success': True,
                'primary_source': 'web',
                'web_data': web_result,
                'analysis': analysis,
                'mysql_attempted': True,
                'timestamp': datetime.now().isoformat()
            }

        # 둘 다 실패한 경우
        return {
            'success': False,
            'primary_source': None,
            'mysql_data': mysql_result,
            'web_data': web_result,
            'message': 'MySQL과 웹 검색 모두에서 관련 데이터를 찾을 수 없습니다.',
            'timestamp': datetime.now().isoformat()
        }

    def analyze_data_with_llm(self, df: pd.DataFrame, query: str) -> str:
        """DataFrame을 LLM으로 분석"""
        try:
            # 데이터 요약 정보 생성
            data_summary = f"""
            데이터 요약:
            - 행 수: {len(df)}
            - 컬럼: {', '.join(df.columns.tolist())}
            - 샘플 데이터:
            {df.head().to_string()}

            통계 정보:
            {df.describe().to_string() if len(df) > 0 else "통계 정보 없음"}
            """

            prompt = f"""
            사용자가 다음과 같이 질문했습니다: "{query}"

            MySQL 데이터베이스에서 찾은 관련 데이터:
            {data_summary}

            이 데이터를 분석하여 사용자의 질문에 대한 유용한 인사이트를 제공해주세요.
            다음 형식으로 답변해주세요:

            1. 핵심 발견사항
            2. 주요 통계
            3. 추천사항
            4. 추가 분석 제안

            답변은 한국어로 작성해주세요.
            """

            response = self.gemini_model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"데이터 분석 오류: {e}")
            return f"데이터 분석 중 오류가 발생했습니다: {str(e)}"

    def analyze_web_results_with_llm(self, web_results: List[Dict], query: str) -> str:
        """웹 검색 결과를 LLM으로 분석"""
        try:
            # 웹 검색 결과 요약
            results_summary = ""
            for i, result in enumerate(web_results[:5], 1):  # 상위 5개만 사용
                results_summary += f"""
                {i}. {result['title']}
                   URL: {result['url']}
                   내용: {result['snippet'][:200]}...
                """

            prompt = f"""
            사용자가 다음과 같이 질문했습니다: "{query}"

            MySQL 데이터베이스에서는 관련 데이터를 찾을 수 없어, 웹에서 검색한 결과입니다:
            {results_summary}

            이 웹 검색 결과를 종합하여 사용자의 질문에 대한 유용한 답변을 제공해주세요.
            다음 형식으로 답변해주세요:

            1. 웹에서 찾은 주요 정보
            2. 관련 리소스 및 링크
            3. 추천사항
            4. 추가 정보 검색 제안

            답변은 한국어로 작성해주세요.
            """

            response = self.gemini_model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"웹 결과 분석 오류: {e}")
            return f"웹 검색 결과 분석 중 오류가 발생했습니다: {str(e)}"

    def determine_search_strategy(self, query: str) -> Dict[str, Any]:
        """LLM이 검색어를 분석하여 최적의 검색 전략을 결정"""
        try:
            prompt = f"""
            다음 검색어를 분석하여 최적의 검색 전략을 결정해주세요: "{query}"

            다음 중에서 선택해주세요:
            1. "academic" - 학술적, 연구 기반 정보가 필요한 경우 (Tavily 우선)
            2. "policy" - 정책, 제도 관련 정보가 필요한 경우 (Serper 우선)
            3. "trend" - 최신 트렌드, 뉴스가 필요한 경우 (Both 병행)
            4. "data" - 데이터, 통계 중심 정보가 필요한 경우 (Serper 우선)

            JSON 형식으로 응답해주세요:
            {{
                "strategy": "academic|policy|trend|data",
                "strategy_name": "전략 이름",
                "reasoning": "선택 이유",
                "enhanced_query": "향상된 검색어"
            }}
            """

            response = self.gemini_model.generate_content(prompt)
            result_text = response.text.strip()

            # JSON 파싱 시도
            try:
                import json
                result = json.loads(result_text)
                return result
            except:
                # JSON 파싱 실패 시 기본 전략 반환
                return {
                    "strategy": "trend",
                    "strategy_name": "종합 검색",
                    "reasoning": "기본 전략 적용",
                    "enhanced_query": f"{query} 상권 창업 분석"
                }

        except Exception as e:
            logger.error(f"검색 전략 결정 오류: {e}")
            return {
                "strategy": "trend",
                "strategy_name": "종합 검색",
                "reasoning": "오류로 인한 기본 전략 적용",
                "enhanced_query": f"{query} 상권 창업"
            }

    def execute_smart_search(self, query: str, strategy: Dict[str, Any], max_results: int = 10) -> Dict[str, Any]:
        """AI가 결정한 전략에 따라 스마트 검색 실행"""
        try:
            enhanced_query = strategy.get('enhanced_query', query)
            strategy_type = strategy.get('strategy', 'trend')

            if strategy_type == "academic":
                # 학술적 정보 우선 - Tavily 먼저
                result = self.search_with_tavily(enhanced_query)
                if not result['success']:
                    result = self.search_with_serper(enhanced_query)

            elif strategy_type == "policy":
                # 정책 정보 우선 - Serper 먼저
                result = self.search_with_serper(enhanced_query)
                if not result['success']:
                    result = self.search_with_tavily(enhanced_query)

            elif strategy_type == "data":
                # 데이터 중심 - Serper 먼저 + CSV 검색어 추가
                data_query = f"{enhanced_query} 데이터 통계 CSV"
                result = self.search_with_serper(data_query)
                if not result['success']:
                    result = self.search_with_tavily(enhanced_query)

            else:  # trend 또는 기타
                # 종합 검색 - 두 엔진 모두 사용
                result = self.search_web_data(enhanced_query)

            # 결과에 전략 정보 추가
            if result['success']:
                result['strategy_used'] = strategy
                result['enhanced_query'] = enhanced_query

            return result

        except Exception as e:
            logger.error(f"스마트 검색 실행 오류: {e}")
            return {
                'success': False,
                'data': None,
                'source': 'smart_search',
                'error': str(e)
            }

    def analyze_web_results_with_smart_llm(self, web_results: List[Dict], query: str, strategy: Dict[str, Any]) -> str:
        """전략 정보를 고려한 고도화된 LLM 분석"""
        try:
            # 웹 검색 결과 요약
            results_summary = ""
            for i, result in enumerate(web_results[:7], 1):  # 더 많은 결과 활용
                results_summary += f"""
                {i}. {result['title']}
                   URL: {result['url']}
                   내용: {result['snippet'][:300]}...
                   출처: {result.get('source', 'Unknown')}
                """

            strategy_context = f"""
            AI 검색 전략: {strategy.get('strategy_name', 'Unknown')}
            선택 이유: {strategy.get('reasoning', 'Unknown')}
            향상된 검색어: {strategy.get('enhanced_query', query)}
            """

            prompt = f"""
            사용자 질문: "{query}"

            {strategy_context}

            검색 결과:
            {results_summary}

            위 정보를 바탕으로 전문적이고 상세한 분석을 제공해주세요.

            다음 구조로 작성해주세요:

            ## 🎯 핵심 요약
            - 질문에 대한 직접적인 답변

            ## 📊 주요 발견사항
            - 검색 결과에서 발견된 중요한 정보들
            - 신뢰할 만한 출처의 데이터나 통계

            ## 🔍 심화 분석
            - 전문가적 관점에서의 해석
            - 트렌드나 패턴 분석

            ## 💡 실행 가능한 제안
            - 구체적이고 실용적인 권장사항

            ## 📚 추가 탐구 방향
            - 더 깊이 알아볼 만한 주제들
            - 관련 키워드나 검색어 제안

            ## 🔗 주요 참고자료
            - 가장 유용한 링크 3-5개 선별

            모든 답변은 한국어로 작성하고, 전문적이면서도 이해하기 쉽게 설명해주세요.
            """

            response = self.gemini_model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"스마트 LLM 분석 오류: {e}")
            return f"고도화된 분석 중 오류가 발생했습니다: {str(e)}"


# 전역 서비스 인스턴스
_intelligent_search_service_complete = None


def get_intelligent_search_service_complete() -> IntelligentSearchServiceComplete:
    """지능형 검색 서비스 인스턴스 반환"""
    global _intelligent_search_service_complete
    if _intelligent_search_service_complete is None:
        _intelligent_search_service_complete = IntelligentSearchServiceComplete()
    return _intelligent_search_service_complete