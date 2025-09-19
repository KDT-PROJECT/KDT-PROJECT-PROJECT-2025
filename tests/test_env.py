"""
환경 변수 로드 및 필수 키 존재 여부 테스트
Task1 완료 기준: .env.example의 키 이름/설명 명확
"""

from pathlib import Path

import pytest
from dotenv import load_dotenv


class TestEnvironment:
    """환경 변수 테스트"""

    def test_env_example_exists(self):
        """env.example 파일 존재 테스트"""
        env_example_path = Path("env.example")
        assert env_example_path.exists(), "env.example 파일이 존재하지 않습니다"

    def test_env_example_has_required_keys(self):
        """env.example에 필수 키들이 있는지 테스트"""
        env_example_path = Path("env.example")

        with open(env_example_path, encoding="utf-8") as f:
            content = f.read()

        # Task1에서 요구하는 필수 키들
        required_keys = [
            "MYSQL_URL",
            "HF_MODEL",
            "GEMINI_API_KEY",
            "DB_HOST",
            "DB_PORT",
            "DB_USER",
            "DB_PASSWORD",
            "DB_NAME",
            "EMBEDDING_MODEL",
            "INDEX_PATH",
            "CHUNK_SIZE",
            "CHUNK_OVERLAP",
            "TOP_K",
            "ALPHA",
        ]

        missing_keys = []
        for key in required_keys:
            if f"{key}=" not in content:
                missing_keys.append(key)

        assert not missing_keys, f"env.example에 누락된 키들: {missing_keys}"

    def test_env_example_format(self):
        """env.example 파일 형식 테스트"""
        env_example_path = Path("env.example")

        with open(env_example_path, encoding="utf-8") as f:
            lines = f.readlines()

        # 빈 줄과 주석을 제외한 실제 설정 라인들
        config_lines = [
            line.strip()
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        ]

        for line in config_lines:
            # KEY=VALUE 형식인지 확인
            assert "=" in line, f"잘못된 형식의 라인: {line}"
            key, value = line.split("=", 1)
            assert key.strip(), f"키가 비어있는 라인: {line}"
            assert value.strip(), f"값이 비어있는 라인: {line}"

    def test_env_loading_without_file(self):
        """환경 파일 없이 로드 테스트 (스킵)"""
        # .env 파일이 없어도 에러가 발생하지 않아야 함
        try:
            load_dotenv(".env")
            # 파일이 없어도 예외가 발생하지 않아야 함
        except Exception as e:
            pytest.fail(f"환경 파일 로드 중 예상치 못한 오류: {e}")

    def test_env_loading_with_example_file(self):
        """env.example 파일로 로드 테스트"""
        env_example_path = Path("env.example")
        if env_example_path.exists():
            try:
                load_dotenv(env_example_path)
                # 로드 성공 확인
                assert True
            except Exception as e:
                pytest.fail(f"env.example 로드 실패: {e}")

    def test_required_env_vars_structure(self):
        """필수 환경 변수 구조 테스트"""
        env_example_path = Path("env.example")

        with open(env_example_path, encoding="utf-8") as f:
            content = f.read()

        # 데이터베이스 관련 키들
        db_keys = [
            "MYSQL_URL",
            "DB_HOST",
            "DB_PORT",
            "DB_USER",
            "DB_PASSWORD",
            "DB_NAME",
        ]
        for key in db_keys:
            assert f"{key}=" in content, f"데이터베이스 관련 키 {key}가 없습니다"

        # LLM 관련 키들
        llm_keys = ["HF_MODEL", "HF_API_KEY", "HF_TEMPERATURE", "HF_MAX_TOKENS"]
        for key in llm_keys:
            assert f"{key}=" in content, f"LLM 관련 키 {key}가 없습니다"

        # RAG 관련 키들
        rag_keys = [
            "EMBEDDING_MODEL",
            "INDEX_PATH",
            "CHUNK_SIZE",
            "CHUNK_OVERLAP",
            "TOP_K",
            "ALPHA",
        ]
        for key in rag_keys:
            assert f"{key}=" in content, f"RAG 관련 키 {key}가 없습니다"

    def test_env_example_has_comments(self):
        """env.example에 설명 주석이 있는지 테스트"""
        env_example_path = Path("env.example")

        with open(env_example_path, encoding="utf-8") as f:
            content = f.read()

        # 섹션별 주석이 있는지 확인
        section_comments = [
            "# Database Configuration",
            "# HuggingFace Model Configuration",
            "# RAG Configuration",
            "# Security Configuration",
            "# Gemini API (Optional)",
            "# Logging Configuration",
        ]

        for comment in section_comments:
            assert comment in content, f"섹션 주석 {comment}가 없습니다"


if __name__ == "__main__":
    pytest.main([__file__])
