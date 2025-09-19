"""
의도 라우터 모듈
system-architecture.mdc 규칙에 따른 SQL vs RAG vs Mixed 질의 라우팅
"""

import logging
import re
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class QueryMode(Enum):
    """질의 모드 열거형"""

    SQL = "sql"
    RAG = "rag"
    MIXED = "mixed"
    EXTERNAL_DATA = "external_data"


class IntentRouter:
    """의도 라우터 클래스"""

    def __init__(self):
        """의도 라우터 초기화"""
        self.sql_keywords = {
            "high_confidence": [
                "매출",
                "거래",
                "데이터",
                "통계",
                "수치",
                "비교",
                "추이",
                "분석",
                "sales",
                "revenue",
                "transaction",
                "data",
                "statistics",
                "trend",
                "강남구",
                "서초구",
                "송파구",
                "강동구",
                "영등포구",
                "마포구",
                "용산구",
                "소매업",
                "음식점업",
                "카페",
                "숙박업",
                "여행업",
                "문화업",
            ],
            "medium_confidence": [
                "얼마",
                "몇",
                "어느",
                "가장",
                "최고",
                "최대",
                "최소",
                "평균",
                "how much",
                "how many",
                "which",
                "best",
                "highest",
                "lowest",
                "월별",
                "일별",
                "년별",
                "계절별",
                "시간별",
                "monthly",
                "daily",
                "yearly",
                "seasonal",
                "hourly",
            ],
            "low_confidence": [
                "보여",
                "알려",
                "찾아",
                "검색",
                "조회",
                "show",
                "tell",
                "find",
                "search",
                "query",
            ],
        }

        self.rag_keywords = {
            "high_confidence": [
                "정책",
                "동향",
                "인사이트",
                "문서",
                "정보",
                "가이드",
                "조언",
                "policy",
                "trend",
                "insight",
                "document",
                "information",
                "guide",
                "서울시",
                "정부",
                "지원",
                "제도",
                "방안",
                "전략",
                "government",
                "support",
                "system",
                "strategy",
                "plan",
            ],
            "medium_confidence": [
                "어떻게",
                "왜",
                "언제",
                "어디서",
                "무엇을",
                "how",
                "why",
                "when",
                "where",
                "what",
                "방법",
                "절차",
                "과정",
                "단계",
                "method",
                "procedure",
                "process",
                "step",
            ],
            "low_confidence": [
                "설명",
                "소개",
                "개요",
                "개념",
                "explain",
                "introduce",
                "overview",
                "concept",
            ],
        }

        self.mixed_keywords = [
            "분석하고",
            "조사하고",
            "연구하고",
            "검토하고",
            "analyze and",
            "investigate and",
            "study and",
            "review and",
            "종합",
            "통합",
            "전체",
            "완전",
            "comprehensive",
            "integrated",
            "complete",
            "full",
        ]

        self.external_data_keywords = {
            "high_confidence": [
                "외부",
                "공공데이터",
                "데이터포털",
                "공개데이터",
                "오픈데이터",
                "kaggle",
                "서울시데이터",
                "정부데이터",
                "external",
                "public data",
                "open data",
                "data portal",
                "government data",
            ],
            "medium_confidence": [
                "참조",
                "가져와",
                "수집",
                "다운로드",
                "참고",
                "reference",
                "fetch",
                "collect",
                "download",
                "refer",
                "데이터사이트",
                "포털",
                "사이트",
            ],
            "low_confidence": [
                "외부에서",
                "다른곳에서",
                "추가로",
                "더 많은",
                "from external",
                "from other",
                "additional",
                "more data",
            ],
        }

        # 패턴 기반 의도 감지
        self.sql_patterns = [
            r"(\d+년|\d+월|\d+일).*매출",
            r"(\w+구).*업종.*비교",
            r"(\w+업).*성장률",
            r"평균.*거래.*금액",
            r"최대.*매출.*지역",
            r"월별.*추이",
            r"계절별.*패턴",
        ]

        self.rag_patterns = [
            r"(\w+).*정책.*동향",
            r"(\w+).*지원.*제도",
            r"(\w+).*가이드.*정보",
            r"(\w+).*방안.*제안",
            r"(\w+).*전략.*계획",
        ]

        self.mixed_patterns = [
            r"(\w+).*분석.*인사이트",
            r"(\w+).*조사.*정책",
            r"(\w+).*연구.*데이터",
            r"(\w+).*검토.*보고서",
        ]

        self.external_data_patterns = [
            r"외부.*데이터.*참조",
            r"공공데이터.*가져와",
            r"데이터포털.*검색",
            r"kaggle.*데이터",
            r"서울시.*데이터.*포털",
            r"정부.*데이터.*참고",
            r"external.*data.*reference",
            r"public.*data.*fetch",
        ]

        logger.info("의도 라우터 초기화 완료")

    def route_intent(
        self, query: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        질의 의도 라우팅

        Args:
            query: 사용자 질의
            context: 추가 컨텍스트 정보

        Returns:
            라우팅 결과 딕셔너리
        """
        try:
            # 기본 라우팅 정보
            routing_result = {
                "mode": QueryMode.MIXED,
                "confidence": 0.0,
                "reasoning": [],
                "suggestions": [],
                "metadata": {
                    "query_length": len(query),
                    "has_numbers": bool(re.search(r"\d", query)),
                    "has_korean": bool(re.search(r"[가-힣]", query)),
                    "has_english": bool(re.search(r"[a-zA-Z]", query)),
                },
            }

            # 키워드 기반 점수 계산
            sql_score = self._calculate_keyword_score(query, self.sql_keywords)
            rag_score = self._calculate_keyword_score(query, self.rag_keywords)
            mixed_score = self._calculate_mixed_score(query)
            external_data_score = self._calculate_keyword_score(query, self.external_data_keywords)

            # 패턴 기반 점수 계산
            sql_pattern_score = self._calculate_pattern_score(query, self.sql_patterns)
            rag_pattern_score = self._calculate_pattern_score(query, self.rag_patterns)
            mixed_pattern_score = self._calculate_pattern_score(
                query, self.mixed_patterns
            )
            external_data_pattern_score = self._calculate_pattern_score(query, self.external_data_patterns)

            # 최종 점수 계산
            final_sql_score = sql_score + sql_pattern_score
            final_rag_score = rag_score + rag_pattern_score
            final_mixed_score = mixed_score + mixed_pattern_score
            final_external_data_score = external_data_score + external_data_pattern_score

            # 의도 결정 (외부 데이터 우선 고려)
            scores = {
                QueryMode.EXTERNAL_DATA: final_external_data_score,
                QueryMode.MIXED: final_mixed_score,
                QueryMode.SQL: final_sql_score,
                QueryMode.RAG: final_rag_score
            }
            
            # 가장 높은 점수의 모드 선택
            best_mode = max(scores, key=scores.get)
            best_score = scores[best_mode]
            
            # 외부 데이터 점수가 높은 경우 우선 처리
            if final_external_data_score > 0.3 and final_external_data_score >= best_score * 0.8:
                routing_result["mode"] = QueryMode.EXTERNAL_DATA
                routing_result["confidence"] = min(final_external_data_score, 1.0)
                routing_result["reasoning"].append(
                    f"외부 데이터 키워드 점수: {final_external_data_score:.2f}"
                )
            elif best_mode == QueryMode.MIXED:
                routing_result["mode"] = QueryMode.MIXED
                routing_result["confidence"] = min(final_mixed_score, 1.0)
                routing_result["reasoning"].append(
                    f"혼합 분석 키워드 점수: {final_mixed_score:.2f}"
                )
            elif best_mode == QueryMode.SQL:
                routing_result["mode"] = QueryMode.SQL
                routing_result["confidence"] = min(final_sql_score, 1.0)
                routing_result["reasoning"].append(
                    f"SQL 키워드 점수: {final_sql_score:.2f}"
                )
            else:
                routing_result["mode"] = QueryMode.RAG
                routing_result["confidence"] = min(final_rag_score, 1.0)
                routing_result["reasoning"].append(
                    f"RAG 키워드 점수: {final_rag_score:.2f}"
                )

            # 컨텍스트 기반 조정
            if context:
                routing_result = self._adjust_by_context(routing_result, context)

            # 제안사항 생성
            routing_result["suggestions"] = self._generate_suggestions(
                query, routing_result["mode"]
            )

            logger.info(
                f"의도 라우팅 완료: {routing_result['mode'].value} (신뢰도: {routing_result['confidence']:.2f})"
            )
            return routing_result

        except Exception as e:
            logger.error(f"의도 라우팅 중 오류 발생: {e}")
            return {
                "mode": QueryMode.MIXED,
                "confidence": 0.0,
                "reasoning": [f"오류 발생: {str(e)}"],
                "suggestions": [],
                "metadata": {},
            }

    def _calculate_keyword_score(
        self, query: str, keyword_groups: dict[str, list[str]]
    ) -> float:
        """키워드 기반 점수 계산"""
        query_lower = query.lower()
        total_score = 0.0

        for confidence_level, keywords in keyword_groups.items():
            weight = {
                "high_confidence": 1.0,
                "medium_confidence": 0.6,
                "low_confidence": 0.3,
            }.get(confidence_level, 0.1)

            matches = sum(1 for keyword in keywords if keyword in query_lower)
            total_score += matches * weight

        # 정규화 (쿼리 길이에 따라)
        max_possible_score = len(query) * 0.1  # 최대 점수 제한
        return min(total_score / max(max_possible_score, 1), 1.0)

    def _calculate_mixed_score(self, query: str) -> float:
        """혼합 분석 점수 계산"""
        query_lower = query.lower()
        mixed_matches = sum(
            1 for keyword in self.mixed_keywords if keyword in query_lower
        )

        # 혼합 키워드가 있으면 높은 점수
        if mixed_matches > 0:
            return 0.8

        # SQL과 RAG 키워드가 모두 있으면 중간 점수
        sql_matches = sum(
            1
            for keyword in self.sql_keywords["high_confidence"]
            if keyword in query_lower
        )
        rag_matches = sum(
            1
            for keyword in self.rag_keywords["high_confidence"]
            if keyword in query_lower
        )

        if sql_matches > 0 and rag_matches > 0:
            return 0.6

        return 0.0

    def _calculate_pattern_score(self, query: str, patterns: list[str]) -> float:
        """패턴 기반 점수 계산"""
        matches = 0
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                matches += 1

        return min(matches * 0.3, 1.0)  # 패턴 매치당 0.3점, 최대 1.0점

    def _adjust_by_context(
        self, routing_result: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """컨텍스트 기반 라우팅 조정"""
        # 이전 질의 히스토리 고려
        if "previous_queries" in context:
            recent_modes = [q.get("mode") for q in context["previous_queries"][-3:]]
            if recent_modes and all(mode == recent_modes[0] for mode in recent_modes):
                # 연속된 같은 모드 질의 시 해당 모드 선호
                routing_result["confidence"] += 0.1
                routing_result["reasoning"].append("이전 질의 패턴 고려")

        # 사용자 선호도 고려
        if "user_preferences" in context:
            preferred_mode = context["user_preferences"].get("preferred_mode")
            if preferred_mode and routing_result["mode"].value == preferred_mode:
                routing_result["confidence"] += 0.1
                routing_result["reasoning"].append("사용자 선호도 고려")

        # 시스템 상태 고려
        if "system_status" in context:
            if context["system_status"].get("sql_available", True) == False:
                if routing_result["mode"] == QueryMode.SQL:
                    routing_result["mode"] = QueryMode.RAG
                    routing_result["reasoning"].append(
                        "SQL 서비스 불가로 RAG 모드로 변경"
                    )

            if context["system_status"].get("rag_available", True) == False:
                if routing_result["mode"] == QueryMode.RAG:
                    routing_result["mode"] = QueryMode.SQL
                    routing_result["reasoning"].append(
                        "RAG 서비스 불가로 SQL 모드로 변경"
                    )

        return routing_result

    def _generate_suggestions(self, query: str, mode: QueryMode) -> list[str]:
        """제안사항 생성"""
        suggestions = []

        if mode == QueryMode.SQL:
            suggestions.extend(
                [
                    "구체적인 수치나 기간을 명시해보세요",
                    "비교하고 싶은 지역이나 업종을 명확히 해주세요",
                    "원하는 차트 유형을 알려주세요 (막대, 선, 원형 등)",
                ]
            )
        elif mode == QueryMode.RAG:
            suggestions.extend(
                [
                    "관련 정책이나 제도에 대해 더 자세히 알아보세요",
                    "특정 문서나 보고서를 찾고 계신가요?",
                    "최신 동향이나 인사이트를 원하시나요?",
                ]
            )
        elif mode == QueryMode.EXTERNAL_DATA:
            suggestions.extend(
                [
                    "외부 데이터 포털에서 관련 정보를 검색해드릴게요",
                    "공공데이터나 Kaggle 등의 외부 데이터를 참조할 수 있습니다",
                    "구체적으로 어떤 외부 데이터를 찾고 계신가요?",
                ]
            )
        else:  # MIXED
            suggestions.extend(
                [
                    "정량적 데이터와 정성적 분석을 모두 제공해드릴게요",
                    "구체적인 분석 범위를 알려주세요",
                    "어떤 형태의 보고서를 원하시나요?",
                ]
            )

        return suggestions

    def get_routing_stats(self) -> dict[str, Any]:
        """라우팅 통계 반환"""
        return {
            "sql_keywords_count": len(self.sql_keywords["high_confidence"])
            + len(self.sql_keywords["medium_confidence"])
            + len(self.sql_keywords["low_confidence"]),
            "rag_keywords_count": len(self.rag_keywords["high_confidence"])
            + len(self.rag_keywords["medium_confidence"])
            + len(self.rag_keywords["low_confidence"]),
            "mixed_keywords_count": len(self.mixed_keywords),
            "sql_patterns_count": len(self.sql_patterns),
            "rag_patterns_count": len(self.rag_patterns),
            "mixed_patterns_count": len(self.mixed_patterns),
        }


# 전역 의도 라우터 인스턴스
_intent_router = None


def get_intent_router() -> IntentRouter:
    """의도 라우터 인스턴스 반환"""
    global _intent_router
    if _intent_router is None:
        _intent_router = IntentRouter()
    return _intent_router
