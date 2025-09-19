"""
프로젝트 구조 및 환경 설정 테스트
TDD: 테스트 코드 먼저 작성
"""

import os
import sys

import pytest
from dotenv import load_dotenv


class TestProjectStructure:
    """프로젝트 구조 테스트"""

    def test_required_directories_exist(self):
        """필수 디렉토리가 존재하는지 확인"""
        required_dirs = [
            "data",
            "infrastructure",
            "llm",
            "pipelines",
            "prompts",
            "tests",
            "utils",
            "models",
            "logs",
        ]

        for dir_name in required_dirs:
            assert os.path.exists(dir_name), f"디렉토리 {dir_name}이 존재하지 않습니다"

    def test_required_files_exist(self):
        """필수 파일들이 존재하는지 확인"""
        required_files = ["requirements.txt", "env.example", "app.py", "config.py"]

        for file_name in required_files:
            assert os.path.exists(file_name), f"파일 {file_name}이 존재하지 않습니다"

    def test_requirements_txt_format(self):
        """requirements.txt 형식 검증"""
        with open("requirements.txt", encoding="utf-8") as f:
            content = f.read()

        # 버전 고정이 없어야 함 (최신 버전 설치)
        assert ">=" not in content, "requirements.txt에 버전 고정이 있습니다"
        assert "==" not in content, "requirements.txt에 버전 고정이 있습니다"

        # 필수 패키지들이 포함되어야 함
        required_packages = [
            "streamlit",
            "pandas",
            "sqlalchemy",
            "pymysql",
            "plotly",
            "python-dotenv",
            "llama-index",
            "transformers",
            "sentence-transformers",
            "chromadb",
            "pytest",
        ]

        for package in required_packages:
            assert package in content, f"패키지 {package}이 requirements.txt에 없습니다"


class TestEnvironmentSetup:
    """환경 설정 테스트"""

    def test_env_example_exists(self):
        """env.example 파일이 존재하는지 확인"""
        assert os.path.exists("env.example"), "env.example 파일이 존재하지 않습니다"

    def test_env_example_contains_required_vars(self):
        """env.example에 필수 환경변수가 포함되어 있는지 확인"""
        with open("env.example", encoding="utf-8") as f:
            content = f.read()

        required_vars = [
            "DB_HOST",
            "DB_PORT",
            "DB_USER",
            "DB_PASSWORD",
            "DB_NAME",
            "LLM_MODEL",
            "EMBEDDING_MODEL",
            "LOG_LEVEL",
        ]

        for var in required_vars:
            assert var in content, f"환경변수 {var}이 env.example에 없습니다"

    def test_env_loading(self):
        """환경변수 로딩 테스트"""
        # .env 파일이 없어도 에러가 발생하지 않아야 함
        try:
            load_dotenv("env.example")
            assert True
        except Exception as e:
            pytest.fail(f"환경변수 로딩 실패: {e}")


class TestPythonVersion:
    """Python 버전 테스트"""

    def test_python_version(self):
        """Python 3.12 버전 확인"""
        version = sys.version_info
        assert (
            version.major == 3
        ), f"Python 3.x가 필요합니다. 현재: {version.major}.{version.minor}"
        assert (
            version.minor >= 12
        ), f"Python 3.12+가 필요합니다. 현재: {version.major}.{version.minor}"


class TestDependencies:
    """의존성 테스트"""

    def test_core_dependencies_importable(self):
        """핵심 의존성 패키지들이 import 가능한지 확인"""
        try:
            import pandas
            import plotly
            import pydantic
            import sqlalchemy
            import streamlit

            assert True
        except ImportError as e:
            pytest.fail(f"핵심 의존성 import 실패: {e}")

    def test_llm_dependencies_importable(self):
        """LLM 관련 의존성 패키지들이 import 가능한지 확인"""
        try:
            import sentence_transformers
            import torch
            import transformers

            assert True
        except ImportError as e:
            pytest.fail(f"LLM 의존성 import 실패: {e}")

    def test_testing_dependencies_importable(self):
        """테스트 관련 의존성 패키지들이 import 가능한지 확인"""
        try:
            import mypy
            import pytest

            assert True
        except ImportError as e:
            pytest.fail(f"테스트 의존성 import 실패: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
