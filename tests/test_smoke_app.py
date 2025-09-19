"""
스모크 테스트: app.py 기본 기능 검증
Task1 완료 기준: streamlit run app.py 실행 시 탭 3개(SQL/문헌/보고서) 노출
"""

from unittest.mock import MagicMock, patch

import pytest


class TestSmokeApp:
    """Streamlit 앱 스모크 테스트"""

    def test_app_import(self):
        """app.py 모듈 import 테스트"""
        try:
            import app

            assert hasattr(app, "SeoulCommercialApp")
            assert hasattr(app, "main")
        except ImportError as e:
            pytest.fail(f"app.py import 실패: {e}")

    def test_app_class_creation(self):
        """SeoulCommercialApp 클래스 생성 테스트"""
        from app import SeoulCommercialApp

        # Mock을 사용하여 의존성 문제 회피
        with (
            patch("infrastructure.logging_service.StructuredLogger"),
            patch("infrastructure.cache_service.get_cache_service"),
            patch("utils.guards.get_sql_guard"),
            patch("utils.guards.get_prompt_guard"),
            patch("utils.guards.get_pii_guard"),
        ):

            app_instance = SeoulCommercialApp()
            assert app_instance is not None
            assert hasattr(app_instance, "initialize_session_state")
            assert hasattr(app_instance, "render_header")
            assert hasattr(app_instance, "render_sidebar")
            assert hasattr(app_instance, "process_query")

    def test_app_has_required_methods(self):
        """앱이 필요한 메서드를 가지고 있는지 테스트"""
        from app import SeoulCommercialApp

        with (
            patch("infrastructure.logging_service.StructuredLogger"),
            patch("infrastructure.cache_service.get_cache_service"),
            patch("utils.guards.get_sql_guard"),
            patch("utils.guards.get_prompt_guard"),
            patch("utils.guards.get_pii_guard"),
        ):

            app_instance = SeoulCommercialApp()

            # 필수 메서드 존재 확인
            required_methods = [
                "initialize_session_state",
                "render_header",
                "render_sidebar",
                "process_query",
                "_format_orchestrator_result",
                "_format_sql_result",
                "_format_rag_result",
                "_format_mixed_result",
                "route_intent",
            ]

            for method_name in required_methods:
                assert hasattr(
                    app_instance, method_name
                ), f"메서드 {method_name}이 없습니다"
                method = getattr(app_instance, method_name)
                assert callable(
                    method
                ), f"메서드 {method_name}이 호출 가능하지 않습니다"

    def test_session_state_initialization(self):
        """세션 상태 초기화 테스트"""
        from unittest.mock import patch

        from app import SeoulCommercialApp

        # Mock streamlit session_state
        mock_session_state = MagicMock()
        mock_session_state.__contains__ = MagicMock(return_value=False)
        mock_session_state.__setitem__ = MagicMock()

        with (
            patch("streamlit.session_state", mock_session_state),
            patch("infrastructure.logging_service.StructuredLogger"),
            patch("infrastructure.cache_service.get_cache_service"),
            patch("utils.guards.get_sql_guard"),
            patch("utils.guards.get_prompt_guard"),
            patch("utils.guards.get_pii_guard"),
        ):

            app_instance = SeoulCommercialApp()
            # initialize_session_state 메서드가 존재하고 호출 가능한지 확인
            assert hasattr(app_instance, "initialize_session_state")
            assert callable(app_instance.initialize_session_state)

            # 메서드 호출 시 예외가 발생하지 않는지 확인
            try:
                app_instance.initialize_session_state()
                assert True  # 예외가 발생하지 않으면 성공
            except Exception as e:
                pytest.fail(f"initialize_session_state 호출 중 예외 발생: {e}")

    def test_app_main_function_exists(self):
        """main 함수 존재 테스트"""
        from app import main

        assert callable(main)

    def test_app_can_handle_empty_query(self):
        """빈 쿼리 처리 테스트"""
        from unittest.mock import patch

        from app import SeoulCommercialApp

        # Mock streamlit session_state
        mock_session_state = MagicMock()
        mock_session_state.__contains__ = MagicMock(return_value=False)
        mock_session_state.__setitem__ = MagicMock()
        mock_session_state.session_id = "test_session"

        with (
            patch("streamlit.session_state", mock_session_state),
            patch("infrastructure.logging_service.StructuredLogger"),
            patch("infrastructure.cache_service.get_cache_service"),
            patch("utils.guards.get_sql_guard"),
            patch("utils.guards.get_prompt_guard"),
            patch("utils.guards.get_pii_guard"),
            patch(
                "orchestration.query_orchestrator.get_query_orchestrator"
            ) as mock_orchestrator,
        ):

            # Mock orchestrator 설정
            mock_orchestrator.return_value.process_query.return_value = {
                "success": False,
                "mode": "unknown",
                "result": None,
                "errors": ["빈 쿼리입니다"],
                "processing_time": 0,
            }

            app_instance = SeoulCommercialApp()
            app_instance.initialize_session_state()

            # 빈 쿼리 처리
            result = app_instance.process_query("", {})
            assert result is not None
            assert "success" in result or "error" in result


if __name__ == "__main__":
    pytest.main([__file__])
