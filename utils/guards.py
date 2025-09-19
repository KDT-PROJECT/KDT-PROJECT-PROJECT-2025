"""
보안 가드 모듈
SQL 쿼리 보안 검증 및 제한
tech-stack.mdc 규칙에 따른 구현
"""

import logging
import re
from typing import Any

from config import get_security_config

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLGuard:
    """SQL 쿼리 보안 가드"""

    def __init__(self):
        security_config = get_security_config()
        self.allowed_tables = security_config.get_allowed_tables_list()
        self.forbidden_keywords = [
            "INSERT",
            "UPDATE",
            "DELETE",
            "ALTER",
            "DROP",
            "TRUNCATE",
            "GRANT",
            "REVOKE",
            "CREATE",
            "EXEC",
            "EXECUTE",
            "CALL",
            "MERGE",
            "REPLACE",
            "LOAD",
            "UNLOAD",
            "COPY",
            "BULK",
        ]
        self.max_query_length = security_config.max_query_length
        self.max_execution_time = security_config.max_execution_time
        self.max_result_rows = security_config.max_result_rows
        self.default_limit = 1000

    def validate_query(self, query: str) -> bool:
        """SQL 쿼리 보안 검증"""
        try:
            if not query or not isinstance(query, str):
                logger.warning("빈 쿼리 또는 잘못된 타입")
                return False

            # 쿼리 길이 검증
            if len(query) > self.max_query_length:
                logger.warning(
                    f"쿼리 길이 초과: {len(query)} > {self.max_query_length}"
                )
                return False

            query_upper = query.upper().strip()

            # SELECT만 허용
            if not self._is_select_only(query_upper):
                logger.warning("SELECT가 아닌 쿼리는 허용되지 않습니다")
                return False

            # 금지된 키워드 검사
            if self._contains_forbidden_keywords(query_upper):
                logger.warning("금지된 키워드가 포함되어 있습니다")
                return False

            # 허용된 테이블만 사용
            if not self._uses_allowed_tables(query_upper):
                logger.warning("허용되지 않은 테이블이 포함되어 있습니다")
                return False

            # 복잡도 검증
            if self._is_too_complex(query_upper):
                logger.warning("쿼리가 너무 복잡합니다")
                return False

            logger.info("쿼리 검증 통과")
            return True

        except Exception as e:
            logger.error(f"쿼리 검증 중 오류 발생: {e}")
            return False

    def _is_select_only(self, query: str) -> bool:
        """SELECT만 허용하는지 검증"""
        # 주석 제거
        query_clean = re.sub(r"--.*$", "", query, flags=re.MULTILINE)
        query_clean = re.sub(r"/\*.*?\*/", "", query_clean, flags=re.DOTALL)

        # 공백 제거
        query_clean = re.sub(r"\s+", " ", query_clean).strip()

        # SELECT로 시작하는지 확인
        return query_clean.upper().startswith("SELECT")

    def _contains_forbidden_keywords(self, query: str) -> bool:
        """금지된 키워드 포함 여부 검사"""
        for keyword in self.forbidden_keywords:
            # 단어 경계를 고려한 검색
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, query):
                logger.warning(f"금지된 키워드 발견: {keyword}")
                return True
        return False

    def _uses_allowed_tables(self, query: str) -> bool:
        """허용된 테이블만 사용하는지 검증"""
        # FROM, JOIN 절에서 테이블명 추출
        table_patterns = [
            r"FROM\s+(\w+)",
            r"JOIN\s+(\w+)",
            r"UPDATE\s+(\w+)",
            r"INTO\s+(\w+)",
        ]

        found_tables = set()
        for pattern in table_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            found_tables.update(matches)

        # 허용된 테이블만 사용하는지 확인
        for table in found_tables:
            if table.lower() not in [t.lower() for t in self.allowed_tables]:
                logger.warning(f"허용되지 않은 테이블: {table}")
                return False

        return True

    def _is_too_complex(self, query: str) -> bool:
        """쿼리 복잡도 검증"""
        complexity_score = self.check_query_complexity(query)

        # 복잡도 임계값 설정
        max_complexity = 10

        if complexity_score > max_complexity:
            logger.warning(f"쿼리 복잡도 초과: {complexity_score} > {max_complexity}")
            return True

        return False

    def check_query_complexity(self, query: str) -> int:
        """쿼리 복잡도 점수 계산"""
        complexity_score = 0

        # JOIN 개수
        join_count = len(re.findall(r"\bJOIN\b", query, re.IGNORECASE))
        complexity_score += join_count * 2

        # 서브쿼리 개수
        subquery_count = len(
            re.findall(r"\([^)]*SELECT[^)]*\)", query, re.IGNORECASE | re.DOTALL)
        )
        complexity_score += subquery_count * 3

        # UNION 개수
        union_count = len(re.findall(r"\bUNION\b", query, re.IGNORECASE))
        complexity_score += union_count * 2

        # GROUP BY, ORDER BY, HAVING 절
        if re.search(r"\bGROUP\s+BY\b", query, re.IGNORECASE):
            complexity_score += 1
        if re.search(r"\bORDER\s+BY\b", query, re.IGNORECASE):
            complexity_score += 1
        if re.search(r"\bHAVING\b", query, re.IGNORECASE):
            complexity_score += 1

        # 함수 사용
        function_count = len(
            re.findall(r"\b(COUNT|SUM|AVG|MAX|MIN|DISTINCT)\b", query, re.IGNORECASE)
        )
        complexity_score += function_count

        return complexity_score

    def enforce_limit(self, query: str) -> str:
        """LIMIT 강제 적용"""
        query_upper = query.upper()

        # 이미 LIMIT이 있는지 확인
        if "LIMIT" in query_upper:
            return query

        # LIMIT 추가
        if query.strip().endswith(";"):
            query = query.rstrip(";")
            return f"{query} LIMIT {self.default_limit};"
        else:
            return f"{query} LIMIT {self.default_limit}"

    def sanitize_query(self, query: str) -> str:
        """쿼리 정제 (보안 강화)"""
        # 주석 제거
        query = re.sub(r"--.*$", "", query, flags=re.MULTILINE)
        query = re.sub(r"/\*.*?\*/", "", query, flags=re.DOTALL)

        # 연속된 공백을 하나로 변환
        query = re.sub(r"\s+", " ", query)

        # 앞뒤 공백 제거
        query = query.strip()

        # LIMIT 강제 적용
        query = self.enforce_limit(query)

        return query

    def get_query_metadata(self, query: str) -> dict[str, Any]:
        """쿼리 메타데이터 추출"""
        metadata = {
            "query_length": len(query),
            "complexity_score": self.check_query_complexity(query),
            "has_joins": bool(re.search(r"\bJOIN\b", query, re.IGNORECASE)),
            "has_subqueries": bool(
                re.search(r"\([^)]*SELECT[^)]*\)", query, re.IGNORECASE | re.DOTALL)
            ),
            "has_aggregations": bool(
                re.search(r"\b(COUNT|SUM|AVG|MAX|MIN)\b", query, re.IGNORECASE)
            ),
            "tables_used": self._extract_tables(query),
            "estimated_rows": self._estimate_result_rows(query),
        }

        return metadata

    def _extract_tables(self, query: str) -> list[str]:
        """쿼리에서 사용된 테이블 추출"""
        table_patterns = [r"FROM\s+(\w+)", r"JOIN\s+(\w+)"]

        tables = set()
        for pattern in table_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            tables.update(matches)

        return list(tables)

    def _estimate_result_rows(self, query: str) -> int:
        """예상 결과 행 수 추정"""
        # 간단한 추정 로직
        if "LIMIT" in query.upper():
            limit_match = re.search(r"LIMIT\s+(\d+)", query, re.IGNORECASE)
            if limit_match:
                return int(limit_match.group(1))

        # 기본값 반환
        return self.default_limit


class PromptInjectionGuard:
    """프롬프트 인젝션 방지 가드"""

    def __init__(self):
        self.forbidden_patterns = [
            r"ignore\s+previous\s+instructions",
            r"forget\s+everything",
            r"you\s+are\s+now",
            r"act\s+as\s+if",
            r"pretend\s+to\s+be",
            r"system\s+prompt",
            r"roleplay",
            r"jailbreak",
            r"bypass",
            r"override",
        ]

        self.suspicious_keywords = [
            "admin",
            "root",
            "password",
            "secret",
            "token",
            "api_key",
            "private",
            "confidential",
            "internal",
        ]

    def validate_input(self, user_input: str) -> dict[str, Any]:
        """사용자 입력 검증"""
        result = {
            "valid": True,
            "sanitized_input": user_input,
            "warnings": [],
            "blocked": False,
        }

        input_lower = user_input.lower()

        # 금지된 패턴 검사
        for pattern in self.forbidden_patterns:
            if re.search(pattern, input_lower):
                result["valid"] = False
                result["blocked"] = True
                result["warnings"].append(f"금지된 패턴 감지: {pattern}")
                logger.warning(f"프롬프트 인젝션 시도 감지: {pattern}")
                break

        # 의심스러운 키워드 검사
        for keyword in self.suspicious_keywords:
            if keyword in input_lower:
                result["warnings"].append(f"의심스러운 키워드: {keyword}")
                logger.info(f"의심스러운 키워드 감지: {keyword}")

        # 입력 정제
        if result["valid"]:
            result["sanitized_input"] = self._sanitize_input(user_input)

        return result

    def _sanitize_input(self, user_input: str) -> str:
        """입력 정제"""
        # 스크립트 태그 내용 제거 (먼저 처리)
        sanitized = re.sub(
            r"<script[^>]*>.*?</script>",
            "",
            user_input,
            flags=re.IGNORECASE | re.DOTALL,
        )

        # HTML 태그 제거
        sanitized = re.sub(r"<[^>]*>", "", sanitized)

        # 특수 문자 이스케이프
        sanitized = sanitized.replace("\\", "\\\\")
        sanitized = sanitized.replace('"', '\\"')
        sanitized = sanitized.replace("'", "\\'")

        # 연속된 공백 정리
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        return sanitized


class PIIGuard:
    """개인정보 보호 가드"""

    def __init__(self):
        # 개인정보 패턴
        self.pii_patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}-\d{4}-\d{4}\b|\b\d{10,11}\b|010-\d{4}-\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        }

        self.mask_char = "*"

    def detect_and_mask_pii(self, text: str) -> dict[str, Any]:
        """개인정보 감지 및 마스킹"""
        result = {
            "original_text": text,
            "masked_text": text,
            "pii_detected": [],
            "has_pii": False,
        }

        masked_text = text

        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                result["has_pii"] = True
                result["pii_detected"].extend(
                    [
                        {
                            "type": pii_type,
                            "value": match,
                            "masked_value": self._mask_value(match),
                        }
                        for match in matches
                    ]
                )

                # 마스킹 적용
                for match in matches:
                    masked_value = self._mask_value(match)
                    masked_text = masked_text.replace(match, masked_value)

        result["masked_text"] = masked_text

        if result["has_pii"]:
            logger.warning(f"개인정보 감지됨: {len(result['pii_detected'])}개 항목")

        return result

    def _mask_value(self, value: str) -> str:
        """값 마스킹"""
        if len(value) <= 4:
            return self.mask_char * len(value)
        else:
            return value[:2] + self.mask_char * (len(value) - 4) + value[-2:]


# 전역 가드 인스턴스
sql_guard = SQLGuard()
prompt_guard = PromptInjectionGuard()
pii_guard = PIIGuard()


def get_sql_guard() -> SQLGuard:
    """SQL 가드 인스턴스 반환"""
    return sql_guard


def get_prompt_guard() -> PromptInjectionGuard:
    """프롬프트 가드 인스턴스 반환"""
    return prompt_guard


def get_pii_guard() -> PIIGuard:
    """PII 가드 인스턴스 반환"""
    return pii_guard
