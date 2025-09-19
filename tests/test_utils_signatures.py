"""
유틸리티 함수 시그니처 존재 검사
Task1 완료 기준: 핵심 함수 시그니처 존재 검사
"""

import inspect

import pytest


class TestUtilsSignatures:
    """유틸리티 함수 시그니처 테스트"""

    def test_data_loader_signatures(self):
        """data_loader.py 함수 시그니처 테스트"""
        try:
            from utils.data_loader import DataLoader

            # DataLoader 클래스 존재 확인
            assert hasattr(DataLoader, "__init__")
            assert hasattr(DataLoader, "load_csv_to_dataframe")
            assert hasattr(DataLoader, "process_csv_data")

            # 메서드 시그니처 확인
            init_sig = inspect.signature(DataLoader.__init__)
            load_csv_sig = inspect.signature(DataLoader.load_csv_to_dataframe)
            process_sig = inspect.signature(DataLoader.process_csv_data)

            # load_csv_to_dataframe 메서드 시그니처 확인
            assert "csv_path" in load_csv_sig.parameters
            assert (
                "return" in str(load_csv_sig.return_annotation)
                or load_csv_sig.return_annotation is not None
            )

            # process_csv_data 메서드 시그니처 확인
            assert "csv_path" in process_sig.parameters
            assert (
                "return" in str(process_sig.return_annotation)
                or process_sig.return_annotation is not None
            )

        except ImportError as e:
            pytest.fail(f"utils.data_loader import 실패: {e}")

    def test_sql_text2sql_signatures(self):
        """sql_text2sql.py 함수 시그니처 테스트"""
        try:
            from utils.sql_text2sql import TextToSQLConverter, nl_to_sql, run_sql

            # TextToSQLConverter 클래스 존재 확인
            assert hasattr(TextToSQLConverter, "__init__")
            assert hasattr(TextToSQLConverter, "convert_to_sql")
            assert hasattr(TextToSQLConverter, "get_schema_info")

            # 메서드 시그니처 확인
            init_sig = inspect.signature(TextToSQLConverter.__init__)
            convert_sig = inspect.signature(TextToSQLConverter.convert_to_sql)
            schema_sig = inspect.signature(TextToSQLConverter.get_schema_info)

            # convert_to_sql 메서드 시그니처 확인
            assert "natural_language_query" in convert_sig.parameters
            assert (
                "return" in str(convert_sig.return_annotation)
                or convert_sig.return_annotation is not None
            )

            # get_schema_info 메서드 시그니처 확인
            assert (
                "return" in str(schema_sig.return_annotation)
                or schema_sig.return_annotation is not None
            )

            # 함수들 존재 확인
            assert callable(nl_to_sql)
            assert callable(run_sql)

        except ImportError as e:
            pytest.fail(f"utils.sql_text2sql import 실패: {e}")

    def test_rag_hybrid_signatures(self):
        """rag_hybrid.py 함수 시그니처 테스트"""
        try:
            from utils.rag_hybrid import (
                BM25Retriever,
                HybridRetriever,
                SearchResult,
                VectorRetriever,
                get_hybrid_retriever,
            )

            # 클래스들 존재 확인
            assert hasattr(HybridRetriever, "__init__")
            assert hasattr(HybridRetriever, "add_documents")
            assert hasattr(HybridRetriever, "search")
            assert hasattr(HybridRetriever, "get_stats")

            assert hasattr(BM25Retriever, "__init__")
            assert hasattr(BM25Retriever, "search")

            assert hasattr(VectorRetriever, "__init__")
            assert hasattr(VectorRetriever, "add_documents")
            assert hasattr(VectorRetriever, "search")

            # SearchResult dataclass 확인
            assert hasattr(SearchResult, "__dataclass_fields__")

            # get_hybrid_retriever 함수 확인
            assert callable(get_hybrid_retriever)

            # HybridRetriever 메서드 시그니처 확인
            add_docs_sig = inspect.signature(HybridRetriever.add_documents)
            search_sig = inspect.signature(HybridRetriever.search)

            assert "documents" in add_docs_sig.parameters
            assert "query" in search_sig.parameters
            assert "top_k" in search_sig.parameters

        except ImportError as e:
            pytest.fail(f"utils.rag_hybrid import 실패: {e}")

    def test_viz_signatures(self):
        """viz.py 함수 시그니처 테스트"""
        try:
            from utils.viz import ChartGenerator, get_chart_generator

            # ChartGenerator 클래스 존재 확인
            assert hasattr(ChartGenerator, "__init__")
            assert hasattr(ChartGenerator, "create_sales_chart")
            assert hasattr(ChartGenerator, "create_comparison_chart")

            # get_chart_generator 함수 확인
            assert callable(get_chart_generator)

            # 메서드 시그니처 확인
            sales_chart_sig = inspect.signature(ChartGenerator.create_sales_chart)
            comparison_sig = inspect.signature(ChartGenerator.create_comparison_chart)

            # create_sales_chart 메서드 시그니처 확인
            assert "data" in sales_chart_sig.parameters
            assert "chart_type" in sales_chart_sig.parameters
            assert "title" in sales_chart_sig.parameters

            # create_comparison_chart 메서드 시그니처 확인
            assert "data" in comparison_sig.parameters
            assert "title" in comparison_sig.parameters

        except ImportError as e:
            pytest.fail(f"utils.viz import 실패: {e}")

    def test_utils_modules_importable(self):
        """utils 모듈들이 import 가능한지 테스트"""
        utils_modules = [
            "utils.data_loader",
            "utils.sql_text2sql",
            "utils.rag_hybrid",
            "utils.viz",
        ]

        for module_name in utils_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"모듈 {module_name} import 실패: {e}")

    def test_utils_init_file_exists(self):
        """utils/__init__.py 파일 존재 테스트"""
        from pathlib import Path

        init_file = Path("utils/__init__.py")
        assert init_file.exists(), "utils/__init__.py 파일이 존재하지 않습니다"

    def test_pipelines_init_file_exists(self):
        """pipelines/__init__.py 파일 존재 테스트"""
        from pathlib import Path

        init_file = Path("pipelines/__init__.py")
        assert init_file.exists(), "pipelines/__init__.py 파일이 존재하지 않습니다"

    def test_prompts_init_file_exists(self):
        """prompts/__init__.py 파일 존재 테스트"""
        from pathlib import Path

        init_file = Path("prompts/__init__.py")
        assert init_file.exists(), "prompts/__init__.py 파일이 존재하지 않습니다"

    def test_tests_init_file_exists(self):
        """tests/__init__.py 파일 존재 테스트"""
        from pathlib import Path

        init_file = Path("tests/__init__.py")
        assert init_file.exists(), "tests/__init__.py 파일이 존재하지 않습니다"


if __name__ == "__main__":
    pytest.main([__file__])
