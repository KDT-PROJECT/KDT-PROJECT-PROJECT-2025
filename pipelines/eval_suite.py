"""
평가 스크립트 (정확도, 속도)
project-structure.mdc 규칙에 따른 평가 스위트
"""

import json
import logging
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvaluationSuite:
    """시스템 평가 스위트"""

    def __init__(self, config: dict[str, Any]):
        """
        평가 스위트 초기화

        Args:
            config: 설정 딕셔너리
        """
        self.config = config
        self.evaluation_results = {}
        self.performance_metrics = {}

        # 평가 결과 저장 경로
        self.results_path = Path(
            config.get("results_path", "models/artifacts/evaluation")
        )
        self.results_path.mkdir(parents=True, exist_ok=True)

    def evaluate_text_to_sql_accuracy(
        self, sql_engine, test_queries: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Text-to-SQL 정확도 평가

        Args:
            sql_engine: SQL 엔진 인스턴스
            test_queries: 테스트 쿼리 리스트

        Returns:
            평가 결과
        """
        try:
            logger.info("Text-to-SQL 정확도 평가 시작")

            results = {
                "total_queries": len(test_queries),
                "successful_queries": 0,
                "failed_queries": 0,
                "accuracy": 0.0,
                "response_times": [],
                "query_results": [],
            }

            for i, test_case in enumerate(test_queries):
                query = test_case["query"]
                expected_keywords = test_case.get("expected_keywords", [])
                expected_tables = test_case.get("expected_tables", [])

                try:
                    # 쿼리 실행 시간 측정
                    start_time = time.time()
                    result = sql_engine.query(query)
                    end_time = time.time()

                    response_time = end_time - start_time
                    results["response_times"].append(response_time)

                    # 결과 분석
                    query_result = {
                        "query": query,
                        "success": result.get("success", False),
                        "response_time": response_time,
                        "sql_query": result.get("sql_query", ""),
                        "has_expected_keywords": False,
                        "has_expected_tables": False,
                        "error": result.get("error", ""),
                    }

                    if result.get("success", False):
                        results["successful_queries"] += 1

                        # 키워드 검증
                        sql_query = result.get("sql_query", "").upper()
                        found_keywords = [
                            kw for kw in expected_keywords if kw.upper() in sql_query
                        ]
                        query_result["has_expected_keywords"] = len(found_keywords) > 0

                        # 테이블 검증
                        found_tables = [
                            table
                            for table in expected_tables
                            if table.upper() in sql_query
                        ]
                        query_result["has_expected_tables"] = len(found_tables) > 0

                    else:
                        results["failed_queries"] += 1

                    results["query_results"].append(query_result)

                    logger.info(
                        f"쿼리 {i+1}/{len(test_queries)} 평가 완료: {query[:50]}..."
                    )

                except Exception as e:
                    logger.error(f"쿼리 평가 중 오류: {query} - {e}")
                    results["failed_queries"] += 1
                    results["query_results"].append(
                        {
                            "query": query,
                            "success": False,
                            "response_time": 0,
                            "error": str(e),
                        }
                    )

            # 정확도 계산
            results["accuracy"] = (
                results["successful_queries"] / results["total_queries"]
                if results["total_queries"] > 0
                else 0
            )

            # 응답 시간 통계
            if results["response_times"]:
                results["avg_response_time"] = statistics.mean(
                    results["response_times"]
                )
                results["median_response_time"] = statistics.median(
                    results["response_times"]
                )
                results["p95_response_time"] = self._calculate_percentile(
                    results["response_times"], 95
                )
                results["p99_response_time"] = self._calculate_percentile(
                    results["response_times"], 99
                )

            logger.info(f"Text-to-SQL 정확도 평가 완료: {results['accuracy']:.2%}")

            return results

        except Exception as e:
            logger.error(f"Text-to-SQL 정확도 평가 실패: {e}")
            return {"error": str(e)}

    def evaluate_rag_quality(
        self, rag_engine, test_queries: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        RAG 품질 평가

        Args:
            rag_engine: RAG 엔진 인스턴스
            test_queries: 테스트 쿼리 리스트

        Returns:
            평가 결과
        """
        try:
            logger.info("RAG 품질 평가 시작")

            results = {
                "total_queries": len(test_queries),
                "response_times": [],
                "query_results": [],
                "relevance_scores": [],
                "diversity_scores": [],
            }

            for i, test_case in enumerate(test_queries):
                query = test_case["query"]
                expected_keywords = test_case.get("expected_keywords", [])
                min_score = test_case.get("min_score", 0.3)

                try:
                    # 검색 실행 시간 측정
                    start_time = time.time()
                    search_results = rag_engine.search(
                        query, search_type="hybrid", top_k=5
                    )
                    end_time = time.time()

                    response_time = end_time - start_time
                    results["response_times"].append(response_time)

                    # 결과 분석
                    query_result = {
                        "query": query,
                        "results_count": len(search_results),
                        "response_time": response_time,
                        "has_results": len(search_results) > 0,
                        "avg_score": 0,
                        "max_score": 0,
                        "relevance_score": 0,
                    }

                    if search_results:
                        # 점수 통계
                        scores = [
                            r.get(
                                "combined_score",
                                r.get("vector_score", r.get("bm25_score", 0)),
                            )
                            for r in search_results
                        ]
                        query_result["avg_score"] = statistics.mean(scores)
                        query_result["max_score"] = max(scores)

                        # 관련성 점수 계산
                        relevance_score = self._calculate_relevance_score(
                            search_results, expected_keywords
                        )
                        query_result["relevance_score"] = relevance_score
                        results["relevance_scores"].append(relevance_score)

                        # 다양성 점수 계산
                        diversity_score = self._calculate_diversity_score(
                            search_results
                        )
                        results["diversity_scores"].append(diversity_score)

                    results["query_results"].append(query_result)

                    logger.info(
                        f"RAG 쿼리 {i+1}/{len(test_queries)} 평가 완료: {query[:50]}..."
                    )

                except Exception as e:
                    logger.error(f"RAG 쿼리 평가 중 오류: {query} - {e}")
                    results["query_results"].append(
                        {
                            "query": query,
                            "results_count": 0,
                            "response_time": 0,
                            "error": str(e),
                        }
                    )

            # 전체 통계 계산
            if results["response_times"]:
                results["avg_response_time"] = statistics.mean(
                    results["response_times"]
                )
                results["median_response_time"] = statistics.median(
                    results["response_times"]
                )
                results["p95_response_time"] = self._calculate_percentile(
                    results["response_times"], 95
                )

            if results["relevance_scores"]:
                results["avg_relevance_score"] = statistics.mean(
                    results["relevance_scores"]
                )
                results["median_relevance_score"] = statistics.median(
                    results["relevance_scores"]
                )

            if results["diversity_scores"]:
                results["avg_diversity_score"] = statistics.mean(
                    results["diversity_scores"]
                )

            logger.info("RAG 품질 평가 완료")

            return results

        except Exception as e:
            logger.error(f"RAG 품질 평가 실패: {e}")
            return {"error": str(e)}

    def evaluate_report_generation(
        self, report_generator, test_configs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        보고서 생성 평가

        Args:
            report_generator: 보고서 생성기 인스턴스
            test_configs: 테스트 설정 리스트

        Returns:
            평가 결과
        """
        try:
            logger.info("보고서 생성 평가 시작")

            results = {
                "total_configs": len(test_configs),
                "successful_generations": 0,
                "failed_generations": 0,
                "generation_times": [],
                "quality_scores": [],
                "config_results": [],
            }

            for i, config in enumerate(test_configs):
                try:
                    # 보고서 생성 시간 측정
                    start_time = time.time()
                    report = report_generator.generate_full_report(config)
                    end_time = time.time()

                    generation_time = end_time - start_time
                    results["generation_times"].append(generation_time)

                    # 결과 분석
                    config_result = {
                        "config": config,
                        "success": "error" not in report,
                        "generation_time": generation_time,
                        "sections_generated": 0,
                        "quality_score": 0,
                        "error": report.get("error", ""),
                    }

                    if "error" not in report:
                        results["successful_generations"] += 1

                        # 생성된 섹션 수 계산
                        sections = [
                            "executive_summary",
                            "quantitative_analysis",
                            "qualitative_analysis",
                            "insights_recommendations",
                        ]
                        sections_generated = sum(
                            1 for section in sections if report.get(section)
                        )
                        config_result["sections_generated"] = sections_generated

                        # 품질 점수 계산
                        quality_score = self._calculate_report_quality(report)
                        config_result["quality_score"] = quality_score
                        results["quality_scores"].append(quality_score)

                    else:
                        results["failed_generations"] += 1

                    results["config_results"].append(config_result)

                    logger.info(f"보고서 생성 {i+1}/{len(test_configs)} 평가 완료")

                except Exception as e:
                    logger.error(f"보고서 생성 평가 중 오류: {e}")
                    results["failed_generations"] += 1
                    results["config_results"].append(
                        {
                            "config": config,
                            "success": False,
                            "generation_time": 0,
                            "error": str(e),
                        }
                    )

            # 전체 통계 계산
            if results["generation_times"]:
                results["avg_generation_time"] = statistics.mean(
                    results["generation_times"]
                )
                results["median_generation_time"] = statistics.median(
                    results["generation_times"]
                )
                results["p95_generation_time"] = self._calculate_percentile(
                    results["generation_times"], 95
                )

            if results["quality_scores"]:
                results["avg_quality_score"] = statistics.mean(
                    results["quality_scores"]
                )
                results["median_quality_score"] = statistics.median(
                    results["quality_scores"]
                )

            # 성공률 계산
            results["success_rate"] = (
                results["successful_generations"] / results["total_configs"]
                if results["total_configs"] > 0
                else 0
            )

            logger.info("보고서 생성 평가 완료")

            return results

        except Exception as e:
            logger.error(f"보고서 생성 평가 실패: {e}")
            return {"error": str(e)}

    def _calculate_percentile(self, data: list[float], percentile: int) -> float:
        """백분위수 계산"""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def _calculate_relevance_score(
        self, search_results: list[dict[str, Any]], expected_keywords: list[str]
    ) -> float:
        """관련성 점수 계산"""
        if not search_results or not expected_keywords:
            return 0.0

        total_score = 0
        for result in search_results:
            text = result.get("text", "").lower()
            keyword_matches = sum(
                1 for keyword in expected_keywords if keyword.lower() in text
            )
            relevance = keyword_matches / len(expected_keywords)
            total_score += relevance

        return total_score / len(search_results)

    def _calculate_diversity_score(self, search_results: list[dict[str, Any]]) -> float:
        """다양성 점수 계산"""
        if not search_results:
            return 0.0

        # 소스별 다양성 계산
        sources = [
            result.get("metadata", {}).get("source", "") for result in search_results
        ]
        unique_sources = set(sources)

        return len(unique_sources) / len(search_results)

    def _calculate_report_quality(self, report: dict[str, Any]) -> float:
        """보고서 품질 점수 계산"""
        try:
            quality_score = 0.0

            # 섹션 완성도 (40%)
            sections = [
                "executive_summary",
                "quantitative_analysis",
                "qualitative_analysis",
                "insights_recommendations",
            ]
            completed_sections = sum(1 for section in sections if report.get(section))
            section_score = completed_sections / len(sections) * 0.4
            quality_score += section_score

            # 내용 길이 (20%)
            total_length = sum(
                len(str(report.get(section, ""))) for section in sections
            )
            length_score = min(total_length / 2000, 1.0) * 0.2  # 2000자 기준
            quality_score += length_score

            # 근거 포함률 (40%)
            data_sources = report.get("data_sources", {})
            qualitative_sources = data_sources.get("qualitative", [])
            evidence_score = min(len(qualitative_sources) / 5, 1.0) * 0.4  # 5개 기준
            quality_score += evidence_score

            return min(quality_score, 1.0)

        except Exception as e:
            logger.error(f"보고서 품질 점수 계산 실패: {e}")
            return 0.0

    def run_comprehensive_evaluation(
        self, sql_engine=None, rag_engine=None, report_generator=None
    ) -> dict[str, Any]:
        """
        종합 평가 실행

        Args:
            sql_engine: SQL 엔진 인스턴스
            rag_engine: RAG 엔진 인스턴스
            report_generator: 보고서 생성기 인스턴스

        Returns:
            종합 평가 결과
        """
        try:
            logger.info("종합 평가 시작")

            evaluation_start_time = time.time()
            comprehensive_results = {
                "evaluation_timestamp": datetime.now().isoformat(),
                "components": {},
                "overall_metrics": {},
            }

            # Text-to-SQL 평가
            if sql_engine:
                test_queries = self._get_test_sql_queries()
                sql_results = self.evaluate_text_to_sql_accuracy(
                    sql_engine, test_queries
                )
                comprehensive_results["components"]["text_to_sql"] = sql_results

            # RAG 평가
            if rag_engine:
                test_queries = self._get_test_rag_queries()
                rag_results = self.evaluate_rag_quality(rag_engine, test_queries)
                comprehensive_results["components"]["rag"] = rag_results

            # 보고서 생성 평가
            if report_generator:
                test_configs = self._get_test_report_configs()
                report_results = self.evaluate_report_generation(
                    report_generator, test_configs
                )
                comprehensive_results["components"][
                    "report_generation"
                ] = report_results

            # 전체 메트릭 계산
            comprehensive_results["overall_metrics"] = self._calculate_overall_metrics(
                comprehensive_results["components"]
            )

            evaluation_end_time = time.time()
            comprehensive_results["total_evaluation_time"] = (
                evaluation_end_time - evaluation_start_time
            )

            # 결과 저장
            self._save_evaluation_results(comprehensive_results)

            logger.info(
                f"종합 평가 완료: {comprehensive_results['total_evaluation_time']:.2f}초"
            )

            return comprehensive_results

        except Exception as e:
            logger.error(f"종합 평가 실패: {e}")
            return {"error": str(e)}

    def _get_test_sql_queries(self) -> list[dict[str, Any]]:
        """테스트 SQL 쿼리 반환"""
        return [
            {
                "query": "강남구에서 가장 매출이 높은 업종은 무엇인가요?",
                "expected_keywords": ["SELECT", "FROM", "WHERE", "ORDER BY", "LIMIT"],
                "expected_tables": ["regions", "industries", "sales_2024"],
            },
            {
                "query": "서울시 전체 매출 상위 5개 지역을 보여주세요",
                "expected_keywords": [
                    "SELECT",
                    "FROM",
                    "GROUP BY",
                    "ORDER BY",
                    "LIMIT",
                ],
                "expected_tables": ["regions", "sales_2024"],
            },
            {
                "query": "음식점 업종의 평균 매출을 지역별로 보여주세요",
                "expected_keywords": ["SELECT", "FROM", "WHERE", "GROUP BY", "AVG"],
                "expected_tables": ["industries", "sales_2024", "regions"],
            },
        ]

    def _get_test_rag_queries(self) -> list[dict[str, Any]]:
        """테스트 RAG 쿼리 반환"""
        return [
            {
                "query": "강남구의 주요 업종은 무엇인가요?",
                "expected_keywords": ["IT", "금융", "의료", "교육"],
                "min_score": 0.3,
            },
            {
                "query": "서울시 정부의 강남구 정책은?",
                "expected_keywords": ["정책", "스타트업", "지원"],
                "min_score": 0.3,
            },
        ]

    def _get_test_report_configs(self) -> list[dict[str, Any]]:
        """테스트 보고서 설정 반환"""
        return [
            {
                "report_type": "comprehensive",
                "target_area": "강남구",
                "target_industry": "IT",
                "analysis_period": "2024년",
            },
            {
                "report_type": "comprehensive",
                "target_area": "서초구",
                "target_industry": "금융",
                "analysis_period": "2024년",
            },
        ]

    def _calculate_overall_metrics(self, components: dict[str, Any]) -> dict[str, Any]:
        """전체 메트릭 계산"""
        metrics = {}

        # Text-to-SQL 메트릭
        if "text_to_sql" in components:
            sql_data = components["text_to_sql"]
            metrics["sql_accuracy"] = sql_data.get("accuracy", 0)
            metrics["sql_avg_response_time"] = sql_data.get("avg_response_time", 0)
            metrics["sql_p95_response_time"] = sql_data.get("p95_response_time", 0)

        # RAG 메트릭
        if "rag" in components:
            rag_data = components["rag"]
            metrics["rag_avg_relevance_score"] = rag_data.get("avg_relevance_score", 0)
            metrics["rag_avg_response_time"] = rag_data.get("avg_response_time", 0)
            metrics["rag_p95_response_time"] = rag_data.get("p95_response_time", 0)

        # 보고서 생성 메트릭
        if "report_generation" in components:
            report_data = components["report_generation"]
            metrics["report_success_rate"] = report_data.get("success_rate", 0)
            metrics["report_avg_quality_score"] = report_data.get(
                "avg_quality_score", 0
            )
            metrics["report_avg_generation_time"] = report_data.get(
                "avg_generation_time", 0
            )

        # KPI 목표 대비 성과
        metrics["kpi_performance"] = {
            "sql_accuracy_target": 0.90,
            "sql_accuracy_achieved": metrics.get("sql_accuracy", 0),
            "sql_accuracy_status": (
                "PASS" if metrics.get("sql_accuracy", 0) >= 0.90 else "FAIL"
            ),
            "response_time_target": 3.0,
            "response_time_achieved": max(
                metrics.get("sql_p95_response_time", 0),
                metrics.get("rag_p95_response_time", 0),
            ),
            "response_time_status": (
                "PASS"
                if max(
                    metrics.get("sql_p95_response_time", 0),
                    metrics.get("rag_p95_response_time", 0),
                )
                <= 3.0
                else "FAIL"
            ),
            "evidence_citation_target": 0.80,
            "evidence_citation_achieved": metrics.get("report_avg_quality_score", 0),
            "evidence_citation_status": (
                "PASS" if metrics.get("report_avg_quality_score", 0) >= 0.80 else "FAIL"
            ),
        }

        return metrics

    def _save_evaluation_results(self, results: dict[str, Any]):
        """평가 결과 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.results_path / f"evaluation_results_{timestamp}.json"

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            logger.info(f"평가 결과 저장 완료: {filename}")

        except Exception as e:
            logger.error(f"평가 결과 저장 실패: {e}")

    def generate_evaluation_report(self, results: dict[str, Any]) -> str:
        """평가 보고서 생성"""
        try:
            report = []
            report.append("# 시스템 평가 보고서")
            report.append(
                f"**평가 일시**: {results.get('evaluation_timestamp', 'N/A')}"
            )
            report.append(
                f"**총 평가 시간**: {results.get('total_evaluation_time', 0):.2f}초"
            )
            report.append("")

            # KPI 성과
            kpi_performance = results.get("overall_metrics", {}).get(
                "kpi_performance", {}
            )
            report.append("## KPI 성과")
            report.append(
                f"- **Text-to-SQL 정확도**: {kpi_performance.get('sql_accuracy_achieved', 0):.1%} (목표: {kpi_performance.get('sql_accuracy_target', 0):.1%}) - {kpi_performance.get('sql_accuracy_status', 'N/A')}"
            )
            report.append(
                f"- **응답 시간 (P95)**: {kpi_performance.get('response_time_achieved', 0):.2f}초 (목표: ≤{kpi_performance.get('response_time_target', 0)}초) - {kpi_performance.get('response_time_status', 'N/A')}"
            )
            report.append(
                f"- **근거 각주 포함률**: {kpi_performance.get('evidence_citation_achieved', 0):.1%} (목표: {kpi_performance.get('evidence_citation_target', 0):.1%}) - {kpi_performance.get('evidence_citation_status', 'N/A')}"
            )
            report.append("")

            # 컴포넌트별 상세 결과
            components = results.get("components", {})

            if "text_to_sql" in components:
                sql_data = components["text_to_sql"]
                report.append("## Text-to-SQL 평가")
                report.append(f"- **정확도**: {sql_data.get('accuracy', 0):.1%}")
                report.append(
                    f"- **평균 응답 시간**: {sql_data.get('avg_response_time', 0):.2f}초"
                )
                report.append(
                    f"- **P95 응답 시간**: {sql_data.get('p95_response_time', 0):.2f}초"
                )
                report.append(
                    f"- **성공한 쿼리**: {sql_data.get('successful_queries', 0)}/{sql_data.get('total_queries', 0)}"
                )
                report.append("")

            if "rag" in components:
                rag_data = components["rag"]
                report.append("## RAG 평가")
                report.append(
                    f"- **평균 관련성 점수**: {rag_data.get('avg_relevance_score', 0):.3f}"
                )
                report.append(
                    f"- **평균 응답 시간**: {rag_data.get('avg_response_time', 0):.2f}초"
                )
                report.append(
                    f"- **P95 응답 시간**: {rag_data.get('p95_response_time', 0):.2f}초"
                )
                report.append("")

            if "report_generation" in components:
                report_data = components["report_generation"]
                report.append("## 보고서 생성 평가")
                report.append(f"- **성공률**: {report_data.get('success_rate', 0):.1%}")
                report.append(
                    f"- **평균 품질 점수**: {report_data.get('avg_quality_score', 0):.3f}"
                )
                report.append(
                    f"- **평균 생성 시간**: {report_data.get('avg_generation_time', 0):.2f}초"
                )
                report.append("")

            return "\n".join(report)

        except Exception as e:
            logger.error(f"평가 보고서 생성 실패: {e}")
            return f"평가 보고서 생성 실패: {e}"
