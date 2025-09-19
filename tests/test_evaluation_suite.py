"""
평가 스위트 테스트
TASK-016: 평가 스위트 - 정확도/각주율/지연 벤치
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from pathlib import Path

from pipelines.eval_suite import EvaluationSuite


class TestEvaluationSuite:
    """평가 스위트 테스트 클래스"""

    @pytest.fixture
    def eval_suite(self):
        """평가 스위트 인스턴스 생성"""
        config = {
            "results_path": "test_models/artifacts/evaluation"
        }
        return EvaluationSuite(config)

    @pytest.fixture
    def mock_sql_engine(self):
        """Mock SQL 엔진 생성"""
        engine = MagicMock()
        engine.query.return_value = {
            "success": True,
            "sql_query": "SELECT * FROM regions WHERE name = '강남구'",
            "data": [{"name": "강남구", "sales": 1000000}]
        }
        return engine

    @pytest.fixture
    def mock_rag_engine(self):
        """Mock RAG 엔진 생성"""
        engine = MagicMock()
        engine.search.return_value = [
            {
                "text": "강남구는 IT와 금융업이 발달한 지역입니다.",
                "combined_score": 0.85,
                "vector_score": 0.8,
                "bm25_score": 0.9,
                "metadata": {"source": "강남구_정책문서.pdf"}
            }
        ]
        return engine

    @pytest.fixture
    def mock_report_generator(self):
        """Mock 보고서 생성기 생성"""
        generator = MagicMock()
        generator.generate_full_report.return_value = {
            "executive_summary": "강남구는 서울의 핵심 상권입니다.",
            "quantitative_analysis": "매출 데이터 분석 결과...",
            "qualitative_analysis": "정책 문서 분석 결과...",
            "insights_recommendations": "개선 방안 제시...",
            "data_sources": {
                "qualitative": ["강남구_정책문서.pdf", "스타트업_지원정책.pdf"]
            }
        }
        return generator

    def test_evaluation_suite_initialization(self, eval_suite):
        """평가 스위트 초기화 테스트"""
        assert eval_suite.config["results_path"] == "test_models/artifacts/evaluation"
        assert eval_suite.evaluation_results == {}
        assert eval_suite.performance_metrics == {}
        assert eval_suite.results_path.exists()

    def test_evaluate_text_to_sql_accuracy(self, eval_suite, mock_sql_engine):
        """Text-to-SQL 정확도 평가 테스트"""
        test_queries = [
            {
                "query": "강남구에서 가장 매출이 높은 업종은 무엇인가요?",
                "expected_keywords": ["SELECT", "FROM", "WHERE"],
                "expected_tables": ["regions", "sales_2024"]
            }
        ]

        with patch('time.time', side_effect=[0, 0.5]):  # Mock time for consistent testing
            results = eval_suite.evaluate_text_to_sql_accuracy(mock_sql_engine, test_queries)

        assert results["total_queries"] == 1
        assert results["successful_queries"] == 1
        assert results["failed_queries"] == 0
        assert results["accuracy"] == 1.0
        assert len(results["response_times"]) == 1
        assert results["response_times"][0] == 0.5
        assert len(results["query_results"]) == 1

        query_result = results["query_results"][0]
        assert query_result["success"] is True
        assert query_result["response_time"] == 0.5
        assert "SELECT" in query_result["sql_query"]

    def test_evaluate_text_to_sql_accuracy_with_failure(self, eval_suite):
        """Text-to-SQL 정확도 평가 실패 케이스 테스트"""
        mock_engine = MagicMock()
        mock_engine.query.return_value = {
            "success": False,
            "error": "SQL syntax error"
        }

        test_queries = [
            {
                "query": "잘못된 쿼리",
                "expected_keywords": ["SELECT"],
                "expected_tables": ["regions"]
            }
        ]

        with patch('time.time', side_effect=[0, 0.2]):
            results = eval_suite.evaluate_text_to_sql_accuracy(mock_engine, test_queries)

        assert results["total_queries"] == 1
        assert results["successful_queries"] == 0
        assert results["failed_queries"] == 1
        assert results["accuracy"] == 0.0

    def test_evaluate_rag_quality(self, eval_suite, mock_rag_engine):
        """RAG 품질 평가 테스트"""
        test_queries = [
            {
                "query": "강남구의 주요 업종은 무엇인가요?",
                "expected_keywords": ["IT", "금융"],
                "min_score": 0.3
            }
        ]

        with patch('time.time', side_effect=[0, 0.3]):
            results = eval_suite.evaluate_rag_quality(mock_rag_engine, test_queries)

        assert results["total_queries"] == 1
        assert len(results["response_times"]) == 1
        assert results["response_times"][0] == 0.3
        assert len(results["query_results"]) == 1

        query_result = results["query_results"][0]
        assert query_result["results_count"] == 1
        assert query_result["has_results"] is True
        assert query_result["avg_score"] == 0.85
        assert query_result["max_score"] == 0.85

    def test_evaluate_report_generation(self, eval_suite, mock_report_generator):
        """보고서 생성 평가 테스트"""
        test_configs = [
            {
                "report_type": "comprehensive",
                "target_area": "강남구",
                "target_industry": "IT"
            }
        ]

        with patch('time.time', side_effect=[0, 2.0]):
            results = eval_suite.evaluate_report_generation(mock_report_generator, test_configs)

        assert results["total_configs"] == 1
        assert results["successful_generations"] == 1
        assert results["failed_generations"] == 0
        assert results["success_rate"] == 1.0
        assert len(results["generation_times"]) == 1
        assert results["generation_times"][0] == 2.0

        config_result = results["config_results"][0]
        assert config_result["success"] is True
        assert config_result["generation_time"] == 2.0
        assert config_result["sections_generated"] == 4  # All 4 sections present

    def test_calculate_percentile(self, eval_suite):
        """백분위수 계산 테스트"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        assert eval_suite._calculate_percentile(data, 50) == 5  # median
        assert eval_suite._calculate_percentile(data, 95) == 10  # p95
        assert eval_suite._calculate_percentile([], 50) == 0.0  # empty data

    def test_calculate_relevance_score(self, eval_suite):
        """관련성 점수 계산 테스트"""
        search_results = [
            {"text": "강남구는 IT와 금융업이 발달한 지역입니다."},
            {"text": "강남구의 주요 산업은 IT와 금융입니다."}
        ]
        expected_keywords = ["IT", "금융"]

        score = eval_suite._calculate_relevance_score(search_results, expected_keywords)
        assert score > 0.5  # Should be high relevance

    def test_calculate_diversity_score(self, eval_suite):
        """다양성 점수 계산 테스트"""
        # High diversity (different sources)
        diverse_results = [
            {"metadata": {"source": "source1.pdf"}},
            {"metadata": {"source": "source2.pdf"}},
            {"metadata": {"source": "source3.pdf"}}
        ]
        diverse_score = eval_suite._calculate_diversity_score(diverse_results)
        assert diverse_score == 1.0  # Perfect diversity

        # Low diversity (same source)
        similar_results = [
            {"metadata": {"source": "source1.pdf"}},
            {"metadata": {"source": "source1.pdf"}},
            {"metadata": {"source": "source1.pdf"}}
        ]
        similar_score = eval_suite._calculate_diversity_score(similar_results)
        assert similar_score < 0.5  # Low diversity

    def test_calculate_report_quality(self, eval_suite):
        """보고서 품질 점수 계산 테스트"""
        # High quality report
        high_quality_report = {
            "executive_summary": "요약 내용" * 100,  # Long content
            "quantitative_analysis": "정량 분석" * 100,
            "qualitative_analysis": "정성 분석" * 100,
            "insights_recommendations": "인사이트" * 100,
            "data_sources": {
                "qualitative": ["doc1.pdf", "doc2.pdf", "doc3.pdf", "doc4.pdf", "doc5.pdf"]
            }
        }
        high_score = eval_suite._calculate_report_quality(high_quality_report)
        assert high_score > 0.8

        # Low quality report
        low_quality_report = {
            "executive_summary": "짧은 요약",
            "data_sources": {"qualitative": []}
        }
        low_score = eval_suite._calculate_report_quality(low_quality_report)
        assert low_score < 0.5

    def test_run_comprehensive_evaluation(self, eval_suite, mock_sql_engine, mock_rag_engine, mock_report_generator):
        """종합 평가 실행 테스트"""
        with patch('time.time', side_effect=[0, 0.5, 1.0, 1.5, 2.0]):  # Mock evaluation time
            results = eval_suite.run_comprehensive_evaluation(
                sql_engine=mock_sql_engine,
                rag_engine=mock_rag_engine,
                report_generator=mock_report_generator
            )

        assert "evaluation_timestamp" in results
        assert "components" in results
        assert "overall_metrics" in results
        assert "total_evaluation_time" in results

        # Check components
        assert "text_to_sql" in results["components"]
        assert "rag" in results["components"]
        assert "report_generation" in results["components"]

        # Check overall metrics
        overall_metrics = results["overall_metrics"]
        assert "kpi_performance" in overall_metrics
        kpi_perf = overall_metrics["kpi_performance"]
        assert "sql_accuracy_status" in kpi_perf
        assert "response_time_status" in kpi_perf
        assert "evidence_citation_status" in kpi_perf

    def test_generate_evaluation_report(self, eval_suite):
        """평가 보고서 생성 테스트"""
        mock_results = {
            "evaluation_timestamp": "2024-01-01T00:00:00",
            "total_evaluation_time": 10.5,
            "overall_metrics": {
                "kpi_performance": {
                    "sql_accuracy_achieved": 0.95,
                    "sql_accuracy_target": 0.90,
                    "sql_accuracy_status": "PASS",
                    "response_time_achieved": 2.5,
                    "response_time_target": 3.0,
                    "response_time_status": "PASS",
                    "evidence_citation_achieved": 0.85,
                    "evidence_citation_target": 0.80,
                    "evidence_citation_status": "PASS"
                }
            },
            "components": {
                "text_to_sql": {
                    "accuracy": 0.95,
                    "avg_response_time": 1.5,
                    "p95_response_time": 2.0,
                    "successful_queries": 19,
                    "total_queries": 20
                },
                "rag": {
                    "avg_relevance_score": 0.85,
                    "avg_response_time": 0.8,
                    "p95_response_time": 1.2
                },
                "report_generation": {
                    "success_rate": 1.0,
                    "avg_quality_score": 0.85,
                    "avg_generation_time": 3.0
                }
            }
        }

        report = eval_suite.generate_evaluation_report(mock_results)
        
        assert "# 시스템 평가 보고서" in report
        assert "KPI 성과" in report
        assert "Text-to-SQL 평가" in report
        assert "RAG 평가" in report
        assert "보고서 생성 평가" in report
        assert "PASS" in report  # KPI status should be included

    def test_save_evaluation_results(self, eval_suite):
        """평가 결과 저장 테스트"""
        test_results = {
            "evaluation_timestamp": "2024-01-01T00:00:00",
            "total_evaluation_time": 10.5,
            "components": {},
            "overall_metrics": {}
        }

        # Mock datetime to get consistent filename
        with patch('pipelines.eval_suite.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101_000000"
            eval_suite._save_evaluation_results(test_results)

        # Check if file was created
        expected_file = eval_suite.results_path / "evaluation_results_20240101_000000.json"
        assert expected_file.exists()

        # Clean up
        expected_file.unlink()

    def test_get_test_queries(self, eval_suite):
        """테스트 쿼리 반환 테스트"""
        sql_queries = eval_suite._get_test_sql_queries()
        assert len(sql_queries) == 3
        assert all("query" in q for q in sql_queries)
        assert all("expected_keywords" in q for q in sql_queries)
        assert all("expected_tables" in q for q in sql_queries)

        rag_queries = eval_suite._get_test_rag_queries()
        assert len(rag_queries) == 2
        assert all("query" in q for q in rag_queries)
        assert all("expected_keywords" in q for q in rag_queries)
        assert all("min_score" in q for q in rag_queries)

        report_configs = eval_suite._get_test_report_configs()
        assert len(report_configs) == 2
        assert all("report_type" in c for c in report_configs)
        assert all("target_area" in c for c in report_configs)
        assert all("target_industry" in c for c in report_configs)

    def test_calculate_overall_metrics(self, eval_suite):
        """전체 메트릭 계산 테스트"""
        components = {
            "text_to_sql": {
                "accuracy": 0.95,
                "avg_response_time": 1.5,
                "p95_response_time": 2.0
            },
            "rag": {
                "avg_relevance_score": 0.85,
                "avg_response_time": 0.8,
                "p95_response_time": 1.2
            },
            "report_generation": {
                "success_rate": 1.0,
                "avg_quality_score": 0.85,
                "avg_generation_time": 3.0
            }
        }

        metrics = eval_suite._calculate_overall_metrics(components)

        assert "sql_accuracy" in metrics
        assert "rag_avg_relevance_score" in metrics
        assert "report_success_rate" in metrics
        assert "kpi_performance" in metrics

        kpi_perf = metrics["kpi_performance"]
        assert kpi_perf["sql_accuracy_achieved"] == 0.95
        assert kpi_perf["sql_accuracy_status"] == "PASS"
        assert kpi_perf["response_time_achieved"] == 2.0  # max of sql and rag p95
        assert kpi_perf["response_time_status"] == "PASS"
        assert kpi_perf["evidence_citation_achieved"] == 0.85
        assert kpi_perf["evidence_citation_status"] == "PASS"
