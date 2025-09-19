"""
Text-to-SQL 파이프라인 - LlamaIndex를 사용한 자연어 SQL 변환
"""

import logging
from typing import Any

from llama_index.core import SQLDatabase, VectorStoreIndex
from llama_index.core.objects import ObjectIndex, SQLTableNodeMapping, SQLTableSchema
from llama_index.core.query_engine import SQLTableRetrieverQueryEngine
from llama_index.core.retrievers import SQLRetriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface import HuggingFaceLLM

from utils.database import DatabaseManager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextToSQLPipeline:
    """Text-to-SQL 파이프라인 클래스"""

    def __init__(self, db_manager: DatabaseManager):
        """
        Text-to-SQL 파이프라인 초기화

        Args:
            db_manager: 데이터베이스 매니저 인스턴스
        """
        self.db_manager = db_manager
        self.sql_database = None
        self.query_engine = None
        self.llm = None
        self.embed_model = None

        # LLM 및 임베딩 모델 초기화
        self._initialize_models()

    def _initialize_models(self):
        """LLM 및 임베딩 모델 초기화"""
        try:
            # Hugging Face LLM 초기화 (경량 모델 사용)
            self.llm = HuggingFaceLLM(
                model_name="microsoft/DialoGPT-medium",
                tokenizer_name="microsoft/DialoGPT-medium",
                context_window=2048,
                max_new_tokens=256,
                generate_kwargs={"temperature": 0.1, "do_sample": True},
                device_map="auto",
            )

            # 임베딩 모델 초기화
            self.embed_model = HuggingFaceEmbedding(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

            logger.info("LLM 및 임베딩 모델이 초기화되었습니다.")

        except Exception as e:
            logger.error(f"모델 초기화 중 오류 발생: {e}")
            # 대체 모델 사용
            self._initialize_fallback_models()

    def _initialize_fallback_models(self):
        """대체 모델 초기화"""
        try:
            # 더 작은 모델 사용
            self.llm = HuggingFaceLLM(
                model_name="distilgpt2",
                tokenizer_name="distilgpt2",
                context_window=1024,
                max_new_tokens=128,
                generate_kwargs={"temperature": 0.1, "do_sample": True},
                device_map="auto",
            )

            self.embed_model = HuggingFaceEmbedding(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )

            logger.info("대체 모델이 초기화되었습니다.")

        except Exception as e:
            logger.error(f"대체 모델 초기화 실패: {e}")

    def setup_sql_database(self) -> bool:
        """SQL 데이터베이스 설정"""
        try:
            if not self.db_manager.engine:
                self.db_manager.connect()

            # SQLDatabase 인스턴스 생성
            self.sql_database = SQLDatabase(
                self.db_manager.engine,
                include_tables=[
                    "regions",
                    "industries",
                    "sales_2024",
                    "features",
                    "docs",
                ],
            )

            logger.info("SQL 데이터베이스가 설정되었습니다.")
            return True

        except Exception as e:
            logger.error(f"SQL 데이터베이스 설정 실패: {e}")
            return False

    def create_query_engine(self) -> bool:
        """쿼리 엔진 생성"""
        try:
            if not self.sql_database:
                if not self.setup_sql_database():
                    return False

            # 테이블 스키마 객체 생성
            table_node_mapping = SQLTableNodeMapping(self.sql_database)
            table_schema_objs = [
                SQLTableSchema(
                    table_name="regions",
                    context_str="지역 정보 테이블: region_id(지역ID), name(지역명), gu(구), dong(동), lat(위도), lon(경도), adm_code(행정구역코드)",
                ),
                SQLTableSchema(
                    table_name="industries",
                    context_str="업종 정보 테이블: industry_id(업종ID), name(업종명), nace_kor(NACE코드), category(카테고리)",
                ),
                SQLTableSchema(
                    table_name="sales_2024",
                    context_str="2024년 매출 데이터 테이블: region_id(지역ID), industry_id(업종ID), date(날짜), sales_amt(매출액), sales_cnt(매출건수), visitors(방문자수)",
                ),
                SQLTableSchema(
                    table_name="features",
                    context_str="특성 데이터 테이블: region_id(지역ID), industry_id(업종ID), feat_json(특성JSON)",
                ),
                SQLTableSchema(
                    table_name="docs",
                    context_str="문서 정보 테이블: doc_id(문서ID), title(제목), source(출처), url(URL), published_date(발행일), content_text(내용)",
                ),
            ]

            # 객체 인덱스 생성
            obj_index = ObjectIndex.from_objects(
                table_schema_objs,
                table_node_mapping,
                VectorStoreIndex,
            )

            # SQL 리트리버 생성
            sql_retriever = SQLRetriever(self.sql_database)

            # 쿼리 엔진 생성
            self.query_engine = SQLTableRetrieverQueryEngine(
                self.sql_database,
                obj_index.as_retriever(similarity_top_k=3),
                sql_retriever=sql_retriever,
            )

            logger.info("쿼리 엔진이 생성되었습니다.")
            return True

        except Exception as e:
            logger.error(f"쿼리 엔진 생성 실패: {e}")
            return False

    def query(self, natural_language_query: str) -> dict[str, Any]:
        """
        자연어 쿼리 실행

        Args:
            natural_language_query: 자연어 질의

        Returns:
            쿼리 결과 딕셔너리
        """
        try:
            if not self.query_engine:
                if not self.create_query_engine():
                    return {
                        "success": False,
                        "error": "쿼리 엔진이 초기화되지 않았습니다.",
                    }

            # 자연어 쿼리 실행
            response = self.query_engine.query(natural_language_query)

            # 결과 파싱
            result = {
                "success": True,
                "query": natural_language_query,
                "response": str(response),
                "sql_query": getattr(response, "metadata", {}).get("sql_query", ""),
                "result_data": getattr(response, "metadata", {}).get("result", ""),
                "source_nodes": getattr(response, "source_nodes", []),
            }

            logger.info(f"쿼리 실행 완료: {natural_language_query}")
            return result

        except Exception as e:
            logger.error(f"쿼리 실행 중 오류 발생: {e}")
            return {"success": False, "error": str(e), "query": natural_language_query}

    def get_table_schema(self) -> dict[str, Any]:
        """테이블 스키마 정보 조회"""
        try:
            if not self.sql_database:
                if not self.setup_sql_database():
                    return {}

            # 테이블 정보 조회
            table_info = {}
            for table_name in self.sql_database.get_usable_table_names():
                table_schema = self.sql_database.get_single_table_info(table_name)
                table_info[table_name] = {
                    "schema": table_schema,
                    "sample_data": self._get_sample_data(table_name),
                }

            return table_info

        except Exception as e:
            logger.error(f"테이블 스키마 조회 중 오류 발생: {e}")
            return {}

    def _get_sample_data(self, table_name: str, limit: int = 5) -> list[dict]:
        """테이블 샘플 데이터 조회"""
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            result = self.db_manager.execute_query(query)

            if result is not None:
                return result.to_dict("records")
            return []

        except Exception as e:
            logger.error(f"샘플 데이터 조회 중 오류 발생: {e}")
            return []

    def validate_sql_query(self, sql_query: str) -> bool:
        """SQL 쿼리 유효성 검증"""
        try:
            # 허용된 SQL 키워드만 사용
            allowed_keywords = [
                "SELECT",
                "FROM",
                "WHERE",
                "GROUP BY",
                "ORDER BY",
                "HAVING",
                "JOIN",
                "INNER JOIN",
                "LEFT JOIN",
                "RIGHT JOIN",
                "LIMIT",
                "COUNT",
                "SUM",
                "AVG",
                "MAX",
                "MIN",
                "DISTINCT",
            ]

            # 금지된 키워드
            forbidden_keywords = [
                "DROP",
                "DELETE",
                "UPDATE",
                "INSERT",
                "ALTER",
                "CREATE",
                "TRUNCATE",
                "EXEC",
                "EXECUTE",
                "UNION",
                "--",
                "/*",
                "*/",
            ]

            sql_upper = sql_query.upper()

            # 금지된 키워드 확인
            for keyword in forbidden_keywords:
                if keyword in sql_upper:
                    logger.warning(f"금지된 키워드 발견: {keyword}")
                    return False

            # SELECT만 허용
            if not sql_upper.strip().startswith("SELECT"):
                logger.warning("SELECT 쿼리만 허용됩니다.")
                return False

            return True

        except Exception as e:
            logger.error(f"SQL 쿼리 검증 중 오류 발생: {e}")
            return False

    def get_query_examples(self) -> list[dict[str, str]]:
        """쿼리 예시 반환"""
        return [
            {
                "category": "지역별 분석",
                "query": "강남구에서 가장 매출이 높은 업종은 무엇인가요?",
                "description": "특정 지역의 업종별 매출 순위 조회",
            },
            {
                "category": "업종별 분석",
                "query": "음식점 업종의 월별 매출 추이를 보여주세요",
                "description": "특정 업종의 시간별 매출 변화 분석",
            },
            {
                "category": "비교 분석",
                "query": "강남구와 홍대 상권의 매출을 비교해주세요",
                "description": "지역 간 매출 비교 분석",
            },
            {
                "category": "통계 분석",
                "query": "2024년 전체 매출 상위 10개 지역을 알려주세요",
                "description": "매출 기준 지역 순위 조회",
            },
            {
                "category": "트렌드 분석",
                "query": "최근 3개월간 매출이 가장 많이 증가한 업종은?",
                "description": "매출 증가율 기준 업종 분석",
            },
        ]

    def get_database_stats(self) -> dict[str, Any]:
        """데이터베이스 통계 정보 조회"""
        try:
            stats = {}

            # 테이블별 레코드 수
            tables = ["regions", "industries", "sales_2024", "features", "docs"]
            for table in tables:
                query = f"SELECT COUNT(*) as count FROM {table}"
                result = self.db_manager.execute_query(query)
                if result is not None and not result.empty:
                    stats[f"{table}_count"] = result.iloc[0]["count"]

            # 전체 매출 통계
            sales_stats_query = """
                SELECT 
                    COUNT(*) as total_records,
                    SUM(sales_amt) as total_sales,
                    AVG(sales_amt) as avg_sales,
                    MAX(sales_amt) as max_sales,
                    MIN(sales_amt) as min_sales
                FROM sales_2024
            """
            sales_result = self.db_manager.execute_query(sales_stats_query)
            if sales_result is not None and not sales_result.empty:
                stats.update(sales_result.iloc[0].to_dict())

            return stats

        except Exception as e:
            logger.error(f"데이터베이스 통계 조회 중 오류 발생: {e}")
            return {}
