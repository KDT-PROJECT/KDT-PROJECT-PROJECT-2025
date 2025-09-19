"""
LLM 보고서 생성 파이프라인 - 정량/정성 데이터를 종합한 보고서 자동 생성
"""

import json
import logging
from datetime import datetime
from typing import Any

from llama_index.llms.huggingface import HuggingFaceLLM

from pipelines.rag import HybridRAGPipeline
from pipelines.text_to_sql import TextToSQLPipeline
from utils.database import DatabaseManager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """LLM 보고서 생성 클래스"""

    def __init__(
        self,
        db_manager: DatabaseManager,
        text_to_sql_pipeline: TextToSQLPipeline,
        rag_pipeline: HybridRAGPipeline,
    ):
        """
        보고서 생성기 초기화

        Args:
            db_manager: 데이터베이스 매니저
            text_to_sql_pipeline: Text-to-SQL 파이프라인
            rag_pipeline: RAG 파이프라인
        """
        self.db_manager = db_manager
        self.text_to_sql_pipeline = text_to_sql_pipeline
        self.rag_pipeline = rag_pipeline
        self.llm = None

        # LLM 초기화
        self._initialize_llm()

    def _initialize_llm(self):
        """LLM 초기화"""
        try:
            # Hugging Face LLM 초기화
            self.llm = HuggingFaceLLM(
                model_name="microsoft/DialoGPT-medium",
                tokenizer_name="microsoft/DialoGPT-medium",
                context_window=2048,
                max_new_tokens=512,
                generate_kwargs={"temperature": 0.3, "do_sample": True},
                device_map="auto",
            )

            logger.info("LLM이 초기화되었습니다.")

        except Exception as e:
            logger.error(f"LLM 초기화 중 오류 발생: {e}")
            # 대체 모델 사용
            self._initialize_fallback_llm()

    def _initialize_fallback_llm(self):
        """대체 LLM 초기화"""
        try:
            self.llm = HuggingFaceLLM(
                model_name="distilgpt2",
                tokenizer_name="distilgpt2",
                context_window=1024,
                max_new_tokens=256,
                generate_kwargs={"temperature": 0.3, "do_sample": True},
                device_map="auto",
            )

            logger.info("대체 LLM이 초기화되었습니다.")

        except Exception as e:
            logger.error(f"대체 LLM 초기화 실패: {e}")

    def generate_executive_summary(
        self, quantitative_data: dict, qualitative_data: list[dict]
    ) -> str:
        """경영진 요약 생성"""
        try:
            prompt = f"""
다음 데이터를 바탕으로 상권분석 보고서의 경영진 요약을 작성해주세요.

정량 데이터:
{json.dumps(quantitative_data, ensure_ascii=False, indent=2)}

정성 데이터 (문헌 검색 결과):
{json.dumps(qualitative_data, ensure_ascii=False, indent=2)}

요약은 다음 구조로 작성해주세요:
1. 핵심 발견사항 (3-4개 주요 포인트)
2. 주요 트렌드 및 패턴
3. 시사점 및 권고사항

한국어로 작성하고, 구체적인 수치와 근거를 포함해주세요.
"""

            if self.llm:
                response = self.llm.complete(prompt)
                return response.text
            else:
                return self._generate_fallback_summary(
                    quantitative_data, qualitative_data
                )

        except Exception as e:
            logger.error(f"경영진 요약 생성 중 오류 발생: {e}")
            return "경영진 요약 생성 중 오류가 발생했습니다."

    def generate_quantitative_analysis(self, sql_results: list[dict]) -> str:
        """정량 분석 섹션 생성"""
        try:
            prompt = f"""
다음 SQL 쿼리 결과를 바탕으로 정량 분석 섹션을 작성해주세요.

SQL 결과:
{json.dumps(sql_results, ensure_ascii=False, indent=2)}

다음 구조로 작성해주세요:
1. 데이터 개요
2. 주요 지표 분석
3. 트렌드 분석
4. 통계적 인사이트

한국어로 작성하고, 수치를 명확히 제시해주세요.
"""

            if self.llm:
                response = self.llm.complete(prompt)
                return response.text
            else:
                return self._generate_fallback_quantitative_analysis(sql_results)

        except Exception as e:
            logger.error(f"정량 분석 생성 중 오류 발생: {e}")
            return "정량 분석 생성 중 오류가 발생했습니다."

    def generate_qualitative_analysis(self, rag_results: list[dict]) -> str:
        """정성 분석 섹션 생성"""
        try:
            prompt = f"""
다음 문헌 검색 결과를 바탕으로 정성 분석 섹션을 작성해주세요.

문헌 검색 결과:
{json.dumps(rag_results, ensure_ascii=False, indent=2)}

다음 구조로 작성해주세요:
1. 관련 정책 및 제도
2. 시장 동향 및 전망
3. 성공 사례 및 벤치마킹
4. 위험 요인 및 기회 요소

한국어로 작성하고, 각 정보의 출처를 명시해주세요.
"""

            if self.llm:
                response = self.llm.complete(prompt)
                return response.text
            else:
                return self._generate_fallback_qualitative_analysis(rag_results)

        except Exception as e:
            logger.error(f"정성 분석 생성 중 오류 발생: {e}")
            return "정성 분석 생성 중 오류가 발생했습니다."

    def generate_insights_and_recommendations(
        self, quantitative_data: dict, qualitative_data: list[dict]
    ) -> str:
        """인사이트 및 권고사항 생성"""
        try:
            prompt = f"""
다음 데이터를 종합하여 인사이트 및 권고사항을 작성해주세요.

정량 데이터:
{json.dumps(quantitative_data, ensure_ascii=False, indent=2)}

정성 데이터:
{json.dumps(qualitative_data, ensure_ascii=False, indent=2)}

다음 구조로 작성해주세요:
1. 핵심 인사이트 (3-5개)
2. 전략적 권고사항
3. 실행 계획 제안
4. 위험 관리 방안

한국어로 작성하고, 실행 가능한 구체적인 제안을 포함해주세요.
"""

            if self.llm:
                response = self.llm.complete(prompt)
                return response.text
            else:
                return self._generate_fallback_insights(
                    quantitative_data, qualitative_data
                )

        except Exception as e:
            logger.error(f"인사이트 및 권고사항 생성 중 오류 발생: {e}")
            return "인사이트 및 권고사항 생성 중 오류가 발생했습니다."

    def generate_full_report(self, report_config: dict[str, Any]) -> dict[str, Any]:
        """
        전체 보고서 생성

        Args:
            report_config: 보고서 설정
                - report_type: 보고서 유형
                - target_area: 분석 대상 지역
                - target_industry: 분석 대상 업종
                - analysis_period: 분석 기간

        Returns:
            생성된 보고서 딕셔너리
        """
        try:
            logger.info(f"보고서 생성 시작: {report_config}")

            # 1. 정량 데이터 수집
            quantitative_data = self._collect_quantitative_data(report_config)

            # 2. 정성 데이터 수집
            qualitative_data = self._collect_qualitative_data(report_config)

            # 3. 보고서 섹션 생성
            executive_summary = self.generate_executive_summary(
                quantitative_data, qualitative_data
            )

            quantitative_analysis = self.generate_quantitative_analysis(
                quantitative_data.get("sql_results", [])
            )

            qualitative_analysis = self.generate_qualitative_analysis(qualitative_data)

            insights_recommendations = self.generate_insights_and_recommendations(
                quantitative_data, qualitative_data
            )

            # 4. 보고서 구성
            report = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "report_type": report_config.get("report_type", "상권분석보고서"),
                    "target_area": report_config.get("target_area", ""),
                    "target_industry": report_config.get("target_industry", ""),
                    "analysis_period": report_config.get("analysis_period", "2024년"),
                },
                "executive_summary": executive_summary,
                "quantitative_analysis": quantitative_analysis,
                "qualitative_analysis": qualitative_analysis,
                "insights_recommendations": insights_recommendations,
                "data_sources": {
                    "quantitative": quantitative_data,
                    "qualitative": qualitative_data,
                },
                "appendix": {
                    "sql_queries": quantitative_data.get("sql_queries", []),
                    "document_sources": [
                        doc.get("metadata", {}) for doc in qualitative_data
                    ],
                },
            }

            logger.info("보고서 생성이 완료되었습니다.")
            return report

        except Exception as e:
            logger.error(f"보고서 생성 중 오류 발생: {e}")
            return {
                "error": str(e),
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "status": "failed",
                },
            }

    def _collect_quantitative_data(
        self, report_config: dict[str, Any]
    ) -> dict[str, Any]:
        """정량 데이터 수집"""
        try:
            quantitative_data = {"sql_results": [], "sql_queries": [], "statistics": {}}

            # 기본 통계 쿼리들
            queries = [
                {
                    "name": "전체_매출_통계",
                    "query": "SELECT COUNT(*) as total_records, SUM(sales_amt) as total_sales, AVG(sales_amt) as avg_sales FROM sales_2024",
                },
                {
                    "name": "지역별_매출_순위",
                    "query": "SELECT r.name, SUM(s.sales_amt) as total_sales FROM sales_2024 s JOIN regions r ON s.region_id = r.region_id GROUP BY r.name ORDER BY total_sales DESC LIMIT 10",
                },
                {
                    "name": "업종별_매출_순위",
                    "query": "SELECT i.name, SUM(s.sales_amt) as total_sales FROM sales_2024 s JOIN industries i ON s.industry_id = i.industry_id GROUP BY i.name ORDER BY total_sales DESC LIMIT 10",
                },
            ]

            # 대상 지역/업종이 지정된 경우 추가 쿼리
            target_area = report_config.get("target_area", "")
            target_industry = report_config.get("target_industry", "")

            if target_area:
                queries.append(
                    {
                        "name": f"{target_area}_상세_분석",
                        "query": f"SELECT i.name, SUM(s.sales_amt) as total_sales, AVG(s.sales_amt) as avg_sales FROM sales_2024 s JOIN regions r ON s.region_id = r.region_id JOIN industries i ON s.industry_id = i.industry_id WHERE r.name LIKE '%{target_area}%' GROUP BY i.name ORDER BY total_sales DESC",
                    }
                )

            if target_industry:
                queries.append(
                    {
                        "name": f"{target_industry}_상세_분석",
                        "query": f"SELECT r.name, SUM(s.sales_amt) as total_sales, AVG(s.sales_amt) as avg_sales FROM sales_2024 s JOIN regions r ON s.region_id = r.region_id JOIN industries i ON s.industry_id = i.industry_id WHERE i.name LIKE '%{target_industry}%' GROUP BY r.name ORDER BY total_sales DESC",
                    }
                )

            # 쿼리 실행
            for query_info in queries:
                try:
                    result = self.db_manager.execute_query(query_info["query"])
                    if result is not None:
                        quantitative_data["sql_results"].append(
                            {
                                "name": query_info["name"],
                                "data": result.to_dict("records"),
                            }
                        )
                        quantitative_data["sql_queries"].append(query_info["query"])
                except Exception as e:
                    logger.warning(f"쿼리 실행 실패: {query_info['name']} - {e}")

            return quantitative_data

        except Exception as e:
            logger.error(f"정량 데이터 수집 중 오류 발생: {e}")
            return {"sql_results": [], "sql_queries": [], "statistics": {}}

    def _collect_qualitative_data(
        self, report_config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """정성 데이터 수집"""
        try:
            # 검색 쿼리 구성
            search_queries = []

            target_area = report_config.get("target_area", "")
            target_industry = report_config.get("target_industry", "")

            if target_area:
                search_queries.append(f"{target_area} 상권 활성화 정책")
                search_queries.append(f"{target_area} 창업 지원")

            if target_industry:
                search_queries.append(f"{target_industry} 업종 전망")
                search_queries.append(f"{target_industry} 창업 가이드")

            # 기본 검색 쿼리
            search_queries.extend(
                ["서울시 상권 활성화 정책", "창업 지원 제도", "상권 분석 방법론"]
            )

            # RAG 검색 실행
            qualitative_data = []
            for query in search_queries:
                try:
                    results = self.rag_pipeline.search(
                        query, search_type="hybrid", top_k=3
                    )
                    qualitative_data.extend(results)
                except Exception as e:
                    logger.warning(f"RAG 검색 실패: {query} - {e}")

            # 중복 제거
            seen_texts = set()
            unique_data = []
            for item in qualitative_data:
                text_hash = hash(item["text"])
                if text_hash not in seen_texts:
                    seen_texts.add(text_hash)
                    unique_data.append(item)

            return unique_data

        except Exception as e:
            logger.error(f"정성 데이터 수집 중 오류 발생: {e}")
            return []

    def _generate_fallback_summary(
        self, quantitative_data: dict, qualitative_data: list[dict]
    ) -> str:
        """대체 요약 생성"""
        return f"""
## 경영진 요약

### 핵심 발견사항
- 정량 데이터 분석 결과 {len(quantitative_data.get('sql_results', []))}개 쿼리 실행
- 문헌 검색을 통해 {len(qualitative_data)}개 관련 문서 발견
- 데이터 기반 의사결정을 위한 기초 자료 확보

### 주요 트렌드
- 상권 데이터 분석을 통한 시장 동향 파악
- 정책 및 제도 변화에 대한 이해도 향상

### 시사점
- 지속적인 데이터 모니터링 필요
- 정책 변화에 대한 대응 방안 수립 권고
"""

    def _generate_fallback_quantitative_analysis(self, sql_results: list[dict]) -> str:
        """대체 정량 분석 생성"""
        return f"""
## 정량 분석

### 데이터 개요
- 총 {len(sql_results)}개 분석 쿼리 실행
- 각 쿼리별 상세 결과 데이터 확보

### 주요 지표
- 데이터의 정확성과 신뢰성 확보
- 시계열 분석을 통한 트렌드 파악

### 통계적 인사이트
- 데이터 기반 의사결정 지원
- 객관적 지표를 통한 성과 측정
"""

    def _generate_fallback_qualitative_analysis(self, rag_results: list[dict]) -> str:
        """대체 정성 분석 생성"""
        return f"""
## 정성 분석

### 관련 정책 및 제도
- {len(rag_results)}개 관련 문서 분석
- 정책 변화 및 제도 개선 방향 파악

### 시장 동향 및 전망
- 업계 전문가 의견 및 시장 분석 자료 검토
- 미래 전망 및 기회 요소 식별

### 성공 사례 및 벤치마킹
- 우수 사례 분석을 통한 벤치마킹 기회
- 모범 사례 적용 방안 검토
"""

    def _generate_fallback_insights(
        self, quantitative_data: dict, qualitative_data: list[dict]
    ) -> str:
        """대체 인사이트 생성"""
        return """
## 인사이트 및 권고사항

### 핵심 인사이트
1. 데이터 기반 의사결정의 중요성
2. 정량/정성 데이터의 통합 분석 필요성
3. 지속적인 모니터링 체계 구축

### 전략적 권고사항
- 정기적인 데이터 업데이트 및 분석
- 정책 변화에 대한 신속한 대응
- 이해관계자와의 소통 강화

### 실행 계획
- 단계별 목표 설정 및 성과 측정
- 리스크 관리 체계 구축
- 지속적인 개선 방안 모색
"""

    def export_report(self, report: dict[str, Any], format: str = "json") -> str:
        """보고서 내보내기"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if format == "json":
                filename = f"reports/commercial_analysis_report_{timestamp}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)

            elif format == "markdown":
                filename = f"reports/commercial_analysis_report_{timestamp}.md"
                markdown_content = self._convert_to_markdown(report)
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

            logger.info(f"보고서가 내보내기되었습니다: {filename}")
            return filename

        except Exception as e:
            logger.error(f"보고서 내보내기 중 오류 발생: {e}")
            return ""

    def _convert_to_markdown(self, report: dict[str, Any]) -> str:
        """보고서를 마크다운 형식으로 변환"""
        metadata = report.get("metadata", {})

        markdown = f"""# {metadata.get('report_type', '상권분석보고서')}

**생성일시**: {metadata.get('generated_at', '')}  
**분석 대상 지역**: {metadata.get('target_area', '전체')}  
**분석 대상 업종**: {metadata.get('target_industry', '전체')}  
**분석 기간**: {metadata.get('analysis_period', '2024년')}

---

## 경영진 요약

{report.get('executive_summary', '')}

---

## 정량 분석

{report.get('quantitative_analysis', '')}

---

## 정성 분석

{report.get('qualitative_analysis', '')}

---

## 인사이트 및 권고사항

{report.get('insights_recommendations', '')}

---

## 부록

### 데이터 소스
- 정량 데이터: {len(report.get('data_sources', {}).get('quantitative', {}).get('sql_results', []))}개 쿼리 결과
- 정성 데이터: {len(report.get('data_sources', {}).get('qualitative', []))}개 문서

### SQL 쿼리 목록
"""

        # SQL 쿼리 추가
        sql_queries = report.get("appendix", {}).get("sql_queries", [])
        for i, query in enumerate(sql_queries, 1):
            markdown += f"\n#### 쿼리 {i}\n```sql\n{query}\n```\n"

        return markdown
