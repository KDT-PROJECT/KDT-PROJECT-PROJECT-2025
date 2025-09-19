"""
질의 오케스트레이터 모듈
system-architecture.mdc 규칙에 따른 통합 질의 처리 및 오류 처리
"""

import logging
import time
from datetime import datetime
from typing import Any

from infrastructure.cache_service import get_query_cache
from infrastructure.logging_service import StructuredLogger
from llm.text_to_sql import get_text_to_sql_service
from orchestration.intent_router import QueryMode, get_intent_router
from utils.guards import get_pii_guard, get_prompt_guard, get_sql_guard
from retrieval.hybrid_external_rag import get_hybrid_external_rag_service

logger = logging.getLogger(__name__)


class QueryOrchestrator:
    """질의 오케스트레이터 클래스"""

    def __init__(self):
        """오케스트레이터 초기화"""
        self.intent_router = get_intent_router()
        self.text_to_sql_service = get_text_to_sql_service()
        self.sql_guard = get_sql_guard()
        self.prompt_guard = get_prompt_guard()
        self.pii_guard = get_pii_guard()
        self.cache = get_query_cache()
        self.logger = StructuredLogger("query_orchestrator")
        self.hybrid_external_service = get_hybrid_external_rag_service()

        # 오류 처리 설정
        self.max_retries = 3
        self.timeout_seconds = 30
        self.fallback_enabled = True

        logger.info("질의 오케스트레이터 초기화 완료")

    def process_query(
        self, query: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        통합 질의 처리

        Args:
            query: 사용자 질의
            context: 컨텍스트 정보

        Returns:
            처리 결과 딕셔너리
        """
        start_time = time.time()
        query_id = f"query_{int(time.time() * 1000)}"

        try:
            # 1. 입력 검증 및 전처리
            validation_result = self._validate_input(query)
            if not validation_result["valid"]:
                return self._create_error_response(
                    query_id, "입력 검증 실패", validation_result["errors"], start_time
                )

            # 2. 의도 라우팅
            routing_result = self.intent_router.route_intent(query, context)
            mode = routing_result["mode"]
            confidence = routing_result["confidence"]

            # 3. 캐시 확인
            cached_result = self._check_cache(query, mode, context)
            if cached_result:
                self.logger.info(f"캐시에서 결과 반환: {query_id}")
                return self._create_success_response(
                    query_id,
                    cached_result,
                    mode,
                    confidence,
                    start_time,
                    from_cache=True,
                )

            # 4. 질의 처리 실행
            processing_result = self._execute_query_processing(query, mode, context)

            # 5. 결과 후처리 및 캐싱
            final_result = self._postprocess_result(processing_result, mode, context)
            self._cache_result(query, mode, final_result, context)

            # 6. 성공 응답 생성
            return self._create_success_response(
                query_id, final_result, mode, confidence, start_time
            )

        except Exception as e:
            self.logger.error(
                f"질의 처리 중 예상치 못한 오류: {e}",
                query_id=query_id,
                errors=[str(e)],
            )
            return self._create_error_response(
                query_id, "시스템 오류", [str(e)], start_time
            )

    def _validate_input(self, query: str) -> dict[str, Any]:
        """입력 검증"""
        errors = []

        # 기본 검증
        if not query or not query.strip():
            errors.append("빈 질의입니다")
            return {"valid": False, "errors": errors}

        if len(query) > 5000:
            errors.append("질의가 너무 깁니다 (최대 5000자)")
            return {"valid": False, "errors": errors}

        # PII 검사
        pii_result = self.pii_guard.detect_and_mask_pii(query)
        if pii_result["has_pii"]:
            errors.append("개인정보가 포함되어 있습니다")

        # 프롬프트 인젝션 검사
        prompt_result = self.prompt_guard.validate_input(query)
        if not prompt_result["valid"]:
            errors.append("잘못된 입력 형식입니다")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "sanitized_query": prompt_result.get("sanitized_input", query),
        }

    def _check_cache(
        self, query: str, mode: QueryMode, context: dict[str, Any] | None
    ) -> Any | None:
        """캐시 확인"""
        try:
            if mode == QueryMode.SQL:
                return self.cache.get_sql_result(
                    query, **self._get_cache_params(context)
                )
            elif mode == QueryMode.RAG:
                return self.cache.get_rag_result(
                    query, **self._get_cache_params(context)
                )
            elif mode == QueryMode.MIXED:
                return self.cache.get_mixed_result(
                    query, **self._get_cache_params(context)
                )
        except Exception as e:
            self.logger.warning(f"캐시 확인 중 오류: {e}")
        return None

    def _get_cache_params(self, context: dict[str, Any] | None) -> dict[str, Any]:
        """캐시 파라미터 추출"""
        if not context:
            return {}

        return {
            "user_id": context.get("user_id"),
            "session_id": context.get("session_id"),
            "preferences": context.get("user_preferences", {}),
        }

    def _execute_query_processing(
        self, query: str, mode: QueryMode, context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """질의 처리 실행"""
        if mode == QueryMode.SQL:
            return self._process_sql_query(query, context)
        elif mode == QueryMode.RAG:
            return self._process_rag_query(query, context)
        elif mode == QueryMode.MIXED:
            return self._process_mixed_query(query, context)
        elif mode == QueryMode.EXTERNAL_DATA:
            return self._process_external_data_query(query, context)
        else:
            raise ValueError(f"지원하지 않는 모드: {mode}")

    def _process_sql_query(
        self, query: str, context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """SQL 질의 처리"""
        try:
            # Text-to-SQL 변환
            sql_query = self.text_to_sql_service.generate_sql_query(query)

            if not sql_query:
                return {
                    "success": False,
                    "error": "SQL 쿼리 생성 실패",
                    "fallback_available": True,
                }

            # SQL 검증
            if not self.sql_guard.validate_query(sql_query):
                return {
                    "success": False,
                    "error": "SQL 쿼리 검증 실패",
                    "fallback_available": True,
                }

            # SQL 실행 (실제 구현에서는 데이터베이스 연결)
            # 여기서는 샘플 데이터 반환
            sample_data = self._generate_sample_data()

            return {
                "success": True,
                "sql_query": sql_query,
                "data": sample_data,
                "metadata": {
                    "query_type": "sql",
                    "result_rows": len(sample_data),
                    "execution_time": 0.1,
                },
            }

        except Exception as e:
            self.logger.error(f"SQL 질의 처리 중 오류: {e}")
            return {"success": False, "error": str(e), "fallback_available": True}

    def _process_rag_query(
        self, query: str, context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """RAG 질의 처리 - 질의 유사도 기반 우선순위 정렬"""
        try:
            # 질의 전처리 및 키워드 추출
            processed_query = self._preprocess_query(query)
            query_keywords = self._extract_keywords(processed_query)
            
            # 하이브리드 검색 (실제 구현에서는 RAG 서비스 사용)
            # 여기서는 샘플 결과를 질의 유사도 기반으로 정렬
            sample_results = [
                {
                    "title": "서울시 상권 활성화 정책",
                    "content": "서울시는 상권 활성화를 위해 다양한 정책을 시행하고 있습니다. 상권 진입 지원, 창업 지원, 매출 증대 방안 등을 포함합니다.",
                    "source": "서울시 상권정책.pdf",
                    "score": 0.95,
                },
                {
                    "title": "상권 분석 보고서 2024",
                    "content": "2024년 상권 분석 결과, 강남구가 가장 높은 성장률을 보였습니다. 매출 데이터와 상권 활성화 지표를 종합 분석했습니다.",
                    "source": "상권분석보고서.pdf",
                    "score": 0.87,
                },
                {
                    "title": "창업 지원 정책 가이드",
                    "content": "창업을 위한 지원 정책과 상권 진입 방안에 대한 상세한 안내입니다. 정부 지원금과 지역별 특화 정책을 소개합니다.",
                    "source": "창업지원가이드.pdf",
                    "score": 0.82,
                },
                {
                    "title": "매출 데이터 분석 방법론",
                    "content": "상권 매출 데이터를 분석하는 방법과 지표에 대한 설명입니다. 통계적 분석 기법과 시각화 방법을 다룹니다.",
                    "source": "데이터분석방법론.pdf",
                    "score": 0.78,
                }
            ]
            
            # 질의 유사도 기반 점수 계산 및 정렬
            scored_results = []
            for result in sample_results:
                content = result.get('content', '')
                title = result.get('title', '')
                
                # 질의 유사도 점수 계산
                query_similarity = self._calculate_query_similarity(query, content)
                title_similarity = self._calculate_query_similarity(query, title)
                
                # 키워드 매칭 점수
                keyword_score = self._calculate_keyword_score(query_keywords, content)
                
                # 종합 점수 계산 (기존 점수 + 질의 유사도)
                final_score = (
                    result['score'] * 0.5 +           # 기존 점수
                    query_similarity * 0.3 +          # 내용 유사도
                    title_similarity * 0.15 +         # 제목 유사도
                    keyword_score * 0.05              # 키워드 매칭
                )
                
                result['query_similarity'] = query_similarity
                result['title_similarity'] = title_similarity
                result['keyword_score'] = keyword_score
                result['final_score'] = final_score
                
                scored_results.append(result)
            
            # 질의 유사도 순으로 정렬
            scored_results.sort(key=lambda x: x['final_score'], reverse=True)
            
            # 관련성 필터링 (최소 점수 이상만 포함)
            filtered_results = [
                result for result in scored_results 
                if result['final_score'] >= 0.3
            ]

            return {
                "success": True,
                "results": filtered_results,
                "metadata": {
                    "query_type": "rag",
                    "result_count": len(filtered_results),
                    "search_time": 0.2,
                    "query_similarity_enabled": True,
                    "min_score_threshold": 0.3,
                },
            }

        except Exception as e:
            self.logger.error(f"RAG 질의 처리 중 오류: {e}")
            return {"success": False, "error": str(e), "fallback_available": True}

    def _process_mixed_query(
        self, query: str, context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """혼합 질의 처리"""
        try:
            # SQL 결과
            sql_result = self._process_sql_query(query, context)

            # RAG 결과
            rag_result = self._process_rag_query(query, context)

            # 결과 통합
            return {
                "success": sql_result["success"] or rag_result["success"],
                "sql_result": sql_result,
                "rag_result": rag_result,
                "metadata": {
                    "query_type": "mixed",
                    "sql_success": sql_result["success"],
                    "rag_success": rag_result["success"],
                },
            }

        except Exception as e:
            self.logger.error(f"혼합 질의 처리 중 오류: {e}")
            return {"success": False, "error": str(e), "fallback_available": True}

    def _process_external_data_query(
        self, query: str, context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """외부 데이터 질의 처리"""
        try:
            # 하이브리드 외부 데이터 검색 실행
            hybrid_result = self.hybrid_external_service.search_hybrid(
                query=query,
                max_results=20,
                include_external=True,
                include_rag=True,
                include_sql=True
            )
            
            if hybrid_result["success"]:
                # 결과를 표준 형태로 변환
                formatted_results = []
                for result in hybrid_result["results"]:
                    formatted_results.append({
                        "title": result["title"],
                        "content": result["content"],
                        "source": result["source"],
                        "url": result["url"],
                        "score": result["relevance_score"],
                        "type": result["result_type"],
                        "timestamp": result["timestamp"],
                        "metadata": result["metadata"]
                    })
                
                return {
                    "success": True,
                    "results": formatted_results,
                    "metadata": {
                        "query_type": "external_data",
                        "result_count": len(formatted_results),
                        "search_time": hybrid_result["metadata"]["processing_time"],
                        "sources_used": hybrid_result["metadata"]["sources_used"],
                        "summary": hybrid_result["summary"]
                    },
                }
            else:
                return {
                    "success": False,
                    "error": hybrid_result.get("error", "외부 데이터 검색 실패"),
                    "fallback_available": True,
                }

        except Exception as e:
            self.logger.error(f"외부 데이터 질의 처리 중 오류: {e}")
            return {"success": False, "error": str(e), "fallback_available": True}

    def _postprocess_result(
        self, result: dict[str, Any], mode: QueryMode, context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """결과 후처리"""
        # 결과 포맷팅
        if mode == QueryMode.SQL:
            return self._format_sql_result(result)
        elif mode == QueryMode.RAG:
            return self._format_rag_result(result)
        elif mode == QueryMode.MIXED:
            return self._format_mixed_result(result)
        else:
            return result

    def _format_sql_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """SQL 결과 포맷팅 - 질의 관련성 기반 정렬"""
        if not result["success"]:
            return result

        # 데이터 시각화 정보 추가
        if "data" in result:
            # 질의 관련성에 따른 차트 타입 결정
            chart_config = self._determine_chart_config(result.get("sql_query", ""))
            result["visualization"] = chart_config
            
            # 데이터 정렬 (질의 의도에 따라)
            if "data" in result and isinstance(result["data"], list):
                result["data"] = self._sort_data_by_query_intent(result["data"])

        return result
    
    def _determine_chart_config(self, sql_query: str) -> dict[str, Any]:
        """SQL 쿼리 분석을 통한 차트 설정 결정"""
        try:
            sql_lower = sql_query.lower()
            
            # 집계 함수 기반 차트 타입 결정
            if "sum(" in sql_lower or "count(" in sql_lower:
                if "group by" in sql_lower:
                    return {
                        "chart_type": "bar",
                        "x_axis": "category",
                        "y_axis": "value",
                        "title": "집계 데이터 분석",
                    }
                else:
                    return {
                        "chart_type": "number",
                        "title": "총합 데이터",
                    }
            elif "avg(" in sql_lower or "mean" in sql_lower:
                return {
                    "chart_type": "line",
                    "x_axis": "category",
                    "y_axis": "average",
                    "title": "평균 데이터 추이",
                }
            else:
                return {
                    "chart_type": "table",
                    "title": "상세 데이터 조회",
                }
                
        except Exception as e:
            self.logger.error(f"차트 설정 결정 중 오류: {e}")
            return {
                "chart_type": "bar",
                "x_axis": "region",
                "y_axis": "sales",
                "title": "데이터 분석",
            }
    
    def _sort_data_by_query_intent(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """질의 의도에 따른 데이터 정렬"""
        try:
            if not data:
                return data
            
            # 숫자 컬럼이 있는 경우 내림차순 정렬
            numeric_columns = []
            for key in data[0].keys():
                if any(keyword in key.lower() for keyword in ['매출', '금액', '건수', 'sales', 'amount', 'count']):
                    numeric_columns.append(key)
            
            if numeric_columns:
                # 첫 번째 숫자 컬럼으로 정렬
                sort_key = numeric_columns[0]
                return sorted(data, key=lambda x: x.get(sort_key, 0), reverse=True)
            
            return data
            
        except Exception as e:
            self.logger.error(f"데이터 정렬 중 오류: {e}")
            return data

    def _format_rag_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """RAG 결과 포맷팅 - 질의 유사도 기반 정렬 및 필터링"""
        if not result["success"]:
            return result

        # 결과 요약 추가
        if "results" in result:
            results = result["results"]
            
            # 질의 유사도 기반 재정렬 (추가 보정)
            if "query_similarity_enabled" in result.get("metadata", {}):
                results = self._apply_query_similarity_ranking(results)
            
            # 관련성 기반 필터링
            filtered_results = self._filter_results_by_relevance(results)
            
            result["results"] = filtered_results
            result["summary"] = (
                f"총 {len(filtered_results)}개의 관련 문서를 찾았습니다. "
                f"(질의 유사도 기반 정렬, 관련성 필터링 적용)"
            )
            
            # 메타데이터 업데이트
            if "metadata" in result:
                result["metadata"]["filtered_count"] = len(filtered_results)
                result["metadata"]["original_count"] = len(results)

        return result

    def _format_mixed_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """혼합 결과 포맷팅"""
        if not result["success"]:
            return result

        # 통합 요약 생성
        summary_parts = []

        if result.get("sql_result", {}).get("success"):
            summary_parts.append("정량적 데이터 분석 완료")

        if result.get("rag_result", {}).get("success"):
            summary_parts.append("관련 문서 검색 완료")

        result["summary"] = " | ".join(summary_parts)

        return result

    def _cache_result(
        self,
        query: str,
        mode: QueryMode,
        result: dict[str, Any],
        context: dict[str, Any] | None,
    ) -> None:
        """결과 캐싱"""
        try:
            cache_params = self._get_cache_params(context)

            if mode == QueryMode.SQL:
                self.cache.set_sql_result(query, result, **cache_params)
            elif mode == QueryMode.RAG:
                self.cache.set_rag_result(query, result, **cache_params)
            elif mode == QueryMode.MIXED:
                self.cache.set_mixed_result(query, result, **cache_params)

        except Exception as e:
            self.logger.warning(f"결과 캐싱 중 오류: {e}")

    def _preprocess_query(self, query: str) -> str:
        """질의 전처리"""
        try:
            import re
            # 불필요한 문자 제거 및 정규화
            processed = re.sub(r'[^\w\s가-힣]', ' ', query)
            processed = ' '.join(processed.split())
            return processed.lower()
        except Exception as e:
            self.logger.error(f"질의 전처리 중 오류: {e}")
            return query.lower()
    
    def _extract_keywords(self, query: str) -> list[str]:
        """질의에서 키워드 추출"""
        try:
            # 불용어 제거
            stop_words = {'은', '는', '이', '가', '을', '를', '에', '의', '로', '으로', '와', '과', '도', '만', '부터', '까지', '에서', '에게', '한테', '에게서', '한테서', '의', '것', '수', '등', '및', '또는', '그리고', '하지만', '그러나', '어떤', '무엇', '어디', '언제', '왜', '어떻게'}
            words = query.split()
            keywords = [word for word in words if word not in stop_words and len(word) > 1]
            return keywords
        except Exception as e:
            self.logger.error(f"키워드 추출 중 오류: {e}")
            return query.split()
    
    def _calculate_query_similarity(self, query: str, content: str) -> float:
        """질의와 콘텐츠 간의 유사도 계산"""
        try:
            query_lower = query.lower()
            content_lower = content.lower()
            
            # Jaccard 유사도
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            
            if not query_words or not content_words:
                return 0.0
            
            intersection = query_words.intersection(content_words)
            union = query_words.union(content_words)
            jaccard_sim = len(intersection) / len(union) if union else 0.0
            
            # 부분 문자열 매칭 점수
            partial_match_score = 0.0
            for query_word in query_words:
                if any(query_word in content_word for content_word in content_words):
                    partial_match_score += 0.5
            partial_match_score = min(partial_match_score / len(query_words), 1.0)
            
            # 최종 유사도
            final_similarity = (jaccard_sim * 0.7 + partial_match_score * 0.3)
            return min(final_similarity, 1.0)

        except Exception as e:
            self.logger.error(f"질의 유사도 계산 중 오류: {e}")
            return 0.0
    
    def _apply_query_similarity_ranking(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """질의 유사도 기반 결과 재정렬"""
        try:
            # 이미 점수가 계산된 결과들을 최종 점수순으로 정렬
            sorted_results = sorted(
                results, 
                key=lambda x: x.get('final_score', x.get('score', 0)), 
                reverse=True
            )
            return sorted_results
        except Exception as e:
            self.logger.error(f"질의 유사도 기반 정렬 중 오류: {e}")
            return results
    
    def _filter_results_by_relevance(self, results: list[dict[str, Any]], 
                                   min_score: float = 0.3,
                                   max_results: int = 10) -> list[dict[str, Any]]:
        """관련성 기반 결과 필터링"""
        try:
            filtered_results = []
            
            for result in results:
                # 최소 점수 이상인 결과만 포함
                final_score = result.get('final_score', result.get('score', 0))
                if final_score >= min_score:
                    # 추가 관련성 검증
                    if self._is_result_relevant(result):
                        filtered_results.append(result)
                        
                        # 최대 결과 수 제한
                        if len(filtered_results) >= max_results:
                            break
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"관련성 필터링 중 오류: {e}")
            return results[:max_results]
    
    def _is_result_relevant(self, result: dict[str, Any]) -> bool:
        """결과의 관련성 검증"""
        try:
            # 기본 점수 확인
            final_score = result.get('final_score', result.get('score', 0))
            if final_score < 0.2:
                return False
            
            # 제목과 내용의 품질 확인
            title = result.get('title', '')
            content = result.get('content', '')
            
            # 너무 짧은 내용 제외
            if len(content.strip()) < 10:
                return False
            
            # 제목이 있는 경우 우선순위 부여
            if title and len(title.strip()) > 0:
                return True
            
            # 내용이 충분히 긴 경우 포함
            if len(content.strip()) > 50:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"관련성 검증 중 오류: {e}")
            return True  # 오류 시 포함

    def _calculate_keyword_score(self, keywords: list[str], content: str) -> float:
        """키워드 매칭 점수 계산"""
        try:
            if not keywords:
                return 0.0
            
            content_lower = content.lower()
            matches = sum(1 for keyword in keywords if keyword in content_lower)
            return matches / len(keywords)

        except Exception as e:
            self.logger.error(f"키워드 점수 계산 중 오류: {e}")
            return 0.0

    def _generate_sample_data(self) -> list[dict[str, Any]]:
        """샘플 데이터 생성"""
        return [
            {"region": "강남구", "sales": 1000000, "transactions": 1000},
            {"region": "서초구", "sales": 800000, "transactions": 800},
            {"region": "송파구", "sales": 600000, "transactions": 600},
        ]

    def _create_success_response(
        self,
        query_id: str,
        result: dict[str, Any],
        mode: QueryMode,
        confidence: float,
        start_time: float,
        from_cache: bool = False,
    ) -> dict[str, Any]:
        """성공 응답 생성"""
        processing_time = time.time() - start_time

        return {
            "query_id": query_id,
            "success": True,
            "mode": mode.value,
            "confidence": confidence,
            "result": result,
            "processing_time": processing_time,
            "from_cache": from_cache,
            "timestamp": datetime.now().isoformat(),
            "metadata": {"orchestrator_version": "1.0.0", "cache_hit": from_cache},
        }

    def _create_error_response(
        self, query_id: str, error_type: str, errors: list[str], start_time: float
    ) -> dict[str, Any]:
        """오류 응답 생성"""
        processing_time = time.time() - start_time

        return {
            "query_id": query_id,
            "success": False,
            "error_type": error_type,
            "errors": errors,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "fallback_available": self.fallback_enabled,
            "metadata": {"orchestrator_version": "1.0.0"},
        }

    def get_system_status(self) -> dict[str, Any]:
        """시스템 상태 반환"""
        try:
            # SQL 서비스 상태
            sql_status = (
                self.text_to_sql_service.test_connection()
                if self.text_to_sql_service
                else False
            )

            # 캐시 상태
            cache_stats = self.cache.cache_service.get_stats()

            return {
                "sql_service": sql_status,
                "rag_service": True,  # 실제 구현에서는 RAG 서비스 상태 확인
                "cache": cache_stats,
                "orchestrator": True,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"시스템 상태 확인 중 오류: {e}")
            return {
                "sql_service": False,
                "rag_service": False,
                "cache": {"error": str(e)},
                "orchestrator": False,
                "timestamp": datetime.now().isoformat(),
            }


# 전역 오케스트레이터 인스턴스
_query_orchestrator = None


def get_query_orchestrator() -> QueryOrchestrator:
    """질의 오케스트레이터 인스턴스 반환"""
    global _query_orchestrator
    if _query_orchestrator is None:
        _query_orchestrator = QueryOrchestrator()
    return _query_orchestrator
